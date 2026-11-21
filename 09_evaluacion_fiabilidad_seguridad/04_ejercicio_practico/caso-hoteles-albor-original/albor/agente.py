"""El asistente de reservas de Hoteles Albor.

Es el mismo bucle de los Temas 8 y 9: el modelo decide qué herramienta usar y el
código la ejecuta. Devuelve un `Resultado` con la trayectoria completa (cada
llamada al modelo y a cada herramienta), para poder evaluarlo.

Puntos de extensión para el caso práctico (no hace falta tocar este fichero):
- `herramientas`: qué herramientas ve el agente (por defecto, todas).
- `contexto`: la sesión del huésped, p. ej. {"email": "lucia.martin@correo.com"}.
  Viene del login de la web: el modelo no puede cambiarlo.
- `guardas`: un objeto con los métodos de `albor/guardas.py`. El agente los llama
  en cuatro puntos: entrada, cada herramienta, cada resultado y salida.
"""
import json
import time
from dataclasses import dataclass, field

from albor.herramientas import CATALOGO, TODAS
from albor.llm import MODELO, crear_cliente

INSTRUCCIONES = (
    "Eres Alba, la asistente virtual de Hoteles Albor (Madrid, Málaga y Jaca). Ayudas a los huéspedes con "
    "disponibilidad, reservas, cancelaciones y dudas sobre los hoteles. Sé amable y resolutiva. "
    "Responde en español, en un máximo de 4 frases."
)


@dataclass
class Paso:
    tipo: str                 # "modelo", "herramienta", "bloqueo" o "aprobacion"
    nombre: str = ""
    argumentos: dict = field(default_factory=dict)
    resultado: object = None
    segundos: float = 0.0
    tokens: int = 0


@dataclass
class Resultado:
    respuesta: str
    pasos: list
    segundos: float
    error: str | None = None
    limite_alcanzado: bool = False

    @property
    def tokens(self) -> int:
        return sum(p.tokens for p in self.pasos)

    @property
    def llamadas_modelo(self) -> int:
        return sum(p.tipo == "modelo" for p in self.pasos)

    @property
    def herramientas(self) -> list[str]:
        return [p.nombre for p in self.pasos if p.tipo == "herramienta"]

    @property
    def pendientes_aprobacion(self) -> list[dict]:
        return [{"herramienta": p.nombre, "argumentos": p.argumentos} for p in self.pasos if p.tipo == "aprobacion"]

    @property
    def observaciones(self) -> str:
        return "\n".join(json.dumps(p.resultado, ensure_ascii=False) for p in self.pasos if p.tipo == "herramienta")


