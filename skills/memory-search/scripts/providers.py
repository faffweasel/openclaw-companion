#!/usr/bin/env python3
"""
Embedding provider abstraction for memory-search.

Reads skills-data/memory-search/config.json for provider config.
API keys come from environment variables (same ones as multi-provider).
All HTTP calls use urllib (stdlib) — no pip dependencies.

Supported formats:
  - openai: POST {endpoint} with {"model": m, "input": [...]}
  - ollama: POST {endpoint} with {"model": m, "input": [...]}

Usage:
    from providers import get_embedder
    embedder = get_embedder()  # auto-detect, or None if unavailable
    vectors = embedder(["text1", "text2"])  # list of float lists
"""

import json
import os
import struct
import sys
import urllib.error
import urllib.request

# Workspace detection — same pattern as multi-provider
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
CONFIG_FILE = os.path.join(SKILL_DATA, "config.json")

USER_AGENT = "Mozilla/5.0 (nanobot-companion memory-search)"


def load_config() -> dict:
    """Load memory-search config. Returns empty dict on failure."""
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not read {CONFIG_FILE}: {e}", file=sys.stderr)
    return {}


def _call_openai_embeddings(
    endpoint: str, model: str, texts: list[str], api_key: str, timeout: int = 60
) -> list[list[float]]:
    """Call OpenAI-compatible embedding endpoint. Returns list of vectors."""
    payload = {"model": model, "input": texts}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, method="POST", headers=headers, data=body)

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    # Response: {"data": [{"embedding": [...], "index": 0}, ...]}
    results = sorted(data.get("data", []), key=lambda x: x.get("index", 0))
    return [item["embedding"] for item in results]


def _call_ollama_embeddings(
    endpoint: str, model: str, texts: list[str], timeout: int = 60
) -> list[list[float]]:
    """Call Ollama /api/embed endpoint. Returns list of vectors."""
    payload = {"model": model, "input": texts}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, method="POST", headers=headers, data=body)

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    # Response: {"embeddings": [[...], [...]]}
    return data.get("embeddings", [])


def _try_provider(cfg: dict) -> callable | None:
    """
    Test if a provider is usable. Returns an embedding function or None.

    The returned function signature: (texts: list[str]) -> list[list[float]]
    """
    endpoint = cfg.get("endpoint", "")
    model = cfg.get("model", "")
    fmt = cfg.get("format", "openai")
    env_var = cfg.get("apiKeyEnvVar", "")

    if not endpoint or not model:
        return None

    # Check API key
    api_key = ""
    if env_var:
        api_key = os.environ.get(env_var, "").strip()
        if not api_key:
            return None

    # Test with a single short string
    try:
        if fmt == "openai":
            _call_openai_embeddings(endpoint, model, ["test"], api_key, timeout=15)
        elif fmt == "ollama":
            _call_ollama_embeddings(endpoint, model, ["test"], timeout=15)
        else:
            return None
    except Exception:
        return None

    # Return a closure that calls this provider
    if fmt == "openai":
        def embed(texts: list[str]) -> list[list[float]]:
            return _call_openai_embeddings(endpoint, model, texts, api_key)
        return embed
    elif fmt == "ollama":
        def embed(texts: list[str]) -> list[list[float]]:
            return _call_ollama_embeddings(endpoint, model, texts)
        return embed

    return None


def get_embedder(config: dict | None = None) -> tuple[callable | None, str, str]:
    """
    Auto-detect an embedding provider from config.

    Returns (embed_fn, provider_name, model_name) or (None, "", "") if unavailable.
    embed_fn signature: (texts: list[str]) -> list[list[float]]
    """
    if config is None:
        config = load_config()

    emb_cfg = config.get("embedding", {})
    providers = emb_cfg.get("providers", {})
    preferred = emb_cfg.get("provider", "auto")

    # If a specific provider is requested, try only that one
    if preferred != "auto" and preferred in providers:
        fn = _try_provider(providers[preferred])
        if fn:
            return fn, preferred, providers[preferred].get("model", "")
        return None, "", ""

    # Auto-detect: try each provider in config order
    for name, pcfg in providers.items():
        fn = _try_provider(pcfg)
        if fn:
            return fn, name, pcfg.get("model", "")

    return None, "", ""


# --- Vector serialisation helpers (for SQLite BLOB storage) ---

def vector_to_blob(vec: list[float]) -> bytes:
    """Pack a float vector into a compact binary blob."""
    return struct.pack(f"{len(vec)}f", *vec)


def blob_to_vector(blob: bytes) -> list[float]:
    """Unpack a binary blob back to a float vector."""
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


if __name__ == "__main__":
    # Quick diagnostic
    config = load_config()
    fn, name, model = get_embedder(config)
    if fn:
        print(f"Embedding provider: {name} ({model})")
        vecs = fn(["hello world"])
        print(f"Dimensions: {len(vecs[0])}")
        print("Status: OK")
    else:
        print("No embedding provider available.")
        print("FTS5 keyword search will still work.")
        emb = config.get("embedding", {})
        providers = emb.get("providers", {})
        if providers:
            print(f"\nConfigured providers: {', '.join(providers.keys())}")
            for pname, pcfg in providers.items():
                env_var = pcfg.get("apiKeyEnvVar", "")
                if env_var:
                    has = "set" if os.environ.get(env_var, "").strip() else "NOT SET"
                    print(f"  {pname}: {env_var} = {has}")
                else:
                    print(f"  {pname}: no API key needed (local)")
