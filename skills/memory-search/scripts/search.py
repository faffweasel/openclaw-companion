#!/usr/bin/env python3
"""
Memory search — hybrid keyword + semantic search.

FTS5 (BM25) keyword search is always available.
Vector (cosine similarity) search is available when embeddings exist.
Results are merged via Reciprocal Rank Fusion (RRF) when both are present.

Usage:
    python3 search.py "what did we decide about the hardware"
    python3 search.py "Alice" --top-k 5
    python3 search.py "RTX 3090" --mode fts     # keyword only
    python3 search.py "infrastructure" --mode vector  # semantic only
    python3 search.py --check                    # check search readiness

Output: ranked results with source file, line range, heading, and snippet.
"""

import argparse
import json
import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
CONFIG_FILE = os.path.join(SKILL_DATA, "config.json")
DB_FILE = os.path.join(SKILL_DATA, "index.sqlite")

sys.path.insert(0, SCRIPT_DIR)
from providers import get_embedder, blob_to_vector, cosine_similarity


def load_config() -> dict:
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def fts_search(db: sqlite3.Connection, query: str, top_k: int) -> list[dict]:
    """
    BM25-ranked full-text search via FTS5.

    Returns list of {chunk_id, source_file, start_line, end_line, heading, snippet, score}.
    """
    # FTS5 query: tokenise and join with OR for broader matching
    # Also try the raw query as a phrase
    tokens = query.split()
    if len(tokens) > 1:
        # Try phrase match first, then fall back to OR
        fts_query = f'"{query}" OR {" OR ".join(tokens)}'
    else:
        fts_query = query

    try:
        rows = db.execute(
            """
            SELECT c.chunk_id, c.source_file, c.start_line, c.end_line,
                   c.heading, c.content, rank
            FROM chunks_fts fts
            JOIN chunks c ON c.rowid = fts.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (fts_query, top_k * 3),  # over-fetch for RRF merge
        ).fetchall()
    except sqlite3.OperationalError:
        # FTS5 query syntax error — fall back to simpler query
        simple_query = " OR ".join(tokens)
        rows = db.execute(
            """
            SELECT c.chunk_id, c.source_file, c.start_line, c.end_line,
                   c.heading, c.content, rank
            FROM chunks_fts fts
            JOIN chunks c ON c.rowid = fts.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (simple_query, top_k * 3),
        ).fetchall()

    results = []
    for row in rows:
        # BM25 rank is negative (lower = better). Convert to 0-1 score.
        bm25_rank = abs(row[6])
        score = 1.0 / (1.0 + bm25_rank)
        results.append({
            "chunk_id": row[0],
            "source_file": row[1],
            "start_line": row[2],
            "end_line": row[3],
            "heading": row[4],
            "snippet": row[5][:700],
            "score": score,
        })

    return results


def vector_search(
    db: sqlite3.Connection, query: str, top_k: int, config: dict
) -> list[dict]:
    """
    Cosine similarity search over stored embeddings.

    Returns list of {chunk_id, source_file, start_line, end_line, heading, snippet, score}.
    """
    # Check if embeddings exist
    count = db.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    if count == 0:
        return []

    # Get embedder
    embedder, _, _ = get_embedder(config)
    if embedder is None:
        return []

    # Embed the query
    try:
        query_vec = embedder([query])[0]
    except Exception as e:
        print(f"Query embedding failed: {e}", file=sys.stderr)
        return []

    # Load all embeddings and compute similarity
    # For <5000 chunks this is fast (milliseconds in Python)
    rows = db.execute(
        """
        SELECT e.chunk_id, c.source_file, c.start_line, c.end_line,
               c.heading, c.content, e.vector
        FROM embeddings e
        JOIN chunks c ON c.chunk_id = e.chunk_id
        """
    ).fetchall()

    scored = []
    for row in rows:
        vec = blob_to_vector(row[6])
        sim = cosine_similarity(query_vec, vec)
        scored.append({
            "chunk_id": row[0],
            "source_file": row[1],
            "start_line": row[2],
            "end_line": row[3],
            "heading": row[4],
            "snippet": row[5][:700],
            "score": sim,
        })

    # Sort by similarity descending, return top-k * 3 for RRF merge
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k * 3]


