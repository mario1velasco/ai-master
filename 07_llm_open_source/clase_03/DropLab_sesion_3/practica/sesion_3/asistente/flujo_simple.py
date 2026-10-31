"""El MISMO proceso que flujo.py, con funciones de Python y un bucle: sin LangGraph.

Sirve para ver qué aporta el framework. Los nodos son exactamente las mismas funciones; solo cambia
quién las encadena:

    sin framework (aquí)                        con LangGraph (flujo.py)
    ------------------------------------------  ---------------------------------------------------
    un bucle while y un if por tarea            nodos y aristas declarados; el grafo se puede dibujar
    el estado es un dict que actualizamos       el estado tiene un tipo (Estado) y reglas de mezcla
      a mano (cuidado con las listas)             (la traza y los errores se acumulan solos)
    el reintento es otro while                  el reintento es una arista condicional
    la traza, a mano                            stream_mode="updates": cada nodo, al terminar
    —                                           puntos de control, pausa para revisión humana,
                                                  ejecución paralela… (no los usamos hoy)

Para un flujo de siete pasos, las dos versiones son igual de válidas. El framework compensa cuando el
proceso crece (más ramas, pausas para que una persona apruebe, reanudar a medias).
"""

from __future__ import annotations

import time

from langgraph.graph import END

from . import flujo


def ejecutar(pregunta: str, imagen: bytes | None = None, al_avanzar=None, **ajustes) -> dict:
    t0 = time.time()
    estado = flujo.estado_inicial(pregunta, imagen, **ajustes)

    def aplicar(nombre, funcion):
        cambios = funcion(estado) or {}
        for clave, valor in cambios.items():           # las listas que se acumulan, a mano
            estado[clave] = estado.get(clave, []) + valor if clave in ("traza", "errores") else valor
        if al_avanzar:
            al_avanzar(nombre, cambios)

    aplicar("planificar", flujo.planificar)
    nodos = {"leer_imagen": flujo.leer_imagen, "consultar_datos": flujo.consultar_datos,
             "buscar_documentos": flujo.buscar_documentos}
    siguiente = flujo.enrutar(estado)
    while siguiente != "contrastar":                    # una tarea tras otra
        aplicar(siguiente, nodos[siguiente])
        siguiente = flujo.enrutar(estado)
    aplicar("contrastar", flujo.contrastar)
    while True:                                         # redactar y verificar, con un reintento
        aplicar("redactar", flujo.redactar)
        aplicar("verificar", flujo.verificar)
        if flujo.tras_verificar(estado) == END:
            break
    return flujo.resultado(estado, time.time() - t0)
