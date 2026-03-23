#!/usr/bin/env python3
"""
Multi-provider LLM text generation.

Route text generation to any OpenAI-compatible provider.
Provider registry lives in skills-data/multi-provider/providers.json.

CLI usage:
    python3 providers.py --provider openrouter --model google/gemini-2.5-flash \
        --system "You are helpful." --prompt "Hello"
    python3 providers.py --list-providers

Output: generated text to stdout. Errors to stderr.

API keys are read from environment variables (set via docker-compose.override.yml).
Identity files (SOUL.md, IDENTITY.md, USER.md) are prepended to system prompt
by default — use --no-identity to skip.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Workspace detection
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
PROVIDERS_FILE = os.path.join(SKILL_DATA, "providers.json")

USER_AGENT = "Mozilla/5.0 (nanobot-companion multi-provider)"

# Identity files Nanobot loads every turn — we replicate for direct API calls
IDENTITY_FILES = ["SOUL.md", "IDENTITY.md", "USER.md"]

# Cache: loaded once per process
_identity_cache: str | None = None
_providers_cache: dict | None = None


def load_providers() -> dict:
    """
    Load provider registry from skills-data/multi-provider/providers.json.

    Returns dict of provider_name -> {endpoint, apiKeyEnvVar, format}.
    Falls back to empty dict if file not found.
    """
    global _providers_cache
    if _providers_cache is not None:
        return _providers_cache

    if os.path.isfile(PROVIDERS_FILE):
        try:
            with open(PROVIDERS_FILE, encoding="utf-8") as f:
                data = json.load(f)
            _providers_cache = data.get("providers", {})
            return _providers_cache
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not read {PROVIDERS_FILE}: {e}", file=sys.stderr)

    _providers_cache = {}
    return _providers_cache


def load_identity_context() -> str:
    """
    Read SOUL.md, IDENTITY.md, USER.md from workspace root.

    Cached per process — files are read once, reused for all calls.
    """
    global _identity_cache
    if _identity_cache is not None:
        return _identity_cache

    parts = []
    for filename in IDENTITY_FILES:
        filepath = os.path.join(WORKSPACE, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    parts.append(content)
            except OSError:
                pass

    _identity_cache = "\n\n---\n\n".join(parts)
    return _identity_cache


def list_providers() -> None:
    """Print available providers and their status."""
    providers = load_providers()
    if not providers:
        print("No providers configured.")
        print(f"Expected: {PROVIDERS_FILE}")
        print("Run setup.sh or copy seed/providers.json to skills-data/multi-provider/")
        return

    print(f"\n{'Provider':<20} {'Format':<10} {'API Key Env Var':<25} {'Key Set?'}")
    print("-" * 75)
    for name, cfg in providers.items():
        env_var = cfg.get("apiKeyEnvVar", "")
        has_key = "yes" if (not env_var or os.environ.get(env_var, "").strip()) else "NO"
        fmt = cfg.get("format", "openai")
        print(f"{name:<20} {fmt:<10} {env_var or '(none)':<25} {has_key}")
    print()


def call_llm(
    provider: str,
    model: str,
    prompt: str,
    system: str | None = None,
    max_tokens: int = 2048,
    temperature: float | None = None,
    timeout: int = 180,
    include_identity: bool = True,
) -> str:
    """
    Call an LLM via the specified provider.

    Args:
        provider: Provider name (from providers.json)
        model: Model ID (provider-specific)
        prompt: User message
        system: System prompt (optional — identity prepended by default)
        max_tokens: Max response tokens
        temperature: Sampling temperature (optional)
        timeout: Request timeout in seconds
        include_identity: Prepend SOUL.md/IDENTITY.md/USER.md to system prompt

    Returns:
        Generated text content

    Raises:
        ValueError: Unknown provider, missing API key, or unsupported format
        RuntimeError: API error
    """
    providers = load_providers()

    if provider not in providers:
        available = ", ".join(providers.keys()) if providers else "(none configured)"
        raise ValueError(
            f"Unknown provider: '{provider}'. "
            f"Available: {available}. "
            f"Edit {PROVIDERS_FILE} to add providers."
        )

    cfg = providers[provider]
    endpoint = cfg.get("endpoint", "")
    env_var = cfg.get("apiKeyEnvVar", "")
    fmt = cfg.get("format", "openai")

    if fmt != "openai":
        raise ValueError(
            f"Provider '{provider}' uses format '{fmt}' which is not yet supported. "
            f"Use an OpenAI-compatible provider or route through OpenRouter."
        )

    # Resolve API key (empty env var = no key needed, e.g. local Ollama)
    api_key = ""
    if env_var:
        api_key = os.environ.get(env_var, "").strip()
        if not api_key:
            raise ValueError(
                f"No API key for provider '{provider}'. "
                f"Set {env_var} in docker-compose.override.yml"
            )

    # Build system prompt with identity context
    full_system = system
    if include_identity:
        identity = load_identity_context()
        if identity:
            full_system = f"{identity}\n\n---\n\n{full_system}" if full_system else identity

    # Build messages
    messages = []
    if full_system:
        messages.append({"role": "system", "content": full_system})
    messages.append({"role": "user", "content": prompt})

    # Build payload
    payload: dict = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if temperature is not None:
        payload["temperature"] = temperature

    # Build headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    # Make request
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, method="POST", headers=headers, data=body)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{provider} API error ({e.code}): {error_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"{provider} connection error: {e.reason}") from e

    # Extract text from OpenAI-compatible response
    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError(
            f"No choices in {provider} response: {json.dumps(data, indent=2)}"
        )

    content = choices[0].get("message", {}).get("content", "")
    if not content:
        raise RuntimeError(
            f"Empty content in {provider} response: {json.dumps(data, indent=2)}"
        )

    return content


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Route text generation to any configured provider/model."
    )
    ap.add_argument("--provider", help="Provider name (from providers.json)")
    ap.add_argument("--model", help="Model ID")
    ap.add_argument("--prompt", help="User message")
    ap.add_argument("--system", help="System prompt")
    ap.add_argument(
        "--max-tokens", type=int, default=2048, help="Max response tokens (default: 2048)"
    )
    ap.add_argument("--temperature", type=float, help="Sampling temperature")
    ap.add_argument(
        "--no-identity", action="store_true",
        help="Don't prepend identity files to system prompt"
    )
    ap.add_argument(
        "--list-providers", action="store_true",
        help="List configured providers and exit"
    )
    args = ap.parse_args()

    if args.list_providers:
        list_providers()
        return 0

    if not args.provider or not args.model or not args.prompt:
        ap.error("--provider, --model, and --prompt are required (or use --list-providers)")

    try:
        result = call_llm(
            provider=args.provider,
            model=args.model,
            prompt=args.prompt,
            system=args.system,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            include_identity=not args.no_identity,
        )
        print(result)
        return 0
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
