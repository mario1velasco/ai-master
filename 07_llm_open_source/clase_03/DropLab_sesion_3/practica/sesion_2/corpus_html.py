"""Página web del corpus del RAG: cada fuente, ANTES (el original) y DESPUÉS (sus fragmentos con ficha).

No se ejecuta solo: lo usa `python practica/sesion_2/10_corpus.py --html --abrir`.

  - Arriba, el mapa: las 10 fuentes, con un cuadrado por fragmento (color = estado).
  - Por fuente, dos columnas: a la izquierda el original (Markdown por secciones, páginas del PDF
    con su imagen, o la llamada como chat) con las líneas que van a la ficha o se descartan;
    a la derecha, los fragmentos con su ficha y el texto que se indexará.
  - Al pasar el ratón por un fragmento se ilumina de dónde sale, y al revés.
"""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

PALETA = ["#3298B3", "#D98A0B", "#12907C", "#7A5BB5", "#D9475A", "#01415B", "#2BA89A", "#B5651D"]
FORMATO = {"documento": "Markdown", "pdf": "PDF", "llamada": "Llamada"}
SE_TROCEA = {"documento": "una sección (## …)", "pdf": "una página", "llamada": "dos turnos seguidos (con solape)"}
QUIEN = {"central": ("Álex", "Operaciones", "#3298B3"), "tienda": ("Dani", "tienda Malasaña", "#D98A0B"),
         "mezcla": ("?", "", "#8FA3AE")}
E = html.escape


def color_estado(estado: str) -> str:
    if estado in ("aprobado", "vigente"):
        return "#12907C"
    if estado in ("sustituido", "borrador"):
        return "#D9475A"
    if estado.startswith("transcripción"):
        return "#7A5BB5"
    if estado == "pendiente":
        return "#D98A0B"
    return "#3298B3"


def slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")


