"""
title: DropLab Analista
author: DropLab · Máster de IA agéntica (sesión 3)
version: 3.0
description: Envía la pregunta (y la imagen adjunta) a la API del Asistente DropLab y muestra la respuesta, las evidencias, las comprobaciones y los límites. La lógica NO está aquí: está en practica/sesion_3/asistente/.
"""

# Una Pipe de Open WebUI es un «modelo» más en el selector: cuando el usuario escribe, Open WebUI llama a pipe().
# Esta Pipe es un adaptador ligero: traduce lo que llega de Open WebUI a una petición HTTP a nuestra API y
# convierte la respuesta en Markdown. No busca, no calcula y no llama a Ollama.
# Los desplegables: Open WebUI 0.12 solo los reconoce con «<details>» y «<summary>…</summary>» en líneas propias.
#
# ASÍNCRONO, no requests: pipe() se ejecuta dentro del bucle de eventos de Open WebUI. Una llamada bloqueante
# (requests) congelaba TODA la interfaz, para todos los usuarios, durante los 1–3 minutos del análisis
# (comprobado: el inicio de sesión de Open WebUI dejaba de responder). Con httpx.AsyncClient, no.
#
# Cómo llega la imagen (comprobado en Open WebUI 0.12.0, ver docs/sesion_3/02):
#   el usuario adjunta una imagen → Open WebUI la guarda y, al llamar a la Pipe, la pone en body["messages"]
#   como una parte {"type": "image_url", "image_url": {"url": "data:image/png;base64,…"}} del último mensaje
#   (unos 110.000 caracteres para el ticket). __files__ llega vacío. Y añade otra parte de texto
#   «<attached_files>…</attached_files>» con la lista de adjuntos: no es la pregunta y hay que quitarla.
#   Por si otra versión dejara la imagen solo en __files__, también se busca allí.

import json
import re
from typing import Optional

