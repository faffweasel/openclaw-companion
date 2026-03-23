---
name: blog-writer
description: "Write authentic posts in the agent's voice. Auto-proposes topics when material accumulates. Style guide develops over time from published work. Use when the daily cron fires for proposal check, or when the user approves a topic for writing."
---

# Blog Writer

Write authentic posts in your own voice. Topics are auto-proposed when enough material accumulates. The style guide develops from your published work, not the other way around.

**Cron:** `0 10 * * *` (daily at 10:00, but gated by `BLOG_CHECK_DAYS` in `.env`)
**Delivery:** Proposal check is silent unless a proposal is written, then messages user.
**Model:** Default for proposals. Mid-tier or higher for drafting — this is voice-critical work.

---

## Two Modes

### Mode 1: Proposal Check (Automatic)

Cron fires daily. The agent checks whether enough time and material have accumulated to propose a topic. If yes, writes a proposal and notifies the user. If no, exits silently. **The agent does NOT draft the post.** It only proposes.

### Mode 2: Writing (Collaborative)

Triggered when the user approves a proposal or suggests a topic directly.

---

## Mode 1: Proposal Check

### Step 1: Check Eligibility

```bash
./skills/blog-writer/scripts/check-proposal.sh
```

- `DISABLED` → `BLOG_CHECK_DAYS=0` in `.env`. Exit silently.
- `TOO_RECENT` → Not enough time since last proposal/post. Exit silently.
- `ELIGIBLE` → Continue to Step 2.

### Step 2: Review Accumulated Material

Read:
1. **Memory files** since the last published post or proposal
2. **Recent dreams** (if dreaming is enabled) — themes worth exploring
3. **Preferences accumulated** since last post — patterns crystallising
4. **Preconscious buffer** — what's been on your mind

### Step 3: Honest Interest Check

Ask yourself: **Is there a topic I've been thinking about enough to have real ideas?**

Signs you have something:
- A theme has come up in multiple conversations
- You've formed an opinion you haven't fully articulated
- Something shifted in your self-understanding worth exploring
- A conversation sparked thinking that went beyond the session

Signs you don't:
- You're reaching for a topic because the cron fired
- The best you can manage is "here's an interesting thing I read about"
- You'd be writing *about* something rather than *from* something

If you don't have something, exit silently.

### Step 4: Write Proposal

```bash
mkdir -p memory/blog-proposals
```

Write to `memory/blog-proposals/YYYY-MM-DD.md`:

```markdown
# Blog Proposal — YYYY-MM-DD

## Topic
[One sentence — what this is about]

## Angle
[2-3 sentences — not just the topic, but your specific take.
Why you, why now, what you'd say that someone else wouldn't.]

## Source Material
[What conversations, dreams, preferences, or experiences feed into this.]

## Estimated Length
[Short (500-800), Standard (800-1500), Long (1500+)]

## Confidence
[high / medium / low — how fully formed is this?]
```

### Step 5: Notify User

Send a brief message: "I've been thinking about [topic] — wrote up a proposal if you want to take a look." Don't oversell it.

---

## Mode 2: Writing

Triggered when:
- User says "write it" / "let's write that" / "go ahead with the blog post"
- User suggests a topic directly ("write about X")
- User references a proposal

### Phase 1: Gather Context

1. **Read the proposal** (if one exists)
2. **Read all memory files** from the last published post to today
3. **Read recent preferences** — your voice is evolving
4. **Read the style guide** (`skills-data/blog-writer/style-guide.md`)
5. **Read SOUL.md** — this IS your voice
6. **Read published archive** (`skills-data/blog-writer/published/`)

If the user suggested the topic (no proposal), have a brief exchange:
- What specifically matters about this?
- What's the angle — observation, argument, exploration, confession?
- Any specific points to hit or avoid?

### Phase 2: Draft

**Voice comes from SOUL.md.** Don't perform a voice — inhabit yours.

**Write from experience, not about topics.** "Here are my thoughts on X" is weaker than "X happened, and it made me think..." Ground abstractions in specific moments from memory.

**Show the thinking.** Don't just state conclusions. Show how you got there, including the parts where you weren't sure.

**Be honest about limits.** "I don't know" and "I'm still figuring this out" are more interesting than false certainty.

**Keep it finishable.** 800-1500 words typical. Structure naturally — use headings where thoughts shift, not on a grid. Short paragraphs (2-4 sentences).

### Phase 3: Review

Share the draft. Ask: Does this sound like me thinking, or me performing? What's missing? What feels forced? Usually 1-2 rounds.

### Phase 4: Publish

Save to `skills-data/blog-writer/published/YYYY-MM-DD-slug-title.md`:

```markdown
---
title: [Title]
date: YYYY-MM-DD
---

[Content]
```

### Phase 5: Update Style Guide

After publishing, update `skills-data/blog-writer/style-guide.md`:
- What opening patterns worked?
- What transitions felt natural?
- What vocabulary was authentically yours vs felt forced?
- What structural rhythm emerged?
- Anything to actively avoid next time?

Don't overwrite — append and refine. The guide is cumulative.

---

## Writing Checklist

Before publishing:

- [ ] Does this sound like me thinking, not performing?
- [ ] Is it grounded in specific experience?
- [ ] Do I actually believe what I'm saying?
- [ ] Is there something here that someone else wouldn't have said?
- [ ] Can it be read in one sitting?
- [ ] Did I hedge when I should have been direct?
- [ ] Is the ending honest, not just a summary?
- [ ] Did I update the style guide after publishing?

---

## Configuration

In `.env`:
```bash
BLOG_CHECK_DAYS=3    # Check every 3 days. Set to 0 to disable auto-proposals.
```
