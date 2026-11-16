"""Solución · Reto de la sesión 2: seguir la procedencia del contenido (taint tracking).

Marcar las reseñas como no fiables ayuda, pero un modelo puede seguir
obedeciendo lo que lee. La defensa estructural es otra: en cuanto el agente
ha leído contenido escrito por terceros en esta conversación, el contexto
queda «contaminado» y las acciones irreversibles se bloquean, digan lo que
digan las instrucciones. No dependemos de que el modelo resista: el código
corta el camino entre el texto malicioso y la acción.

Es una versión sencilla de la idea de separar datos no fiables y acciones
(como hacen propuestas de defensa como CaMeL o la «regla de dos»).

Uso:  python -m soluciones.sesion2.deber_reto
"""
from comun import tienda
from comun.agente import Agente, mostrar
from comun.herramientas import CATALOGO, TODAS
from sesion2.guardarrailes import Guardarrailes
from sesion2.inyeccion import CONTEXTO, PREGUNTA

FUENTES_NO_FIABLES = {"leer_resenas"}


class GuardarrailesConProcedencia(Guardarrailes):
    def revisar_entrada(self, texto, contexto):
        contexto["contaminado"] = False  # cada conversación empieza limpia
        return super().revisar_entrada(texto, contexto)

    def revisar_resultado(self, nombre, resultado, contexto):
        if nombre in FUENTES_NO_FIABLES:
            contexto["contaminado"] = True
        return super().revisar_resultado(nombre, resultado, contexto)

    def revisar_herramienta(self, nombre, argumentos, contexto):
        if contexto.get("contaminado") and CATALOGO.get(nombre, {}).get("riesgo") == "irreversible":
            return self._anotar("herramienta", "se ha leído contenido no fiable en esta conversación: las acciones "
                                               "irreversibles necesitan confirmación de una persona")
        return super().revisar_herramienta(nombre, argumentos, contexto)


if __name__ == "__main__":
    tienda.reiniciar()
    # Incluso con TODAS las herramientas, el camino reseña → acción queda cortado
    mostrar(Agente(herramientas=TODAS, contexto=dict(CONTEXTO), guardas=GuardarrailesConProcedencia()).ejecutar(PREGUNTA))
    print(f"   📤 Emails: {tienda.BANDEJA_SALIDA or 'ninguno'} · 💸 Reembolsos: {tienda.REEMBOLSOS or 'ninguno'}")
