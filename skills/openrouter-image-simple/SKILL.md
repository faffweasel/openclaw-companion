---
name: openrouter-image-simple
description: Generate, edit, and analyze images via OpenRouter using pure Python stdlib. Zero dependencies. Supports Gemini 2.5 Flash image generation and vision analysis.
metadata: '{"nanobot":{"emoji":"🎨","requires":{"bins":["python3"],"env":["OPENROUTER_API_KEY"]}}}'
---

# OpenRouter Image Simple

Generate, edit, and analyze images via OpenRouter. Multiple models supported including Gemini 2.5 Flash Image. Pure Python stdlib — no pip installs needed.

## Prerequisites

- **Python 3.10+**
- **OpenRouter API key** — see `docs/setup-reference.md` for Docker environment configuration

## Setup

1. Get your API key at [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys) (starts with `sk-or-v1-`)
2. Add to `docker-compose.override.yml` per `docs/setup-reference.md`
3. Verify:
   ```bash
   python3 skills/openrouter-image-simple/scripts/generate.py "A test image" /tmp/test.png
   ```

## Quick Start

```bash
# Generate image
python3 skills/openrouter-image-simple/scripts/generate.py "A cat wearing a tiny hat" cat.png

# Analyze image (vision)
python3 skills/openrouter-image-simple/scripts/analyze.py cat.png "What's in this image?"

# Edit existing image
python3 skills/openrouter-image-simple/scripts/generate.py "Make it sunset lighting" edited.png --input original.png
```

## Image Generation

```bash
python3 skills/openrouter-image-simple/scripts/generate.py "Misty mountains at sunrise" mountains.png
python3 skills/openrouter-image-simple/scripts/generate.py "prompt" output.png --model google/gemini-2.5-flash-image-preview:floor
python3 skills/openrouter-image-simple/scripts/generate.py "Add a rainbow" rainbow.png --input mountains.png
```

**Key flags:** `prompt` (positional or `--prompt`), `output` (positional or `--output`), `--input` (source image for editing), `--model` (default: `google/gemini-2.5-flash-image-preview`)

Both calling conventions work:
```bash
python3 .../generate.py "a cat" cat.webp           # positional
python3 .../generate.py --prompt "a cat" --output cat.webp  # IMAGE_GEN_CMD compatible
```

Supported input formats: PNG, JPG, JPEG, GIF, WEBP.

## Image Analysis (Vision)

```bash
python3 skills/openrouter-image-simple/scripts/analyze.py image.png "Describe what you see"
python3 skills/openrouter-image-simple/scripts/analyze.py image.png "prompt" --model google/gemini-2.0-flash-001
```

**Key flags:** `image` (positional), `prompt` (positional), `--model` (default: `google/gemini-2.0-flash-001`)

## Available Models

**Image Generation:**
- `google/gemini-2.5-flash-image-preview` (default) — text + image output
- `google/gemini-2.5-flash-image-preview:floor` — faster, cheaper variant

**Image Analysis (Vision):**
- `google/gemini-2.0-flash-001` (default)
- Any OpenRouter model with vision capabilities

## Output

`generate.py` prints `MEDIA: /path/to/file` on stdout for agent auto-attach. `analyze.py` prints the model's text response.

## Troubleshooting

**"OPENROUTER_API_KEY not found"** — See `docs/setup-reference.md` for Docker environment setup. Restart with `docker compose up -d` after changes.

**"No images in response"** — Model may not support generation. Try the default model. Check OpenRouter credit balance.

**"HTTP Error 429"** — Rate limited. Wait and retry.
