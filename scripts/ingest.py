"""Ingestion des guides PDF dans Qdrant (chunking parent-document).

Pipeline : PDF -> blocs de texte propres -> parents -> petits chunks
           -> embeddings -> insertion par lots dans Qdrant.

Exemples :
    python scripts/ingest.py --only ready_gov_emergency --recreate   # test sur 1 PDF
    python scripts/ingest.py --recreate                              # tout le corpus
    EMBED_MODEL=intfloat/multilingual-e5-small python scripts/ingest.py --recreate

Le script est rejouable : les identifiants de points sont déterministes (uuid5),
donc relancer l'ingestion met à jour les points au lieu de les dupliquer.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz  # PyMuPDF (l'ancien nom `fitz` est déprécié)
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
GUIDES_DIR = ROOT / "data" / "raw" / "guides"
SOURCES_MD = ROOT / "data" / "raw" / "SOURCES.md"

# Réglages par défaut (modifiables par variables d'environnement ou options)
DEFAULT_QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DEFAULT_COLLECTION = os.getenv("QDRANT_COLLECTION", "guides")
DEFAULT_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-m3")  # dimension 1024

# PDF dont la détection de tableaux fait planter PyMuPDF (arrêt brutal, sans message d'erreur,
# donc impossible à rattraper avec try/except). Leur texte est lu normalement.
NO_TABLE_DOCS = {"ready_gov_are_you_ready_guide.pdf"}

# PDF téléchargés à la main : ils ne sont pas dans les tableaux de SOURCES.md
MANUAL_URLS = {
    "emergency-water-supply-planning-guide-2019-508.pdf":
        "https://www.cdc.gov/water-emergency/media/pdfs/2024/07/emergency-water-supply-planning-guide-2019-508.pdf",
    "make-water-safe-during-emergency-p.pdf":
        "https://www.cdc.gov/water-emergency/media/pdfs/make-water-safe-during-emergency-p.pdf",
    "basic_preparedness.pdf":
        "https://www.fema.gov/pdf/areyouready/basic_preparedness.pdf",
}


# --------------------------------------------------------------------------
# Métadonnées
# --------------------------------------------------------------------------
def categorize(filename: str) -> str:
    """Catégorie utilisée pour le filtre de la démo (à valider avec Ayoub)."""
    n = filename.lower()
    if n.startswith("who_"):
        return "oms"
    if n.startswith("sphere"):
        return "sphere"
    if n.startswith("cdc_") or "water" in n:
        return "cdc"
    return "ready_gov"


def guess_year(*texts: str) -> str | None:
    for t in texts:
        m = re.search(r"(?<!\d)(20\d\d)(?!\d)", t)
        if m:
            return m.group(1)
    return None


def load_sources() -> dict[str, str]:
    """Lit data/raw/SOURCES.md et renvoie {nom_de_fichier: url}."""
    urls: dict[str, str] = {}
    if SOURCES_MD.exists():
        for line in SOURCES_MD.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\|\s*`([^`]+\.pdf)`\s*\|[^|]*\|\s*(\S+)", line)
            if m:
                urls[m.group(1)] = m.group(2)
    for name, url in MANUAL_URLS.items():
        urls.setdefault(name, url)
    return urls


# --------------------------------------------------------------------------
# Lecture et nettoyage
# --------------------------------------------------------------------------
@dataclass
class Block:
    page: int
    kind: str  # "text" ou "table"
    text: str


def normalize(text: str) -> str:
    text = text.replace(" ", " ").replace("­", "")
    text = re.sub(r"-\n(?=[a-zà-ÿ])", "", text)  # mot coupé en fin de ligne
    text = text.replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def table_to_markdown(rows: list[list[str | None]]) -> str:
    rows = [[(c or "").replace("\n", " ").strip() for c in r] for r in rows if r]
    if not rows or not any(any(r) for r in rows):
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * width]
    lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(lines)


def extract_blocks(path: Path, with_tables: bool) -> list[Block]:
    blocks: list[Block] = []
    with fitz.open(path) as doc:
        for number, page in enumerate(doc, start=1):
            table_rects: list[fitz.Rect] = []
            if with_tables:
                try:
                    for table in page.find_tables().tables:
                        md = table_to_markdown(table.extract())
                        if md:
                            table_rects.append(fitz.Rect(table.bbox))
                            blocks.append(Block(number, "table", md))
                except Exception:
                    pass  # une page à tableau illisible ne doit pas tout arrêter
            for b in page.get_text("blocks", sort=True):
                x0, y0, x1, y1, raw, _, kind = b[:7]
                if kind != 0:  # 0 = texte, 1 = image
                    continue
                if any(fitz.Rect(x0, y0, x1, y1).intersects(r) for r in table_rects):
                    continue  # déjà capturé dans le tableau
                text = normalize(raw)
                if text and not text.isdigit():
                    blocks.append(Block(number, "text", text))
    return blocks


# --------------------------------------------------------------------------
# Chunking parent-document
# --------------------------------------------------------------------------
SENTENCE_END = re.compile(r"(?<=[.!?:;])\s+")


def make_parents(blocks: list[Block], parent_size: int) -> list[list[Block]]:
    """Regroupe les blocs en parents d'environ parent_size caractères.
    Un tableau forme toujours un parent à lui seul (on ne le coupe jamais)."""
    parents: list[list[Block]] = []
    current: list[Block] = []
    length = 0
    for b in blocks:
        if b.kind == "table":
            if current:
                parents.append(current)
                current, length = [], 0
            parents.append([b])
            continue
        if current and length + len(b.text) > parent_size:
            parents.append(current)
            current, length = [], 0
        current.append(b)
        length += len(b.text) + 1
    if current:
        parents.append(current)
    return parents


def hard_split(text: str, size: int) -> list[str]:
    """Coupe une phrase démesurée sur les espaces."""
    pieces, cur = [], ""
    for word in text.split(" "):
        if cur and len(cur) + len(word) + 1 > size:
            pieces.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        pieces.append(cur)
    return pieces


def split_children(parent: list[Block], child_size: int, overlap: int) -> list[tuple[str, int, str]]:
    """Découpe un parent en petits chunks sur les limites de phrases.
    Renvoie une liste de (texte, page, type)."""
    if parent[0].kind == "table":
        return [(parent[0].text, parent[0].page, "table")]

    sentences: list[tuple[str, int]] = []
    for b in parent:
        for s in SENTENCE_END.split(b.text):
            if s:
                pieces = [s] if len(s) <= child_size else hard_split(s, child_size)
                sentences += [(p, b.page) for p in pieces]

    out: list[tuple[str, int, str]] = []
    cur: list[tuple[str, int]] = []
    length = 0
    for sentence, page in sentences:
        if cur and length + len(sentence) + 1 > child_size:
            out.append((" ".join(s for s, _ in cur), cur[0][1], "text"))
            tail = cur[-1] if len(cur[-1][0]) <= overlap else None  # léger chevauchement
            cur = [tail] if tail else []
            length = sum(len(s) + 1 for s, _ in cur)
        cur.append((sentence, page))
        length += len(sentence) + 1
    if cur:
        out.append((" ".join(s for s, _ in cur), cur[0][1], "text"))
    return out


def build_payloads(pdf: Path, blocks: list[Block], source: str, args) -> list[dict]:
    doc_id = pdf.stem
    category = categorize(pdf.name)
    date = guess_year(pdf.name, source)
    payloads: list[dict] = []
    for p_idx, parent in enumerate(make_parents(blocks, args.parent_size)):
        parent_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:parent:{p_idx}"))
        parent_text = "\n".join(b.text for b in parent)
        for c_idx, (text, page, kind) in enumerate(split_children(parent, args.child_size, args.overlap)):
            payloads.append({
                "chunk_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{doc_id}:{p_idx}:{c_idx}")),
                "parent_id": parent_id,
                "doc_id": doc_id,
                "source": source,
                "page": page,
                "category": category,
                "date": date,
                "type": kind,
                "text": text,
                "parent_text": parent_text,
            })
    return payloads


# --------------------------------------------------------------------------
# Qdrant
# --------------------------------------------------------------------------
def ensure_collection(client: QdrantClient, name: str, dim: int, recreate: bool) -> None:
    if recreate and client.collection_exists(name):
        client.delete_collection(name)
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100),
        )
        # Index sur les champs de filtrage : le filtre reste rapide dans le graphe HNSW
        for field, schema in [
            ("category", models.PayloadSchemaType.KEYWORD),
            ("doc_id", models.PayloadSchemaType.KEYWORD),
            ("type", models.PayloadSchemaType.KEYWORD),
            ("page", models.PayloadSchemaType.INTEGER),
        ]:
            client.create_payload_index(name, field_name=field, field_schema=schema)
        print(f"Collection '{name}' créée (dimension {dim}, Cosine, HNSW m=16 ef_construct=100).")
    else:
        size = client.get_collection(name).config.params.vectors.size
        if size != dim:
            sys.exit(f"La collection '{name}' a la dimension {size}, le modèle produit {dim}. "
                     f"Relancez avec --recreate ou changez --collection.")


def passage(text: str, model_name: str) -> str:
    # Les modèles e5 attendent un préfixe ; bge-m3 n'en a pas besoin.
    return f"passage: {text}" if "e5" in model_name.lower() else text


def upsert_batches(client, model, payloads: list[dict], args, label: str) -> None:
    for start in tqdm(range(0, len(payloads), args.batch), desc=label, unit="lot"):
        batch = payloads[start:start + args.batch]
        vectors = model.encode(
            [passage(p["text"], args.model) for p in batch],
            batch_size=args.batch, normalize_embeddings=True, show_progress_bar=False,
        )
        points = [
            models.PointStruct(id=p["chunk_id"], vector=v.tolist(), payload=p)
            for p, v in zip(batch, vectors)
        ]
        client.upsert(collection_name=args.collection, points=points)


# --------------------------------------------------------------------------
# Programme principal
# --------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Ingestion des guides dans Qdrant")
    ap.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL)
    ap.add_argument("--collection", default=DEFAULT_COLLECTION)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--parent-size", type=int, default=3500, help="taille d'un parent (caractères)")
    ap.add_argument("--child-size", type=int, default=900, help="taille d'un petit chunk (caractères)")
    ap.add_argument("--overlap", type=int, default=150, help="chevauchement maximal (caractères)")
    ap.add_argument("--batch", type=int, default=64, help="points par appel à Qdrant")
    ap.add_argument("--only", help="ne traiter que les PDF dont le nom contient ce texte")
    ap.add_argument("--limit", type=int, help="nombre maximal de PDF")
    ap.add_argument("--no-tables", action="store_true", help="ne pas extraire les tableaux (plus rapide)")
    ap.add_argument("--recreate", action="store_true", help="supprimer et recréer la collection")
    ap.add_argument("--skip-done", action="store_true",
                    help="ignorer les documents déjà présents dans la collection")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    pdfs = sorted(GUIDES_DIR.glob("*.pdf"))
    if args.only:
        pdfs = [p for p in pdfs if args.only.lower() in p.name.lower()]
    if args.limit:
        pdfs = pdfs[: args.limit]
    if not pdfs:
        sys.exit(f"Aucun PDF trouvé dans {GUIDES_DIR}")

    print(f"Modèle d'embeddings : {args.model}")
    model = SentenceTransformer(args.model)
    get_dim = getattr(model, "get_embedding_dimension", None) or model.get_sentence_embedding_dimension
    dim = get_dim()
    client = QdrantClient(url=args.qdrant_url, check_compatibility=False)
    ensure_collection(client, args.collection, dim, args.recreate)

    sources = load_sources()
    done, failed, total = [], [], 0
    for pdf in pdfs:
        if args.skip_done:
            already = client.count(
                args.collection,
                count_filter=models.Filter(must=[models.FieldCondition(
                    key="doc_id", match=models.MatchValue(value=pdf.stem))]),
                exact=True,
            ).count
            if already:
                print(f"{pdf.name} : déjà ingéré ({already} points), ignoré.")
                done.append(pdf.name)
                continue
        with_tables = not args.no_tables and pdf.name not in NO_TABLE_DOCS
        if not args.no_tables and not with_tables:
            print(f"{pdf.name} : extraction des tableaux désactivée (plante PyMuPDF).")
        try:
            blocks = extract_blocks(pdf, with_tables=with_tables)
        except Exception as exc:  # PDF cassé : on continue avec les autres
            print(f"[ERREUR] {pdf.name} illisible : {exc}")
            failed.append(pdf.name)
            continue
        if sum(len(b.text) for b in blocks) < 200:
            print(f"[ERREUR] {pdf.name} : presque aucun texte (scan ? faux PDF ?), ignoré.")
            failed.append(pdf.name)
            continue

        payloads = build_payloads(pdf, blocks, sources.get(pdf.name, pdf.name), args)
        n_tables = sum(1 for p in payloads if p["type"] == "table")
        print(f"{pdf.name} : {len(blocks)} blocs -> {len(payloads)} chunks ({n_tables} tableaux)")
        upsert_batches(client, model, payloads, args, label=pdf.name[:40])
        done.append(pdf.name)
        total += len(payloads)

    print("\n=== Résumé ===")
    print(f"Documents ingérés : {len(done)}/{len(pdfs)}")
    if failed:
        print("Documents en échec : " + ", ".join(failed))
    print(f"Chunks insérés : {total}")
    print(f"Points dans '{args.collection}' : {client.count(args.collection, exact=True).count}")


if __name__ == "__main__":
    main()
