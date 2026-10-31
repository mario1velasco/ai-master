"""Panel en directo: la llamada suena y todo se dibuja a la vez, en el navegador.

Paneles (se actualizan 60 veces por segundo, sincronizados con lo que suena):
  1. La llamada completa: forma de onda, turnos y cabezal (clic = saltar ahí).
  2. La onda ahora mismo: los últimos 50 ms de cada canal (un osciloscopio).
  3. Quién habla: nivel de cada canal frente al umbral de −40 dB, con una luz por interlocutor.
  4. Espectrograma en directo: las frecuencias de cada voz, desplazándose.
  5. Lo que ve Whisper: la imagen log-mel exacta (128 bandas) de los últimos 30 s.
  6. La transcripción: las burbujas aparecen al hablar y se resalta la palabra que suena.
  Y un contador de los números (muestras) que se van leyendo.

Botones: reproducir/pausa, volver al principio, cámara lenta (0,5×) y estéreo/centrado.
Teclas: espacio = reproducir/pausa · ← → = 5 s atrás/adelante.

Cómo funciona: Python prepara los datos exactos (la imagen mel, los turnos y la transcripción)
y levanta un servidor web local (solo en este equipo). El navegador reproduce el audio y lo
analiza en tiempo real con la Web Audio API.

Uso:
  python practica/sesion_2/09_panel_en_directo.py                  # usa la última transcripción si existe
  python practica/sesion_2/09_panel_en_directo.py --transcripcion practica/sesion_2/transcripciones/turbo_canales.json
  python practica/sesion_2/09_panel_en_directo.py --sin-abrir      # solo el servidor (abre tú la dirección)
Para terminar: Ctrl + C.
"""

from __future__ import annotations

import argparse
import base64
import functools
import http.server
import io
import json
import subprocess
import sys
import threading
from importlib import import_module
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
ver = import_module("06_ver_audio")
chat = import_module("08_ver_transcripcion")

AUDIO = ROOT / "data" / "audio" / "llamada_0704_dos_canales.wav"
PANEL = AQUI / "panel"
PUERTO = 8765
# Si aún no has transcrito, el panel usa la transcripción guardada de las pruebas (y lo dice).
RESPALDO = ROOT / "experimentos" / "audio" / "transcripciones_openai_whisper" / "turbo_canales.json"


# ---------------------------------------------------------------------------
# Datos que prepara Python (exactos) para el navegador
# ---------------------------------------------------------------------------


def preparar_datos(transcripcion: Path | None, origen: str = "") -> dict:
    audio, sr, ficha = ver.leer_wav(AUDIO)
    n = audio.shape[1]
    # Envolvente de cada canal (1.400 puntos) para la vista de la llamada completa
    trozos = np.array_split(np.abs(audio), 1400, axis=1)
    envolvente = np.stack([t.max(axis=1) for t in trozos], axis=1).round(3).tolist()
    # La imagen log-mel EXACTA de Whisper, de toda la llamada (mezcla), como PNG
    lm = ver.log_mel(audio.mean(axis=0))                       # [128, n/160]
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    img = plt.get_cmap("viridis")((np.clip(lm, lm.min(), lm.max()) - lm.min()) / (lm.max() - lm.min()))
    buf = io.BytesIO()
    plt.imsave(buf, img[::-1], format="png")                  # graves abajo
    mel_png = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    turnos = [{"canal": c, "inicio": round(a, 2), "fin": round(b, 2)} for c, a, b in ver.detectar_turnos(audio)]
    datos = {"duracion": n / sr, "sr": sr, "envolvente": envolvente, "mel_png": mel_png, "mel_columnas": lm.shape[1],
             "turnos": turnos, "transcripcion": None}
    if transcripcion and transcripcion.exists():
        t = json.loads(transcripcion.read_text(encoding="utf-8"))
        datos["transcripcion"] = {"modelo": t["modelo"], "modo": t["modo"], "origen": origen,
                                  "segmentos": t["segmentos"], "turnos": chat.unir_turnos(t["segmentos"])}
    return datos


def ultima_transcripcion() -> Path | None:
    candidatos = sorted((AQUI / "transcripciones").glob("*.json"), key=lambda p: p.stat().st_mtime)
    return candidatos[-1] if candidatos else None


