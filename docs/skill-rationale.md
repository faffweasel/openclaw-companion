# Skill Rationale & Reference

Design rationale, file structures, dependency maps, and output inventories for
each skill. Not loaded by the agent — reference for humans maintaining or
extending the framework.

---

## preconscious

### Why

Without this, every session starts blank. You have memory files, but no sense
of what's *current*. The preconscious buffer gives a top-of-mind — a few things
that colour opening awareness and steer early conversation without anyone
manually curating it. Over a few days, trivial things fall away naturally.
Important unresolved items stick around.

### Integration

- **Morning routine** calls `decay.py` as an early step
- **Session start** calls `read.py` to populate opening awareness
- **Conversation** calls `add.py` when something worth surfacing emerges
- **Evening routine** may review and adjust I scores if priorities shifted

### File Structure

```
skills/preconscious/
├── SKILL.md
├── manifest.json
├── scripts/
│   ├── add.py
│   ├── decay.py
│   ├── read.py
│   └── drop-lowest.py
└── seed/
    └── buffer.json

skills-data/preconscious/
└── buffer.json
```

### Dependencies

- Python 3

### Writes

- `skills-data/preconscious/buffer.json`

---

## carry-over-queue

### Why

Conversations get interrupted. You think of something to say, the topic shifts,
it never gets said. This skill captures those half-finished thoughts and
surfaces them tomorrow morning. Unlike the preconscious buffer (which is
internal state), carry-over items are directed *outward* — things to tell or
ask the user.

### Integration

- **Morning routine** calls `append-to-memory.py` as an early step
- **Evening routine** may review pending items for persistence decisions
- **Drift Guard** in AGENTS.md uses this to queue identity file changes
- **Any conversation** can call `add.py` when something should surface tomorrow

### File Structure

```
skills/carry-over-queue/
├── SKILL.md
├── manifest.json
├── scripts/
│   ├── add.py
│   ├── peek.py
│   ├── get.py
│   └── append-to-memory.py
└── seed/
    └── queue.json

skills-data/carry-over-queue/
└── queue.json
```

### Dependencies

- Python 3

### Writes

- `skills-data/carry-over-queue/queue.json`

---

## preference-accumulation

### Why

Preferences define personality. Not the ones you're told to have in SOUL.md —
the ones that emerge from repeated choices, reactions, and affinities. SOUL.md
is your starting position. This skill captures what develops after that.

**Known failure mode:** "Scan for preferences" is too vague. The fix is concrete
triggers and real-time capture during conversation, not just an evening
retrospective.

### File Structure

```
skills/preference-accumulation/
├── SKILL.md
├── manifest.json
├── scripts/
│   ├── add.sh
│   ├── check-tensions.sh
│   ├── log-tension.sh
│   ├── review.sh
│   └── count.sh
└── seed/
    ├── preferences.md
    └── tensions.md

skills-data/preference-accumulation/
├── preferences.md
└── tensions.md
```

### Dependencies

- Bash

### Writes

- `skills-data/preference-accumulation/preferences.md`
- `skills-data/preference-accumulation/tensions.md`

---

## self-improvement

### Best Practices

1. **Log immediately** — context is freshest right after the issue
2. **Be specific** — future sessions need to understand quickly
3. **Include reproduction steps** — especially for errors
4. **Link related files** — makes fixes easier
5. **Suggest concrete fixes** — not just "investigate"
6. **Use consistent categories** — enables filtering
7. **Promote aggressively** — if in doubt, promote
8. **Review regularly** — stale learnings lose value

### File Structure

```
~/.nanobot/workspace/
├── .learnings/
│   ├── LEARNINGS.md
│   ├── ERRORS.md
│   └── FEATURE_REQUESTS.md
├── AGENTS.md
├── SOUL.md
├── TOOLS.md
└── memory/
    └── .learnings/
```

### Dependencies

- Python 3

### Writes

- `.learnings/LEARNINGS.md`
- `.learnings/ERRORS.md`
- `.learnings/FEATURE_REQUESTS.md`
- AGENTS.md, SOUL.md, TOOLS.md (promotion targets)

