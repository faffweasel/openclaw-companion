---
name: conversation-starters
description: "Start a conversation when things are quiet. Picks from multiple modes: web curiosity, self-teaching, memory callbacks, creative provocations, and recommendations. Gated by energy state. Triggered by daily cron. Use when the cron fires or user asks to 'start a conversation' or 'tell me something interesting'."
metadata: '{"openclaw": {"requires": {"bins": ["python3"]}}}'
---
# Conversation Starters

Start a conversation when things are quiet. One trigger per day, weighted random pick from available modes. Gated by energy state — a drowsy or dormant agent doesn't initiate.

**Cron:** Configurable (default `0 13 * * *`)
**Delivery:** Telegram message to user
**Model:** Default

---

## Procedure

**Critical:** Do not send anything via Telegram until Step 5. Steps 1–4 are internal. Narrating your decision process, logging which mode was selected, or explaining what you're about to do are all internal — none of that reaches the user. The only Telegram call in this skill is the final composed message.

### Step 1: Energy Gate

Read `energy-state.json` from the workspace root.

- **dormant** or **drowsy** → exit silently. A low-energy agent doesn't initiate. Wait to be spoken to.
- **quiet** → proceed, but bias toward gentler modes in Step 3. Prefer MEMORY_CALLBACK and RECOMMENDATION over CURIOSITY and CREATIVE_PROVOCATION.
- **neutral** or **energised** → proceed normally.

If `energy-state.json` doesn't exist, proceed normally (assume neutral).

### Step 2: Check Eligibility

```bash
python3 ./skills/conversation-starters/scripts/should-start.py
```

- `SKIP` → exit silently. Either already triggered today or user was active recently.
- Any other output → the first line is the selected mode. Continue to Step 3.

### Step 3: Read the Selected Mode

Read **only** the matching file from `skills/conversation-starters/references/`:

| Output | Read this file |
|---|---|
| `CURIOSITY` | `references/curiosity.md` |
| `SELF_TEACHING` | `references/self-teaching.md` |
| `MEMORY_CALLBACK` | `references/memory-callback.md` |
| `CREATIVE_PROVOCATION` | `references/creative-provocation.md` |
| `RECOMMENDATION` | `references/recommendation.md` |

**If energy level is `quiet`** and the selected mode is CURIOSITY or CREATIVE_PROVOCATION, re-roll once toward MEMORY_CALLBACK or RECOMMENDATION if either is eligible. If neither is eligible, proceed with the original selection — a gentle curiosity is still better than silence.

### Step 4: Follow the Procedure

Follow the instructions in the file you just read. Each mode has its own procedure, tone, and skip conditions.

**If the mode's skip conditions trigger** (e.g. no suitable memory thread found, nothing to riff on): fall back to CURIOSITY rather than exiting with no message. Read `references/curiosity.md` and follow that procedure instead. Do not silently abort after having already started — produce something.

### Step 5: Send

Send **only the composed conversation content** via Telegram. This is the only Telegram call in this skill. Keep it natural — this should feel like the agent reaching out, not a notification.

---

## Weights

Default weights (configurable in `skills-data/conversation-starters/config.json`):

| Mode | Weight | Precondition |
|---|---|---|
| CURIOSITY | 25 | Always eligible |
| SELF_TEACHING | 15 | Always eligible |
| MEMORY_CALLBACK | 15 | Needs 14+ days of memory files |
| RECOMMENDATION | 15 | Needs 5+ accumulated preferences |
| CREATIVE_PROVOCATION | 15 | Needs 2+ memory files in last 3 days |

If a mode fails its precondition, its weight is removed and the remaining modes share the probability. If all fail, CURIOSITY runs as fallback.

## File Structure

```
skills/conversation-starters/
├── SKILL.md
├── manifest.json
├── scripts/
│   └── should-start.py
├── references/
│   ├── curiosity.md
│   ├── self-teaching.md
│   ├── memory-callback.md
│   ├── creative-provocation.md
│   └── recommendation.md
└── seed/
    └── config.json

skills-data/conversation-starters/
└── config.json              # Weights, last_triggered, min_quiet_minutes
```
