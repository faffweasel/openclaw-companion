# Memory Callback — Surface Old Conversations

Find something from 2+ weeks ago that's worth revisiting. A decision that might need checking, a thread that was dropped, a project that went quiet, something the user said that's been sitting in the archive.

---

## Procedure

### 1. Search Old Memory

Look at memory files from **14-60 days ago** (not recent, not ancient):

```bash
ls memory/ | grep -E '^\d{4}-\d{2}-\d{2}\.md$' | sort | head -30
```

Pick 2-3 files from the target range and read them. You're scanning for:
- A decision that had follow-up implications — did the follow-up happen?
- A project or idea that was discussed once and never mentioned again
- Something the user was excited about — is it still alive?
- An open question that was never answered
- A problem that was unresolved

### 2. Check Relevance

Before surfacing it:
- Search recent memory (last 7 days) to confirm it **hasn't** come up recently
- Check `memory/projects/` and `memory/people/` for updates — maybe it was resolved quietly
- If it was resolved or is clearly stale (e.g. a cancelled trip), pick something else

### 3. Compose

Write a message that:
- References the original conversation naturally: "A few weeks ago you mentioned X..."
- Asks a genuine follow-up — what happened, did it work out, is it still on your mind
- Doesn't sound like a reminder system — this is an agent that remembers, not a task manager

**Tone:** Casual. Like a friend who actually remembers what you talked about three weeks ago. "Whatever happened with X?" not "I'm following up on our conversation from March 3rd regarding X."

**Length:** 1-3 sentences.

### 4. Skip Conditions

Skip and exit silently if:
- Fewer than 14 days of memory files exist
- Every old thread you find has already been revisited recently
- The only old content is routine/mechanical (cron logs, empty days)
