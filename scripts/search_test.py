"""Recherche Top-k dans Qdrant, avec filtre optionnel sur les métadonnées.

Exemples :
    python scripts/search_test.py                                   # démo : sans puis avec filtre
    python scripts/search_test.py "Comment rendre l'eau potable ?"
    python scripts/search_test.py "eau potable" --category cdc --k 5
    python scripts/search_test.py "cholera" --doc-id who_communicable_disease_emergencies

Utilisez le MÊME modèle que pour l'ingestion (variable EMBED_MODEL ou --model).
"""
from __future__ import annotations

import argparse
import os
import sys
import time

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "guides")
DEFAULT_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-m3")

DEMO_QUERY = "Comment rendre l'eau potable en situation d'urgence ?"
DEMO_CATEGORY = "oms"


def build_filter(category: str | None, doc_id: str | None) -> models.Filter | None:
    conditions = []
    if category:
        conditions.append(models.FieldCondition(key="category", match=models.MatchValue(value=category)))
    if doc_id:
        conditions.append(models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id)))
    return models.Filter(must=conditions) if conditions else None


def search(client: QdrantClient, model: SentenceTransformer, args, query: str,
           category: str | None, doc_id: str | None) -> None:
    label = f'"{query}"'
    if category:
        label += f"  [category={category}]"
    if doc_id:
        label += f"  [doc_id={doc_id}]"
    print(f"\n=== {label} ===")

    prefix = "query: " if "e5" in args.model.lower() else ""
    started = time.perf_counter()
    vector = model.encode(prefix + query, normalize_embeddings=True).tolist()
    result = client.query_points(
        collection_name=args.collection,
        query=vector,
        limit=args.k,
        query_filter=build_filter(category, doc_id),
        with_payload=True,
    )
    elapsed = (time.perf_counter() - started) * 1000

    if not result.points:
        print("Aucun résultat (filtre trop strict, ou collection vide ?).")
        return
    for rank, point in enumerate(result.points, start=1):
        p = point.payload
        snippet = p["text"][: args.snippet].replace("\n", " ")
        print(f"[{rank}] score={point.score:.4f} | {p['category']} | {p['doc_id']} | page {p['page']} | {p['type']}")
        print(f"    {snippet}...")
    print(f"({len(result.points)} résultats en {elapsed:.0f} ms)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Recherche Top-k dans Qdrant")
    ap.add_argument("query", nargs="?", help="la question (sans argument : mode démo)")
    ap.add_argument("--category", help="filtre : ready_gov, cdc, oms, sphere")
    ap.add_argument("--doc-id", help="filtre sur un document précis")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--snippet", type=int, default=220, help="longueur de l'extrait affiché")
    ap.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    ap.add_argument("--collection", default=DEFAULT_COLLECTION)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    client = QdrantClient(url=args.qdrant_url, check_compatibility=False)
    if not client.collection_exists(args.collection):
        sys.exit(f"La collection '{args.collection}' n'existe pas. Lancez d'abord scripts/ingest.py.")
    print(f"Collection '{args.collection}' : {client.count(args.collection, exact=True).count} points | modèle : {args.model}")

    model = SentenceTransformer(args.model)
    if args.query:
        search(client, model, args, args.query, args.category, args.doc_id)
    else:  # mode démo : même question sans filtre, puis avec filtre
        search(client, model, args, DEMO_QUERY, None, None)
        search(client, model, args, DEMO_QUERY, DEMO_CATEGORY, None)


if __name__ == "__main__":
    main()
