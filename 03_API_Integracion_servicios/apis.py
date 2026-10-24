#%%
import json

import requests

API_KEY = '5a0f26576a428bfe4d80dce226785e86'
GEO_BASE_URL = "https://api.openweathermap.org/geo/1.0"
WEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

#%%
# Geocoding
geocoding_params = {
    "q": "Madrid,ES",
    "limit": 5,
    "appid": API_KEY
}

geocoding_response = requests.get(
    f"{GEO_BASE_URL}/direct",
    params=geocoding_params,
    timeout=10
)

geocoding_response
# %%
print(f'Method: {geocoding_response.request.method}')
print(f'Url: {geocoding_response.url}')
print(f'Status Code: {geocoding_response.status_code}')
print(f'Reason: {geocoding_response.reason}')
print(f'Response time: {geocoding_response.elapsed}')
print(f'Encoding: {geocoding_response.encoding}')
print(f'Ok?: {geocoding_response.ok}')

# %%
print(f'\nHeaders:\n{json.dumps(dict(geocoding_response.headers), indent=4)}')

# %%
print(f'\nContent:\n{geocoding_response.content}')
# %%
print(f'\nContent:\n{geocoding_response.content}')

# %%
print(f'\nContent:\n{json.dumps(json.loads(geocoding_response.content), indent=4)}')

# %%
print(f'\nContent:\n{json.dumps(geocoding_response.json(), indent=4)}')

# %%
geocoding_response.json()
# %%
geocoding_response.text
# %%
# %%
# %%

# %%
# Levantar error si code != 200
geocoding_response.raise_for_status()



#%%
# Error no results
geocoding_params = {
    "q": "",
    "limit": 5,
    "appid": API_KEY
}

geocoding_response = requests.get(
    f"{GEO_BASE_URL}/direct",
    params=geocoding_params,
    timeout=10
)

geocoding_response
# %%
print(f'Method: {geocoding_response.request.method}')
print(f'Url: {geocoding_response.url}')
print(f'Status Code: {geocoding_response.status_code}')
print(f'Reason: {geocoding_response.reason}')
print(f'Response time: {geocoding_response.elapsed}')
print(f'Encoding: {geocoding_response.encoding}')
print(f'Ok?: {geocoding_response.ok}')

print(f'\nHeaders:\n{json.dumps(dict(geocoding_response.headers), indent=4)}')

print(f'\nContent:\n{geocoding_response.content}')

print(f'\nContent:\n{geocoding_response.content}')


#%%
# Error not found
geocoding_params = {
    "q": "",
    "limit": 5,
    "appid": API_KEY
}

geocoding_response = requests.get(
    f"{GEO_BASE_URL}/pepito",
    params=geocoding_params,
    timeout=10
)

geocoding_response
# %%
print(f'Method: {geocoding_response.request.method}')
print(f'Url: {geocoding_response.url}')
print(f'Status Code: {geocoding_response.status_code}')
print(f'Reason: {geocoding_response.reason}')
print(f'Response time: {geocoding_response.elapsed}')
print(f'Encoding: {geocoding_response.encoding}')
print(f'Ok?: {geocoding_response.ok}')

print(f'\nHeaders:\n{json.dumps(dict(geocoding_response.headers), indent=4)}')

print(f'\nContent:\n{geocoding_response.content}')

print(f'\nContent:\n{geocoding_response.content}')

#%%
from IPython.display import HTML, display

display(HTML(geocoding_response.text))

# %%
# Levantar error si code != 200
geocoding_response.raise_for_status()

#%%
# Varios resultados
# Geocoding
geocoding_params = {
    "q": "Merida",
    "limit": 5,
    "appid": API_KEY
}

geocoding_response = requests.get(
    f"{GEO_BASE_URL}/direct",
    params=geocoding_params,
    timeout=10
)

results = geocoding_response.json()

print(f'Results found: {len(results)}')

#%%
print(f'\nContent:\n{json.dumps(geocoding_response.json(), indent=4)}')

# %%
# Weather
result = results[0]
current_weather_params = {
    "lat": result.get('lat'),
    "lon": result.get('lon'),
    "appid": API_KEY
}

current_weather_response = requests.get(
    f'{WEATHER_BASE_URL}/weather',
    params=current_weather_params,
    timeout=10
)

current_weather_data = current_weather_response.json()

print(f'Content:\n{json.dumps(current_weather_data, indent=4)}')




# %%
# Icon
from pathlib import Path

from IPython.display import Image

weather_icon_code = current_weather_data["weather"][0]["icon"]
weather_icon_url = (
    f"https://openweathermap.org/img/wn/{weather_icon_code}@2x.png"
)
weather_icon_path = Path(f"weather_icon_{weather_icon_code}.png")

weather_icon_response = requests.get(
    weather_icon_url,
    timeout=10
)

print(f'Content Type: {weather_icon_response.headers.get("Content-Type")}')

#%%
weather_icon_path.write_bytes(weather_icon_response.content)
display(Image(filename=str(weather_icon_path)))
