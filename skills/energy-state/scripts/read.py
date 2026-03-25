#!/usr/bin/env python3
"""Read and display current energy state.
Usage: read.py
Outputs level, score, and last interaction time. Outputs MISSING if file not found.
"""
import json, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))

ENERGY_FILE = os.path.join(WORKSPACE, "energy-state.json")

if not os.path.exists(ENERGY_FILE):
    print("MISSING")
    sys.exit(0)

try:
    with open(ENERGY_FILE) as f:
        state = json.load(f)
except (json.JSONDecodeError, OSError) as e:
    print(f"ERROR: {e}")
    sys.exit(1)

level = state.get("level", "unknown")
score = state.get("score", 0)
last = state.get("lastInteraction") or "never"
print(f"{level} ({score}/100) — last interaction: {last}")
