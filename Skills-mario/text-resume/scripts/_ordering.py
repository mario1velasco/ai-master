"""Descubre los textos de un directorio y decide su orden (orden natural por número).

Si el orden no se puede deducir con seguridad devuelve `ambiguities`; quien llame debe
preguntar al usuario en vez de adivinar. Los `warnings` no bloquean (p. ej. huecos en la numeración).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

TEXT_EXTS = {".txt", ".md"}
TOKEN = re.compile(r"(\d+)")


def find_texts(directory: Path) -> List[Path]:
    return sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in TEXT_EXTS)


def tokens(name: str) -> List[str]:
    return TOKEN.split(Path(name).stem)  # posiciones impares = números


def natural_key(path: Path) -> List:
    return [int(t) if t.isdigit() else t.lower() for t in tokens(path.name)]


def order_files(files: List[Path]) -> Dict:
    """Devuelve {'files': [...ordenados], 'ambiguities': [...], 'warnings': [...]}."""
    ambiguities: List[str] = []
    warnings: List[str] = []
    ordered = sorted(files, key=natural_key)
    if len(files) <= 1:
        return {"files": ordered, "ambiguities": ambiguities, "warnings": warnings}

    toks = [tokens(f.name) for f in files]
    if all(len(t) == 1 for t in toks):
        ambiguities.append("ningún nombre contiene números: solo se podría ordenar alfabéticamente")
    elif len({len(t) for t in toks}) > 1:
        ambiguities.append("los nombres tienen estructuras distintas (distinto nº de números): puede haber varias series mezcladas")
    else:
        for pos in range(0, len(toks[0]), 2):
            if len({t[pos].lower() for t in toks}) > 1:
                ambiguities.append("el texto del nombre cambia entre archivos ({}): ¿son series distintas?".format(
                    ", ".join(sorted({t[pos] for t in toks})[:4])))
                break
        varying = [pos for pos in range(1, len(toks[0]), 2) if len({int(t[pos]) for t in toks}) > 1]
        # Varios números pueden variar a la vez (p. ej. 001_parte_001): solo es ambiguo si ordenar
        # por cada uno de ellos da un orden distinto.
        orders = {tuple(sorted(range(len(files)), key=lambda i, p=pos: int(toks[i][p]))) for pos in varying}
        if len(orders) > 1:
            ambiguities.append("varios números cambian entre archivos y dan órdenes distintos: no está claro cuál manda")
        elif varying:
            nums = sorted(int(t[varying[-1]]) for t in toks)
            if len(set(nums)) != len(nums):
                ambiguities.append("hay números repetidos en la numeración")
            else:
                missing = [n for n in range(nums[0], nums[-1] + 1) if n not in set(nums)]
                if missing:
                    warnings.append("faltan números en la secuencia: {}".format(missing[:10]))
        else:
            ambiguities.append("los nombres solo difieren en mayúsculas o ceros a la izquierda")
    return {"files": ordered, "ambiguities": ambiguities, "warnings": warnings}
