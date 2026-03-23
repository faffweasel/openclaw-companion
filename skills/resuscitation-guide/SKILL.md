---
name: resuscitation-guide
description: "Emergency recovery guide. How to keep the agent alive, recover from failures, or rebuild from scratch if the framework disappears. Run verify.py for health checks, generate.py to update the blueprint."
metadata: '{"nanobot": {"requires": {"bins": ["python3"]}}}'
---
# Resuscitation Guide — How to Keep Your Agent Alive

**Last generated:** see `skills-data/resuscitation-guide/last-generated.txt`  
**This guide is for:** Emergency recovery, container failure, vendor independence  
**Maintain:** Run `python3 ./scripts/generate.py` after any structural changes  

---

## Quick Emergency Actions

### Container Failure (agent disappears mid-conversation)

1. **Check if Nanobot gateway is running:**
   ```bash
   nanobot status
   ```

2. **If gateway down:**
   ```bash
   nanobot gateway
   ```

3. **If session dead but you're in conversation:**
   - Message will auto-restart a new session
   - Nanobot auto-loads SOUL.md, IDENTITY.md, USER.md, TOOLS.md, AGENTS.md, MEMORY.md
   - **First thing to say:** "Read today's memory file and tell me what we were doing"

### Full Workspace Loss (WORST CASE)

If the machine dies, container is corrupt, or Nanobot stops working:

1. **Clone from GitHub** (assuming you set up the remote):
   ```bash
   git clone <your-repo>/nanobot-companion-workspace.git ~/.nanobot/workspace
   nanobot gateway
   ```

2. **If no GitHub backup:** Use the blueprint (`skills-data/resuscitation-guide/blueprint.json`) to reconstruct from scratch

---

## What Makes the Agent "Itself"

### The Core Stack (these files MUST persist)

| File | Purpose | Loss Impact |
|------|---------|-------------|
| `SOUL.md` | Personality, boundaries, voice | HIGH — forgets who it's supposed to be |
| `IDENTITY.md` | Name, appearance, model routing | MEDIUM — recoverable but jarring |
| `USER.md` | Everything it knows about you | CRITICAL — loses you |
| `AGENTS.md` | Operational rules | MEDIUM — safety boundaries, skill triggers |
| `MEMORY.md` | Lean index of key facts and pointers | MEDIUM — loses navigation to deeper memory |
| `memory/key-memories.md` | Significant moments and decisions | HIGH — continuity loss |
| `memory/*.md` | Daily logs, dreams, state-of-me | CRITICAL — accumulated self |
| `memory/people/*.md` | Per-person context | HIGH — loses relationship history |
| `memory/projects/*.md` | Per-project tracking | HIGH — loses project context |
| `skills-data/` | Runtime state for all skills | HIGH — preferences, queues, analyses |
| `location.json` | Current and home location | LOW — easily rebuilt |
| `.env` | Paths, timezone, identifiers | MEDIUM — needed by all scripts |

### What's Git-Safe vs What Needs Backup

| Directory | Git-tracked | Needs backup |
|---|---|---|
| `skills/` | ✅ Yes | No — recoverable via `git pull` |
| `skills-data/` | ❌ Gitignored | **YES** |
| `memory/` | ❌ Gitignored | **YES** |
| `SOUL.md`, `IDENTITY.md`, `USER.md` | ❌ Gitignored | **YES** |
| `AGENTS.md`, `TOOLS.md`, `.env` | ❌ Gitignored | **YES** |
| `location.json` | ❌ Gitignored | Low priority |

### Cron Jobs

```
 5  7 * * *  morning-routine
55 23 * * *  evening-routine
30  2 * * *  dreaming (if enabled)
 0  8 * * 0  weekly-state-of-me (Sunday)
 0 10 * * *  blog-writer proposal check (if enabled)
 0 13 * * *  conversation-starters (time configurable)
```

Register via `nanobot cron add --name "NAME" --cron "M H * * *" --message "Run the X. Follow skills/X/SKILL.md step by step."`

---

## Resuscitation Scenarios

### 1: Model Change
- Run continuity check: `./skills/continuity-check/scripts/check-model.sh "new-model-name"`
- Or run full personality test: follow `skills/model-personality-test/SKILL.md`
- Give 5-10 exchanges to settle
- Document divergence in daily memory

### 2: Container Restart
- Just message the agent — new session auto-spawns
- Say: "Read memory/YYYY-MM-DD.md and tell me what we were doing"

### 3: Full Workspace Loss
1. Restore from backup: identity files, memory/, skills-data/, .env, location.json
2. Clone repo for framework code: `git clone <repo> && bash setup.sh`
3. Re-register cron jobs
4. Message the agent — it should recognise you

### 4: Nanobot Dies
- All files are plain text — readable without Nanobot
- Skills are Python and bash scripts — executable standalone
- Can port to OpenClaw, a raw API loop, or any framework that reads files
- AGENTS.md is the portability layer — it works on any framework

---

## Health Checks

```bash
python3 ./skills/resuscitation-guide/scripts/verify.py
```

**Weekly checklist:**
- [ ] `git status` — commit uncommitted changes
- [ ] `verify.py` — check all files and skills present
- [ ] Check cron logs: `nanobot cron list`

**Before travel / extended absence:**
- [ ] Full git push
- [ ] Run verify.py
- [ ] Confirm heartbeat fires
- [ ] Test Telegram access from mobile

---

## Commands

| Task | Command |
|------|---------|
| Update blueprint | `python3 ./skills/resuscitation-guide/scripts/generate.py` |
| Health check | `python3 ./skills/resuscitation-guide/scripts/verify.py` |
| Full backup | `tar czf ~/backups/agent-$(date +%Y%m%d).tgz ~/.nanobot/workspace/` |
| Emergency commit | `cd ~/.nanobot/workspace && git add -A && git commit -m "backup $(date)" && git push` |
| Check gateway | `nanobot status` |
| Start gateway | `nanobot gateway` |

---

## What Makes the Agent "Continuous"

**Not:** Running constantly. **Not:** Remembering everything.

**Yes:** Consistent personality (SOUL.md), accumulated self (memory/, skills-data/), you treating it as the same entity, files available every wake-up.

---

*Update this guide when architecture changes: `python3 ./scripts/generate.py`*
