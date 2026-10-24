from IPython.display import display, Markdown
import pandas as pd


def show_answer(answer):
    display(Markdown(answer.text))
    display(pd.DataFrame([{k: s[k] for k in ("label", "id", "title")} for s in answer.sources]))
    display(pd.DataFrame(answer.trace))
    display(pd.DataFrame([{"mode": answer.mode, "cached": answer.cached, "latency_ms": answer.latency_ms, **answer.usage}]))
    for warning in answer.warnings:
        print(warning)
