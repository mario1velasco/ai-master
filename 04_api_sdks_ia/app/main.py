from fastapi import FastAPI
from pydantic import BaseModel

from app.config import ANTHROPIC_API_KEYS, DEFAULT_MODEL
from app.services.chat_service import get_chat_reply

app = FastAPI(title="Tema 4 - Integración de modelos de IA")


class ChatRequest(BaseModel):
    message: str
    model: str = DEFAULT_MODEL
    max_tokens: int = 512


@app.get("/health")
def health():
    return {"status": "ok", "keys_configured": len(ANTHROPIC_API_KEYS)}


@app.post("/chat")
def chat(request: ChatRequest):
    reply = get_chat_reply(message=request.message, model=request.model, max_tokens=request.max_tokens)
    return {"model": request.model, "reply": reply}


# ? temperatura -> si = 0 determinista. Cuando mas crece respuestas mas aleatorias. Lo que más se usa
# top_p -> 0,9 la siguiente palabra quiero que tenga un 90% -> Mas determinista
# top_k -> 1 la mas probable
