#!/usr/bin/env python3
"""Decay currency scores and drop expired items.
Called by the morning routine skill.
Usage: decay.py
"""
import json, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)

BUFFER_FILE = os.path.join(SKILL_DATA, "buffer.json")

if not os.path.exists(BUFFER_FILE):
    print("Buffer empty, nothing to decay.")
    sys.exit(0)

with open(BUFFER_FILE) as f:
    data = json.load(f)

if not data.get("items"):
    print("Buffer empty, nothing to decay.")
    sys.exit(0)

# Show what's about to be decayed
print("Decaying:")
for item in data["items"]:
    print(f"  {item['description']} [C:{item['c']} → C:{item['c'] - 1}, I:{item['i']}]")

# Decrement C by 1
for item in data["items"]:
    item["c"] -= 1

# Drop items where C <= 0 AND I <= 2
dropped = [item for item in data["items"] if item["c"] <= 0 and item["i"] <= 2]
if dropped:
    print("Dropping (expired):")
    for item in dropped:
        print(f"  {item['description']}")
    data["items"] = [item for item in data["items"] if not (item["c"] <= 0 and item["i"] <= 2)]

with open(BUFFER_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"Buffer: {len(data['items'])} items remaining.")
