#!/usr/bin/env python3
"""Output current preconscious buffer for session loading.
Sorted by effective score (C + I) descending.
Usage: read.py
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
    print("Preconscious buffer is empty.")
    sys.exit(0)

with open(BUFFER_FILE) as f:
    data = json.load(f)

if not data.get("items"):
    print("Preconscious buffer is empty.")
    sys.exit(0)

print("## Preconscious Buffer")
print()
for item in sorted(data["items"], key=lambda x: x["c"] + x["i"], reverse=True):
    print(f"- {item['description']} [C:{item['c']}, I:{item['i']}]")
