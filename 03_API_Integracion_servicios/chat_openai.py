"""
Chat simple por terminal usando la API de OpenAI.
Requiere: API key de OpenAI en la variable de entorno OPENAI_API_KEY
    export OPENAI_API_KEY="tu-api-key-aqui"
"""

import os
import json
import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()

console = Console()

BASE_URL = "https://api.openai.com/v1"
MODEL = "gpt-4o-mini"
API_KEY = os.getenv("OPENAI_API_KEY")


def preguntar_a_openai(prompt: str, historial: list) -> str:
    """Envía un mensaje a la API de OpenAI con historial y devuelve la respuesta."""
    if not API_KEY:
        return "[ERROR] Variable de entorno OPENAI_API_KEY no está configurada."

    historial.append({"role": "user", "content": prompt})

    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "max_tokens": 1024,
        "stream": True,
        "messages": historial
    }

    respuesta_completa = ""
    response = None
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        response.raise_for_status()

        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue

            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break

                try:
                    evento = json.loads(data_str)
                    if evento.get("choices") and len(evento["choices"]) > 0:
                        delta = evento["choices"][0].get("delta", {})
                        texto = delta.get("content", "")
                        if texto:
                            respuesta_completa += texto
                except json.JSONDecodeError:
                    pass

    except requests.exceptions.ConnectionError:
        historial.pop()
        return "[ERROR] No se ha podido conectar con la API de OpenAI. ¿Tienes conexión a internet?"
    except requests.exceptions.HTTPError as e:
        historial.pop()
        resp = e.response if hasattr(e, 'response') else response
        if resp is not None:
            try:
                error_data = resp.json()
                error_msg = error_data.get("error", {}).get("message", resp.text)
            except:
                error_msg = resp.text
            return f"[ERROR] {resp.status_code}: {error_msg}"
        return "[ERROR] Error HTTP desconocido al contactar con OpenAI."

    historial.append({"role": "assistant", "content": respuesta_completa})
    return respuesta_completa


def main():
    print(f"=== Chat con OpenAI ({MODEL}) ===")
    print("Escribe 'salir' en cualquier momento para terminar.\n")

    historial = []

    while True:
        pregunta = input()

        if pregunta.strip().lower() in ("salir", "exit", "quit"):
            print("¡Hasta luego!")
            break

        console.print("\nPensando...\n")
        respuesta = preguntar_a_openai(pregunta, historial)
        console.print("Assistant:")
        console.print(Markdown(respuesta))
        console.print()


if __name__ == "__main__":
    main()
