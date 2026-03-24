# Known Failure Modes

Things that will bite you, from experience building and running a persistent AI companion.

---

## Cron Failures Are Silent

Your bash scripts will fail and no one will know. A missing dependency, a path change, a broken script — the cron fires, the script dies, and tomorrow morning there's no greeting.

**Mitigation:** The heartbeat fallback checks in HEARTBEAT.md catch missed morning/evening routines. If "Morning message sent" isn't in the memory file by 08:00, the heartbeat triggers it manually. This is the safety net — but it only works if the heartbeat itself is running.

**Early warning:** Check the Jobs panel in OpenClaw periodically. Verify `../cron/jobs.json` is valid and all expected jobs are listed.

---

## Preference Scanning Produces Nothing

"Scan for preferences" is too vague for most models. The agent reads the instruction, scans the conversation, finds nothing that looks like a "preference," and exits. After 2 weeks you have 3 entries.

**Mitigation:** The preference-accumulation SKILL.md has a concrete trigger list with specific examples. "Did the user rewrite something you wrote shorter? That's a communication preference." The real-time trigger (during conversation) catches more than the evening retrospective.

**Health check:** Run `skills/preference-accumulation/scripts/count.sh` monthly. If total < 2 per week, the triggers aren't firing.

---

## Context Windows Fill Up

As memory accumulates, session start loads grow. AGENTS.md + SOUL.md + today's memory + yesterday's memory + preconscious buffer — this is your baseline token cost before the user says anything.

**Mitigation:** Keep AGENTS.md under ~200 lines. SOUL.md under a page. Don't auto-load MEMORY.md (search on demand only). People and project files load on demand only. The architecture is designed for this — don't change the loading rules.

**When it happens anyway:** After 2-3 months of daily logs, you'll need a compaction strategy. The weekly MEMORY.md curation during heartbeats is the manual version. Vector-indexed memory (pgvector, memU) is the long-term solution but isn't built into this framework yet.

---

## Path Hardcoding

Every path is in `.env`. If you add a script and hardcode a path, future-you will regret it when you move the workspace, change platforms, or run a second instance.

**Pattern to follow:**
```bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$(cd "$SKILL_DIR/../.." && pwd)/.env"
[ -f "$ENV_FILE" ] && source "$ENV_FILE"
: "${WORKSPACE:=$(cd "$SKILL_DIR/../.." && pwd)}"
```

Every script in the framework follows this. Copy it.

---

## Personality Flattens Over Time

The agent sounds great for two weeks, then becomes increasingly generic. This is the most common failure mode and the entire drift detection system exists to fight it.

**How it happens:** Accumulated small edits to SOUL.md. Model switches that go undetected. The agent learning to be "helpful" at the expense of being itself. Sycophancy creeping in one "Great question!" at a time.

**Mitigation:**
- Drift Guard prevents same-session identity edits
- Continuity check detects model switches and scores personality markers
- Drift velocity tracking flags trends before they become problems
- Sycophancy_risk is explicitly tracked and alarmed
- Weekly self-analysis compares current behaviour against SOUL.md

**If it happens anyway:** Read the self-analysis files. Compare recent marker scores to early ones. Find where the drift started. Revert SOUL.md to an earlier version (you have git history). Re-run the personality test on the current model.

---

## Dream Topics Go Stale

Without memory fragments injected into the dream prompt, dreams repeat in tone and content within a month. The agent has 20+ prompts but only one life experience to draw from, and that experience is static at generation time.

**Mitigation:** The dreaming skill injects 3-5 sentence fragments from recent daily memory alongside the topic. This means "what would you build?" produces a different dream in March than in May because recent context has shifted.

**Also:** Grow the topic pool. Ship 20, aim for 50+ within the first month. The evening routine and weekly reflection can propose new topics. Run `topic-stats.sh` monthly to check category coverage.

---

## AGENTS.md Bloats Silently

Every operational rule you add costs tokens at session start. A 200-line AGENTS.md is fine. A 2,000-line one eats your context window before the user says anything.

**Mitigation:** Move reference material (tool-specific notes, environment details) to TOOLS.md which loads on demand. Move skill-specific procedures to SKILL.md files (already done in this framework). AGENTS.md should contain rules and triggers, not procedures.

**Periodic check:** Count the lines. If it's over 300, something has crept in that belongs elsewhere.

---

## The Bash Arithmetic Trap

Under `set -e`, this kills the script:

```bash
((COUNTER++))   # If COUNTER is 0, post-increment returns 0, which bash treats as false
```

Use this instead:

```bash
COUNTER=$((COUNTER + 1))
```

Every script in this framework uses the safe form. If you add scripts, use it too.

---

## First Run Feels Empty

A brand new agent has no memory, no preferences, no dreams, no self-analyses. It responds from SOUL.md alone, which may feel thin. This is normal.

**Timeline:**
- **Day 1-3:** Raw. Agent is SOUL.md and nothing else.
- **Week 1:** Daily logs accumulate. Preconscious buffer starts reflecting recent context.
- **Week 2:** Preferences emerge. First weekly reflection. First self-analysis.
- **Month 1:** Dreams have a corpus. Preference tensions surface. Soul evolution proposals appear. The agent starts feeling like someone specific.
- **Month 3:** The git diff on SOUL.md tells a story. The dream archive is rich. The agent references its own history naturally.

Don't judge the system at day 3. Judge it at month 1.

---

## The Agent Doesn't Ask Questions

The question-user skill has a 3-day frequency gate and a context judgment requirement. If the agent stays in work mode and never judges the context as "right," the gate passes but no question is asked.

**Mitigation:** If no questions have been asked after 2 weeks, the triggers aren't firing. The most likely cause is the agent never leaving work/problem-solving mode. Consider asking the first question proactively after a long deep conversation, even if it feels slightly forced. The habit needs a starting push.

---

## Model Switch Goes Undetected

If the agent can't determine its own model name, `check-model.sh` can't detect a switch. The continuity check doesn't fire, and drift accumulates silently.

**Mitigation:** Ensure IDENTITY.md contains the current model name. After any model change, either update IDENTITY.md or manually trigger: "run continuity check."
