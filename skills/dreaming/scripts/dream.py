#!/usr/bin/env python3
"""
dream.py — legacy entry point, not used in OpenClaw.

In OpenClaw the cron job runs the agent natively as the dream model
(set via payload.model in ../cron/jobs.json). The agent follows
skills/dreaming/SKILL.md directly — no external API calls needed.

Useful helpers for the agent (still active):
  should-dream.py  — quiet hours check, nightly limit, topic picker
  post-dream.py    — writes intensity/mood header, preconscious integration
"""

import sys


def main() -> int:
    print("In OpenClaw, dreaming is handled natively by the agent following SKILL.md.")
    print("The cron job starts a session with the dream model set in ../cron/jobs.json.")
    print("See skills/dreaming/SKILL.md for the procedure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
