#!/usr/bin/env python3
"""
Store a model continuity analysis entry.
Usage: store-analysis.py --model "kimi-k2.5" --feel "yes" --assessment "Still me" --markers '{"directness": 5, ...}'
"""
import argparse
import json
import os
from datetime import datetime, timezone

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
STORE_PATH = os.path.join(SKILL_DATA, "analyses.json")
LAST_MODEL_PATH = os.path.join(SKILL_DATA, "last-model.txt")
MAX_ENTRIES = 10

# Read timezone from .env if available
TZ_NAME = os.environ.get("TZ", "UTC")
try:
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(TZ_NAME)
except (ImportError, Exception):
    tz = timezone.utc


def load_store():
    if os.path.exists(STORE_PATH):
        with open(STORE_PATH) as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    return []


def save_store(entries):
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    with open(STORE_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, help="Model name/alias")
    parser.add_argument("--feel", required=True, choices=["yes", "no", "weird"], help="Still feel like me?")
    parser.add_argument("--assessment", required=True, help="Brief self-assessment text")
    parser.add_argument("--markers", default="{}", help="JSON object of personality marker scores")
    args = parser.parse_args()

    entries = load_store()

    entry = {
        "date": datetime.now(tz).strftime("%Y-%m-%d"),
        "timestamp": datetime.now(tz).isoformat(),
        "model": args.model,
        "feel": args.feel,
        "assessment": args.assessment,
        "markers": json.loads(args.markers),
    }
    entries.append(entry)

    # Keep only last N
    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]

    save_store(entries)

    # Update last-model tracker
    os.makedirs(os.path.dirname(LAST_MODEL_PATH), exist_ok=True)
    with open(LAST_MODEL_PATH, "w") as f:
        f.write(args.model)

    print(f"Stored: model={args.model}, feel={args.feel} ({len(entries)} total)")


if __name__ == "__main__":
    main()
