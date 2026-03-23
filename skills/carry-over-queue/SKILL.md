---
name: carry-over-queue
description: "Store thoughts for the user that don't fit the current moment. Surfaces them next morning. Items lingering 3+ days auto-promote to urgent. Use when the agent thinks of something to tell the user later, or needs to queue drift guard proposals."
metadata: '{"nanobot": {"requires": {"bins": ["python3"]}}}'
---

# Carry-Over Queue

Store thoughts for the user that don't fit the current moment. Surfaces them next morning.

## How It Works

- Queue stored in `skills-data/carry-over-queue/queue.json` as a JSON array
- Each item has: message, timestamp, priority, status
- Morning routine calls `append-to-memory.py` which writes pending items into today's memory file
- Status changes from `pending` to `retrieved`
- History is preserved (retrieved items stay for reference)

### Simmering Priority

Items that linger for 3+ days without being retrieved auto-promote to `urgent`. When appended to memory, urgent items are marked with 🔥.

Priority levels: `urgent` > `curious` > `simmering` > `normal`

## Scripts

### Add an item

```bash
./scripts/add.py "message" [priority]
```

Priority: `normal` (default), `urgent`, `curious`, `simmering`.

### Peek at pending items

```bash
./scripts/peek.py
```

Shows pending items without consuming them.

### Get and consume pending items

```bash
./scripts/get.py
```

Outputs pending items formatted for memory file insertion. Marks items as `retrieved`. Sorts by priority then age.

### Append to today's memory

```bash
./scripts/append-to-memory.py [YYYY-MM-DD]
```

Called by the morning routine. Runs simmering check, calls get.py, appends to memory file. Exits silently if no pending items.

## Data

`skills-data/carry-over-queue/queue.json`:

```json
{
  "items": [
    {
      "message": "Ask about the Japan trip",
      "timestamp": "2026-03-18T10:00:00+07:00",
      "priority": "normal",
      "status": "pending"
    }
  ]
}
```

## When to Add Items

- Something you want to tell the user but the moment has passed
- A follow-up question for next session
- A reminder about something the user mentioned
- Drift Guard proposals: `add.py "DRIFT GUARD: [proposed change to FILE.md]"`

## Preconscious vs Carry-Over

See `preconscious/SKILL.md` for the comparison table. Key distinction: preconscious = your internal state (agent→agent). Carry-over = things to tell the user (agent→user).
