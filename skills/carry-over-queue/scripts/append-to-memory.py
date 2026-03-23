#!/usr/bin/env python3
"""Auto-promote old items, then append carry-over to today's memory file.
Called by the morning routine skill.
Usage: append-to-memory.py [YYYY-MM-DD]
"""
import json, os, re, sys, subprocess
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
MEMORY_DIR = os.environ.get("MEMORY_DIR", os.path.join(WORKSPACE, "memory"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
TZ = os.environ.get("TZ", "UTC")

QUEUE_FILE = os.path.join(SKILL_DATA, "queue.json")
SIMMER_DAYS = 3

# Resolve date
if len(sys.argv) > 1:
    date_str = sys.argv[1]
else:
    try:
        from zoneinfo import ZoneInfo
        date_str = datetime.now(ZoneInfo(TZ)).strftime("%Y-%m-%d")
    except Exception:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Validate date format — prevent path traversal
if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
    print(f"ERROR: Invalid date format: {date_str} (expected YYYY-MM-DD)", file=sys.stderr)
    sys.exit(1)

memory_file = os.path.join(MEMORY_DIR, f"{date_str}.md")

if not os.path.exists(QUEUE_FILE):
    sys.exit(0)

with open(QUEUE_FILE) as f:
    data = json.load(f)

pending = [item for item in data.get("items", []) if item["status"] == "pending"]

if not pending:
    sys.exit(0)

# --- Simmering check: auto-promote items 3+ days old to urgent ---
now_epoch = datetime.now(timezone.utc).timestamp()
promoted = 0

for item in data["items"]:
    if item["status"] != "pending" or item["priority"] == "urgent":
        continue
    try:
        item_date = item["timestamp"].split("T")[0]
        item_epoch = datetime.strptime(item_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
        age_days = int((now_epoch - item_epoch) / 86400)
        if age_days >= SIMMER_DAYS:
            item["priority"] = "urgent"
            promoted += 1
    except (ValueError, KeyError):
        pass

if promoted > 0:
    print(f"Simmering: {promoted} item(s) promoted to urgent (3+ days old).")

with open(QUEUE_FILE, "w") as f:
    json.dump(data, f, indent=2)

# --- Get formatted carry-over via get.py ---
get_script = os.path.join(SCRIPT_DIR, "get.py")
result = subprocess.run([sys.executable, get_script], capture_output=True, text=True, env=os.environ)
carry_over = result.stdout.strip()

if not carry_over:
    sys.exit(0)

# --- Append to memory file ---
os.makedirs(os.path.dirname(memory_file), exist_ok=True)
if not os.path.exists(memory_file):
    with open(memory_file, "w") as f:
        f.write(f"# {date_str}\n\n")

with open(memory_file, "a") as f:
    f.write(f"\n{carry_over}\n")

pending_count = len(pending)
print(f"Appended {pending_count} carry-over item(s) to {memory_file}")
