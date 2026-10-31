"""Para casa (ampliación) · Evaluar por piezas: ¿dónde está el fallo?

Un sistema que combina visión, datos y documentos puede fallar en cinco sitios distintos. Cada parte del
examen (examen/examen_sesion_3.json) prueba UNA pieza, para que un fallo diga dónde está:

    lectura        ¿el VLM lee bien la imagen?            campos extraídos frente a lo que dice la imagen
    recuperacion   ¿el buscador trae la fuente correcta?   fuente esperada entre los 5 primeros (sin modelo de texto)
    calculo        ¿las consultas dan la cifra correcta?   consultas fijas frente a la cifra calculada a mano
    respuesta      ¿la respuesta interpreta bien?          hechos que debe tener y lo que NO debe afirmar
    integracion    ¿se hablan bien las piezas?             errores con nombre: API caída, Ollama caído, imagen mala…

Uso:
    python practica/sesion_3/06_evaluar.py                          # resultados guardados (instantáneo)
    python practica/sesion_3/06_evaluar.py --parte integracion      # en directo, sin modelos (segundos)
    python practica/sesion_3/06_evaluar.py --parte calculo          # en directo, sin modelos
    python practica/sesion_3/06_evaluar.py --parte recuperacion     # en directo, solo embeddings (segundos)
    python practica/sesion_3/06_evaluar.py --parte lectura          # en directo: VLM (~1 min por imagen)
    python practica/sesion_3/06_evaluar.py --parte respuesta        # en directo: flujo completo (~2 min por pregunta)
    python practica/sesion_3/06_evaluar.py --todo --guardar         # todo, y lo guarda (antes de clase)
    python practica/sesion_3/06_evaluar.py --todo --texto qwen3:4b-instruct --vision qwen3-vl:4b-instruct --guardar
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI / "openwebui"))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from asistente import config, datos, documentos, flujo, vision  # noqa: E402
from asistente.ollama import ErrorComponente, chat  # noqa: E402

c = Console()
EXAMEN = json.loads((AQUI / "examen" / "examen_sesion_3.json").read_text(encoding="utf-8"))
PARTES = ["integracion", "calculo", "recuperacion", "lectura", "respuesta"]
PIEZA = {"lectura": "VLM (lectura visual)", "recuperacion": "RAG (recuperación)", "calculo": "SQL (consulta/cálculo)",
         "respuesta": "LLM (interpretación)", "integracion": "integración entre piezas"}


def nombre_config(texto: str, vision_: str) -> str:
    return f"{texto.split(':')[0]}-{texto.split(':')[1].split('-')[0] if ':' in texto else ''}__{vision_.replace(':', '-')}"


def obtener(d, ruta: str):
    for p in ruta.split("."):
        if isinstance(d, list):
            d = d[int(p)] if p.isdigit() and int(p) < len(d) else None
        elif isinstance(d, dict):
            d = d.get(p)
        else:
            return None
    return d


def igual(a, b) -> bool:
    if isinstance(b, bool) or b is None:
        return a is b
    if isinstance(b, (int, float)) and isinstance(a, (int, float)):
        return abs(a - b) <= 0.011
    return str(a).strip().upper() == str(b).strip().upper()


# ---------------------------------------------------------------------------
# Las cinco partes
# ---------------------------------------------------------------------------

def parte_integracion(_a) -> list[dict]:
    """Errores con nombre: cada pieza, cuando falla, dice quién es. Sin modelos: segundos."""
    from droplab_pipe import Pipe
    filas = []

    def prueba(id_, que, funcion, esperado):
        t0 = time.time()
        try:
            obtenido = funcion()
        except ErrorComponente as e:
            obtenido = e.codigo
        except Exception as e:  # noqa: BLE001
            obtenido = f"{type(e).__name__}: {e}"[:80]
        filas.append({"id": id_, "prueba": que, "esperado": esperado, "obtenido": obtenido, "ok": obtenido == esperado,
                      "segundos": round(time.time() - t0, 2)})

    prueba("I1", "Ollama caído (dirección equivocada)",
           lambda: chat("qwen3:4b-instruct", [{"role": "user", "content": "hola"}], url="http://127.0.0.1:9"),
           "OLLAMA_NO_DISPONIBLE")
    prueba("I2", "Modelo no instalado", lambda: chat("modelo-que-no-existe:1b", [{"role": "user", "content": "hola"}]),
           "MODELO_NO_INSTALADO")
    prueba("I3", "Archivo que no es una imagen", lambda: vision.preparar_imagen(b"esto no es un PNG"), "IMAGEN_NO_VALIDA")
    prueba("I4", "Parámetro malicioso en una consulta", lambda: datos.pedido("1; DROP TABLE ventas"), "PARAMETRO_NO_VALIDO")
    prueba("I5", "Pregunta vacía", lambda: flujo.estado_inicial("   "), "PREGUNTA_VACIA")
    png = base64.b64encode((config.IMAGENES / "ticket_abril.png").read_bytes()).decode()
    cuerpo = {"messages": [{"role": "user", "content": [
        {"type": "text", "text": "<attached_files>\n<file type=\"file\" id=\"x\" name=\"ticket_abril.png\"/>\n</attached_files>"},
        {"type": "text", "text": "¿Qué demuestra este ticket?"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + png}}]}]}
    prueba("I6", "La Pipe extrae la pregunta y la imagen como las envía Open WebUI 0.12",
           lambda: (lambda t: "ok" if t[0] == "¿Qué demuestra este ticket?" and t[1].startswith("data:image/png")
                    else f"pregunta={t[0][:30]!r}")(Pipe._ultimo_usuario(cuerpo)), "ok")
    p = Pipe()
    p.valves.API_URL = "http://127.0.0.1:9"
    prueba("I7", "API caída: la Pipe lo dice con su nombre",
           lambda: "API_NO_DISPONIBLE" if "API_NO_DISPONIBLE" in asyncio.run(
               p.pipe({"messages": [{"role": "user", "content": "hola"}]})) else "otro", "API_NO_DISPONIBLE")
    prueba("I8", "Tarea interna de Open WebUI (título del chat): la Pipe no la envía a la API",
           lambda: "ignorada" if asyncio.run(p.pipe({"messages": [{"role": "user", "content": "x"}]},
                                                    __task__="title_generation")) == "" else "enviada", "ignorada")
    prueba("I9", "La imagen se decodifica desde un data URI", lambda: "ok" if vision.preparar_imagen(
        vision.desde_data_uri("data:image/png;base64," + png)).ancho > 0 else "no", "ok")
    prueba("I10", "La Pipe no bloquea Open WebUI mientras espera a la API (asíncrona)", pipe_no_bloquea, "no bloquea")
    return filas


def pipe_no_bloquea() -> str:
    """Una API falsa tarda 2 s; mientras, otra tarea debe seguir avanzando. Con requests (bloqueante) no avanzaba."""
    import http.server
    import threading
    from droplab_pipe import Pipe

    class Lenta(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            time.sleep(2)
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"errores": [{"codigo": "X", "componente": "prueba", "mensaje": "lenta"}]}')

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Lenta)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    p = Pipe()
    p.valves.API_URL = f"http://127.0.0.1:{srv.server_address[1]}"
    latidos = 0

    async def latir():
        nonlocal latidos
        for _ in range(15):
            await asyncio.sleep(0.1)
            latidos += 1

    async def ambos():
        await asyncio.gather(p.pipe({"messages": [{"role": "user", "content": "hola"}]}), latir())

    asyncio.run(ambos())
    srv.shutdown()
    return "no bloquea" if latidos == 15 else f"bloquea ({latidos}/15 latidos)"


def parte_calculo(_a) -> list[dict]:
    filas = []
    for q in EXAMEN["calculo"]:
        t0 = time.time()
        r = getattr(datos, q["consulta"])(**q["parametros"])
        clave = "periodo" if q["consulta"] == "resumen_tienda" else "sku"
        por = {f.get(clave): f for f in r["filas"]} if q["consulta"] != "pedido" else {}
        for ruta, esperado in q["esperado"].items():
            if ruta == "total":
                obtenido = r["total"]
            else:
                fila, campo = ruta.rsplit(".", 1)          # «B - A.ventas_netas» → fila «B - A», campo «ventas_netas»
                obtenido = (por.get(fila) or {}).get(campo)
            filas.append({"id": q["id"], "prueba": f"{q['consulta']}({', '.join(map(str, q['parametros'].values()))}) · "
                          f"{ruta}", "esperado": esperado, "obtenido": obtenido, "ok": igual(obtenido, esperado),
                          "segundos": round(time.time() - t0, 2)})
    return filas


def coincide_fuente(f: dict, patron: str) -> bool:
    if "#" in patron:
        archivo, pag = patron.split("#")
        return f["fuente"] == archivo and str(f["pagina"]) == pag
    return f["fuente"] == patron


def parte_recuperacion(_a) -> list[dict]:
    filas = []
    for q in EXAMEN["recuperacion"]:
        t0 = time.time()
        frags = documentos.buscar(q["pregunta"], k=5, vigentes=False)
        pos = next((i for i, f in enumerate(frags, 1) if any(coincide_fuente(f, p) for p in q["fuentes"])), None)
        filas.append({"id": q["id"], "prueba": q["pregunta"], "esperado": " o ".join(q["fuentes"][:2]),
                      "obtenido": f"puesto {pos}: {frags[pos - 1]['cita']}" if pos else "no está entre los 5 primeros",
                      "ok": pos is not None, "segundos": round(time.time() - t0, 2)})
    return filas


def parte_lectura(a) -> list[dict]:
    filas = []
    for q in EXAMEN["lectura"]:
        t0 = time.time()
        try:
            r = vision.analizar_imagen((config.ROOT / q["imagen"]).read_bytes(), q["tipo"], modelo=a.vision)
        except ErrorComponente as e:
            filas.append({"id": q["id"], "prueba": Path(q["imagen"]).name, "esperado": "lectura", "obtenido": e.codigo,
                          "ok": False, "segundos": round(time.time() - t0, 1)})
            continue
        d = r["extraccion"]["datos"] or {}
        bien = [k for k, v in q["campos"].items() if igual(obtener(d, k), v)]
        mal = {k: obtener(d, k) for k in q["campos"] if k not in bien}
        ver = (r["comprobacion"] or {}).get("veredicto", "json no válido")
        aceptables = q.get("veredicto_aceptable", [q.get("veredicto")])
        sint = " (sintética)" if q.get("sintetica") else ""
        if q.get("veredicto_aceptable"):          # lo que cuenta: que el sistema avise
            ok, esperado = ver in aceptables, "el sistema detecta la mala lectura"
        else:
            ok, esperado = len(bien) == len(q["campos"]) and ver in aceptables, f"{len(q['campos'])} campos · {aceptables[0]}"
        filas.append({"id": q["id"], "prueba": Path(q["imagen"]).name + sint, "esperado": esperado,
                      "obtenido": f"{len(bien)}/{len(q['campos'])} campos · {ver}"
                                  + (f" · mal: {json.dumps(mal, ensure_ascii=False)[:90]}" if mal else ""),
                      "ok": ok, "campos_bien": len(bien), "campos": len(q["campos"]),
                      "segundos": round(time.time() - t0, 1), "tiempos": r["extraccion"]["tiempos"]})
    return filas


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").lower())


def parte_respuesta(a) -> list[dict]:
    filas = []
    for q in EXAMEN["respuesta"]:
        t0 = time.time()
        img = (config.ROOT / q["imagen"]).read_bytes() if q.get("imagen") else None
        try:
            r = flujo.ejecutar(q["pregunta"], img, modelo_texto=a.texto, modelo_vision=a.vision)
        except ErrorComponente as e:
            filas.append({"id": q["id"], "prueba": q["tipo"], "esperado": "respuesta", "obtenido": e.codigo, "ok": False,
                          "segundos": round(time.time() - t0, 1)})
            continue
        citas = sum(1 for e in r["evidencias"] if e.get("citada"))
        filas.append({"id": q["id"], "prueba": f"{q['tipo']} · {q['pregunta'][:60]}", "esperado": "hechos y límites",
                      **calificar(q, r["respuesta"], r["verificacion"], citas),
                      "verificacion": r["verificacion"], "verificacion_limpia": not r["verificacion"], "citas": citas,
                      "segundos": round(time.time() - t0, 1), "respuesta": r["respuesta"], "plan": r["plan"]["tareas"],
                      "traza": [{k: x[k] for k in ("nodo", "segundos", "detalle")} for x in r["traza"]]})
    return filas


def calificar(q: dict, respuesta: str, verificacion: list[str], citas: int = 0) -> dict:
    """La nota de una respuesta (sin modelo): hechos que debe tener, lo que no debe decir y si afirma una causa.
    Se puede volver a aplicar a respuestas guardadas si cambia el examen (07_comparar.py --recalificar)."""
    t = norm(respuesta)
    faltan = [g[0] for g in q.get("debe", []) if not any(norm(x) in t for x in g)]
    prohibidas = [x for x in q.get("no_debe", []) if norm(x) in t]
    if q.get("negacion_permitida"):               # «no demuestra fraude» está bien; «es un fraude», no
        prohibidas = [x for x in prohibidas if flujo.frases_con(re.compile(re.escape(x), re.I), respuesta)]
    causa = q.get("no_debe_afirmar_causa", False) and "afirma una causa sin presentarla como hipótesis" in verificacion
    ok = not faltan and not prohibidas and not causa
    problemas = ([f"falta {faltan}"] if faltan else []) + ([f"dice {prohibidas}"] if prohibidas else []) + \
                (["afirma la causa"] if causa else []) + ([f"verificación: {verificacion}"] if verificacion else [])
    return {"ok": ok, "obtenido": ("✓ " if ok else "") + ("; ".join(problemas) or f"{citas} evidencias citadas")}


FUNCIONES = {"integracion": parte_integracion, "calculo": parte_calculo, "recuperacion": parte_recuperacion,
             "lectura": parte_lectura, "respuesta": parte_respuesta}


def mostrar(resultados: dict, origen: str) -> None:
    resumen = Table(title=f"Dónde falla el sistema · {origen}", title_justify="left", header_style="bold")
    for col in ("parte", "pieza que se prueba", "aciertos", "s por prueba"):
        resumen.add_column(col)
    for parte in PARTES:
        filas = resultados.get(parte)
        if not filas:
            continue
        t = Table(title=f"{parte.upper()} · {PIEZA[parte]}", title_justify="left", header_style="bold", show_lines=False)
        for col in ("", "id", "prueba", "esperado", "obtenido", "s"):
            t.add_column(col, overflow="fold")
        for f in filas:
            t.add_row("[green]✓[/]" if f["ok"] else "[red]✗[/]", f["id"], str(f["prueba"])[:70], str(f["esperado"])[:40],
                      str(f["obtenido"])[:110], str(f["segundos"]))
        c.print(t)
        n_ok = sum(f["ok"] for f in filas)
        col = "green" if n_ok == len(filas) else "yellow" if n_ok >= len(filas) - 1 else "red"
        resumen.add_row(parte, PIEZA[parte], f"[{col}]{n_ok}/{len(filas)}[/]",
                        f"{sum(f['segundos'] for f in filas) / len(filas):.1f}")
    c.print(resumen)


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluar el asistente por piezas.")
    ap.add_argument("--parte", choices=PARTES, action="append")
    ap.add_argument("--todo", action="store_true")
    ap.add_argument("--texto", default=config.MODELO_TEXTO)
    ap.add_argument("--vision", default=config.MODELO_VISION)
    ap.add_argument("--guardar", action="store_true", help=f"Guardar en {config.RESULTADOS.relative_to(config.ROOT)}/")
    a = ap.parse_args()
    archivo = config.RESULTADOS / f"evaluacion_{nombre_config(a.texto, a.vision)}.json"
    if not a.parte and not a.todo:
        guardados = sorted(config.RESULTADOS.glob("evaluacion_*.json"))
        if not guardados:
            raise SystemExit("No hay resultados guardados: python practica/sesion_3/06_evaluar.py --todo --guardar")
        for g in guardados:
            d = json.loads(g.read_text(encoding="utf-8"))
            mostrar(d["resultados"], f"GUARDADO {d['fecha']} · texto {d['texto']} · visión {d['vision']}")
        return
    partes = PARTES if a.todo else a.parte
    resultados = {}
    for p in partes:
        c.rule(f"[bold]{p}[/] · {PIEZA[p]}")
        resultados[p] = FUNCIONES[p](a)
    mostrar(resultados, f"EN DIRECTO · texto {a.texto} · visión {a.vision}")
    if a.guardar:
        previo = json.loads(archivo.read_text(encoding="utf-8"))["resultados"] if archivo.exists() else {}
        config.RESULTADOS.mkdir(parents=True, exist_ok=True)
        archivo.write_text(json.dumps({"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "texto": a.texto,
                                       "vision": a.vision, "resultados": {**previo, **resultados}},
                                      ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        c.print(f"[dim]Guardado: {archivo.relative_to(config.ROOT)}[/]")


if __name__ == "__main__":
    main()