def mmss(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def tarjeta(f: dict, color: str) -> str:
    est = color_estado(f["estado"])
    chips = [f'<span class="chip">código <b>{E(f["codigo"])}</b></span>',
             f'<span class="chip estado" style="background:{est}">{E(f["estado"])}'
             + (f' → {E(f["sustituido_por"])}' if f.get("sustituido_por") else "") + "</span>",
             f'<span class="chip">fecha <b>{E(f["fecha"])}</b></span>']
    if f.get("responsable"):
        chips.append(f'<span class="chip">responsable <b>{E(f["responsable"])}</b></span>')
    chips.append(f'<span class="chip">{len(f["texto"].split())} palabras</span>')
    cab, _, cuerpo = f["texto_indexado"].partition("\n")
    return (f'<div class="frag" data-id="{f["id"]}" style="--c:{color}">'
            f'<div class="frag-cab"><span class="num">#{f["id"]}</span><span class="cita">{E(f["cita"])}</span></div>'
            f'<div class="chips">{"".join(chips)}</div>'
            f'<div class="idx"><div class="et">TEXTO QUE SE INDEXA</div>'
            f'<div class="cabecera"><span>cabecera ▸</span> {E(cab)}</div>'
            f'<div class="cuerpo" onclick="this.classList.toggle(\'abierto\')">{E(cuerpo)}</div></div></div>')


def original_documento(fuente: str, regiones: list[dict], color_de: dict) -> str:
    partes = [f'<div class="archivo"><div class="barra">{E(fuente)}</div>']
    for r in regiones:
        col = color_de.get(r["ids"][0], "#8FA3AE") if r["ids"] else "#8FA3AE"
        destino = " ".join(f"#{i}" for i in r["ids"]) or "ficha, no fragmento"
        partes.append(f'<div class="region" data-ids="{" ".join(map(str, r["ids"]))}" style="--c:{col}">'
                      f'<div class="corte">✂ {E(r["etiqueta"])} <b>→ {destino}</b></div>')
        for l, clase, nota in r["lineas"]:
            partes.append(f'<div class="l {clase}"><span class="txt">{E(l)}</span>'
                          + (f'<span class="nota">{E(nota)}</span>' if nota else "") + "</div>")
        partes.append("</div>")
    partes.append("</div>")
    return "".join(partes)


def original_pdf(fuente: str, regiones: list[dict], color_de: dict) -> str:
    partes = []
    for r in regiones:
        col = color_de.get(r["ids"][0], "#8FA3AE") if r["ids"] else "#8FA3AE"
        img = (f'<img onclick="this.classList.toggle(\'grande\')" src="data:image/png;base64,{base64.b64encode(r["png"]).decode()}" alt="{E(r["etiqueta"])}">'
               if r.get("png") else "")
        lineas = "".join(f'<div class="l {c}"><span class="txt">{E(l)}</span><span class="nota">{E(n)}</span></div>'
                         for l, c, n in r["lineas"] if c != "texto")
        n_txt, n_frases = r.get("unidas", (0, 0))
        resumen = (f'<div class="l texto"><span class="txt">… {n_txt} líneas de texto'
                   + (f' → <b>{n_frases} frases</b> (se unen las que el PDF cortó a mitad)' if n_frases != n_txt else "")
                   + "</span></div>")
        partes.append(f'<div class="region pdf" data-ids="{" ".join(map(str, r["ids"]))}" style="--c:{col}">'
                      f'<div class="corte">✂ {E(r["etiqueta"])} <b>→ {" ".join(f"#{i}" for i in r["ids"])}</b></div>'
                      f'<div class="pagina">{img}<div class="lineas">{lineas}{resumen}</div></div></div>')
    return "".join(partes)


def original_llamada(frags: list[dict], turnos: list[dict]) -> str:
    burbujas = []
    for n, t in enumerate(turnos, 1):
        nombre, rol, col = QUIEN.get(t["quien"], QUIEN["mezcla"])
        lado = "der" if t["quien"] == "tienda" else "izq"
        burbujas.append(f'<div class="burbuja {lado}" data-turno="{n}" style="--c:{col}">'
                        f'<div class="quien">T{n} · {nombre} <span>{rol} · {mmss(t["inicio"])}</span></div>'
                        f'{E(t["texto"])}</div>')
    cab = "".join(f"<th>T{n}</th>" for n in range(1, len(turnos) + 1))
    filas = []
    for f in frags:
        celdas = "".join(
            f'<td><span class="celda" style="background:{QUIEN.get(turnos[n - 1]["quien"], QUIEN["mezcla"])[2]}"></span></td>'
            if n in f.get("turnos", []) else "<td>·</td>" for n in range(1, len(turnos) + 1))
        filas.append(f'<tr class="fila-frag" data-id="{f["id"]}" data-turnos="{" ".join(map(str, f.get("turnos", [])))}">'
                     f'<th>#{f["id"]}</th>{celdas}<td class="min">{E(f["seccion"])}</td></tr>')
    rejilla = (f'<div class="rejilla"><div class="et">CADA FRAGMENTO = DOS TURNOS SEGUIDOS (VENTANA DESLIZANTE)</div>'
               f'<table><tr><th></th>{cab}<th></th></tr>{"".join(filas)}</table>'
               f'<p>Cada turno aparece en <b>dos</b> fragmentos: es el <b>solapamiento</b>. Así una respuesta '
               f'(«Sí, el 31 aparecía en el borrador…») nunca llega sin su pregunta.</p></div>')
    return rejilla + f'<div class="chat">{"".join(burbujas)}</div>'


def generar(frags: list[dict], origen: str, regiones: dict, turnos: list[dict], destino: Path) -> Path:
    fuentes = list(dict.fromkeys(f["fuente"] for f in frags))
    mapa, secciones = [], []
    for fuente in fuentes:
        g = [f for f in frags if f["fuente"] == fuente]
        tipo = g[0]["tipo"]
        color_de = {f["id"]: PALETA[i % len(PALETA)] for i, f in enumerate(g)}
        cuadros = "".join(f'<span class="cuadro" title="#{f["id"]} · {E(f["estado"])}" '
                          f'style="background:{color_estado(f["estado"])}"></span>' for f in g)
        mapa.append(f'<a class="fuente-card" href="#{slug(fuente)}"><div class="fmt {tipo}">{FORMATO[tipo]}</div>'
                    f'<div class="fn">{E(fuente)}</div><div class="cuadros">{cuadros}</div>'
                    f'<div class="min">{len(g)} fragmento{"s" if len(g) > 1 else ""} · uno = {SE_TROCEA[tipo]}</div></a>')
        if tipo == "documento":
            antes = original_documento(fuente, regiones.get(fuente, []), color_de)
        elif tipo == "pdf":
            antes = original_pdf(fuente, regiones.get(fuente, []), color_de)
        else:
            antes = original_llamada(g, turnos)
        despues = "".join(tarjeta(f, color_de[f["id"]]) for f in g)
        secciones.append(
            f'<section class="fuente" id="{slug(fuente)}"><h2>{E(fuente)} <span class="fmt {tipo}">{FORMATO[tipo]}</span>'
            f'<span class="sub">{len(g)} fragmento{"s" if len(g) > 1 else ""} · un fragmento = {SE_TROCEA[tipo]}</span></h2>'
            f'<div class="dos"><div><h3>ANTES · el original</h3>{antes}</div>'
            f'<div><h3>DESPUÉS · fragmentos con su ficha</h3>{despues}</div></div></section>')
    leyenda = "".join(f'<span><i style="background:{c}"></i>{n}</span>' for n, c in
                      [("aprobado / vigente", "#12907C"), ("sustituido", "#D9475A"),
                       ("registro, aviso, informe…", "#3298B3"), ("pendiente", "#D98A0B"),
                       ("transcripción automática", "#7A5BB5")])
    palabras = sum(len(f["texto"].split()) for f in frags)
    pagina = PLANTILLA.format(
        n_fuentes=len(fuentes), n_frags=len(frags), palabras=f"{palabras:,}".replace(",", "."), origen=E(origen),
        mapa="".join(mapa), leyenda=leyenda, secciones="".join(secciones))
    destino.write_text(pagina, encoding="utf-8")
    return destino


PLANTILLA = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>DropLab · corpus del RAG</title>
<style>
 :root {{ --azul:#01415B; --azul2:#0D5673; --acento:#3298B3; --suave:#F1F6F8; --linea:#DCE8ED; --tinta:#0B2A3A;
          --gris:#4A5D69; --morado:#7A5BB5; }}
 * {{ box-sizing: border-box; }}
 body {{ margin:0; font-family: Arial, Helvetica, sans-serif; color:var(--tinta); background:#fff; }}
 header {{ background:var(--azul); color:#fff; padding:22px 40px 18px; }}
 header h1 {{ margin:0 0 6px; font-size:26px; }}
 header .sub {{ color:#CFE4EC; font-size:14px; }}
 .tubo {{ display:flex; gap:10px; align-items:center; margin-top:14px; flex-wrap:wrap; }}
 .tubo div {{ background:var(--azul2); border-radius:8px; padding:8px 14px; font-size:14px; }}
 .tubo div b {{ color:#6ACBB8; }} .tubo span {{ color:#6ACBB8; font-size:20px; }}
 .tubo .luego {{ background:transparent; border:1px dashed #6ACBB8; color:#CFE4EC; }}
 main {{ padding:20px 40px 80px; max-width:1500px; margin:0 auto; }}
 .et {{ font-size:11px; font-weight:bold; letter-spacing:.06em; color:var(--gris); margin:4px 0 8px; }}
 .mapa {{ display:grid; grid-template-columns:repeat(5, 1fr); gap:10px; }}
 .fuente-card {{ display:block; text-decoration:none; color:inherit; background:var(--suave); border-radius:10px;
                 padding:10px 12px; border:1px solid var(--linea); }}
 .fuente-card:hover {{ border-color:var(--acento); box-shadow:0 2px 8px #0002; }}
 .fn {{ font-family: Consolas, "DejaVu Sans Mono", monospace; font-size:12.5px; font-weight:bold; margin:6px 0;
        word-break:break-all; }}
 .fmt {{ display:inline-block; font-size:10.5px; font-weight:bold; border-radius:99px; padding:2px 9px; color:#fff;
         vertical-align:middle; }}
 .fmt.documento {{ background:var(--acento); }} .fmt.pdf {{ background:var(--azul); }} .fmt.llamada {{ background:var(--morado); }}
 .cuadros {{ display:flex; flex-wrap:wrap; gap:3px; margin:4px 0; }}
 .cuadro {{ width:13px; height:13px; border-radius:3px; display:inline-block; }}
 .min {{ font-size:11.5px; color:var(--gris); }}
 .leyenda {{ margin:12px 0 0; font-size:12.5px; color:var(--gris); display:flex; gap:18px; flex-wrap:wrap; }}
 .leyenda i {{ display:inline-block; width:12px; height:12px; border-radius:3px; margin-right:5px; vertical-align:-1px; }}
 .ideas {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin:16px 0 4px; }}
 .idea {{ background:#fff; border:1px solid var(--linea); border-left:5px solid var(--acento); border-radius:8px;
           padding:10px 14px; font-size:13.5px; }}
 .idea b {{ display:block; margin-bottom:3px; }}
 section.fuente {{ margin-top:38px; padding-top:10px; border-top:3px solid var(--azul); }}
 h2 {{ font-size:21px; color:var(--azul); margin:6px 0 12px; font-family: Consolas, "DejaVu Sans Mono", monospace; }}
 h2 .fmt {{ font-family: Arial, sans-serif; margin-left:8px; }}
 h2 .sub {{ font-family: Arial, sans-serif; font-size:13px; color:var(--gris); font-weight:normal; margin-left:10px; }}
 h3 {{ font-size:12px; letter-spacing:.06em; color:var(--gris); margin:0 0 8px; }}
 .dos {{ display:grid; grid-template-columns: 1fr 1fr; gap:24px; align-items:start; }}
 .archivo {{ border:1px solid var(--linea); border-radius:8px; overflow:hidden; }}
 .barra {{ background:var(--tinta); color:#fff; font-family: Consolas, monospace; font-size:12px; padding:6px 12px; }}
 .region {{ border-left:6px solid var(--c); margin:0; background:#fff; transition: background .15s; }}
 .region.pdf {{ border:1px solid var(--linea); border-left:6px solid var(--c); border-radius:8px; margin-bottom:10px; }}
 .region.luz, .frag.luz {{ background: color-mix(in srgb, var(--c) 14%, white); }}
 .corte {{ font-size:12px; color:var(--c); padding:5px 10px; border-top:1px dashed var(--c);
           background: color-mix(in srgb, var(--c) 8%, white); }}
 .l {{ display:flex; justify-content:space-between; gap:10px; padding:1px 10px; font-family: Consolas, "DejaVu Sans Mono", monospace;
       font-size:12px; line-height:1.55; }}
 .l .txt {{ white-space:pre-wrap; word-break:break-word; }}
 .l .nota {{ flex:none; font-family: Arial, sans-serif; font-size:11px; color:var(--morado); font-weight:bold; }}
 .l.titulo .txt, .l.seccion .txt {{ font-weight:bold; }}
 .l.ficha {{ background:#F3EFF9; }} .l.ficha .txt {{ color:var(--morado); font-weight:bold; }}
 .l.clave {{ background:#FDF3E2; }} .l.clave .txt {{ color:#B5651D; font-weight:bold; }}
 .l.clave .nota {{ color:#B5651D; }}
 .l.descartada .txt {{ color:#A9B8C0; text-decoration:line-through; }} .l.descartada .nota {{ color:#A9B8C0; }}
 .pagina {{ display:flex; gap:12px; padding:8px 10px; align-items:flex-start; }}
 .pagina img {{ width:190px; border:1px solid var(--linea); box-shadow:0 1px 4px #0002; flex:none; cursor:zoom-in;
              transition: width .2s; }}
 .pagina img.grande {{ width:520px; cursor:zoom-out; }}
 .lineas {{ flex:1; min-width:0; }} .lineas .l {{ padding:1px 4px; }}
 .frag {{ border:1px solid var(--linea); border-left:6px solid var(--c); border-radius:8px; padding:10px 12px;
          margin-bottom:10px; transition: background .15s; }}
 .frag-cab {{ display:flex; align-items:baseline; gap:10px; }}
 .num {{ font-size:20px; font-weight:bold; color:var(--c); }}
 .cita {{ font-family: Consolas, monospace; font-size:12.5px; color:var(--gris); }}
 .chips {{ display:flex; flex-wrap:wrap; gap:5px; margin:7px 0; }}
 .chip {{ font-size:11.5px; background:var(--suave); border-radius:99px; padding:2px 9px; color:var(--gris); }}
 .chip b {{ color:var(--tinta); }} .chip.estado {{ color:#fff; font-weight:bold; }}
 .idx {{ background:#FAFCFD; border:1px solid var(--linea); border-radius:6px; padding:6px 9px; }}
 .idx .et {{ margin:0 0 4px; font-size:10px; }}
 .cabecera {{ font-size:12px; font-weight:bold; color:#1F7A93; margin-bottom:4px; }}
 .cabecera span {{ color:var(--gris); font-weight:normal; }}
 .cuerpo {{ font-family: Consolas, monospace; font-size:11.5px; white-space:pre-wrap; max-height:7.5em; overflow:hidden;
            cursor:pointer; position:relative; }}
 .cuerpo:not(.abierto)::after {{ content:"▾ clic para ver todo"; position:absolute; right:0; bottom:0; background:#FAFCFD;
            color:var(--acento); font-family:Arial; font-size:11px; padding-left:20px; }}
 .cuerpo.abierto {{ max-height:none; }}
 .chat {{ display:flex; flex-direction:column; gap:6px; margin-top:12px; }}
 .burbuja {{ max-width:85%; background:#fff; border:1px solid var(--linea); border-left:5px solid var(--c);
             border-radius:10px; padding:6px 10px; font-size:13px; transition: background .15s; }}
 .burbuja.der {{ align-self:flex-end; border-left:1px solid var(--linea); border-right:5px solid var(--c); background:#FFFBF3; }}
 .burbuja.luz {{ background: color-mix(in srgb, var(--c) 18%, white); }}
 .quien {{ font-size:11px; font-weight:bold; color:var(--c); }} .quien span {{ color:var(--gris); font-weight:normal; }}
 .rejilla table {{ border-collapse:collapse; font-size:11px; }}
 .rejilla th {{ color:var(--gris); padding:1px 4px; font-weight:normal; }}
 .rejilla td {{ text-align:center; color:#C8D8DF; padding:1px 3px; }}
 .rejilla td.min {{ text-align:left; padding-left:8px; }}
 .celda {{ display:inline-block; width:16px; height:12px; border-radius:2px; }}
 .rejilla tr.fila-frag:hover {{ background:var(--suave); cursor:default; }}
 .rejilla p {{ font-size:12.5px; color:var(--gris); margin:6px 0 0; }}
 footer {{ margin-top:40px; padding:16px; background:var(--suave); border-radius:10px; font-size:14px; }}
 code {{ font-family: Consolas, monospace; background:#fff; padding:1px 5px; border-radius:4px; }}
 @media (max-width: 1100px) {{ .dos {{ grid-template-columns:1fr; }} .mapa {{ grid-template-columns:repeat(2,1fr); }} }}
</style></head><body>
<header><h1>El corpus del RAG: cómo se trocean y etiquetan las fuentes</h1>
<div class="sub">Paso 1 de 4 · <b>{n_fuentes} fuentes</b> → <b>{n_frags} fragmentos</b> · {palabras} palabras ·
 llamada: {origen} · nunca la carpeta docente/</div>
<div class="tubo"><div>📄 <b>{n_fuentes}</b> fuentes</div><span>→</span><div>✂ trocear por su estructura</div><span>→</span>
<div>🏷 ficha: documento, página, fecha, estado</div><span>→</span><div><b>{n_frags}</b> fragmentos · corpus.jsonl</div>
<span>→</span><div class="luego">paso 2 (11_indice.py): cada fragmento → un vector</div></div></header>
<main>
<div class="et" style="margin-top:6px">EL MAPA · UN CUADRADO POR FRAGMENTO, DEL COLOR DE SU ESTADO · CLIC PARA IR A LA FUENTE</div>
<div class="mapa">{mapa}</div>
<div class="leyenda">{leyenda}</div>
<div class="ideas">
 <div class="idea"><b>✂ Por estructura, no por caracteres</b>Sección, página o turno: nunca a mitad de frase.
   Cortar «cada 500 caracteres» mezclaría temas.</div>
 <div class="idea" style="border-left-color:#7A5BB5"><b>🏷 La ficha sale del propio documento</b>Las líneas en morado
   (código, estado, fecha…) pasan a la ficha. «Sustituido» lo deduce el código: otro documento dice «sustituye a…».</div>
 <div class="idea" style="border-left-color:#12907C"><b>Sin OCR y sin embeddings todavía</b>Los PDF son digitales: el texto
   está dentro. Los vectores llegan en el paso 2. Pasa el ratón por un fragmento para ver de dónde sale.</div>
</div>
{secciones}
<footer><b>Siguiente:</b> <code>python practica/sesion_2/11_indice.py</code> convierte cada «texto que se indexa» en un
vector (1.024 números con bge-m3) y lo guarda en DuckDB, junto a su ficha.</footer>
</main>
<script>
 function luz(id, on) {{
   document.querySelectorAll('.frag[data-id="' + id + '"]').forEach(e => e.classList.toggle('luz', on));
   document.querySelectorAll('.region').forEach(r => {{ if ((' ' + r.dataset.ids + ' ').includes(' ' + id + ' ')) r.classList.toggle('luz', on); }});
   const fila = document.querySelector('.fila-frag[data-id="' + id + '"]');
   if (fila) fila.dataset.turnos.split(' ').forEach(t => {{
     const b = document.querySelector('.burbuja[data-turno="' + t + '"]'); if (b) b.classList.toggle('luz', on); }});
 }}
 document.querySelectorAll('.frag, .fila-frag').forEach(f => {{
   f.addEventListener('mouseenter', () => luz(f.dataset.id, true));
   f.addEventListener('mouseleave', () => luz(f.dataset.id, false)); }});
 document.querySelectorAll('.region').forEach(r => {{
   r.addEventListener('mouseenter', () => r.dataset.ids.split(' ').filter(Boolean).forEach(i => luz(i, true)));
   r.addEventListener('mouseleave', () => r.dataset.ids.split(' ').filter(Boolean).forEach(i => luz(i, false))); }});
</script></body></html>"""
