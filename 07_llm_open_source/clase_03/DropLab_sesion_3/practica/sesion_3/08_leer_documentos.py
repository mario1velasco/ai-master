"""Práctica 2 · Leer lo que no es texto: los PDF de junio (tablas partidas, un gráfico y un expediente escaneado).

Segundo encargo de dirección: el cierre de la reposición de junio. Dos PDF que el RAG de la sesión 2 no sabe leer:
    informe    01_DropLab_informe_reposicion_junio.pdf   8 págs. digitales: tablas sin rejilla, una tabla que
                                                          sigue en la página siguiente, un gráfico (imagen) y un
                                                          anexo con el BORRADOR v0.9 dentro del documento aprobado
    escaneado  02_DropLab_expediente_escaneado.pdf       3 págs. que son solo imagen: albarán, incidencia y
                                                          rectificación (sin capa de texto)

Cuatro formas de leer una página (en asistente/lectura.py está qué hace cada una):
    texto   capa de texto con pymupdf          (lo que hacía 10_corpus.py)
    ocr     PP-OCRv6 en la GPU                 (texto + confianza por línea; sin estructura)
    vl      PaddleOCR-VL-1.6 en la GPU         (maquetación + tablas + gráfico → Markdown)
    vlm     qwen3-vl:8b-instruct en Ollama     (el VLM general de la práctica de los tickets)

Uso (.venv del curso: todo lo guardado y la capa de texto):
    python practica/sesion_3/08_leer_documentos.py                        # qué hay en cada página
    python practica/sesion_3/08_leer_documentos.py --antes                # el lector de la sesión 2 con estos PDF
    python practica/sesion_3/08_leer_documentos.py --leer informe 4 --con vl --guardada
    python practica/sesion_3/08_leer_documentos.py --leer escaneado 2 --con ocr --guardada
    python practica/sesion_3/08_leer_documentos.py --comparar             # tiempos y cifras comprobadas, medidos
    python practica/sesion_3/08_leer_documentos.py --capas escaneado 2 --guardada   # qué hace PaddleOCR solo y qué nuestro código
    python practica/sesion_3/08_leer_documentos.py --capas escaneado 2 --guardada --solo-modelo   # solo la salida cruda
    python practica/sesion_3/08_leer_documentos.py --capas informe 8 --guardada --solo-reglas     # limpieza, reglas y ficha
    python practica/sesion_3/08_leer_documentos.py --grafico              # EXTRA: el gráfico G1 recortado, a un VLM (~7 s)
    python practica/sesion_3/08_leer_documentos.py --grafico --modelo qwen3-vl:4b-instruct   # el 4B: ¿96 o 95?

En directo (necesita el venv de OCR, con PaddleOCR y PyTorch con CUDA; ver requirements_ocr.txt):
    .venv-ocr/bin/python practica/sesion_3/08_leer_documentos.py --leer escaneado 2 --con ocr    # ~2 s (+ ~10 s de carga)
    .venv-ocr/bin/python practica/sesion_3/08_leer_documentos.py --leer informe 4 --con vl       # ~25-30 s (+ ~10 s de carga)
    .venv-ocr/bin/python practica/sesion_3/08_leer_documentos.py --guardar                       # todo: ~8 min

Salida de --guardar: practica/sesion_3/salidas_guardadas/documentos/{informe,escaneado}.json
El paso siguiente (09_indice_junio.py) pone ficha a cada página y la añade al índice.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from importlib import import_module
from io import BytesIO
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")    # no comprobar la red en cada arranque
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")                 # en clase: sin avisos internos de transformers
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

import pymupdf  # noqa: E402
import requests  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402
from rich.syntax import Syntax  # noqa: E402
from rich.text import Text  # noqa: E402

from asistente import config, lectura  # noqa: E402

c = Console()
DPI = 150
FORMAS = ("texto", "ocr", "vl", "vlm")
PROMPT_VLM = ("Transcribe esta página en Markdown, tal cual, sin resumir ni añadir nada. Las tablas, como tablas "
              "Markdown. Si hay un gráfico, da sus valores en una tabla. Si algo no se lee, escribe [ilegible].")


# ---------------------------------------------------------------------------
# Las cuatro lecturas
# ---------------------------------------------------------------------------

def png(alias: str, n: int) -> Path:
    """La página como imagen (150 ppp): es lo que ven el OCR y los VLM."""
    destino = Path(tempfile.gettempdir()) / "droplab_paginas" / f"{alias}_p{n}.png"
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        with pymupdf.open(lectura.ruta_documento(alias)) as doc:
            doc[n - 1].get_pixmap(dpi=DPI).save(destino)
    return destino


def leer_texto(alias: str, n: int) -> dict:
    t = time.time()
    with pymupdf.open(lectura.ruta_documento(alias)) as doc:
        texto = doc[n - 1].get_text()
    return {"texto": texto, "segundos": round(time.time() - t, 3)}


def _paddle():
    try:
        return import_module("paddleocr")
    except ImportError:
        raise SystemExit("PaddleOCR no está en este entorno. En el Jetson:\n"
                         "  .venv-ocr/bin/python practica/sesion_3/08_leer_documentos.py ...\n"
                         "o añade --guardada para ver la lectura guardada.")


_MODELOS: dict = {}


def modelo(forma: str):
    """Carga el modelo una vez (la primera carga es lo lento: se mide aparte)."""
    if forma not in _MODELOS:
        t = time.time()
        p = _paddle()
        import logging
        try:
            from paddlex.utils import logging as plog
            plog.setup_logging("WARNING")                # sin «Creating model…» en verde
        except Exception:                                # noqa: BLE001
            pass
        logging.getLogger("transformers").setLevel(logging.ERROR)
        if forma == "ocr":
            _MODELOS[forma] = p.PaddleOCR(lang="es", engine="transformers", device="gpu:0",
                                          use_doc_orientation_classify=False, use_doc_unwarping=False,
                                          use_textline_orientation=False)
        else:
            # Configuración NUESTRA (lo demás lo hace la librería sola): por defecto PaddleOCR-VL deja los gráficos como
            # imagen y quita del Markdown cabecera, pie y notas. Necesitamos G1 como tabla y el pie (código y versión).
            _MODELOS[forma] = p.PaddleOCRVL(engine="transformers", device="gpu:0", use_doc_orientation_classify=False,
                                            use_doc_unwarping=False, use_chart_recognition=True,
                                            markdown_ignore_labels=["number"])   # solo fuera el número de página
        _MODELOS[f"{forma}_carga"] = round(time.time() - t, 1)
    return _MODELOS[forma]


def leer_ocr(alias: str, n: int) -> dict:
    ocr = modelo("ocr")
    t = time.time()
    r = ocr.predict(str(png(alias, n)))[0]
    return {"lineas": [[txt, round(float(s), 3)] for txt, s in zip(r["rec_texts"], r["rec_scores"])],
            "segundos": round(time.time() - t, 2)}


def leer_vl(alias: str, n: int) -> dict:
    vl = modelo("vl")
    t = time.time()
    r = list(vl.predict(str(png(alias, n))))[0]
    return {"markdown": r.markdown["markdown_texts"], "segundos": round(time.time() - t, 1)}


def leer_vlm(alias: str, n: int, modelo_vlm: str = config.MODELO_VISION) -> dict:
    from PIL import Image
    im = Image.open(png(alias, n)).convert("RGB")
    im.thumbnail((1280, 1280))
    buf = BytesIO()
    im.save(buf, "PNG")
    cuerpo = {"model": modelo_vlm, "stream": False, "think": False, "keep_alive": config.KEEP_ALIVE,
              "options": {"temperature": 0, "num_ctx": config.CTX_VISION, "num_predict": 1500},
              "messages": [{"role": "user", "content": PROMPT_VLM, "images": [base64.b64encode(buf.getvalue()).decode()]}]}
    t = time.time()
    r = requests.post(config.OLLAMA_URL + "/api/chat", json=cuerpo, timeout=900).json()
    return {"markdown": r["message"]["content"], "segundos": round(time.time() - t, 1), "modelo": modelo_vlm,
            "carga": round(r.get("load_duration", 0) / 1e9, 1)}


LEER = {"texto": leer_texto, "ocr": leer_ocr, "vl": leer_vl, "vlm": lambda alias, n: leer_vlm(alias, n, ARGS_MODELO)}
ARGS_MODELO = config.MODELO_VISION

# Los valores reales de G1 (comprobados a mano con el PDF original): semana → tienda → %
G1 = {"01-07": {"MAD-MAL": 92, "MAD-GOY": 94, "BCN-EIX": 96}, "08-14": {"MAD-MAL": 68, "MAD-GOY": 90, "BCN-EIX": 94},
      "15-21": {"MAD-MAL": 81, "MAD-GOY": 93, "BCN-EIX": 95}, "22-28": {"MAD-MAL": 95, "MAD-GOY": 96, "BCN-EIX": 97}}
PROMPT_G1 = ("Es un gráfico de líneas. Para cada serie (tienda) y cada semana del eje X, da el porcentaje que indica su "
             "etiqueta. Responde con una tabla Markdown: semana | MAD-MAL | MAD-GOY | BCN-EIX. Si una etiqueta no se lee "
             "con seguridad, escribe '?'.")


def grafico(modelo_vlm: str) -> None:
    """EXTRA · Solo el gráfico (recortado del PDF), a un VLM general, y su lectura frente a los valores reales."""
    with pymupdf.open(lectura.ruta_documento("informe")) as doc:
        img = doc.extract_image(doc[3].get_images()[0][0])["image"]
    cuerpo = {"model": modelo_vlm, "stream": False, "think": False, "keep_alive": config.KEEP_ALIVE,
              "options": {"temperature": 0, "num_ctx": config.CTX_VISION, "num_predict": 400},
              "messages": [{"role": "user", "content": PROMPT_G1, "images": [base64.b64encode(img).decode()]}]}
    t = time.time()
    try:
        r = requests.post(config.OLLAMA_URL + "/api/chat", json=cuerpo, timeout=600).json()
    except requests.exceptions.ConnectionError:
        raise SystemExit("No responde Ollama.")
    if "message" not in r:
        raise SystemExit(f"Ollama: {r.get('error', r)}  (¿ollama pull {modelo_vlm}?)")
    texto = r["message"]["content"]
    c.print(Panel(texto.strip(), title=f"G1 recortado · {modelo_vlm} · {time.time() - t:.1f} s "
                  f"(carga {r.get('load_duration', 0) / 1e9:.1f} s)", title_align="left"))
    t2 = Table(title="Frente a los valores reales (comprobados a mano)", title_justify="left", header_style="bold")
    for col in ("semana", "MAD-MAL", "MAD-GOY", "BCN-EIX"):
        t2.add_column(col)
    aciertos = 0
    for semana, reales in G1.items():
        fila = next((l for l in texto.splitlines() if semana in l.replace(" ", "")), "")
        leidos = [x.strip().rstrip("%").strip() for x in fila.strip().strip("|").split("|")[1:4]] if fila else ["", "", ""]
        celdas = []
        for (tienda, real), leido in zip(reales.items(), leidos + [""] * 3):
            ok = leido == str(real)
            aciertos += ok
            celdas.append(Text(f"{leido or '—'}" + ("" if ok else f" (es {real})"), style="green" if ok else "bold red"))
        t2.add_row(semana, *celdas)
    c.print(t2)
    c.print(f"[bold]{aciertos}/12 valores correctos.[/] [dim]Un fallo dicho con la misma seguridad que un acierto: "
            "por eso la ficha dice «SIN COMPROBAR».[/]")


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------

def paginas(alias: str) -> list[dict]:
    with pymupdf.open(lectura.ruta_documento(alias)) as doc:
        out = []
        for n, p in enumerate(doc, 1):
            palabras, imagenes = len(p.get_text().split()), len(p.get_images())
            clase = ("escaneada (solo imagen)" if palabras < 20 else
                     "digital + imagen (gráfico)" if imagenes else "digital")
            out.append({"n": n, "palabras": palabras, "imagenes": imagenes, "clase": clase})
    return out


def mapa() -> None:
    t = Table(title="Los PDF de junio: qué hay en cada página", title_justify="left", header_style="bold")
    for col in ("documento", "pág.", "palabras en la capa de texto", "imágenes", "tipo de página"):
        t.add_column(col)
    for alias in lectura.ALIAS:
        for p in paginas(alias):
            color = "red" if p["palabras"] < 20 else "yellow" if p["imagenes"] else ""
            t.add_row(alias, str(p["n"]), str(p["palabras"]), str(p["imagenes"]), Text(p["clase"], style=color))
        t.add_section()
    c.print(t)
    c.print("[dim]Rojo: no hay texto que extraer (hace falta OCR). Amarillo: hay texto, pero parte del contenido es una "
            "imagen (el gráfico G1): sus valores no están en la capa de texto.[/]")


def antes() -> None:
    """El lector de PDF de la sesión 2 (10_corpus.leer_pdf), sin cambios, con los documentos de junio."""
    sys.path.insert(0, str(config.SESION2))
    corpus = import_module("10_corpus")
    t = Table(title="ANTES · 10_corpus.leer_pdf() con el informe de junio", title_justify="left", header_style="bold")
    for col in ("pág.", "código", "estado", "fecha", "empieza por"):
        t.add_column(col, overflow="fold")
    for f in corpus.leer_pdf(lectura.ruta_documento("informe")):
        t.add_row(str(f["pagina"]), Text(f["codigo"], style="red"), Text(f["estado"], style="red"), f["fecha"],
                  f["texto"][:70].replace("\n", " ") + "…")
    c.print(t)
    try:
        corpus.leer_pdf(lectura.ruta_documento("escaneado"))
        c.print("[green]El escaneado se ha leído.[/]")
    except Exception as exc:                                        # noqa: BLE001 (queremos enseñar el error tal cual)
        c.print(f"[bold red]El escaneado: {type(exc).__name__}: {exc}[/]  ← la página no tiene texto: lineas = []")
    c.print("\n[bold]Qué ha pasado[/]\n"
            "  · código «Uso interno»: la regla busca la primera línea con dos «|»… y en este formato es el pie.\n"
            "  · estado «sin estado» en todas: el borrador v0.9 del anexo (pág. 6) queda igual que el aprobado.\n"
            "  · «sustituye a ([A-Z0-9-]+)» captura LOG-2026-06: el MISMO código para v0.9 y v1.1. La versión no está en la clave.\n"
            "  · El gráfico G1 (pág. 4) es una imagen: sus 12 porcentajes no existen para el RAG.\n"
            "  · Pág. 8: tras la cabecera repetida de T2 viene «tarde. La firma…»: es el final de la fila ENT-06-012 "
            "de la pág. 7. Suelta, no dice de qué entrada es.")


def mostrar(alias: str, n: int, forma: str, guardada: bool) -> None:
    if guardada:
        g = lectura.lectura_guardada(alias)
        p = next((x for x in g["paginas"] if x["n"] == n), None)
        if p is None or (forma != "texto" and not p.get(forma)):
            raise SystemExit(f"No hay lectura guardada «{forma}» de {alias} pág. {n}. Guardadas: "
                             + ", ".join(f"{x['n']}:{'+'.join(k for k in FORMAS if x.get(k) or k == 'texto')}" for x in g["paginas"]))
        r = {"texto": p["capa_texto"], "segundos": None} if forma == "texto" else p[forma]
        origen = f"guardada el {g['fecha']} · {g.get('equipo', '')}"
        capa = p["capa_texto"]
    else:
        r = LEER[forma](alias, n)
        origen = "en directo" + (f" · carga del modelo {_MODELOS.get(forma + '_carga')} s" if forma in ("ocr", "vl") else "")
        capa = leer_texto(alias, n)["texto"]
    titulo = f"{alias} · pág. {n} · {forma} · {r.get('segundos') if r.get('segundos') is not None else '—'} s · {origen}"
    if forma == "texto":
        txt = r["texto"].strip()
        c.print(Panel(txt or "[red](vacío: la página es una imagen)[/]", title=titulo, title_align="left"))
        c.print(f"[dim]{len(txt.split())} palabras. Una tabla sale celda a celda; un gráfico, no sale.[/]")
        return
    if forma == "ocr":
        lineas = r["lineas"]
        cuerpo = Text()
        for txt, s in lineas:
            cuerpo.append(f"{s:.2f} ", style="red" if s < 0.90 else "yellow" if s < 0.97 else "green")
            cuerpo.append(txt + "\n")
        c.print(Panel(cuerpo, title=titulo, title_align="left"))
        conf = [s for _, s in lineas]
        c.print(f"[bold]{len(lineas)} líneas · confianza media {sum(conf) / len(conf):.3f} · mínima {min(conf):.3f}[/]  "
                "[dim](verde ≥ 0,97 · amarillo < 0,97 · rojo < 0,90: lo que revisaría una persona)[/]\n"
                "[dim]Lee cada línea, pero no sabe que «1 / 6 / 6 / 0» es una fila: la tabla se ha perdido.[/]")
        return
    limpio = lectura.limpiar_markdown(r["markdown"])
    c.print(Panel(limpio, title=titulo, title_align="left"))
    rev = lectura.comprobar_con_capa(lectura.sin_cabecera_ni_pie(limpio)[0], capa)
    color = "yellow" if not rev["comprobable"] or rev["solo_en_lectura"] else "green"
    c.print(f"[{color}]Comprobación con la capa de texto (sin cabecera ni pie): {lectura.resumen_revision(rev)}[/]")
    if alias == "informe" and n == 4 and "68" not in limpio:
        c.print("[bold red]El gráfico G1 no aparece en esta lectura: sus 12 valores se han perdido. Que las cifras que sí "
                "salen coincidan con el PDF no significa que esté todo.[/]")
    elif alias == "informe" and n == 4:
        c.print("[dim]Los valores «solo en la imagen» son los del gráfico G1: 9 porcentajes distintos (algunos se repiten) "
                "y los días que delimitan las semanas (08, 14, 15, 21, 22).[/]")


def capas(alias: str, n: int, guardada: bool, solo: str | None = None) -> None:
    """Qué hace PaddleOCR solo (salida cruda) y qué hace nuestro código después (limpiar, reglas de este formato y
    comprobar). Solo lecturas guardadas: no llama a ningún modelo, funciona en el .venv del curso.

    Los números de los paneles son los de la tabla de pasos: 1 fuente · 2-3 MODELO (la librería, sola) · 4 LIMPIEZA ·
    5 REGLAS · 6 COMPROBACIÓN · 7 FICHA (nuestro código, asistente/lectura.py) · y una persona valida las reglas."""
    if not guardada:
        raise SystemExit("--capas enseña lecturas ya guardadas: añade --guardada. No llama a ningún modelo.")
    g = lectura.lectura_guardada(alias)
    p = next((x for x in g["paginas"] if x["n"] == n), None)
    if p is None:
        raise SystemExit(f"{alias} no tiene página {n} (tiene {len(g['paginas'])}).")
    capa = p["capa_texto"]
    crudo = p["vl"]["markdown"]
    tablas_crudas = re.findall(r"<table.*?</table>", crudo, flags=re.S)
    cuerpo, pie = lectura.sin_cabecera_ni_pie(lectura.limpiar_markdown(crudo))
    revision = lectura.comprobar_con_capa(cuerpo, capa)
    palabras = len(capa.split())
    digital = palabras >= 20
    frags = lectura.fichas([g]) if solo != "modelo" else []      # el PDF entero: unir filas necesita páginas seguidas
    ficha = next((x for x in frags if x["pagina"] == n), None)
    partida = alias == "informe" and n in (7, 8)

    c.rule(f"[bold]--capas {alias} {n} · qué hace PaddleOCR solo y qué hace nuestro código · lecturas guardadas[/]")
    c.print(Panel(f"PDF digital: tiene capa de texto ({palabras} palabras). PyMuPDF la extrae, pero sin tablas ni "
                  "gráfico: no sirve como lectura, sí para COMPROBAR lo que lea un modelo." if digital else
                  "PDF escaneado: la página es una imagen y PyMuPDF no encuentra texto. Solo tenemos lo que lea un "
                  "modelo… y nada con qué comprobarlo.", title="1 · FUENTE", title_align="left"))
    if solo is None:
        pasos = Table(box=None, padding=(0, 1), header_style="bold")
        for col in ("paso", "quién", "qué hace", "verlo"):
            pasos.add_column(col, overflow="fold")
        pasos.add_row("0 · Preparar", Text("NOSOTROS", style="cyan"), "página → imagen (150 ppp); configurar PaddleOCR: GPU, "
                      "gráficos activados, conservar cabecera y pie", "08 · png(), modelo()")
        pasos.add_row("1 · Fuente", "PyMuPDF", f"{'digital' if digital else 'escaneada'}: {palabras} palabras en la capa de "
                      "texto", "")
        pasos.add_row("2 · OCR", Text("MODELO PP-OCRv6 (solo)", style="magenta"), "detecta líneas, las lee, confianza por "
                      "línea", "--solo-modelo")
        pasos.add_row("3 · Parser", Text("MODELO PaddleOCR-VL (solo)", style="magenta"), "maquetación → lee cada bloque → "
                      "Markdown; tablas en HTML; gráfico → tabla", "--solo-modelo")
        pasos.add_row("4 · Limpiar", Text("NUESTRO código (mecánico)", style="cyan"), "HTML → filas «| a | b |»; fuera "
                      "logo y nº de página; el pie, aparte", "--solo-reglas")
        pasos.add_row("5 · Reglas", Text("NUESTRO código (este formato)", style="cyan"), "código + versión y fecha del pie; "
                      "estado; «sustituye a»; unir la fila partida", "--solo-reglas")
        pasos.add_row("6 · Comprobar", Text("NUESTRO código", style="cyan"), "cifras leídas frente a la capa de texto → "
                      "«sin revisar» / SIN COMPROBAR", "--solo-reglas")
        pasos.add_row("7 · Ficha", Text("NUESTRO código", style="cyan"), "la ficha que 09_indice_junio.py lleva al índice",
                      "--solo-reglas")
        pasos.add_row("✓ · Validar", Text("PERSONAS (negocio)", style="yellow"), "¿las reglas describen el proceso real? "
                      "¿qué se acepta sin revisar?", "")
        c.print(pasos)

    # ---- 2-3 · Lo que hace PaddleOCR solo: la salida cruda, tal cual se guardó -----------------------------------------
    if solo in (None, "modelo"):
        if p.get("ocr"):
            lineas = p["ocr"]["lineas"]
            if alias == "escaneado":
                inicio = next((i for i, (t, _) in enumerate(lineas) if t == "Caja"), 0)
                lineas = lineas[inicio:inicio + 20]
            else:
                marcas = ("ENT-06-012", "tarde. La firma", "ENT-06-013", "T2 · Detalle", "TOTAL T2")
                indices = [i for i, (t, _) in enumerate(lineas) if any(m in t for m in marcas)]
                if indices:
                    lineas = lineas[max(0, min(indices) - 2):min(len(lineas), max(indices) + 6)]
            ocr_s = Text()
            for t, conf in lineas:
                ocr_s.append(f"{conf:.2f}".replace(".", ",") + "  ", style="red" if conf < .90 else "yellow" if conf < .97 else "green")
                ocr_s.append(t + "\n")
            c.print(Panel(ocr_s, title="2 · MODELO PP-OCRv6 · SALIDA CRUDA: líneas + confianza (extracto)", title_align="left"))
            if alias == "escaneado":
                c.print("[dim]«Caja / 1 / 6 / 6 / 0 / Sin incidencia»: lee cada línea, pero no sabe qué columna es cada número.[/]")
        if partida:
            # La tabla partida: las DOS filas crudas que importan (pág. 7 y pág. 8), pequeñas y legibles.
            for numero in (7, 8):
                pag = next((x for x in g["paginas"] if x["n"] == numero), None)
                filas = [f for t in re.findall(r"<table.*?</table>", pag["vl"]["markdown"], flags=re.S)
                         for f in re.findall(r"<tr[^>]*>.*?</tr>", t, flags=re.S)] if pag else []
                if numero == 7:
                    fila = next((f for f in filas if "ENT-06-012" in f), "(fila ENT-06-012 no encontrada)")
                    etiqueta = "ENT-06-012, con la observación cortada en «…turno de»"
                else:
                    fila = next((f for f in filas if re.search(r"<td[^>]*>\s*</td>\s*<td[^>]*>\s*</td>", f)),
                                "(fila vacía no encontrada)")
                    etiqueta = "cinco celdas vacías + «tarde. La firma…»"
                c.print(Panel(Syntax("<table>" + fila + "</table>", "html", word_wrap=True),
                              title=f"3 · MODELO PaddleOCR-VL · SALIDA CRUDA · pág. {numero}: {etiqueta}", title_align="left"))
            c.print("[dim]PaddleOCR-VL lee página a página: devuelve estas dos filas por separado. No las une ni sabe "
                    "que son la misma entrada.[/]")
        else:
            texto_raw = re.sub(r"<table.*?</table>", "[tabla HTML: en el panel siguiente]", crudo, flags=re.S)
            c.print(Panel(texto_raw[:2200], title="3 · MODELO PaddleOCR-VL · SALIDA CRUDA: Markdown (cabecera y pie "
                          "incluidos)", title_align="left"))
            for i, tabla in enumerate(tablas_crudas, 1):
                c.print(Panel(Syntax(tabla, "html", word_wrap=True),
                              title=f"3 · MODELO PaddleOCR-VL · SALIDA CRUDA · tabla HTML {i}/{len(tablas_crudas)}, sin tocar",
                              title_align="left"))
            if alias == "informe" and n == 4:
                if "68" in crudo:
                    c.print("[dim]El gráfico G1 sale como tabla porque activamos use_chart_recognition (por defecto, "
                            "PaddleOCR-VL lo deja como imagen).[/]")
                else:
                    c.print("[bold red]El modelo no devolvió valores del gráfico: lo dejó como imagen.[/]")
        c.print("[bold magenta]Hasta aquí, PaddleOCR solo.[/] [dim]Devuelve texto, tablas y confianzas; no sabe qué es "
                "un código, una versión, un estado ni que una fila sigue en otra página.[/]")

    # ---- 4-7 · Lo que hace nuestro código después (asistente/lectura.py) ----------------------------------------------
    if solo in (None, "reglas"):
        c.print("\n[bold cyan]LO QUE HACE NUESTRO CÓDIGO DESPUÉS (asistente/lectura.py)[/]")
        limpio = "\n\n".join(lectura.limpiar_markdown(t) for t in tablas_crudas) if tablas_crudas else "(no hay tablas)"
        c.print(Panel(f"{limpio}\n\n[bold]Pie, aparte (lleva código, versión y fecha):[/] {pie or '(ninguno)'}",
                      title="4 · LIMPIEZA nuestra (mecánica): HTML → filas «| a | b |»", title_align="left"))
        c.print("[dim]Mecánica: saca el texto de cada <td>/<th> y lo pone entre barras (colspan → celdas vacías), quita "
                "logotipo y número de página y guarda el pie. No interpreta columnas ni une páginas.[/]")
        reglas = []
        if ficha:
            reglas.append(f"[bold]Código y fecha[/] → {ficha['codigo'] or '—'} · {ficha['fecha'] or '—'}  "
                          f"[dim]({ficha['origen']['codigo']})[/]")
            reglas.append(f"[bold]Estado[/] → {ficha['estado']}  [dim]({ficha['origen']['estado']})[/]")
            if ficha.get("sustitucion_mencion"):
                reglas.append(f"[bold]Versiones[/] → la pág. 1 dice «{ficha['sustitucion_mencion']}»: código Y versión "
                              f"coinciden → SUSTITUIDO por {ficha['sustituido_por']}  [dim](la versión entra en la clave)[/]")
        if partida:
            fila = next((l for x in frags if x["pagina"] == 7 for l in x["texto"].splitlines()
                         if l.startswith("|") and "ENT-06-012" in l), "")
            reglas.append("[bold]Fila partida[/] → la pág. 8 empieza con una fila sin registro (celdas vacías): es la cola "
                          "de la ÚLTIMA fila de la pág. 7 (ENT-06-012) y se pega ahí. La nota (1) del propio informe lo "
                          "dice: «Las casillas vacías en una continuación pertenecen a la misma observación…».")
            if fila:
                reglas.append(f"\n[green]{fila}[/]")
        c.print(Panel("\n".join(reglas) or "(sin ficha)", title="5 · REGLAS nuestras de ESTE formato (no las sabe "
                      "ningún lector)", title_align="left"))
        c.print(Panel(lectura.resumen_revision(revision) + ("" if revision["comprobable"] else
                      "\nNo hay capa de texto: nadie ha comprobado estas cifras. Por eso la ficha dice «sin revisar»."),
                      title="6 · COMPROBACIÓN nuestra: cifras leídas frente a la capa de texto del PDF", title_align="left"))
        if ficha:
            t = Table(title="7 · FICHA que 09_indice_junio.py lleva al índice (cada campo, con su procedencia)",
                      title_justify="left", header_style="bold")
            for col in ("campo", "valor", "de dónde sale"):
                t.add_column(col, overflow="fold")
            for k in ("titulo", "codigo", "fecha", "estado", "responsable", "lectura"):
                t.add_row(k, str(ficha.get(k) or "—"), str((ficha.get("origen") or {}).get(k, "regla de lectura.py")))
            c.print(t)
            c.print("[dim]Ningún modelo devuelve esta ficha: la construye nuestro código con reglas escritas para estos "
                    "dos PDF. Funcionan aquí; en otro formato hay que escribirlas de nuevo, probarlas y medirlas.[/]")
    if solo is None:
        c.print(Panel("PaddleOCR LEE: líneas, tablas y gráfico (pasos 2-3). Lo demás es NUESTRO código: limpiar, poner la "
                      "ficha, unir la fila partida, resolver versiones y comprobar (4-7). Que esas reglas describan el "
                      "proceso real lo confirma una persona de negocio. Y lo que no se ha podido comprobar, se dice.",
                      title="Idea para explicar", border_style="green"))


def comparar() -> None:
    filas = []
    for alias in lectura.ALIAS:
        g = lectura.lectura_guardada(alias)
        for forma in FORMAS:
            ps = [p for p in g["paginas"] if forma == "texto" or p.get(forma)]
            if not ps:
                continue
            seg = [p[forma]["segundos"] for p in ps] if forma != "texto" else [p.get("texto_segundos", 0) for p in ps]
            if forma == "texto":
                rev = [lectura.comprobar_con_capa(p["capa_texto"], p["capa_texto"]) for p in ps]
                nota = (f"{sum(len(p['capa_texto'].split()) for p in ps)} palabras · tablas celda a celda · sin G1" if alias == "informe" else "0 palabras: no hay texto que extraer")
            elif forma == "ocr":
                conf = [s for p in ps for _, s in p["ocr"]["lineas"]]
                nota = f"{len(conf)} líneas · confianza media {sum(conf) / len(conf):.3f} (mín. {min(conf):.2f}) · sin tablas"
            else:
                textos = [lectura.sin_cabecera_ni_pie(lectura.limpiar_markdown(p[forma]["markdown"]))[0] for p in ps]
                rev = [lectura.comprobar_con_capa(t, p["capa_texto"]) for t, p in zip(textos, ps)]
                comp = [x for x in rev if x["comprobable"]]
                nota = (f"{sum(x['en_capa'] for x in comp)}/{sum(x['cifras'] for x in comp)} valores en la capa de texto"
                        if comp else "sin capa de texto: nada que comprobar")
                tablas = sum(t.count("\n|") > 2 for t in textos)
                nota += f" · {tablas} pág. con tablas" if tablas else " · sin tablas"
                if alias == "informe":
                    g1 = any(p["n"] == 4 and "68" in t for t, p in zip(textos, ps))
                    nota += " · G1: 12/12" if g1 else " · G1: no aparece (0/12)"
            filas.append((alias, forma, f"{len(ps)}", f"{sum(seg):.1f}", f"{sum(seg) / len(ps):.1f}", nota))
        cargas = g.get("carga", {})
    t = Table(title=f"Lecturas guardadas · {g.get('equipo', '')}", title_justify="left", header_style="bold")
    for col in ("documento", "forma", "págs.", "segundos", "s/pág.", "resultado"):
        t.add_column(col, overflow="fold")
    for f in filas:
        t.add_row(*f)
    c.print(t)
    c.print(f"[dim]Carga de los modelos (una vez por proceso): {', '.join(f'{k} {v} s' for k, v in cargas.items())}.[/]")


# ---------------------------------------------------------------------------
# Guardar todas las lecturas (en el Jetson, con .venv-ocr)
# ---------------------------------------------------------------------------

def equipo() -> str:
    modo = shutil.which("nvpmodel") and subprocess.run(["nvpmodel", "-q"], capture_output=True, text=True).stdout.split("\n")[0]
    return f"Jetson AGX Orin · {modo.replace('NV Power Mode: ', '')}" if modo else os.uname().machine


def guardar(solo: str | None, vlm_todas: bool) -> None:
    lectura.LECTURAS.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    leer_ocr("escaneado", 1)                             # calentar: la primera inferencia en la GPU compila kernels
    leer_vl("escaneado", 1)
    carga = {"PP-OCRv6": _MODELOS["ocr_carga"], "PaddleOCR-VL": _MODELOS["vl_carga"]}
    for alias in ([solo] if solo else lectura.ALIAS):
        salida = {"pdf": lectura.ALIAS[alias], "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "equipo": equipo(),
                  "modelos": {"ocr": "PP-OCRv6_medium (PaddleOCR 3.7, motor transformers, GPU)",
                              "vl": "PaddleOCR-VL-1.6 0.9B (motor transformers, GPU)", "vlm": config.MODELO_VISION},
                  "carga": carga, "paginas": []}
        for p in paginas(alias):
            n = p["n"]
            tx = leer_texto(alias, n)
            pag = {"n": n, "clase": p["clase"], "capa_texto": tx["texto"], "texto_segundos": tx["segundos"]}
            pag["ocr"] = leer_ocr(alias, n)
            pag["vl"] = leer_vl(alias, n)
            if vlm_todas or (alias, n) in (("escaneado", 2), ("informe", 4)):
                pag["vlm"] = leer_vlm(alias, n)
            c.print(f"{alias} pág. {n}: ocr {pag['ocr']['segundos']} s · vl {pag['vl']['segundos']} s"
                    + (f" · vlm {pag['vlm']['segundos']} s" if pag.get("vlm") else ""))
            salida["paginas"].append(pag)
        ruta = lectura.LECTURAS / f"{alias}.json"
        ruta.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
        c.print(f"[green]Guardado {ruta.relative_to(config.ROOT)}[/]")
    c.print(f"Total {time.time() - t0:.0f} s")


def main() -> None:
    ap = argparse.ArgumentParser(description="Leer los PDF de junio de cuatro formas y compararlas.")
    ap.add_argument("--antes", action="store_true", help="El lector de PDF de la sesión 2 con estos documentos.")
    ap.add_argument("--leer", nargs=2, metavar=("DOC", "PAG"), help="Leer una página: informe|escaneado y su número.")
    ap.add_argument("--con", choices=FORMAS, default="vl", help="Cómo leerla (por defecto, vl).")
    ap.add_argument("--guardada", action="store_true", help="Enseñar la lectura guardada (sin modelos).")
    ap.add_argument("--comparar", action="store_true", help="Tiempos y comprobaciones de las lecturas guardadas.")
    ap.add_argument("--capas", nargs=2, metavar=("DOC", "PAG"), help="Qué hace PaddleOCR solo (salida cruda) y qué hace nuestro código después (con --guardada).")
    capas_vista = ap.add_mutually_exclusive_group()
    capas_vista.add_argument("--solo-modelo", action="store_true", help="Con --capas: solo la salida cruda de PP-OCRv6 y PaddleOCR-VL.")
    capas_vista.add_argument("--solo-reglas", action="store_true", help="Con --capas: solo nuestro código (limpieza, reglas, comprobación y ficha).")
    ap.add_argument("--grafico", action="store_true", help="EXTRA: solo el gráfico G1, a un VLM, frente a los valores reales.")
    ap.add_argument("--modelo", default=config.MODELO_VISION, help="VLM para --grafico y --con vlm (por defecto, el de config).")
    ap.add_argument("--guardar", action="store_true", help="Leer todo y guardarlo (Jetson, .venv-ocr).")
    ap.add_argument("--solo", choices=list(lectura.ALIAS), help="Con --guardar: un solo documento.")
    ap.add_argument("--vlm-todas", action="store_true", help="Con --guardar: también el VLM general en todas las páginas.")
    a = ap.parse_args()
    global ARGS_MODELO
    ARGS_MODELO = a.modelo
    if a.grafico:
        grafico(a.modelo)
    elif a.capas:
        vista = "modelo" if a.solo_modelo else "reglas" if a.solo_reglas else None
        capas(lectura.alias_de(a.capas[0]), int(a.capas[1]), a.guardada, vista)
    elif a.guardar:
        guardar(a.solo, a.vlm_todas)
    elif a.antes:
        antes()
    elif a.leer:
        alias, n = lectura.alias_de(a.leer[0]), int(a.leer[1])
        if not re.fullmatch(r"\d+", a.leer[1]) or not 1 <= n <= len(paginas(alias)):
            raise SystemExit(f"{alias} tiene {len(paginas(alias))} páginas.")
        mostrar(alias, n, a.con, a.guardada)
    elif a.comparar:
        comparar()
    else:
        mapa()


if __name__ == "__main__":
    main()
