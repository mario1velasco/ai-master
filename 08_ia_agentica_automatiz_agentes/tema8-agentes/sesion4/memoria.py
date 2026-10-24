"""Sesión 4 · Memoria a largo plazo por cliente.

Un almacén vectorial mínimo, escrito a mano para que se vea qué hace por dentro
(en el Tema 5 visteis bases vectoriales completas; aquí lo importante es la
lógica de memoria, no el motor).

- Escribir: tras cada conversación, el modelo extrae qué merece recordarse.
- Recuperar: puntuación = similitud con la consulta + recencia.
- Olvidar: borrar todo lo de un cliente (derecho de supresión, RGPD).
"""
import hashlib
import json
import math
import os
import re
from datetime import datetime
from pathlib import Path

from comun.llm import MODELO, crear_cliente
from comun.utilidades import extraer_json

MODELO_EMBEDDINGS = os.getenv("LLM_EMBED_MODEL", "nomic-embed-text")
RUTA = Path("datos/memoria.json")

EXTRACTOR = (
    "Analiza la conversación entre un cliente y Lumen Shop y extrae solo lo que merezca recordarse en "
    "futuras conversaciones. Tipos: 'semantica' (hechos o preferencias estables del cliente) y "
    "'episodica' (qué pasó en esta interacción, en una frase). No guardes datos de pago ni de salud "
    'más allá de lo necesario para recomendar productos. Responde solo con JSON: '
    '{"memorias": [{"tipo": "semantica", "texto": "..."}]}'
)


def embedding_local(texto: str, dimensiones: int = 256) -> list[float]:
    """Alternativa sin modelo de embeddings: bolsa de palabras con hashing. Peor, pero funciona en cualquier equipo."""
    vector = [0.0] * dimensiones
    for palabra in re.findall(r"\w+", texto.lower()):
        vector[int(hashlib.md5(palabra.encode()).hexdigest(), 16) % dimensiones] += 1.0
    return vector


def coseno(a, b) -> float:
    norma = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / norma if norma else 0.0


class MemoriaClientes:
    def __init__(self, ruta: Path = RUTA, cliente_llm=None, peso_recencia: float = 0.3, vida_media_dias: float = 30):
        self.ruta, self.llm = Path(ruta), cliente_llm
        self.peso_recencia, self.vida_media = peso_recencia, vida_media_dias
        self.datos = json.loads(self.ruta.read_text()) if self.ruta.exists() else {}
        self._usar_embeddings_del_modelo = True

    # --- utilidades -------------------------------------------------------
    def _llm(self):
        self.llm = self.llm or crear_cliente()
        return self.llm

    def _embedding(self, texto: str) -> list[float]:
        if self._usar_embeddings_del_modelo:
            try:
                return self._llm().embeddings.create(model=MODELO_EMBEDDINGS, input=texto).data[0].embedding
            except Exception:
                print("ℹ️  Sin modelo de embeddings disponible: uso la alternativa local.")
                self._usar_embeddings_del_modelo = False
        return embedding_local(texto)

    def _guardar_en_disco(self):
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.ruta.write_text(json.dumps(self.datos, ensure_ascii=False, indent=1))

    # --- escribir ---------------------------------------------------------
    def guardar(self, email: str, texto: str, tipo: str = "semantica", fecha: datetime | None = None):
        self.datos.setdefault(email, []).append({
            "texto": texto, "tipo": tipo, "fecha": (fecha or datetime.now()).isoformat(),
            "vector": self._embedding(texto)})
        self._guardar_en_disco()

    def recordar_conversacion(self, email: str, conversacion: str) -> list[dict]:
        respuesta = self._llm().chat.completions.create(model=MODELO, messages=[
            {"role": "system", "content": EXTRACTOR}, {"role": "user", "content": conversacion}])
        memorias = extraer_json(respuesta.choices[0].message.content)["memorias"]
        for m in memorias:
            self.guardar(email, m["texto"], m["tipo"])
        return memorias

    # --- recuperar --------------------------------------------------------
    def puntuar(self, memoria: dict, vector_consulta, ahora: datetime) -> float:
        dias = (ahora - datetime.fromisoformat(memoria["fecha"])).days
        recencia = 0.5 ** (dias / self.vida_media)
        return (1 - self.peso_recencia) * coseno(vector_consulta, memoria["vector"]) + self.peso_recencia * recencia

    def recuperar(self, email: str, consulta: str, k: int = 3, ahora: datetime | None = None) -> list[str]:
        memorias = self.datos.get(email, [])
        if not memorias:
            return []
        vector, ahora = self._embedding(consulta), ahora or datetime.now()
        ordenadas = sorted(memorias, key=lambda m: self.puntuar(m, vector, ahora), reverse=True)
        return [m["texto"] for m in ordenadas[:k]]

    # --- olvidar ----------------------------------------------------------
    def olvidar(self, email: str) -> int:
        borradas = len(self.datos.pop(email, []))
        self._guardar_en_disco()
        return borradas