import httpx                       # viene con Open WebUI; ASÍNCRONO (ver más abajo)
from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        API_URL: str = Field(default="http://127.0.0.1:8000", description="Dirección de la API del Asistente DropLab")
        TIMEOUT: int = Field(default=900, description="Segundos máximos de espera")
        MODELO_TEXTO: str = Field(default="", description="Vacío = el de la API (qwen3:30b-a3b-instruct)")
        MODELO_VISION: str = Field(default="", description="Vacío = el de la API (qwen3-vl:8b-instruct)")
        MOSTRAR_TRAZA: bool = Field(default=True, description="Añadir la traza de ejecución al final")

    def __init__(self):
        self.valves = self.Valves()

    # -- lo que llega de Open WebUI ------------------------------------------------------------
    @staticmethod
    def _ultimo_usuario(body: dict) -> tuple[str, Optional[str]]:
        """El texto y la primera imagen (data URI) del último mensaje del usuario."""
        for m in reversed(body.get("messages", [])):
            if m.get("role") != "user":
                continue
            contenido = m.get("content")
            if isinstance(contenido, str):
                return contenido, None
            texto, imagen = [], None
            for parte in contenido or []:
                if parte.get("type") == "text":
                    t = re.sub(r"<attached_files>.*?</attached_files>", "", parte.get("text", ""), flags=re.S).strip()
                    if t:
                        texto.append(t)
                elif parte.get("type") in ("image_url", "input_image") and imagen is None:
                    url = parte.get("image_url")
                    imagen = url.get("url") if isinstance(url, dict) else url
            return "\n".join(texto), imagen
        return "", None

    @staticmethod
    def _imagen_en_files(files: list) -> Optional[str]:
        for f in files or []:
            url = f.get("url") or ""
            if url.startswith("data:image/"):
                return url
        return None

    # -- la llamada ----------------------------------------------------------------------------
    async def pipe(self, body: dict, __event_emitter__=None, __files__: list = None, __task__: str = None) -> str:
        async def estado(texto: str, fin: bool = False):
            if __event_emitter__:
                await __event_emitter__({"type": "status", "data": {"description": texto, "done": fin}})

        # Open WebUI también llama al «modelo» elegido para tareas internas (título del chat, etiquetas,
        # preguntas de seguimiento). Con esta Pipe, cada una sería un análisis completo: se ignoran.
        # (Comprobado: sin esto, cada pregunta lanzaba un segundo análisis para poner título al chat.)
        if __task__ or not body.get("messages"):
            return ""
        pregunta, imagen = self._ultimo_usuario(body)
        imagen = imagen or self._imagen_en_files(__files__)
        if not pregunta.strip():
            pregunta = "¿Qué demuestra esta imagen?" if imagen else ""
        if not pregunta.strip():
            return "Escribe una pregunta (y, si quieres, adjunta un ticket, un recuento o un albarán)."

        peticion = {"pregunta": pregunta, "imagen_base64": imagen}
        if self.valves.MODELO_TEXTO:
            peticion["modelo_texto"] = self.valves.MODELO_TEXTO
        if self.valves.MODELO_VISION:
            peticion["modelo_vision"] = self.valves.MODELO_VISION
        await estado(f"Enviando a la API{' con una imagen' if imagen else ''}…")
        resultado, errores = None, []
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.valves.TIMEOUT, connect=5)) as cliente:
                async with cliente.stream("POST", self.valves.API_URL + "/analizar/stream", json=peticion) as r:
                    if r.status_code != 200:
                        cuerpo = (await r.aread()).decode("utf-8", "replace")
                        try:
                            errores = json.loads(cuerpo).get("errores") or [
                                {"codigo": f"HTTP_{r.status_code}", "componente": "api", "mensaje": cuerpo[:300]}]
                        except ValueError:
                            errores = [{"codigo": f"HTTP_{r.status_code}", "componente": "api", "mensaje": cuerpo[:300]}]
                    else:
                        async for linea in r.aiter_lines():
                            if not linea:
                                continue
                            x = json.loads(linea)
                            if x["tipo"] == "paso":
                                for t in x.get("traza", []):
                                    await estado(f"{t['nodo']} · {t['detalle'][:90]} ({t['segundos']} s)")
                            elif x["tipo"] == "resultado":
                                resultado = x
                            else:
                                errores = x.get("errores", [])
        except httpx.ConnectError:
            errores = [{"codigo": "API_NO_DISPONIBLE", "componente": "pipe",
                        "mensaje": f"No hay respuesta en {self.valves.API_URL}. ¿Está arrancada la API "
                                   f"(python practica/sesion_3/03_api.py)?"}]
        except httpx.TimeoutException:
            errores = [{"codigo": "API_TIEMPO_AGOTADO", "componente": "pipe",
                        "mensaje": f"La API no terminó en {self.valves.TIMEOUT} s."}]
        await estado("Listo" if resultado else "Error", fin=True)
        if resultado is None:
            return "### ⚠ No se ha podido responder\n\n" + "\n".join(
                f"- **{e['codigo']}** ({e['componente']}): {e['mensaje']}" for e in errores)
        return self._markdown(resultado, imagen is not None)

    # -- lo que ve el usuario ------------------------------------------------------------------
    def _markdown(self, r: dict, hubo_imagen: bool) -> str:
        md = [r["respuesta"] or "_(sin respuesta)_", ""]
        if r.get("verificacion"):
            md += ["> ⚠ **La revisión automática encontró problemas:** " + "; ".join(r["verificacion"]), ""]
        if r.get("comprobaciones"):
            md += ["#### Comprobaciones del código"]
            iconos = {"coincide": "✅", "discrepancia": "❌", "lectura_dudosa": "❓", "aviso": "⚠️", "no_elegible": "➖",
                      "elegible": "✔️", "revisar": "⚠️", "coincide_en_parte": "◐", "no_verificable": "❓", "no_valida": "❓"}
            md += [f"- {iconos.get(c['resultado'], '•')} **{c['nombre']}** · {c['resultado']}: {c['detalle']}"
                   for c in r["comprobaciones"]]
            md.append("")
        v = next((e for e in r["evidencias"] if e["tipo"] == "imagen"), None)
        if v and v.get("comprobaciones"):
            md += ["<details>", "<summary>Imagen: campo a campo</summary>", "",
                   "| Campo | En la imagen | En el registro | Resultado |", "|---|---|---|---|"]
            md += [f"| {c['campo']} | {c['en_imagen'] if c['en_imagen'] is not None else '—'} | "
                   f"{c['en_registro'] if c['en_registro'] is not None else '—'} | {c['resultado']} |"
                   for c in v["comprobaciones"]]
            md += ["", "</details>", ""]
        elif hubo_imagen and not v:
            md += ["> ⚠ Se adjuntó una imagen, pero no se pudo leer (ver errores).", ""]
        if r.get("limitaciones"):
            md += ["#### Límites que añade el código"] + [f"- {x}" for x in r["limitaciones"]] + [""]
        md += ["<details>", "<summary>Fuentes (las numera el código)</summary>", ""]
        for e in r["evidencias"]:
            marca = "●" if e.get("citada") else "○"
            if e["tipo"] == "datos":
                md.append(f"- {marca} **[{e['id']}]** {e['titulo']} · `{e['sql'][:160]}` · parámetros {e['parametros']}")
            elif e["tipo"] == "documento":
                extra = f" · ⚠ SUSTITUIDO por {e['sustituido_por']}" if e.get("sustituido_por") else ""
                if e.get("lectura"):
                    extra += " · 🔎 " + e["lectura"].split(" · fila partida")[0]
                md.append(f"- {marca} **[{e['id']}]** {e['cita']} · {e['estado']} · {e['fecha']}{extra}")
            else:
                md.append(f"- {marca} **[{e['id']}]** {e['titulo']} · {e['modelo']} · veredicto: {e.get('veredicto')}")
        md += ["", "● citada en la respuesta · ○ consultada, no citada", "</details>", ""]
        if self.valves.MOSTRAR_TRAZA:
            md += ["<details>", "<summary>Traza de ejecución (" + str(r["segundos"]) + " s)</summary>", "",
                   "| Paso | Herramienta | Detalle | s |", "|---|---|---|---|"]
            md += [f"| {t['nodo']} | {t['herramienta']} | {t['detalle'][:120]} | {t['segundos']} |" for t in r["traza"]]
            md += ["", "Es lo que hizo el sistema (pasos, herramientas, tiempos), no lo que «pensó» el modelo.", "</details>"]
        if r.get("errores"):
            md += ["", "#### Errores"] + [f"- **{e['codigo']}** ({e['componente']}): {e['mensaje']}" for e in r["errores"]]
        return "\n".join(md)
