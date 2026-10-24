"""
Consultando APIs con rate limit.
Hace peticiones a la API de GitHub sin token hasta agotar las 60/hora,
logueando las cabeceras X-RateLimit y la respuesta cuando se bloquea.
"""

import time
import requests
import json

URL = "https://api.github.com/users/octocat"


def loguear_rate_limit(response):
    """Imprime las cabeceras X-RateLimit de la respuesta."""
    limite = response.headers.get("X-RateLimit-Limit")
    restantes = response.headers.get("X-RateLimit-Remaining")
    reset = response.headers.get("X-RateLimit-Reset")

    if reset is not None:
        reset = time.strftime("%H:%M:%S", time.localtime(int(reset)))

    print(
        f"response: {json.dumps(response.json(), indent=2)} | "
        f"Headers: {json.dumps(dict(response.headers), indent=2)} | "
        f"Status: {response.status_code} | "
        f"Limit: {limite} | Remaining: {restantes} | Reset: {reset}"
    )
    return restantes


def agotar_rate_limit():
    """Repite peticiones a GitHub sin token hasta que el rate limit se agote."""
    peticion = 1

    while True:
        print(f"\nPetición {peticion}")
        response = requests.get(URL)
        restantes = loguear_rate_limit(response)

        if response.status_code == 403 and restantes == "0":
            print("\nRate limit agotado. Respuesta de bloqueo:")
            print(response.json())
            break

        peticion += 1


if __name__ == "__main__":
    agotar_rate_limit()
