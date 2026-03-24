#!/usr/bin/env python3
"""Verify system health — check files, skills, memory, cron.
Usage: verify.py
"""
import os, sys, shutil, re, json
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
ENV_FILE = os.path.join(WORKSPACE, ".env")

# Source .env
if os.path.isfile(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                val = val.strip('"').strip("'")
                if key.strip() not in os.environ:
                    os.environ[key.strip()] = val

TZ = os.environ.get("TZ", "UTC")
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILLS_DIR = os.path.join(WORKSPACE, "skills")

errors = 0
warnings = 0

try:
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo(TZ))
except Exception:
    now = datetime.now(timezone.utc)

print("=== Agent System Health Check ===")
print(f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')} ({TZ})")
print(f"Workspace: {WORKSPACE}")
print()

# --- Core identity files ---
print("Core Identity Files:")
for fname in ["SOUL.md", "IDENTITY.md", "USER.md", "AGENTS.md", "HEARTBEAT.md", "TOOLS.md", ".env", "energy-state.json"]:
    fpath = os.path.join(WORKSPACE, fname)
    if os.path.isfile(fpath):
        size = os.path.getsize(fpath)
        print(f"  ✓ {fname} ({size} bytes)")
    else:
        marker = "✗" if fname not in ("HEARTBEAT.md", "TOOLS.md", "energy-state.json") else "⚠"
        print(f"  {marker} {fname} MISSING")
        if fname not in ("HEARTBEAT.md", "TOOLS.md", "energy-state.json"):
            errors += 1
        else:
            warnings += 1
print()

# --- MEMORY.md ---
memory_md_root = os.path.join(WORKSPACE, "MEMORY.md")
memory_md_old = os.path.join(WORKSPACE, "memory", "MEMORY.md")
root_exists = os.path.isfile(memory_md_root)
old_exists = os.path.isfile(memory_md_old)

if root_exists and old_exists:
    print("MEMORY.md: ⚠ Found at BOTH locations — duplicate!")
    print("  Root (correct): MEMORY.md")
    print("  Old location:   memory/MEMORY.md")
    print("  Fix: rm memory/MEMORY.md (keep the root copy)")
    warnings += 1
elif root_exists:
    with open(memory_md_root) as f:
        line_count = len(f.readlines())
    status = "✓" if line_count <= 50 else "⚠"
    if line_count > 50:
        warnings += 1
    print(f"MEMORY.md: {status} {line_count} lines at workspace root (target: ≤50)")
elif old_exists:
    print("MEMORY.md: ⚠ Found at memory/MEMORY.md (old location) — should be at workspace root")
    print("  Fix: mv memory/MEMORY.md MEMORY.md")
    warnings += 1
else:
    print("MEMORY.md: ✗ MISSING")
    errors += 1

# --- Key memories ---
key_mem = os.path.join(WORKSPACE, "memory", "key-memories.md")
if os.path.isfile(key_mem):
    print("key-memories.md: ✓")
else:
    print("key-memories.md: ⚠ MISSING")
    warnings += 1

# --- location.json ---
loc = os.path.join(WORKSPACE, "location.json")
print(f"location.json: {'✓' if os.path.isfile(loc) else '— not configured'}")

# --- Cron jobs ---
cron_file = os.path.join(WORKSPACE, "..", "cron", "jobs.json")
cron_file = os.path.normpath(cron_file)
if os.path.isfile(cron_file):
    try:
        with open(cron_file) as f:
            cron_data = json.load(f)
        job_count = len(cron_data.get("jobs", []))
        print(f"../cron/jobs.json: ✓ ({job_count} job(s))")
    except (json.JSONDecodeError, OSError):
        print("../cron/jobs.json: ⚠ Exists but invalid JSON")
        warnings += 1
else:
    print("../cron/jobs.json: ✗ MISSING — run setup.sh to generate")
    errors += 1
print()

# --- Memory directory ---
memory_dir = os.path.join(WORKSPACE, "memory")
if os.path.isdir(memory_dir):
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

    for subdir in ["people", "projects", "dreams", ".learnings", "state-of-me", "self-analysis", "reflections", "soul-proposals"]:
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
core_skills = ["preconscious", "carry-over-queue", "morning-routine", "evening-routine", "zero-trust"]
companion_skills = [
    "preference-accumulation", "continuity-check", "question-user",
    "self-analysis", "model-personality-test", "weekly-state-of-me",
    "blog-writer", "conversation-starters", "dreaming", "offline-reflection",
    "resuscitation-guide", "self-improvement", "memory-search", "selfie",
    "venice-ai-media", "openrouter-image-simple",
]

for skill in core_skills:
    skill_path = os.path.join(SKILLS_DIR, skill)
    if os.path.isdir(skill_path) and os.path.isfile(os.path.join(skill_path, "SKILL.md")):
        print(f"  ✓ {skill} (core)")
    else:
        print(f"  ✗ {skill} (core) MISSING")
        errors += 1

for skill in companion_skills:
    skill_path = os.path.join(SKILLS_DIR, skill)
    if os.path.isdir(skill_path) and os.path.isfile(os.path.join(skill_path, "SKILL.md")):
        print(f"  ✓ {skill}")
    else:
        print(f"  — {skill} (not installed)")
print()

# --- Skills-data cross-validation ---
print("Skills-data:")
if os.path.isdir(DATA_DIR):
    data_skills = sorted(os.listdir(DATA_DIR))
    print(f"  {len(data_skills)} skill(s) with runtime data")
    for d in data_skills:
        files = os.listdir(os.path.join(DATA_DIR, d))
        print(f"  {d}/: {len(files)} file(s)")

    # Check that each installed skill with a seed/ dir has a skills-data/ dir
    missing_data = []
    for skill in os.listdir(SKILLS_DIR):
        seed_path = os.path.join(SKILLS_DIR, skill, "seed")
        data_path = os.path.join(DATA_DIR, skill)
        if os.path.isdir(seed_path) and not os.path.isdir(data_path):
            missing_data.append(skill)
    if missing_data:
        print(f"  ⚠ Skills with seed/ but no skills-data/: {', '.join(missing_data)}")
        print("    Re-run setup.sh to seed them.")
        warnings += 1
else:
    print("  ✗ MISSING")
    errors += 1
print()

# --- Environment ---
print("Environment:")
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
