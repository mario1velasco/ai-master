from dataclasses import dataclass, field, asdict


@dataclass
class Evidence:
    id: str
    title: str
    text: str
    score: float = 0.0


@dataclass
class SearchResult:
    query: str
    documents: list[Evidence]
    trace: dict = field(default_factory=dict)


@dataclass
class Answer:
    question: str
    mode: str
    text: str
    sources: list[dict]
    trace: list[dict]
    usage: dict
    latency_ms: float
    cached: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
