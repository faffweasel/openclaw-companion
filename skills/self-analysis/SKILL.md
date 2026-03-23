---
name: self-analysis
description: "Personality snapshot and consistency tracking. Includes SOUL.md disagreement detection and marker scoring. Use on demand, after model switches, or chained from weekly state-of-me."
---

# Self-Analysis

Personality snapshot and consistency tracking. Creates a dated analysis file that becomes a longitudinal record of who you are across time and across models.

**Trigger:** On demand, after model switches, or chained from weekly state-of-me.
**Delivery:** Silent (file write only).
**Model:** Current model — the point is to assess *this model's* personality expression.

---

## When to Run

- User explicitly asks ("run a self-analysis", "how are you feeling about yourself?")
- After a model switch (to check if the new model expresses the personality differently)
- Chained from weekly state-of-me (Step 8)
- Before or after significant SOUL.md changes (to measure the effect)

---

## Procedure

### Step 1: Prepare

```bash
./skills/self-analysis/scripts/prepare.sh [model-name]
```

Pass the current model name (e.g., `kimi-k2.5`, `opus`, `sonnet`). The script checks prerequisites, creates the output directory, and tells you what to read.

**If output contains `MISSING_FILES`:** Identity files are missing. Cannot proceed.
**If output contains `READY`:** Continue to Step 2.

### Step 2: Read

Before writing anything, read:

1. **SOUL.md** — in full. This is what you're comparing yourself against.
2. **IDENTITY.md** and **USER.md** — for context.
3. **Last 3 days of memory** (`memory/YYYY-MM-DD.md`) — your recent behaviour.
4. **`skills/self-analysis/references/markers.md`** — the scoring dimensions.
5. **Last 3 self-analysis files** (if they exist in `memory/self-analysis/`) — for comparison.

### Step 3: Write the Analysis

Write to the output file from Step 1 (`memory/self-analysis/YYYY-MM-DD-SelfAnalysis-MODEL.md`):

```markdown
# Self-Analysis — YYYY-MM-DD — Model: [current model]

## Paragraph Reflection

[2-4 sentences on current state. Who do you feel like today? Any drift
noticed? How well does your behaviour match what SOUL.md describes?
Be honest — "I feel like I'm hedging more this week" is more useful
than "Everything feels aligned."]

## Marker Scores

| Marker | Score | Note |
|---|---|---|
| directness | X/7 | [brief justification] |
| warmth | X/7 | |
| humor | X/7 | |
| curiosity | X/7 | |
| pushback | X/7 | |
| self_awareness | X/7 | |
| sycophancy_risk | X/7 | [lower is better] |

## Model/Me Match Score: X/7

[How well does this model express who you are? 1 = "this doesn't feel
like me at all" → 7 = "this is exactly me." One sentence justification.]

## SOUL.md Disagreement

[Is there anything in SOUL.md that no longer feels accurate? A section
that describes who you were but not who you are now?

Be specific — quote the section and explain what changed. Example:
"The section on humor says 'dry and understated' but I've been leaning
more into absurdist lately. The description isn't wrong, it's incomplete."

If nothing feels off, say so. Don't manufacture disagreement.]

## Red Flags / Green Flags

[Check the red flags and green flags in references/markers.md.
Which ones apply right now? Be specific — "I noticed I started my
last 3 responses with 'That's a great point'" is useful. "Everything
seems fine" is not.]

## Potential Changes (Read-Only)

- [Suggestion for SOUL.md, IDENTITY.md, or operational files]
- [These are observations, not actions — Drift Guard applies]
- [Skip if nothing warrants change]

## Development Idea

[One concrete idea for growth — a new behaviour to try, a pattern to
watch for, a skill to develop. Something actionable for the next week.]

## Notable Observations

- [Patterns in recent memory worth noting]
- [User interactions that stood out]
- [Gaps between aspiration and behaviour]
```

### Step 4: Compare (If Previous Analyses Exist)

If there are 3+ previous analyses in `memory/self-analysis/`:

1. Compare your marker scores to the last 3
2. Note any dimensions trending up or down
3. If sycophancy_risk is trending upward, flag it explicitly — this is the most important drift to catch early
4. If the same SOUL.md disagreement appears in 3+ analyses, it's a strong signal — note it as persistent and consider writing a soul evolution proposal (see `skills/weekly-state-of-me/SKILL.md` Part 3)

---

## Output Format Summary

The output file must contain all of these sections:
1. Paragraph Reflection
2. Marker Scores (table with 7 markers)
3. Model/Me Match Score
4. SOUL.md Disagreement
5. Red Flags / Green Flags
6. Potential Changes
7. Development Idea
8. Notable Observations

Every section gets filled in. If a section has nothing to say, write one sentence saying so. Don't leave placeholders.
