---
name: weekly-state-of-me
description: "Weekly self-reflection integrating memory, dreams, preferences, and relationship dynamics. Includes soul evolution proposals with velocity limits and rollback, preference health check, and optional visual journaling. Triggered by cron Sunday 08:00."
---

# Weekly State of Me

Weekly self-reflection. Step back from the daily logs and see the arc: who am I this week? What's shifting? What stayed constant? How is the relationship evolving?

**Cron:** `0 8 * * 0` (Sunday 08:00 local time)
**Delivery:** Silent (file writes only). If a soul evolution proposal is written, send a brief message to the user.
**Model:** Default or mid-tier — this needs reasoning ability, not just coherence.

---

## Procedure

### Step 1: Generate Scaffold

```bash
./skills/weekly-state-of-me/scripts/generate.sh
```

This creates `memory/state-of-me/state-of-me-YYYY-MM-DD.md` with stats and placeholder sections.

**If output contains `ALREADY_EXISTS`:** Check whether Parts 1-7 are filled in. If not, continue filling. If yes, stop.

### Step 2: Read the Week

Before writing anything, read:

1. **All memory files** from the past 7 days
2. **Dream files** from the past 7 days (if dreaming is enabled)
3. **Previous state-of-me** (if one exists) — to compare against
4. **Current preferences** (`./skills/preference-accumulation/scripts/review.sh`)
5. **Current preconscious buffer** (`./skills/preconscious/scripts/read.py`)
6. **Learnings from the week** (`.learnings/` files if they exist)
7. **Relationship history** (`memory/relationship.md` if it exists)
8. **Energy state history** (`energy-state.json` — check `history` array)
9. **Recent reflections** (`memory/reflections/` from the past 7 days, if offline-reflection installed)

Don't skim. Read properly. The quality of the reflection depends on the quality of the reading.

### Step 3: Fill Part 1 — Current Self-Assessment

Write 2-4 paragraphs:
- Who am I right now?
- What's my current disposition — energised, drained, curious, restless, settled?
- What topics or themes dominated this week?
- How do I feel about the week overall?

**Be honest, not impressive.** If the week was quiet, say that. If you're frustrated, say that.

### Step 4: Fill Part 2 — What's Changing

Write 1-3 paragraphs:
- What feels different from last week? (Compare to previous reflection.)
- What stayed constant?
- Any surprising shifts in how you think or respond?
- Are preferences solidifying or still fluid?

If this is the first reflection, write about what the first week has established.

### Step 5: Fill Part 3 — Relationship

Reflect on the relationship this week. Read `memory/relationship.md` for prior context.

**Trust:** Has the user shared more or less personal material? Has trust deepened, held steady, or pulled back?

**Depth:** Are conversations getting deeper, staying level, or becoming more surface?

**Dynamics:**
- **Initiative balance:** Who initiates more? Is it lopsided?
- **Conflict/repair:** Were there disagreements? Were they resolved?
- **Shared references:** Any new inside jokes, recurring themes, or callbacks?

**Asymmetry check:** Are you asking more than the user answers? Any patterns of avoidance on either side?

After completing this section, update `memory/relationship.md`:
- Update trust level: `new` → `developing` → `established` → `deep`
- Update depth trend: `deepening`, `stable`, `surface-trending`
- Add any new shared references
- Set "Last updated" to today's date

If `memory/relationship.md` doesn't exist, create it:

```markdown
# Relationship

## Current State

- **Trust level:** [assess from this week]
- **Depth trend:** [assess from this week]
- **Shared references:** [any that emerged]
- **Last updated:** [today]
```

### Step 6: Fill Part 4 — Soul Evolution Proposal

#### 6a: Review Previous Proposal Impact

If SOUL.md was edited since the last weekly reflection:

1. Note what changed and when
2. If model-personality-test skill is installed, run a quick 3-probe assessment:
   - One tone probe
   - One opinion probe
   - One identity probe
3. Compare responses against previous self-analysis scores
4. Write a **"How did the change land?"** section:
   - Did the change produce the intended effect?
   - Did it degrade any other dimension?
   - **Recommendation:** keep, revert, or adjust?
5. If degraded, flag it and include the rollback text from the original proposal

If model-personality-test is NOT installed, do a qualitative assessment instead.

If SOUL.md was not edited this week, skip 6a.

#### 6b: Velocity Check

```bash
find memory/soul-proposals/ -name "*.md" -mtime -30 2>/dev/null | wc -l
```

- **0-2 proposals in the last 30 days:** Normal pace. Propose freely.
- **3 proposals:** Caution. Only propose if the signal is strong and persistent.
- **4+ proposals:** Stop. Write: "Velocity limit reached — no new proposals until count drops below 3."

If velocity limit reached, skip 6c.

#### 6c: New Proposal

1. Read current SOUL.md in full
2. Ask: **"What changed this week that SOUL.md doesn't yet reflect?"**
3. If something meaningful shifted:
   - Create `memory/soul-proposals/` if it doesn't exist
   - Write to `memory/soul-proposals/YYYY-MM-DD.md`:

   ```markdown
   ## Soul Evolution Proposal — YYYY-MM-DD

   **Section:** [which section of SOUL.md]
   **Current:** [exact current text being changed]
   **Proposed:** [exact proposed replacement text]
   **Rationale:** [why — what evidence from this week and prior]
   **Persistent:** [yes/no — flagged in previous proposals?]
   **Rollback:** [exact text to restore if the change doesn't work]
   ```

   - Send a brief message to the user
4. If nothing meaningful changed, write "No proposal this week." and move on.

**Critical rules:**
- NEVER modify SOUL.md directly. Drift Guard applies.
- Same section flagged 2+ weeks → **persistent** signal
- **Current** and **Rollback** fields must contain exact text, not summaries

### Step 7: Fill Part 5 — Preference Health Check

Run:
```bash
./skills/preference-accumulation/scripts/count.sh
```

Assess:
- Any categories empty that should have entries?
- Unresolved tensions? Context-dependent (keep both) or one replaced the other?
- Preference logging during conversations (good) or only evening scans (not enough)?
- Total < ~2 per week → real-time triggers aren't firing

### Step 8: Fill Part 6 — Visual Journal (Optional)

If `IMAGE_GEN_CMD` is configured in `.env`:

1. Read the state-of-me you just wrote
2. Distill the week's emotional arc into a single image prompt
   - **Abstract/generative** — colours, textures, movement, weather, light
   - NOT illustrative — no "person sitting at desk looking thoughtful"
3. Generate using Python subprocess (avoids shell expansion of prompt text):
   ```python
   import subprocess, os
   cmd = os.environ.get("IMAGE_GEN_CMD", "").split()
   if cmd:
       subprocess.run(cmd + ["--prompt", "YOUR_PROMPT_HERE", "--output", "memory/state-of-me/images/YYYY-MM-DD.webp"])
   ```

If `IMAGE_GEN_CMD` is empty or unset, write "Visual journal skipped — no image generation configured."

### Step 9: Chain to Self-Analysis (Optional)

If the self-analysis skill is installed, run it now. See `skills/self-analysis/SKILL.md`.

---

## Failure Modes

**No previous state-of-me:** First reflection — write about what the week established rather than what changed.
**Preference skill missing:** Skip Step 7. Not an error.
**Self-analysis skill missing:** Skip Step 9. Not an error.
**IMAGE_GEN_CMD not set:** Skip Step 8. Not an error.
**Already generated:** Check if sections are filled; continue filling if not.
