#!/usr/bin/env python3
"""
Image Generation via OpenRouter - Pure Python stdlib, no dependencies.
Routes through OpenRouter for spend control via credit balance.

Usage:
    python3 generate.py "prompt" output.png
    python3 generate.py "edit instructions" output.png --input original.png
    python3 generate.py "prompt" output.png --model gemini-pro
    python3 generate.py --check

Requires OPENROUTER_API_KEY environment variable.
Model and aliases configured in skills-data/openrouter-image-simple/config.json.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path

# Workspace detection
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
CONFIG_FILE = os.path.join(SKILL_DATA, "config.json")

_FALLBACK_ALIASES = {
    "gemini": "google/gemini-2.5-flash-image",
    "gemini-3.1": "google/gemini-3.1-flash-image-preview",
    "gemini-pro": "google/gemini-3-pro-image-preview",
    "sourceful": "sourceful/riverflow-v2-fast",
    "sourceful-pro": "sourceful/riverflow-v2-pro",
    "seedream": "bytedance-seed/seedream-4.5",
    "flux": "sourceful/riverflow-v2-fast",
    "gpt-image": "openai/gpt-5-image-mini",
}


def _load_config() -> dict:
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


_config = _load_config()
_gen_cfg = _config.get("generation", {})
DEFAULT_MODEL = _gen_cfg.get("model", "google/gemini-2.5-flash-image")
ALIASES = _gen_cfg.get("aliases", _FALLBACK_ALIASES)
API_URL = _config.get("apiUrl", "https://openrouter.ai/api/v1/chat/completions")
MODELS_URL = "https://openrouter.ai/api/v1/models?output_modalities=image"


def get_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("Error: OPENROUTER_API_KEY not found in environment", file=sys.stderr)
        print("Set it via OpenClaw's environment configuration.", file=sys.stderr)
        sys.exit(1)
    return key


def resolve_model(model: str) -> str:
    return ALIASES.get(model, model)


def load_image_as_base64(path: str) -> str:
    mime_type = detect_mime_type(path)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime_type};base64,{b64}"


def detect_mime_type(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/png")


def check_account() -> None:
    """Query available image models and verify account access."""
    api_key = get_api_key()
    req = urllib.request.Request(
        MODELS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} checking account: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)

    models = [m.get("id") for m in data.get("data", [])]
    print(f"Account OK — {len(models)} image model(s) available\n")

    default_ok = DEFAULT_MODEL in models
    status = "✓" if default_ok else "✗ NOT FOUND"
    print(f"Default model: {DEFAULT_MODEL} — {status}")

    print("\nAll available image models:")
    for m in sorted(models):
        print(f"  {m}")

    print("\nConfigured aliases:")
    for alias, target in sorted(ALIASES.items()):
        found = "✓" if target in models else "✗ not available"
        print(f"  {alias:15} → {target}  [{found}]")

    if not default_ok:
        print(f"\n⚠ Default model '{DEFAULT_MODEL}' not found.", file=sys.stderr)
        print("Update defaultGenerationModel in skills-data/openrouter-image-simple/config.json", file=sys.stderr)
        sys.exit(1)


def generate_image(prompt: str, output_path: str, input_image_path: str | None = None, model: str | None = None) -> str:
    api_key = get_api_key()
    model = resolve_model(model or DEFAULT_MODEL)

    if input_image_path:
        if not os.path.exists(input_image_path):
            print(f"Error: Input image not found: {input_image_path}", file=sys.stderr)
            sys.exit(1)
        data_url = load_image_as_base64(input_image_path)
        content = [
            {"type": "image_url", "image_url": {"url": data_url}},
            {"type": "text", "text": prompt},
        ]
    else:
        content = prompt

    # Gemini models need both modalities; image-only models use just "image"
    is_gemini = model.startswith("google/")
    modalities = ["image", "text"] if is_gemini else ["image"]

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "modalities": modalities,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(API_URL, data=data, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"HTTP Error {e.code}: {error_body}", file=sys.stderr)
        if e.code == 404:
            print(f"\nModel '{model}' not found on OpenRouter.", file=sys.stderr)
            print("Run --check to see available models and verify account access.", file=sys.stderr)
            print("Note: OpenRouter returns 404 (not 401) when OPENROUTER_API_KEY is missing or invalid.", file=sys.stderr)
        elif e.code == 402:
            print("\nInsufficient credits: https://openrouter.ai/credits", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)

    try:
        choices = result.get("choices", [])
        if not choices:
            print("Error: No choices in response", file=sys.stderr)
            print(json.dumps(result, indent=2), file=sys.stderr)
            sys.exit(1)

        message = choices[0].get("message", {})
        images = message.get("images", [])

        if not images:
            print("Error: No images in response", file=sys.stderr)
            print(json.dumps(result, indent=2), file=sys.stderr)
            sys.exit(1)

        image_url = images[0].get("image_url", {}).get("url", "")
        if not image_url:
            print("Error: Empty image URL in response", file=sys.stderr)
            sys.exit(1)

        if ";base64," in image_url:
            b64_data = image_url.split(";base64,", 1)[1]
        else:
            b64_data = image_url

        img_data = base64.b64decode(b64_data)

        output_dir = Path(output_path).parent
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(img_data)

        print(f"Saved: {output_path}")
        print(f"\nMEDIA: {output_path}")
        return output_path

    except (KeyError, IndexError) as e:
        print(f"Error parsing response: {e}", file=sys.stderr)
        print(json.dumps(result, indent=2), file=sys.stderr)
        sys.exit(1)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate or edit images via OpenRouter (pure stdlib, no dependencies)"
    )
    parser.add_argument("prompt_pos", nargs="?", help="Image prompt (positional)")
    parser.add_argument("output_pos", nargs="?", help="Output file path (positional)")
    parser.add_argument("--prompt", "-p", dest="prompt_flag", help="Image prompt (named flag)")
    parser.add_argument("--output", "-o", dest="output_flag", help="Output file path (named flag)")
    parser.add_argument("--input", "-i", help="Input image for editing (optional)")
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"Model ID or alias (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify account access and list available image models",
    )

    args = parser.parse_args()

    if args.check:
        check_account()
        return

    prompt = args.prompt_flag or args.prompt_pos
    output = args.output_flag or args.output_pos

    if not prompt:
        parser.error("prompt is required (positional or --prompt)")
    if not output:
        parser.error("output is required (positional or --output)")

    generate_image(prompt, output, args.input, args.model)


if __name__ == "__main__":
    main()
