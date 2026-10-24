import json
import secrets
import os
from dotenv import load_dotenv
from urllib.parse import urlencode
import webbrowser
import requests
import yaml

load_dotenv()

state = secrets.token_urlsafe(16)
params = {
    "response_type": "code",
    "client_id": os.environ["CLIENT_ID"],
    "redirect_uri": os.environ["REDIRECT_URI"],
    "scope": "openid profile email",
    "state": state,
}

url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"

webbrowser.open(url)

input("Press Enter after you have been redirected back to the application...")

with open("callback_data.yaml", "r") as file:
    callback_data = yaml.safe_load(file)

    if callback_data["state"] != state:
        raise ValueError("State does not match! Possible CSRF attack.")
        exit(1)

params = {
    "grant_type": "authorization_code",
    "code": callback_data["code"],
    "redirect_uri": os.environ["REDIRECT_URI"],
    "client_id": os.environ["CLIENT_ID"],
    "client_secret": os.environ["CLIENT_SECRET"],
}

response = requests.post("https://www.linkedin.com/oauth/v2/accessToken", data=params)

response.raise_for_status()

token = response.json()["access_token"]

response = requests.get(
    "https://api.linkedin.com/v2/me",
    headers={"Authorization": f"Bearer {token}"},
)

print(json.dumps(response.json(), indent=4))