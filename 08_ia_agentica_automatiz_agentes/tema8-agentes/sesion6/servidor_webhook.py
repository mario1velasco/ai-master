"""Sesión 6 · Demo I: el agente integrado en los sistemas de la empresa.

Tres formas de llamar al mismo agente desde fuera:
- POST /webhooks/tickets  → asíncrono: el helpdesk avisa de un ticket nuevo y el
  agente lo procesa en segundo plano. Si quiere reembolsar, el ticket queda
  pendiente hasta que un supervisor decide.
- POST /consultas          → síncrono: el chat de la web pregunta y espera la respuesta.
- GET  /tickets            → lo que consultan otros procesos, como el informe diario.

Arranque:  uvicorn sesion6.servidor_webhook:app --reload
Pruebas:   python -m sesion6.enviar_ticket      ·  documentación: http://127.0.0.1:8000/docs
"""
from fastapi import BackgroundTasks, FastAPI, HTTPException
from langgraph.types import Command
from pydantic import BaseModel

from comun.grafo import acciones_pendientes
from sesion6.agente_tickets import crear_agente_consultas, crear_agente_ticket, formatear_ticket

app = FastAPI(title="Lumen Shop · Agente de tickets")
TICKETS: dict[str, dict] = {}   # en producción: base de datos
fabrica_modelo = None           # permite inyectar un modelo simulado en las pruebas


class Ticket(BaseModel):
    id: str
    email: str
    asunto: str
    mensaje: str


class Decision(BaseModel):
    aprobar: bool
    motivo: str = ""


class Consulta(BaseModel):
    mensaje: str


def _modelo():
    return fabrica_modelo() if fabrica_modelo else None


def _actualizar(id_ticket: str, resultado: dict):
    if acciones := acciones_pendientes(resultado):
        TICKETS[id_ticket].update(estado="pendiente_aprobacion", acciones=acciones)
    else:
        TICKETS[id_ticket].update(estado="resuelto", respuesta=resultado["messages"][-1].content, acciones=None)


def _procesar(ticket: Ticket):
    try:
        resultado = crear_agente_ticket(ticket.email, _modelo()).invoke(
            {"messages": [("user", formatear_ticket(ticket.email, ticket.asunto, ticket.mensaje))]},
            {"configurable": {"thread_id": ticket.id}, "recursion_limit": 20})
        _actualizar(ticket.id, resultado)
    except Exception as e:  # nunca perder un ticket: si falla, pasa a un humano
        TICKETS[ticket.id].update(estado="escalado_a_humano", error=str(e))


# --- Asíncrono: webhook del helpdesk ------------------------------------------
@app.post("/webhooks/tickets", status_code=202)
def recibir_ticket(ticket: Ticket, tareas: BackgroundTasks):
    if ticket.id in TICKETS:  # idempotencia: los webhooks pueden llegar repetidos
        return {"id": ticket.id, "estado": TICKETS[ticket.id]["estado"], "duplicado": True}
    TICKETS[ticket.id] = {"estado": "procesando", "email": ticket.email, "asunto": ticket.asunto}
    tareas.add_task(_procesar, ticket)  # respondemos ya; el agente trabaja en segundo plano
    return {"id": ticket.id, "estado": "procesando"}


@app.get("/tickets")
def listar_tickets(estado: str | None = None):
    return {i: t for i, t in TICKETS.items() if estado is None or t["estado"] == estado}


@app.get("/tickets/{id_ticket}")
def consultar_ticket(id_ticket: str):
    if id_ticket not in TICKETS:
        raise HTTPException(404, "Ticket no encontrado")
    return TICKETS[id_ticket]


# --- Humano en el bucle: panel de aprobaciones ---------------------------------
@app.get("/aprobaciones")
def aprobaciones_pendientes():
    return listar_tickets("pendiente_aprobacion")


@app.post("/aprobaciones/{id_ticket}")
def decidir(id_ticket: str, decision: Decision):
    ticket = TICKETS.get(id_ticket)
    if not ticket or ticket["estado"] != "pendiente_aprobacion":
        raise HTTPException(409, "Este ticket no tiene ninguna acción pendiente de aprobación")
    resultado = crear_agente_ticket(ticket["email"], _modelo()).invoke(
        Command(resume=decision.model_dump()), {"configurable": {"thread_id": id_ticket}})
    _actualizar(id_ticket, resultado)
    return TICKETS[id_ticket]


# --- Síncrono: el chat de la web espera la respuesta ---------------------------
@app.post("/consultas")
def consulta(consulta: Consulta):
    try:
        resultado = crear_agente_consultas(_modelo()).invoke(
            {"messages": [("user", consulta.mensaje)]}, {"recursion_limit": 10})
    except Exception:
        raise HTTPException(503, "El asistente no está disponible. Te atenderá una persona.")
    return {"respuesta": resultado["messages"][-1].content}
