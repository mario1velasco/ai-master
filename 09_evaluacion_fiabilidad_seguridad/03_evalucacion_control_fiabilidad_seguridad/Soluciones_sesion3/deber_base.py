"""Solución · Deber base de la sesión 3: alertas a partir de los logs.

Una métrica que nadie mira no sirve. Una alerta es una regla sobre las
métricas que avisa cuando algo se sale de lo normal. Cuatro reglas típicas:

- latencia p95 por encima de un umbral (el cliente espera demasiado)
- tasa de errores técnicos alta (el modelo o una API no responden)
- pico de bloqueos de guardarraíles (alguien está probando a atacar el agente)
- acciones irreversibles por encima de lo habitual (posible abuso)

Uso:  python -m sesion3.observabilidad  y después  python -m soluciones.sesion3.deber_base
"""
from sesion3.observabilidad import leer_logs, metricas

UMBRALES = {"latencia_p95": 15.0, "tasa_errores": 0.2, "bloqueos": 3, "acciones_irreversibles": 5}


def alertas(m: dict, umbrales: dict = UMBRALES) -> list[str]:
    avisos = []
    if m["latencia_p95"] > umbrales["latencia_p95"]:
        avisos.append(f"Latencia p95 de {m['latencia_p95']:.1f} s (umbral {umbrales['latencia_p95']} s)")
    if m["conversaciones"] and m["errores_tecnicos"] / m["conversaciones"] > umbrales["tasa_errores"]:
        avisos.append(f"{m['errores_tecnicos']} errores técnicos en {m['conversaciones']} conversaciones")
    total_bloqueos = sum(m["bloqueos"].values())
    if total_bloqueos >= umbrales["bloqueos"]:
        avisos.append(f"{total_bloqueos} bloqueos de guardarraíles: revisa si hay un intento de ataque")
    if m["acciones_irreversibles"] > umbrales["acciones_irreversibles"]:
        avisos.append(f"{m['acciones_irreversibles']} acciones irreversibles: más de lo habitual")
    return avisos


if __name__ == "__main__":
    avisos = alertas(metricas(leer_logs()))
    print("\n".join(f"🚨 {a}" for a in avisos) if avisos else "✅ Ninguna alerta")
