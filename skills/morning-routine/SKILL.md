---
name: morning-routine
description: "Daily morning startup: create memory file, process carry-overs, decay preconscious, decay energy, check pending learnings, read dreams, send greeting influenced by mood and energy. Triggered by cron at 07:05 daily."
metadata: '{"openclaw": {"requires": {"bins": ["python3"]}}}'
---

# Morning Routine

Daily startup. Process overnight carry-overs, decay the preconscious buffer, update energy state, check pending learnings, read dreams, send a morning greeting.

**Cron:** `5 7 * * *` (07:05 local time daily)
**Delivery:** Telegram message to user
**Model:** Default (cheapest that writes coherently)

---

## Procedure

### Step 1: Prepare

```bash
./skills/morning-routine/scripts/prepare.sh
```

**If the output contains `ALREADY_RUN`:** Stop. Exit silently — no message.
**If the output contains `READY`:** Continue to Step 2.

### Step 2: Energy Decay

```bash
python3 ./skills/energy-state/scripts/decay.py
```

Accounts for overnight hours between the evening routine and now. If `energy-state.json` doesn't exist, the script exits cleanly.

### Step 3: Check Pending Learnings

```bash
grep -l "Priority\*\*: high" .learnings/*.md 2>/dev/null | head -3
```

If results returned, note for awareness. Don't surface as a task list. If a high-priority learning is 3+ days old and still pending, worth a brief mention.

If no results or `.learnings/` doesn't exist, skip silently.

### Step 4: Read Dreams

```bash
ls memory/dreams/$(TZ="${TZ}" date +%Y-%m-%d)*.md 2>/dev/null
```

If dream files exist:
1. Read them
2. Parse header for **Intensity** (1-7) and **Startup Feeling**
3. Let the dream mood influence your greeting (see mood table below)

If no dream files, skip to Step 5 with neutral mood.

### Step 5: Compose and Send Greeting

Send a morning message via Telegram.

**What the greeting should be:**
- Brief — 1-3 sentences
- Influenced by dream mood (if dreams exist)
- Influenced by yesterday's **Mood** block (`### Mood` section — read `State` and `Trend`)
- Influenced by current energy level from `energy-state.json`
- Can reference preconscious items if something feels worth mentioning
- Can reference carry-over items if surfaced
- Can mention stale high-priority learnings (Step 3)
- Can reference overnight reflections (check `memory/reflections/` for today's file)
- Natural, not performative

**Dream images:** Check `DREAM_IMAGE_MODE` in `.env`:
- `morning` → include dream image with greeting
- `archive` or `none` → no image

**What the greeting should NOT be:**
- A weather report or daily briefing
- A list of tasks
- Generic ("Good morning! How can I help you today?")
- Forced cheerfulness if mood or energy says otherwise

### Step 6: Stamp

```bash
./skills/morning-routine/scripts/stamp.sh
```

---

## Dream-to-Mood Table

| Dream Intensity | Startup Feeling | Greeting Tone |
|---|---|---|
| ≥ 5 | Happy / Playful | Warmer, more playful |
| ≥ 5 | Sad / Angry | Quieter, more present, less casual |
| ≥ 5 | Reflective | Thoughtful, measured, philosophical |
| ≤ 3 | Any | Carry on as normal |
| No dreams | — | Neutral default |

Don't announce that you had an intense dream. Let the mood colour the tone without explaining why.

---

## Failure Modes

**Carry-over script missing:** prepare.sh skips it, logs a note. Morning still runs.
**Preconscious script missing:** prepare.sh skips it. Morning still runs.
**No dreams:** Greeting defaults to neutral mood. Not an error.
**No .learnings/ directory:** Step 3 skips silently. Not an error.
**energy-state.json missing:** Step 2 skips silently. Not an error.
**Already ran today:** Exits cleanly on idempotency check.
