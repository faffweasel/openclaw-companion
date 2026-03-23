#!/usr/bin/env python3
"""Log a question with its outcome.
Usage: log-question.py "question text" "answered|deflected|declined" ["optional notes"]
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

LOGFILE = os.path.join(SKILL_DATA, "questions-log.json")
VALID_STATUSES = ("answered", "deflected", "declined")

if len(sys.argv) < 3:
    print('Usage: log-question.py "question" "answered|deflected|declined" ["notes"]')
    sys.exit(1)

question = sys.argv[1]
status = sys.argv[2]
notes = sys.argv[3] if len(sys.argv) > 3 else ""

if status not in VALID_STATUSES:
    print(f"Invalid status: {status} (use {', '.join(VALID_STATUSES)})")
    sys.exit(1)

os.makedirs(SKILL_DATA, exist_ok=True)
if os.path.exists(LOGFILE):
    with open(LOGFILE) as f:
        data = json.load(f)
else:
    data = {"questions": []}

try:
    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo(TZ)).strftime("%Y-%m-%d")
except Exception:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

data["questions"].append({
    "question": question,
    "status": status,
    "date": today,
    "notes": notes
})

with open(LOGFILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"Logged [{status}]: {question}")
