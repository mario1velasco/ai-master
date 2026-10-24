from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yaml

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=['GET', 'POST', 'DELETE'],
    allow_headers=['*']
)

@api.get('/')
def home():
    return {"message": "Hello World"}

@api.get('/greetings/{username}')
def greetings(username: str):
    return {"message": f"Hello, {username.upper()}"}

@api.get('/callback')
def callback(state: str, code: str):
    with open('callback_result.yaml', 'w') as file:
        yaml.dump({
            'state': state,
            'code': code
        }, file)
    return {
        'message': 'ok'
    }