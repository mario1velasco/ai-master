"""La API del Asistente DropLab (FastAPI). El contrato completo, en /docs (OpenAPI).

    GET  /salud                     ¿Están Ollama, el índice y los datos? (no llama a ningún modelo)
    POST /documentos/buscar         buscar fragmentos (RAG: sesión 2 + PDF de junio), sin generar texto
    POST /datos/consulta            una consulta FIJA con parámetros validados (sin modelo)
    POST /tickets/comprobar         subir una imagen (multipart) → extraer, validar, consultar y comparar
    POST /analizar                  pregunta (+ imagen en base64) → el flujo completo → respuesta con evidencias
    POST /analizar/stream           lo mismo, enviando cada paso según termina (NDJSON): lo usa Open WebUI

Todas las respuestas llevan «errores»: una lista de {codigo, componente, mensaje}. Si la petición está mal,
el código HTTP es 4xx; si falla una pieza (Ollama, el índice…), 503, con el mismo formato.

Arranque: uvicorn asistente.api:app --port 8000   (desde practica/sesion_3; lo hace 03_api.py)
"""

from __future__ import annotations

import base64
import json
import queue
import threading
import time
from typing import Literal

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from . import config, datos, documentos, flujo, vision
from .ollama import ErrorComponente
from .ollama import estado as estado_ollama

app = FastAPI(
    title="Asistente DropLab",
    version="3.0",
    description="Datos (SQL de solo lectura), documentos (RAG) y visión (VLM) del caso DropLab, en local. "
                "Las cifras y las comparaciones las calcula el código; el modelo lee imágenes y redacta.",
)

ESTADO_HTTP = {"PREGUNTA_VACIA": 422, "PARAMETRO_NO_VALIDO": 422, "IMAGEN_VACIA": 422, "IMAGEN_NO_VALIDA": 422,
               "IMAGEN_DEMASIADO_GRANDE": 413, "TIPO_NO_VALIDO": 422, "DOCUMENTO_NO_RECONOCIDO": 422}


@app.exception_handler(ErrorComponente)
async def error_componente(_: Request, exc: ErrorComponente):
    return JSONResponse(status_code=ESTADO_HTTP.get(exc.codigo, 503), content={"errores": [exc.como_dict()]})


@app.exception_handler(RequestValidationError)
async def peticion_no_valida(_: Request, exc: RequestValidationError):
    """La petición no cumple el contrato (un campo que falta, que sobra o con otro tipo): el mismo formato de error."""
    errores = [{"codigo": "PETICION_NO_VALIDA", "componente": "api",
                "mensaje": f"{'.'.join(str(x) for x in e.get('loc', []) if x != 'body') or 'petición'}: {e.get('msg', '')}"}
               for e in exc.errors()]
    return JSONResponse(status_code=422, content={"errores": errores})


# ---------------------------------------------------------------------------
# Contratos (lo que entra y lo que sale)
# ---------------------------------------------------------------------------

class Error(BaseModel):
    codigo: str = Field(examples=["OLLAMA_NO_DISPONIBLE"])
    componente: str = Field(examples=["ollama"])
    mensaje: str


class PeticionBuscar(BaseModel):
    model_config = ConfigDict(extra="forbid")          # un campo que no existe es un error, no se ignora
    pregunta: str = Field(min_length=3, examples=["¿Qué semana de junio tuvo el peor porcentaje de líneas completas en Malasaña?"])
    k: int = Field(5, ge=1, le=10)
    modo: Literal["semantica", "palabras", "hibrida"] = "hibrida"


class Fragmento(BaseModel):
    id: int
    cita: str
    titulo: str
    estado: str
    fecha: str
    sustituido_por: str | None = None
    lectura: str | None = Field(None, description="Si la página se leyó con OCR/VLM: con qué y si se ha revisado")
    puntuacion: float | None = None
    anadido: bool = False
    texto: str


class RespuestaBuscar(BaseModel):
    fragmentos: list[Fragmento]
    segundos: float
    errores: list[Error] = []


class PeticionConsulta(BaseModel):
    model_config = ConfigDict(extra="forbid")          # un campo que no existe es un error, no se ignora
    consulta: Literal["resumen_tienda", "pedido", "disponibilidad_en", "roturas_dia"] = Field(
        description="Solo consultas fijas: el SQL lo escribimos nosotros")
    local_id: Literal["MAD-MAL", "MAD-GOY", "BCN-EIX"] = "MAD-MAL"
    pedido_id: str | None = Field(None, examples=["A-MAD-MAL-ORD-0014"])
    instante: str | None = Field(None, examples=["2026-04-06 10:00"])
    dia: str | None = Field(None, examples=["2026-04-06"])
    skus: list[str] = []


class RespuestaConsulta(BaseModel):
    herramienta: str
    titulo: str
    sql: str
    parametros: list
    filas: list[dict]
    errores: list[Error] = []


class PeticionAnalizar(BaseModel):
    model_config = ConfigDict(extra="forbid")          # un campo que no existe es un error, no se ignora
    pregunta: str = Field(min_length=3, examples=["¿Qué cambió en Malasaña y qué demuestra este ticket?"])
    imagen_base64: str | None = Field(None, description="Imagen en base64 o como data URI (data:image/png;base64,…)")
    tipo_imagen: Literal["ticket", "recuento", "albaran"] | None = None
    modelo_texto: str | None = Field(None, examples=[config.MODELO_TEXTO])
    modelo_vision: str | None = Field(None, examples=[config.MODELO_VISION])
    planificador: Literal["modelo", "reglas"] = "modelo"
    reutilizar_lecturas: bool = Field(True, description="Reutilizar la lectura de una imagen idéntica ya leída "
                                                        "(misma huella sha256 y modelo). La traza lo indica.")


