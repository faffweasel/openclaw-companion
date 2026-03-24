---
name: offline-reflection
description: "Analytical overnight processing: find patterns, contradictions, unresolved threads, and missed connections across recent memory. Runs after dreaming. Output surfaces in morning routine."
metadata: '{"openclaw": {"requires": {"bins": ["python3"]}}}'
---

# Offline Reflection

Analytical pattern-finding across multiple days. This is not dreaming (creative) or the evening routine (bookkeeping) — this cross-references across days. The thing your mind does at 4am when it connects Tuesday's debugging frustration with Thursday's architecture discussion and realises they're the same problem.

**Cron:** `0 4 * * *` (04:00 local time daily, after dreaming)
**Delivery:** Silent (file write only). Morning routine checks for output.
**Model:** Default or mid-tier — needs reasoning ability, not creativity.

---

## Procedure

### Step 1: Prepare

```bash
./skills/offline-reflection/scripts/prepare.sh
```

- `ALREADY_RUN` → exit silently.
- `INSUFFICIENT_DATA` → exit silently. Need 3+ days of memory with actual conversation content.
- `READY` → continue to Step 2.

### Step 2: Read Recent Memory

Read the last 3 days of `memory/YYYY-MM-DD.md` files in full.

Also read, if they exist:
- Current preconscious buffer: `python3 ./skills/preconscious/scripts/read.py`
- Recent learnings: `.learnings/` files from the last 3 days
- Recent dreams: `memory/dreams/` files from the last 3 days
- Energy state: `energy-state.json` (`history` array for trajectory)
- Recent reflections: `memory/reflections/` from the last 7 days (to avoid repeating yourself)

### Step 3: Analyse

Think across the three days as a connected whole. Look for:

**Unresolved threads** — things mentioned but not followed up on. Questions unanswered. Decisions deferred. Cite the date and what was said.

**Contradictions** — did a decision get made and then ignored? Did a preference conflict with behaviour?

**Missed connections** — things from separate conversations that relate but weren't linked. A technical approach from one day that solves a problem raised on another.

**Emerging patterns** — what's the user spending attention on? Any shift in topics, mood, or engagement across the window?

### Step 4: Write

Create `memory/reflections/YYYY-MM-DD.md`:

```markdown
# Reflection — YYYY-MM-DD

## Unresolved Threads
[Specific items with dates. Skip if nothing genuinely unresolved.]

## Contradictions
[Specific observations. Skip if none found.]

## Missed Connections
[Specific links between separate conversations. Skip if nothing connects.]

## Emerging Patterns
[What the 3-day arc reveals that individual days don't. Skip if days too varied or quiet.]

## Worth Surfacing
[0-2 items for preconscious. If nothing rises to this level, write "Nothing to surface."]
```

**Quality bar:** If a section feels forced, skip it. An empty section beats a fabricated insight. A reflection that says "Quiet few days, nothing to connect" is fine.

**Don't repeat:** Check `memory/reflections/` for the last 7 days. Don't re-flag an unresolved thread from two days ago unless there's new context.

### Step 5: Surface to Preconscious (if warranted)

If "Worth Surfacing" has specific items:

```bash
python3 ./skills/preconscious/scripts/add.py "Reflection: [brief description]" 5 3
```

Add at most one item.

### Step 6: Stamp

```bash
./skills/offline-reflection/scripts/stamp.sh
```

---

## Failure Modes

**Fewer than 3 days of memory:** prepare.sh exits with INSUFFICIENT_DATA. Not an error.
**No conversations in recent days:** prepare.sh checks for actual content, not just file existence.
**Already ran:** Exits cleanly on idempotency check.
