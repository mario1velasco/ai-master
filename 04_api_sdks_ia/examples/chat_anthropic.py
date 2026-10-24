"""
Chat simple por terminal usando la API de Anthropic.
Requiere: API key de Anthropic en la variable de entorno ANTHROPIC_API_KEY
    export ANTHROPIC_API_KEY="tu-api-key-aqui"
"""

import os
import requests
from dotenv import load_dotenv
from rich.markdown import Markdown
from rich.console import Console

load_dotenv()

console = Console()

BASE_URL = "https://api.anthropic.com/v1"
MODEL = "claude-haiku-4-5-20251001"
API_KEY = os.getenv("ANTHROPIC_API_KEY")


def preguntar_a_anthropic(prompt: str, historial: list) -> str:
    """Envía un mensaje a la API de Anthropic con historial y devuelve la respuesta."""
    if not API_KEY:
        return "[ERROR] Variable de entorno ANTHROPIC_API_KEY no está configurada."

    historial.append({"role": "user", "content": prompt})

    url = f"{BASE_URL}/messages"
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": MODEL,
        "max_tokens": 1024,
        "messages": historial
    }

    response = None
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        historial.pop()
        return "[ERROR] No se ha podido conectar con la API de Anthropic. ¿Tienes conexión a internet?"
    except requests.exceptions.HTTPError as e:
        historial.pop()
        resp = e.response or response
        if resp is not None:
            error_data = resp.json()
            error_msg = error_data.get("error", {}).get("message", resp.text)
            return f"[ERROR] {resp.status_code}: {error_msg}"
        return "[ERROR] Error HTTP desconocido al contactar con Anthropic."

    data = response.json()
    respuesta = data["content"][0]["text"]
    historial.append({"role": "assistant", "content": respuesta})
    return respuesta


def main():
    print(f"=== Chat con Anthropic ({MODEL}) ===")
    print("Escribe 'salir' en cualquier momento para terminar.\n")

    historial = []

    while True:
        pregunta = input()

        if pregunta.strip().lower() in ("salir", "exit", "quit"):
            print("¡Hasta luego!")
            break

        console.print("\nPensando...\n")
        respuesta = preguntar_a_anthropic(pregunta, historial)
        console.print("Claude:")
        console.print(Markdown(respuesta))
        console.print()



if __name__ == "__main__":
    main()
