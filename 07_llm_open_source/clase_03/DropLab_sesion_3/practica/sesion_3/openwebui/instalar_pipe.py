"""Instala (o actualiza) la Pipe «DropLab Analista» en Open WebUI y comprueba que funciona.

    python practica/sesion_3/openwebui/instalar_pipe.py                   # crear o actualizar y activar
    python practica/sesion_3/openwebui/instalar_pipe.py --api http://127.0.0.1:8000
    python practica/sesion_3/openwebui/instalar_pipe.py --comprobar       # solo: ¿está y responde?

Se usa la API de Open WebUI (la misma que usa su interfaz). Con WEBUI_AUTH=False, el «inicio de sesión»
sin contraseña devuelve un token de administrador. También se puede hacer a mano: Panel de administración →
Funciones → «+» → pegar droplab_pipe.py → Guardar → activar (ver docs/sesion_3/02).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

AQUI = Path(__file__).resolve().parent
PIPE = AQUI / "droplab_pipe.py"
ID = "droplab_analista"


def token(webui: str) -> str:
    r = requests.post(webui + "/api/v1/auths/signin", json={"email": "", "password": ""}, timeout=10)
    if r.status_code != 200:
        sys.exit(f"No se pudo iniciar sesión en {webui} ({r.status_code}). ¿Está arrancado con WEBUI_AUTH=False?")
    return r.json()["token"]


def main() -> None:
    ap = argparse.ArgumentParser(description="Instalar la Pipe DropLab Analista en Open WebUI.")
    ap.add_argument("--webui", default="http://127.0.0.1:3000")
    ap.add_argument("--api", default="http://127.0.0.1:8000", help="Dirección de la API vista DESDE el contenedor")
    ap.add_argument("--comprobar", action="store_true")
    a = ap.parse_args()
    h = {"Authorization": f"Bearer {token(a.webui)}"}
    existe = requests.get(f"{a.webui}/api/v1/functions/id/{ID}", headers=h, timeout=10).status_code == 200
    if a.comprobar:
        print("Pipe instalada:", "sí" if existe else "NO")
    else:
        cuerpo = {"id": ID, "name": "DropLab Analista", "content": PIPE.read_text(encoding="utf-8"),
                  "meta": {"description": "Datos, documentos e imágenes de DropLab, con evidencias (API de la sesión 3)"}}
        url = f"{a.webui}/api/v1/functions/" + (f"id/{ID}/update" if existe else "create")
        r = requests.post(url, json=cuerpo, headers=h, timeout=30)
        if r.status_code != 200:
            sys.exit(f"Error al {'actualizar' if existe else 'crear'} la Pipe: {r.status_code} {r.text[:400]}")
        f = requests.get(f"{a.webui}/api/v1/functions/id/{ID}", headers=h, timeout=10).json()
        if not f.get("is_active"):
            requests.post(f"{a.webui}/api/v1/functions/id/{ID}/toggle", headers=h, timeout=10)
        requests.post(f"{a.webui}/api/v1/functions/id/{ID}/valves/update", json={"API_URL": a.api}, headers=h, timeout=10)
        print(f"Pipe {'actualizada' if existe else 'creada'} y activa · API_URL = {a.api}")
        # Sin tareas automáticas (título, etiquetas, seguimiento): con la Pipe elegida, cada una sería otro análisis
        cfg = requests.get(f"{a.webui}/api/v1/tasks/config", headers=h, timeout=10).json()
        cfg.update({"ENABLE_TITLE_GENERATION": False, "ENABLE_TAGS_GENERATION": False,
                    "ENABLE_FOLLOW_UP_GENERATION": False, "ENABLE_AUTOCOMPLETE_GENERATION": False,
                    "ENABLE_SEARCH_QUERY_GENERATION": False, "ENABLE_RETRIEVAL_QUERY_GENERATION": False})
        r = requests.post(f"{a.webui}/api/v1/tasks/config/update", json=cfg, headers=h, timeout=10)
        print("Tareas automáticas de Open WebUI (título, etiquetas, seguimiento):",
              "desactivadas" if r.status_code == 200 else f"no se pudieron desactivar ({r.status_code})")
    modelos = requests.get(a.webui + "/api/models", headers=h, timeout=30).json().get("data", [])
    pipe = [m for m in modelos if m["id"].startswith(ID)]
    print("En el selector de modelos:", ", ".join(m["name"] for m in pipe) or "NO aparece")
    try:
        salud = requests.get(a.api + "/salud", timeout=5).json()
        print("API desde este equipo:", "ok" if salud["ok"] else "con problemas: " + str(
            [k for k, v in salud["piezas"].items() if not v.get("ok")]))
    except requests.exceptions.RequestException:
        print(f"API: no responde en {a.api} (arráncala con python practica/sesion_3/03_api.py)")


if __name__ == "__main__":
    main()
