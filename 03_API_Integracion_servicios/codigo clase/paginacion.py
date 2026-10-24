#%%
import requests
import json
from urllib.parse import urlencode

next_url = "https://pokeapi.co/api/v2/pokemon/"
offset = 0
params = {
    "limit": 50,
    "offset": offset
}

next_url = f'{next_url}?{urlencode(params)}'

#%%
while next_url:
    print(offset)
    response = requests.get(next_url)
    json.dump(response.json(), open(f'./pokemon/pokeapi_result_{offset}.json', 'w'), indent=4)
    next_url = response.json().get("next")
    offset += 50
# %%
