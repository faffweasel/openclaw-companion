#!/usr/bin/env python3
"""Check when the last question was asked. Used for frequency limiting.
Usage: last-asked.py
Output: ELIGIBLE (3+ days since last) or TOO_RECENT (asked within 3 days)
"""
import json, os, sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)

LOGFILE = os.path.join(SKILL_DATA, "questions-log.json")
MIN_GAP_DAYS = 3

if not os.path.exists(LOGFILE):
    print("ELIGIBLE")
    print("No questions ever asked.")
    sys.exit(0)

with open(LOGFILE) as f:
    data = json.load(f)

questions = data.get("questions", [])
if not questions:
    print("ELIGIBLE")
    print("No questions ever asked.")
    sys.exit(0)

last_date = questions[-1].get("date")
if not last_date:
    print("ELIGIBLE")
    print("No valid date found.")
    sys.exit(0)

try:
    last_epoch = datetime.strptime(last_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
    now_epoch = datetime.now(timezone.utc).timestamp()
    days_since = int((now_epoch - last_epoch) / 86400)
except ValueError:
    print("ELIGIBLE")
    print("Could not parse last question date.")
    sys.exit(0)

if days_since >= MIN_GAP_DAYS:
    print("ELIGIBLE")
    print(f"Last question: {last_date} ({days_since} days ago)")
    deflected = sum(1 for q in questions if q.get("status") == "deflected")
    if deflected > 0:
        print(f"Deflected questions available: {deflected} (consider re-approaching from a new angle)")
else:
    print("TOO_RECENT")
    print(f"Last question: {last_date} ({days_since} days ago). Wait {MIN_GAP_DAYS - days_since} more day(s).")
