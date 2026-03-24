#!/usr/bin/env python3
"""
Post-dream processing: call reflection model to score the dream,
write structured header, handle preconscious integration.

Calls the reflection model (per-topic routing via dream-config.json models table)
directly via OpenRouter or Venice API — stdlib urllib only, no pip dependencies.

Usage:
    python3 post-dream.py --dream-file memory/dreams/2026-03-22.md \
        --dream-index 1 \
        --reflection-model default \
        --category personal
"""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Workspace detection
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))

# Load .env
ENV_FILE = os.path.join(WORKSPACE, ".env")
if os.path.isfile(ENV_FILE):
    with open(ENV_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILLS_DIR = os.environ.get("SKILLS_DIR", os.path.join(WORKSPACE, "skills"))

SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
CONFIG_FILE = os.path.join(SKILL_DATA, "dream-config.json")
PRECONSCIOUS_ADD = os.path.join(SKILLS_DIR, "preconscious", "scripts", "add.py")

USER_AGENT = "Mozilla/5.0 (openclaw-companion dreaming)"

DEFAULT_REFLECTION_SYSTEM = (
    'Read the following dream text. Respond with ONLY a JSON object, no markdown, no preamble: '
    '{"intensity": <1-7>, "mood": "<one of: sad, happy, angry, reflective, playful, anxious, serene, curious>", '
    '"summary": "<1-2 sentence summary>"}. '
    "Intensity 7 = viscerally intense body-memory, 1 = passing thought."
)

PROVIDER_ENDPOINTS = {
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY"),
    "venice": ("https://api.venice.ai/api/v1/chat/completions", "VENICE_API_KEY"),
}


def load_config() -> dict:
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: could not read config: {e}", file=sys.stderr)
    return {}


def extract_dream_section(dream_file: Path, index: int) -> str:
    """Extract the Nth (1-based) ## section from the dream file."""
    text = dream_file.read_text(encoding="utf-8")
    sections = []
    current: list[str] = []
    in_section = False
    for line in text.split("\n"):
        if line.startswith("## "):
            if in_section:
                sections.append("\n".join(current))
            current = [line]
            in_section = True
        elif in_section:
            current.append(line)
    if in_section:
        sections.append("\n".join(current))
    if index < 1 or index > len(sections):
        return ""
    return sections[index - 1]


def call_chat_completion(
    endpoint: str, api_key: str, model: str, system: str, user: str
) -> str:
    """Call an OpenAI-compatible chat completions endpoint. Returns assistant message text."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 200,
        "temperature": 0.0,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": USER_AGENT,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(endpoint, method="POST", headers=headers, data=body)
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def score_dream(dream_text: str, model_label: str, config: dict) -> dict:
    """Call the reflection model to score the dream. Returns {intensity, mood, summary}."""
    models = config.get("models", {})
    reflection_system = config.get("reflectionSystem", DEFAULT_REFLECTION_SYSTEM)

    model_cfg = models.get(model_label) or models.get("default") or {}
    provider = model_cfg.get("provider", "openrouter")
    model_id = model_cfg.get("model", "google/gemini-2.5-flash")

    if provider not in PROVIDER_ENDPOINTS:
        print(f"  Unknown provider '{provider}', falling back to openrouter", file=sys.stderr)
        provider = "openrouter"

    endpoint, key_env = PROVIDER_ENDPOINTS[provider]
    api_key = os.environ.get(key_env, "").strip()
    if not api_key:
        print(f"  {key_env} not set — skipping reflection, using defaults", file=sys.stderr)
        return {"intensity": 3, "mood": "reflective", "summary": ""}

    try:
        raw = call_chat_completion(endpoint, api_key, model_id, reflection_system, dream_text)
        raw = raw.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
            if raw.endswith("```"):
                raw = raw[:-3].strip()
        return json.loads(raw)
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, OSError) as e:
        print(f"  Reflection call failed: {e}", file=sys.stderr)
        return {"intensity": 3, "mood": "reflective", "summary": ""}


def insert_header(dream_file: Path, index: int, intensity: int, mood: str) -> None:
    """Insert intensity/mood header after the Nth ## heading."""
    header_line = f"**Intensity:** {intensity}/7 | **Mood:** {mood}"
    text = dream_file.read_text(encoding="utf-8")
    if header_line in text:
        return
    lines = text.split("\n")
    count = 0
    for i, line in enumerate(lines):
        if line.startswith("## "):
            count += 1
            if count == index:
                lines.insert(i + 1, header_line)
                break
    dream_file.write_text("\n".join(lines), encoding="utf-8")


def add_to_preconscious(summary: str, intensity: int) -> None:
    if not os.path.isfile(PRECONSCIOUS_ADD):
        print("preconscious add.py not found, skipping", file=sys.stderr)
        return
    importance = min(5, max(3, intensity - 2))  # Map intensity 5→3, 6→4, 7→5
    result = subprocess.run(
        ["python3", PRECONSCIOUS_ADD, f"Dream: {summary}", "5", str(importance)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode == 0:
        print(f"  Added to preconscious (C=5, I={importance})")
    else:
        print(f"  Preconscious add failed: {result.stderr}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Post-dream reflection and preconscious integration")
    ap.add_argument("--dream-file", required=True, help="Path to dream markdown file")
    ap.add_argument("--dream-index", type=int, required=True, help="Dream number (1-based)")
    ap.add_argument(
        "--reflection-model",
        default="default",
        help="Model label from dream-config.json models table (e.g. default, heretic, opus)",
    )
    ap.add_argument("--category", default="unknown", help="Dream category")
    args = ap.parse_args()

    dream_file = Path(args.dream_file)
    if not dream_file.is_file():
        print(f"Dream file not found: {dream_file}", file=sys.stderr)
        return 1

    config = load_config()

    dream_text = extract_dream_section(dream_file, args.dream_index)
    if not dream_text:
        print(f"Could not extract dream section {args.dream_index}", file=sys.stderr)
        return 1

    print(f"  Scoring dream {args.dream_index} ({args.category}) with '{args.reflection_model}'...")
    scored = score_dream(dream_text, args.reflection_model, config)

    intensity = max(1, min(7, int(scored.get("intensity", 3))))
    mood = scored.get("mood", "reflective")
    summary = scored.get("summary", "")

    print(f"  Result: intensity={intensity}/7, mood={mood}")

    insert_header(dream_file, args.dream_index, intensity, mood)

    if intensity >= 5 and summary:
        add_to_preconscious(summary, intensity)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
