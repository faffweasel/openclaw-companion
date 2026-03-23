#!/usr/bin/env python3
"""Verify system health — check files, skills, memory, gateway.
Usage: verify.py
"""
import os, sys, shutil, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
ENV_FILE = os.path.join(WORKSPACE, ".env")
TZ = os.environ.get("TZ", "UTC")

# Source .env manually for key vars
if os.path.isfile(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                val = val.strip('"').strip("'")
                # Don't override existing env vars, only fill gaps
                if key.strip() not in os.environ:
                    os.environ[key.strip()] = val

errors = 0
warnings = 0

print("=== Agent System Health Check ===")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Workspace: {WORKSPACE}")
print()

# --- Core identity files ---
print("Core Identity Files:")
for fname in ["SOUL.md", "IDENTITY.md", "USER.md", "AGENTS.md", "HEARTBEAT.md", "TOOLS.md", ".env"]:
    fpath = os.path.join(WORKSPACE, fname)
    if os.path.isfile(fpath):
        size = os.path.getsize(fpath)
        print(f"  ✓ {fname} ({size} bytes)")
    else:
        print(f"  ✗ {fname} MISSING")
        errors += 1
print()

# --- MEMORY.md size check ---
memory_md = os.path.join(WORKSPACE, "MEMORY.md")
if os.path.isfile(memory_md):
    with open(memory_md) as f:
        line_count = len(f.readlines())
    status = "✓" if line_count <= 50 else "⚠"
    if line_count > 50:
        warnings += 1
    print(f"MEMORY.md: {status} {line_count} lines (target: ≤50)")
else:
    print("MEMORY.md: ✗ MISSING")
    errors += 1

# --- Key memories ---
key_mem = os.path.join(WORKSPACE, "memory", "key-memories.md")
if os.path.isfile(key_mem):
    print(f"key-memories.md: ✓")
else:
    print(f"key-memories.md: ✗ MISSING")
    warnings += 1

# --- location.json ---
loc = os.path.join(WORKSPACE, "location.json")
if os.path.isfile(loc):
    print(f"location.json: ✓")
else:
    print(f"location.json: — not configured")
print()

# --- Memory directory ---
memory_dir = os.path.join(WORKSPACE, "memory")
if os.path.isdir(memory_dir):
    # Count recent daily files
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo(TZ))
    except Exception:
        now = datetime.now(timezone.utc)

    recent = 0
    for i in range(7):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        if os.path.isfile(os.path.join(memory_dir, f"{d}.md")):
            recent += 1

    total = len([f for f in os.listdir(memory_dir) if re.match(r"\d{4}-\d{2}-\d{2}\.md$", f)])
    print(f"Memory: {total} daily files total, {recent} in last 7 days")
    if recent < 3:
        print("  ⚠ Low recent activity")
        warnings += 1

    # Subdirectories
    for subdir in ["people", "projects", "dreams", ".learnings", "state-of-me", "self-analysis"]:
        path = os.path.join(memory_dir, subdir)
        if os.path.isdir(path):
            count = len(os.listdir(path))
            print(f"  memory/{subdir}/: {count} files")
else:
    print("Memory directory: ✗ MISSING")
    errors += 1
print()

# --- Skills ---
print("Skills:")
skills_dir = os.path.join(WORKSPACE, "skills")
core_skills = ["preconscious", "carry-over-queue", "morning-routine", "evening-routine"]
companion_skills = ["preference-accumulation", "continuity-check", "question-user",
                    "self-analysis", "model-personality-test", "weekly-state-of-me",
                    "blog-writer", "conversation-starters", "dreaming", "resuscitation-guide"]

for skill in core_skills:
    skill_path = os.path.join(skills_dir, skill)
    if os.path.isdir(skill_path) and os.path.isfile(os.path.join(skill_path, "SKILL.md")):
        print(f"  ✓ {skill} (core)")
    else:
        print(f"  ✗ {skill} (core) MISSING")
        errors += 1

for skill in companion_skills:
    skill_path = os.path.join(skills_dir, skill)
    if os.path.isdir(skill_path) and os.path.isfile(os.path.join(skill_path, "SKILL.md")):
        print(f"  ✓ {skill}")
    else:
        print(f"  — {skill} (not installed)")
print()

# --- Skills-data ---
data_dir = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
if os.path.isdir(data_dir):
    data_skills = sorted(os.listdir(data_dir))
    print(f"Skills-data: {len(data_skills)} skill(s) with runtime data")
    for d in data_skills:
        files = os.listdir(os.path.join(data_dir, d))
        print(f"  {d}/: {len(files)} file(s)")
else:
    print("Skills-data: ✗ MISSING")
    errors += 1
print()

# --- Environment ---
print("Environment:")
if shutil.which("nanobot"):
    print("  ✓ nanobot in PATH")
else:
    print("  ✗ nanobot not in PATH")
    errors += 1

if shutil.which("python3"):
    print("  ✓ python3 in PATH")
else:
    print("  ✗ python3 not in PATH")
    errors += 1
print()

# --- Git ---
git_dir = os.path.join(WORKSPACE, ".git")
if os.path.isdir(git_dir):
    import subprocess
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=WORKSPACE)
    uncommitted = len([l for l in result.stdout.strip().split("\n") if l.strip()])
    print(f"Git: {uncommitted} uncommitted file(s)")
    if uncommitted > 0:
        print(f"  ⚠ Consider: git add -A && git commit -m 'backup {now.strftime('%Y%m%d')}'")
        warnings += 1
else:
    print("Git: not initialised")
    warnings += 1
print()

# --- Summary ---
if errors == 0 and warnings == 0:
    print("=== STATUS: HEALTHY ===")
elif errors == 0:
    print(f"=== STATUS: OK ({warnings} warning(s)) ===")
else:
    print(f"=== STATUS: {errors} ERROR(S), {warnings} WARNING(S) ===")

sys.exit(errors)
