"""Solución · Reto de la sesión 4: memoria con criterio de importancia.

Al guardar, el modelo puntúa la importancia de cada memoria de 1 a 10 (una
alergia importa más que «preguntó por el horario»). Al recuperar, la
puntuación combina similitud, recencia e importancia, como en el paper
«Generative Agents» (Park et al., 2023).
"""
from comun.llm import MODELO
from comun.utilidades import extraer_json
from sesion4.memoria import MemoriaClientes

EXTRACTOR_CON_IMPORTANCIA = (
    "Extrae de la conversación lo que merezca recordarse sobre el cliente de Lumen Shop. Para cada memoria, "
    "puntúa su importancia de 1 (trivial) a 10 (crítica para atenderle bien en el futuro). Responde solo con "
    'JSON: {"memorias": [{"tipo": "semantica", "texto": "...", "importancia": 7}]}'
)


class MemoriaConImportancia(MemoriaClientes):
    def __init__(self, *args, peso_importancia: float = 0.3, **kwargs):
        super().__init__(*args, **kwargs)
        self.peso_importancia = peso_importancia

    def recordar_conversacion(self, email: str, conversacion: str) -> list[dict]:
        respuesta = self._llm().chat.completions.create(model=MODELO, messages=[
            {"role": "system", "content": EXTRACTOR_CON_IMPORTANCIA}, {"role": "user", "content": conversacion}])
        memorias = extraer_json(respuesta.choices[0].message.content)["memorias"]
        for m in memorias:
            self.guardar(email, m["texto"], m["tipo"])
            self.datos[email][-1]["importancia"] = int(m.get("importancia", 5))
        self._guardar_en_disco()
        return memorias

    def puntuar(self, memoria, vector_consulta, ahora) -> float:
        base = super().puntuar(memoria, vector_consulta, ahora)
        return (1 - self.peso_importancia) * base + self.peso_importancia * memoria.get("importancia", 5) / 10