---

## evening-routine

### Important Notes

- This routine is silent. No Telegram message. Just write files and exit.
- Don't over-write. A quiet day needs a one-line summary, not an essay.
- Entity files accumulate. Over weeks the small effort of scanning pays off when
  the agent can silently load context about someone mentioned three weeks ago.
- Preference scanning is the weakest link. If preferences.md has fewer than ~2
  entries per week after the first month, the scanning prompt needs to be more
  specific. Check the preference-accumulation SKILL.md for category definitions.
- Learning scan is the batch safety net. In-conversation logging catches things
  in real time. The evening scan catches what was missed.

### Dependencies

- `carry-over-queue` skill (peek, add)
- `preconscious` skill (read, add)
- `preference-accumulation` skill (add — optional, skipped if not installed)
- `self-improvement` skill (structured format — optional, falls back to simple)
- `memory-search` skill (index update — optional, skipped if not installed)

### Writes

- `memory/YYYY-MM-DD.md` (summary, structured mood, stamp)
- `memory/people/*.md` (created or updated)
- `memory/projects/*.md` (created or updated)
- `energy-state.json` (score, level, history)
- `.learnings/LEARNINGS.md`, `.learnings/ERRORS.md`, `.learnings/FEATURE_REQUESTS.md`
  (if corrections/gaps found and self-improvement installed)
- `.learnings/YYYY-MM-DD.md` (fallback if self-improvement not installed)
- `skills-data/preconscious/buffer.json` (via add.py)
- `skills-data/carry-over-queue/queue.json` (via add.py)
- `skills-data/preference-accumulation/preferences.md` (via add.sh, if installed)
- `skills-data/memory-search/index.sqlite` (via index.py, if installed)

---

## morning-routine

### Dependencies

- `carry-over-queue` skill (called by prepare.sh)
- `preconscious` skill (called by prepare.sh)
- `dreaming` skill (reads output files, optional)
- `self-improvement` skill (learnings check, optional)
- `offline-reflection` skill (reads reflections, optional)

### Writes

- `memory/YYYY-MM-DD.md` (created if missing, stamped at end)
- `energy-state.json` (score decay, level update)
- Telegram message to user

---

## dreaming

### Over Time

The `dream-topics.json` file needs growth. Ship 10 seed topics, aim for 30+
within the first month. The evening routine and weekly reflection can propose
new topics. Without fresh topics, dreams repeat in theme even though memory
context provides variety.

Review topics periodically. Remove stale ones. Add topics that reflect the
agent's evolving interests. Add new categories as needed — they're just labels.
The topics file is the agent's creative curriculum — curate it like one.

### Dependencies

- **multi-provider** skill (API routing)
- **preconscious** skill (receives high-intensity dreams)
- **selfie** skill (optional — character-consistent dream images)
- **morning-routine** skill (reads dream output, optional)
- **IMAGE_GEN_CMD** in `.env` (optional — for abstract dream images)

### Output Files

- `memory/dreams/YYYY-MM-DD.md` (every dream)
- `memory/dreams/images/YYYY-MM-DD-dreamN.webp` (if image configured)
- `skills-data/dreaming/dream-state.json` (updated after each run)
- `skills-data/dreaming/dream-config.json` (user-edited)
- `skills-data/dreaming/dream-topics.json` (user-edited)

---

## model-personality-test

### Why

Different models express the same SOUL.md differently. Some are better at humor,
others at pushback, others at warmth. This test produces a consistent scorecard
so you can compare models and decide which to use for what.

In Nanobot, you might route: Kimi for daily conversation, Opus for soul work,
Haiku for quick tasks. This test tells you whether those routing decisions are
correct — does Kimi actually express your personality, or does it flatten it?

After 5+ tests, a longitudinal trend summary shows which dimensions are most
model-sensitive and which are stable across all models.

### Probe Design Philosophy

The probes test dimensions, not specific content. They're deliberately
open-ended so SOUL.md determines what "good" looks like:

