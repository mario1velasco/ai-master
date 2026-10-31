"""Documentos difíciles: del PDF de junio (tablas, gráfico, escaneado) a fragmentos con ficha para el RAG.

Una página se puede leer de cuatro formas (08_leer_documentos.py las compara, medidas en el Jetson):

    capa de texto   pymupdf: el texto que lleva dentro un PDF digital. Exacto y gratis, pero sin
                    estructura (una tabla sale celda a celda) y vacío si la página es una imagen.
    OCR clásico     PP-OCRv6 (PaddleOCR) en la GPU: detecta líneas de texto en la imagen y las reconoce,
                    con una confianza por línea. Rápido (~2 s/página); no sabe qué es una tabla.
    parser de       PaddleOCR-VL-1.6 (0,9 B) en la GPU: detecta la maquetación (título, tabla, gráfico,
    documentos      pie…) y un VLM pequeño especializado lee cada bloque → Markdown con tablas (~25 s/pág.).
    VLM general     qwen3-vl:8b-instruct (Ollama): le pedimos la transcripción. Lee bien, pero es el modelo
                    grande para todo (~30 s/página) y no da cajas ni confianza.

Aquí está lo que NO depende de PaddleOCR (funciona en el .venv del curso): limpiar el Markdown de la lectura,
comprobar sus cifras contra la capa de texto y poner a cada página su ficha con reglas de este formato.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from . import config

DOCUMENTOS = config.ROOT / "data" / "documentos_junio"           # carpeta aparte: no toca el corpus de la sesión 2
LECTURAS = config.GUARDADAS / "documentos"                       # lecturas guardadas (08_leer_documentos.py --guardar)
ALIAS = {"informe": "01_DropLab_informe_reposicion_junio.pdf", "escaneado": "02_DropLab_expediente_escaneado.pdf"}
LECTOR = "PaddleOCR-VL-1.6"


def ruta_documento(alias: str) -> Path:
    nombre = ALIAS.get(alias, alias)
    ruta = DOCUMENTOS / nombre
    if not ruta.exists():
        raise SystemExit(f"No encuentro {nombre} en {DOCUMENTOS.relative_to(config.ROOT)}. Alias: {', '.join(ALIAS)}")
    return ruta


def alias_de(nombre: str) -> str:
    return next((a for a, n in ALIAS.items() if n == nombre or a == nombre or a in nombre), nombre)


def lectura_guardada(alias: str) -> dict:
    ruta = LECTURAS / f"{alias_de(alias)}.json"
    if not ruta.exists():
        raise SystemExit(f"Falta {ruta.relative_to(config.ROOT)}: .venv-ocr/bin/python practica/sesion_3/08_leer_documentos.py --guardar")
    return json.loads(ruta.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Del Markdown de PaddleOCR-VL a texto para el RAG
# ---------------------------------------------------------------------------

def _celdas(fila: str) -> list[str]:
    """Celdas de una fila HTML → columnas Markdown. Expande colspan con celdas vacías (regla nuestra)."""
    salida = []
    for m in re.finditer(r"<(?:td|th)(?P<attrs>[^>]*)>(?P<texto>.*?)</(?:td|th)>", fila, flags=re.S):
        celda = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m["texto"]).replace("\\n", " "))).strip()
        span = re.search(r"\bcolspan\s*=\s*[\"']?(\d+)", m["attrs"], flags=re.I)
        cantidad = int(span[1]) if span else 1
        salida.append(celda)
        salida.extend([""] * (cantidad - 1))
    return salida


def tabla_a_texto(tabla_html: str) -> str:
    """Una tabla HTML (como la devuelve PaddleOCR-VL) → filas «| a | b |». Menos tokens y se lee igual."""
    filas = [_celdas(f) for f in re.findall(r"<tr[^>]*>(.*?)</tr>", tabla_html, flags=re.S)]
    return "\n".join("| " + " | ".join(f) + " |" for f in filas if any(f))


NOTA = re.compile(r"\$\s*([^$]*?)\s*\^\{+(\w+)\}+\s*\$")         # «$ Aceptados^{{1}} $» → «Aceptados (1)»
RUIDO = re.compile(r"^(DROP LAB|OPERACIONES / ABASTECIMIENTO|\d+ ?/ ?\d+)$")


def limpiar_markdown(md: str) -> str:
    """Markdown de la lectura → texto: tablas en filas, notas al pie legibles, sin imágenes ni comentarios."""
    md = re.sub(r"<table.*?</table>", lambda m: "\n" + tabla_a_texto(m.group()) + "\n", md, flags=re.S)
    md = re.sub(r"<div[^>]*>\s*<img[^>]*>\s*</div>|<img[^>]*>|<!--.*?-->", "", md, flags=re.S)
    md = NOTA.sub(lambda m: (m[1] + " " if m[1] else "") + f"({m[2]})", md)
    md = md.replace("\\n", " ")
    lineas = [l.strip() for l in md.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lineas)).strip()


def sin_cabecera_ni_pie(texto: str) -> tuple[str, str]:
    """Quita logotipo, banda y número de página; devuelve (cuerpo, pie). El pie lleva el código: se guarda aparte."""
    pie, cuerpo = "", []
    for l in texto.splitlines():
        if l.startswith("Uso interno |"):
            pie = l
        elif not RUIDO.match(l):
            cuerpo.append(l)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(cuerpo)).strip(), pie


# ---------------------------------------------------------------------------
# Comprobar la lectura con la capa de texto (solo es posible si el PDF es digital)
# ---------------------------------------------------------------------------

CIFRA = re.compile(r"\d+(?:[.,]\d+)*")


def cifras(texto: str) -> list[str]:
    """Los valores numéricos DISTINTOS de un texto (de dos o más dígitos: sin notas al pie ni números de lista)."""
    return list(dict.fromkeys(c for c in CIFRA.findall(texto) if len(re.sub(r"\D", "", c)) >= 2))


def comprobar_con_capa(lectura: str, capa: str) -> dict:
    """¿Cada valor leído está en el texto que lleva dentro el PDF? Si no hay capa de texto, no se puede comprobar.

    Se cuentan valores distintos (un 96 que sale dos veces cuenta una) y conviene pasar la lectura sin cabecera ni pie
    (sin_cabecera_ni_pie), para contar igual en 08, 09 y la ficha."""
    leidas = cifras(lectura)
    if len(capa.split()) < 20:
        return {"comprobable": False, "cifras": len(leidas), "en_capa": 0, "solo_en_lectura": leidas}
    en_capa = set(cifras(capa))
    solo = [c for c in leidas if c not in en_capa]
    return {"comprobable": True, "cifras": len(leidas), "en_capa": len(leidas) - len(solo), "solo_en_lectura": solo}


def resumen_revision(r: dict) -> str:
    if not r["comprobable"]:
        return f"escaneada, sin capa de texto: {r['cifras']} valores SIN COMPROBAR"
    if not r["solo_en_lectura"]:
        return f"{r['en_capa']}/{r['cifras']} valores coinciden con la capa de texto"
    return (f"{r['en_capa']}/{r['cifras']} valores en la capa de texto; {len(r['solo_en_lectura'])} solo en la imagen "
            f"(SIN COMPROBAR): {', '.join(r['solo_en_lectura'])}")


# ---------------------------------------------------------------------------
# Reglas de preparación definidas por nosotros para ESTE informe (no son PaddleOCR)
# ---------------------------------------------------------------------------

def fila_inicio_sin_registro(texto: str) -> tuple[str, str] | None:
    """Detecta la cola de una fila de tabla que comienza en otra página. Devuelve (fila completa, cola)."""
    m = re.search(r"^\|(?:\s*\|){2,}\s*(?P<cola>[^|]+?)\s*\|$", texto, flags=re.M)
    return (m.group(), m["cola"]) if m else None


def unir_fila_partida(texto_anterior: str, texto_siguiente: str) -> tuple[str, str, str] | None:
    """Regla de este formato: la cola sin registro de la página siguiente completa la última fila de la anterior.

    No la aplica PaddleOCR-VL; la aplica nuestra lógica, porque conocemos la estructura de T2.
    Devuelve (texto anterior actualizado, texto siguiente actualizado, explicación) o None.
    """
    cola = fila_inicio_sin_registro(texto_siguiente)
    filas = [l for l in texto_anterior.splitlines() if l.startswith("|")]
    if not cola or not filas:
        return None
    fila, final = cola
    ultima = filas[-1]
    actualizada = ultima[:-1].rstrip() + " " + final + " |"
    ant = texto_anterior.replace(ultima, actualizada, 1)
    sig = texto_siguiente.replace(fila, "", 1).strip()
    explicacion = f"La fila sin registro de la pág. siguiente completa {actualizada.split('|')[1].strip()}."
    return ant, sig, explicacion


def ficha_base(pie: str) -> dict:
    """Regla local: sacar referencia/código y fecha del pie «Uso interno | … | dd/mm/aaaa»."""
    m = PIE.search(pie)
    if not m:
        return {"codigo": "", "version": "", "fecha": "", "regla": "sin pie reconocible"}
    ref = m["ref"]
    if re.match(r"[A-Z]{3}-\d{4}-\d{2} v", ref):
        partes = ref.split(" / ")[0].split()
        return {"codigo": partes[0], "version": partes[1], "fecha": m["fecha"],
                "regla": "pie → primera referencia + versión + fecha"}
    registro = ref.split(" / ")[-1]
    return {"codigo": registro, "version": "", "fecha": m["fecha"],
            "regla": "pie → último identificador (registro de esta página) + fecha"}


def estado_pagina(texto: str) -> tuple[str, str]:
    """Regla local: estado explícito de página (BORRADOR, APROBADO, ABIERTA, RECIBIDO)."""
    estado = next((e for k, e in ESTADOS if re.search(rf"\b{k}", texto)), "sin estado")
    return estado, "buscar en el texto de la propia página"


def sustituir_version(codigo: str, version: str, menciona_sustitucion: str, codigo_vigente: str) -> dict | None:
    """Regla local: versión + mención «sustituye a» → etiqueta de sustituido."""
    m = SUSTITUYE.search(menciona_sustitucion)
    if m and codigo == m["codigo"] and version == m["version"]:
        return {"estado": "sustituido", "sustituido_por": codigo_vigente, "mencion": m.group()}
    return None


# ---------------------------------------------------------------------------
# La ficha de cada página: reglas de ESTE formato (como 10_corpus.py), no un parser universal
# ---------------------------------------------------------------------------

PIE = re.compile(r"Uso interno \| (?P<ref>.+?) \| (?P<fecha>\d{2}/\d{2}/\d{4})")
VERSION_PAGINA = re.compile(r"(?P<codigo>[A-Z]{3}-\d{4}-\d{2}) (?P<version>v\d+\.\d+) \| (?P<fecha>\d{2}/\d{2}/\d{4}) \| (?P<estado>[A-ZÁÉÍÓÚ]+)")
SUSTITUYE = re.compile(r"sustituye a (?P<codigo>[A-Z]{3}-\d{4}-\d{2}) (?P<version>v\d+\.\d+)", re.I)
ESTADOS = (("BORRADOR", "borrador"), ("APROBAD", "aprobado"), ("ABIERTA", "abierta (pendiente)"),
           ("RECIBIDO EN TIENDA", "registro"))


def _primera(patron: str, texto: str, grupo: int = 1) -> str:
    m = re.search(patron, texto, flags=re.M)
    return m[grupo].strip() if m else ""


def fichas(lecturas: list[dict]) -> list[dict]:
    """Una ficha por página de los PDF de junio. Cada campo dice de dónde sale (clave «origen»)."""
    salida = []
    for doc in lecturas:
        paginas = []
        for p in doc["paginas"]:
            texto, pie = sin_cabecera_ni_pie(limpiar_markdown(p["vl"]["markdown"]))
            paginas.append({"n": p["n"], "texto": texto, "pie": pie, "capa": p.get("capa_texto", ""),
                            "segundos": p["vl"]["segundos"]})
        # REGLA NUESTRA para T2 (no la salida del modelo): fila de continuación sin identificador → añadir a la anterior.
        for ant, pag in zip(paginas, paginas[1:]):
            unido = unir_fila_partida(ant["texto"], pag["texto"])
            if unido:
                ant["texto"], pag["texto"], explicacion = unido
                ant["union"] = f"{explicacion} Cola leída en pág. {pag['n']} y unida aquí."
                pag["union"] = f"La cola leída aquí se ha unido a la fila de pág. {ant['n']}."
        # Estado y versión del documento: los da la página de control (p. 1); una página con su propia línea
        # «CÓDIGO vX | fecha | ESTADO» (el anexo con el borrador) manda sobre ella.
        todo = "\n".join(p["texto"] for p in paginas)
        sust = SUSTITUYE.search(todo)
        for pag in paginas:
            n, texto = pag["n"], pag["texto"]
            base = ficha_base(pag["pie"])
            ref = PIE.search(pag["pie"])
            propia = VERSION_PAGINA.search(texto)
            origen = {}
            if ref and re.match(r"[A-Z]{3}-\d{4}-\d{2} v", ref["ref"]):           # informe con versión
                codigo = f"{base['codigo']} {base['version']}"                       # «LOG-2026-06 v1.1»
                origen["codigo"] = f"pie de página: «{pag['pie']}» (código + versión)"
            elif ref:                                                            # expediente: «REC-2026-0617 / A-0617-04»
                codigo = base["codigo"]
                origen["codigo"] = f"pie de página: «{pag['pie']}» (el registro de esta página)"
            else:
                codigo, origen["codigo"] = "", "no hay pie legible"
            fecha = ref["fecha"] if ref else ""
            origen["fecha"] = "pie de página" if ref else "—"
            estado_txt, regla_estado = estado_pagina(texto)
            origen["estado"] = regla_estado
            ficha = {"sustituido_por": None, "estado_documento": None, "sustitucion_deducida_de": None,
                     "sustitucion_mencion": None}
            if propia:
                codigo = f"{propia['codigo']} {propia['version']}"
                fecha = propia["fecha"]
                estado_txt = next((e for k, e in ESTADOS if propia["estado"].startswith(k)), propia["estado"].lower())
                origen["codigo"] = origen["fecha"] = origen["estado"] = f"línea de la propia página: «{propia.group()}»"
            elif codigo.startswith("LOG-"):
                ctrl = re.search(r"\| Código y estado \| (.+?) \|", todo)
                estado_txt = "aprobado" if ctrl and "APROBADO" in ctrl[1] else estado_txt
                origen["estado"] = f"página de control (p. 1): «{ctrl[1] if ctrl else '—'}»"
            sustituido = sustituir_version(codigo.split()[0] if " " in codigo else codigo,
                                           codigo.split()[1] if " " in codigo else "", todo,
                                           codigo_principal(paginas))
            if sust and sustituido:
                ficha.update({"sustituido_por": sustituido["sustituido_por"], "estado_documento": estado_txt,
                              "sustitucion_deducida_de": f"{doc['pdf']} · pág. 1",
                              "sustitucion_mencion": sustituido["mencion"]})
                estado_txt = "sustituido"
                origen["estado"] += f" → SUSTITUIDO: la pág. 1 dice «{sust.group()}» (la versión es parte de la clave)"
            titulo = _primera(r"^#+ (.+)$", texto) or _primera(r"^([A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ /]{6,})$", texto)
            seccion = _primera(r"^(\d\d / .+|ANEXO .+|[A-ZÁÉÍÓÚÑ ]{8,})$", texto)
            responsable = _primera(r"(?:Responsable de recepción|Responsable de seguimiento|Responsable|Aprobación)(?::| \|) ([^|.\n]+)", texto)
            origen["titulo"] = "primer título «#» de la página"
            origen["responsable"] = "«Responsable: …» o «Aprobación: …» en la página"
            if not titulo and salida and salida[-1]["fuente"] == doc["pdf"]:      # página sin título: sigue la anterior
                titulo, seccion = salida[-1]["titulo"] + " (continuación)", salida[-1]["seccion"]
                origen["titulo"] = f"la página no tiene título: es la continuación de la pág. {n - 1}"
            if not responsable and codigo.startswith("LOG-"):
                responsable = _primera(r"Responsable: ([^|.\n]+)", paginas[0]["texto"])
                origen["responsable"] = "la página no lo dice: el de la pág. 1 (responsable del documento)"
            revision = comprobar_con_capa(texto, pag["capa"])
            lectura = f"{LECTOR} · sin revisar · " + resumen_revision(revision)
            if pag.get("union"):
                lectura += " · " + pag["union"]
            salida.append({"fuente": doc["pdf"], "tipo": "pdf leído (PaddleOCR-VL)", "titulo": titulo, "codigo": codigo,
                           "seccion": seccion, "pagina": n, "fecha": fecha, "estado": estado_txt,
                           "responsable": responsable, "texto": texto, "lectura": lectura, **ficha,
                           "origen": {**origen, "lectura": "08_leer_documentos.py + comprobación con la capa de texto"},
                           "revision": revision})
    return salida


def codigo_principal(paginas: list[dict]) -> str:
    """El código + versión del documento vigente: el del pie de la primera página."""
    ref = PIE.search(paginas[0]["pie"]) if paginas else None
    return " ".join(ref["ref"].split(" / ")[0].split()[:2]) if ref else ""


def texto_indexado(f: dict) -> str:
    """Igual que en 10_corpus.py: una cabecera con documento, código, estado y fecha, para que el fragmento se entienda solo."""
    return f"{f['titulo']} ({f['codigo']}, {f['estado']}, {f['fecha']}) · {f['seccion']}\n{f['texto']}"
