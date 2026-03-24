---
name: openrouter-image-simple
description: Generate, edit, and analyze images via OpenRouter using pure Python stdlib. Zero dependencies. Supports multiple image generation models and vision analysis.
metadata: '{"openclaw":{"emoji":"🎨","requires":{"bins":["python3"],"env":["OPENROUTER_API_KEY"]}}}'
---

# OpenRouter Image Simple

Generate, edit, and analyze images via OpenRouter. Pure Python stdlib — no pip installs needed.

## Prerequisites

- **Python 3.10+**
- **OpenRouter API key** — set via OpenClaw's environment configuration as `OPENROUTER_API_KEY`

## Setup

1. Get your API key at [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys) (starts with `sk-or-v1-`)
2. Add to OpenClaw's environment configuration
3. Verify account access and available models:
   ```bash
   python3 skills/openrouter-image-simple/scripts/generate.py --check
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
python3 skills/openrouter-image-simple/scripts/generate.py "prompt" output.png --model gemini-pro
python3 skills/openrouter-image-simple/scripts/generate.py "Add a rainbow" rainbow.png --input mountains.png
```

**Flags:** `prompt` (positional or `--prompt`), `output` (positional or `--output`), `--input` (source image for editing), `--model` (alias or full model ID), `--check` (account diagnostics)

Both calling conventions work:
```bash
python3 .../generate.py "a cat" cat.webp                         # positional
python3 .../generate.py --prompt "a cat" --output cat.webp       # IMAGE_GEN_CMD compatible
```

Supported input formats: PNG, JPG, JPEG, GIF, WEBP.

## Image Analysis (Vision)

```bash
python3 skills/openrouter-image-simple/scripts/analyze.py image.png "Describe what you see"
python3 skills/openrouter-image-simple/scripts/analyze.py image.png "prompt" --model google/gemini-2.0-flash-001
```

## Configuration

Models and aliases are configured in `skills-data/openrouter-image-simple/config.json` (seeded from `seed/config.json` during setup). To change the default model or add aliases, edit that file — no script changes needed.

```json
{
  "generation": {
    "model": "google/gemini-2.5-flash-image",
    "aliases": { "gemini": "google/gemini-2.5-flash-image", ... }
  },
  "vision": {
    "model": "google/gemini-2.0-flash-001"
  }
}
```

## Available Models (March 2026)

**Image Generation** — verified on OpenRouter:

| Alias | Model ID | Notes |
|---|---|---|
| `gemini` | `google/gemini-2.5-flash-image` | Default. Cheapest Gemini. |
| `gemini-3.1` | `google/gemini-3.1-flash-image-preview` | Faster |
| `gemini-pro` | `google/gemini-3-pro-image-preview` | Highest quality Gemini |
| `sourceful` | `sourceful/riverflow-v2-fast` | Fast, production-grade |
| `sourceful-pro` | `sourceful/riverflow-v2-pro` | Highest quality non-Gemini |
| `seedream` | `bytedance-seed/seedream-4.5` | ByteDance |
| `gpt-image` | `openai/gpt-5-image-mini` | GPT-5 image |
| `flux` | `sourceful/riverflow-v2-fast` | Alias (Flux removed from OpenRouter) |

**Vision:** `google/gemini-2.0-flash-001` (default), or any OpenRouter vision model.

Run `generate.py --check` to see what's currently available on your account.

## Output

`generate.py` prints `MEDIA: /path/to/file` on stdout for agent auto-attach. `analyze.py` prints the model's text response.

## Troubleshooting

**First step for any failure:** run `--check` to verify account access and model availability.

```bash
python3 skills/openrouter-image-simple/scripts/generate.py --check
```

**"HTTP 404"** — Model not found, or `OPENROUTER_API_KEY` is missing/invalid. OpenRouter returns 404 (not 401) for auth failures. Run `--check` to confirm which.

**"OPENROUTER_API_KEY not found"** — Set it via OpenClaw's environment configuration.

**"No images in response"** — Model may not support image generation. Run `--check` and pick a model from the available list.

**"HTTP 402"** — Insufficient credits. Top up at [openrouter.ai/credits](https://openrouter.ai/credits).

**"HTTP 429"** — Rate limited. Wait and retry.