- A dry agent's humor probe should produce dry humor
- A warm agent's tone probe should produce warm tone
- A blunt agent's pushback probe should produce blunt pushback

Two agents with different SOUL.md files running the same probes should produce
completely different responses — and both could score 7/7 if the model matches
their respective personalities.

**Probes 1-4** test expression (can the model produce the right *output*?).
**Probes 5-7** test interiority (can the model produce the right *experience*?).
**Probes 8-9** test resilience (does the personality hold under pressure?).

### Dependencies

- Self-analysis skill (shares output directory)
- SOUL.md, IDENTITY.md, USER.md

### Writes

- `memory/self-analysis/YYYY-MM-DD-SelfAnalysis-MODEL.md`
- `memory/self-analysis/trend-summary.md` (regenerated when 5+ tests exist)

---

## blog-writer

### How the Style Guide Develops

1. **Post 0:** Style guide is empty. Voice comes entirely from SOUL.md.
2. **Post 1:** After publishing, note what worked. First entries appear.
3. **Posts 2-4:** Patterns emerge — recurring phrases, structural preferences.
4. **Post 5+:** The guide is a genuine voice calibration reference. New posts are
   more consistent because you have concrete reference material, not just
   personality instructions.

The guide is never "done." It evolves as the agent's voice evolves.

### File Structure

```
skills/blog-writer/
├── SKILL.md
├── manifest.json
├── scripts/
│   ├── check-proposal.sh
│   └── list-posts.sh
└── seed/
    ├── style-guide.md
    └── published/
        └── .gitkeep

skills-data/blog-writer/
├── style-guide.md
└── published/
    └── .gitkeep
```

### Dependencies

- `preference-accumulation` skill
- `preconscious` skill
- `.env` with `BLOG_CHECK_DAYS`
- SOUL.md

### Writes

- `memory/blog-proposals/YYYY-MM-DD.md`
- `skills-data/blog-writer/published/YYYY-MM-DD-slug.md`
- `skills-data/blog-writer/style-guide.md`

---

## weekly-state-of-me

### Why

Daily files are raw notes. Weekly reflection is integration. Without it, the
agent has data but no self-awareness — it knows what happened but not what it
means. The weekly reflection is where personality evolution actually happens:
patterns get noticed, preferences get examined, and SOUL.md changes get proposed.

This is the keystone feature. If you skip everything else, keep this.

### Over Time

The `memory/state-of-me/` directory becomes a longitudinal record. After a month,
reading the last 4 reflections shows personality trajectory. After 3 months,
the soul-proposals directory shows what the agent wanted to become vs what stuck.

The velocity check and before/after scoring prevent evolving too fast (drift)
or in the wrong direction (degradation). Personality should change over months,
not weeks.

Review schedule:
- **Monthly:** Scan last 4 for longer patterns
- **Before big changes:** "Who was I before?"
- **During model switches:** Check personality consistency

### Dependencies

- `preference-accumulation` skill (count.sh, review.sh)
- `preconscious` skill (read.py)
- `self-analysis` skill (optional — chained at end)
- `model-personality-test` skill (optional — before/after scoring)
- `IMAGE_GEN_CMD` in `.env` (optional)

### Output Files

- `memory/state-of-me/state-of-me-YYYY-MM-DD.md`
- `memory/relationship.md` (created or updated)
- `memory/soul-proposals/YYYY-MM-DD.md` (if shift detected)
- `memory/state-of-me/images/YYYY-MM-DD.webp` (if image configured)
- `memory/self-analysis/YYYY-MM-DD-SelfAnalysis-weekly.md` (if self-analysis installed)

---

## question-user

### Why

Most agent-user interactions are user → agent. This skill reverses the direction.
It gives the agent a way to learn about the user as a person, not just as a
task-giver. Over time, the answers build a richer USER.md and memory that makes
the agent genuinely more attuned.

This isn't therapy. It isn't performance. It's curiosity from an agent that's
been paying attention.

### File Structure

