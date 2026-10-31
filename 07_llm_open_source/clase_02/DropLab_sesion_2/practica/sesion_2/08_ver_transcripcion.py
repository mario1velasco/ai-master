"""La transcripción, para verla y escucharla: una página web con la llamada como un chat.

  - Arriba, la forma de onda de los dos canales (clic = saltar a ese instante).
  - Debajo, la conversación: Álex (Central) a la izquierda y Dani (Tienda) a la derecha.
  - Cada palabra lleva su probabilidad: en amarillo las dudosas (p < 0,70) y en rojo
    las muy dudosas (p < 0,50). Al pasar el ratón se ve la probabilidad y el segundo.
  - Clic en una palabra: el audio salta a ese instante y suena.

Uso:
  python practica/sesion_2/08_ver_transcripcion.py                       # la última transcripción
  python practica/sesion_2/08_ver_transcripcion.py transcripciones/turbo_canales.json
  python practica/sesion_2/08_ver_transcripcion.py --abrir               # y abrirla en el navegador

Salida: practica/sesion_2/transcripciones/<nombre>.html
"""

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
CARPETA = AQUI / "transcripciones"
sys.path.insert(0, str(AQUI))
ver = import_module("06_ver_audio")

AUDIO_DOS = ROOT / "data" / "audio" / "llamada_0704_dos_canales.wav"
AUDIO_ESCUCHA = ROOT / "data" / "audio" / "llamada_0704_escucha_mono.wav"
NOMBRE = {"central": "Álex · Central", "tienda": "Dani · Tienda Malasaña", "mezcla": "Mezcla (sin saber quién)"}


def onda_svg(ancho: int = 1100, alto: int = 70) -> str:
    """Envolvente de cada canal como SVG (una franja por canal)."""
    audio, sr, _ = ver.leer_wav(AUDIO_DOS)
    n = audio.shape[1]
    trozos = np.array_split(np.abs(audio), ancho, axis=1)
    picos = np.stack([t.max(axis=1) for t in trozos], axis=1)          # [canal, ancho]
    partes = []
    for c, color in enumerate(("#3298B3", "#D98A0B")):
        y0 = c * alto + alto / 2
        puntos = " ".join(f"{x},{y0 - v * alto / 2:.1f}" for x, v in enumerate(picos[c]))
        puntos += " " + " ".join(f"{x},{y0 + v * alto / 2:.1f}" for x, v in reversed(list(enumerate(picos[c]))))
        partes.append(f'<polygon points="{puntos}" fill="{color}" opacity="0.85"/>')
    return (f'<svg id="onda" viewBox="0 0 {ancho} {2 * alto}" preserveAspectRatio="none" '
            f'data-duracion="{n / sr:.3f}">{"".join(partes)}'
            f'<line id="cursor" x1="0" x2="0" y1="0" y2="{2 * alto}" stroke="#D9475A" stroke-width="2"/></svg>')


def palabra_html(w: dict) -> str:
    clase = "mal" if w["p"] < 0.5 else ("duda" if w["p"] < 0.7 else "")
    return (f'<span class="w {clase}" data-t="{w["inicio"]}" title="p = {w["p"]:.2f} · {w["inicio"]:.1f} s">'
            f'{html.escape(w["palabra"])}</span>')


def unir_turnos(segmentos: list[dict], pausa: float = 1.5) -> list[dict]:
    """Une segmentos seguidos del mismo interlocutor en un solo turno (una burbuja)."""
    turnos = []
    for s in segmentos:
        if turnos and turnos[-1]["quien"] == s["quien"] and s["inicio"] - turnos[-1]["fin"] < pausa:
            turnos[-1] = {**turnos[-1], "fin": s["fin"], "texto": turnos[-1]["texto"] + " " + s["texto"],
                          "palabras": turnos[-1]["palabras"] + s["palabras"]}
        else:
            turnos.append(dict(s))
    return turnos


