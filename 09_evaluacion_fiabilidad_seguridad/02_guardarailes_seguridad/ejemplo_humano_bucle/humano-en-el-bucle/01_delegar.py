"""Demo 1 · Delegar y esperar.

Encarga una campaña al equipo de agentes. El equipo trabaja hasta que necesita a una
persona; entonces le deja una tarea, avisa por email (simulado, en buzon/) y SE DETIENE.
El programa termina, pero el estado queda guardado: nadie pierde el trabajo hecho.

Uso:
  python 01_delegar.py                        ← Obrador Espiga: 1.500 €, necesita aprobación y datos
  python 01_delegar.py --cliente taller-radios ← 600 €: solo necesita datos
  python 01_delegar.py --brief "..."           ← tu propio encargo para Obrador Espiga
"""
import argparse

from faro import agencia
from faro.flujo import abrir_faro

parser = argparse.ArgumentParser()
parser.add_argument("--cliente", default="obrador-espiga", choices=list(agencia.CLIENTES))
parser.add_argument("--brief", help="Texto del encargo (por defecto, el de la ficha del cliente)")
args = parser.parse_args()

with abrir_faro() as faro:
    print(f"📨 Nuevo encargo para {agencia.CLIENTES[args.cliente]['nombre']}\n")
    id_encargo = faro.nuevo_encargo(args.cliente, args.brief)
    tarea = faro.tarea_pendiente(id_encargo)
    if tarea:
        print(f"\n📧 Aviso enviado: mira la carpeta buzon/")
        print(f"👉 Siguiente paso: python 02_bandeja.py y abre http://127.0.0.1:8000/encargo/{id_encargo}")