def abrir_servidor(manejador, puerto: int):
    """El primer puerto libre desde `puerto` (si el 8765 está ocupado, prueba 8766, 8767…)."""
    for p in range(puerto, puerto + 20):
        try:
            return http.server.ThreadingHTTPServer(("127.0.0.1", p), manejador), p
        except OSError:
            continue
    raise SystemExit(f"No hay ningún puerto libre entre {puerto} y {puerto + 19}.")


# ---------------------------------------------------------------------------
# La página (HTML + CSS + JavaScript)
# ---------------------------------------------------------------------------

PAGINA = r"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<title>DropLab · La llamada, en directo</title>
<style>
 :root { --fondo:#04263A; --panel:#0B3550; --borde:#14506F; --texto:#E6F2F7; --sub:#8FB8CA;
         --alex:#3FB4D3; --dani:#F2A93B; --rojo:#E25A6C; --verde:#6ACBB8; }
 * { box-sizing: border-box; }
 html, body { margin:0; height:100%; background:var(--fondo); color:var(--texto); font-family: Arial, sans-serif; }
 body { display:grid; grid-template-rows: 64px 132px 1fr; height:100vh; }
 #subtitulo { display:flex; align-items:center; gap:22px; padding:8px 24px; background:#021B29; border-bottom:2px solid var(--borde); min-height:0; }
 #quien { display:flex; align-items:center; gap:14px; min-width:250px; }
 #avatar { width:62px; height:62px; border-radius:50%; background:#21445A; color:#04263A; font-size:30px; font-weight:bold;
           display:flex; align-items:center; justify-content:center; transition: all .12s; }
 #avatar.central { background:var(--alex); box-shadow:0 0 22px var(--alex); } #avatar.tienda { background:var(--dani); box-shadow:0 0 22px var(--dani); }
 #quienNombre { font-size:22px; font-weight:bold; } #quienRol { font-size:13px; color:var(--sub); display:block; margin-top:2px; }
 #frases { flex:1; min-width:0; }
 #frasePrevia { font-size:14px; color:var(--sub); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; height:20px; }
 #fraseActual { font-size:29px; line-height:1.3; max-height:84px; overflow:hidden; }
 #fraseActual .s { color:#ffffff59; padding:0 2px; border-radius:5px; transition: background .08s; }
 #fraseActual .s.dicha { color:#fff; }
 #fraseActual .s.duda { box-shadow: inset 0 -4px 0 #F2C94C; } #fraseActual .s.mal { box-shadow: inset 0 -4px 0 var(--rojo); }
 #fraseActual .s.ahora.central { background:var(--alex); color:#04263A; } #fraseActual .s.ahora.tienda { background:var(--dani); color:#04263A; }
 #fraseActual .s.ahora.mezcla { background:#fff; color:#04263A; }
 #fraseActual .pausa { color:var(--sub); font-size:22px; font-style:italic; }
 header { display:flex; align-items:center; gap:14px; padding:0 20px; background:#01415B; border-bottom:2px solid var(--borde); }
 header h1 { font-size:20px; margin:0 12px 0 0; white-space:nowrap; }
 button { background:var(--panel); color:var(--texto); border:1px solid var(--borde); border-radius:8px; padding:8px 14px;
          font-size:15px; cursor:pointer; } button:hover { border-color:var(--verde); }
 button.on { background:var(--verde); color:#04263A; font-weight:bold; }
 #play { background:var(--verde); color:#04263A; font-weight:bold; min-width:130px; }
 .reloj { font-family: Consolas, monospace; font-size:22px; color:#fff; margin-left:auto; }
 .numeros { font-family: Consolas, monospace; font-size:14px; color:var(--sub); text-align:right; line-height:1.2; }
 .numeros b { color:var(--verde); font-size:18px; }
 main { display:grid; gap:10px; padding:10px; min-height:0;
        grid-template-columns: 1fr 1fr 0.95fr; grid-template-rows: 128px 1fr 1fr; }
 .p { background:var(--panel); border:1px solid var(--borde); border-radius:10px; padding:8px 12px 10px; display:flex;
      flex-direction:column; min-height:0; min-width:0; }
 .p h2 { margin:0 0 6px; font-size:13px; letter-spacing:.06em; text-transform:uppercase; color:var(--sub); display:flex; gap:10px; }
 .p h2 .n { color:var(--verde); } .p h2 .der { margin-left:auto; text-transform:none; letter-spacing:0; color:var(--sub); }
 canvas { width:100%; flex:1; min-height:0; display:block; border-radius:6px; background:#021B29; }
 #completa { grid-column: 1 / 3; } #texto { grid-column: 3; grid-row: 1 / 4; }
 #chat { flex:1; overflow-y:auto; padding-right:4px; scroll-behavior:smooth; }
 .fila { display:flex; margin:8px 0; opacity:0; transform:translateY(8px); transition: all .35s; }
 .fila.visible { opacity:1; transform:none; } .fila.tienda { justify-content:flex-end; }
 .burbuja { max-width:86%; padding:8px 12px; border-radius:12px; background:#123F5C; font-size:16px; line-height:1.45; }
 .central .burbuja { border-left:4px solid var(--alex); } .tienda .burbuja { border-right:4px solid var(--dani); background:#3A3220; }
 .quien { font-size:11px; font-weight:bold; color:var(--sub); margin-bottom:2px; }
 .w { border-radius:3px; padding:0 1px; } .w.futura { color:#ffffff40; }
 .w.duda { box-shadow: inset 0 -3px 0 #F2C94C; } .w.mal { box-shadow: inset 0 -3px 0 var(--rojo); }
 .w.sonando { background:#fff; color:#04263A; }
 .vacio { color:var(--sub); font-size:15px; padding:20px; line-height:1.5; }
 .luces { display:flex; gap:14px; margin-bottom:6px; font-size:14px; }
 .luz { display:flex; align-items:center; gap:7px; color:var(--sub); }
 .luz i { width:16px; height:16px; border-radius:50%; background:#21445A; display:inline-block; transition: all .08s; }
 .luz.on.a i { background:var(--alex); box-shadow:0 0 14px var(--alex); } .luz.on.d i { background:var(--dani); box-shadow:0 0 14px var(--dani); }
 .luz.on { color:#fff; font-weight:bold; }
 #aviso { position:fixed; inset:0; background:#04263Aee; display:flex; align-items:center; justify-content:center;
          font-size:26px; flex-direction:column; gap:16px; z-index:5; } #aviso small { font-size:15px; color:var(--sub); }
</style></head><body>
<div id="aviso">Cargando la llamada…<small>16.000 números por segundo, dos canales</small></div>
<header>
 <h1>📞 Operaciones → Malasaña · 07/04</h1>
 <button id="play">▶ Reproducir</button>
 <button id="inicio">⏮ Principio</button>
 <button id="lento">🐢 Cámara lenta</button>
 <button id="estereo" class="on">🎧 Estéreo</button>
 <span class="reloj" id="reloj">0:00.0 / 1:53</span>
 <span class="numeros">números leídos<br><b id="contador">0</b></span>
</header>
<section id="subtitulo">
 <div id="quien"><div id="avatar">·</div><div><span id="quienNombre">Silencio</span><span id="quienRol">pulsa Reproducir</span></div></div>
 <div id="frases"><div id="frasePrevia"></div><div id="fraseActual"></div></div>
</section>
<main>
 <section class="p" id="completa"><h2><span class="n">1</span> La llamada completa <span class="der">
   <span style="color:var(--alex)">■ Álex · Central (canal izquierdo)</span> &nbsp; <span style="color:var(--dani)">■ Dani · Tienda (canal derecho)</span> &nbsp; · clic para saltar</span></h2>
   <canvas id="cCompleta"></canvas></section>
 <section class="p" id="texto"><h2><span class="n">6</span> La transcripción <span class="der" id="modeloTxt"></span></h2>
   <div id="chat"></div></section>
 <section class="p"><h2><span class="n">2</span> La onda ahora mismo <span class="der">los últimos 50 ms · 800 números por canal · ampliada ×3</span></h2>
   <canvas id="cOnda"></canvas></section>
 <section class="p"><h2><span class="n">3</span> Quién habla <span class="der">energía de cada canal · umbral −40 dB</span></h2>
   <div class="luces"><span class="luz a" id="luzA"><i></i>Álex</span><span class="luz d" id="luzD"><i></i>Dani</span>
   <span class="luz" style="margin-left:auto" id="dbTxt"></span></div>
   <canvas id="cEnergia"></canvas></section>
 <section class="p"><h2><span class="n">4</span> Espectrograma en directo <span class="der">0 – 8 kHz · arriba Álex, abajo Dani</span></h2>
   <canvas id="cEspectro"></canvas></section>
 <section class="p"><h2><span class="n">5</span> Lo que ve Whisper <span class="der">log-mel exacto · 128 bandas × 100 por segundo · los últimos 30 s</span></h2>
   <canvas id="cMel"></canvas></section>
</main>
<script>
const D = __DATOS__;
const $ = id => document.getElementById(id);
const COL = ['#3FB4D3', '#F2A93B'];
let ctx, buffer, fuente = null, salida, mono, divisor, an = [], inicioCtx = 0, desde = 0, sonando = false, vel = 1, estereo = true;

// ---------- Canvas con resolución real ----------
function lienzo(id) {
  const c = $(id), r = c.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  c.width = Math.max(10, r.width * dpr); c.height = Math.max(10, r.height * dpr);
  const g = c.getContext('2d'); return { c, g, w: c.width, h: c.height };
}
let L = {};
function medir() { for (const id of ['cCompleta', 'cOnda', 'cEnergia', 'cEspectro', 'cMel']) L[id] = lienzo(id); }

// ---------- Audio ----------
async function cargar() {
  ctx = new AudioContext({ sampleRate: D.sr });
  const r = await fetch('/data/audio/llamada_0704_dos_canales.wav');
  buffer = await ctx.decodeAudioData(await r.arrayBuffer());
  divisor = ctx.createChannelSplitter(2);
  for (let i = 0; i < 2; i++) {
    const a = ctx.createAnalyser(); a.fftSize = 1024; a.smoothingTimeConstant = 0; a.minDecibels = -100; a.maxDecibels = -20;
    divisor.connect(a, i); an.push(a);
  }
  salida = ctx.createGain();
  mono = ctx.createGain(); mono.channelCount = 1; mono.channelCountMode = 'explicit'; mono.channelInterpretation = 'speakers';
  mono.connect(ctx.destination); salida.connect(ctx.destination);
  $('aviso').style.display = 'none';
}
function ahora() { return sonando ? Math.min(D.duracion, desde + (ctx.currentTime - inicioCtx) * vel) : desde; }
function reproducir(t) {
  parar(); desde = Math.max(0, Math.min(t, D.duracion - 0.05));
  fuente = ctx.createBufferSource(); fuente.buffer = buffer; fuente.playbackRate.value = vel;
  fuente.connect(divisor); fuente.connect(estereo ? salida : mono);
  fuente.start(0, desde); inicioCtx = ctx.currentTime; sonando = true; $('play').textContent = '⏸ Pausa';
  fuente.onended = () => { if (sonando && ahora() >= D.duracion - 0.1) { sonando = false; desde = D.duracion; $('play').textContent = '▶ Reproducir'; } };
}
function parar() { if (fuente) { const t = ahora(); fuente.onended = null; try { fuente.stop(); } catch (e) {} fuente = null; desde = t; } sonando = false; $('play').textContent = '▶ Reproducir'; }
function saltar(t) { if (sonando) reproducir(t); else desde = Math.max(0, Math.min(t, D.duracion)); limpiarDirecto(); }

// ---------- Colores ----------
const MAGMA = [[0,0,4],[40,11,84],[101,21,110],[159,42,99],[212,72,66],[245,125,21],[250,193,39],[252,253,191]];
function magma(v) { v = Math.max(0, Math.min(1, v)) * (MAGMA.length - 1); const i = Math.floor(v), f = v - i, a = MAGMA[i], b = MAGMA[Math.min(i + 1, MAGMA.length - 1)];
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f]; }
function mmss(t) { const m = Math.floor(t / 60), s = t - m * 60; return m + ':' + (s < 10 ? '0' : '') + s.toFixed(1); }

// ---------- 1. La llamada completa ----------
function dibujarCompleta(t) {
  const { g, w, h } = L.cCompleta; g.clearRect(0, 0, w, h);
  const n = D.envolvente[0].length, mitad = h / 2;
  for (const tu of D.turnos) { g.fillStyle = COL[tu.canal] + '22'; g.fillRect(tu.inicio / D.duracion * w, tu.canal * mitad, (tu.fin - tu.inicio) / D.duracion * w, mitad); }
  for (let c = 0; c < 2; c++) {
    const y0 = c * mitad + mitad / 2; g.fillStyle = COL[c];
    for (let i = 0; i < n; i++) { const x = i / n * w, v = D.envolvente[c][i] * mitad * 0.95; g.globalAlpha = (i / n * D.duracion) <= t ? 1 : 0.35; g.fillRect(x, y0 - v / 2, Math.max(1, w / n), Math.max(1, v)); }
  }
  g.globalAlpha = 1; const x = t / D.duracion * w;
  g.fillStyle = '#fff'; g.fillRect(x - 1, 0, 3, h);
}
$('cCompleta').addEventListener('click', ev => { const r = ev.target.getBoundingClientRect(); saltar((ev.clientX - r.left) / r.width * D.duracion); });

// ---------- 2. La onda ahora mismo ----------
const muestras = [new Float32Array(1024), new Float32Array(1024)];
function dibujarOnda() {
  const { g, w, h } = L.cOnda; g.clearRect(0, 0, w, h);
  g.strokeStyle = '#ffffff18'; g.beginPath(); g.moveTo(0, h / 4); g.lineTo(w, h / 4); g.moveTo(0, 3 * h / 4); g.lineTo(w, 3 * h / 4); g.stroke();
  for (let c = 0; c < 2; c++) {
    an[c].getFloatTimeDomainData(muestras[c]);
    const y0 = h / 4 + c * h / 2, n = 800, a = muestras[c];
    g.strokeStyle = COL[c]; g.lineWidth = 2 * (window.devicePixelRatio || 1); g.beginPath();
    for (let i = 0; i < n; i++) { const x = i / (n - 1) * w, y = y0 - Math.max(-1, Math.min(1, a[a.length - n + i] * 3)) * h / 4 * 0.95; i ? g.lineTo(x, y) : g.moveTo(x, y); }
    g.stroke();
    g.fillStyle = COL[c]; g.font = 'bold ' + (13 * (window.devicePixelRatio || 1)) + 'px Arial'; g.fillText(c ? 'Dani' : 'Álex', 8, c * h / 2 + 18 * (window.devicePixelRatio || 1));
  }
}

// ---------- 3. Quién habla ----------
const HIST = 600, historia = [new Array(HIST).fill(-100), new Array(HIST).fill(-100)];
function rmsDb(a) { let s = 0; for (const v of a) s += v * v; return 20 * Math.log10(Math.sqrt(s / a.length) + 1e-9); }
function dibujarEnergia() {
  const { g, w, h } = L.cEnergia; g.clearRect(0, 0, w, h);
  const db = [0, 1].map(c => sonando ? Math.max(-100, rmsDb(muestras[c])) : -100);
  for (let c = 0; c < 2; c++) { historia[c].push(db[c]); historia[c].shift(); }
  const y = v => h - (v + 90) / 90 * h;
  g.strokeStyle = '#E25A6C'; g.setLineDash([8, 6]); g.beginPath(); g.moveTo(0, y(-40)); g.lineTo(w, y(-40)); g.stroke(); g.setLineDash([]);
  g.fillStyle = '#E25A6C'; g.font = (12 * (window.devicePixelRatio || 1)) + 'px Arial'; g.fillText('umbral −40 dB', 6, y(-40) - 6);
  for (let c = 0; c < 2; c++) {
    g.strokeStyle = COL[c]; g.lineWidth = 2; g.beginPath();
    historia[c].forEach((v, i) => { const x = i / (HIST - 1) * w * 0.86; i ? g.lineTo(x, y(v)) : g.moveTo(x, y(v)); }); g.stroke();
    const bx = w * 0.89 + c * w * 0.055, alto = Math.max(0, (db[c] + 90) / 90) * h;   // vúmetro
    g.fillStyle = '#21445A'; g.fillRect(bx, 0, w * 0.04, h); g.fillStyle = COL[c]; g.fillRect(bx, h - alto, w * 0.04, alto);
  }
  $('luzA').classList.toggle('on', db[0] > -40); $('luzD').classList.toggle('on', db[1] > -40);
  $('dbTxt').textContent = sonando ? `Álex ${db[0].toFixed(0)} dB · Dani ${db[1].toFixed(0)} dB` : '';
}

// ---------- 4. Espectrograma en directo ----------
const frec = [new Float32Array(512), new Float32Array(512)];
function dibujarEspectro() {
  const { c, g, w, h } = L.cEspectro, paso = 2 * (window.devicePixelRatio || 1);
  g.drawImage(c, -paso, 0);                                  // desplazar a la izquierda
  const mitad = Math.floor(h / 2), col = g.createImageData(paso, h);
  for (let k = 0; k < 2; k++) {
    an[k].getFloatFrequencyData(frec[k]);
    for (let yy = 0; yy < mitad; yy++) {
      const bin = Math.floor((1 - yy / mitad) * 511), v = sonando ? (frec[k][bin] + 100) / 80 : 0, [r, gg, b] = magma(v);
      for (let xx = 0; xx < paso; xx++) { const p = ((k * mitad + yy) * paso + xx) * 4; col.data[p] = r; col.data[p + 1] = gg; col.data[p + 2] = b; col.data[p + 3] = 255; }
    }
  }
  g.putImageData(col, w - paso, 0);
  g.fillStyle = '#ffffff60'; g.fillRect(0, mitad - 1, w, 2);
}

// ---------- 5. Lo que ve Whisper ----------
const melImg = new Image(); melImg.src = D.mel_png;
function dibujarMel(t) {
  const { g, w, h } = L.cMel; g.fillStyle = '#021B29'; g.fillRect(0, 0, w, h);
  const ancho = 30, ini = t - ancho, colsPorSeg = 100;
  const sx = Math.max(0, ini * colsPorSeg), sw = t * colsPorSeg - sx;
  if (sw > 1 && melImg.complete) { const dx = (Math.max(0, ini) - ini) / ancho * w; g.drawImage(melImg, sx, 0, sw, 128, dx, 0, w - dx, h); }
  g.fillStyle = '#fff'; g.fillRect(w - 3, 0, 3, h);
  g.fillStyle = '#ffffffb0'; g.font = (12 * (window.devicePixelRatio || 1)) + 'px Arial';
  g.fillText('agudos', 6, 16 * (window.devicePixelRatio || 1)); g.fillText('graves', 6, h - 8);
}

// ---------- 6. La transcripción ----------
let palabras = [], filas = [];
function prepararChat() {
  const T = D.transcripcion, chat = $('chat');
  if (!T) { chat.innerHTML = '<div class="vacio">Todavía no hay transcripción.<br>Ejecuta <b>07_transcribir.py</b> y vuelve a abrir el panel: aquí aparecerá la conversación mientras suena.</div>'; return; }
  $('modeloTxt').textContent = `Whisper ${T.modelo} · ${T.modo}` + (T.origen.startsWith('guardada') ? ' · de las pruebas' : '');
  for (const s of T.turnos) {
    const f = document.createElement('div'); f.className = 'fila ' + s.quien; f.dataset.t = s.inicio;
    const b = document.createElement('div'); b.className = 'burbuja';
    b.innerHTML = `<div class="quien">${s.quien === 'central' ? 'Álex · Central' : s.quien === 'tienda' ? 'Dani · Tienda' : 'Mezcla'} · ${s.inicio.toFixed(1)} s</div>`;
    const txt = document.createElement('div');
    for (const w of s.palabras) {
      const e = document.createElement('span'); e.className = 'w futura' + (w.p < 0.5 ? ' mal' : w.p < 0.7 ? ' duda' : '');
      e.textContent = w.palabra + ' '; e.dataset.t = w.inicio; e.title = `p = ${w.p.toFixed(2)}`;
      e.addEventListener('click', () => saltar(w.inicio)); txt.appendChild(e); palabras.push(e);
    }
    b.appendChild(txt); f.appendChild(b); chat.appendChild(f); filas.push(f);
  }
}
let ultimaFila = null;
function actualizarChat(t) {
  let actual = null;
  for (const f of filas) { const v = parseFloat(f.dataset.t) <= t + 0.05; f.classList.toggle('visible', v); if (v) actual = f; }
  for (const e of palabras) { const pas = parseFloat(e.dataset.t) <= t; e.classList.toggle('futura', !pas); e.classList.remove('sonando'); }
  const sonandoW = palabras.filter(e => parseFloat(e.dataset.t) <= t).pop();
  if (sonandoW && sonando) sonandoW.classList.add('sonando');
  if (actual && actual !== ultimaFila) { actual.scrollIntoView({ block: 'end' }); ultimaFila = actual; }
}

// ---------- Subtítulos: quién habla y qué está diciendo ----------
const NOMBRES = { central: ['Á', 'Álex', 'Central · Operaciones'], tienda: ['D', 'Dani', 'Tienda · Malasaña'], mezcla: ['?', 'Alguien', 'mezcla: no sabemos quién'] };
const SEGS = D.transcripcion ? D.transcripcion.segmentos.filter(s => s.palabras && s.palabras.length) : [];
let segActual = null, spans = [];
function textoSeg(s) { return s.palabras.map(w => w.palabra).join(' '); }
function pintarSeg(s) {
  const caja = $('fraseActual'); caja.innerHTML = ''; spans = [];
  if (!s) return;
  for (const w of s.palabras) {
    const e = document.createElement('span');
    e.className = 's ' + s.quien + (w.p < 0.5 ? ' mal' : w.p < 0.7 ? ' duda' : '');
    e.textContent = w.palabra; e.dataset.i = w.inicio; e.dataset.f = w.fin;
    caja.appendChild(e); caja.appendChild(document.createTextNode(' ')); spans.push(e);
  }
}
function quienPorEnergia() {
  const db = [0, 1].map(c => historia[c][HIST - 1]);
  if (!sonando) return null; if (db[0] > -40 && db[0] >= db[1]) return 'central'; if (db[1] > -40) return 'tienda'; return null;
}
function ponerQuien(q, rol) {
  const a = $('avatar'); a.className = q || ''; a.textContent = q ? NOMBRES[q][0] : '·';
  $('quienNombre').textContent = q ? NOMBRES[q][1] : 'Silencio';
  $('quienRol').textContent = rol !== undefined ? rol : (q ? NOMBRES[q][2] : (sonando ? 'nadie habla' : 'en pausa'));
}
function actualizarSubtitulos(t) {
  if (!SEGS.length) {                                  // sin transcripción: solo quién habla, por energía
    ponerQuien(quienPorEnergia());
    if (!$('fraseActual').dataset.aviso) { $('fraseActual').innerHTML = '<span class="pausa">Sin transcripción: ejecuta 07_transcribir.py para ver aquí lo que se dice.</span>'; $('fraseActual').dataset.aviso = 1; }
    return;
  }
  let s = null, previo = null;
  for (const x of SEGS) { if (x.inicio - 0.25 <= t && t <= x.fin + 0.5) s = x; if (x.fin < t) previo = x; }
  if (s !== segActual) {
    segActual = s; pintarSeg(s);
    const ant = s ? SEGS[SEGS.indexOf(s) - 1] : previo;
    $('frasePrevia').textContent = ant ? `${NOMBRES[ant.quien][1]}: «${textoSeg(ant)}»` : '';
    if (!s) $('fraseActual').innerHTML = '<span class="pausa">…</span>';
  }
  if (s) {
    let ahoraW = null;
    for (const e of spans) {
      const ini = parseFloat(e.dataset.i), fin = parseFloat(e.dataset.f);
      e.classList.toggle('dicha', ini <= t); e.classList.remove('ahora');
      if (ini <= t && t <= Math.max(fin, ini + 0.15) + 0.12) ahoraW = e;
    }
    if (ahoraW) ahoraW.classList.add('ahora');
    ponerQuien(s.quien);
  } else {
    ponerQuien(quienPorEnergia());
  }
}

// ---------- Bucle ----------
function limpiarDirecto() { L.cEspectro.g.fillStyle = '#021B29'; L.cEspectro.g.fillRect(0, 0, L.cEspectro.w, L.cEspectro.h); for (const h of historia) h.fill(-100); }
const PASOS = [t => dibujarCompleta(t), () => dibujarOnda(), () => dibujarEnergia(), () => dibujarEspectro(),
               t => dibujarMel(t), t => actualizarChat(t), t => actualizarSubtitulos(t)];
function bucle() {
  const t = ahora();
  for (const paso of PASOS) { try { paso(t); } catch (e) { console.error(e); } }   // si un panel falla, el resto sigue
  $('reloj').textContent = mmss(t) + ' / ' + mmss(D.duracion);
  $('contador').textContent = Math.floor(t * D.sr * 2).toLocaleString('es-ES');
  requestAnimationFrame(bucle);
}

// ---------- Botones y teclas ----------
$('play').onclick = async () => { if (ctx.state === 'suspended') await ctx.resume(); sonando ? parar() : reproducir(desde >= D.duracion - 0.1 ? 0 : desde); };
$('inicio').onclick = () => { saltar(0); };
$('lento').onclick = () => { const t = ahora(); vel = vel === 1 ? 0.5 : 1; $('lento').classList.toggle('on', vel !== 1); if (sonando) reproducir(t); };
$('estereo').onclick = () => { estereo = !estereo; $('estereo').textContent = estereo ? '🎧 Estéreo' : '🔈 Centrado'; $('estereo').classList.toggle('on', estereo); if (sonando) reproducir(ahora()); };
document.addEventListener('keydown', ev => {
  if (ev.code === 'Space') { ev.preventDefault(); $('play').click(); }
  if (ev.code === 'ArrowRight') saltar(ahora() + 5); if (ev.code === 'ArrowLeft') saltar(ahora() - 5);
});
window.addEventListener('resize', () => { medir(); limpiarDirecto(); });

medir(); prepararChat();
cargar().then(() => {
  limpiarDirecto(); bucle();
  const q = new URLSearchParams(location.search);       // ?auto=40 → empezar solo en el segundo 40 (pruebas)
  if (q.has('auto')) reproducir(parseFloat(q.get('auto')) || 0);
}).catch(e => { $('aviso').innerHTML = 'No se pudo cargar el audio<small>' + e + '</small>'; console.error(e); });
</script></body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Panel en directo: la llamada suena y todo se dibuja a la vez.")
    ap.add_argument("--transcripcion", type=Path, help="JSON de 07_transcribir.py (por defecto, el último).")
    ap.add_argument("--puerto", type=int, default=PUERTO)
    ap.add_argument("--sin-abrir", action="store_true", help="No abrir el navegador.")
    a = ap.parse_args()

    transcripcion, origen = a.transcripcion, "la indicada"
    if transcripcion is None:
        transcripcion, origen = ultima_transcripcion(), "la última de 07_transcribir.py"
    if transcripcion is None and RESPALDO.exists():
        transcripcion, origen = RESPALDO, "guardada de las pruebas: aún no has ejecutado 07"
    if transcripcion and not transcripcion.is_absolute():
        transcripcion = (Path.cwd() / transcripcion).resolve()
    print("Preparando los datos (imagen mel exacta, turnos y transcripción)…")
    datos = preparar_datos(transcripcion, origen)
    PANEL.mkdir(exist_ok=True)
    (PANEL / "index.html").write_text(PAGINA.replace("__DATOS__", json.dumps(datos, ensure_ascii=False)),
                                      encoding="utf-8")
    if datos["transcripcion"]:
        print(f"  transcripción: {transcripcion.relative_to(ROOT)}  ({origen})")
    else:
        print("  transcripción: ninguna (ejecuta 07_transcribir.py)")

    # Servidor web local: solo escucha en este equipo (127.0.0.1) y sirve la carpeta del proyecto
    manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    manejador.log_message = lambda *args, **kwargs: None
    servidor, puerto = abrir_servidor(manejador, a.puerto)
    url = f"http://127.0.0.1:{puerto}/practica/sesion_2/panel/index.html"
    print(f"\nPanel en: {url}\nPulsa Reproducir (o la barra espaciadora). Para terminar: Ctrl + C.")
    if not a.sin_abrir:
        import webbrowser
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor cerrado.")


if __name__ == "__main__":
    main()
