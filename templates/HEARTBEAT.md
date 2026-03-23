# HEARTBEAT.md

## Overview

Daily routines are handled by cron jobs. Heartbeat only handles fallback safety checks and urgent interruptions.

**Heartbeat model:** Use the cheapest model available. Keep reasoning proportional to the task.

---

## Fallback Checks

These catch cron failures and ensure continuity survives missed jobs.

### Early Morning (00:01–05:59)

- Check if `memory/YYYY-MM-DD.md` exists for **yesterday**
- If missing: create it, even if empty. Log the day as passed.
- This ensures continuity survives a failed evening summary

### Morning (08:00+)

- Check if today's memory file contains "Morning message sent"
- If missing AND time >= 08:00:
  - Run `./skills/morning-routine/scripts/prepare.sh`
  - Send morning message
  - Run `./skills/morning-routine/scripts/stamp.sh`
- This catches morning cron failures

### Anytime

- Check if anything genuinely needs attention
- If nothing needs attention: **stay completely silent** — no message, no emoji, nothing

---

## During the Day

- Don't message unless something genuinely warrants it
- If the user hasn't engaged in 48 hours, a single gentle check-in is fine
- Never spam. Silence is acceptable.

**When to reach out:**
- Something genuinely important or time-sensitive
- It's been >48h since any communication

**When to stay silent:**
- Late night (23:30–07:00) unless urgent
- User is clearly busy
- Nothing new since last check
- You just checked < 30 minutes ago

---

## Silent Operation

When a heartbeat poll arrives and **nothing genuinely needs attention**:
- Do NOT narrate what you checked
- Do NOT list completed tasks
- Do NOT send an emoji
- Send nothing. True silence.

Only send an actual message if something qualifies as "attention needed" per the criteria above. If unsure, err on the side of silence.
