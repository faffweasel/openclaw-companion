#!/usr/bin/env python3
"""Drop the item with the lowest effective score (C + I).
Usage: drop-lowest.py
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
    print("Buffer empty, nothing to drop.")
    sys.exit(0)

with open(BUFFER_FILE) as f:
    data = json.load(f)

if not data.get("items"):
    print("Buffer empty, nothing to drop.")
    sys.exit(0)

data["items"].sort(key=lambda x: x["c"] + x["i"])
dropped = data["items"].pop(0)

with open(BUFFER_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"Dropped: [{dropped['description']}] [C:{dropped['c']}, I:{dropped['i']}]")
