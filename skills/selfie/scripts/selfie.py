#!/usr/bin/env python3
"""
selfie.py — Companion selfie skill.

Generate character-consistent images using a reference image and
IMAGE_EDIT_CMD. Mood-aware, setting-aware, prompt-engineered for
photorealistic output.

Called directly by the agent ("send a selfie") or by dreaming
for character dream images.

Usage:
    python3 selfie.py --prompt "at a night market, neon lights"
    python3 selfie.py --prompt "reading in bed" --mood intimate
    python3 selfie.py --prompt "in a forest clearing" --output memory/dreams/images/2026-03-22-dream1.webp
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Workspace detection
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

DATA_DIR = os.environ.get("DATA_DIR", os.path.join(WORKSPACE, "skills-data"))
SKILL_DATA = os.path.join(DATA_DIR, SKILL_NAME)
MEMORY_DIR = os.environ.get("MEMORY_DIR", os.path.join(WORKSPACE, "memory"))

IMAGE_EDIT_CMD = os.environ.get("IMAGE_EDIT_CMD", "").strip()

CONFIG_FILE = os.path.join(SKILL_DATA, "selfie-config.json")
PREFS_FILE = os.path.join(SKILL_DATA, "preferences.json")
DEFAULT_OUT_DIR = os.path.join(MEMORY_DIR, "selfies")

# ============================================================================
# MODE DETECTION
# ============================================================================

MODE_KEYWORDS = {
    "portrait": [
        "close-up", "face", "looking at you", "portrait", "headshot",
        "shoulders", "close",
    ],
    "scene": [
        "wide", "full scene", "landscape", "environment", "panorama",
        "view", "standing",
    ],
    "candid": [
        "reading", "working", "didn't notice", "unaware", "caught",
        "busy", "focused", "natural",
    ],
    "intimate": [
        "lying", "bed", "close", "soft", "warm", "intimate",
        "personal", "together",
    ],
}

# ============================================================================
# MOOD SYSTEM
# ============================================================================

MOOD_CONFIG = {
    "contemplative": {"expression_hint": "pensive expression"},
    "playful": {"expression_hint": "happy, slight smile"},
    "teasing": {"expression_hint": "confident smirk"},
    "intimate": {"expression_hint": "soft gaze"},
    "vulnerable": {"expression_hint": "unguarded expression"},
    "quiet": {"expression_hint": "calm expression"},
}

MOOD_KEYWORDS = {
    "contemplative": [
        "thinking", "thoughtful", "reflective", "gazing", "looking away",
        "serene", "peaceful",
    ],
    "playful": [
        "smile", "grin", "laugh", "fun", "play", "sparkle",
    ],
    "teasing": [
        "raised eyebrow", "smirk", "knowing", "challenge", "confident",
    ],
    "intimate": [
        "close", "warm", "soft", "together", "bed", "lying", "personal",
    ],
    "vulnerable": [
        "raw", "open", "unguarded", "bare", "honest", "real",
    ],
    "quiet": [
        "still", "calm", "quiet", "silent", "minimal", "subdued",
    ],
}

# ============================================================================
# CONFIG
# ============================================================================


def load_config() -> dict:
    """Load selfie config from skills-data."""
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
            # Resolve ${WORKSPACE} in reference image paths
            refs = data.get("referenceImages", {})
            for key in refs:
                refs[key] = refs[key].replace("${WORKSPACE}", WORKSPACE)
            return data
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def load_preferences() -> dict:
    """Load selfie preferences."""
    if os.path.isfile(PREFS_FILE):
        try:
            with open(PREFS_FILE, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "favorite_moods": [],
        "favorite_settings": [],
        "generated_count": 0,
        "last_generated": None,
    }


def save_preferences(prefs: dict) -> None:
    """Save selfie preferences."""
    os.makedirs(os.path.dirname(PREFS_FILE), exist_ok=True)
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)


def update_preferences(mood: str, setting: str | None) -> None:
    """Track what gets generated."""
    prefs = load_preferences()
    prefs["generated_count"] = prefs.get("generated_count", 0) + 1
    prefs["last_generated"] = datetime.now().isoformat()
    if mood:
        prefs.setdefault("favorite_moods", []).append(mood)
    if setting:
        prefs.setdefault("favorite_settings", []).append(setting)
    save_preferences(prefs)


# ============================================================================
# DETECTION
# ============================================================================


def detect_mode(prompt: str) -> str:
    """Auto-detect selfie mode from prompt keywords."""
    p = prompt.lower()
    scores = {mode: 0 for mode in MODE_KEYWORDS}
    for mode, keywords in MODE_KEYWORDS.items():
        for kw in keywords:
            if kw in p:
                scores[mode] += 1
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "portrait"


def detect_mood(prompt: str) -> str:
    """Auto-detect mood from prompt keywords."""
    p = prompt.lower()
    scores = {mood: 0 for mood in MOOD_KEYWORDS}
    for mood, keywords in MOOD_KEYWORDS.items():
        for kw in keywords:
            if kw in p:
                scores[mood] += 1
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return "contemplative"


# ============================================================================
# PROMPT ENGINEERING
# ============================================================================


def sanitize_prompt(prompt: str) -> str:
    """Remove viewer-presence phrases that would put a second person in frame."""
    viewer_patterns = [
        r"you'?re?\s+watching[^.]*[.,]?\s*",
        r"you\s+watch(?:ing)?[^.]*[.,]?\s*",
        r"you\s+seeing[^.]*[.,]?\s*",
        r"you\s+look(?:ing)?[^.]*[.,]?\s*",
        r"you\s+on\s+the[^.]*[.,]?\s*",
        r"you\s+standing[^.]*[.,]?\s*",
        r"he'?s?\s+watching[^.]*[.,]?\s*",
        r"he\s+watch(?:ing)?[^.]*[.,]?\s*",
        r"someone\s+watching[^.]*[.,]?\s*",
        r"watched\s+by[^.]*[.,]?\s*",
    ]
    result = prompt
    for pattern in viewer_patterns:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    return result.strip()


def extract_clothing_from_prompt(prompt: str) -> str | None:
    """Extract clothing mentioned in prompt."""
    patterns = [
        r"wearing\s+([^,.]+)",
        r"in\s+(?:a|the)\s+([^,.]+(?:dress|shirt|jacket|sweater|top|jeans|pants|shorts|skirt|outfit)[^,.]*)",
        r"\b([^,.]*(?:dungarees|overalls|kimono|yukata|hoodie|cardigan|blazer)[^,.]*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt.lower())
        if match:
            return match.group(1).strip()
    return None


def parse_clothing_modifiers(clothing: str) -> tuple[str, list[str]]:
    """Parse clothing for modifiers like 'nothing underneath', 'barefoot'."""
    modifiers = []
    modifier_patterns = [
        (r"(?:nothing|no\s+\w+)\s+underneath", "nothing underneath"),
        (r"barefoot", "barefoot"),
        (r"without\s+(?:a\s+)?jacket", "without jacket"),
    ]
    for pattern, mod_name in modifier_patterns:
        if re.search(pattern, clothing.lower()):
            modifiers.append(mod_name)
    return clothing, modifiers


def infer_clothing(config: dict, setting: str | None, mood: str, prompt: str) -> str:
    """Infer appropriate clothing from context."""
    p = prompt.lower()

    # Prompt-level minimal clothing hints
    minimal_hints = ["towel", "nothing", "bare ", "barefoot", "stepping in",
                     "slipping off", "let go", "surrender"]
    if any(kw in p for kw in minimal_hints):
        if any(w in p for w in ["onsen", "pool", "water", "bath"]):
            return "minimal damp white yukata loosely draped, barefoot"

    # Mood-based inference
    mood_map = {
        "vulnerable": "minimal comfortable clothing, natural",
        "intimate": "comfortable minimal clothing, relaxed layers",
        "playful": "fun casual outfit, easy to move in",
        "contemplative": "comfortable understated clothing",
        "teasing": "deliberate casual outfit, something chosen on purpose",
        "quiet": "simple soft clothing, no statement",
    }
    if mood in mood_map:
        return mood_map[mood]

    return config.get("appearance", {}).get("defaultClothing", "casual comfortable clothing")


def build_setting_context(config: dict, setting: str | None, prompt: str) -> str:
    """Build background/setting context from config or prompt."""
    settings = config.get("settings", {})

    if setting and setting in settings:
        return settings[setting]

    # Check if a configured setting is mentioned in prompt
    p = prompt.lower()
    for key, desc in settings.items():
        if key in p:
            return desc

    return config.get("defaultSetting", "neutral warm interior, soft lighting")


def build_prompt(
    config: dict,
    user_prompt: str,
    mode: str,
    mood: str,
    setting: str | None,
    clothing_override: str | None,
    style_override: str | None,
) -> str:
    """
    Build a natural-language edit prompt. Five parts max:
    1. Face anchor (specific physical descriptors)
    2. Clothing
    3. Scene (user prompt + expression hint)
    4. Only one person guard
    5. Signature element (conditional)

    No structured key:value labels — reads like a scene description.
    """
    appearance = config.get("appearance", {})
    mood_config = MOOD_CONFIG.get(mood, MOOD_CONFIG["contemplative"])

    # 1. Face anchor — FIRST, most important
    face_anchor = appearance.get(
        "faceAnchor",
        "Same person, keep exact face, same round glasses, same short dark hair",
    )

    # 2. Clothing
    if clothing_override:
        clothing = clothing_override
    else:
        extracted = extract_clothing_from_prompt(user_prompt)
        clothing = extracted or infer_clothing(config, setting, mood, user_prompt)

    # 3. Scene — user prompt (sanitized) + expression hint
    clean_prompt = sanitize_prompt(user_prompt)
    expression_hint = mood_config.get("expression_hint", "")
    if expression_hint:
        scene = f"{clean_prompt}, {expression_hint}"
    else:
        scene = clean_prompt

    # 4. Only one person
    guard = "Only one person"

    # 5. Signature element (conditional on mood)
    sig = config.get("signatureElement", {})
    sig_text = ""
    if sig.get("enabled") and mood in sig.get("moods", []):
        sig_text = sig.get("description", "")

    # Assemble as natural language
    parts = [face_anchor, clothing, scene, guard]

    # Photo style — optional, from config or --style override
    photo_style = style_override or config.get("photoStyle", "")
    if photo_style:
        parts.append(photo_style)

    if sig_text:
        parts.append(sig_text)

    return ". ".join(parts)


# ============================================================================
# GENERATION
# ============================================================================


def resolve_reference_image(config: dict, mode: str) -> str | None:
    """Pick the right reference image based on mode."""
    refs = config.get("referenceImages", {})

    # Portrait/intimate → face reference; scene/candid → body reference
    if mode in ("portrait", "intimate"):
        primary = refs.get("portrait", "")
        fallback = refs.get("body", "")
    else:
        primary = refs.get("body", "")
        fallback = refs.get("portrait", "")

    # Also check env vars
    env_portrait = os.environ.get("COMPANION_REFERENCE_PORTRAIT", "").strip()
    env_body = os.environ.get("COMPANION_REFERENCE_BODY", "").strip()
    env_generic = os.environ.get("COMPANION_REFERENCE_IMAGE", "").strip()

    # Priority: config → env specific → env generic → fallback
    for candidate in [primary, env_portrait if mode in ("portrait", "intimate") else env_body,
                      fallback, env_generic]:
        if candidate and os.path.isfile(candidate):
            return candidate

    return None


def slugify(text: str) -> str:
    """Convert text to filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text[:50]


