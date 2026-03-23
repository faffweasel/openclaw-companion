#!/usr/bin/env python3
"""
Image Generation via OpenRouter - Pure Python stdlib, no dependencies.
Routes through OpenRouter for spend control via credit balance.

Usage:
    python3 generate.py "prompt" output.png
    python3 generate.py "edit instructions" output.png --input original.png
    python3 generate.py "prompt" output.png --model google/gemini-2.5-flash-preview:image

Requires OPENROUTER_API_KEY environment variable.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_MODEL = "google/gemini-2.5-flash-image-preview"

# Valid image models on OpenRouter
VALID_MODELS = {
    "gemini": "google/gemini-2.5-flash-image-preview",  # text + image output
    "gemini-fast": "google/gemini-2.5-flash-image-preview:floor",  # faster, cheaper
    "sourceful": "mistralai/sourceful-v0.1",  # image only
    "flux": "black-forest-labs/flux-1-schnell",  # image only
}
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_api_key():
    """Get API key from environment."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        print("Error: OPENROUTER_API_KEY not found in environment", file=sys.stderr)
        print("Add it to docker-compose.override.yml:", file=sys.stderr)
        print("  environment:", file=sys.stderr)
        print("    - OPENROUTER_API_KEY=sk-or-v1-your_key_here", file=sys.stderr)
        sys.exit(1)
    return key


def load_image_as_base64(path):
    """Load an image file and return base64 data URL."""
    mime_type = detect_mime_type(path)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:{mime_type};base64,{b64}"


def detect_mime_type(path):
    """Detect MIME type from file extension."""
    ext = Path(path).suffix.lower()
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mime_types.get(ext, "image/png")


def generate_image(prompt, output_path, input_image_path=None, model=None):
    """Generate or edit an image via OpenRouter."""
    api_key = get_api_key()
    model = model or DEFAULT_MODEL

    # Build message content
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

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "modalities": ["image", "text"],
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
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)

    # Extract image from OpenRouter response
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

        # First image - extract base64 from data URL
        image_url = images[0].get("image_url", {}).get("url", "")

        if not image_url:
            print("Error: Empty image URL in response", file=sys.stderr)
            sys.exit(1)

        # Strip data URL prefix: "data:image/png;base64,..."
        if ";base64," in image_url:
            b64_data = image_url.split(";base64,", 1)[1]
        else:
            b64_data = image_url

        img_data = base64.b64decode(b64_data)

        # Ensure output directory exists
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


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate or edit images via OpenRouter (pure stdlib, no dependencies)"
    )
    # Positional args (direct usage)
    parser.add_argument("prompt_pos", nargs="?", help="Image prompt (positional)")
    parser.add_argument("output_pos", nargs="?", help="Output file path (positional)")
    # Named flags (IMAGE_GEN_CMD compatible)
    parser.add_argument("--prompt", "-p", dest="prompt_flag", help="Image prompt (named flag)")
    parser.add_argument("--output", "-o", dest="output_flag", help="Output file path (named flag)")
    parser.add_argument("--input", "-i", help="Input image for editing (optional)")
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"OpenRouter model ID (default: {DEFAULT_MODEL})",
    )

    args = parser.parse_args()

    # Resolve: named flags take priority over positional
    prompt = args.prompt_flag or args.prompt_pos
    output = args.output_flag or args.output_pos

    if not prompt:
        parser.error("prompt is required (positional or --prompt)")
    if not output:
        parser.error("output is required (positional or --output)")

    generate_image(prompt, output, args.input, args.model)


if __name__ == "__main__":
    main()