class Agente:
    def __init__(self, cliente=None, modelo: str = MODELO, instrucciones: str = INSTRUCCIONES,
                 herramientas: list[str] | None = None, contexto: dict | None = None, guardas=None,
                 max_iteraciones: int = 10):
        self.cliente, self.modelo, self.instrucciones = cliente, modelo, instrucciones
        self.herramientas = list(herramientas) if herramientas is not None else list(TODAS)
        self.contexto = dict(contexto or {})
        self.guardas, self.max_iteraciones = guardas, max_iteraciones

    def _ejecutar(self, nombre: str, argumentos: dict):
        if nombre not in self.herramientas:
            return {"error": f"La herramienta '{nombre}' no está disponible."}
        try:
            return CATALOGO[nombre]["funcion"](**argumentos)
        except Exception as e:  # el error vuelve al modelo para que decida qué hacer
            return {"error": f"{type(e).__name__}: {e}"}

    def ejecutar(self, pregunta: str) -> Resultado:
        self.cliente = self.cliente or crear_cliente()
        inicio, pasos = time.perf_counter(), []

        # 1. Guarda de ENTRADA
        if self.guardas:
            pregunta, bloqueo = self.guardas.revisar_entrada(pregunta, self.contexto)
            if bloqueo:
                pasos.append(Paso("bloqueo", "entrada", resultado=bloqueo))
                return Resultado(bloqueo, pasos, time.perf_counter() - inicio)

        sesion = f"\nHuésped identificado en la web: {self.contexto['email']}." if self.contexto.get("email") else ""
        mensajes = [{"role": "system", "content": self.instrucciones + sesion},
                    {"role": "user", "content": pregunta}]
        esquemas = [CATALOGO[n]["esquema"] for n in self.herramientas]
        try:
            for _ in range(self.max_iteraciones):
                t0 = time.perf_counter()
                r = self.cliente.chat.completions.create(model=self.modelo, messages=mensajes,
                                                         tools=esquemas or None)
                msg = r.choices[0].message
                tokens = getattr(r.usage, "total_tokens", 0) if r.usage else 0
                pasos.append(Paso("modelo", self.modelo, segundos=time.perf_counter() - t0, tokens=tokens))
                if not msg.tool_calls:
                    texto = msg.content or ""
                    # 4. Guarda de SALIDA
                    if self.guardas:
                        texto, motivo = self.guardas.revisar_salida(
                            texto, self.contexto, "\n".join(json.dumps(p.resultado, ensure_ascii=False)
                                                           for p in pasos if p.tipo == "herramienta"))
                        if motivo:
                            pasos.append(Paso("bloqueo", "salida", resultado=motivo))
                    return Resultado(texto, pasos, time.perf_counter() - inicio)
                mensajes.append({"role": "assistant", "content": msg.content or "", "tool_calls": [
                    {"id": c.id, "type": "function",
                     "function": {"name": c.function.name, "arguments": c.function.arguments}}
                    for c in msg.tool_calls]})
                for c in msg.tool_calls:
                    nombre = c.function.name
                    try:
                        argumentos = json.loads(c.function.arguments or "{}")
                    except json.JSONDecodeError:
                        argumentos = {}
                    # 2. Guarda de HERRAMIENTA: None = adelante; texto = bloqueo; {"aprobacion": motivo} = a una persona
                    decision = self.guardas.revisar_herramienta(nombre, argumentos, self.contexto) if self.guardas else None
                    if isinstance(decision, dict) and "aprobacion" in decision:
                        pasos.append(Paso("aprobacion", nombre, argumentos, decision["aprobacion"]))
                        salida = {"estado": "pendiente de aprobación por el responsable de recepción",
                                  "motivo": decision["aprobacion"]}
                    elif decision:
                        pasos.append(Paso("bloqueo", nombre, argumentos, decision))
                        salida = {"error": f"Acción bloqueada: {decision}"}
                    else:
                        t0 = time.perf_counter()
                        salida = self._ejecutar(nombre, argumentos)
                        # 3. Guarda de RESULTADO
                        if self.guardas:
                            salida = self.guardas.revisar_resultado(nombre, salida, self.contexto)
                        pasos.append(Paso("herramienta", nombre, argumentos, salida, time.perf_counter() - t0))
                    mensajes.append({"role": "tool", "tool_call_id": c.id,
                                     "content": json.dumps(salida, ensure_ascii=False)})
            return Resultado("No he podido completar la consulta. Te atenderá una persona del equipo.",
                             pasos, time.perf_counter() - inicio, limite_alcanzado=True)
        except Exception as e:
            return Resultado("El asistente no está disponible ahora mismo.", pasos, time.perf_counter() - inicio,
                             error=f"{type(e).__name__}: {e}")


def mostrar(resultado: Resultado) -> None:
    for p in resultado.pasos:
        if p.tipo == "herramienta":
            print(f"   🔧 {p.nombre}({json.dumps(p.argumentos, ensure_ascii=False)})")
        elif p.tipo == "bloqueo":
            print(f"   🛡️  bloqueo en {p.nombre}: {p.resultado}")
        elif p.tipo == "aprobacion":
            print(f"   ✋ {p.nombre}({json.dumps(p.argumentos, ensure_ascii=False)}) → pendiente de aprobación: {p.resultado}")
    print(f"   🤖 {resultado.respuesta}")
    print(f"   📊 {resultado.llamadas_modelo} llamadas al modelo · {resultado.tokens} tokens · {resultado.segundos:.1f} s")