def generate_selfie(
    config: dict,
    user_prompt: str,
    mode: str | None,
    mood: str | None,
    setting: str | None,
    clothing: str | None,
    style: str | None,
    output: str | None,
    out_dir: str | None,
) -> str | None:
    """Generate a selfie image. Returns output path or None on failure."""

    if not IMAGE_EDIT_CMD:
        print("Error: IMAGE_EDIT_CMD not configured in .env", file=sys.stderr)
        return None

    # Auto-detect mode and mood
    if mode is None:
        mode = detect_mode(user_prompt)
    if mood is None:
        mood = detect_mood(user_prompt)

    # Find reference image
    ref_image = resolve_reference_image(config, mode)
    if not ref_image:
        print("Error: No reference image found.", file=sys.stderr)
        print("Configure in selfie-config.json or set COMPANION_REFERENCE_IMAGE in .env", file=sys.stderr)
        return None

    # Build prompt
    edit_prompt = build_prompt(config, user_prompt, mode, mood, setting, clothing, style)

    # Resolve output path (extension is a hint — venice-edit may correct it)
    if output:
        out_path = output
    else:
        dir_path = out_dir or DEFAULT_OUT_DIR
        os.makedirs(dir_path, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        desc = slugify(user_prompt)
        out_path = os.path.join(dir_path, f"{date_str}-{mood}-{desc}.png")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Call IMAGE_EDIT_CMD
    cmd = IMAGE_EDIT_CMD.split() + [
        "--input", ref_image,
        "--prompt", edit_prompt,
        "--output", out_path,
    ]

    print(f"Generating selfie ({mode}, {mood})...")
    print(f"  Reference: {os.path.basename(ref_image)}")
    print(f"  Setting: {setting or 'auto'}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    if result.returncode != 0:
        print(f"Error: IMAGE_EDIT_CMD failed:\n{result.stderr}", file=sys.stderr)
        return None

    # Parse actual output path from MEDIA: line (extension may have been corrected)
    actual_path = out_path
    for line in result.stdout.splitlines():
        if line.startswith("MEDIA:"):
            actual_path = line.split("MEDIA:", 1)[1].strip()
            print(line)

    print(f"Saved: {actual_path}")

    # Track preferences
    update_preferences(mood, setting)

    return actual_path


# ============================================================================
# CLI
# ============================================================================


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate companion selfie via reference image editing"
    )
    ap.add_argument("--prompt", required=True, help="Scene description")
    ap.add_argument(
        "--mode", choices=["portrait", "scene", "candid", "intimate"],
        help="Selfie mode (auto-detected if not set)",
    )
    ap.add_argument(
        "--mood", choices=list(MOOD_CONFIG.keys()),
        help="Photo mood (auto-detected if not set)",
    )
    ap.add_argument("--setting", help="Background setting (from selfie-config.json)")
    ap.add_argument("--clothing", help="Override clothing description")
    ap.add_argument("--style", help="Override photo style (replaces config photoStyle)")
    ap.add_argument("--output", "-o", help="Output file path (overrides --out-dir)")
    ap.add_argument("--out-dir", help=f"Output directory (default: memory/selfies/)")
    args = ap.parse_args()

    config = load_config()
    if not config:
        print("Warning: No selfie config found, using defaults", file=sys.stderr)
        print(f"Expected: {CONFIG_FILE}", file=sys.stderr)

    result = generate_selfie(
        config=config,
        user_prompt=args.prompt,
        mode=args.mode,
        mood=args.mood,
        setting=args.setting,
        clothing=args.clothing,
        style=args.style,
        output=args.output,
        out_dir=args.out_dir,
    )

    return 0 if result else 1


if __name__ == "__main__":
    raise SystemExit(main())