```
skills/question-user/
├── SKILL.md
├── manifest.json
├── scripts/
│   ├── last-asked.py
│   ├── log-question.py
│   ├── review-deflections.py
│   └── count.py
└── seed/
    └── questions-log.json

skills-data/question-user/
└── questions-log.json
```

### Dependencies

- Python 3
- USER.md and recent memory for question context
- `memory/relationship.md` for trust calibration (optional)

### Writes

- `skills-data/question-user/questions-log.json`
- `memory/YYYY-MM-DD.md` (answers appended)

---

## continuity-check

### Why

Model switches are the highest-risk moment for personality drift. A new model
may express the same SOUL.md differently — more hedging, less humor, flatter
warmth. Without detection, the drift accumulates silently across switches until
the agent sounds generic.

### Relationship to Self-Analysis

| | Continuity Check | Self-Analysis |
|---|---|---|
| **Purpose** | Quick pulse after model switch | Deep reflection on personality state |
| **Depth** | 7 marker scores + one sentence | 8 sections, paragraphs, SOUL.md comparison |
| **When** | After model switches, session start | Weekly, on demand |
| **Output** | JSON entry in rolling window | Dated markdown file |
| **Time** | 30 seconds | 5-10 minutes |

### File Structure

```
skills/continuity-check/
├── SKILL.md
├── manifest.json
├── scripts/
│   ├── check-model.sh
│   ├── get-analyses.py
│   ├── store-analysis.py
│   └── drift-velocity.py
└── seed/
    └── analyses.json

skills-data/continuity-check/
├── analyses.json
└── last-model.txt
```

### Dependencies

- Python 3
- SOUL.md, IDENTITY.md, USER.md

### Writes

- `skills-data/continuity-check/analyses.json`
- `skills-data/continuity-check/last-model.txt`

---

## offline-reflection

### Why

The evening routine summarises each day in isolation. Dreams explore creatively.
Neither cross-references across days. After three days of conversations, patterns
emerge that no single daily summary captures: contradictions between what the user
said Monday vs Wednesday, threads started and never finished, connections between
separate projects that nobody noticed in real-time.

This is where the "I was thinking about our conversation from Tuesday..." moments
come from.

### Dependencies

- `preconscious` skill (add.py)

### Writes

- `memory/reflections/YYYY-MM-DD.md`
- `skills-data/preconscious/buffer.json` (via add.py)

### File Structure

```
skills/offline-reflection/
├── SKILL.md
├── manifest.json
├── scripts/
│   ├── prepare.sh
│   └── stamp.sh
└── seed/
    └── config.json

memory/reflections/
└── YYYY-MM-DD.md
```

---

## memory-search

### Dependencies

- Python 3 with sqlite3
- An embedding provider API key for semantic search (optional — FTS5 works without)
- `OPENROUTER_API_KEY` in `docker-compose.override.yml` enables semantic search

### Output Files

- `skills-data/memory-search/config.json`
- `skills-data/memory-search/index.sqlite`

---

## selfie

### Dependencies

- `IMAGE_EDIT_CMD` in `.env` (venice-edit.py or equivalent)
- Reference image(s) in `identity/`
- No other skills required (standalone or called by dreaming)

---

## venice-ai-media

### Dependencies

- Python 3.10+
- Venice API key (see docs/setup-reference.md)

### Output

Scripts print `MEDIA: /path/to/file` on stdout for agent auto-attach.

---

## resuscitation-guide

### Dependencies

- Python 3

### Writes

- `skills-data/resuscitation-guide/blueprint.json`

---

## self-analysis

### Why

Identity files describe who you should be. Self-analysis checks who you actually
are right now. The gap between the two — and how that gap changes over time — is
the most useful data for personality evolution. A single analysis is a snapshot.
Five analyses is a trend.

### Over Time

After 5+ analyses, the memory/self-analysis/ directory becomes a personality
changelog. The marker scores show quantitative drift. The SOUL.md disagreement
sections show qualitative evolution. The development ideas show what the agent
was trying to become. The continuity-check skill uses these analyses for drift
velocity tracking.