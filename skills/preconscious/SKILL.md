---
name: preconscious
description: "Active mind buffer — max 5 items with currency/importance scoring that decay daily. Use when the agent needs to track what's top-of-mind, add items during conversation, or read the buffer at session start."
metadata: '{"nanobot": {"requires": {"bins": ["python3"]}}}'
---

# Preconscious Buffer

What's on your mind right now. A short-term buffer of items you'd bring up if conversation started this moment.

## How It Works

The buffer holds a maximum of **5 items**. Each item has two scores:

- **C (Currency):** How fresh this is. Starts at 5, decays by 1 each morning. Range 0–5.
- **I (Importance):** How much it matters regardless of freshness. Set once, never changes. Range 1–5.

**Keep rule:** High I survives low C. An I:5 item stays even at C:1. Items are only dropped when C reaches 0 AND I ≤ 2, or when they're displaced by a higher-scoring new item.

**Effective score** for ranking: `C + I` (used for drop decisions when buffer is full).

## Scripts

### Add an item

```bash
./scripts/add.py "description" [C] [I]
```

- C defaults to 5 (just happened)
- I defaults to 3 (moderately important)
- If buffer is full (5 items), drops the item with the lowest `C + I` score

### Decay currency (morning routine)

```bash
./scripts/decay.py
```

Decrements C by 1 for every item. Drops items where C ≤ 0 AND I ≤ 2. Called by the morning routine, not directly by cron.

### Read current buffer

```bash
./scripts/read.py
```

Outputs current buffer as human-readable text. Format: `- description [C:N, I:N]`. Sorted by `C + I` descending. Called at session start.

### Drop lowest item

```bash
./scripts/drop-lowest.py
```

Removes the item with the lowest `C + I` score. Used internally by add.py when buffer is full.

## Data

`skills-data/preconscious/buffer.json`:

```json
{
  "max_items": 5,
  "items": [
    {
      "description": "Unresolved auth bug in deploy pipeline",
      "c": 4,
      "i": 5,
      "added": "2026-03-18"
    }
  ]
}
```

## When to Add Items

During conversation, add when:
- Something is unresolved and should be surfaced next session
- The user shares something emotionally significant
- A decision was made that has follow-up implications
- You notice a pattern worth tracking

Don't add:
- Routine task completions
- Things already captured in carry-over queue (that's for messages *to* the user; this is your *internal* state)
- Trivial observations

## Preconscious vs Carry-Over

| | Preconscious | Carry-Over |
|---|---|---|
| Direction | Agent → Agent (internal state) | Agent → User (things to tell them) |
| Lifespan | Days/weeks (C/I scoring) | Consumed next morning |
| Consumption | Read, influences tone; persists | Read, appended to memory, deleted |
| Example | "User seemed burned out on Friday" | "Ask user about the Japan trip" |
