from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import tempfile
import time
from umbra.domain.models import Answer
from umbra.generation.context import citation_warnings
from umbra.generation.flows import standard, tool_rag

PROMPT_VERSION = "umbra-grounded-v1"


class RAGService:
    def __init__(self, settings, retriever, model):
        self.settings, self.retriever, self.model = settings, retriever, model

    def answer(self, question, mode="standard", history=None, use_cache=True):
        question = question.strip()
        if not question or len(question) > 2000 or mode not in ("standard", "tools"):
            raise ValueError("Pregunta vacía, demasiado larga o modo no válido.")
        history = history or []
        if len(history) > 8 or any(set(m) != {"role", "content"} or m["role"] not in ("user", "assistant")
            or not isinstance(m["content"], str) or len(m["content"]) > 4000 for m in history):
            raise ValueError("Historial no válido.")
        started = time.perf_counter()
        identity = {"question": question, "mode": mode, "history": history,
                    "settings": asdict(self.settings), "prompt": PROMPT_VERSION,
                    "baseline": self.retriever.baseline.payload}
        signature = hashlib.sha256(json.dumps(identity, sort_keys=True, default=str).encode()).hexdigest()
        cache = self.settings.artifacts / "answers" / (signature + ".json")
        if self.settings.answer_cache and use_cache and cache.exists():
            result = Answer(**json.loads(cache.read_text()))
            result.cached = True
            result.latency_ms = (time.perf_counter() - started) * 1000
            return result
        flow = standard if mode == "standard" else tool_rag
        text, sources, trace, turns = flow(question, history, self.retriever, self.model, self.settings)
        warnings = citation_warnings(text, sources)
        if warnings:
            text = "No puedo presentar una respuesta fundamentada: la generación no superó la comprobación de citas. Revisa las fuentes recuperadas."
        if not sources:
            text = "No he encontrado evidencia suficiente en la colección para responder."
        result = Answer(question, mode, text, sources, trace,
            {"llm_calls": len(turns), "input_tokens": sum(t.input_tokens for t in turns),
             "output_tokens": sum(t.output_tokens for t in turns), "search_calls": len(trace)},
            round((time.perf_counter()-started)*1000, 1), warnings=warnings)
        if self.settings.answer_cache and use_cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", dir=cache.parent, delete=False, encoding="utf-8") as stream:
                json.dump(result.to_dict(), stream, ensure_ascii=False)
                temporary = Path(stream.name)
            temporary.replace(cache)
        return result
