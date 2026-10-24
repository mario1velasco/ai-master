import sys

if sys.version_info[:2] != (3, 11):
    raise RuntimeError(f"Se esperaba Python 3.11 y se encontro {sys.version.split()[0]}")

import datasets
import faiss
import jupyterlab
import langchain_community
import langchain_core
import matplotlib
import model2vec
import numpy
import pandas

index = faiss.IndexHNSWFlat(8, 8)
assert index.d == 8
print("Entorno verificado correctamente.")