class RespuestaAnalizar(BaseModel):
    respuesta: str
    evidencias: list[dict]
    comprobaciones: list[dict]
    limitaciones: list[str]
    verificacion: list[str]
    plan: dict | None
    traza: list[dict]
    errores: list[Error]
    configuracion: dict
    segundos: float
    origen: str


# ---------------------------------------------------------------------------
# Operaciones
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse("/docs")


@app.get("/salud", summary="Estado de las piezas (sin llamar a ningún modelo)")
def salud() -> dict:
    o = estado_ollama()
    piezas = {"api": {"ok": True}, "ollama": o, "indice_rag": documentos.estado()}
    try:
        datos.conexion()
        piezas["datos"] = {"ok": True, "vistas": len(datos.conexion().execute("SHOW TABLES").fetchall())}
    except Exception as exc:  # noqa: BLE001
        piezas["datos"] = {"ok": False, "error": str(exc)}
    faltan = [m for m in (config.MODELO_TEXTO, config.MODELO_VISION, "bge-m3")
              if o.get("ok") and not any(i.split(":latest")[0] == m.split(":latest")[0] for i in o["instalados"])]
    piezas["modelos"] = {"ok": not faltan, "texto": config.MODELO_TEXTO, "vision": config.MODELO_VISION, "faltan": faltan}
    return {"ok": all(p.get("ok") for p in piezas.values()), "piezas": piezas}


@app.post("/documentos/buscar", response_model=RespuestaBuscar, summary="Buscar en los documentos (RAG: sesión 2 + PDF de junio)")
def buscar_documentos(p: PeticionBuscar):
    t0 = time.time()
    frags = documentos.buscar(p.pregunta, k=p.k, modo=p.modo)
    return {"fragmentos": frags, "segundos": round(time.time() - t0, 2), "errores": []}


@app.post("/datos/consulta", response_model=RespuestaConsulta, summary="Una consulta fija, con parámetros validados")
def consulta(p: PeticionConsulta):
    if p.consulta == "resumen_tienda":
        r = datos.resumen_tienda(p.local_id)
    elif p.consulta == "pedido":
        r = datos.pedido(p.pedido_id or "")
    elif p.consulta == "disponibilidad_en":
        r = datos.disponibilidad_en(p.local_id, p.instante or "", p.skus)
    else:
        r = datos.roturas_dia(p.local_id, p.dia or "")
    return {k: r[k] for k in ("herramienta", "titulo", "sql", "parametros", "filas")} | {"errores": []}


@app.post("/tickets/comprobar", summary="Comprobar una imagen (ticket, recuento o albarán) con los registros")
async def comprobar(imagen: UploadFile = File(..., description="PNG o JPEG"),
                    tipo: Literal["ticket", "recuento", "albaran"] | None = Form(None),
                    modelo_vision: str | None = Form(None), reutilizar_lecturas: bool = Form(True)) -> dict:
    contenido = await imagen.read()
    r = vision.analizar_imagen(contenido, tipo=tipo, modelo=modelo_vision, usar_cache=reutilizar_lecturas)
    return {**r, "archivo": imagen.filename, "errores": []}


def _imagen(p: PeticionAnalizar) -> bytes | None:
    return vision.desde_data_uri(p.imagen_base64) if p.imagen_base64 else None


def _ajustes(p: PeticionAnalizar) -> dict:
    return {"tipo_imagen": p.tipo_imagen, "modelo_texto": p.modelo_texto, "modelo_vision": p.modelo_vision,
            "planificador": p.planificador, "reutilizar_lecturas": p.reutilizar_lecturas}


@app.post("/analizar", response_model=RespuestaAnalizar, summary="Pregunta (+ imagen) → flujo completo → respuesta")
def analizar(p: PeticionAnalizar):
    return flujo.ejecutar(p.pregunta, _imagen(p), **_ajustes(p))


@app.post("/analizar/stream", summary="Igual que /analizar, enviando cada paso al terminar (NDJSON)")
def analizar_stream(p: PeticionAnalizar):
    """Cada línea es un JSON: {"tipo": "paso", ...} mientras avanza y {"tipo": "resultado", ...} al final."""
    imagen, ajustes = _imagen(p), _ajustes(p)
    flujo.estado_inicial(p.pregunta, imagen, **ajustes)            # valida antes de empezar a enviar
    cola: queue.Queue = queue.Queue()

    def trabajar():
        try:
            r = flujo.ejecutar(p.pregunta, imagen, al_avanzar=lambda n, c: cola.put(
                {"tipo": "paso", "nodo": n, "traza": c.get("traza", []), "errores": c.get("errores", [])}), **ajustes)
            cola.put({"tipo": "resultado", **r})
        except ErrorComponente as exc:
            cola.put({"tipo": "error", "errores": [exc.como_dict()]})
        except Exception as exc:  # noqa: BLE001
            cola.put({"tipo": "error", "errores": [{"codigo": "ERROR_INTERNO", "componente": "flujo", "mensaje": str(exc)}]})
        cola.put(None)

    threading.Thread(target=trabajar, daemon=True).start()

    def emitir():
        while (x := cola.get()) is not None:
            yield json.dumps(x, ensure_ascii=False, default=str) + "\n"

    return StreamingResponse(emitir(), media_type="application/x-ndjson")


def imagen_b64(ruta) -> str:
    """Ayuda para clientes: una imagen del disco → base64."""
    return base64.b64encode(open(ruta, "rb").read()).decode()
