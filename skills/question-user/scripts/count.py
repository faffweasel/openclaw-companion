#!/usr/bin/env python3
"""Question statistics. Useful for health checks.
Usage: count.py
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

questions = data.get("questions", [])
total = len(questions)
answered = sum(1 for q in questions if q.get("status") == "answered")
deflected = sum(1 for q in questions if q.get("status") == "deflected")
declined = sum(1 for q in questions if q.get("status") == "declined")

print("=== Question Statistics ===")
print(f"Total asked: {total}")
print(f"  Answered:  {answered}")
print(f"  Deflected: {deflected}")
print(f"  Declined:  {declined}")

if deflected > 0:
    print()
    print("Deflected questions available for re-approach.")
