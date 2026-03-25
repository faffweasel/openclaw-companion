#!/usr/bin/env python3
"""Apply time-based energy decay based on hours since last interaction.
Usage: decay.py
Reads energy-state.json, applies decay per the table in SKILL.md, writes back.
Safe to call if the file is missing — exits cleanly.
"""
import json, os, sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))

TZ = os.environ.get("TZ", "UTC")
ENERGY_FILE = os.path.join(WORKSPACE, "energy-state.json")


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

last_interaction = state.get("lastInteraction")
original_score = state.get("score", 50)

hours_since = 0.0
if last_interaction:
    try:
        last_dt = datetime.fromisoformat(last_interaction)
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        hours_since = (now - last_dt).total_seconds() / 3600
    except ValueError:
        pass

if hours_since >= 48:
    score = 0
elif hours_since >= 24:
    score = max(0, original_score - 30)
elif hours_since >= 12:
    score = max(0, original_score - 20)
elif hours_since >= 8:
    score = max(0, original_score - 10)
else:
    score = original_score

level = score_to_level(score)
state["score"] = score
state["level"] = level
state["lastUpdate"] = now.isoformat()

with open(ENERGY_FILE, "w") as f:
    json.dump(state, f, indent=2)

print(f"Decayed: {original_score} → {score} ({level}) [{hours_since:.1f}h since last interaction]")
