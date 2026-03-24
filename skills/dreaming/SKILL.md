---
name: dreaming
description: "Creative exploration during quiet hours. Generates 2-3 dreams per night using the configured dream model. Post-dream reflection (scoring) uses per-topic model routing via direct API call. Writes to memory/dreams/ for morning routine to read. Optional image generation."
metadata: '{"openclaw":{"emoji":"💭","requires":{"bins":["python3"]}}}'
---

# Dreaming

Creative, exploratory thinking during quiet hours. Not task-oriented work — freeform associative exploration that gets captured for later review.

**Cron:** `30 2 * * *` (2:30 AM local time)
**Dream model:** Set via `payload.model` in `../cron/jobs.json` (configured by setup.sh). The cron session runs as that model for dream generation.
**Reflection model:** Per-topic, configured in `dream-topics.json` as the first field of each topic string. `post-dream.py` calls the reflection model directly via its provider API (OpenRouter or Venice) to score the dream.
**Delivery:** Silent (file writes only). Morning routine reads dreams and incorporates mood into greeting.

---

## Setup

### 1. Install prerequisites

- **preconscious** skill (required — receives high-intensity dreams)

### 2. Edit dream config

The wizard copies `seed/dream-config.json` to `skills-data/dreaming/dream-config.json`. Edit it to configure topics, styles, and timing.

### 3. Dream images (optional)

If dream images are enabled (`dreamImages: true` in config), read `skills/dreaming/references/DREAM-IMAGES.md` for .env setup, style mapping, and image routing.

---

## Configuration

All config lives in `skills-data/dreaming/`. Three files:

| File | Purpose |
|---|---|
| `dream-config.json` | Models, styles, timing, image settings |
| `dream-topics.json` | Topics array + category definitions (grows over time) |
| `dream-state.json` | Runtime state (nightly count, last date) |

### Dream Model

The dream model is set in the OpenClaw cron job (`../cron/jobs.json`) via the `payload.model` field. setup.sh configures this during install. To change it, edit the "Dreaming" job in jobs.json directly.

The `dreamModel` field in `dream-config.json` is reference documentation only — the active model is always the one in jobs.json.

### Reflection Models

Post-dream reflection (intensity/mood/summary scoring) uses per-topic model routing. The `models` table in `dream-config.json` maps label → provider+model:

```json
"models": {
  "heretic": {"provider": "venice", "model": "heretic-r1"},
  "default": {"provider": "openrouter", "model": "google/gemini-2.5-flash"},
  "opus":    {"provider": "openrouter", "model": "anthropic/claude-opus-4"}
}
```

Supported providers: `openrouter` (requires `OPENROUTER_API_KEY`), `venice` (requires `VENICE_API_KEY`). Both use OpenAI-compatible chat completions. `post-dream.py` calls the provider directly via stdlib urllib — no extra dependencies.

### Topics (dream-topics.json)

Separate file so it can grow without burying the config. Format: `reflection_model:category:prompt`

```json
{
  "categories": {
    "future": "Forward-looking scenarios and possibilities",
    "creative": "Wild ideas, unconstrained thinking",
    "personal": "Identity, emotions, inner life"
  },
  "topics": [
    "default:future:What could this project become in 5 years?",
    "heretic:creative:A wild idea that might be crazy or brilliant",
    "opus:identity:Who are you becoming? What has shifted?"
  ]
}
```

The first field is the reflection model label (key in the `models` table). Dream generation always uses the model from jobs.json; only reflection routing varies per topic.

Categories are user-defined labels. Add domain-specific topics relevant to your agent's life. Aim for 20+ topics within the first month.

### Timing

```json
"quietStart": 1,
"quietEnd": 6,
"maxDreamsPerNight": 3,
"dreamChance": 1.0
```

Dreams only generate during quiet hours (1-6 AM by default). `dreamChance` is probability per attempt (1.0 = guaranteed if under nightly limit).

---

## Memory Sources

Each dream is seeded with memory fragments to ground the exploration:

| Source | What | Size |
|---|---|---|
| Yesterday's memory | Random 30-line window from `memory/YYYY-MM-DD.md` (yesterday). Random, not first-30, because the start is morning routine scaffolding. | 30 lines |
| Archival fragment | 5 lines from a random past memory file. Unexpected connections across time. | 5 lines |
| Preconscious buffer | Output of `preconscious/read.py` — what's actively top-of-mind. | Variable |
| Key memories | Random 15-line window from `memory/key-memories.md`. | 15 lines |

All sources are optional — if a file doesn't exist, that source is silently skipped.

---

## Dream Output Format

Written to `memory/dreams/YYYY-MM-DD.md`:

```markdown
# Dreams — 2026-03-22

## 02:34 — dream:Something from your soul, mixed with recent (personal)
**Intensity:** 6/7 | **Mood:** reflective

[Dream content — 300-500 words of freeform exploration]
```

Multiple dreams per night append to the same file. If the file already exists, suffixed files are created (`-a.md`, `-b.md`).

---

## Scripts

| Script | Purpose |
|---|---|
| `should-dream.py` | Quiet hours check, nightly limit, topic picker. Returns `{"category": "...", "prompt": "...", "reflectionModel": "..."}` or exits non-zero. |
| `post-dream.py` | Calls the reflection model to score the dream, writes intensity/mood header, adds high-intensity dreams to preconscious. Args: `--dream-file PATH --dream-index N --reflection-model LABEL --category CAT` |
