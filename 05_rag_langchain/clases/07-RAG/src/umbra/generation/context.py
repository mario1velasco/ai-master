import json
import re
import tiktoken

def encoding(model="gpt-4.1-mini"):
    return tiktoken.encoding_for_model(model)


def pack_context(documents, settings, existing=None):
    """Presupuesto de tokens del JSON completo, incluidas etiquetas y títulos."""
    sources = list(existing or [])
    tokenizer = encoding(settings.llm_model)
    seen = {row["id"] for row in sources}
    for document in documents:
        if document.id in seen or not document.text.strip():
            continue
        if len(sources) >= settings.context_k:
            break
        tokens = tokenizer.encode(document.text, disallowed_special=())[:settings.document_tokens]
        entry = {"label": f"D{len(sources) + 1}", "id": document.id,
                 "title": document.title[:500], "text": tokenizer.decode(tokens), "score": document.score}
        while tokens and token_count(sources + [entry], settings.llm_model) > settings.context_tokens:
            tokens = tokens[:-100]
            entry["text"] = tokenizer.decode(tokens)
        if not tokens:
            continue
        sources.append(entry)
        seen.add(document.id)
    return sources


def token_count(sources, model="gpt-4.1-mini"):
    return len(encoding(model).encode(json.dumps(sources, ensure_ascii=False), disallowed_special=()))


def citation_warnings(text, sources):
    allowed = {s["label"] for s in sources}
    citations = set(re.findall(r"\[(D\d+)\]", text))
    warnings = []
    if citations - allowed:
        warnings.append("El modelo citó etiquetas que no estaban en el contexto.")
    if sources and not citations:
        warnings.append("La respuesta no incluye citas verificables; no se presenta como fundamentada.")
    return warnings
