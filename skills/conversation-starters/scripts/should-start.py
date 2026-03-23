#!/usr/bin/env python3
"""Decide whether to start a conversation and pick which type.
Usage: should-start.py
Output: SKIP (already triggered today or too recent) or one of:
  CURIOSITY, SELF_TEACHING, MEMORY_CALLBACK, CREATIVE_PROVOCATION, RECOMMENDATION
"""
import json, os, sys, random
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
MEMORY_DIR = os.environ.get("MEMORY_DIR", os.path.join(WORKSPACE, "memory"))
TZ = os.environ.get("TZ", "UTC")

CONFIG_FILE = os.path.join(SKILL_DATA, "config.json")

# --- Load config ---
os.makedirs(SKILL_DATA, exist_ok=True)
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        config = json.load(f)
else:
    config = {
        "weights": {
            "CURIOSITY": 25,
            "SELF_TEACHING": 15,
            "MEMORY_CALLBACK": 15,
            "RECOMMENDATION": 15,
            "CREATIVE_PROVOCATION": 15
        },
        "min_quiet_minutes": 30,
        "last_triggered": None
    }

# --- Resolve today's date ---
try:
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo(TZ))
except Exception:
    now = datetime.now(timezone.utc)

today = now.strftime("%Y-%m-%d")

# --- Check if already triggered today ---
last = config.get("last_triggered")
if last == today:
    print("SKIP")
    print("Already triggered today.")
    sys.exit(0)

# --- Check if conversation is quiet ---
memory_file = os.path.join(MEMORY_DIR, f"{today}.md")
min_quiet = config.get("min_quiet_minutes", 30)

if os.path.exists(memory_file):
    mtime = os.path.getmtime(memory_file)
    now_ts = datetime.now(timezone.utc).timestamp()
    minutes_since = (now_ts - mtime) / 60
    if minutes_since < min_quiet:
        print("SKIP")
        print(f"Last activity {int(minutes_since)} minutes ago (threshold: {min_quiet}).")
        sys.exit(0)

# --- Check preconditions for specific subskills ---
weights = dict(config.get("weights", {}))

# Memory callback needs 14+ days of history
if os.path.isdir(MEMORY_DIR):
    memory_files = [f for f in os.listdir(MEMORY_DIR) if f.endswith(".md") and f[0].isdigit()]
else:
    memory_files = []
if len(memory_files) < 14:
    weights.pop("MEMORY_CALLBACK", None)

# Recommendation needs 5+ accumulated preferences
pref_file = os.path.join(DATA_DIR, "preference-accumulation", "preferences.md")
if os.path.exists(pref_file):
    with open(pref_file) as f:
        pref_count = f.read().count("## ")
    if pref_count < 5:
        weights.pop("RECOMMENDATION", None)
else:
    weights.pop("RECOMMENDATION", None)

# Creative provocation needs 2+ memory files in last 3 days
recent_count = 0
for i in range(3):
    check_date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
    if os.path.exists(os.path.join(MEMORY_DIR, f"{check_date}.md")):
        recent_count += 1
if recent_count < 2:
    weights.pop("CREATIVE_PROVOCATION", None)

# --- Weighted random pick ---
if not weights:
    weights = {"CURIOSITY": 100}

options = list(weights.keys())
weight_values = [weights[k] for k in options]
chosen = random.choices(options, weights=weight_values, k=1)[0]

# --- Record trigger ---
config["last_triggered"] = today
with open(CONFIG_FILE, "w") as f:
    json.dump(config, f, indent=2)

print(chosen)
print(f"Selected: {chosen} (from {len(options)} eligible subskills)")
