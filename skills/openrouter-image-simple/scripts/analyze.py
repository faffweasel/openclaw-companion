#!/usr/bin/env python3
"""
Image Analysis (Vision) via OpenRouter - Pure Python stdlib.
Analyze/understand images using vision-capable models.

Usage:
    python3 analyze.py image.png "Describe what's in this image"
    python3 analyze.py image.png "Who is this person?" --model google/gemini-2.0-flash-001

Requires OPENROUTER_API_KEY environment variable.
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_VISION_MODEL = "google/gemini-2.0-flash-001"
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


def analyze_image(image_path, prompt, model=None):
    """Analyze an image using a vision model via OpenRouter."""
    api_key = get_api_key()
    model = model or DEFAULT_VISION_MODEL

    if not os.path.exists(image_path):
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    data_url = load_image_as_base64(image_path)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": prompt}
                ]
            }
        ],
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

    # Extract text response
    try:
        choices = result.get("choices", [])
        if not choices:
            print("Error: No choices in response", file=sys.stderr)
            print(json.dumps(result, indent=2), file=sys.stderr)
            sys.exit(1)

        message = choices[0].get("message", {})
        content = message.get("content", "")
        
        print(content)
        return content

    except (KeyError, IndexError) as e:
        print(f"Error parsing response: {e}", file=sys.stderr)
        print(json.dumps(result, indent=2), file=sys.stderr)
        sys.exit(1)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze images via OpenRouter vision models (pure stdlib, no dependencies)"
    )
    parser.add_argument("image", help="Path to image file to analyze")
    parser.add_argument("prompt", help="What to ask about the image")
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_VISION_MODEL,
        help=f"OpenRouter vision model ID (default: {DEFAULT_VISION_MODEL})",
    )

    args = parser.parse_args()
    analyze_image(args.image, args.prompt, args.model)


if __name__ == "__main__":
    main()
