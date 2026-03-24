#!/usr/bin/env python3
"""
Check if the agent should dream and pick a topic.

Checks: quiet hours, nightly limit, dream chance.
Outputs JSON to stdout on success, exits 1 if no dream.

Output format:
    {"category": "personal", "prompt": "...", "reflectionModel": "default"}
"""

import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))

ENV_FILE = os.path.join(WORKSPACE, ".env")
if os.path.isfile(ENV_FILE):
    with open(ENV_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

TZ = os.environ.get("TZ", "UTC")
os.environ["TZ"] = TZ

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)

CONFIG_FILE = os.path.join(SKILL_DATA, "dream-config.json")
TOPICS_FILE = os.path.join(SKILL_DATA, "dream-topics.json")
STATE_FILE = os.path.join(SKILL_DATA, "dream-state.json")


def load_json(path: str, default: dict) -> dict:
    """Load JSON file or return default."""
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return default.copy()


def save_json(path: str, data: dict) -> None:
    """Write JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def in_quiet_hours(hour: int, quiet_start: int, quiet_end: int) -> bool:
    """Check if current hour is within quiet hours window."""
    if quiet_start > quiet_end:
        # Window crosses midnight (e.g., 23-07)
        return hour >= quiet_start or hour < quiet_end
    else:
        # Window within same day (e.g., 1-6)
        return quiet_start <= hour < quiet_end


def parse_topic(topic_str: str) -> dict:
    """
    Parse topic string: 'reflection_model:category:prompt'
    Returns {"reflectionModel": "...", "category": "...", "prompt": "..."}
    """
    parts = topic_str.split(":", 2)
    if len(parts) == 3:
        return {
            "reflectionModel": parts[0],
            "category": parts[1],
            "prompt": parts[2],
        }
    elif len(parts) == 2:
        return {
            "reflectionModel": "default",
            "category": parts[0],
            "prompt": parts[1],
        }
    else:
        return {
            "reflectionModel": "default",
            "category": "freeform",
            "prompt": topic_str,
        }


def main() -> int:
    config = load_json(CONFIG_FILE, {
        "maxDreamsPerNight": 3,
        "dreamChance": 1.0,
        "quietStart": 1,
        "quietEnd": 6,
    })
    state = load_json(STATE_FILE, {
        "lastDreamDate": None,
        "dreamsTonight": 0,
    })

    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_hour = now.hour

    # Check quiet hours
    quiet_start = config.get("quietStart", 1)
    quiet_end = config.get("quietEnd", 6)
    if not in_quiet_hours(current_hour, quiet_start, quiet_end):
        print("Outside quiet hours", file=sys.stderr)
        return 1

    # Reset counter if new night
    if state.get("lastDreamDate") != current_date:
        if in_quiet_hours(current_hour, quiet_start, quiet_end):
            state["dreamsTonight"] = 0

    # Check nightly limit
    max_dreams = config.get("maxDreamsPerNight", 3)
    if state["dreamsTonight"] >= max_dreams:
        print("Nightly limit reached", file=sys.stderr)
        return 1

    # Roll the dice
    dream_chance = config.get("dreamChance", 1.0)
    if random.random() > dream_chance:
        print("Dream chance failed", file=sys.stderr)
        return 1

    # Pick a random topic (from dream-topics.json, not dream-config.json)
    topics_data = load_json(TOPICS_FILE, {"topics": []})
    topics = topics_data.get("topics", [])
    if not topics:
        print("No topics configured", file=sys.stderr)
        return 1

    topic_str = random.choice(topics)
    topic = parse_topic(topic_str)

    # Update state
    state["lastDreamDate"] = current_date
    state["dreamsTonight"] = state.get("dreamsTonight", 0) + 1
    save_json(STATE_FILE, state)

    # Output topic as JSON
    print(json.dumps(topic))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
