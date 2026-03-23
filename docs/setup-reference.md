# Setup Reference

Shared setup patterns for skills that use external APIs. Not loaded by the
agent — reference for humans configuring the workspace.

---

## API Keys in Docker

API keys go in `docker-compose.override.yml` as environment variables, **not**
in the workspace `.env` (which is readable by the agent).

```yaml
services:
  nanobot-gateway:
    environment:
      - VENICE_API_KEY=vn_your_key_here
      - OPENROUTER_API_KEY=sk-or-v1-your_key_here
      - NVIDIA_API_KEY=nvapi-your_key_here
```

After changing the override file: `docker compose up -d`

### Skills that need API keys

| Skill | Key | Purpose |
|---|---|---|
| venice-ai-media | `VENICE_API_KEY` | Image/video generation |
| dreaming | `VENICE_API_KEY`, `OPENROUTER_API_KEY` | Dream generation + reflection models |
| multi-provider | Any provider keys | API routing |
| openrouter-image-simple | `OPENROUTER_API_KEY` | Image generation via OpenRouter |
| memory-search | `OPENROUTER_API_KEY` (optional) | Semantic embeddings |

---

## .env Variables

The workspace `.env` holds paths, timezone, and identifiers. Not secrets.

```bash
TZ=Asia/Bangkok
WORKSPACE=/path/to/workspace
SKILLS_DIR=${WORKSPACE}/skills
DATA_DIR=${WORKSPACE}/skills-data

# Optional — for image generation
IMAGE_GEN_CMD="python3 ${SKILLS_DIR}/venice-ai-media/scripts/venice-image.py"
IMAGE_EDIT_CMD="python3 ${SKILLS_DIR}/venice-ai-media/scripts/venice-edit.py"
COMPANION_REFERENCE_PORTRAIT="${WORKSPACE}/identity/reference-portrait.webp"
COMPANION_REFERENCE_BODY="${WORKSPACE}/identity/reference-body.webp"

# Optional — blog writer
BLOG_CHECK_DAYS=3

# Optional — dream images
DREAM_IMAGE_MODE=morning  # morning | archive | none
```

---

## Verifying Setup

```bash
# Venice AI
python3 skills/venice-ai-media/scripts/venice-image.py --list-models

# Memory search embeddings
python3 skills/memory-search/scripts/search.py --check

# Memory search provider
python3 skills/memory-search/scripts/providers.py
```
