# Image Generation Interface

Any skill that wants to be used as `IMAGE_GEN_CMD` must follow this contract. Other skills (dreaming, weekly-state-of-me) call `IMAGE_GEN_CMD` without knowing which image generation skill is behind it.

---

## .env Configuration

```bash
# Text-to-image (abstract dreams, visual journals)
IMAGE_GEN_CMD="python3 ${SKILLS_DIR}/venice-ai-media/scripts/venice-image.py"
# or
IMAGE_GEN_CMD="python3 ${SKILLS_DIR}/openrouter-image-simple/scripts/generate.py"

# Reference-based image editing (character in scene)
IMAGE_EDIT_CMD="python3 ${SKILLS_DIR}/venice-ai-media/scripts/venice-edit.py"

# Reference image for character consistency
COMPANION_REFERENCE_IMAGE="${WORKSPACE}/identity/reference.webp"
```

`IMAGE_GEN_CMD` and `IMAGE_EDIT_CMD` are full command paths. `COMPANION_REFERENCE_IMAGE` is a file path. All stored in workspace `.env` (paths, not secrets).

API keys belong in `docker-compose.override.yml`, never in `.env`. See [architecture.md](architecture.md) for details.

---

## IMAGE_GEN_CMD — Text-to-Image

Every `IMAGE_GEN_CMD`-compatible script must accept:

```bash
$IMAGE_GEN_CMD --prompt "description of the image" --output /full/path/to/file.webp
```

| Flag | Required | Description |
|---|---|---|
| `--prompt` | Yes | Text description of the image to generate |
| `--output` | Yes | Full output file path including filename and extension |

The script must:

1. Accept `--prompt` and `--output` as named flags (not positional-only)
2. Create parent directories if they don't exist
3. Write exactly one image to the specified `--output` path
4. Infer the output format from the file extension (`.webp`, `.png`, `.jpg`)
5. Print `MEDIA: /path/to/file` to stdout on success
6. Exit 0 on success, non-zero on failure
7. Print errors to stderr, not stdout
8. Read its API key from an environment variable (set via `docker-compose.override.yml`)

## Callers (IMAGE_GEN_CMD)

| Skill | When | Output path pattern |
|---|---|---|
| weekly-state-of-me | Step 7 (visual journal) | `memory/state-of-me/images/YYYY-MM-DD.webp` |
| dreaming | Abstract dream images | `memory/dreams/images/YYYY-MM-DD-dreamN.webp` |

Callers always:
- Source `.env` to get `IMAGE_GEN_CMD`
- Provide both `--prompt` and `--output`
- Control the output filename (typically date-based)
- Check whether `IMAGE_GEN_CMD` is set before calling

---

## IMAGE_EDIT_CMD — Reference-Based Editing

For character-consistent images (companion appears in the scene):

```bash
$IMAGE_EDIT_CMD --input /path/to/reference.webp --prompt "scene description" --output /full/path/to/file.webp
```

| Flag | Required | Description |
|---|---|---|
| `--input` | Yes | Reference image path (the character/face to preserve) |
| `--prompt` | Yes | Scene description + style |
| `--output` | Yes | Full output file path including filename and extension |

The script must:

1. Accept `--input`, `--prompt`, and `--output` as named flags
2. Use the input image as a reference for the edit (img2img)
3. Create parent directories if they don't exist
4. Write exactly one image to the specified `--output` path
5. Print `MEDIA: /path/to/file` to stdout on success
6. Exit 0 on success, non-zero on failure
7. Print errors to stderr

### Companion Reference Images

Two reference images for different framing:

```bash
COMPANION_REFERENCE_PORTRAIT="${WORKSPACE}/identity/reference-portrait.webp"
COMPANION_REFERENCE_BODY="${WORKSPACE}/identity/reference-body.webp"
```

The selfie skill selects automatically: portrait reference for close-ups/intimate, body reference for scenes/candid. Both stored in `identity/` alongside SOUL.md and IDENTITY.md.

**Creating good reference images:**
- Clean, well-lit, face clearly visible, minimal background
- Front-facing or slight angle — extreme profiles reduce consistency
- Neutral expression — the edit model adapts expression to the scene
- Resolution: 1024x1024 or higher
- For AI-generated companions: generate one canonical image, iterate until happy
- For real people: a natural photo works, avoid heavy filters
- One reference per type — multiple creates inconsistency

### Callers (IMAGE_EDIT_CMD)

| Skill | When | Output path pattern |
|---|---|---|
| selfie | Character images (selfies, dream images via dreaming) | `memory/selfies/*.webp` or caller-specified |

---

## Currently Compatible Skills

| Skill | Script | Supports | API Key Env Var |
|---|---|---|---|
| venice-ai-media | `venice-image.py` | `IMAGE_GEN_CMD` | `VENICE_API_KEY` |
| venice-ai-media | `venice-edit.py` | `IMAGE_EDIT_CMD` | `VENICE_API_KEY` |
| openrouter-image-simple | `generate.py` | `IMAGE_GEN_CMD`, `IMAGE_EDIT_CMD` (via `--input`) | `OPENROUTER_API_KEY` |

Both also support direct usage with additional flags beyond the standard interface. See each skill's SKILL.md for full documentation.

## Adding a New Image Skill

1. Implement `--prompt` + `--output` for `IMAGE_GEN_CMD` compatibility
2. Optionally implement `--input` + `--prompt` + `--output` for `IMAGE_EDIT_CMD`
3. Read the API key from an environment variable, not from workspace files
4. Document the env var with setup instructions pointing to `docker-compose.override.yml`
5. Add the skill to the table above
6. Add an entry to `docs/skills-catalogue.md`
