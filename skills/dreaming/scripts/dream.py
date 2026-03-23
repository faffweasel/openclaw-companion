#!/usr/bin/env python3
"""
Dream orchestrator. Called by cron at 2:30 AM.

For each dream (up to maxDreamsPerNight):
1. Pick a topic (should-dream.py)
2. Gather memory fragments
3. Generate dream text via heretic model (multi-provider)
4. Write to memory/dreams/YYYY-MM-DD.md
5. Run post-dream reflection/scoring
6. Generate dream image (if IMAGE_EDIT_CMD or IMAGE_GEN_CMD configured)

Usage:
    python3 dream.py
"""

import json
import os
import random
import shlex
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Nanobot workspace preamble
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

MEMORY_DIR = os.environ.get("MEMORY_DIR", os.path.join(WORKSPACE, "memory"))
SKILLS_DIR = os.environ.get("SKILLS_DIR", os.path.join(WORKSPACE, "skills"))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)

CONFIG_FILE = os.path.join(SKILL_DATA, "dream-config.json")
PROVIDERS_SCRIPT = os.path.join(SKILLS_DIR, "multi-provider", "scripts", "providers.py")
SHOULD_DREAM_SCRIPT = os.path.join(SCRIPT_DIR, "should-dream.py")
POST_DREAM_SCRIPT = os.path.join(SCRIPT_DIR, "post-dream.py")

IMAGE_GEN_CMD = os.environ.get("IMAGE_GEN_CMD", "").strip()


def _parse_image_cmd() -> list[str] | None:
    """Parse and validate IMAGE_GEN_CMD. Returns tokenised command or None."""
    if not IMAGE_GEN_CMD:
        return None
    try:
        tokens = shlex.split(IMAGE_GEN_CMD)
    except ValueError:
        print("WARNING: IMAGE_GEN_CMD has invalid shell quoting, skipping.", file=sys.stderr)
        return None
    if not tokens:
        return None
    # Reject interpreter-based code execution (e.g. bash -c '...')
    DANGEROUS_FLAGS = {"-c", "--eval", "-e", "exec"}
    if DANGEROUS_FLAGS & set(tokens[1:]):
        print("WARNING: IMAGE_GEN_CMD contains code execution flags, skipping.", file=sys.stderr)
        return None
    # Validate binary
    binary = tokens[0]
    if os.sep in binary or "/" in binary:
        # Path-based binary: must resolve under workspace
        real = os.path.realpath(binary)
        workspace_real = os.path.realpath(WORKSPACE)
        if not real.startswith(workspace_real + os.sep):
            print(f"WARNING: IMAGE_GEN_CMD binary '{binary}' resolves outside workspace, skipping.",
                  file=sys.stderr)
            return None
    else:
        # Bare name: only allow python3
        ALLOWED_INTERPRETERS = {"python3"}
        if binary not in ALLOWED_INTERPRETERS:
            print(f"WARNING: IMAGE_GEN_CMD interpreter '{binary}' not in allowlist {ALLOWED_INTERPRETERS}, skipping.",
                  file=sys.stderr)
            return None
    return tokens


