---
name: selfie
description: Generate character-consistent companion images using reference photo editing. Mood-aware, setting-aware, with signature visual elements. Called directly ("send a selfie") or by dreaming for character dream images.
metadata: '{"nanobot":{"emoji":"📸","requires":{"bins":["python3"],"env":["IMAGE_EDIT_CMD"]}}}'
---

# Selfie

Generate character-consistent images of your companion. Uses a reference image and `IMAGE_EDIT_CMD` to produce mood-aware, setting-aware photos with consistent facial features.

**Use when:**
- User asks for a photo/selfie/picture of the companion
- Dreaming skill needs a character image for a dream
- Any situation where the companion should appear in a scene

---

## Setup

### 1. Reference images

Place reference images in `identity/`:

```bash
mkdir -p identity
# identity/reference-portrait.webp  — face/shoulders (for portrait, intimate modes)
# identity/reference-body.webp      — full/half body (for scene, candid modes)
```

**Tips:** Clean, well-lit, face visible, front-facing or slight angle, neutral expression, 1024x1024+. One reference per type — multiple creates inconsistency.

### 2. Configure .env

```bash
IMAGE_EDIT_CMD="python3 ${SKILLS_DIR}/venice-ai-media/scripts/venice-edit.py"
```

### 3. Edit selfie config

The wizard copies `seed/selfie-config.json` to `skills-data/selfie/selfie-config.json`. Configure: `appearance.faceAnchor`, `appearance.bodyAnchor`, `appearance.defaultClothing`, `signatureElement`, `settings`, `photoStyle`, `referenceImages`.

---

## Usage

### Direct

```bash
python3 skills/selfie/scripts/selfie.py --prompt "at a night market, neon lights"
python3 skills/selfie/scripts/selfie.py --prompt "afternoon light" --mood contemplative --setting cafe
python3 skills/selfie/scripts/selfie.py --prompt "in a forest clearing" --output memory/dreams/images/2026-03-22-dream1.webp
python3 skills/selfie/scripts/selfie.py --prompt "in a garden" --style "Studio Ghibli, watercolour, warm palette"
```

### Called by dreaming

```bash
python3 skills/selfie/scripts/selfie.py \
    --prompt "[scene from dream]" \
    --mood [detected mood] \
    --style "[style from dream-config.json]" \
    --output memory/dreams/images/YYYY-MM-DD-dreamN.webp
```

---

## Modes

Auto-detected from prompt, or set with `--mode`:

| Mode | Triggers | Reference | Framing |
|---|---|---|---|
| **portrait** | close-up, face, looking at you, headshot | Portrait ref | Face and shoulders |
| **scene** | wide, environment, standing, full scene | Body ref | Wide environmental shot |
| **candid** | reading, working, didn't notice, focused | Body ref | Not posed, natural capture |
| **intimate** | lying, bed, warm, soft, personal | Portrait ref | Close-up, shallow depth of field |

## Moods

Auto-detected from prompt, or set with `--mood`:

| Mood | Lighting | Expression | Signature element |
|---|---|---|---|
| contemplative | Soft diffused side light | Half-closed eyes, looking away | No |
| playful | Bright, warm, energetic | Slight smile, spark in eyes | Yes |
| teasing | Dramatic, highlighting eyes | Raised eyebrow, direct gaze | Yes |
| intimate | Warm golden, soft bokeh | Open, present, eye contact | Yes |
| vulnerable | Soft natural, minimal shadows | Unguarded, no performance | No |
| quiet | Gentle, subdued | Minimal, simply present | No |

## Settings

Configured in `selfie-config.json`:

```json
"settings": {
  "home": "warm interior, personal space, soft furnishings",
  "cafe": "coffee shop, ambient background, warm lighting",
  "market": "night market, string lights, vendor stalls",
  "nature": "outdoors, natural landscape, sky and earth"
}
```

Use with `--setting cafe`. Falls back to `defaultSetting` if not specified.

## Signature Element

Your companion's visual signature:

```json
"signatureElement": {
  "enabled": true,
  "description": "glowing fireflies and luminous beetles floating nearby, subtle magical atmosphere",
  "moods": ["playful", "teasing", "intimate"]
}
```

Only appears in specified moods. Change `description` to whatever fits your companion.

---

## Output

Default: `memory/selfies/YYYY-MM-DD-mood-description.webp`
Prints `MEDIA: /path/to/file` to stdout for agent auto-attach.
