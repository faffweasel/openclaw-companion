---
name: memory-search
description: "Semantic and keyword search across all memory files — daily logs, people, projects, dreams, learnings. Use when: (1) searching for past conversations, decisions, or context, (2) user asks 'what did we discuss about...', 'when did we decide...', 'what do you remember about...', (3) looking up a person, project, or topic across multiple memory files, (4) needing to find related context before answering a question about past events, (5) any memory search where the exact wording is unknown. Prefer this over grep for any search that isn't a simple exact-string lookup."
metadata: '{"nanobot":{"emoji":"🔍","requires":{"bins":["python3"]}}}'
---

# Memory Search

Hybrid keyword + semantic search across all memory files. FTS5 keyword search is always available. Vector semantic search is available when an embedding provider is configured.

---

## When to Use This vs Grep

| Situation | Use |
|-----------|-----|
| Exact string lookup ("ERR-20260315-001") | `grep` |
| Known filename or date | Direct file read |
| Topic search, unknown wording | **memory-search** |
| Cross-file lookup (person across months) | **memory-search** |
| "What did we decide about..." | **memory-search** |
| "When did I mention..." | **memory-search** |

---

## Search

```bash
python3 skills/memory-search/scripts/search.py "what did we decide about the hardware"
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--top-k N` | 10 | Number of results |
| `--mode hybrid\|fts\|vector` | hybrid | Search mode |
| `--json` | off | Output as JSON (for scripts) |
| `--check` | — | Show index and embedding status |

### After Getting Results

1. Read the search results — snippets are capped at ~700 chars
2. If relevant, **read the full source file** at the indicated line range
3. Combine information from multiple results if the answer spans several files

---

## Indexing

The index updates during the evening routine. To manually reindex:

```bash
python3 skills/memory-search/scripts/index.py
```

| Flag | Description |
|------|-------------|
| `--force` | Re-index all files |
| `--stats` | Show index statistics |
| `--clear` | Drop all indexed data |

### What Gets Indexed

Everything in the configured `index_paths` (default: `memory/` and `.learnings/`), plus `MEMORY.md` at the workspace root.

### Incremental Indexing

Files are SHA-256 hashed. Only changed files are re-chunked and re-embedded.

---

## Search Modes

**Hybrid** (default): FTS5 keyword + vector semantic, merged via Reciprocal Rank Fusion. Best accuracy.

**FTS** (keyword only): BM25-ranked full-text search. Good for names, IDs, specific terms. Always available.

**Vector** (semantic only): Cosine similarity over embedded chunks. Finds meaning-based matches. Requires embedding provider.

If no embedding provider is available, hybrid degrades to FTS-only.

---

## Diagnostics

```bash
python3 skills/memory-search/scripts/search.py --check
python3 skills/memory-search/scripts/providers.py
```

---

## Configuration

Edit `skills-data/memory-search/config.json`:

```json
{
  "index_paths": ["memory/", ".learnings/"],
  "max_chunk_chars": 1600,
  "search_top_k": 10,
  "embedding": {
    "provider": "auto",
    "providers": {
      "openrouter": {
        "endpoint": "https://openrouter.ai/api/v1/embeddings",
        "model": "openai/text-embedding-3-small",
        "apiKeyEnvVar": "OPENROUTER_API_KEY",
        "format": "openai"
      },
      "ollama": {
        "endpoint": "http://localhost:11434/api/embed",
        "model": "nomic-embed-text",
        "apiKeyEnvVar": "",
        "format": "ollama"
      }
    }
  }
}
```

### Adding Index Paths

```json
"index_paths": ["memory/", ".learnings/", "notes/", "TOOLS.md"]
```

### Adding Embedding Providers

Any OpenAI-compatible embedding endpoint works:

```json
"nvidia": {
  "endpoint": "https://integrate.api.nvidia.com/v1/embeddings",
  "model": "NV-Embed-V2",
  "apiKeyEnvVar": "NVIDIA_API_KEY",
  "format": "openai"
}
```

The `format` field: `"openai"` for OpenAI-compatible APIs, `"ollama"` for Ollama's `/api/embed`.

Set `provider` to `"auto"` (try each until one works) or a specific name.

---

## Failure Modes

**No index:** Search tells the agent to run `index.py`. Not an error.
**No embedding provider:** Degrades to FTS5 keyword search. Still better than grep.
**Embedding API error during indexing:** Indexes what it can, continues with FTS5.
**Stale index:** Run `index.py` manually. The agent can run it before searching if results seem incomplete.