def rrf_merge(
    fts_results: list[dict], vec_results: list[dict], top_k: int, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion: combine two ranked lists.

    RRF score = sum(1 / (k + rank)) across lists.
    k=60 is the standard constant.
    """
    scores: dict[str, float] = {}
    items: dict[str, dict] = {}

    for rank, item in enumerate(fts_results):
        cid = item["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank + 1)
        items[cid] = item

    for rank, item in enumerate(vec_results):
        cid = item["chunk_id"]
        scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank + 1)
        if cid not in items:
            items[cid] = item

    # Sort by RRF score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    results = []
    for cid, score in ranked[:top_k]:
        item = items[cid]
        item["score"] = score
        results.append(item)

    return results


def search(query: str, top_k: int = 10, mode: str = "hybrid") -> list[dict]:
    """
    Main search entry point.

    Args:
        query: search query string
        top_k: number of results to return
        mode: "hybrid" (default), "fts" (keyword only), "vector" (semantic only)

    Returns list of result dicts sorted by relevance.
    """
    if not os.path.isfile(DB_FILE):
        print("No index found. Run: python3 skills/memory-search/scripts/index.py",
              file=sys.stderr)
        return []

    config = load_config()
    db = sqlite3.connect(DB_FILE)

    try:
        fts_results = []
        vec_results = []

        if mode in ("hybrid", "fts"):
            fts_results = fts_search(db, query, top_k)

        if mode in ("hybrid", "vector"):
            vec_results = vector_search(db, query, top_k, config)

        if mode == "fts" or (not vec_results and fts_results):
            return fts_results[:top_k]
        elif mode == "vector" or (not fts_results and vec_results):
            return vec_results[:top_k]
        elif fts_results and vec_results:
            return rrf_merge(fts_results, vec_results, top_k)
        else:
            return []
    finally:
        db.close()


def format_results(results: list[dict]) -> str:
    """Format results for agent consumption."""
    if not results:
        return "No results found."

    lines = []
    for i, r in enumerate(results, 1):
        heading = f" > {r['heading']}" if r["heading"] else ""
        lines.append(f"--- Result {i} (score: {r['score']:.4f}) ---")
        lines.append(f"Source: {r['source_file']} (lines {r['start_line']}-{r['end_line']}){heading}")
        lines.append(r["snippet"])
        lines.append("")

    return "\n".join(lines)


def check_readiness() -> None:
    """Diagnostic: check index and embedding status."""
    if not os.path.isfile(DB_FILE):
        print("Index: NOT FOUND")
        print("Run: python3 skills/memory-search/scripts/index.py")
        return

    db = sqlite3.connect(DB_FILE)
    chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    embedded = db.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    files = db.execute("SELECT COUNT(*) FROM file_hashes").fetchone()[0]
    db.close()

    print(f"Index: {files} files, {chunks} chunks")
    print(f"FTS5: {'ready' if chunks > 0 else 'empty'}")
    print(f"Embeddings: {embedded}/{chunks} chunks")

    if embedded > 0:
        print("Search mode: hybrid (FTS5 + vector)")
    elif chunks > 0:
        print("Search mode: FTS5 keyword only")
    else:
        print("Search mode: none (index empty)")

    config = load_config()
    embedder, name, model = get_embedder(config)
    if embedder:
        print(f"Embedding provider: {name} ({model}) — active")
    else:
        print("Embedding provider: none available")


def main() -> int:
    ap = argparse.ArgumentParser(description="Search memory files.")
    ap.add_argument("query", nargs="?", help="Search query")
    ap.add_argument("--top-k", type=int, default=10, help="Number of results (default: 10)")
    ap.add_argument(
        "--mode", choices=["hybrid", "fts", "vector"], default="hybrid",
        help="Search mode (default: hybrid)"
    )
    ap.add_argument("--json", action="store_true", help="Output as JSON")
    ap.add_argument("--check", action="store_true", help="Check search readiness")
    args = ap.parse_args()

    if args.check:
        check_readiness()
        return 0

    if not args.query:
        ap.error("Query required (or use --check)")

    results = search(args.query, args.top_k, args.mode)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
