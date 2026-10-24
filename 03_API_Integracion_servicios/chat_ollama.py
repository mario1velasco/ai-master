"""
Chat simple por terminal usando la API local de Ollama.
Requiere: Ollama instalado y corriendo (ollama serve) y el modelo descargado:
    ollama pull llama3.2
"""

import requests

BASE_URL = "http://localhost:11434"
MODEL = "llama3.2"


def preguntar_a_ollama(prompt: str) -> str:
    """Envía un mensaje al endpoint /api/chat de Ollama y devuelve la respuesta."""
    url = f"{BASE_URL}/api/chat"
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    response = None
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return "[ERROR] No se ha podido conectar con Ollama. ¿Está corriendo? (ollama serve)"
    except requests.exceptions.HTTPError as e:
        resp = e.response or response
        if resp is not None:
            return f"[ERROR] {resp.status_code}: {resp.json().get('error', resp.text)}"
        return "[ERROR] Error HTTP desconocido al contactar con Ollama."

    data = response.json()
    return data["message"]["content"]


def main():
    print(f"=== Chat con Ollama ({MODEL}) ===")
    print("Escribe 'salir' en cualquier momento para terminar.\n")

    while True:
        pregunta = input("¿Qué quieres saber? ")

        if pregunta.strip().lower() in ("salir", "exit", "quit"):
            print("¡Hasta luego!")
            break

        print("\nPensando...\n")
        respuesta = preguntar_a_ollama(pregunta)
        print(f"Ollama: {respuesta}\n")

        continuar = input("¿Quieres hacer otra pregunta? (s/n): ")
        if continuar.strip().lower() not in ("s", "si", "sí", "y", "yes"):
            print("¡Hasta luego!")
            break


if __name__ == "__main__":
    main()
