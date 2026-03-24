# Architecture

Four layers, each independent and portable.

---

## Layer Model

```
┌─────────────────────────────────────────────┐
│  Identity Layer (you write)                 │
│  SOUL.md  IDENTITY.md  USER.md              │
├─────────────────────────────────────────────┤
│  Operational Layer (framework provides)     │
│  AGENTS.md  HEARTBEAT.md  TOOLS.md  .env    │
├─────────────────────────────────────────────┤
│  Memory Layer (accumulates)                 │
│  memory/  MEMORY.md  .learnings/            │
├─────────────────────────────────────────────┤
│  Skill Layer (modular, opt-in)              │
│  skills/*/  +  skills-data/*/               │
└─────────────────────────────────────────────┘
```

Each layer can be replaced independently. Swap SOUL.md and you have a different agent. Swap the skill layer and you have different capabilities. Move to another framework and the identity, memory, and skills come with you — only the operational layer adapts.

---

## Identity Layer

Written by the user (or bootstrapped via interview). Loaded at the start of every session.

| File | Purpose | Loaded |
|---|---|---|
| SOUL.md | Personality, voice, values, boundaries | Every session |
| IDENTITY.md | Name, appearance, model routing table | Every session |
| USER.md | Context about the human — projects, preferences, location | Every session |

These files are the agent's identity. They're protected by the Drift Guard: proposed changes are queued overnight and applied next session only if they still feel right.

## Operational Layer

Provided by the framework. Defines how the agent uses everything else.

| File | Purpose |
|---|---|
| AGENTS.md | Session init, memory rules, safety, skill triggers. Generated from `AGENTS.md.template` by the wizard. |
| HEARTBEAT.md | What to check on heartbeat polls. Catches cron failures. |
| TOOLS.md | Agent's personal notes — API quirks, workarounds, learned knowledge. |
| .env | All paths, timezone, identifiers, feature flags. Sourced by every script. |

## Memory Layer

Accumulates over time. Daily files are raw notes; MEMORY.md is a lean index.

```
memory/
├── YYYY-MM-DD.md           # Daily conversation logs
├── key-memories.md         # Significant moments (searched on demand)
├── relationship.md         # Trust, depth, dynamics (updated weekly)
├── dreams/                 # Overnight creative output
│   └── images/             # Dream imagery
├── reflections/            # Overnight analytical output
├── people/                 # Per-person context files
├── projects/               # Per-project tracking
├── state-of-me/            # Weekly reflections
│   └── images/             # Visual journal
├── self-analysis/          # Personality snapshots
├── soul-proposals/         # Proposed SOUL.md changes
├── blog-proposals/         # Proposed blog topics
└── .learnings/             # Corrections and failures

MEMORY.md                   # Lean index — under 50 lines (auto-loaded every turn)
energy-state.json           # Energy/engagement level (read at session start)
location.json               # Current + home location for location-aware skills
```

**Loading rules:** OpenClaw auto-loads MEMORY.md, SOUL.md, USER.md, IDENTITY.md, and TOOLS.md every turn. Daily memory and preconscious load at session start via AGENTS.md instructions. Everything else loads on demand — when a person is mentioned, a project referenced, or older context needed.

**MEMORY.md** is a lightweight index: critical facts, pointers to people/project files, and a handful of lessons. Target under 50 lines. Rich context lives in `key-memories.md`, searched via grep when needed. This keeps the per-turn auto-load cost predictable.

## Skill Layer

Modular capabilities. Each skill is split across two directories:

```
skills/example-skill/          ← Git-managed framework code
├── SKILL.md                   # Documentation + procedure
├── manifest.json              # Metadata: type, dependencies, cron
├── scripts/                   # Bash/Python scripts
├── references/                # Static reference material (if any)
└── seed/                      # Initial data values (copied to skills-data/ by wizard)

skills-data/example-skill/     ← Gitignored runtime state
└── *.json / *.md              # Runtime data created from seed/
```

