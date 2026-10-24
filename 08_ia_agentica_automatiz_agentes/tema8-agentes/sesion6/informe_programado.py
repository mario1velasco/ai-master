"""Sesión 6 · Demo II: un agente que trabaja solo, cada mañana.

Nadie le escribe: lo lanza una tarea programada. Consulta los tickets del
servidor, revisa los pedidos que necesite y escribe el informe diario de
soporte para el equipo. Lo guarda en datos/informes/ y, si se indica, lo
publica en un canal (un webhook entrante de Slack, Teams o similar).

Uso:
  python -m sesion6.informe_programado
  python -m sesion6.informe_programado --enviar-a https://hooks.slack.com/services/...

Programarlo (cada día laborable a las 8:00):
  cron (Linux/macOS):  0 8 * * 1-5  cd /ruta/tema8-agentes && .venv/bin/python -m sesion6.informe_programado
  Windows:             Programador de tareas → acción «python -m sesion6.informe_programado»
  n8n:                 nodo Schedule Trigger → nodo Execute Command con el mismo comando
"""
import argparse
from datetime import date
from pathlib import Path

import httpx
from langchain_core.tools import tool

from comun.grafo import construir_agente
from comun.herramientas_lc import consultar_pedido
from comun.modelo_lc import crear_modelo

SERVIDOR = "http://127.0.0.1:8000"
CARPETA = Path("datos/informes")

INSTRUCCIONES = (
    "Eres el analista de soporte de Lumen Shop. Prepara el informe diario para el equipo: cuántos tickets "
    "hay por estado, cuáles esperan aprobación humana (y qué acción proponen), cuáles se han escalado y por "
    "qué, y una recomendación final. Usa las herramientas; no inventes datos. Formato Markdown breve, en español."
)


def crear_listar_tickets(servidor: str = SERVIDOR, http=httpx):
    @tool
    def listar_tickets(estado: str = "") -> dict:
        """[Lectura] Lista los tickets del sistema de soporte. `estado` filtra por: procesando, resuelto,
        pendiente_aprobacion o escalado_a_humano. Vacío devuelve todos."""
        try:
            respuesta = http.get(f"{servidor}/tickets", params={"estado": estado} if estado else None)
            return respuesta.json()
        except Exception:
            return {"error": "El sistema de tickets no responde. Indícalo en el informe."}
    return listar_tickets


def generar_informe(modelo=None, servidor: str = SERVIDOR, http=httpx, carpeta: Path = CARPETA) -> Path:
    agente = construir_agente(modelo or crear_modelo(), [crear_listar_tickets(servidor, http), consultar_pedido],
                              INSTRUCCIONES)
    hoy = date.today().isoformat()
    resultado = agente.invoke({"messages": [("user", f"Prepara el informe de soporte del {hoy}.")]},
                              {"recursion_limit": 20})
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"informe_{hoy}.md"
    ruta.write_text(resultado["messages"][-1].content, encoding="utf-8")
    return ruta


def publicar(ruta: Path, url_webhook: str, http=httpx):
    """Publica el informe en un canal mediante un webhook entrante (formato compatible con Slack)."""
    return http.post(url_webhook, json={"text": ruta.read_text(encoding="utf-8")}, timeout=10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--servidor", default=SERVIDOR)
    parser.add_argument("--enviar-a", help="URL de un webhook entrante (Slack, Teams...)")
    args = parser.parse_args()
    ruta = generar_informe(servidor=args.servidor)
    print(f"📄 Informe guardado en {ruta}\n\n{ruta.read_text(encoding='utf-8')}")
    if args.enviar_a:
        print("📤 Publicado:", publicar(ruta, args.enviar_a).status_code)
