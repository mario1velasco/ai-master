import json
import threading
from functools import cached_property
from umbra.domain.models import Evidence


class Corpus:
    def __init__(self, settings):
        self.path = settings.session06 / "data/trec-covid/corpus.jsonl"
        self._lock = threading.Lock()
        self._records = None

    @property
    def records(self):
        with self._lock:
            if self._records is None:
                if not self.path.is_file():
                    raise FileNotFoundError("Falta el corpus de Sesión 06; no se descarga automáticamente.")
                with self.path.open(encoding="utf-8") as stream:
                    self._records = {str(r["_id"]): r for r in map(json.loads, stream)}
        return self._records

    def document(self, identifier, score=0):
        row = self.records[identifier]
        return Evidence(identifier, row.get("title") or "Sin título", row.get("text") or "", score)

    def catalog(self, query="", limit=12):
        terms = query.casefold().split()
        result = []
        for identifier, row in self.records.items():
            text = ((row.get("title") or "") + " " + (row.get("text") or "")).casefold()
            if all(term in text for term in terms):
                result.append({"id": identifier, "title": row.get("title") or "Sin título",
                               "text": (row.get("text") or "")[:350]})
            if len(result) == limit:
                break
        return result
