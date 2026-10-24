"""Utilidades compartidas: localizar ffmpeg/ffprobe y leer metadatos con ffprobe."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


def require_binary(name: str) -> str:
    path = shutil.which(name)
    if not path:
        sys.exit("error: no se encuentra '{}' en el PATH. Instala ffmpeg (p. ej. 'sudo apt install ffmpeg').".format(name))
    return path


def probe(path: Path) -> Dict[str, Any]:
    """Devuelve duración (s), códec, bitrate (bit/s), sample rate y canales del primer stream de audio."""
    ffprobe = require_binary("ffprobe")
    result = subprocess.run(
        [ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit("error: ffprobe no pudo leer {}: {}".format(path, result.stderr.strip()))
    data = json.loads(result.stdout)
    streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
    if not streams:
        sys.exit("error: {} no contiene ningún stream de audio".format(path))
    stream = streams[0]
    fmt = data.get("format", {})
    duration = float(fmt.get("duration") or stream.get("duration") or 0)
    raw_adts = fmt.get("format_name") == "aac"  # AAC crudo: sin índice ni cabecera de duración
    if raw_adts:
        duration = decoded_duration(path)  # ffprobe solo la estima por bitrate (puede errar >10 s en 1 h)
    if duration <= 0:
        sys.exit("error: no se pudo determinar la duración de {}".format(path))
    return {
        "duration": duration,
        "raw_adts": raw_adts,
        "codec": stream.get("codec_name"),
        "bit_rate": int(fmt.get("bit_rate") or stream.get("bit_rate") or 0),
        "sample_rate": int(stream.get("sample_rate") or 0),
        "channels": int(stream.get("channels") or 0),
    }


def decoded_duration(path: Path) -> float:
    """Duración exacta decodificando todo el archivo (ffmpeg -f null)."""
    ffmpeg = require_binary("ffmpeg")
    result = subprocess.run([ffmpeg, "-nostats", "-i", str(path), "-vn", "-f", "null", "-"],
                            capture_output=True, text=True)
    times = re.findall(r"time=(\d+):(\d+):([\d.]+)", result.stderr)
    if result.returncode != 0 or not times:
        sys.exit("error: no se pudo decodificar {} para medir su duración".format(path))
    h, m, s = times[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


def fmt_time(seconds: float) -> str:
    total = int(round(seconds))
    return "{:d}:{:02d}:{:02d}".format(total // 3600, (total % 3600) // 60, total % 60)
