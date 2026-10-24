"""Envuelve el cliente del modelo para contar llamadas, tokens y tiempo."""
import time
from types import SimpleNamespace


class ClienteMedido:
    def __init__(self, cliente):
        self._cliente = cliente
        self.llamadas, self.tokens, self.segundos = 0, 0, 0.0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._crear))

    def _crear(self, **kwargs):
        inicio = time.perf_counter()
        respuesta = self._cliente.chat.completions.create(**kwargs)
        self.segundos += time.perf_counter() - inicio
        self.llamadas += 1
        self.tokens += getattr(getattr(respuesta, "usage", None), "total_tokens", 0) or 0
        return respuesta

    def resumen(self) -> str:
        return f"{self.llamadas} llamadas · {self.tokens} tokens · {self.segundos:.1f} s"
