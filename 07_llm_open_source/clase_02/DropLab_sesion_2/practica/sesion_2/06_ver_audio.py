"""Cómo se ve la voz: la llamada de Operaciones a Malasaña, de números a imágenes.

Antes de transcribir, miramos qué ES un audio para un ordenador y qué «ve» Whisper.
No hace falta Whisper ni ninguna librería nueva: solo numpy y matplotlib.

Vistas (una ventana cada una; con --guardar, también un PNG en practica/sesion_2/figuras_audio/):

  datos          qué hay en el archivo: canales, muestras por segundo, bits, duración
  onda           la llamada entera: un canal por interlocutor
  zoom           acercándonos a una palabra hasta ver los números (las muestras)
  espectrograma  qué frecuencias suenan en cada instante: dos voces, dos «huellas»
  mel            lo que de verdad entra en Whisper: 30 s convertidos en una imagen de 128 × 3000
  turnos         quién habla cuándo, detectado por la energía de cada canal (sin IA)
  todo           todas, una detrás de otra

Uso:
  python practica/sesion_2/06_ver_audio.py datos
  python practica/sesion_2/06_ver_audio.py onda
  python practica/sesion_2/06_ver_audio.py zoom --inicio 1.0
  python practica/sesion_2/06_ver_audio.py mel --inicio 0
  python practica/sesion_2/06_ver_audio.py todo --guardar
"""

from __future__ import annotations

import argparse
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AUDIO = ROOT / "data" / "audio" / "llamada_0704_dos_canales.wav"
FIGURAS = Path(__file__).resolve().parent / "figuras_audio"
NOMBRES = ["Central · Álex (Operaciones)", "Tienda · Dani (Malasaña)"]
COLORES = ["#3298B3", "#D98A0B"]

# Los mismos parámetros que usa Whisper para «mirar» el audio
SR = 16_000          # muestras por segundo
N_FFT = 400          # ventana de 25 ms
HOP = 160            # un paso cada 10 ms → 100 columnas por segundo
N_MELS = 128         # bandas de frecuencia (large-v3 y turbo; los modelos antiguos usan 80)
TROZO = 30           # Whisper procesa el audio en trozos de 30 segundos


# ---------------------------------------------------------------------------
# Leer el audio: un WAV es una cabecera y una lista enorme de números
# ---------------------------------------------------------------------------


def leer_wav(ruta: Path) -> tuple[np.ndarray, int, dict]:
    """Devuelve (muestras [canales, n] en −1..1, frecuencia de muestreo, ficha del archivo)."""
    with wave.open(str(ruta), "rb") as w:
        ficha = {"canales": w.getnchannels(), "muestras_por_segundo": w.getframerate(),
                 "bytes_por_muestra": w.getsampwidth(), "n_muestras": w.getnframes()}
        crudo = w.readframes(w.getnframes())
    enteros = np.frombuffer(crudo, dtype=np.int16).reshape(-1, ficha["canales"]).T   # [canal, tiempo]
    ficha["duracion_s"] = ficha["n_muestras"] / ficha["muestras_por_segundo"]
    pico = int(np.argmax(np.abs(enteros[0, : 3 * ficha["muestras_por_segundo"]])))
    ficha["ejemplo_enteros"] = enteros[0, pico:pico + 8].tolist()
    return enteros.astype(np.float32) / 32768.0, ficha["muestras_por_segundo"], ficha


# ---------------------------------------------------------------------------
# Del sonido a la imagen: espectrograma y log-mel (como Whisper)
# ---------------------------------------------------------------------------


