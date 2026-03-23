#!/usr/bin/env python3
"""Add an item to the preconscious buffer.
Usage: add.py "description" [C] [I]
C defaults to 5, I defaults to 3.
"""
import json, os, sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
TZ = os.environ.get("TZ", "UTC")

BUFFER_FILE = os.path.join(SKILL_DATA, "buffer.json")

if len(sys.argv) < 2:
    print('Usage: add.py "description" [C] [I]')
    sys.exit(1)

description = sys.argv[1]
c = int(sys.argv[2]) if len(sys.argv) > 2 else 5
importance = int(sys.argv[3]) if len(sys.argv) > 3 else 3

os.makedirs(SKILL_DATA, exist_ok=True)
if os.path.exists(BUFFER_FILE):
    with open(BUFFER_FILE) as f:
        data = json.load(f)
else:
    data = {"max_items": 5, "items": []}

max_items = data.get("max_items", 5)

# If buffer is full, drop lowest before adding
if len(data["items"]) >= max_items:
    data["items"].sort(key=lambda x: x["c"] + x["i"])
    dropped = data["items"].pop(0)
    print(f"Dropped: {dropped['description']}")

today = datetime.now().strftime("%Y-%m-%d")
data["items"].append({"description": description, "c": c, "i": importance, "added": today})

with open(BUFFER_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"Added [C:{c}, I:{importance}]: {description}")
