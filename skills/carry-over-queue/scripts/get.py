#!/usr/bin/env python3
"""Get and consume all pending items. Outputs formatted text for memory file.
Marks items as 'retrieved'. Sorted by priority then age.
Usage: get.py
"""
import json, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)

QUEUE_FILE = os.path.join(SKILL_DATA, "queue.json")

PRIORITY_ORDER = {"urgent": 0, "curious": 1, "simmering": 2, "normal": 3}
PRIORITY_PREFIX = {"urgent": "🔥 ", "curious": "💭 ", "simmering": "", "normal": ""}

if not os.path.exists(QUEUE_FILE):
    sys.exit(0)

with open(QUEUE_FILE) as f:
    data = json.load(f)

pending = [item for item in data.get("items", []) if item["status"] == "pending"]

if not pending:
    sys.exit(0)

pending.sort(key=lambda x: (PRIORITY_ORDER.get(x["priority"], 3), x["timestamp"]))

print("## Carry-Over from Previous Sessions")
print()
for item in pending:
    prefix = PRIORITY_PREFIX.get(item["priority"], "")
    print(f"- {prefix}{item['message']}")
print()

# Mark all pending as retrieved
for item in data["items"]:
    if item["status"] == "pending":
        item["status"] = "retrieved"

with open(QUEUE_FILE, "w") as f:
    json.dump(data, f, indent=2)
