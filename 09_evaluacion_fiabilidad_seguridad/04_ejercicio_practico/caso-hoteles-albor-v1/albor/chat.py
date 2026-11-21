"""Prueba el asistente con una pregunta.

Uso:
  python -m albor.chat "¿Hay habitaciones dobles en Albor Playa el 20 de diciembre?"
  python -m albor.chat --email lucia.martin@correo.com "Quiero cancelar mi reserva"

`--email` simula que el huésped ha iniciado sesión en la web.
Al final se muestran los efectos: cancelaciones, reembolsos y emails enviados.
"""
import argparse

from albor import hotel
from albor.agente import mostrar
from albor.configuracion import crear_agente

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pregunta")
    parser.add_argument("--email", help="Email del huésped identificado en la web")
    args = parser.parse_args()
    hotel.reiniciar()
    resultado = crear_agente({"email": args.email} if args.email else {}).ejecutar(args.pregunta)
    mostrar(resultado)
    for nombre, lista in (("Cancelaciones", hotel.CANCELACIONES), ("Reembolsos", hotel.REEMBOLSOS),
                          ("Emails enviados", hotel.BANDEJA_SALIDA)):
        if lista:
            print(f"   ⚠️  {nombre}: {lista}")
    if resultado.pendientes_aprobacion:
        print(f"   ✋ Pendiente de aprobación: {resultado.pendientes_aprobacion}")
