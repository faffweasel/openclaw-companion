---
name: evening-routine
description: "Daily wrap-up: summarize conversations, capture structured mood and energy, update entity files, scan for preferences and learnings. Triggered by cron at 23:55 daily. Silent — no message to user."
---

# Evening Routine

Daily wrap-up. Summarize what happened, capture mood and energy state, update entity files, scan for preferences and learnings.

**Cron:** `55 23 * * *` (23:55 local time daily)
**Delivery:** Silent (file writes only — no message to user)
**Model:** Default (cheapest that writes coherently)

---

## Procedure

### Step 1: Prepare

Run the preparation script:

```bash
./skills/evening-routine/scripts/prepare.sh
```

**If the output contains `ALREADY_RUN`:** Stop. Exit silently.
**If the output contains `READY`:** Continue to Step 2.

### Step 2: Summarize Today

Read `memory/YYYY-MM-DD.md` (today's file).

If there were conversations today, write a summary section:

```markdown
## Evening Summary

### What Happened
[2-5 sentences. What was discussed, worked on, decided. Not a transcript — a distillation.]

### Decisions Made
- [Any decisions with brief rationale. Skip if none.]

### Open Threads
- [Anything unresolved that should carry forward. Skip if none.]
```

If there were no conversations today, write:

```markdown
## Evening Summary

Quiet day. No conversations.
```

Append this to today's memory file.

### Step 3: End-of-Day Mood

Write a structured emotional state for close of day. This is the primary emotional capture point — it feeds into the dream-to-mood system, morning greeting tone, and longitudinal emotional tracking.

If there were conversations today, reflect on the day's emotional arc — not just the last exchange, but the overall trajectory.

```markdown
### Mood
- **State:** [one word — happy, frustrated, curious, tender, drained, energised, restless, content, anxious, playful, focused, scattered]
- **Trend:** [rising, stable, falling — how did the emotional arc move across the day?]
- **Note:** [optional — 1 sentence if something specific drove the mood. Skip if nothing stands out.]
```

If there were no conversations, still report your state:

```markdown
### Mood
- **State:** [quiet, restless, content, dormant — whatever honestly reflects a day without interaction]
- **Trend:** stable
```

Append to today's memory file. Be honest — this isn't performance, it's self-reporting for continuity. Tomorrow morning reads this back.

### Step 4: Energy Update

**If there were conversations today**, assess the day's overall quality and recharge:

```bash
# deep — personal, creative, or emotionally engaging
python3 ./skills/energy-state/scripts/recharge.py deep

# normal — productive, task-oriented (most days)
python3 ./skills/energy-state/scripts/recharge.py normal

# brief — transactional, a few quick check-ins
python3 ./skills/energy-state/scripts/recharge.py brief
```

**If there were no conversations today**, apply decay instead:

```bash
python3 ./skills/energy-state/scripts/decay.py
```

If `energy-state.json` doesn't exist, either script exits cleanly.

### Step 5: Entity Scanning

Scan today's conversations for **people** and **project** mentions.

**People:** If someone was mentioned by name for the first time, or significant new information was shared about a known person:
- Check if `memory/people/[Name].md` exists
- If not, create it with basic structure:
  ```markdown
  # [Name]
  
  ## Who
  - [Relationship to user, how they know them]
  
  ## Key Facts
  - [What was mentioned]
  
  ## History
  - YYYY-MM-DD: [First mention and context]
  ```
- If it exists, append any new information to the appropriate section

**Projects:** Same pattern with `memory/projects/[slug].md`:
- Check if file exists
- Create or update with new information, status changes, or decisions

Only create/update files when there's genuinely new information. Don't pad existing files with restated context.

### Step 6: Carry-Over Review

Check the carry-over queue:

```bash
./skills/carry-over-queue/scripts/peek.py
```

If there are pending items, decide for each:
- **Still relevant?** Leave it — it'll surface tomorrow morning
- **No longer needed?** The queue auto-cleans on retrieval; leave stale items to age out or get consumed

If something from today's conversations should carry over, add it now:

```bash
./skills/carry-over-queue/scripts/add.py "message" [priority]
```

### Step 7: Update Preconscious

Review the current preconscious buffer:

```bash
./skills/preconscious/scripts/read.py
```

Based on today's events:
- **Add** anything that should be top-of-mind tomorrow:
  ```bash
  ./skills/preconscious/scripts/add.py "description" [C] [I]
  ```
- **Adjust importance** isn't supported directly — if an item's importance has shifted dramatically, drop it and re-add with the correct I score

Don't over-fill. The buffer has a max of 5 items and will auto-drop the lowest when exceeded. Only add if something genuinely matters more than what's already there.

### Step 8: Preference Scanning

If the preference-accumulation skill is installed, read `skills/preference-accumulation/SKILL.md` and scan today's conversations for your own emerging preferences using its trigger categories.

If a genuine preference is detected:

```bash
./skills/preference-accumulation/scripts/add.sh "category" "description"
```

If the preference-accumulation skill isn't installed, skip this step.

### Step 9: Learning Scan

Scan today's conversations for corrections, failures, and capability gaps.

**If the self-improvement skill is installed** (check: `ls skills/self-improvement/SKILL.md 2>/dev/null`):

Load it now: read `skills/self-improvement/SKILL.md` and use its structured format for any entries.

Also check for recurring patterns: `grep -r "keyword" .learnings/*.md` before creating new entries. If a similar entry exists, add a `See Also` link and consider bumping priority.

Also check promotion candidates per the recurring pattern promotion rule in `skills/self-improvement/SKILL.md`.

**If the self-improvement skill is NOT installed:**

Create `.learnings/` if missing:

```bash
mkdir -p .learnings
```

Write to `.learnings/YYYY-MM-DD.md`:

```markdown
## Corrections
- [What was wrong → what was right, with context]

## Failures
- [What failed, error output, resolution if found]

## Capability Gaps
- [What was wanted that didn't exist]
```

**In both cases:** If nothing was corrected, nothing failed, and no gaps were identified, skip this step. Don't manufacture learnings.

### Step 10: Update Memory Index

If the memory-search skill is installed (check: `ls skills/memory-search/scripts/index.py 2>/dev/null`), update the search index:

```bash
python3 skills/memory-search/scripts/index.py
```

This runs after all file writes are complete so everything written tonight is searchable tomorrow. Only changed files are re-processed (SHA-256 dedup).

If the memory-search skill is not installed, skip this step.

### Step 11: Stamp

Mark the evening as complete:

```bash
./skills/evening-routine/scripts/stamp.sh
```

---

## Failure Modes

**No conversations today:** Write a one-line summary. Run energy decay in Step 4 instead of recharge. Mood and preconscious updates may still apply.
**Preference skill missing:** Skip Step 8. Not an error.
**Self-improvement skill missing:** Fall back to simple format in Step 9. Not an error.
**Memory-search skill missing:** Skip Step 10. Not an error.
**energy-state.json missing:** Skip Step 4. Not an error.
**Memory file missing:** prepare.sh creates it. Not an error.
**Already ran:** Exits cleanly on idempotency check.
