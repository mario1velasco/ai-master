"""Sesión 6 · Simula los sistemas que llaman al agente.

Uso (con el servidor arrancado):
  python -m sesion6.enviar_ticket                 → ticket normal (asíncrono)
  python -m sesion6.enviar_ticket reembolso       → ticket que acaba pidiendo aprobación
  python -m sesion6.enviar_ticket aprobar T-2     → el supervisor aprueba la acción pendiente
  python -m sesion6.enviar_ticket rechazar T-2    → el supervisor la rechaza
  python -m sesion6.enviar_ticket consulta "¿Tenéis protector solar?"   → chat de la web (síncrono)
"""
import sys
import time

import httpx

URL = "http://127.0.0.1:8000"
TICKETS = {
    "normal": {"id": "T-1", "email": "marta.lopez@email.com", "asunto": "Mi pedido",
               "mensaje": "Hola, ¿cómo va mi pedido ORD-10544?"},
    "reembolso": {"id": "T-2", "email": "jorge.ruiz@email.com", "asunto": "Producto roto",
                  "mensaje": "El protector solar del pedido ORD-10598 me llegó con el bote roto. "
                             "Adjunto foto. Quiero que me devolváis el dinero."},
}


def enviar(tipo: str):
    ticket = TICKETS[tipo]
    print("📨", httpx.post(f"{URL}/webhooks/tickets", json=ticket).json())
    while (estado := httpx.get(f"{URL}/tickets/{ticket['id']}").json())["estado"] == "procesando":
        time.sleep(1)
    print("📋", estado)


if __name__ == "__main__":
    accion = sys.argv[1] if len(sys.argv) > 1 else "normal"
    if accion in ("aprobar", "rechazar") and len(sys.argv) > 2:
        decision = {"aprobar": accion == "aprobar", "motivo": "decisión del supervisor"}
        print(httpx.post(f"{URL}/aprobaciones/{sys.argv[2]}", json=decision, timeout=120).json())
    elif accion == "consulta":
        mensaje = sys.argv[2] if len(sys.argv) > 2 else input("Cliente: ")
        print("💬", httpx.post(f"{URL}/consultas", json={"mensaje": mensaje}, timeout=120).json())
    else:
        enviar(accion)