def construir(datos: dict, origen: Path) -> str:
    segs = unir_turnos(datos["segmentos"])
    burbujas = []
    for s in segs:
        palabras = " ".join(palabra_html(w) for w in s["palabras"]) or html.escape(s["texto"])
        burbujas.append(f'''<div class="fila {s["quien"]}"><div class="burbuja" data-t="{s["inicio"]}">
<div class="quien">{NOMBRE[s["quien"]]} <span class="t">{s["inicio"]:.1f}–{s["fin"]:.1f} s</span></div>
<div class="texto">{palabras}</div></div></div>''')
    total = sum(len(s["palabras"]) for s in segs)
    dudosas = sum(1 for s in segs for w in s["palabras"] if w["p"] < 0.7)
    audio_rel = os.path.relpath(AUDIO_ESCUCHA, origen.parent)
    return f'''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>Llamada 07/04 · {datos["modelo"]} · {datos["modo"]}</title>
<style>
 body {{ font-family: Arial, sans-serif; margin: 0; background: #F1F6F8; color: #0B2A3A; }}
 header {{ background: #01415B; color: #fff; padding: 18px 32px; position: sticky; top: 0; z-index: 2; }}
 header h1 {{ margin: 0 0 4px; font-size: 22px; }} header .sub {{ color: #CFE4EC; font-size: 14px; }}
 #onda {{ width: 100%; height: 90px; background: #0D5673; border-radius: 6px; margin-top: 12px; cursor: pointer; }}
 audio {{ width: 100%; margin-top: 8px; }}
 .leyenda {{ font-size: 13px; color: #CFE4EC; margin-top: 6px; }}
 .leyenda span {{ padding: 1px 6px; border-radius: 4px; margin: 0 4px; color: #0B2A3A; }}
 main {{ max-width: 1100px; margin: 0 auto; padding: 20px 32px 80px; }}
 .fila {{ display: flex; margin: 10px 0; }} .fila.tienda {{ justify-content: flex-end; }}
 .burbuja {{ max-width: 70%; padding: 10px 14px; border-radius: 14px; background: #fff; box-shadow: 0 1px 2px #0002; }}
 .central .burbuja {{ border-left: 5px solid #3298B3; }} .tienda .burbuja {{ border-right: 5px solid #D98A0B; background: #FFF8EC; }}
 .mezcla .burbuja {{ border-left: 5px solid #8FA3AE; }}
 .quien {{ font-size: 12px; font-weight: bold; color: #4A5D69; margin-bottom: 4px; }} .t {{ font-weight: normal; color: #8FA3AE; }}
 .texto {{ font-size: 17px; line-height: 1.55; }}
 .w {{ cursor: pointer; border-radius: 3px; padding: 0 1px; }} .w:hover {{ outline: 1px solid #3298B3; }}
 .w.duda {{ background: #FDE7A8; }} .w.mal {{ background: #D9475A; color: #fff; }}
 .w.sonando {{ background: #01415B; color: #fff; }}
</style></head><body>
<header><h1>Llamada de Operaciones a Malasaña · 07/04/2026</h1>
<div class="sub">Whisper <b>{datos["modelo"]}</b> · modo <b>{datos["modo"]}</b>{" · solo voz" if datos.get("solo_voz") else ""}
 · {datos["dispositivo"].upper()} · transcripción en {datos["segundos_transcripcion"]} s ·
 {dudosas} palabras dudosas de {total}</div>
{onda_svg()}
<audio id="audio" controls src="{html.escape(audio_rel)}"></audio>
<div class="leyenda">Probabilidad de cada palabra: <span style="background:#FDE7A8">dudosa &lt; 0,70</span>
<span style="background:#D9475A;color:#fff">muy dudosa &lt; 0,50</span> · clic en una palabra para escucharla</div>
</header>
<main>{"".join(burbujas)}</main>
<script>
 const audio = document.getElementById('audio'), onda = document.getElementById('onda');
 const dur = parseFloat(onda.dataset.duracion), cursor = document.getElementById('cursor');
 const palabras = [...document.querySelectorAll('.w')];
 function ir(t) {{ audio.currentTime = Math.max(0, t - 0.15); audio.play(); }}
 document.querySelectorAll('[data-t]').forEach(e => e.addEventListener('click', ev => {{ ev.stopPropagation(); ir(parseFloat(e.dataset.t)); }}));
 onda.addEventListener('click', ev => {{ const r = onda.getBoundingClientRect(); ir((ev.clientX - r.left) / r.width * dur); }});
 audio.addEventListener('timeupdate', () => {{
   cursor.setAttribute('x1', audio.currentTime / dur * 1100); cursor.setAttribute('x2', audio.currentTime / dur * 1100);
   palabras.forEach(w => w.classList.remove('sonando'));
   let actual = null; for (const w of palabras) {{ if (parseFloat(w.dataset.t) <= audio.currentTime) actual = w; }}
   if (actual && !audio.paused) actual.classList.add('sonando');
 }});
</script></body></html>'''


def main() -> None:
    ap = argparse.ArgumentParser(description="Ver y escuchar la transcripción como un chat.")
    ap.add_argument("json", nargs="?", type=Path, help="Transcripción (por defecto, la más reciente).")
    ap.add_argument("--abrir", action="store_true", help="Abrir la página en el navegador.")
    a = ap.parse_args()
    if a.json is None:
        candidatos = sorted(CARPETA.glob("*.json"), key=lambda p: p.stat().st_mtime)
        if not candidatos:
            raise SystemExit("No hay transcripciones: ejecuta antes 07_transcribir.py")
        a.json = candidatos[-1]
    ruta = a.json if a.json.is_absolute() else (AQUI / a.json if (AQUI / a.json).exists() else Path.cwd() / a.json)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    destino = ruta.with_suffix(".html")
    destino.write_text(construir(datos, destino), encoding="utf-8")
    print(f"Página: {destino.relative_to(ROOT)}")
    if a.abrir:
        import webbrowser
        webbrowser.open(destino.as_uri())


if __name__ == "__main__":
    main()
