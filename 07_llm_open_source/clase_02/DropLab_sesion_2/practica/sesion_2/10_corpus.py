"""RAG · paso 1: preparar el corpus. Leer las fuentes, trocearlas y ponerles una etiqueta.

Qué fuentes entran (y cuáles no):
  - Los archivos .md y .pdf que haya en data/documentos/ (en este paquete: 6 Markdown y 3 PDF).
  - La llamada del 07/04, transcrita con Whisper (07_transcribir.py).
  - docente/ no se recorre: allí están las respuestas. La allowlist docente del caso no se carga aquí.

Cómo se trocea (reglas específicas para el formato de este paquete, no parser universal):
  Markdown → secciones separadas por una línea que empieza exactamente «## »; si el cuerpo pasa 320 palabras,
              partir() agrupa piezas delimitadas por saltos de línea (no divide una línea larga).
  PDF      → una página como unidad inicial (cada página lleva código, estado y fecha); cuerpos largos pasan
              por la misma función de empaquetado por saltos de línea.
  Llamada  → dos turnos seguidos (pregunta y respuesta), con quién habla y en qué segundo

Cada fragmento lleva sus METADATOS, los que pide el Manual (pág. 7): documento, sección o
página, fecha, estado y responsable. El texto que se indexa empieza por una cabecera con el
documento y la sección: así el fragmento se entiende aunque llegue solo.

Si un documento contiene literalmente «sustituye a X», una regex de este caso marca los fragmentos con código X
como SUSTITUIDO antes de embeddings y guarda la cita/mención que disparó la regla. No valida por sí sola la
autoridad del documento ni resuelve toda clase de versiones.

Uso:
  python practica/sesion_2/10_corpus.py                       # el mapa: fuentes y fragmentos
  python practica/sesion_2/10_corpus.py --trocear calendario  # cómo se corta UNA fuente: antes y después
  python practica/sesion_2/10_corpus.py --trocear expediente  # (vale parte del nombre: llamada, aviso, manual…)
  python practica/sesion_2/10_corpus.py --ver 36              # ficha del borrador y origen de la inferencia
  python practica/sesion_2/10_corpus.py --lista               # todos los fragmentos, una línea cada uno
  python practica/sesion_2/10_corpus.py --html --abrir        # todo, visual, en el navegador
  python practica/sesion_2/10_corpus.py --llamada large-v3_canales_solo-voz.json   # otra transcripción

Aquí NO hay embeddings ni OCR: los PDF son digitales (el texto está dentro) y los vectores
se calculan en el paso siguiente (11_indice.py). Este paso solo lee, trocea y etiqueta.

Salida: practica/sesion_2/rag/corpus.jsonl (un fragmento por línea) y, con --html, rag/corpus.html
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
DOCS = ROOT / "data" / "documentos"
RAG = AQUI / "rag"
CORPUS = RAG / "corpus.jsonl"
TRANSCRIPCIONES = AQUI / "transcripciones"
RESPALDO_LLAMADA = ROOT / "experimentos" / "audio" / "transcripciones_openai_whisper" / "turbo_canales.json"
# La transcripción elegida para el RAG: turbo, por canales y solo voz (la que mejor salió al comparar).
# Sigue siendo automática: entra con ese estado y se puede cambiar con --llamada.
LLAMADA_PREFERIDA = TRANSCRIPCIONES / "turbo_canales_solo-voz.json"
MAX_PALABRAS = 320          # una sección/página larga se empaqueta por líneas; no parte una línea larga

NOMBRE = {"central": "Álex (Operaciones)", "tienda": "Dani (tienda Malasaña)", "mezcla": "Interlocutor"}


def palabras(texto: str) -> int:
    return len(texto.split())


def estado_normalizado(texto: str) -> str:
    t = texto.lower()
    for clave, valor in [("sustituido", "sustituido"), ("pendiente de aprobación", "borrador"), ("borrador", "borrador"),
                         ("aprobado", "aprobado"), ("vigente", "vigente"), ("emitido", "emitido"),
                         ("recibido", "recibido"), ("consolidado", "consolidado"), ("observado", "registro"),
                         ("registro", "registro"), ("referencia", "referencia"), ("pendiente", "pendiente")]:
        if clave in t:
            return valor
    return "vigente" if "versión" in t else "sin estado"      # con versión y sin estado: documento en vigor


def partir(texto: str) -> list[str]:
    """Empaqueta líneas en bloques hasta MAX_PALABRAS; no tokeniza frases ni parte una línea individual larga."""
    if palabras(texto) <= MAX_PALABRAS:
        return [texto]
    trozos, actual = [], ""
    for p in re.split(r"\n(?=\S)", texto):
        if actual and palabras(actual) + palabras(p) > MAX_PALABRAS:
            trozos.append(actual.strip())
            actual = ""
        actual += p + "\n"
    if actual.strip():
        trozos.append(actual.strip())
    return trozos


# ---------------------------------------------------------------------------
# Lectores
# ---------------------------------------------------------------------------


def leer_md(ruta: Path) -> list[dict]:
    texto = ruta.read_text(encoding="utf-8")
    lineas = texto.splitlines()
    titulo = lineas[0].lstrip("# ").replace("DropLab · ", "")
    cabecera = " · ".join(l for l in lineas[1:4] if l and not l.startswith("#"))   # « · » separa las líneas
    codigo = (re.search(r"Documento ([A-Z0-9-]+)", cabecera) or [None, ""])[1]
    fecha = (re.findall(r"\d{2}/\d{2}/\d{4}", cabecera) or [""])[0]
    responsable = (re.search(r"Responsable: ([^·.]+)", cabecera) or [None, ""])[1].strip()
    estado = estado_normalizado(cabecera)
    secciones = re.split(r"\n(?=## )", texto)
    frags = []
    for i, sec in enumerate(secciones):
        if i == 0:                                   # la cabecera: solo si tiene contenido propio
            cuerpo = "\n".join(l for l in sec.splitlines()[1:] if l.strip())
            nombre_sec = "Cabecera"
        else:
            nombre_sec = sec.splitlines()[0].lstrip("# ").strip()
            cuerpo = "\n".join(sec.splitlines()[1:]).strip()
        if not cuerpo or (i == 0 and palabras(cuerpo) < 25):
            continue
        for j, trozo in enumerate(partir(cuerpo)):
            frags.append({"fuente": ruta.name, "tipo": "documento", "titulo": titulo, "codigo": codigo,
                          "seccion": nombre_sec + (f" ({j + 1})" if j else ""), "pagina": None, "fecha": fecha,
                          "estado": estado, "responsable": responsable, "texto": trozo})
    return frags


def unir_lineas(lineas: list[str]) -> list[str]:
    """El PDF corta las frases al final de cada línea: se unen cuando la siguiente sigue la frase."""
    salida = []
    for l in lineas:
        if salida and not salida[-1].endswith((".", ":", ";", "?", "!", "»")) and (l[0].islower() or l[0] in "(«"):
            salida[-1] += " " + l
        else:
            salida.append(l)
    return salida


DESCARTE = {"DROP LAB": "logotipo", "COMERCIAL / DATOS / OPERACIONES": "banda superior"}


def ruido_pdf(linea: str, anterior: str = "") -> str | None:
    """Líneas que no son contenido: logotipo, bandas, pies y números de página. Devuelve el motivo.

    Ojo con limpiar de más: un «3» suelto puede ser un dato de una tabla. Solo es número de página
    si va justo detrás del pie «DropLab · …»."""
    if linea in DESCARTE:
        return DESCARTE[linea]
    if linea.startswith("DropLab | Uso interno") or re.fullmatch(r"DropLab · [\w ]+", linea):
        return "pie de página"
    if re.fullmatch(r"\d+ / \d+", linea) or (linea.isdigit() and re.fullmatch(r"DropLab · [\w ]+", anterior)):
        return "n.º de página"
    return None


def limpiar(lineas: list[str]) -> list[tuple[str, str | None]]:
    """Cada línea con su motivo de descarte (None = es contenido)."""
    return [(l, ruido_pdf(l, lineas[i - 1] if i else "")) for i, l in enumerate(lineas)]


def leer_pdf(ruta: Path) -> list[dict]:
    import pymupdf
    frags = []
    with pymupdf.open(ruta) as doc:
        for n, pagina in enumerate(doc, 1):
            lineas = [l.strip() for l in pagina.get_text().splitlines() if l.strip()]
            lineas = [l for l, motivo in limpiar(lineas) if not motivo]
            crudas = list(lineas)                    # antes de unir: para sacar bien el título
            lineas = unir_lineas(lineas)
            cab = next((l for l in lineas if l.count("|") >= 2), "")   # «CAM-2026-03-FINAL | APROBADO / V2 | 01/03/2026»
            if cab:
                codigo, estado_txt, fecha = [x.strip() for x in cab.split("|")[:3]]
                i = lineas.index(cab)
                seccion = lineas[i - 1] if i > 0 else ""
                k = crudas.index(cab)
                titulo = crudas[k + 1] if k + 1 < len(crudas) else ""
                if k + 2 < len(crudas) and len(crudas[k + 2].split()) <= 3 and crudas[k + 2][0].islower():
                    titulo += " " + crudas[k + 2]     # título en dos líneas («… para el / comité»)
                cuerpo = "\n".join(lineas[i + 1:])
            else:                                    # PDF sin cabecera por página (informe de logística):
                k = next((j for j, l in enumerate(lineas)  # la línea del código hace de cabecera
                          if re.search(r"[A-Z]{3}-[A-Z]{3}-\d{4}-\d{2}", l)), None)
                linea_cod = lineas[k] if k is not None else " ".join(lineas[:4])
                codigo = (re.search(r"([A-Z]{3}-[A-Z]{3}-\d{4}-\d{2})", linea_cod) or [None, ""])[1]
                estado_txt = linea_cod
                fecha = (re.findall(r"\d{2}/\d{2}/\d{4}", linea_cod) or [""])[0]
                titulo = lineas[k - 1] if k else lineas[0]
                seccion, cuerpo = "", "\n".join(lineas[k + 1:] if k is not None else lineas)
            responsable = (re.search(r"Responsable: ([^.]+)", cuerpo.replace("\n", " ")) or [None, ""])[1].strip()
            for j, trozo in enumerate(partir(cuerpo)):
                frags.append({"fuente": ruta.name, "tipo": "pdf", "titulo": titulo, "codigo": codigo,
                              "seccion": seccion + (f" ({j + 1})" if j else ""), "pagina": n, "fecha": fecha,
                              "estado": estado_normalizado(estado_txt), "responsable": responsable, "texto": trozo})
    return frags


def transcripcion_llamada(elegida: Path | None = None) -> tuple[Path | None, str]:
    """Qué transcripción entra: la indicada con --llamada, la preferida, la última de 07 o la de respaldo."""
    if elegida is not None:
        ruta = elegida if elegida.is_absolute() else (TRANSCRIPCIONES / elegida if (TRANSCRIPCIONES / elegida).exists()
                                                      else Path.cwd() / elegida)
        if not ruta.exists():
            raise SystemExit(f"No existe la transcripción {elegida}. Disponibles: "
                             + ", ".join(p.name for p in sorted(TRANSCRIPCIONES.glob("*.json"))))
        return ruta, "elegida con --llamada"
    if LLAMADA_PREFERIDA.exists():
        return LLAMADA_PREFERIDA, "turbo, por canales y solo voz (la elegida)"
    candidatos = sorted(TRANSCRIPCIONES.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if candidatos:
        return candidatos[-1], "la última de 07_transcribir.py"
    if RESPALDO_LLAMADA.exists():
        return RESPALDO_LLAMADA, "guardada de las pruebas (aún no has ejecutado 07)"
    return None, ""


def turnos_llamada(datos: dict) -> list[dict]:
    """Une los segmentos seguidos del mismo interlocutor: un turno = lo que dice uno hasta que habla el otro."""
    turnos = []
    for s in datos["segmentos"]:
        if turnos and turnos[-1]["quien"] == s["quien"] and s["inicio"] - turnos[-1]["fin"] < 1.5:
            turnos[-1]["fin"] = s["fin"]
            turnos[-1]["texto"] += " " + s["texto"]
        else:
            turnos.append({"quien": s["quien"], "inicio": s["inicio"], "fin": s["fin"], "texto": s["texto"]})
    return turnos


def leer_llamada(ruta: Path) -> list[dict]:
    """Turnos de la llamada, de dos en dos (pregunta y respuesta), con quién habla y cuándo.

    Ventana deslizante: el fragmento i lleva el turno anterior y el turno i. Cada turno aparece
    en dos fragmentos (solapamiento): así una respuesta nunca llega sin su pregunta."""
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    turnos = turnos_llamada(datos)
    frags = []
    for i in range(len(turnos)):
        par = turnos[max(0, i - 1):i + 1]
        texto = "\n".join(f"{NOMBRE[t['quien']]} [{mmss(t['inicio'])}]: {t['texto']}" for t in par)
        frags.append({"fuente": "llamada_0704", "tipo": "llamada", "titulo": "Llamada de Operaciones a la tienda de Malasaña",
                      "codigo": "LLAMADA-0704", "seccion": f"{mmss(par[0]['inicio'])}–{mmss(par[-1]['fin'])}",
                      "pagina": None, "fecha": "07/04/2026",
                      "estado": f"transcripción automática (Whisper {datos['modelo']}"
                                + (", solo voz" if datos.get("solo_voz") else "") + ")",
                      "responsable": NOMBRE[turnos[i]["quien"]], "inicio": par[0]["inicio"], "fin": par[-1]["fin"],
                      "quien": turnos[i]["quien"], "turnos": list(range(max(1, i), i + 2)), "texto": texto})
    return frags


def mmss(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------


def construir(llamada: Path | None = None) -> tuple[list[dict], str]:
    frags = []
    # El alcance se determina actualmente por carpeta y extensión, no por rag_allowlist.
    # Mantener docente/ fuera de DOCS; en producción, preferir una allowlist explícita y validada.
    for ruta in sorted(DOCS.iterdir()):
        if ruta.suffix == ".md":
            frags += leer_md(ruta)
        elif ruta.suffix == ".pdf":
            frags += leer_pdf(ruta)
    ruta_llamada, origen = transcripcion_llamada(llamada)
    if ruta_llamada:
        frags += leer_llamada(ruta_llamada)
        origen = f"{ruta_llamada.name} · {origen}"
    # La cita se prepara antes de relacionar versiones, para conservar la fuente explícita de la inferencia.
    for f in frags:
        donde = f"pág. {f['pagina']}" if f["pagina"] else f["seccion"]
        f["cita"] = f"{f['fuente']} · {donde}"
    # Regla literal de este caso: buscar «sustituye a CÓDIGO». No valida firma, autoridad ni fecha.
    sustituciones = {}
    for f in frags:
        for m in re.finditer(r"sustituye a ([A-Z0-9-]+)", f["texto"], re.IGNORECASE):
            codigo = m[1]
            sustituciones[codigo] = {"por": f["codigo"], "evidencia": f["cita"],
                                     "mencion": m[0]}
    for f in frags:
        relacion = sustituciones.get(f["codigo"])
        if relacion and f["codigo"] != relacion["por"]:
            if f["estado"] != "sustituido":
                f["estado_documento"] = f["estado"]      # lo que decía el propio documento (p. ej. «borrador»)
            f["estado"] = "sustituido"
            f["sustituido_por"] = relacion["por"]
            f["sustitucion_deducida_de"] = relacion["evidencia"]
            f["sustitucion_mencion"] = relacion["mencion"]
    for i, f in enumerate(frags):
        f["id"] = i
        # El texto que se indexa: cabecera de contexto + contenido
        f["texto_indexado"] = (f"{f['titulo']} ({f['codigo']}, {f['estado']}, {f['fecha']})"
                               + (f" · {f['seccion']}" if f["seccion"] else "") + f"\n{f['texto']}")
    return frags, origen


# ---------------------------------------------------------------------------
# Vistas: lo mismo que hace el código, pero para verlo
# ---------------------------------------------------------------------------

FORMATO = {"documento": "Markdown", "pdf": "PDF", "llamada": "Llamada"}
SE_TROCEA = {"documento": "una sección (## …)", "pdf": "una página", "llamada": "dos turnos (con solape)"}
COLORES = ["cyan", "yellow", "green", "magenta", "blue", "bright_red", "bright_cyan", "bright_yellow"]
ESTILO = {"titulo": "bold", "ficha": "bold magenta", "seccion": "bold", "descartada": "dim strike", "texto": "",
          "clave": "bold yellow"}


def clase_texto(linea: str) -> tuple[str, str, str]:
    """Una línea de texto normal… salvo si dice «sustituye a X»: de ahí sale el estado SUSTITUIDO de X."""
    m = re.search(r"sustituye a ([A-Z0-9-]+)", linea)
    return (linea, "clave", f"→ el código deduce: {m[1]} sustituido") if m else (linea, "texto", "")


def color_estado(estado: str) -> str:
    """Un color por tipo de estado: verde manda, rojo sustituido, morado automático, amarillo pendiente."""
    if estado in ("aprobado", "vigente"):
        return "green"
    if estado in ("sustituido", "borrador"):
        return "red"
    if estado.startswith("transcripción"):
        return "magenta"
    if estado == "pendiente":
        return "yellow"
    return "cyan"


def etiqueta_ficha(linea: str) -> str:
    """Qué metadatos salen de una línea de la cabecera de un Markdown."""
    partes = [n for n, patron in [("código", r"Documento [A-Z]"), ("versión", r"Versión"), ("estado", r"Estado|Recibido|Consolidado|Vigente"),
                                   ("fecha", r"\d{2}/\d{2}/\d{4}"), ("responsable", r"Responsable")]
              if re.search(patron, linea)]
    return "→ ficha: " + ", ".join(partes) if partes else "→ cabecera"


def regiones_md(ruta: Path, frags: list[dict]) -> list[dict]:
    """El Markdown tal cual, partido igual que en leer_md, con cada línea clasificada."""
    regiones = []
    for i, sec in enumerate(re.split(r"\n(?=## )", ruta.read_text(encoding="utf-8"))):
        lineas = [l for l in sec.splitlines() if l.strip()]
        if i == 0:
            nombre = "Cabecera"
            clas = [(lineas[0], "titulo", "→ título")] + [(l, "ficha", etiqueta_ficha(l)) for l in lineas[1:]]
        else:
            nombre = lineas[0].lstrip("# ").strip()
            clas = [(lineas[0], "seccion", "→ sección")] + [clase_texto(l) for l in lineas[1:]]
        ids = [f["id"] for f in frags if f["seccion"] == nombre or f["seccion"].startswith(nombre + " (")]
        nota = ("cabecera: de aquí sale la ficha" if i == 0 and not ids else
                "cabecera: ficha y, por ser larga, también fragmento" if i == 0 else f"sección «{nombre}»")
        regiones.append({"etiqueta": nota, "lineas": clas, "ids": ids})
    return regiones


def regiones_pdf(ruta: Path, frags: list[dict], imagenes: bool = False) -> list[dict]:
    """Cada página del PDF tal cual sale de pymupdf, con cada línea clasificada (y su imagen, para la web)."""
    import pymupdf
    regiones = []
    with pymupdf.open(ruta) as doc:
        for n, pagina in enumerate(doc, 1):
            crudas = [l.strip() for l in pagina.get_text().splitlines() if l.strip()]
            fs = [f for f in frags if f["pagina"] == n]
            f0 = fs[0] if fs else {}
            limpias = limpiar(crudas)
            utiles = [l for l, motivo in limpias if not motivo]
            k = next((j for j, l in enumerate(utiles) if l.count("|") >= 2), None)
            papel = {}
            if k is not None:
                papel[k] = ("ficha", "→ ficha: código | estado | fecha")
                if k > 0:
                    papel[k - 1] = ("seccion", "→ sección")
                papel[k + 1] = ("titulo", "→ título")
                if k + 2 < len(utiles) and len(utiles[k + 2].split()) <= 3 and utiles[k + 2][0].islower():
                    papel[k + 2] = ("titulo", "→ título (2.ª línea)")
            else:
                for j, l in enumerate(utiles):
                    if f0.get("codigo") and f0["codigo"] in l:
                        papel[j] = ("ficha", "→ ficha: código, estado y fecha")
                    elif l == f0.get("titulo"):
                        papel[j] = ("titulo", "→ título")
            clas, j = [], 0
            for l, motivo in limpias:
                if motivo:
                    clas.append((l, "descartada", f"✗ se quita: {motivo}"))
                else:
                    clas.append((l, *papel[j]) if j in papel else clase_texto(l))
                    j += 1
            texto = [l for l, c, _ in clas if c in ("texto", "clave")]
            png = pagina.get_pixmap(dpi=60).tobytes("png") if imagenes else None
            regiones.append({"etiqueta": f"página {n}", "lineas": clas, "ids": [f["id"] for f in fs], "png": png,
                             "unidas": (len(texto), len(unir_lineas(texto)))})
    return regiones


def tarjeta(f: dict, color: str, max_lineas: int = 4):
    """Un fragmento como tarjeta: su ficha arriba y el texto que se indexa debajo."""
    from rich.panel import Panel
    from rich.text import Text
    t = Text()
    t.append("código ", "dim")
    t.append(f["codigo"], "bold")
    t.append("  ·  estado ", "dim")
    t.append(f["estado"], f"bold {color_estado(f['estado'])}")
    if f.get("sustituido_por"):
        t.append(f" → {f['sustituido_por']}", color_estado(f["estado"]))
    t.append("  ·  fecha ", "dim")
    t.append(f["fecha"])
    if f["responsable"]:
        t.append("  ·  responsable ", "dim")
        t.append(f["responsable"])
    t.append(f"  ·  {palabras(f['texto'])} palabras\n", "dim")
    cab, _, cuerpo = f["texto_indexado"].partition("\n")
    t.append("cabecera ▸ ", "dim cyan")
    t.append(cab + "\n", "bold cyan")
    lineas = cuerpo.splitlines()
    vistas = ["           " + (l if len(l) < 105 else l[:104] + "…") for l in lineas[:max_lineas]]
    t.append("\n".join(vistas))
    resto = len(lineas) - max_lineas
    if resto > 0:
        t.append(f"\n           … (+{resto} línea{'s' if resto > 1 else ''}; todo: --ver {f['id']})", "dim")
    return Panel(t, title=f"[bold {color}]fragmento #{f['id']}[/] · {f['cita']}", title_align="left",
                 border_style=color)


def buscar_fuente(nombre: str, frags: list[dict]) -> str:
    fuentes = list(dict.fromkeys(f["fuente"] for f in frags))
    hay = [x for x in fuentes if nombre.lower() in x.lower()]
    if len(hay) != 1:
        raise SystemExit(f"«{nombre}» {'no coincide con ninguna' if not hay else 'coincide con varias'} fuente. "
                         f"Elige una de: {', '.join(fuentes)}")
    return hay[0]


def vista_resumen(c, frags: list[dict], origen: str) -> None:
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    fuentes = list(dict.fromkeys(f["fuente"] for f in frags))
    c.print(Panel(Text.assemble((f"{len(fuentes)} fuentes", "bold"), "  →  ✂ trocear  →  🏷  etiquetar  →  ",
                                (f"{len(frags)} fragmentos", "bold"), "  →  ", (str(CORPUS.relative_to(ROOT)), "cyan")),
                  title="[bold]RAG · paso 1 · preparar el corpus[/]", border_style="cyan", expand=False))
    t = Table(header_style="bold", box=None, padding=(0, 2))
    t.add_column("Fuente", no_wrap=True, style="bold")
    for col in ("Formato", "Un fragmento =", "Fragmentos (■ = 1)", "Palabras", "Estado"):
        t.add_column(col, no_wrap=col != "Estado")
    for fuente in fuentes:
        g = [f for f in frags if f["fuente"] == fuente]
        cuadros = Text()
        for f in g:
            cuadros.append("■ ", color_estado(f["estado"]))
        cuadros.append(f" {len(g)}", "bold")
        distintos = list(dict.fromkeys(f["estado"] for f in g))
        estados = (Text(f"{len(distintos)} distintos: cada página es otro documento") if len(distintos) > 3 else
                   Text(", ").join(Text(e, color_estado(e)) for e in distintos))
        t.add_row(fuente, FORMATO[g[0]["tipo"]], SE_TROCEA[g[0]["tipo"]], cuadros,
                  str(sum(palabras(f["texto"]) for f in g)), estados)
    c.print(t)
    leyenda = Text("  Color del estado:  ")
    for nombre, col in [("aprobado / vigente", "green"), ("sustituido", "red"), ("registro, aviso, informe…", "cyan"),
                        ("pendiente", "yellow"), ("transcripción automática", "magenta")]:
        leyenda.append("■ ", col)
        leyenda.append(nombre + "   ")
    c.print(leyenda)
    if origen:
        c.print(f"  [dim]Llamada: {origen}.[/dim]")
    sust = sorted({f["codigo"] + " → " + f["sustituido_por"] for f in frags if f.get("sustituido_por")})
    if sust:
        c.print(f"  [red]Sustituido, deducido por el código:[/red] {', '.join(sust)} "
                "[dim](otro documento dice «sustituye a …»)[/dim]")
    c.print("  [dim]No entra nada de docente/: allí están las respuestas.[/dim]\n")
    c.print("[bold]Para verlo por dentro:[/bold]\n"
            "  [cyan]--trocear calendario[/]   cómo se corta un documento (prueba: expediente, llamada, aviso…)\n"
            "  [cyan]--ver 36[/]               la ficha del borrador y de dónde sale cada dato (lo deducido, en amarillo)\n"
            "  [cyan]--html --abrir[/]         todo el corpus en el navegador: original y fragmentos, lado a lado")


def vista_trocear(c, nombre: str, frags: list[dict], ruta_llamada: Path | None, todo: bool = False) -> None:
    from rich.text import Text
    fuente = buscar_fuente(nombre, frags)
    g = [f for f in frags if f["fuente"] == fuente]
    tipo = g[0]["tipo"]
    color_de = {f["id"]: COLORES[i % len(COLORES)] for i, f in enumerate(g)}
    c.rule(f"[bold]✂  Cómo se trocea {fuente}  ·  {FORMATO[tipo]} → {SE_TROCEA[tipo]} por fragmento")
    ancho = max(40, min(c.width - 44, 92))
    max_texto = 10_000 if todo else 4

    if tipo == "llamada":
        datos = json.loads(ruta_llamada.read_text(encoding="utf-8"))
        turnos = turnos_llamada(datos)
        quien_col = {"central": "cyan", "tienda": "yellow", "mezcla": "white"}
        c.print(f"\n[bold]ANTES · la transcripción[/] [dim]({ruta_llamada.name}): {len(turnos)} turnos[/]")
        for n, tu in enumerate(turnos, 1):
            texto = tu["texto"] if len(tu["texto"]) <= ancho else tu["texto"][:ancho - 1] + "…"
            c.print(Text.assemble(f"  T{n:<3}", (f"{mmss(tu['inicio']):>5} ", "dim"),
                                  (f"{NOMBRE[tu['quien']].split(' (')[0]:5} ", f"bold {quien_col[tu['quien']]}"), texto))
        c.print(f"\n[bold]DESPUÉS · {len(g)} fragmentos de dos turnos seguidos[/]  "
                "[dim](ventana deslizante: cada turno aparece en dos fragmentos)[/]")
        cab = Text("         ")
        for n in range(1, len(turnos) + 1):
            cab.append(f"T{n:<3}", "dim")
        c.print(cab)
        for f in g:
            fila = Text(f"  #{f['id']:<5}")
            for n in range(1, len(turnos) + 1):
                if n in f["turnos"]:
                    fila.append("██  ", quien_col[turnos[n - 1]["quien"]])
                else:
                    fila.append("·   ", "dim")
            fila.append(f["seccion"], "dim")
            c.print(fila)
        c.print("\n[bold]Tres fragmentos, con su ficha:[/] [dim](el resto: --ver N)[/]")
        for f in g[4:7]:
            c.print(tarjeta(f, color_de[f["id"]], max_texto))
        return

    regiones = regiones_md(DOCS / fuente, g) if tipo == "documento" else regiones_pdf(DOCS / fuente, g)
    c.print("\n[bold]ANTES · el archivo tal cual[/]  [dim](a la derecha, qué hace el código con cada línea)[/]")
    for r in regiones:
        col = color_de[r["ids"][0]] if r["ids"] else "white"
        destino = ", ".join(f"#{i}" for i in r["ids"]) or "ningún fragmento"
        c.print(Text.assemble("  ✂ ", (f"──── {r['etiqueta']} → {destino} ", f"bold {col}"),
                              (f"{'─' * max(0, ancho - len(r['etiqueta']) - len(destino) - 10)}", col)))
        mostradas = 0
        ocultas = max(0, sum(1 for _, cl, _ in r["lineas"] if cl == "texto") - max_texto)
        for l, clase, nota in r["lineas"]:
            if clase == "texto":
                mostradas += 1
                if mostradas == max_texto + 1:      # el aviso, en el sitio de las líneas que no se enseñan
                    c.print(Text.assemble(("  ▌ ", col), (f"… (+{ocultas} línea{'s' if ocultas > 1 else ''} de texto; "
                                                          "todas con --todo)", "dim")))
                if mostradas > max_texto:
                    continue
            texto = l if len(l) <= ancho else l[:ancho - 1] + "…"
            c.print(Text.assemble(("  ▌ ", col), (f"{texto:<{ancho}}", ESTILO[clase]),
                                  ("  " + nota, {"ficha": "magenta", "titulo": "magenta", "seccion": "magenta",
                                                 "clave": "bold yellow"}.get(clase, "dim"))))
        if r.get("unidas") and r["unidas"][0] != r["unidas"][1]:
            c.print(Text.assemble(("  ▌ ", col), (f"↳ {r['unidas'][0]} líneas del PDF → {r['unidas'][1]} frases: "
                                                  "se unen las que el PDF cortó a mitad", "italic dim")))
    c.print(f"\n[bold]DESPUÉS · {len(g)} fragmento{'s' if len(g) > 1 else ''}, cada uno con su ficha[/]  "
            "[dim](la cabecera en azul se pega delante del texto: así se entiende aunque llegue solo)[/]")
    for f in g:
        c.print(tarjeta(f, color_de[f["id"]], max_texto))


def vista_ficha(c, f: dict, total: int) -> None:
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    tipo = f["tipo"]
    origen = {
        "id": "lo numera el código (posición en el corpus)",
        "fuente": "el nombre del archivo",
        "tipo": "la extensión del archivo",
        "titulo": {"documento": "la primera línea (# …)", "pdf": "la línea bajo el código",
                   "llamada": "fijo en el código"}[tipo],
        "codigo": {"documento": "la cabecera: «Documento …»", "pdf": "la línea «CÓDIGO | ESTADO | FECHA»",
                   "llamada": "fijo en el código"}[tipo],
        "seccion": {"documento": "el título de la sección (## …)", "pdf": "el rótulo de la página",
                    "llamada": "minuto de inicio y de fin de los dos turnos"}[tipo],
        "pagina": "el número de página del PDF",
        "fecha": {"documento": "la primera fecha de la cabecera", "pdf": "la línea «CÓDIGO | ESTADO | FECHA»",
                  "llamada": "el día de la llamada"}[tipo],
        "estado": {"documento": "la cabecera (Estado / Versión / Recibido…)", "pdf": "la línea «CÓDIGO | ESTADO | FECHA»",
                   "llamada": "cómo se obtuvo: Whisper (no está revisada)"}[tipo],
        "sustituido_por": "DEDUCIDO por el código: otro documento dice «sustituye a …»",
        "sustitucion_deducida_de": "DEDUCIDO por una coincidencia literal; localización del texto «sustituye a …»",
        "sustitucion_mencion": "DEDUCIDO por coincidencia literal en el documento sustituto",
        "responsable": {"documento": "la cabecera: «Responsable: …»", "pdf": "el texto: «Responsable: …»",
                        "llamada": "quién habla en el último turno"}[tipo],
        "cita": "la construye el código: archivo + página o sección",
        "inicio": "los tiempos de Whisper (segundos)", "fin": "los tiempos de Whisper (segundos)",
        "quien": "el canal del audio (izquierdo = Álex, derecho = Dani)",
        "turnos": "qué turnos entran (ventana de dos)",
    }
    if f.get("estado_documento"):
        origen["estado"] = (f"DEDUCIDO por el código: el documento dice «{f['estado_documento']}», pero "
                            f"la fuente {f.get('sustitucion_deducida_de', f['sustituido_por'])} dice "
                            f"«{f.get('sustitucion_mencion', 'sustituye a ' + f['codigo'])}»")
    elif f["estado"] == "sustituido":
        origen["estado"] = "la línea «CÓDIGO | ESTADO | FECHA» (y el código lo confirma: «sustituye a …»)"
    origen["estado_documento"] = "lo que decía el propio documento, antes de la deducción"
    c.rule(f"[bold]🏷  La ficha del fragmento #{f['id']}  ·  {f['cita']}")
    t = Table(box=None, padding=(0, 2), header_style="bold")
    t.add_column("Campo (metadato)", style="bold")
    t.add_column("Valor")
    t.add_column("De dónde sale", style="dim")
    orden = ["id", "cita"] + [k for k in f if k not in ("id", "cita")]
    for k in orden:
        v = f[k]
        if k in ("texto", "texto_indexado") or v in (None, ""):
            continue
        valor = Text(str(v), color_estado(str(v)) if k == "estado" else ("red" if k == "sustituido_por" else ""))
        nota = origen.get(k, "")
        t.add_row(k, valor, Text(nota, "bold yellow") if nota.startswith("DEDUCIDO") else nota)
    c.print(t)
    cab, _, cuerpo = f["texto_indexado"].partition("\n")
    texto = Text()
    texto.append(cab + "\n", "bold cyan")
    texto.append(cuerpo)
    c.print(Panel(texto, title="Texto que se indexa: [bold cyan]cabecera de contexto[/] + contenido",
                  subtitle="esto es lo que el paso 11 convertirá en un vector", border_style="green",
                  title_align="left"))
    c.print("[dim]La ficha viaja con el fragmento: en el índice (paso 11) queda en columnas junto al vector.\n"
            f"En la nube sería igual: en Azure AI Search, campos filtrables del índice.   "
            f"Otros: --ver {max(0, f['id'] - 1)} · --ver {min(total - 1, f['id'] + 1)}[/dim]")


def abrir_en_navegador(ruta: Path) -> None:
    import webbrowser
    webbrowser.open(ruta.as_uri())


def main() -> None:
    ap = argparse.ArgumentParser(description="RAG · paso 1: trocear las fuentes y etiquetarlas.")
    ap.add_argument("--trocear", metavar="FUENTE", help="Ver cómo se corta una fuente (vale parte del nombre).")
    ap.add_argument("--todo", action="store_true", help="Con --trocear: enseñar todas las líneas.")
    ap.add_argument("--ver", type=int, help="La ficha completa de un fragmento y de dónde sale cada dato.")
    ap.add_argument("--lista", action="store_true", help="Enseñar todos los fragmentos (una línea cada uno).")
    ap.add_argument("--html", action="store_true", help="Crear rag/corpus.html: original y fragmentos, lado a lado.")
    ap.add_argument("--abrir", action="store_true", help="Con --html: abrir la página en el navegador.")
    ap.add_argument("--llamada", type=Path, help="Transcripción de la llamada (por defecto turbo_canales_solo-voz.json).")
    a = ap.parse_args()
    from rich.console import Console
    from rich.table import Table
    c = Console()

    frags, origen = construir(a.llamada)
    RAG.mkdir(exist_ok=True)
    with CORPUS.open("w", encoding="utf-8") as f:
        for x in frags:
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    ruta_llamada, _ = transcripcion_llamada(a.llamada)

    if a.ver is not None:
        if not 0 <= a.ver < len(frags):
            raise SystemExit(f"Hay {len(frags)} fragmentos: del 0 al {len(frags) - 1}.")
        vista_ficha(c, frags[a.ver], len(frags))
    elif a.trocear:
        vista_trocear(c, a.trocear, frags, ruta_llamada, a.todo)
    elif a.lista:
        t = Table(header_style="bold", box=None, padding=(0, 2))
        for col in ("id", "cita", "estado", "palabras"):
            t.add_column(col)
        for x in frags:
            t.add_row(str(x["id"]), x["cita"], f"[{color_estado(x['estado'])}]{x['estado']}[/]",
                      str(palabras(x["texto"])))
        c.print(t)
    elif a.html:
        sys.path.insert(0, str(AQUI))
        from corpus_html import generar
        regiones = {}
        for fuente in dict.fromkeys(f["fuente"] for f in frags):
            g = [f for f in frags if f["fuente"] == fuente]
            if g[0]["tipo"] == "documento":
                regiones[fuente] = regiones_md(DOCS / fuente, g)
            elif g[0]["tipo"] == "pdf":
                regiones[fuente] = regiones_pdf(DOCS / fuente, g, imagenes=True)
        turnos = turnos_llamada(json.loads(ruta_llamada.read_text(encoding="utf-8"))) if ruta_llamada else []
        destino = generar(frags, origen, regiones, turnos, RAG / "corpus.html")
        c.print(f"Página: [cyan]{destino.relative_to(ROOT)}[/]")
        if a.abrir:
            abrir_en_navegador(destino)
    else:
        vista_resumen(c, frags, origen)
    c.print(f"\n[dim]Guardado: {CORPUS.relative_to(ROOT)} ({len(frags)} fragmentos, uno por línea)[/dim]")


if __name__ == "__main__":
    main()
