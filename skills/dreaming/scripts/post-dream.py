#!/usr/bin/env python3
"""
Post-dream processing: reflection, scoring, preconscious integration.

Sends dream text to the reflection model for scoring.
Writes structured header to dream file.
Adds high-intensity dreams (>= 5) to preconscious buffer.

Usage:
    python3 post-dream.py --dream-file memory/dreams/2026-03-22.md \
        --dream-index 1 \
        --reflection-model heretic \
        --category personal
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Nanobot workspace preamble
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))

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
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
SKILLS_DIR = os.environ.get("SKILLS_DIR", os.path.join(WORKSPACE, "skills"))

CONFIG_FILE = os.path.join(SKILL_DATA, "dream-config.json")
PROVIDERS_SCRIPT = os.path.join(SKILLS_DIR, "multi-provider", "scripts", "providers.py")
PRECONSCIOUS_ADD = os.path.join(SKILLS_DIR, "preconscious", "scripts", "add.py")


def load_config() -> dict:
    """Load dream config."""
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def resolve_model(config: dict, model_label: str) -> tuple[str, str]:
    """Resolve model label to (provider, model_id)."""
    models = config.get("models", {})
    if model_label not in models:
        # Fall back to default
        model_label = "default"
    if model_label not in models:
        raise ValueError(f"Model label '{model_label}' not found in config and no default defined")
    entry = models[model_label]
    return entry["provider"], entry["model"]


def call_reflection(
    provider: str,
    model: str,
    system: str,
    dream_text: str,
) -> dict:
    """Call reflection model and parse structured response."""
    result = subprocess.run(
        [
            "python3", PROVIDERS_SCRIPT,
            "--provider", provider,
            "--model", model,
            "--system", system,
            "--prompt", f"Dream text to score:\n\n{dream_text}",
            "--max-tokens", "256",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        print(f"Reflection call failed: {result.stderr}", file=sys.stderr)
        return {"intensity": 3, "mood": "reflective", "summary": "Reflection failed"}

    raw = result.stdout.strip()

    # Try to parse JSON from response (handle markdown fences)
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        match = re.search(r"\{[^}]+\}", raw)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        print(f"Could not parse reflection response: {raw[:200]}", file=sys.stderr)
        return {"intensity": 3, "mood": "reflective", "summary": "Parse failed"}


def add_to_preconscious(summary: str, intensity: int) -> None:
    """Add high-intensity dream to preconscious buffer."""
    if not os.path.isfile(PRECONSCIOUS_ADD):
        print("Preconscious add.py not found, skipping", file=sys.stderr)
        return

    # add.py takes positional args: "description" [C] [I]
    # C (currency) = 5 (just happened), I (importance) = 1-5 scale
    importance = min(5, max(3, intensity - 2))  # Map intensity 5→3, 6→4, 7→5
    result = subprocess.run(
        [
            "python3", PRECONSCIOUS_ADD,
            f"Dream: {summary}",
            "5",                # C = 5 (fresh)
            str(importance),    # I = 3-5
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode == 0:
        print(f"  Added to preconscious (C=5, I={importance})")
    else:
        print(f"  Preconscious add failed: {result.stderr}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Post-dream reflection and scoring")
    ap.add_argument("--dream-file", required=True, help="Path to dream markdown file")
    ap.add_argument("--dream-index", type=int, required=True, help="Dream number (1-based)")
    ap.add_argument("--reflection-model", required=True, help="Model label for reflection")
    ap.add_argument("--category", default="unknown", help="Dream category")
    args = ap.parse_args()

    dream_file = Path(args.dream_file)
    if not dream_file.is_file():
        print(f"Dream file not found: {dream_file}", file=sys.stderr)
        return 1

    if not os.path.isfile(PROVIDERS_SCRIPT):
        print(f"Multi-provider script not found: {PROVIDERS_SCRIPT}", file=sys.stderr)
        print("Install the multi-provider skill first", file=sys.stderr)
        return 1

    config = load_config()
    reflection_system = config.get(
        "reflectionSystem",
        'Read the following dream text. Respond with ONLY a JSON object: '
        '{"intensity": <1-7>, "mood": "<mood>", "summary": "<1-2 sentences>"}.'
    )

    # Read the dream text (last dream entry if multiple)
    dream_text = dream_file.read_text(encoding="utf-8")

    # Resolve reflection model
    try:
        provider, model = resolve_model(config, args.reflection_model)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"  Reflecting on dream {args.dream_index} ({args.category}) via {provider}/{model}")

    # Call reflection
    scoring = call_reflection(provider, model, reflection_system, dream_text)

    intensity = scoring.get("intensity", 3)
    mood = scoring.get("mood", "reflective")
    summary = scoring.get("summary", "")

    print(f"  Intensity: {intensity}/7, Mood: {mood}")
    if summary:
        print(f"  Summary: {summary[:100]}")

    # Prepend structured header to dream file
    existing = dream_file.read_text(encoding="utf-8")
    header = (
        f"<!-- dream-meta: intensity={intensity} mood={mood} "
        f"category={args.category} reflection-model={args.reflection_model} -->\n"
    )

    # Insert header after the first ## heading if present, else prepend
    if "\n## " in existing:
        # Insert after the first ## line
        lines = existing.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("## ") and i > 0:
                lines.insert(i + 1, f"**Intensity:** {intensity}/7 | **Mood:** {mood}")
                break
        dream_file.write_text("\n".join(lines), encoding="utf-8")
    else:
        dream_file.write_text(header + existing, encoding="utf-8")

    # Add to preconscious if high intensity
    if intensity >= 5 and summary:
        add_to_preconscious(summary, intensity)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