**`skills/`** is fully git-managed. Safe to overwrite on `git pull`. Contains only framework code: SKILL.md, manifest.json, scripts, static references, and seed templates.

**`skills-data/`** is entirely gitignored. Contains only runtime state: JSON files, accumulated preferences, published posts, analyses. Created by the wizard from seed values. Never touched by git.

This split means `git pull` updates framework code (procedures, scripts, bug fixes) without overwriting instance state (your preferences, your queue, your analyses).

Skills are either **core** (always installed) or **companion** (opt-in). The wizard installs selected skills and writes cron job definitions to `../cron/jobs.json` for OpenClaw to execute automatically.

---

## Data Flow

### Session Start

```
Agent wakes up
  → reads SOUL.md, IDENTITY.md, USER.md
  → reads today's + yesterday's memory
  → runs preconscious/read.py → gets top-of-mind items
  → runs continuity-check/check-model.sh → detects model switches
  → ready to respond
```

### During Conversation

```
User message arrives
  → agent responds (personality from SOUL.md, context from memory)
  → on correction → log to today's memory
  → on preference signal → preference-accumulation/add.sh
  → on carry-over thought → carry-over-queue/add.py
  → on preconscious item → preconscious/add.py
  → on emotional moment → preconscious/add.py (carries emotion across the day)
  → on question opportunity → check last-asked.py gate → trust calibration → ask
  → on long conversation (20+ exchanges) → checkpoint key points to today's memory
```

### End of Session

```
Agent writes to memory/YYYY-MM-DD.md:
  what was discussed, decisions, open questions, next steps
```

### Morning Cron (07:05)

```
morning-routine/prepare.sh
  → creates memory file
  → processes carry-over queue → appends to memory
  → decays preconscious buffer
Agent decays energy-state.json (time since last interaction)
Agent checks .learnings/ for stale high-priority items
Agent reads dreams → parses mood
Agent reads yesterday's structured mood from memory
Agent reads overnight reflections (if offline-reflection installed)
Agent composes greeting (influenced by dream mood, energy level, emotional carryover)
  → sends via Telegram
morning-routine/stamp.sh → marks complete
```

### Offline Reflection Cron (04:00)

```
offline-reflection/prepare.sh → idempotency + data sufficiency check
  → needs 3+ days of memory files with actual content
Agent reads last 3 days of memory, dreams, learnings, preconscious, energy history
Agent analyses for: unresolved threads, contradictions, missed connections, emerging patterns
Agent writes to memory/reflections/YYYY-MM-DD.md
Agent surfaces 0-1 items to preconscious (if genuinely worth mentioning)
offline-reflection/stamp.sh → marks complete
```

### Evening Cron (23:55)

```
evening-routine/prepare.sh → idempotency check
Agent summarizes conversations → writes to memory
Agent captures structured mood (state, trend, note)
Agent updates energy-state.json (recharge or decay based on conversation quality)
Agent scans for entity mentions → updates people/project files
Agent reviews carry-over queue
Agent updates preconscious buffer
Agent scans for preferences → preference-accumulation/add.sh
Agent scans for learnings → writes to .learnings/
Agent updates memory search index (if installed)
evening-routine/stamp.sh → marks complete
```

### Weekly Cron (Sunday 08:00)

```
weekly-state-of-me/generate.sh → creates scaffold with stats
Agent reads the week's memory, dreams, preferences, energy history, reflections
Agent fills: self-assessment, what's changing
Agent fills: relationship assessment → updates memory/relationship.md
Agent reviews previous proposal impact (before/after scoring if model-personality-test installed)
Agent checks soul proposal velocity (3/month caution, 4+ stop)
Agent writes soul evolution proposal (if warranted and velocity allows) → notifies user
Agent runs preference health check
Agent generates visual journal image (if configured)
Agent chains to self-analysis (if installed)
```

### Dream Cron (02:30)

