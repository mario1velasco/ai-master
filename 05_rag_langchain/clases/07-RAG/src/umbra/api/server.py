from functools import lru_cache
import os
import threading
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from umbra.configuration.settings import load_settings
from umbra.data.corpus import Corpus
from umbra.retrieval.baseline import Baseline
from umbra.retrieval.hybrid import HybridRetriever
from umbra.generation.client import OpenAIModel
from umbra.generation.service import RAGService

app = FastAPI(title="UMBRA · Biblioteca de investigación")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
busy = threading.BoundedSemaphore(1)


@lru_cache
def settings():
    return load_settings()


@lru_cache
def corpus():
    return Corpus(settings())


@lru_cache
def service():
    return RAGService(settings(), HybridRetriever(settings(), corpus()), OpenAIModel(settings()))


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    mode: Literal["standard", "tools"] = "standard"
    history: list[Message] = Field(default_factory=list, max_length=8)


@app.get("/api/health")
def health():
    try:
        config = settings()
        baseline = Baseline(config)
        ready = corpus().path.is_file() and all(os.getenv(k) for k in ("OPENAI_API_KEY", "PINECONE_API_KEY"))
        return {"configured": bool(ready), "remote_verified": False, "llm": config.llm_model,
                "baseline": baseline.summary(), "message": "Configuración local comprobada; servicios remotos aún no verificados."}
    except (OSError, ValueError, KeyError, StopIteration):
        return {"configured": False, "remote_verified": False,
                "message": "Revisa SESSION06_DIR, el corpus y la decisión congelada de Sesión 06."}


@app.get("/api/catalog")
def catalog(q: str = ""):
    if len(q) > 150:
        raise HTTPException(422, "Consulta de catálogo demasiado larga.")
    try:
        return {"documents": corpus().catalog(q), "search_type": "local_literal"}
    except (OSError, ValueError, KeyError):
        raise HTTPException(503, "No se puede abrir el corpus local. Revisa la ruta de Sesión 06.")


@app.get("/api/documents/{identifier}")
def document(identifier: str):
    try:
        doc = corpus().document(identifier)
        return {"id": doc.id, "title": doc.title, "text": doc.text}
    except KeyError:
        raise HTTPException(404, "Documento no encontrado.")
    except OSError:
        raise HTTPException(503, "Corpus no disponible.")


@app.post("/api/chat")
def chat(request: Question):
    if not busy.acquire(blocking=False):
        raise HTTPException(429, "El librero está atendiendo otra consulta. Inténtalo de nuevo en unos segundos.")
    try:
        result = service().answer(request.question, request.mode, [m.model_dump() for m in request.history])
        return result.to_dict()
    except Exception as error:
        status = getattr(error, "status_code", None)
        if status == 429:
            raise HTTPException(429, "Se ha alcanzado una cuota del proveedor. Revisa los límites o el saldo antes de reintentar.")
        if status in (401, 403):
            raise HTTPException(503, "El proveedor no autoriza la solicitud. Revisa las credenciales y permisos locales.")
        if isinstance(error, (ValueError, FileNotFoundError, KeyError, StopIteration)):
            raise HTTPException(503, "Configuración o recursos incompatibles. Revisa la conexión con Sesión 06.")
        raise HTTPException(502, "No se pudo completar la consulta. No se ha generado una respuesta de sustitución; puedes reintentar.")
    finally:
        busy.release()


static_root = Path(__file__).resolve().parents[3] / "app/dist"
if static_root.is_dir():
    app.mount("/", StaticFiles(directory=static_root, html=True), name="library")
