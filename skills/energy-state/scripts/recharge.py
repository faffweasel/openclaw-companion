#!/usr/bin/env python3
"""Recharge energy after a day of conversations.
Usage: recharge.py [deep|normal|brief]
  deep    — personal, creative, or emotionally engaging (+25)
  normal  — productive, task-oriented (+12, default)
  brief   — transactional or a few quick check-ins (+5)
Caps at 100. Sets lastInteraction and lastUpdate. Appends to history (keeps last 7).
"""
import json, os, sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))

TZ = os.environ.get("TZ", "UTC")
ENERGY_FILE = os.path.join(WORKSPACE, "energy-state.json")
MAX_HISTORY = 7

QUALITY_POINTS: dict[str, int] = {"deep": 25, "normal": 12, "brief": 5}


def score_to_level(score: int) -> str:
    if score >= 70:
        return "energised"
    if score >= 40:
        return "neutral"
    if score >= 20:
        return "quiet"
    if score >= 5:
        return "drowsy"
    return "dormant"


quality = sys.argv[1].lower() if len(sys.argv) > 1 else "normal"
if quality not in QUALITY_POINTS:
    print(f"Unknown quality '{quality}'. Use: deep, normal, brief")
    sys.exit(1)

if not os.path.exists(ENERGY_FILE):
    print("energy-state.json not found — skipping")
    sys.exit(0)

try:
    with open(ENERGY_FILE) as f:
        state = json.load(f)
except (json.JSONDecodeError, OSError) as e:
    print(f"ERROR reading energy-state.json: {e}")
    sys.exit(1)

try:
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo(TZ))
except Exception:
    now = datetime.now(timezone.utc)

original_score = state.get("score", 50)
points = QUALITY_POINTS[quality]
score = min(100, original_score + points)
level = score_to_level(score)
now_iso = now.isoformat()
today = now.strftime("%Y-%m-%d")

history = state.get("history", [])
history.append({"date": today, "level": level, "score": score})
history = history[-MAX_HISTORY:]

state.update({
    "score": score,
    "level": level,
    "lastInteraction": now_iso,
    "lastUpdate": now_iso,
    "history": history,
})

with open(ENERGY_FILE, "w") as f:
    json.dump(state, f, indent=2)

print(f"Recharged ({quality}): {original_score} → {score} ({level}) [+{points}]")