```
OpenClaw starts isolated session as the dream model (set in jobs.json payload.model)
Agent follows skills/dreaming/SKILL.md:
  → for each dream (up to maxDreamsPerNight):
      → should-dream.py → quiet hours? under limit? → picks topic
      → gathers memory fragments (yesterday + random archival)
      → generates dream text natively (agent IS the dream model)
      → writes to memory/dreams/YYYY-MM-DD.md
      → scores intensity (1-7) + mood
      → if intensity ≥ 5 → preconscious/add.py
      → if IMAGE_EDIT_CMD set → character image with reference
      → if IMAGE_GEN_CMD set (abstract style) → abstract image
```

---

## .env — Single Source of Truth for Configuration

Every script sources `.env` for paths and feature flags. Nothing is hardcoded.

```bash
WORKSPACE, MEMORY_DIR, SKILLS_DIR, DATA_DIR   # Paths
TZ                                             # Timezone
AGENT_NAME, USER_NAME                          # Identity
IMAGE_GEN_CMD                                  # Image generation (see docs/image-generation-interface.md)
IMAGE_EDIT_CMD                                 # Reference-based image editing (character consistency)
COMPANION_REFERENCE_PORTRAIT                   # Path to portrait reference image (face/shoulders)
COMPANION_REFERENCE_BODY                       # Path to body reference image (full/half body)
BLOG_CHECK_DAYS                                # Blog proposal frequency
```

Move the workspace → update WORKSPACE in `.env` → everything follows.

### API Keys

API keys that can spend money (VENICE_API_KEY, OPENROUTER_API_KEY, etc.) must **not** go in `.env` — that file lives in the workspace and is readable by the agent.

Set them via OpenClaw's environment configuration instead. Scripts read these via `os.environ` / `$ENV_VAR`.

**Rule of thumb:** If it's a path, a feature flag, or a non-secret identifier → `.env`. If it's an API key or token → OpenClaw environment config.

### Script Preamble

Every script resolves data paths via `DATA_DIR`:

```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="$(basename "$SKILL_DIR")"
WORKSPACE="$(cd "$SKILL_DIR/../.." && pwd)"
ENV_FILE="${WORKSPACE}/.env"
[ -f "$ENV_FILE" ] && source "$ENV_FILE"

: "${DATA_DIR:=${WORKSPACE}/skills-data}"
SKILL_DATA="${DATA_DIR}/${SKILL_NAME}"
```

Then reference `$SKILL_DATA/buffer.json` instead of `$SKILL_DIR/data/buffer.json`. The fallback default means scripts still work without .env — they just assume `skills-data/` is at the workspace root.

---

## Cron Pattern

Cron jobs are defined in `../cron/jobs.json` (one level up from the workspace). The setup wizard generates this file automatically with all selected skills' schedules, using the OpenClaw job format. OpenClaw reads it directly — no manual registration or agent bootstrapping needed.

Cron jobs fire one-line messages that reference SKILL.md:

```
"Run the morning routine. Follow skills/morning-routine/SKILL.md step by step."
```

The agent reads the SKILL.md and executes the procedure. Update the procedure by editing SKILL.md — no need to re-register the cron. The mechanical parts (file creation, idempotency, script calls) are handled by scripts. The creative parts (composing greetings, writing summaries, scoring moods) are handled by the agent following instructions.

---

## Skill Manifests

Each skill declares metadata:

```json
{
  "name": "morning-routine",
  "type": "core",
  "dependencies": ["python3"],
  "cron": {
    "schedule": "5 7 * * *",
    "message": "Run the morning routine. Follow skills/morning-routine/SKILL.md step by step."
  },
  "requires_skills": ["carry-over-queue", "preconscious"],
  "optional": false
}
```

The wizard reads manifests to check dependencies. Type values: `core` (always installed), `companion` (opt-in).

---

## Framework Agnosticism

This architecture requires four things from the framework:
1. The agent can read and write files
2. You can schedule background jobs (cron)
3. The agent loads AGENTS.md and identity files at session start
4. You can route different tasks to different models (helpful, not essential)

OpenClaw or any other framework with file access and cron scheduling — the patterns are the same. AGENTS.md is the portability layer.
