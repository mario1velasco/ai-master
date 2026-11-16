"""Demo 4 · Canales y plazos: ¿y si la persona no responde?

Un equipo de agentes que espera a una persona puede quedarse parado días. Este script es
lo que en una empresa se ejecutaría cada hora (un cron o una tarea programada):
- Si una tarea lleva más de HORAS_RECORDATORIO esperando, envía un recordatorio.
- Si lleva más de HORAS_ESCALADO, la reasigna a la directora de cuentas y la avisa.
Los avisos son emails simulados en la carpeta buzon/.

Para no esperar horas de verdad, --dentro-de simula que ha pasado ese tiempo.

Uso:
  python 04_plazos.py                    ← revisa ahora
  python 04_plazos.py --dentro-de 5      ← como si hubieran pasado 5 horas: recordatorio
  python 04_plazos.py --dentro-de 26     ← como si hubieran pasado 26 horas: escalado
"""
import argparse
from datetime import datetime, timedelta

from faro import agencia
from faro.flujo import abrir_faro

HORAS_RECORDATORIO = 4
HORAS_ESCALADO = 24
ESCALAR_A = "carmen"

parser = argparse.ArgumentParser()
parser.add_argument("--dentro-de", type=float, default=0, help="Horas que simulamos que han pasado")
args = parser.parse_args()
momento = datetime.now() + timedelta(hours=args.dentro_de)

with abrir_faro(mostrar=False) as faro:
    pendientes = [e for e in faro.encargos() if e["estado"] == "esperando_persona"]
    if not pendientes:
        print("No hay tareas esperando a una persona. Crea una con: python 01_delegar.py")
    for e in pendientes:
        horas = faro.horas_esperando(e, momento)
        persona = agencia.PERSONAS[e["asignado_a"]]["nombre"]
        tarea = faro.tarea_pendiente(e["id"])
        print(f"{e['id']} · {tarea['titulo']} · {persona} · esperando {horas:.1f} h")
        if horas >= HORAS_ESCALADO and e["asignado_a"] != ESCALAR_A:
            faro.escalar(e["id"], ESCALAR_A)
            print(f"   ⬆️  Escalada a {agencia.PERSONAS[ESCALAR_A]['nombre']} (email en buzon/)")
        elif horas >= HORAS_RECORDATORIO and e["recordatorios"] == 0:
            faro.recordar(e["id"])
            print(f"   🔔 Recordatorio enviado a {persona} (email en buzon/)")
        else:
            print("   ✔️  Dentro de plazo")
