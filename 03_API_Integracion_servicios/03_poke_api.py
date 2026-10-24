"""
Consultando APIs con paginación.
Recorre los ~1.300 pokémon de PokéAPI siguiendo el enlace "next",
guardando un lote (una página) en cada iteración.
"""

import json
import requests

BASE_URL = "https://pokeapi.co/api/v2/pokemon?limit=100"
OUTPUT_FILE = "pokemon_data.json"


def obtener_pokemons():
    """Recorre todas las páginas de PokéAPI y guarda todos los lotes en un único fichero JSON."""
    url = BASE_URL
    pagina = 1
    todos_los_pokemons = []

    while url:
        print(f"Descargando página {pagina}: {url}")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        lote = data["results"]
        todos_los_pokemons.extend(lote)

        print(f"  Añadidos {len(lote)} pokémon (total: {len(todos_los_pokemons)})")

        url = data["next"]
        pagina += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(todos_los_pokemons, file, ensure_ascii=False, indent=2)

    print(f"\nCompletado: {len(todos_los_pokemons)} pokémon guardados en {OUTPUT_FILE}.")


if __name__ == "__main__":
    obtener_pokemons()
