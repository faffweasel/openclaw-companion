#!/usr/bin/env python3
"""
Memory search indexer.

Crawls configured memory directories, chunks markdown by heading structure,
stores in SQLite FTS5 for keyword search, and optionally embeds chunks via
a configured provider for semantic search.

Usage:
    python3 index.py                 # incremental index (skip unchanged)
    python3 index.py --force         # re-index everything
    python3 index.py --stats         # show index statistics
    python3 index.py --clear         # drop all indexed data

SHA-256 content hashing ensures unchanged chunks are never re-embedded.
Runs during evening routine or on demand.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
CONFIG_FILE = os.path.join(SKILL_DATA, "config.json")
DB_FILE = os.path.join(SKILL_DATA, "index.sqlite")

# Import embedding provider from same directory
sys.path.insert(0, SCRIPT_DIR)
from providers import get_embedder, vector_to_blob


def load_config() -> dict:
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def init_db(db: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    db.executescript("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id    TEXT PRIMARY KEY,
            source_file TEXT NOT NULL,
            start_line  INTEGER NOT NULL,
            end_line    INTEGER NOT NULL,
            heading     TEXT NOT NULL DEFAULT '',
            content     TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            indexed_at  REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS embeddings (
            chunk_id   TEXT PRIMARY KEY,
            provider   TEXT NOT NULL,
            model      TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            vector     BLOB NOT NULL,
            FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
        );

        CREATE TABLE IF NOT EXISTS file_hashes (
            file_path   TEXT PRIMARY KEY,
            file_hash   TEXT NOT NULL,
            indexed_at  REAL NOT NULL
        );
    """)

    # FTS5 virtual table — separate try because it can't use IF NOT EXISTS
    try:
        db.execute("""
            CREATE VIRTUAL TABLE chunks_fts USING fts5(
                content, heading, source_file,
                content='chunks',
                content_rowid='rowid'
            )
        """)
    except sqlite3.OperationalError:
        pass  # already exists

    db.commit()


def file_hash(filepath: str) -> str:
    """SHA-256 of file contents."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def chunk_hash(content: str) -> str:
    """SHA-256 of chunk content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def chunk_markdown(filepath: str, max_chars: int = 1600) -> list[dict]:
    """
    Split a markdown file into chunks by heading structure.

    Each heading section becomes a chunk. Sections exceeding max_chars
    are split at paragraph boundaries (blank lines).

    Returns list of {source_file, start_line, end_line, heading, content}.
    File path is relative to workspace.
    """
    try:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return []

    if not lines:
        return []

    # Make path relative to workspace
    rel_path = os.path.relpath(filepath, WORKSPACE)

    # Parse into sections by heading
    heading_re = re.compile(r"^(#{1,6})\s+(.+)")
    sections = []
    current_heading = ""
    current_lines = []
    current_start = 1

    for i, line in enumerate(lines, 1):
        m = heading_re.match(line)
        if m:
            # Save previous section
            if current_lines:
                text = "".join(current_lines).strip()
                if text:
                    sections.append({
                        "heading": current_heading,
                        "content": text,
                        "start_line": current_start,
                        "end_line": i - 1,
                    })
            current_heading = line.strip()
            current_lines = [line]
            current_start = i
        else:
            current_lines.append(line)

    # Don't forget last section
    if current_lines:
        text = "".join(current_lines).strip()
        if text:
            sections.append({
                "heading": current_heading,
                "content": text,
                "start_line": current_start,
                "end_line": len(lines),
            })

    # Split oversized sections at paragraph boundaries
    chunks = []
    for sec in sections:
        if len(sec["content"]) <= max_chars:
            chunks.append({
                "source_file": rel_path,
                "start_line": sec["start_line"],
                "end_line": sec["end_line"],
                "heading": sec["heading"],
                "content": sec["content"],
            })
        else:
            # Split at blank lines
            paragraphs = re.split(r"\n\s*\n", sec["content"])
            buf = ""
            buf_start = sec["start_line"]
            approx_line = sec["start_line"]

            for para in paragraphs:
                para_lines = para.count("\n") + 1
                if buf and len(buf) + len(para) + 2 > max_chars:
                    chunks.append({
                        "source_file": rel_path,
                        "start_line": buf_start,
                        "end_line": approx_line,
                        "heading": sec["heading"],
                        "content": buf.strip(),
                    })
                    buf = para
                    buf_start = approx_line + 1
                else:
                    buf = f"{buf}\n\n{para}" if buf else para
                approx_line += para_lines + 1

            if buf.strip():
                chunks.append({
                    "source_file": rel_path,
                    "start_line": buf_start,
                    "end_line": sec["end_line"],
                    "heading": sec["heading"],
                    "content": buf.strip(),
                })

    return chunks


