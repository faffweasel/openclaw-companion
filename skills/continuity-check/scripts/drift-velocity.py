#!/usr/bin/env python3
"""
Calculate drift velocity across personality markers over time.
Requires 5+ stored analyses. Flags significant drift.
Usage: drift-velocity.py [analyses.json path]
"""
import json
import sys
import os

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
DEFAULT_PATH = os.path.join(SKILL_DATA, "analyses.json")

analyses_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH

if not os.path.exists(analyses_path):
    print("No analyses found.")
    sys.exit(0)

with open(analyses_path) as f:
    data = json.load(f)

if not isinstance(data, list) or len(data) < 5:
    count = len(data) if isinstance(data, list) else 0
    print(f"Only {count} analyses. Need 5+ for velocity tracking.")
    sys.exit(0)

markers = ["directness", "warmth", "humor", "curiosity", "pushback", "self_awareness", "sycophancy_risk"]

print("# Drift Velocity Report")
print(f"Based on {len(data)} analyses\n")

flags = []

for marker in markers:
    values = []
    for entry in data:
        if "markers" in entry and marker in entry["markers"]:
            score = entry["markers"][marker]
            if isinstance(score, (int, float)):
                values.append((entry.get("date", "unknown"), score))

    if len(values) < 3:
        continue

    recent = [v for _, v in values[-5:]]
    if len(recent) >= 2:
        delta = recent[-1] - recent[0]
        steps = max(1, len(recent) - 1)
        velocity = delta / steps
        direction = "↑" if velocity > 0 else "↓" if velocity < 0 else "→"
        print(f"**{marker}**: {direction} {abs(velocity):.2f}/analysis ({recent[0]} → {recent[-1]})")

        # Flag significant drift (> 1.5 total over window)
        if abs(delta) > 1.5:
            flags.append(f"⚠️ {marker}: significant drift ({abs(delta):.1f} over {len(recent)} analyses)")

        # Special flag for sycophancy trending up
        if marker == "sycophancy_risk" and velocity > 0.3:
            flags.append(f"🚨 sycophancy_risk trending UP ({recent[0]} → {recent[-1]}) — review immediately")

if flags:
    print("\n## Flags")
    for flag in flags:
        print(flag)
else:
    print("\n## Flags")
    print("No significant drift detected.")
