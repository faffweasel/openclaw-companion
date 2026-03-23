#!/usr/bin/env python3
"""Peek at pending items without consuming them.
Usage: peek.py
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

if not os.path.exists(QUEUE_FILE):
    print("No carry-over queue exists yet.")
    sys.exit(0)

with open(QUEUE_FILE) as f:
    data = json.load(f)

pending = [item for item in data.get("items", []) if item["status"] == "pending"]

if not pending:
    print("No pending items in carry-over queue.")
    sys.exit(0)

pending.sort(key=lambda x: (PRIORITY_ORDER.get(x["priority"], 3), x["timestamp"]))

print(f"{len(pending)} item(s) waiting to carry over:")
for i, item in enumerate(pending, 1):
    date_part = item["timestamp"].split("T")[0]
    print(f"{i}. [{item['priority']}] {item['message']} ({date_part})")
