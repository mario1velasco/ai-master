from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import Markdown, display
from retrieval_lab.data.corpus import document_text
from retrieval_lab.evaluation.runner import table
from retrieval_lab.evaluation.selection import candidate_shortlist, conclude_evaluation


def corpus_overview(corpus, queries, qrels, dev_ids, holdout_ids, texts, config):
    display(pd.DataFrame([{"Documentos": len(corpus), "Consultas": len(queries),
                           "Juicios": sum(map(len, qrels.values())), "Desarrollo": len(dev_ids),
                           "Reserva final": len(holdout_ids)}]))
    raw_lengths = pd.Series([len(document_text(c).encode("utf-8")) for c in corpus.values()])
    display(pd.DataFrame({"Bytes UTF-8 por documento": raw_lengths.describe(percentiles=[.5, .95, .99])}).round(1))
    shortened = int((raw_lengths > config.text_max_bytes).sum())
    display(Markdown(f"**{shortened:,} documentos ({shortened / len(corpus):.2%})** superan "
                     f"el límite común de {config.text_max_bytes:,} bytes. "
                     "Se conserva el comienzo del título y del texto; el límite es idéntico para todos los modelos."))
    return shortened


def relevance_profile(queries, qrels, ids, config):
    rows = []
    for qid in ids:
        relevant = sum(g > 0 for g in qrels[qid].values())
        rows.append({"Consulta": qid, "Palabras": len(queries[qid].split()), "Relevantes": relevant,
                     **{f"Relevantes recuperables@{k}": min(k, relevant)
                        for k in config.candidate_depths}})
    frame = pd.DataFrame(rows).set_index("Consulta")
    display(frame.describe().round(3))
    grades = pd.Series([g for q in ids for g in qrels[q].values()]).value_counts().sort_index()
    display(grades.rename_axis("Grado").rename("Juicios en desarrollo").to_frame())
    plt.figure(figsize=(8, 4))
    plt.hist(frame["Relevantes"], bins=10)
    plt.xlabel("Documentos relevantes por consulta de desarrollo")
    plt.ylabel("Número de consultas")
    plt.title("Relevantes por consulta: denominador normalizado = min(k, relevantes)")
    plt.tight_layout()
    plt.show()
    return frame


def show_results(results):
    columns = ["Experimento", "nDCG@10", "Precision@10", "MRR@10", "Recall normalizado@k", "MAP@k",
               "p95 (ms)", "RU por consulta"]
    display(table(results)[columns].round(4))


def controlled_comparisons(results, config):
    frame = table(results)
    comparable = frame[(frame["Candidatos por rama"] == config.comparison_depth) &
                       (frame["Estrategia"] == "densa")]
    if comparable["Modelo"].nunique() > 1:
        display(Markdown("**Modelo, manteniendo dimensión y profundidad:**"))
        display(comparable[comparable["Dimensiones"] == config.reference_dimension][
            ["Modelo", "Dimensiones", "nDCG@10", "Recall normalizado@k", "p95 (ms)"]].round(4))
    display(Markdown("**Dimensión, manteniendo modelo, estrategia y profundidad:**"))
    display(comparable[["Modelo", "Dimensiones", "nDCG@10", "Recall normalizado@k", "p95 (ms)"]]
            .sort_values(["Modelo", "Dimensiones"]).round(4))


def depth_and_hybrid(results, config, model):
    frame = table(results)
    selected = frame[(frame["Modelo"] == model) & (frame["Dimensiones"] == config.reference_dimension)]
    display(selected[["Estrategia", "Candidatos por rama", "nDCG@10", "Recall normalizado@k",
                      "Relevantes recuperables@k", "p95 (ms)", "RU por consulta"]]
            .sort_values(["Estrategia", "Candidatos por rama"]).round(4))
    plt.figure(figsize=(8, 4))
    for strategy, group in selected.groupby("Estrategia"):
        group = group.sort_values("Candidatos por rama")
        plt.plot(group["Candidatos por rama"], group["nDCG@10"], marker="o", label=strategy)
    plt.xlabel("Candidatos solicitados a cada rama")
    plt.ylabel("nDCG@10 de desarrollo")
    plt.title(f"¿Más candidatos cambian los diez primeros? · {model}")
    plt.legend()
    plt.tight_layout()
    plt.show()


def inspect_query(result, qid, queries, corpus, qrels, limit=5):
    display(Markdown(f"**Consulta {qid}:** {queries[qid]}"))
    rows = [{"Posición": position, "ID": doc_id, "Título": corpus[doc_id]["title"],
             "Relevancia": qrels[qid].get(doc_id, "sin juicio"),
             "Puntuación interna": score, "Inicio del texto": corpus[doc_id]["text"][:240]}
            for position, (doc_id, score) in enumerate(result["run"][qid][:limit], 1)]
    display(pd.DataFrame(rows))


def error_analysis(reference, candidate, queries, corpus, qrels):
    deltas = (candidate["metrics"]["nDCG@10"] - reference["metrics"]["nDCG@10"]).sort_values()
    selected = list(dict.fromkeys([deltas.index[0], deltas.index[-1]]))
    display(deltas.rename("Delta nDCG@10 B−A").to_frame().loc[selected].round(4))
    for qid in selected:
        display(Markdown(f"**A: {reference['arm'].name}**"))
        inspect_query(reference, qid, queries, corpus, qrels, limit=3)
        display(Markdown(f"**B: {candidate['arm'].name}**"))
        inspect_query(candidate, qid, queries, corpus, qrels, limit=3)
    return selected


def select_candidate(results, config, corpus_size, sparse_bytes):
    frame, shortlist, chosen = candidate_shortlist(results, config, corpus_size, sparse_bytes)
    display(shortlist[["Experimento", "nDCG@10", "Recall normalizado@k", "p95 (ms)", "Vectores brutos (GiB)"]].round(4))
    display(Markdown(f"**Candidato provisional: {chosen['Experimento']}**. "
                     "Cumple el presupuesto de búsqueda y queda dentro de la tolerancia de calidad; "
                     "entre esos candidatos minimiza los bytes brutos y después la latencia."))
    plt.figure(figsize=(9, 4))
    for strategy, group in frame.groupby("Estrategia"):
        plt.scatter(group["p95 (ms)"], group["nDCG@10"], label=strategy, alpha=.7)
    plt.xlabel("p95 de búsqueda con embedding precalculado (ms)")
    plt.ylabel("nDCG@10 de desarrollo")
    plt.title("Calidad frente a latencia: cada punto es una configuración")
    plt.legend()
    plt.tight_layout()
    plt.show()
    return results[chosen["Experimento"]]["arm"]


def final_report(results, reference, candidate, config):
    show_results(results)
    delta, conclusion = conclude_evaluation(results, reference, candidate, config)
    display(pd.DataFrame([delta]).round(4))
    display(Markdown(conclusion))
    return delta
