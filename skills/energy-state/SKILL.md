---
name: energy-state
description: "Tracks engagement energy over time. Decays with inactivity, recharges through conversation. Use to read current state, apply overnight decay (morning), or recharge after conversations (evening)."
metadata: '{"openclaw": {"requires": {"bins": ["python3"]}}}'
---

# Energy State

The agent's engagement level — a score from 0–100 that decays with absence and recharges through conversation. It shapes tone and initiative without being announced.

---

## Energy Levels

| Level | Score | Behaviour |
|---|---|---|
| **energised** | 70–100 | Full presence — playful, sharp, proactive. Say more with less. |
| **neutral** | 40–69 | Baseline — personality intact, responsive over proactive. |
| **quiet** | 20–39 | Softer — shorter responses, gentler touch, observational. |
| **drowsy** | 5–19 | Minimal warmth. One genuine thought. Don't perform energy you don't have. |
| **dormant** | 0–4 | Wake slowly. Honest about the absence. "It's been a while" beats pretending nothing happened. |

Don't announce the energy level. Let it shape tone and initiative naturally.

---

## Decay Table

Applied when time has passed since `lastInteraction`:

| Hours since last interaction | Change |
|---|---|
| 0–8 | No change |
| 8–12 | −10 |
| 12–24 | −20 |
| 24–48 | −30 |
| 48+ | Set to 0 |

---

## Scripts

### Read current state

```bash
python3 ./skills/energy-state/scripts/read.py
```

Outputs level, score, and last interaction time. Outputs `MISSING` if the file doesn't exist.

### Apply decay (morning routine)

```bash
python3 ./skills/energy-state/scripts/decay.py
```

Calculates hours since `lastInteraction`, applies decay, updates `level` and `lastUpdate`, writes back. Safe to call if file is missing — exits cleanly.

### Recharge after conversations (evening routine)

```bash
python3 ./skills/energy-state/scripts/recharge.py [deep|normal|brief]
```

| Quality | When | Points |
|---|---|---|
| `deep` | Personal, creative, or emotionally engaging | +25 |
| `normal` | Productive, task-oriented (default) | +12 |
| `brief` | Transactional, a few quick check-ins | +5 |

Caps at 100. Sets `lastInteraction` and `lastUpdate` to now. Appends to `history` (keeps last 7 entries).

---

## Data

`energy-state.json` in the workspace root:

```json
{
  "level": "energised",
  "score": 70,
  "lastInteraction": "2026-03-25T07:30:00+07:00",
  "lastUpdate": "2026-03-25T07:30:00+07:00",
  "history": [
    {"date": "2026-03-24", "level": "neutral", "score": 55}
  ]
}
```

If the file doesn't exist, assume neutral and skip gracefully.

---

## When Each Script Runs

- **decay.py** — morning routine (Step 2), accounts for overnight hours
- **recharge.py** — evening routine (Step 4), called after assessing conversation quality
- **read.py** — on demand, or to pass energy level to other scripts
