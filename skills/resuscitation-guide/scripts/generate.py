#!/usr/bin/env python3
"""Generate an updated system blueprint.
Run after any structural changes (new skills, path changes, cron updates).
Usage: generate.py
"""
import json, os, sys, re
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SKILL_NAME = os.path.basename(SKILL_DIR)
WORKSPACE = os.path.dirname(os.path.dirname(SKILL_DIR))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
SKILLS_DIR = os.path.join(WORKSPACE, "skills")
TZ = os.environ.get("TZ", "UTC")

os.makedirs(SKILL_DATA, exist_ok=True)

print("Generating system blueprint...")

# --- Resolve timestamp ---
try:
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo(TZ))
except Exception:
    now = datetime.now(timezone.utc)

# --- Scan skills ---
skills = []
if os.path.isdir(SKILLS_DIR):
    for entry in sorted(os.listdir(SKILLS_DIR)):
        manifest_path = os.path.join(SKILLS_DIR, entry, "manifest.json")
        if os.path.isfile(manifest_path):
            try:
                with open(manifest_path) as f:
                    m = json.load(f)
                skills.append({
                    "name": m.get("name", entry),
                    "type": m.get("type", "unknown"),
                    "description": m.get("description", "No description"),
                    "dependencies": m.get("dependencies", []),
                    "has_cron": m.get("cron") is not None
                })
            except (json.JSONDecodeError, IOError):
                skills.append({"name": entry, "type": "unknown", "description": "Failed to read manifest"})

# --- Scan skills-data ---
skills_data_contents = {}
if os.path.isdir(DATA_DIR):
    for entry in sorted(os.listdir(DATA_DIR)):
        skill_data_path = os.path.join(DATA_DIR, entry)
        if os.path.isdir(skill_data_path):
            files = [f for f in os.listdir(skill_data_path) if not f.startswith(".")]
            skills_data_contents[entry] = files

# --- Check identity files ---
identity_files = {}
for fname in ["SOUL.md", "IDENTITY.md", "USER.md", "AGENTS.md", "TOOLS.md",
              "HEARTBEAT.md", "location.json"]:
    fpath = os.path.join(WORKSPACE, fname)
    identity_files[fname] = {
        "exists": os.path.isfile(fpath),
        "size": os.path.getsize(fpath) if os.path.isfile(fpath) else 0
    }

# --- Check memory ---
memory_dir = os.path.join(WORKSPACE, "memory")
memory_info = {"exists": os.path.isdir(memory_dir)}
if memory_info["exists"]:
    daily_files = [f for f in os.listdir(memory_dir) if re.match(r"\d{4}-\d{2}-\d{2}\.md$", f)]
    memory_info["daily_file_count"] = len(daily_files)
    memory_info["has_key_memories"] = os.path.isfile(os.path.join(memory_dir, "key-memories.md"))
    memory_info["has_people"] = os.path.isdir(os.path.join(memory_dir, "people"))
    memory_info["has_projects"] = os.path.isdir(os.path.join(memory_dir, "projects"))
    memory_info["has_dreams"] = os.path.isdir(os.path.join(memory_dir, "dreams"))
    memory_info["has_learnings"] = os.path.isdir(os.path.join(memory_dir, ".learnings"))

    memory_md = os.path.join(WORKSPACE, "MEMORY.md")
    if os.path.isfile(memory_md):
        with open(memory_md) as f:
            memory_info["memory_md_lines"] = len(f.readlines())

# --- Check environment ---
import shutil
nanobot_info = {
    "python3_in_path": shutil.which("python3") is not None,
}

# --- Build blueprint ---
blueprint = {
    "generated": now.isoformat(),
    "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown",
    "workspace": WORKSPACE,
    "framework": "openclaw",
    "skills": skills,
    "skills_data": skills_data_contents,
    "identity_files": identity_files,
    "memory": memory_info,
    "environment": nanobot_info,
    "cron_jobs": [
        {"name": s["name"], "note": "see manifest.json for schedule"}
        for s in skills if s.get("has_cron")
    ],
    "backup_critical": [
        "SOUL.md", "IDENTITY.md", "USER.md", "AGENTS.md", "TOOLS.md",
        "HEARTBEAT.md", ".env", "location.json",
        "MEMORY.md", "memory/", "skills-data/"
    ]
}

# --- Write ---
output_path = os.path.join(SKILL_DATA, "blueprint.json")
with open(output_path, "w") as f:
    json.dump(blueprint, f, indent=2)

print(f"Blueprint written: {output_path}")
print(f"  Skills found: {len(skills)}")
print(f"  Skills-data dirs: {len(skills_data_contents)}")
print(f"  Identity files: {sum(1 for v in identity_files.values() if v['exists'])}/{len(identity_files)}")

# --- Record generation timestamp ---
# Write to skills-data (agent-writable) rather than skills/SKILL.md (protected)
timestamp_file = os.path.join(SKILL_DATA, "last-generated.txt")
with open(timestamp_file, "w") as f:
    f.write(now.strftime("%Y-%m-%d") + "\n")
print(f"Timestamp written: {timestamp_file}")

print("Done.")
