#!/usr/bin/env python3
"""Show deflected questions for re-approach from new angles.
Usage: review-deflections.py
"""
import json, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)

LOGFILE = os.path.join(SKILL_DATA, "questions-log.json")

if not os.path.exists(LOGFILE):
    print("No questions log exists yet.")
    sys.exit(0)

with open(LOGFILE) as f:
    data = json.load(f)

deflected = [q for q in data.get("questions", []) if q.get("status") == "deflected"]

if not deflected:
    print("No deflected questions.")
    sys.exit(0)

print(f"{len(deflected)} deflected question(s) — consider re-approaching from a different angle:")
print()
for q in deflected:
    note = f" (note: {q['notes']})" if q.get("notes") else ""
    print(f"{q['date']}: {q['question']}{note}")
print()
print("Don't repeat the same question. Reframe it — come at the same territory from a different direction.")
