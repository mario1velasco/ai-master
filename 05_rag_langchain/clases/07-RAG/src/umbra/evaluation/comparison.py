import re


def compare_modes(service, questions):
    """Prueba exploratoria: no reutiliza respuestas cacheadas ni estima calidad factual."""
    rows, answers = [], []
    for question in questions:
        for mode in ("standard", "tools"):
            answer = service.answer(question, mode, use_cache=False)
            answers.append(answer)
            rows.append({"Pregunta": question, "Modo": mode, "Latencia ms": answer.latency_ms,
                "Fuentes entregadas": len(answer.sources), "Citas distintas": len(set(re.findall(r"\[D\d+\]", answer.text))),
                "Avisos": len(answer.warnings), **answer.usage})
    return rows, answers
