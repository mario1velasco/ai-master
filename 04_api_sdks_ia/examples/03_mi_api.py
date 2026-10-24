# pip install "fastapi[standard]"
# python -m fastapi run mi_api.py --port 4200

import base64
import hashlib
import hmac
import os
import time

import yaml
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Header, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI()
saved_api_key= os.getenv("MI_API_KEY")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=True)

WEBHOOK_TOLERANCE_SECONDS = 300  # eventos con timestamp fuera de esta ventana se rechazan



# ! CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    # allow_methods=["GET", "POST"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ! Solo se usa 1 o API Key Verification o Bearer Token Verification en la APP, no ambos al mismo tiempo.
# ! API Key Verification 
def verify_api_key(api_key: str = Depends(api_key_header) ):
    if api_key != saved_api_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")  

# !Bearer Token Verification
security = HTTPBearer()
def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token != saved_api_key:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid Bearer Token", 
            headers={"WWW-Authenticate": "Bearer"})

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/greetings/{name}", dependencies=[Depends(verify_api_key)])
def read_greetings(name: str):
    return {"message": f"Hello, {name}!"}


@app.get("/callback", dependencies=[Depends(verify_api_key)])
def callback(code: str, state: str):
    with open("callback_data.yaml", "w") as file:
        yaml.dump({"code": code, "state": state}, file)
    return {"message": "Callback received successfully!"}

@app.get("/bearertoken", dependencies=[Depends(verify_bearer_token)])
def read_bearer_token():
    return {"message": "Bearer token is valid!"}

# ! Webhook
secret_key = os.getenv("MY_SECRET_KEY")  # Clave secreta para verificar la firma del webhook



def process_webhook_event(event:dict):
    # Procesamiento pesado/lento: se ejecuta tras devolver la respuesta al cliente
    for i in range(30):
        print(f"Processing event: {i}")
        time.sleep(1)  # Simula un procesamiento lento

# ! Necesitas ejecutar primero 05_event_creator_webhook.py para generar un evento y obtener la firma, 
# ! luego puedes usar esa firma para probar este endpoint de webhook. En PostMan tienen ya el endpoint y el header de firma,
# ! solo falta enviar el evento (En Body RAW) y el token generado (Headers X-Webhook-Signature) en 05_event_creator_webhook.py
@app.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def webhook(request: Request, background_tasks: BackgroundTasks, x_webhook_signature: str = Header()):
    raw_body = await request.body()

    # ! Verifica que la clave secreta esté configurada
    if secret_key is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Secret key not configured")
    # ! Verifica que el header de firma esté presente
    if not x_webhook_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature header")
    # ! Verifica la firma HMAC-SHA256 del webhook
    signature = hmac.new(secret_key.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, x_webhook_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    payload = await request.json()
    emitted_at = payload.get("emitted_at")
    current_time = int(time.time())
    if abs(current_time - emitted_at) > WEBHOOK_TOLERANCE_SECONDS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event too old")

    # ! Responde rápido: el trabajo real se difiere a background_tasks
    background_tasks.add_task(process_webhook_event, payload)
    return {"message": "Event accepted"}

# * EJEMPLOS DE MULTIPLES FORMATOS DE ARCHIVOS (IMAGENES, AUDIO, VIDEO) EN BASE64 O BINARIO
# * Siempre el frontend mandar en la cabecera content-type: 
# * - application/json, image/png, image/jpeg, audio/mpeg, audio/wav, video/mp4, 
# * - apllication/octet-stream, multipart/form-data, etc.
# * y en el body el evento en formato JSON.

# ! Pydantic model for receiving base64 encoded files
class Base64File(BaseModel):
    filename: str = Field(..., description="The name of the file")
    file_data: str = Field(..., description="The base64 encoded file data")


@app.post('/image')
def receive_image(image: Base64File):
    """ Receives an image in base64 format and returns its size. """
    # ! wb es guardar
    with open(image.filename, 'wb') as f:
        f.write(base64.b64decode(image.file_data))
    return {"message": "Image received and saved successfully"}


@app.post('/audio')
def receive_audio(audio: UploadFile = File(...)):
    """ Receives an audio file in base64 format and returns its size. """
    audio_data = audio.file.read()
    # ! wb es guardar
    with open(audio.filename, 'wb') as f:
        f.write(audio_data)
    return {"message": "Audio received and saved successfully"}

@app.post('/multipart')
def receive_multipart(files: list[UploadFile] = File(...)):
    """ Receives multiple files in multipart/form-data format and returns their sizes. """
    for file in files:
        # ! wb es guardar
        with open(file.filename, 'wb') as f:
            f.write(file.file.read())
    return {"message": "Files received and saved successfully"}