def discover_files(config: dict) -> list[str]:
    """Walk configured index_paths and return all .md file paths."""
    index_paths = config.get("index_paths", ["memory/", ".learnings/"])
    files = []
    workspace_real = os.path.realpath(WORKSPACE)

    for rel_path in index_paths:
        abs_path = os.path.realpath(os.path.join(WORKSPACE, rel_path))

        # Boundary check: reject paths that resolve outside workspace
        if not abs_path.startswith(workspace_real + os.sep) and abs_path != workspace_real:
            print(f"WARNING: index_path '{rel_path}' resolves outside workspace, skipping.",
                  file=sys.stderr)
            continue

        if os.path.isfile(abs_path) and abs_path.endswith(".md"):
            files.append(abs_path)
        elif os.path.isdir(abs_path):
            for root, _dirs, filenames in os.walk(abs_path):
                for fn in sorted(filenames):
                    if fn.endswith(".md"):
                        files.append(os.path.join(root, fn))

    # Also check MEMORY.md at workspace root
    mem_file = os.path.join(WORKSPACE, "MEMORY.md")
    if os.path.isfile(mem_file) and mem_file not in files:
        files.append(mem_file)

    return sorted(set(files))


def index_files(config: dict, force: bool = False) -> None:
    """Main indexing pipeline."""
    os.makedirs(SKILL_DATA, exist_ok=True)
    db = sqlite3.connect(DB_FILE)
    init_db(db)

    max_chars = config.get("max_chunk_chars", 1600)
    files = discover_files(config)

    if not files:
        print("No markdown files found in configured paths.")
        db.close()
        return

    # Check which files changed
    changed_files = []
    current_file_hashes = {}

    for fpath in files:
        fh = file_hash(fpath)
        rel = os.path.relpath(fpath, WORKSPACE)
        current_file_hashes[rel] = fh

        if force:
            changed_files.append(fpath)
            continue

        row = db.execute(
            "SELECT file_hash FROM file_hashes WHERE file_path = ?", (rel,)
        ).fetchone()
        if row is None or row[0] != fh:
            changed_files.append(fpath)

    # Remove stale files from index
    indexed_files = {r[0] for r in db.execute("SELECT file_path FROM file_hashes").fetchall()}
    current_files = set(current_file_hashes.keys())
    stale = indexed_files - current_files

    for stale_file in stale:
        db.execute("DELETE FROM chunks WHERE source_file = ?", (stale_file,))
        db.execute(
            "DELETE FROM embeddings WHERE chunk_id IN "
            "(SELECT chunk_id FROM chunks WHERE source_file = ?)", (stale_file,)
        )
        db.execute("DELETE FROM file_hashes WHERE file_path = ?", (stale_file,))

    if not changed_files and not stale:
        print(f"Index up to date. {len(files)} files, no changes.")
        db.close()
        return

    # Chunk changed files
    new_chunks = []
    for fpath in changed_files:
        rel = os.path.relpath(fpath, WORKSPACE)
        # Remove old chunks for this file
        db.execute(
            "DELETE FROM embeddings WHERE chunk_id IN "
            "(SELECT chunk_id FROM chunks WHERE source_file = ?)", (rel,)
        )
        db.execute("DELETE FROM chunks WHERE source_file = ?", (rel,))

        for chunk in chunk_markdown(fpath, max_chars):
            ch = chunk_hash(chunk["content"])
            cid = hashlib.sha256(
                f"{chunk['source_file']}:{chunk['start_line']}:{chunk['end_line']}:{ch}".encode()
            ).hexdigest()[:16]

            new_chunks.append((cid, chunk, ch))

    # Insert chunks and FTS5
    now = time.time()
    for cid, chunk, ch in new_chunks:
        db.execute(
            "INSERT OR REPLACE INTO chunks "
            "(chunk_id, source_file, start_line, end_line, heading, content, content_hash, indexed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (cid, chunk["source_file"], chunk["start_line"], chunk["end_line"],
             chunk["heading"], chunk["content"], ch, now),
        )

    # Rebuild FTS5 index
    db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")

    # Update file hashes
    for rel, fh in current_file_hashes.items():
        db.execute(
            "INSERT OR REPLACE INTO file_hashes (file_path, file_hash, indexed_at) "
            "VALUES (?, ?, ?)", (rel, fh, now)
        )

    db.commit()

    # Embed new chunks if provider available
    embedder, prov_name, prov_model = get_embedder(config)
    embedded_count = 0

    if embedder and new_chunks:
        # Batch embed in groups of 50
        batch_size = 50
        texts = [(cid, c["content"]) for cid, c, _ in new_chunks]

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_ids = [t[0] for t in batch]
            batch_texts = [t[1] for t in batch]

            try:
                vectors = embedder(batch_texts)
                for cid, vec in zip(batch_ids, vectors):
                    db.execute(
                        "INSERT OR REPLACE INTO embeddings "
                        "(chunk_id, provider, model, dimensions, vector) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (cid, prov_name, prov_model, len(vec), vector_to_blob(vec)),
                    )
                    embedded_count += 1
            except Exception as e:
                print(f"Embedding batch failed: {e}", file=sys.stderr)
                print("Continuing with FTS5-only for remaining chunks.", file=sys.stderr)
                break

        db.commit()

    # Summary
    total_chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    total_embedded = db.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    total_files = db.execute("SELECT COUNT(*) FROM file_hashes").fetchone()[0]

    print(f"Indexed {len(changed_files)} changed files ({len(new_chunks)} chunks).")
    if stale:
        print(f"Removed {len(stale)} deleted files.")
    print(f"Total: {total_files} files, {total_chunks} chunks, {total_embedded} embedded.")
    if embedder:
        print(f"Embedding: {prov_name} ({prov_model})")
    else:
        print("Embedding: none (FTS5 keyword search only)")

    db.close()


