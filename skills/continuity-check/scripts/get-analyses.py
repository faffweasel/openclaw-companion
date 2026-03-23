#!/usr/bin/env python3
"""
Retrieve last N model continuity analyses for comparison.
Usage: get-analyses.py [--last N]
Outputs JSON array of last N entries, most recent last.
"""
import argparse
import json
import os

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
STORE_PATH = os.path.join(SKILL_DATA, "analyses.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--last", type=int, default=3, help="Number of recent entries to return")
    args = parser.parse_args()

    if not os.path.exists(STORE_PATH):
        print("[]")
        return

    with open(STORE_PATH) as f:
        entries = json.load(f)

    if not entries:
        print("[]")
        return

    recent = entries[-args.last:]
    print(json.dumps(recent, indent=2))


if __name__ == "__main__":
    main()
