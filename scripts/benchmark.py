"""Benchmark Recall@5 : compare plusieurs collections / modèles sur les requêtes de test.

Lit docs/benchmark_queries.md (question, document attendu, pages attendues, catégorie).
Une requête est réussie si, parmi les k premiers résultats, il y a un chunk du bon
document ET d'une des bonnes pages. On rapporte aussi le score « document seul ».

Chaque exécution (--run) est de la forme  collection=modèle  :

    python scripts/benchmark.py ^
        --run guides=intfloat/multilingual-e5-small ^
        --run guides_small=intfloat/multilingual-e5-small ^
        --run guides_bge=BAAI/bge-m3 ^
        --out docs/benchmark_s2.md

Option --filter : applique la catégorie attendue comme filtre de métadonnées.
"""
from __future__ import annotations

import argparse
import gc
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUERIES = ROOT / "docs" / "benchmark_queries.md"
DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


@dataclass
class Query:
    num: int
    question: str
    doc_id: str
    pages: set[int]
    category: str


def parse_pages(cell: str) -> set[int]:
    """'28-29' -> {28, 29} ; '1 et 2' -> {1, 2} ; '113 (début du chapitre 4)' -> {113}."""
    cell = cell.split("(")[0]
    pages: set[int] = set()
    for token in re.findall(r"\d+(?:\s*-\s*\d+)?", cell):
        if "-" in token:
            a, b = (int(x) for x in re.split(r"\s*-\s*", token))
            pages.update(range(a, b + 1))
        else:
            pages.add(int(token))
    return pages


def load_queries(path: Path) -> list[Query]:
    queries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"\|\s*\d+\s*\|", line):
            continue
        # le dernier champ peut contenir « \| » : on limite le découpage aux 6 premières colonnes
        cells = [c.strip() for c in line.strip().strip("|").split("|", 6)]
        queries.append(Query(int(cells[0]), cells[1], cells[2], parse_pages(cells[3]), cells[4]))
    if not queries:
        sys.exit(f"Aucune requête lue dans {path}")
    return queries


def evaluate(collection: str, model_name: str, queries: list[Query], args) -> list[dict]:
    from qdrant_client import QdrantClient, models
    from sentence_transformers import SentenceTransformer

    client = QdrantClient(url=args.qdrant_url, check_compatibility=False)
    if not client.collection_exists(collection):
        sys.exit(f"La collection '{collection}' n'existe pas.")
    print(f"\n>>> {collection}  ({client.count(collection, exact=True).count} points) | modèle : {model_name}")

    model = SentenceTransformer(model_name)
    prefix = "query: " if "e5" in model_name.lower() else ""
    rows = []
    for q in queries:
        vector = model.encode(prefix + q.question, normalize_embeddings=True).tolist()
        flt = None
        if args.filter:
            flt = models.Filter(must=[models.FieldCondition(
                key="category", match=models.MatchValue(value=q.category))])
        points = client.query_points(
            collection_name=collection, query=vector, limit=args.k,
            query_filter=flt, with_payload=True,
        ).points

        rank_exact = rank_doc = None
        for rank, p in enumerate(points, start=1):
            same_doc = p.payload["doc_id"] == q.doc_id
            if same_doc and rank_doc is None:
                rank_doc = rank
            if same_doc and p.payload["page"] in q.pages and rank_exact is None:
                rank_exact = rank
        rows.append({"q": q, "rank_exact": rank_exact, "rank_doc": rank_doc,
                     "top1": f"{points[0].payload['doc_id']} p.{points[0].payload['page']}" if points else "-"})
        status = f"OK (rang {rank_exact})" if rank_exact else ("doc seul" if rank_doc else "raté")
        print(f"  Q{q.num:<2} {status:<14} {q.question[:70]}")

    del model
    gc.collect()
    return rows


def summarize(rows: list[dict]) -> tuple[float, float]:
    n = len(rows)
    exact = sum(1 for r in rows if r["rank_exact"]) / n
    doc = sum(1 for r in rows if r["rank_doc"]) / n
    return exact, doc


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark Recall@k sur les requêtes de test")
    ap.add_argument("--run", action="append", required=True, metavar="COLLECTION=MODELE")
    ap.add_argument("--queries", type=Path, default=DEFAULT_QUERIES)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--filter", action="store_true", help="filtrer sur la catégorie attendue")
    ap.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    ap.add_argument("--out", type=Path, help="écrire le tableau de résultats (markdown)")
    args = ap.parse_args()

    queries = load_queries(args.queries)
    print(f"{len(queries)} requêtes lues dans {args.queries.name} | k = {args.k} | filtre catégorie : {args.filter}")

    results = {}
    for spec in args.run:
        if "=" not in spec:
            sys.exit(f"--run attend COLLECTION=MODELE, reçu : {spec}")
        collection, model_name = spec.split("=", 1)
        results[spec] = evaluate(collection, model_name, queries, args)

    # --- tableau récapitulatif ---
    lines = [f"# Benchmark Recall@{args.k}", "",
             f"{len(queries)} requêtes ({args.queries.name}), filtre de catégorie : {'oui' if args.filter else 'non'}.", "",
             f"| Exécution (collection=modèle) | Recall@{args.k} (doc + page) | Recall@{args.k} (doc seul) |",
             "|---|---|---|"]
    for spec, rows in results.items():
        exact, doc = summarize(rows)
        lines.append(f"| `{spec}` | {exact:.2f} ({round(exact * len(rows))}/{len(rows)}) | "
                     f"{doc:.2f} ({round(doc * len(rows))}/{len(rows)}) |")

    lines += ["", "## Détail par requête (rang du premier bon résultat, « - » = absent du Top-k)", "",
              "| # | Question | " + " | ".join(f"`{s.split('=')[0]}`" for s in results) + " |",
              "|---|---|" + "---|" * len(results)]
    for i, q in enumerate(queries):
        cells = []
        for rows in results.values():
            r = rows[i]
            cells.append(str(r["rank_exact"]) if r["rank_exact"] else ("doc " + str(r["rank_doc"]) if r["rank_doc"] else "-"))
        lines.append(f"| {q.num} | {q.question} | " + " | ".join(cells) + " |")
    report = "\n".join(lines) + "\n"

    print("\n" + report)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"Résultats écrits dans {args.out}")


if __name__ == "__main__":
    main()
