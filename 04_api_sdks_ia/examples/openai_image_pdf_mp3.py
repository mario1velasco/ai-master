import base64
import os

import requests
from dotenv import load_dotenv

load_dotenv()

openai_url= 'https://api.openai.com/v1/responses'

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'    
}

# ********************* IMAGEN: Solicitud de descripción de imagen *********************
payload = {
    "model": "gpt-4o-mini",
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe la imagen "
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{base64.b64encode(open('examples/imagen.png', 'rb').read()).decode()}"
                }
            ]
        }
    ]
}

response = requests.post(openai_url, headers=headers, json=payload)
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Error: {response.status_code} - {response.text}")
# ********************* IMAGEN: Solicitud de descripción de imagen *********************


# ************************ PDF: Solicitud de descripción de documento PDF *********************
payload = {
    "model": "gpt-4o-mini",
    "input": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe brevemente el contenido del documento PDF adjunto"
                },
                {
                    "type": "input_file",
                    "file_name": "document.pdf",
                    "file_data": f"data:application/pdf;base64,{base64.b64encode(open('examples/document.pdf', 'rb').read()).decode()}"
                }
            ]
        }
    ]
}
# ************************ PDF: Solicitud de descripción de documento PDF *********************

# ********************* AUDIO: Solicitud de descripción de archivo de audio *********************
url_audio = 'https://api.openai.com/v1/audio/transcriptions'

response_audio = requests.post(
    url_audio,
    headers={
        'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'
    },
    data={
        'model': 'gpt-4o-mini-transcribe',
    },
    # ! El fichero es mp3 el mp4 hay que ponerlo sino peta
    files={'file': ('audio.mp4', open('examples/audio.mp3', 'rb'), 'audio/mp4')}
)
# ********************* AUDIO: Solicitud de descripción de archivo de audio *********************

# ********************** BACK END *********************
# ********************** BACK END *********************
# ? @app.post('/image')
# ? def receive_image(image: Base64File):
# ?     """ Receives an image in base64 format and returns its size. """
# ! wb es guardar
# ?     with open(image.filename, 'wb') as f:
# ?         f.write(base64.b64decode(image.file_data))
# ?     return {"message": "Image received and saved successfully"}


# ? @app.post('/audio')
# ? def receive_audio(audio: UploadFile = File(...)):
# ?     """ Receives an audio file in base64 format and returns its size. """
# ?     audio_data = audio.file.read()
# ! wb es guardar
# ?     with open(audio.filename, 'wb') as f:
# ?         f.write(audio_data)
# ?     return {"message": "Audio received and saved successfully"}

# ? @app.post('/multipart')
# ? def receive_multipart(files: list[UploadFile] = File(...)):
# ?     """ Receives multiple files in multipart/form-data format and returns their sizes. """
# ?     for file in files:
# ! wb es guardar
# ?         with open(file.filename, 'wb') as f:
# ?             f.write(file.file.read())
# ?     return {"message": "Files received and saved successfully"}
# ********************** BACK END *********************
# ********************** BACK END *********************
# ********************** BACK END *********************