def stft(x: np.ndarray) -> np.ndarray:
    """Potencia por frecuencia y por instante: ventanas de 25 ms, cada 10 ms. [201 frecuencias, n_ventanas]."""
    ventana = np.hanning(N_FFT + 1)[:-1]
    x = np.pad(x, N_FFT // 2, mode="reflect")
    n = 1 + (len(x) - N_FFT) // HOP
    tramas = np.stack([x[i * HOP:i * HOP + N_FFT] * ventana for i in range(n)])
    return (np.abs(np.fft.rfft(tramas, axis=1)) ** 2).T


def filtros_mel(n_mels: int = N_MELS) -> np.ndarray:
    """Bandas «mel»: estrechas en graves y anchas en agudos, como el oído (escala de Slaney, la de Whisper)."""
    def hz_a_mel(f):
        f = np.asarray(f, dtype=float)
        return np.where(f < 1000, 3 * f / 200, 15 + np.log(np.maximum(f, 1e-9) / 1000) / (np.log(6.4) / 27))

    def mel_a_hz(m):
        m = np.asarray(m, dtype=float)
        return np.where(m < 15, 200 * m / 3, 1000 * np.exp((m - 15) * np.log(6.4) / 27))
    frecs = np.linspace(0, SR / 2, N_FFT // 2 + 1)
    bordes = mel_a_hz(np.linspace(hz_a_mel(0), hz_a_mel(SR / 2), n_mels + 2))
    banco = np.zeros((n_mels, len(frecs)))
    for i in range(n_mels):
        izq, cen, der = bordes[i:i + 3]
        subida = (frecs - izq) / (cen - izq)
        bajada = (der - frecs) / (der - cen)
        banco[i] = np.maximum(0, np.minimum(subida, bajada)) * 2 / (der - izq)
    return banco


def log_mel(x: np.ndarray) -> np.ndarray:
    """La entrada de Whisper: 128 bandas mel × 100 columnas por segundo, en escala logarítmica y normalizada."""
    mel = filtros_mel() @ stft(x)[:, :-1]
    lm = np.log10(np.maximum(mel, 1e-10))
    lm = np.maximum(lm, lm.max() - 8.0)
    return (lm + 4.0) / 4.0


# ---------------------------------------------------------------------------
# Quién habla cuándo, sin IA: energía de cada canal
# ---------------------------------------------------------------------------


def energia_db(x: np.ndarray, ms: int = 20) -> tuple[np.ndarray, np.ndarray]:
    """Energía (dB) en ventanas de 20 ms. Devuelve (tiempos, dB)."""
    n = int(SR * ms / 1000)
    tramas = x[: len(x) // n * n].reshape(-1, n)
    rms = np.sqrt((tramas ** 2).mean(axis=1) + 1e-12)
    return np.arange(len(rms)) * ms / 1000, 20 * np.log10(rms)


def detectar_turnos(audio: np.ndarray, umbral_db: float = -40, pausa_s: float = 0.8,
                    minimo_s: float = 0.4) -> list[tuple[int, float, float]]:
    """Tramos con voz en cada canal: energía por encima del umbral, uniendo pausas cortas."""
    turnos = []
    for canal in range(audio.shape[0]):
        t, db = energia_db(audio[canal])
        activo = db > umbral_db
        tramos, ini = [], None
        for ti, a in zip(t, activo):
            if a and ini is None:
                ini = ti
            if not a and ini is not None:
                tramos.append([ini, ti])
                ini = None
        if ini is not None:
            tramos.append([ini, t[-1]])
        unidos = []
        for a, b in tramos:
            if unidos and a - unidos[-1][1] < pausa_s:
                unidos[-1][1] = b
            else:
                unidos.append([a, b])
        turnos += [(canal, a, b) for a, b in unidos if b - a >= minimo_s]
    return sorted(turnos, key=lambda x: x[1])


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------


def vista_datos(audio, sr, ficha, ruta):
    n = ficha["n_muestras"]
    print(f"Archivo: {ruta.relative_to(ROOT)}")
    print(f"  Canales:               {ficha['canales']}  (0 = {NOMBRES[0]}, 1 = {NOMBRES[1]})")
    print(f"  Muestras por segundo:  {sr:,}".replace(",", ".") + "  (16 kHz: suficiente para la voz)")
    print(f"  Bits por muestra:      {ficha['bytes_por_muestra'] * 8}  (cada número va de −32.768 a 32.767)")
    print(f"  Duración:              {ficha['duracion_s']:.1f} s")
    print(f"  Números en total:      {n:,} por canal × {ficha['canales']} = {n * ficha['canales']:,}".replace(",", "."))
    print(f"  Peso:                  {ruta.stat().st_size / 1e6:.1f} MB")
    print(f"  Ocho números seguidos:  {ficha['ejemplo_enteros']} …  (½ milisegundo de voz)")
    print("\nEso es todo un audio: una lista de números que dicen cuánto se mueve la membrana del micrófono.")


def vista_onda(plt, audio, sr, turnos):
    t = np.arange(audio.shape[1]) / sr
    fig, ejes = plt.subplots(2, 1, figsize=(15, 6), sharex=True)
    fig.suptitle("La llamada: un canal por interlocutor (forma de onda)", fontsize=14, fontweight="bold")
    for c, ax in enumerate(ejes):
        ax.plot(t[::8], audio[c, ::8], color=COLORES[c], linewidth=0.4)
        for cc, a, b in turnos:
            if cc == c:
                ax.axvspan(a, b, color=COLORES[c], alpha=0.08)
        ax.set_ylim(-1, 1)
        ax.set_ylabel(NOMBRES[c], rotation=0, ha="right", va="center", fontsize=10)
        ax.set_yticks([])
        ax.spines[["top", "right", "left"]].set_visible(False)
    ejes[-1].set_xlabel("segundos")
    fig.tight_layout()
    return fig


def vista_zoom(plt, audio, sr, inicio):
    """Tres zooms sobre el canal central: 2 s → 0,1 s → 5 ms (aquí ya se ven los números uno a uno)."""
    c = 0
    niveles = [(2.0, "2 segundos: palabras"), (0.1, "0,1 s: la vibración de la voz"), (0.005, "5 ms: 80 números")]
    fig, ejes = plt.subplots(3, 1, figsize=(15, 8))
    fig.suptitle("Acercándonos a la voz hasta ver los números", fontsize=14, fontweight="bold")
    # Centramos los zooms en el instante con más energía de esos 2 s: el centro de una vocal
    tramo = audio[c, int(inicio * sr):int((inicio + 2) * sr)]
    env = np.convolve(np.abs(tramo), np.ones(400) / 400, mode="same")
    centro = inicio + int(np.argmax(env)) / sr
    for ax, (ancho, titulo) in zip(ejes, niveles):
        a = int((centro - ancho / 2) * sr) if ancho < 2 else int(inicio * sr)
        b = a + int(ancho * sr)
        tt = np.arange(a, b) / sr
        ax.plot(tt, audio[c, a:b], color=COLORES[c], linewidth=0.8 if ancho > 0.01 else 1.2)
        if ancho <= 0.01:
            ax.plot(tt, audio[c, a:b], "o", color="#01415B", markersize=4)
        ax.set_title(titulo, loc="left", fontsize=11)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_ylabel("amplitud")
    ejes[-1].set_xlabel("segundos")
    fig.tight_layout()
    return fig


def vista_espectrograma(plt, audio, sr, turnos):
    """El primer turno de cada interlocutor: dos voces, dos patrones de frecuencias."""
    fig, ejes = plt.subplots(1, 2, figsize=(15, 5.5))
    fig.suptitle("Espectrograma: qué frecuencias suenan en cada instante", fontsize=14, fontweight="bold")
    for c, ax in enumerate(ejes):
        _, a, b = next(x for x in turnos if x[0] == c)
        b = min(b, a + 5)
        p = 10 * np.log10(stft(audio[c, int(a * sr):int(b * sr)]) + 1e-10)
        ax.imshow(p, origin="lower", aspect="auto", cmap="magma", extent=[a, b, 0, sr / 2 / 1000],
                  vmin=p.max() - 80, vmax=p.max())
        ax.set_ylim(0, 5)
        ax.set_title(NOMBRES[c], color=COLORES[c], fontsize=12, fontweight="bold")
        ax.set_xlabel("segundos")
        ax.set_ylabel("frecuencia (kHz)")
    fig.tight_layout()
    return fig


def vista_mel(plt, audio, sr, inicio):
    """Exactamente la forma de la entrada de Whisper: 30 s → 128 bandas × 3000 columnas."""
    mono = audio.mean(axis=0)
    trozo = mono[int(inicio * sr):int((inicio + TROZO) * sr)]
    trozo = np.pad(trozo, (0, TROZO * sr - len(trozo)))
    lm = log_mel(trozo)
    fig, ax = plt.subplots(figsize=(15, 5))
    ax.imshow(lm, origin="lower", aspect="auto", cmap="viridis", extent=[inicio, inicio + TROZO, 0, N_MELS])
    ax.set_title(f"Lo que entra en Whisper: {TROZO} s de audio → una imagen de {lm.shape[0]} × {lm.shape[1]}",
                 fontsize=14, fontweight="bold", loc="left")
    ax.set_xlabel("segundos")
    ax.set_ylabel("banda mel (grave → agudo)")
    fig.tight_layout()
    return fig


def vista_turnos(plt, audio, sr, turnos):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    fig.suptitle("Quién habla cuándo, sin IA: la energía de cada canal", fontsize=14, fontweight="bold")
    for c in range(audio.shape[0]):
        t, db = energia_db(audio[c])
        ax1.plot(t, db, color=COLORES[c], linewidth=0.7, label=NOMBRES[c])
    ax1.axhline(-40, color="#D9475A", linestyle="--", linewidth=1)
    ax1.text(0.5, -38, "umbral: −40 dB", color="#D9475A", fontsize=9)
    ax1.set_ylim(-90, 0)
    ax1.set_ylabel("energía (dB)")
    ax1.legend(loc="lower right", fontsize=9)
    for c, a, b in turnos:
        ax2.barh(1 - c, b - a, left=a, height=0.6, color=COLORES[c])
    ax2.set_yticks([1, 0], ["Central", "Tienda"])
    ax2.set_xlabel("segundos")
    for ax in (ax1, ax2):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def main() -> None:
    p = argparse.ArgumentParser(description="Cómo se ve la voz: de números a imágenes.")
    p.add_argument("vista", nargs="?", default="todo",
                   choices=["datos", "onda", "zoom", "espectrograma", "mel", "turnos", "todo"])
    p.add_argument("--archivo", type=Path, default=AUDIO)
    p.add_argument("--inicio", type=float, default=0.0, help="Segundo de inicio para zoom y mel.")
    p.add_argument("--guardar", action="store_true", help="Guardar además cada figura como PNG.")
    p.add_argument("--sin-ventana", action="store_true", help="No abrir ventanas (por SSH): solo guardar.")
    a = p.parse_args()

    audio, sr, ficha = leer_wav(a.archivo)
    if sr != SR:
        raise SystemExit(f"Se esperaba audio a {SR} Hz y este está a {sr} Hz.")
    if a.vista in ("datos", "todo"):
        vista_datos(audio, sr, ficha, a.archivo)
    if a.vista == "datos":
        return

    import matplotlib
    if a.sin_ventana:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    turnos = detectar_turnos(audio) if audio.shape[0] == 2 else []
    if a.vista in ("turnos", "todo") and turnos:
        print(f"\nTurnos detectados por energía: {len(turnos)}")
        for c, ini, fin in turnos:
            print(f"  {ini:6.1f} – {fin:6.1f} s   {NOMBRES[c]}")

    vistas = {"onda": lambda: vista_onda(plt, audio, sr, turnos),
              "zoom": lambda: vista_zoom(plt, audio, sr, a.inicio or 1.0),
              "espectrograma": lambda: vista_espectrograma(plt, audio, sr, turnos),
              "mel": lambda: vista_mel(plt, audio, sr, a.inicio),
              "turnos": lambda: vista_turnos(plt, audio, sr, turnos)}
    elegidas = list(vistas) if a.vista == "todo" else [a.vista]
    for nombre in elegidas:
        fig = vistas[nombre]()
        if a.guardar or a.sin_ventana:
            FIGURAS.mkdir(exist_ok=True)
            destino = FIGURAS / f"{nombre}.png"
            fig.savefig(destino, dpi=130)
            print(f"Figura guardada: {destino.relative_to(ROOT)}")
    if not a.sin_ventana:
        plt.show()


if __name__ == "__main__":
    main()