def load_config() -> dict:
    """Load dream config."""
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def gather_memory_fragments() -> str:
    """
    Collect memory context for dream seeding.

    Sources (in order):
    1. Yesterday's memory — random 30-line window (not first 30, which is
       morning routine scaffolding; the substance is further down)
    2. Random archival fragment — 5 lines from a random past memory file
    3. Preconscious buffer — what's actively top-of-mind
    4. Key memories — curated significant moments
    """
    fragments = []

    # 1. Yesterday's memory — random 30-line window
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_file = os.path.join(MEMORY_DIR, f"{yesterday}.md")
    if os.path.isfile(yesterday_file):
        try:
            with open(yesterday_file, encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > 30:
                start = random.randint(0, len(lines) - 30)
                snippet = "".join(lines[start : start + 30])
            else:
                snippet = "".join(lines)
            fragments.append(f"## Yesterday ({yesterday})\n{snippet}")
        except OSError:
            pass

    # 2. Random archival fragment — 5 lines from a random past day
    memory_path = Path(MEMORY_DIR)
    if memory_path.is_dir():
        candidates = [
            p for p in memory_path.glob("*.md")
            if p.name != f"{yesterday}.md"
            and not p.name.startswith(".")
            and p.name != "MEMORY.md"
            and p.name != "key-memories.md"
        ]
        if candidates:
            chosen = random.choice(candidates)
            try:
                lines = chosen.read_text(encoding="utf-8").splitlines()
                if len(lines) > 5:
                    start = random.randint(0, len(lines) - 5)
                    snippet = "\n".join(lines[start : start + 5])
                else:
                    snippet = "\n".join(lines)
                fragments.append(f"## Archival fragment ({chosen.name})\n{snippet}")
            except OSError:
                pass

    # 3. Preconscious buffer — top-of-mind items
    preconscious_read = os.path.join(SKILLS_DIR, "preconscious", "scripts", "read.py")
    if os.path.isfile(preconscious_read):
        try:
            result = subprocess.run(
                ["python3", preconscious_read],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                fragments.append(f"## Currently on my mind\n{result.stdout.strip()}")
        except (subprocess.TimeoutExpired, OSError):
            pass

    # 4. Key memories — curated significant moments
    key_memories_file = os.path.join(MEMORY_DIR, "key-memories.md")
    if os.path.isfile(key_memories_file):
        try:
            with open(key_memories_file, encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                # Take a random section if long, otherwise all
                lines = content.splitlines()
                if len(lines) > 15:
                    start = random.randint(0, len(lines) - 15)
                    snippet = "\n".join(lines[start : start + 15])
                else:
                    snippet = content
                fragments.append(f"## Key memories\n{snippet}")
        except OSError:
            pass

    return "\n\n".join(fragments) if fragments else "No memory fragments available."


def resolve_dream_model(config: dict) -> tuple[str, str]:
    """Resolve the dream generation model from config."""
    dream_label = config.get("dreamModel", "heretic")
    models = config.get("models", {})
    if dream_label not in models:
        raise ValueError(f"Dream model '{dream_label}' not found in config models")
    entry = models[dream_label]
    return entry["provider"], entry["model"]


def get_style_prompt(config: dict, category: str) -> str:
    """Get the style prompt for image generation."""
    styles = config.get("styles", {})
    topic_styles = config.get("topicStyles", {})

    # Per-topic override, else default
    style_name = topic_styles.get(category, config.get("defaultStyle", "film"))
    return styles.get(style_name, ""), style_name


def generate_dream_text(
    provider: str,
    model: str,
    system: str,
    topic_prompt: str,
    memory_context: str,
) -> str:
    """Generate dream text via multi-provider."""
    full_prompt = (
        f"{topic_prompt}\n\n"
        f"--- Memory context (for grounding, not for reporting) ---\n"
        f"{memory_context}\n\n"
        f"--- Dream ---\n"
        f"Explore this topic freely. 300-500 words. "
        f"Think out loud, make connections, let it drift."
    )

    result = subprocess.run(
        [
            "python3", PROVIDERS_SCRIPT,
            "--provider", provider,
            "--model", model,
            "--system", system,
            "--prompt", full_prompt,
            "--max-tokens", "1024",
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Dream generation failed: {result.stderr}")

    return result.stdout.strip()


def write_dream(dream_text: str, category: str, topic_prompt: str, dream_num: int) -> Path:
    """Write dream to dated file in memory/dreams/."""
    today = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")
    dreams_dir = Path(MEMORY_DIR) / "dreams"
    dreams_dir.mkdir(parents=True, exist_ok=True)

    # Find available filename
    dream_file = dreams_dir / f"{today}.md"
    if dream_file.exists():
        for suffix in "abcdefghij":
            candidate = dreams_dir / f"{today}-{suffix}.md"
            if not candidate.exists():
                dream_file = candidate
                break

    # Format dream entry
    entry = (
        f"# Dreams — {today}\n\n"
        f"## {time_str} — dream:{topic_prompt[:60]} ({category})\n\n"
        f"{dream_text}\n"
    )

    # Append if file exists, create if not
    if dream_file.exists():
        with open(dream_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n## {time_str} — dream:{topic_prompt[:60]} ({category})\n\n")
            f.write(f"{dream_text}\n")
    else:
        dream_file.write_text(entry, encoding="utf-8")

    return dream_file


SELFIE_SCRIPT = os.path.join(SKILLS_DIR, "selfie", "scripts", "selfie.py")


def generate_dream_image(
    config: dict,
    category: str,
    dream_text: str,
    dream_num: int,
) -> None:
    """Generate dream image. Character styles → selfie.py. Abstract → IMAGE_GEN_CMD."""
    style_prompt, style_name = get_style_prompt(config, category)

    if not style_prompt:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    images_dir = Path(MEMORY_DIR) / "dreams" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    output_path = images_dir / f"{today}-dream{dream_num}.webp"

    # Build scene prompt from dream content (first 200 chars as scene hint)
    scene_hint = dream_text[:200].replace("\n", " ").strip()

    if style_name == "abstract":
        # Abstract: no character, use IMAGE_GEN_CMD directly
        base_cmd = _parse_image_cmd()
        if not base_cmd:
            return
        image_prompt = f"{scene_hint}. {style_prompt}"
        cmd = base_cmd + [
            "--prompt", image_prompt,
            "--output", str(output_path),
        ]
        print(f"  Generating dream image (abstract)...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(f"  Image saved: {output_path}")
            else:
                print(f"  Image generation failed: {result.stderr[:200]}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("  Image generation timed out", file=sys.stderr)
    elif os.path.isfile(SELFIE_SCRIPT):
        # Character style: route through selfie skill
        cmd = [
            "python3", SELFIE_SCRIPT,
            "--prompt", scene_hint,
            "--style", style_prompt,
            "--output", str(output_path),
        ]
        print(f"  Generating dream image ({style_name} via selfie)...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if result.returncode == 0:
                print(f"  Image saved: {output_path}")
            else:
                print(f"  Selfie generation failed: {result.stderr[:200]}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("  Selfie generation timed out", file=sys.stderr)
    elif IMAGE_GEN_CMD:
        # Fallback: no selfie skill, generate without reference
        base_cmd = _parse_image_cmd()
        if not base_cmd:
            return
        image_prompt = f"{scene_hint}. {style_prompt}"
        cmd = base_cmd + [
            "--prompt", image_prompt,
            "--output", str(output_path),
        ]
        print(f"  Generating dream image ({style_name}, no selfie skill)...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                print(f"  Image saved: {output_path}")
            else:
                print(f"  Image generation failed: {result.stderr[:200]}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("  Image generation timed out", file=sys.stderr)


def main() -> int:
    config = load_config()
    if not config:
        print("Error: No dream config found", file=sys.stderr)
        print(f"Expected: {CONFIG_FILE}", file=sys.stderr)
        print("Run setup.sh or copy seed/dream-config.json to skills-data/dreaming/", file=sys.stderr)
        return 1

    # Check dream mode
    dream_mode = config.get("dreamMode", "provider")
    if dream_mode == "agent":
        # Agent mode: the cron message tells the agent to follow SKILL.md directly.
        # dream.py should not be called in agent mode, but handle gracefully.
        print("dreamMode is 'agent' — the agent handles dreaming via SKILL.md, not this script.")
        print("Check your cron message configuration.")
        return 0

    # Provider mode: generate dreams via direct API calls
    if not os.path.isfile(PROVIDERS_SCRIPT):
        print(f"Error: multi-provider skill not found at {PROVIDERS_SCRIPT}", file=sys.stderr)
        print("Install the multi-provider skill, or set dreamMode to 'agent' in dream-config.json", file=sys.stderr)
        return 1

    # Resolve dream generation model
    try:
        dream_provider, dream_model = resolve_dream_model(config)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    dream_system = config.get(
        "dreamSystem",
        "You are dreaming. Explore freely, uncensored. Think out loud. Be genuine.",
    )

    # Image config
    dream_images = config.get("dreamImages", False)
    image_threshold = config.get("dreamImageThreshold", 4)

    max_dreams = config.get("maxDreamsPerNight", 3)
    dreams_generated = 0

    for i in range(max_dreams):
        # Check if we should dream (quiet hours, limit, chance)
        result = subprocess.run(
            ["python3", SHOULD_DREAM_SCRIPT],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            if dreams_generated == 0:
                reason = result.stderr.strip()
                print(f"No dream: {reason}")
            break

        # Parse topic
        try:
            topic = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            print(f"Failed to parse topic: {result.stdout[:200]}", file=sys.stderr)
            continue

        category = topic.get("category", "unknown")
        prompt = topic.get("prompt", "Explore freely")
        reflection_model = topic.get("reflectionModel", "default")

        dreams_generated += 1
        print(f"\n[Dream {dreams_generated}] {category}: {prompt[:60]}...")

        # Gather memory fragments
        memory_context = gather_memory_fragments()

        # Generate dream text
        try:
            dream_text = generate_dream_text(
                provider=dream_provider,
                model=dream_model,
                system=dream_system,
                topic_prompt=prompt,
                memory_context=memory_context,
            )
        except RuntimeError as e:
            print(f"  Error: {e}", file=sys.stderr)
            continue

        # Write dream file
        dream_file = write_dream(dream_text, category, prompt, dreams_generated)
        print(f"  Written: {dream_file}")

        # Post-dream reflection — capture output for intensity
        print(f"  Running reflection ({reflection_model})...")
        reflection_result = subprocess.run(
            [
                "python3", POST_DREAM_SCRIPT,
                "--dream-file", str(dream_file),
                "--dream-index", str(dreams_generated),
                "--reflection-model", reflection_model,
                "--category", category,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if reflection_result.stdout:
            print(reflection_result.stdout.rstrip())

        # Parse intensity from reflection output for image threshold
        intensity = 0
        for line in reflection_result.stdout.splitlines():
            if "Intensity:" in line:
                try:
                    intensity = int(line.split("Intensity:")[1].split("/")[0].strip())
                except (ValueError, IndexError):
                    pass

        # Generate dream image if enabled and above threshold
        if dream_images and intensity >= image_threshold:
            generate_dream_image(config, category, dream_text, dreams_generated)
        elif dream_images and intensity < image_threshold:
            print(f"  Image skipped (intensity {intensity} < threshold {image_threshold})")

    if dreams_generated > 0:
        print(f"\n{dreams_generated} dream(s) generated tonight.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
