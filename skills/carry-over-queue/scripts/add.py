#!/usr/bin/env python3
"""Add an item to the carry-over queue.
Usage: add.py "message" [priority]
Priority: normal (default), urgent, curious, simmering
"""
import json, os, sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
TZ = os.environ.get("TZ", "UTC")

QUEUE_FILE = os.path.join(SKILL_DATA, "queue.json")
VALID_PRIORITIES = ("normal", "urgent", "curious", "simmering")

if len(sys.argv) < 2:
    print('Usage: add.py "message" [priority]')
    sys.exit(1)

message = sys.argv[1]
priority = sys.argv[2] if len(sys.argv) > 2 else "normal"

if priority not in VALID_PRIORITIES:
    print(f"Invalid priority: {priority} (use {', '.join(VALID_PRIORITIES)})")
    sys.exit(1)

os.makedirs(SKILL_DATA, exist_ok=True)
if os.path.exists(QUEUE_FILE):
    with open(QUEUE_FILE) as f:
        data = json.load(f)
else:
    data = {"items": []}

try:
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo(TZ))
except Exception:
    now = datetime.now(timezone.utc)

data["items"].append({
    "message": message,
    "timestamp": now.isoformat(),
    "priority": priority,
    "status": "pending"
})

with open(QUEUE_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"Queued [{priority}]: {message}")
