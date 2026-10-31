"""Primera inspección manual de data/.

Objetivo de este script, escrito nosotros mismos como ejercicio:
- listar los CSV recibidos;
- contar filas y columnas de cada uno;
- mostrar tipos de columna detectados por pandas;
- contar valores nulos por columna;
- enseñar una vista previa de las primeras filas.

Todavía no usamos Ollama. Todavía no asumimos nada sobre el significado de
negocio de los datos: solo describimos lo que hay, literalmente.
"""

import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def buscar_datos() -> Path:
    """Carpeta de los CSV: DROPLAB_DATOS, data/datos (aula) o DropLab/datos (zip de alumnos), aquí o más arriba."""
    if os.environ.get("DROPLAB_DATOS"):
        return Path(os.environ["DROPLAB_DATOS"])
    for base in [ROOT, *ROOT.parents, Path.cwd()]:
        for candidato in (base / "data" / "datos", base / "DropLab" / "datos"):
            if (candidato / "ventas.csv").exists():
                return candidato
    return ROOT / "data" / "datos"


DATA = buscar_datos()


def inspeccionar_csv(ruta: Path) -> None:
    df = pd.read_csv(ruta)

    print("=" * 70)
    print(f"Archivo: {ruta.name}")
    print(f"Filas: {len(df)} | Columnas: {len(df.columns)}")
    print("-" * 70)

    print("Tipos de columna detectados por pandas:")
    print(df.dtypes)

    print("-" * 70)
    print("Valores nulos por columna:")
    nulos = df.isna().sum()
    print(nulos[nulos > 0] if nulos.sum() > 0 else "Ninguno")

    print("-" * 70)
    print("Primeras filas:")
    print(df.head(3).to_string())
    print()


def main() -> None:
    if not DATA.exists():
        raise SystemExit(f"No se encontró la carpeta de datos esperada: {DATA}")

    archivos = sorted(DATA.glob("*.csv"))
    if not archivos:
        raise SystemExit(f"No hay archivos CSV en {DATA}")

    print(f"Carpeta de datos: {DATA}")
    print(f"Archivos CSV encontrados: {len(archivos)}")
    print()

    for ruta in archivos:
        inspeccionar_csv(ruta)


if __name__ == "__main__":
    main()
