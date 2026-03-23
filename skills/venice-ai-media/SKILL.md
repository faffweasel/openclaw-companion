---
name: venice-ai-media
description: Generate, edit, and upscale images; create videos from images via Venice AI. Supports text-to-image, image-to-video (Sora, WAN), upscaling, and AI editing. Called by other skills via IMAGE_GEN_CMD.
metadata: '{"nanobot":{"emoji":"🎨","requires":{"bins":["python3"],"env":["VENICE_API_KEY"]}}}'
---

# Venice AI Media

Generate images and videos using Venice AI APIs. Venice is an uncensored AI platform with competitive pricing.

Other skills (dreaming, weekly-state-of-me) call this via the `IMAGE_GEN_CMD` environment variable.

## Prerequisites

- **Python 3.10+**
- **Venice API key** — see `docs/setup-reference.md` for Docker environment configuration

## Setup

### 1. Get Your API Key

1. Create account at [venice.ai](https://venice.ai)
2. Go to [venice.ai/settings/api](https://venice.ai/settings/api)
3. Click "Create API Key" (starts with `vn_...`)

### 2. Configure IMAGE_GEN_CMD

Add to your workspace `.env`:

```bash
IMAGE_GEN_CMD="python3 ${SKILLS_DIR}/venice-ai-media/scripts/venice-image.py"
```

### 3. Verify Setup

```bash
python3 skills/venice-ai-media/scripts/venice-image.py --list-models
```

## Pricing Overview

| Feature          | Cost                              |
| ---------------- | --------------------------------- |
| Image generation | ~$0.01-0.03 per image             |
| Image upscale    | ~$0.02-0.04                       |
| Image edit       | $0.04                             |
| Video (WAN)      | ~$0.10-0.50 depending on duration |
| Video (Sora)     | ~$0.50-2.00 depending on duration |

Use `--quote` with video commands to check pricing before generation.

## Image Generation

```bash
python3 skills/venice-ai-media/scripts/venice-image.py --prompt "a serene canal in Venice at sunset"
python3 skills/venice-ai-media/scripts/venice-image.py --prompt "cyberpunk city" --count 4
python3 skills/venice-ai-media/scripts/venice-image.py --prompt "portrait" --width 768 --height 1024
python3 skills/venice-ai-media/scripts/venice-image.py --prompt "abstract art" --out-dir /tmp/venice
python3 skills/venice-ai-media/scripts/venice-image.py --list-models
python3 skills/venice-ai-media/scripts/venice-image.py --list-styles
```

**Key flags:** `--prompt`, `--model` (default: lustify-sdxl), `--output` (single image to exact path), `--count` (batch), `--width`, `--height`, `--format` (webp/png/jpeg), `--out-dir`, `--resolution` (1K/2K/4K), `--aspect-ratio`, `--negative-prompt`, `--style-preset` (use `--list-styles`), `--cfg-scale` (0-20, default 7.5), `--seed`, `--safe-mode` (disabled by default), `--hide-watermark`, `--embed-exif`, `--lora-strength` (0-100), `--steps`, `--enable-web-search`, `--no-validate` (skip model check)

When `--output` is used, generates exactly one image to that path. `--output` and `--out-dir`/`--count` are mutually exclusive.

## Image Upscale

```bash
python3 skills/venice-ai-media/scripts/venice-upscale.py photo.jpg --scale 2
python3 skills/venice-ai-media/scripts/venice-upscale.py photo.jpg --scale 4 --enhance
python3 skills/venice-ai-media/scripts/venice-upscale.py --url "https://example.com/image.jpg" --scale 2
```

**Key flags:** `--scale` (1-4, default: 2), `--enhance`, `--enhance-prompt`, `--enhance-creativity` (0.0-1.0), `--replication` (0.0-1.0, default: 0.35), `--url`, `--output`, `--out-dir`

## Image Edit

```bash
python3 skills/venice-ai-media/scripts/venice-edit.py photo.jpg --prompt "add sunglasses"
python3 skills/venice-ai-media/scripts/venice-edit.py photo.jpg --prompt "change the sky to sunset" --model flux-2-max-edit
python3 skills/venice-ai-media/scripts/venice-edit.py --list-models
```

**Key flags:** `--prompt` (required), `--model` (default: seedream-v4-edit), `--aspect-ratio` (auto, 1:1, 3:2, 16:9, 21:9, 9:16, 2:3, 3:4, 4:5), `--url`, `--output`, `--out-dir`, `--list-models`, `--no-validate`

**Note:** The default model has some content restrictions. Use `--list-models` to see alternatives.

## Video Generation

```bash
# Get price quote first
python3 skills/venice-ai-media/scripts/venice-video.py --quote --model wan-2.6-image-to-video --duration 10s --resolution 720p

# Image-to-video (WAN 2.6 — default)
python3 skills/venice-ai-media/scripts/venice-video.py --image photo.jpg --prompt "camera pans slowly" --duration 10s

# Image-to-video (Sora)
python3 skills/venice-ai-media/scripts/venice-video.py --image photo.jpg --prompt "cinematic" \
  --model sora-2-image-to-video --duration 8s --aspect-ratio 16:9 --skip-audio-param

# List models
python3 skills/venice-ai-media/scripts/venice-video.py --list-models
```

**Key flags:** `--image` (required), `--prompt` (required), `--model` (default: wan-2.6-image-to-video), `--duration`, `--resolution` (480p/720p/1080p), `--aspect-ratio`, `--audio`/`--no-audio`, `--skip-audio-param`, `--quote`, `--timeout`, `--poll-interval`, `--no-delete`, `--complete` (cleanup), `--no-validate`

## Model Notes

Use `--list-models` to see current availability. Models change frequently.

**Tips:**
- Use `--no-validate` for new or beta models not yet in the model list
- Use `--quote` for video to check pricing before generation
- Safe mode is disabled by default (Venice is an uncensored API)

## Troubleshooting

**"VENICE_API_KEY not found in environment"** — See `docs/setup-reference.md` for Docker environment setup.

**"Invalid API key"** — Verify at [venice.ai/settings/api](https://venice.ai/settings/api). Keys start with `vn_`.

**"Model not found"** — Run `--list-models`. Use `--no-validate` for new/beta models.

**Video stuck/timeout** — Videos take 1-5 minutes. Use `--timeout 600` for longer videos.