def show_stats() -> None:
    """Print index statistics."""
    if not os.path.isfile(DB_FILE):
        print("No index found. Run: python3 index.py")
        return

    db = sqlite3.connect(DB_FILE)
    try:
        files = db.execute("SELECT COUNT(*) FROM file_hashes").fetchone()[0]
        chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        embedded = db.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]

        print(f"Files indexed:  {files}")
        print(f"Total chunks:   {chunks}")
        print(f"Embedded:       {embedded}")

        if embedded > 0:
            row = db.execute(
                "SELECT provider, model, dimensions FROM embeddings LIMIT 1"
            ).fetchone()
            if row:
                print(f"Provider:       {row[0]} ({row[1]})")
                print(f"Dimensions:     {row[2]}")

        # Show source breakdown
        rows = db.execute(
            "SELECT source_file, COUNT(*) FROM chunks GROUP BY source_file ORDER BY source_file"
        ).fetchall()
        if rows:
            print(f"\nFiles ({len(rows)}):")
            for path, count in rows:
                print(f"  {path}: {count} chunks")

    finally:
        db.close()


def clear_index() -> None:
    """Drop all indexed data."""
    if os.path.isfile(DB_FILE):
        os.remove(DB_FILE)
        print("Index cleared.")
    else:
        print("No index to clear.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Index memory files for search.")
    ap.add_argument("--force", action="store_true", help="Re-index all files")
    ap.add_argument("--stats", action="store_true", help="Show index statistics")
    ap.add_argument("--clear", action="store_true", help="Drop all indexed data")
    args = ap.parse_args()

    if args.clear:
        clear_index()
        return 0

    if args.stats:
        show_stats()
        return 0

    config = load_config()
    try:
        index_files(config, force=args.force)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
