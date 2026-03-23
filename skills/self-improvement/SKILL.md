---
name: self-improvement
description: "Captures learnings, errors, and corrections to .learnings/ files for continuous improvement. Use when: (1) A command or operation fails unexpectedly, (2) User corrects the agent — 'No, that's wrong', 'Actually...', 'That's outdated', (3) User requests a capability that doesn't exist, (4) An external API or tool fails, (5) Agent discovers its knowledge is outdated or incorrect, (6) A better approach is discovered for a recurring task, (7) User says 'log this', 'learn this', 'remember this mistake', 'save this as a learning', 'save this as a skill'. Also load before major tasks to review pending learnings."
metadata: '{"nanobot":{"emoji":"📝","requires":{"bins":["python3"]}}}'
---

# Self-Improvement

Log learnings, errors, and feature gaps to `.learnings/` files. Proven learnings get promoted to workspace files (AGENTS.md, SOUL.md, TOOLS.md). High-value patterns get extracted as reusable skills.

**Trigger:** In-conversation (on detection or user request), evening routine (batch sweep), morning routine (awareness check)
**Delivery:** Silent (file writes only)
**Key principle:** Log immediately — context is freshest right after the issue.

---

## Quick Reference

| Situation | Action |
|-----------|--------|
| Command/operation fails | Log to `.learnings/ERRORS.md` |
| User corrects you | Log to `.learnings/LEARNINGS.md` with category `correction` |
| User wants missing feature | Log to `.learnings/FEATURE_REQUESTS.md` |
| API/external tool fails | Log to `.learnings/ERRORS.md` with integration details |
| Knowledge was outdated | Log to `.learnings/LEARNINGS.md` with category `knowledge_gap` |
| Found better approach | Log to `.learnings/LEARNINGS.md` with category `best_practice` |
| Recurring pattern detected | Log/update `.learnings/LEARNINGS.md` with `Pattern-Key` |
| Similar to existing entry | Link with `See Also`, consider priority bump |
| Broadly applicable learning | Promote to AGENTS.md, SOUL.md, or TOOLS.md |

---

## Logging

When writing an entry, read `skills/self-improvement/references/TEMPLATES.md` for the structured format. Three templates: Learning Entry (`[LRN-...]`), Error Entry (`[ERR-...]`), Feature Request (`[FEAT-...]`).

---

## Detection Triggers

Automatically log when you notice:

| Trigger | Category | Target file |
|---|---|---|
| User corrects you | `correction` | `.learnings/LEARNINGS.md` |
| User requests missing capability | feature request | `.learnings/FEATURE_REQUESTS.md` |
| User provides info you didn't know | `knowledge_gap` | `.learnings/LEARNINGS.md` |
| Command/operation fails | error | `.learnings/ERRORS.md` |
| User says "log this" / "learn this" / "save this as a skill" | whatever fits | appropriate file |

---

## Resolving Entries

When an issue is fixed, update the entry:

1. Change `**Status**: pending` → `**Status**: resolved`
2. Add resolution block after Metadata:

```markdown
### Resolution
- **Resolved**: 2025-01-16T09:00:00Z
- **Commit/PR**: abc123 or #42
- **Notes**: Brief description of what was done
```

Other status values: `in_progress`, `wont_fix` (add reason), `promoted`, `promoted_to_skill`.

---

## Promoting to Workspace Files

When a learning is broadly applicable — not a one-off fix — promote it to permanent workspace context.

### Promotion Targets

| Target | What Belongs There |
|--------|-------------------|
| `AGENTS.md` | Workflow improvements, delegation patterns, automation rules |
| `SOUL.md` | Behavioural patterns, communication style, principles |
| `TOOLS.md` | Tool capabilities, API gotchas, integration quirks |
| `MEMORY.md` | Persistent facts worth loading every session (keep under 50 lines) |

### How to Promote

1. **Distill** the learning into a concise rule or fact
2. **Add** to appropriate section in target file
3. **Update** original entry: `**Status**: promoted`, `**Promoted**: AGENTS.md`

**Example — verbose learning:**
> Project uses pnpm workspaces. Attempted `npm install` but failed.
> Lock file is `pnpm-lock.yaml`. Must use `pnpm install`.

**Promoted to TOOLS.md — concise:**
```markdown
## Package Management
- Package manager: pnpm (not npm) — use `pnpm install`
```

---

## Recurring Pattern Detection

If logging something similar to an existing entry:

1. **Search first**: `grep -r "keyword" .learnings/`
2. **Link entries**: Add `See Also: ERR-20250110-001` in Metadata
3. **Bump priority** if issue keeps recurring

### Promotion Rule for Recurring Patterns

Promote when all are true:
- `Recurrence-Count >= 3`
- Seen across at least 2 distinct tasks
- Occurred within a 30-day window

Write promoted rules as short prevention rules (what to do before/while working), not long incident write-ups.

---

## Skill Extraction

When a learning is valuable enough to become a reusable skill, extract it.

### Extraction Criteria

| Criterion | Description |
|-----------|-------------|
| **Recurring** | Has `See Also` links to 2+ similar issues |
| **Verified** | Status is `resolved` with working fix |
| **Non-obvious** | Required investigation to discover |
| **Broadly applicable** | Useful beyond this specific project |
| **User-flagged** | User says "save this as a skill" |

### Extraction Workflow

1. **Identify candidate** — learning meets criteria above
2. **Run helper** (or create manually):
   ```bash
   ./skills/self-improvement/scripts/extract-skill.sh skill-name --dry-run
   ./skills/self-improvement/scripts/extract-skill.sh skill-name
   ```
3. **Customise SKILL.md** — fill template with learning content
4. **Update learning** — set `promoted_to_skill`, add `Skill-Path`
5. **Verify** — read skill in fresh session to ensure it's self-contained

See `references/SKILL-TEMPLATE.md` for the full template. See `references/examples.md` for concrete entry examples including skill extraction.

---

## Priority Guidelines

| Priority | When to Use |
|----------|-------------|
| `critical` | Blocks core functionality, data loss risk, security issue |
| `high` | Significant impact, affects common workflows, recurring issue |
| `medium` | Moderate impact, workaround exists |
| `low` | Minor inconvenience, edge case, nice-to-have |

## Area Tags

| Area | Scope |
|------|-------|
| `frontend` | UI, components, client-side code |
| `backend` | API, services, server-side code |
| `infra` | CI/CD, deployment, Docker, cloud |
| `tests` | Test files, testing utilities, coverage |
| `docs` | Documentation, comments, READMEs |
| `config` | Configuration files, environment, settings |


