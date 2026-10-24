from __future__ import annotations

import json
from retrieval_lab.infrastructure.artifacts import file_digest, write_json


def document_text(item):
    return ((item.get("title") or "").strip() + "\n\n" + (item.get("text") or "").strip()).strip()


def prepare_text(text, max_bytes):
    return text.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore").strip() or "[documento sin texto]"


def load_trec_covid(config):
    root = config.data_dir / "trec-covid"
    required = [root / "corpus.jsonl", root / "queries.jsonl", root / "qrels/test.tsv"]
    if not all(p.is_file() for p in required):
        from beir import util
        util.download_and_unzip(
            "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/trec-covid.zip",
            str(config.data_dir))
    corpus, queries, qrels = {}, {}, {}
    with required[0].open(encoding="utf-8") as stream:
        for line in stream:
            item = json.loads(line)
            corpus[str(item["_id"])] = {"title": item.get("title") or "", "text": item.get("text") or ""}
    with required[1].open(encoding="utf-8") as stream:
        for line in stream:
            item = json.loads(line)
            queries[str(item["_id"])] = item["text"]
    import csv
    with required[2].open(encoding="utf-8") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            qrels.setdefault(row["query-id"], {})[row["corpus-id"]] = int(row["score"])
    if any(d not in corpus for grades in qrels.values() for d in grades):
        raise ValueError("Los qrels contienen documentos ausentes.")
    signature = {p.name: file_digest(p) for p in required}
    write_json(config.results_dir / "dataset.json", signature)
    return corpus, queries, qrels, signature
