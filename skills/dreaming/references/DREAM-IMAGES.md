# Dream Images

Image generation for dreams. Only loaded when `dreamImages: true` in `dream-config.json`.

---

## .env Configuration

```bash
IMAGE_GEN_CMD="python3 ${SKILLS_DIR}/venice-ai-media/scripts/venice-image.py"
IMAGE_EDIT_CMD="python3 ${SKILLS_DIR}/venice-ai-media/scripts/venice-edit.py"
COMPANION_REFERENCE_PORTRAIT="${WORKSPACE}/identity/reference-portrait.webp"
COMPANION_REFERENCE_BODY="${WORKSPACE}/identity/reference-body.webp"
```

Place companion reference image at `identity/reference.webp` if using character-consistent dream images. See selfie skill SKILL.md for reference image tips.

```bash
mkdir -p identity
```

---

## Category-to-Style Mapping (topicStyles)

In `dream-config.json`, the `topicStyles` dict maps dream categories to image styles:

```json
"styles": {
  "film": "Natural warm lighting... Rinko Kawauchi style...",
  "anime": "Studio Ghibli inspired...",
  "noir": "High contrast black and white...",
  "abstract": "No character. Abstract colours, textures..."
},
"defaultStyle": "film",
"topicStyles": {
  "hypothetical": "anime",
  "personal": "film",
  "creative": "impressionist"
}
```

How it works:
1. Dream generates with category `"creative"`
2. Pipeline checks `topicStyles["creative"]` → `"impressionist"`
3. Looks up `styles["impressionist"]` → the full style prompt
4. If style is `"abstract"`: uses `IMAGE_GEN_CMD` (no character)
5. If any other style: routes through **selfie** skill with reference image
6. If category not in `topicStyles`: falls back to `defaultStyle`

---

## Image Routing

After each dream, if image generation is configured:

1. Gets the style for this dream's category (from `topicStyles` or `defaultStyle`)
2. Builds a scene prompt from the dream text
3. Routes the image:
   - **Abstract style** → `IMAGE_GEN_CMD --prompt "..." --output path.webp` (no character)
   - **Character style + selfie skill** → `selfie.py --prompt "..." --style "..." --output path.webp`
   - **Character style, no selfie skill** → falls back to `IMAGE_GEN_CMD` without reference

Images save to `memory/dreams/images/YYYY-MM-DD-dreamN.webp`.

## Style Matching

| Dream mood | Style suggestion |
|---|---|
| Intimate, domestic, real | `film` — 35mm, natural grain, observational |
| Magical, symbolic, whimsical | `anime` — watercolour, painterly, warm |
| Dark, psychological, surreal | `noir` — high contrast, desaturated |
| Abstract, identity, philosophical | `abstract` — no character, pure emotion |

Configure `topicStyles` to auto-match categories to styles, or let `defaultStyle` handle everything.
