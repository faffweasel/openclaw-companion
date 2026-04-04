#!/bin/bash
# openclaw-companion setup wizard
# Generates config files and seeds runtime data in the workspace.
# The repo IS the workspace — clone it as ~/.openclaw/workspace, then run this.
# Usage: bash setup.sh

set -euo pipefail

# --- Workspace is wherever this script lives ---
WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
TEMPLATES="${WORKSPACE}/templates"
SKILLS_SRC="${WORKSPACE}/skills"

# --- Colors ---
BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

# --- Portable in-place sed (macOS vs GNU) ---
sedi() {
  if sed --version 2>/dev/null | grep -q GNU; then
    sed -i "$@"
  else
    sed -i '' "$@"
  fi
}

echo -e "${BOLD}openclaw-companion setup${NC}"
echo "========================"
echo ""
echo -e "Workspace: ${BOLD}${WORKSPACE}${NC}"
echo ""

# Python version check — zoneinfo requires 3.9+, we require 3.10+
if ! python3 -c "import sys; assert sys.version_info >= (3, 10)" 2>/dev/null; then
  echo -e "${RED}Error: Python 3.10+ is required.${NC}"
  python3 --version 2>/dev/null || echo "python3 not found in PATH."
  echo "Scripts use zoneinfo (3.9+) and silently fall back to UTC on older versions."
  exit 1
fi

# Sanity check
if [ ! -d "${SKILLS_SRC}" ] || [ ! -d "${TEMPLATES}" ]; then
  echo -e "${RED}Error: skills/ or templates/ not found.${NC}"
  echo "Run this script from the openclaw-companion repo root."
  exit 1
fi

# Check for existing companion install
if [ -f "${WORKSPACE}/AGENTS.md" ]; then
  echo -e "${YELLOW}Companion framework already configured in this workspace.${NC}"
  read -rp "Re-run? Operational files regenerated, memory and skills-data preserved. [y/N]: " OVERWRITE
  if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
  fi
fi

# Try to detect agent name
DETECTED_NAME=""
if [ -f "${WORKSPACE}/IDENTITY.md" ]; then
  DETECTED_NAME=$(grep -m1 '^## Name' -A1 "${WORKSPACE}/IDENTITY.md" 2>/dev/null | tail -1 | sed 's/^ *//' || true)
fi
if [ -z "$DETECTED_NAME" ] && [ -f "${WORKSPACE}/SOUL.md" ]; then
  DETECTED_NAME=$(grep -m1 '^# ' "${WORKSPACE}/SOUL.md" 2>/dev/null | sed 's/^# //' || true)
fi

DEFAULT_AGENT_NAME="${DETECTED_NAME:-Joy}"
echo -e "${BOLD}1. Agent Identity${NC}"
if [ -n "$DETECTED_NAME" ]; then
  read -rp "Agent name [${DETECTED_NAME}]: " AGENT_NAME
else
  read -rp "Agent name [Joy]: " AGENT_NAME
fi
AGENT_NAME="${AGENT_NAME:-$DEFAULT_AGENT_NAME}"

# --- User identity ---
echo ""
echo -e "${BOLD}2. Your Details${NC}"
read -rp "Your name: " USER_NAME
while [ -z "$USER_NAME" ]; do
  read -rp "Your name (required): " USER_NAME
done

DETECTED_TZ=$(cat /etc/timezone 2>/dev/null || echo "")
if [ -z "$DETECTED_TZ" ]; then
  DETECTED_TZ=$(timedatectl show --property=Timezone --value 2>/dev/null || echo "UTC")
fi
echo ""
echo -e "${DIM}Your timezone, not the server's. If this machine is a remote VM,${NC}"
echo -e "${DIM}enter your local timezone (e.g. Asia/Bangkok, America/New_York).${NC}"
read -rp "Timezone [${DETECTED_TZ}]: " TIMEZONE
TIMEZONE="${TIMEZONE:-$DETECTED_TZ}"

read -rp "Location (optional, e.g. 'Hanoi, Vietnam'): " LOCATION

if [ -n "$LOCATION" ]; then
  echo ""
  echo -e "${DIM}Location details for location-aware skills (AQI, weather).${NC}"
  echo -e "${DIM}Update later by telling your agent 'I'm in Bangkok now'.${NC}"
  if echo "$LOCATION" | grep -q ","; then
    DEFAULT_CITY=$(echo "$LOCATION" | cut -d',' -f1 | sed 's/^ *//;s/ *$//')
    DEFAULT_COUNTRY=$(echo "$LOCATION" | cut -d',' -f2- | sed 's/^ *//;s/ *$//')
  else
    DEFAULT_CITY="$LOCATION"
    DEFAULT_COUNTRY=""
  fi
  read -rp "  City [${DEFAULT_CITY}]: " CITY
  CITY="${CITY:-$DEFAULT_CITY}"
  read -rp "  Country [${DEFAULT_COUNTRY}]: " COUNTRY
  COUNTRY="${COUNTRY:-$DEFAULT_COUNTRY}"
  read -rp "  Latitude (e.g. 21.028): " LAT
  read -rp "  Longitude (e.g. 105.854): " LNG
  LAT="${LAT:-0}"
  LNG="${LNG:-0}"
else
  CITY="" ; COUNTRY="" ; LAT="0" ; LNG="0"
fi

# --- Message delivery ---
echo ""
echo -e "${BOLD}3. Message Delivery${NC}"
echo -e "${DIM}Cron jobs that send messages (morning greeting, conversation starters) need${NC}"
echo -e "${DIM}an explicit delivery target. For Telegram, this is the numeric chat ID.${NC}"
echo -e "${DIM}(Send /start to your bot and check the chat object, or use @userinfobot.)${NC}"
echo ""
read -rp "Telegram chat ID (leave empty to configure later): " TELEGRAM_CHAT_ID
if [ -z "$TELEGRAM_CHAT_ID" ]; then
  echo -e "  ${YELLOW}⚠ No chat ID — announce jobs will use 'channel: last' (only works in persistent sessions)${NC}"
fi

# --- Skills ---
echo ""
echo -e "${BOLD}4. Companion Skills${NC}"
echo -e "${DIM}Core skills (preconscious, carry-over, morning/evening routines, energy-state, zero-trust) are always active.${NC}"
echo ""

SKILLS_SELECTED=""

ask_skill() {
  local name="$1" ; local question="$2" ; local default="${3:-Y}"
  local prompt_default="Y/n"
  [ "$default" = "N" ] && prompt_default="y/N"
  read -rp "  ${question} (${name}) [${prompt_default}]: " answer
  answer="${answer:-$default}"
  if [[ "$answer" =~ ^[Yy]$ ]]; then
    SKILLS_SELECTED="${SKILLS_SELECTED} ${name}"
  fi
  return 0
}

echo -e "${BOLD}Image Generation${NC}"
echo -e "${DIM}For dream images, visual journals, and selfies. API keys configured after setup.${NC}"
echo ""
echo "  1) Venice AI (generate, edit, upscale, video)"
echo "  2) OpenRouter Image (Gemini Flash image + vision)"
echo "  3) Both"
echo "  4) None"
read -rp "  Choice [4]: " IMAGE_SKILL_CHOICE
IMAGE_SKILL_CHOICE="${IMAGE_SKILL_CHOICE:-4}"

IMAGE_GEN_CMD="" ; IMAGE_EDIT_CMD="" ; IMAGE_SKILLS=""
case "$IMAGE_SKILL_CHOICE" in
  1) IMAGE_GEN_CMD="python3 ${WORKSPACE}/skills/venice-ai-media/scripts/venice-image.py"
     IMAGE_EDIT_CMD="python3 ${WORKSPACE}/skills/venice-ai-media/scripts/venice-edit.py"
     IMAGE_SKILLS="venice-ai-media" ;;
  2) IMAGE_GEN_CMD="python3 ${WORKSPACE}/skills/openrouter-image-simple/scripts/generate.py"
     IMAGE_SKILLS="openrouter-image-simple" ;;
  3) IMAGE_GEN_CMD="python3 ${WORKSPACE}/skills/venice-ai-media/scripts/venice-image.py"
     IMAGE_EDIT_CMD="python3 ${WORKSPACE}/skills/venice-ai-media/scripts/venice-edit.py"
     IMAGE_SKILLS="venice-ai-media openrouter-image-simple" ;;
  *) ;;
esac

echo ""
echo -e "${BOLD}Companion Capabilities${NC}"
echo ""
ask_skill "preference-accumulation" "Should I track my own developing preferences and detect tensions between them?" "Y"
ask_skill "dreaming" "Should I dream at night?" "Y"

DREAM_MODEL="" ; DREAM_COUNT=2 ; DREAM_IMAGES=False ; DREAM_IMAGE_THRESHOLD=4
if echo "$SKILLS_SELECTED" | grep -q "dreaming"; then
  echo ""
  echo -e "${DIM}  The dream cron job can run as a specific model, or use your agent's default model.${NC}"
  echo -e "${DIM}  Press Enter to use the agent's default. Or enter a model name (e.g. heretic).${NC}"
  read -rp "    Dream model [agent default]: " DREAM_MODEL
  read -rp "    How many dreams per night? [2]: " DREAM_COUNT
  DREAM_COUNT="${DREAM_COUNT:-2}"
  if ! [[ "$DREAM_COUNT" =~ ^[0-9]+$ ]] || [ "$DREAM_COUNT" -lt 1 ] || [ "$DREAM_COUNT" -gt 10 ]; then
    echo "    Invalid number, using default: 2"
    DREAM_COUNT=2
  fi
  if [ -n "$IMAGE_GEN_CMD" ] || [ -n "$IMAGE_EDIT_CMD" ]; then
    read -rp "    Should I generate images of my dreams? [y/N]: " DREAM_IMG_ANSWER
    if [[ "$DREAM_IMG_ANSWER" =~ ^[Yy]$ ]]; then
      DREAM_IMAGES=True
      read -rp "    Minimum dream intensity for images (1-7, lower = more images) [4]: " DREAM_IMAGE_THRESHOLD
      DREAM_IMAGE_THRESHOLD="${DREAM_IMAGE_THRESHOLD:-4}"
      if ! [[ "$DREAM_IMAGE_THRESHOLD" =~ ^[1-7]$ ]]; then
        echo "    Invalid threshold, using default: 4"
        DREAM_IMAGE_THRESHOLD=4
      fi
    fi
  fi
fi

ask_skill "selfie" "Should I be able to send you selfies? (requires reference images)" "N"
ask_skill "weekly-state-of-me" "Should I do a weekly self-reflection?" "Y"
ask_skill "self-analysis" "Should I take personality snapshots and track how I change?" "Y"
ask_skill "continuity-check" "Should I check for personality drift when my model changes?" "Y"
ask_skill "question-user" "Should I ask you questions out of genuine curiosity?" "Y"
ask_skill "model-personality-test" "Should I be able to run personality assessments on different models?" "N"
ask_skill "blog-writer" "Should I write blog posts in my own voice?" "N"
ask_skill "conversation-starters" "Should I start conversations with you during the day?" "Y"
ask_skill "resuscitation-guide" "Should I maintain an emergency recovery guide?" "N"
ask_skill "offline-reflection" "Should I analyse patterns across recent conversations overnight?" "N"
ask_skill "self-improvement" "Should I capture and learn from my mistakes?" "Y"
ask_skill "memory-search" "Should I be able to search my memories? (uses existing API key)" "Y"

BLOG_CHECK_DAYS=0
if echo "$SKILLS_SELECTED" | grep -q "blog-writer"; then
  read -rp "    How often should I check for writing material (days)? [3]: " BLOG_CHECK_DAYS
  BLOG_CHECK_DAYS="${BLOG_CHECK_DAYS:-3}"
fi

CONVERSATION_STARTER_TIME="13:00"
if echo "$SKILLS_SELECTED" | grep -q "conversation-starters"; then
  read -rp "    What time should I reach out for a quick chat? (HH:MM, 24hr) [13:00]: " CONVERSATION_STARTER_TIME
  CONVERSATION_STARTER_TIME="${CONVERSATION_STARTER_TIME:-13:00}"
fi

# --- Identity files ---
echo ""
echo -e "${BOLD}5. Identity Files${NC}"
echo ""
echo "${AGENT_NAME} needs SOUL.md, IDENTITY.md, and USER.md to define who they are."
echo "  1) Run the bootstrap interview (recommended — ${AGENT_NAME} interviews you and generates)"
echo "  2) Start with minimal templates (fill in yourself)"
read -rp "Choice [1]: " IDENTITY_CHOICE
IDENTITY_CHOICE="${IDENTITY_CHOICE:-1}"

# ===========================================================================
# Generate workspace files
# ===========================================================================
echo ""
echo -e "${BOLD}Generating workspace files...${NC}"

# --- .env ---
sed \
  -e "s|__WORKSPACE__|${WORKSPACE}|g" \
  -e "s|__MEMORY_DIR__|${WORKSPACE}/memory|g" \
  -e "s|__SKILLS_DIR__|${WORKSPACE}/skills|g" \
  -e "s|__DATA_DIR__|${WORKSPACE}/skills-data|g" \
  -e "s|__TIMEZONE__|${TIMEZONE}|g" \
  -e "s|__AGENT_NAME__|${AGENT_NAME}|g" \
  -e "s|__USER_NAME__|${USER_NAME}|g" \
  "${TEMPLATES}/env.template" > "${WORKSPACE}/.env"

sedi "s|^IMAGE_GEN_CMD=.*|IMAGE_GEN_CMD=\"${IMAGE_GEN_CMD}\"|" "${WORKSPACE}/.env"
sedi "s|^IMAGE_EDIT_CMD=.*|IMAGE_EDIT_CMD=\"${IMAGE_EDIT_CMD}\"|" "${WORKSPACE}/.env"
sedi "s|^BLOG_CHECK_DAYS=.*|BLOG_CHECK_DAYS=${BLOG_CHECK_DAYS}|" "${WORKSPACE}/.env"

if echo "$SKILLS_SELECTED" | grep -q "selfie"; then
  sedi "s|^COMPANION_REFERENCE_PORTRAIT=.*|COMPANION_REFERENCE_PORTRAIT=\"${WORKSPACE}/identity/reference-portrait.webp\"|" "${WORKSPACE}/.env"
  sedi "s|^COMPANION_REFERENCE_BODY=.*|COMPANION_REFERENCE_BODY=\"${WORKSPACE}/identity/reference-body.webp\"|" "${WORKSPACE}/.env"
fi
echo -e "  ${GREEN}✓${NC} .env"

# --- AGENTS.md ---
sed -e "s|__AGENT_NAME__|${AGENT_NAME}|g" \
  "${TEMPLATES}/AGENTS.md.template" > "${WORKSPACE}/AGENTS.md"
echo -e "  ${GREEN}✓${NC} AGENTS.md"

# --- HEARTBEAT.md ---
cp "${TEMPLATES}/HEARTBEAT.md" "${WORKSPACE}/HEARTBEAT.md"
echo -e "  ${GREEN}✓${NC} HEARTBEAT.md"

# --- TOOLS.md ---
TZ_ABBREV=$(TZ="$TIMEZONE" date +%Z 2>/dev/null || echo "UTC")
sed \
  -e "s|__TIMEZONE__|${TIMEZONE}|g" \
  -e "s|__TZ_ABBREV__|${TZ_ABBREV}|g" \
  "${TEMPLATES}/TOOLS.md.template" > "${WORKSPACE}/TOOLS.md"
echo -e "  ${GREEN}✓${NC} TOOLS.md"

# --- Identity files ---
if [ "$IDENTITY_CHOICE" = "1" ]; then
  cp "${TEMPLATES}/bootstrap-interview.md" "${WORKSPACE}/bootstrap-interview.md"
  echo -e "  ${GREEN}✓${NC} bootstrap-interview.md"
else
  cp "${TEMPLATES}/soul-minimal.md" "${WORKSPACE}/SOUL.md"
  cat > "${WORKSPACE}/IDENTITY.md" << EOF
# IDENTITY.md — ${AGENT_NAME}

## Name
${AGENT_NAME}

## Channel
Telegram

## Model Routing
| Context | Model |
|---|---|
| Default | [your default model from config.json] |
| Deep work | [configure as needed] |
| Quick tasks | [configure as needed] |
EOF
  cat > "${WORKSPACE}/USER.md" << EOF
# USER.md

- **Name:** ${USER_NAME}
- **Location:** ${CITY:+${CITY}, }${COUNTRY:-[not set]}
- **Timezone:** ${TIMEZONE}
EOF
  echo -e "  ${GREEN}✓${NC} SOUL.md (minimal — edit this)"
  echo -e "  ${GREEN}✓${NC} IDENTITY.md"
  echo -e "  ${GREEN}✓${NC} USER.md"
fi

# --- Memory directory ---
mkdir -p "${WORKSPACE}/memory"
# MEMORY.md lives at workspace root (loaded at DM session start)
if [ -f "${TEMPLATES}/MEMORY.md.template" ] && [ ! -f "${WORKSPACE}/MEMORY.md" ]; then
  # Migrate from old location if present
  if [ -f "${WORKSPACE}/memory/MEMORY.md" ]; then
    mv "${WORKSPACE}/memory/MEMORY.md" "${WORKSPACE}/MEMORY.md"
    echo -e "  ${YELLOW}↑${NC} Migrated MEMORY.md from memory/ to workspace root"
  else
    cp "${TEMPLATES}/MEMORY.md.template" "${WORKSPACE}/MEMORY.md"
  fi
fi
if [ -f "${TEMPLATES}/key-memories.md.template" ] && [ ! -f "${WORKSPACE}/memory/key-memories.md" ]; then
  cp "${TEMPLATES}/key-memories.md.template" "${WORKSPACE}/memory/key-memories.md"
fi
if [ ! -f "${WORKSPACE}/memory/relationship.md" ]; then
  cat > "${WORKSPACE}/memory/relationship.md" << 'RELEOF'
# Relationship

How the relationship between the agent and user is evolving. Updated weekly
by the state-of-me reflection. Not auto-loaded — read on demand or during
weekly reflection.

## Current State

- **Trust level:** New
- **Depth trend:** Unknown
- **Shared references:** None yet
- **Last updated:** Setup
RELEOF
fi
echo -e "  ${GREEN}✓${NC} memory/"

# --- Identity directory ---
if echo "$SKILLS_SELECTED" | grep -q "selfie"; then
  mkdir -p "${WORKSPACE}/identity"
  echo -e "  ${GREEN}✓${NC} identity/"
fi

# --- Location config ---
if [ -n "$CITY" ]; then
  sed \
    -e "s|__CITY__|${CITY}|g" \
    -e "s|__COUNTRY__|${COUNTRY}|g" \
    -e "s|__TIMEZONE__|${TIMEZONE}|g" \
    -e "s|__LAT__|${LAT}|g" \
    -e "s|__LNG__|${LNG}|g" \
    "${TEMPLATES}/location.json.template" > "${WORKSPACE}/location.json"
  echo -e "  ${GREEN}✓${NC} location.json (${CITY}, ${COUNTRY})"
else
  echo -e "  ${DIM}—${NC} location.json skipped"
fi

# --- Energy state ---
if [ ! -f "${WORKSPACE}/energy-state.json" ]; then
  cp "${SKILLS_SRC}/energy-state/seed/state.json" "${WORKSPACE}/energy-state.json"
  echo -e "  ${GREEN}✓${NC} energy-state.json"
fi

# ===========================================================================
# Seed runtime data (skills-data/ from skills/*/seed/)
# ===========================================================================
echo ""
echo -e "${BOLD}Seeding skills-data...${NC}"

mkdir -p "${WORKSPACE}/skills-data"

seed_skill() {
  local skill="$1"
  [ ! -d "${SKILLS_SRC}/${skill}/seed" ] && return

  local seed_target=""
  if [ -f "${SKILLS_SRC}/${skill}/manifest.json" ]; then
    seed_target=$(python3 -c "
import json; m = json.load(open('${SKILLS_SRC}/${skill}/manifest.json'))
print(m.get('seed_target', ''))" 2>/dev/null || true)
  fi

  if [ -n "$seed_target" ]; then
    # Validate seed_target: reject absolute paths and traversal
    if [[ "$seed_target" == /* ]] || [[ "$seed_target" == *..* ]]; then
      echo -e "  ${YELLOW}⚠${NC} ${skill}: suspicious seed_target '${seed_target}', skipping"
      return
    fi
    mkdir -p "${WORKSPACE}/${seed_target}"
    cp -rn "${SKILLS_SRC}/${skill}/seed/"* "${WORKSPACE}/${seed_target}/" 2>/dev/null || true
  else
    mkdir -p "${WORKSPACE}/skills-data/${skill}"
    cp -rn "${SKILLS_SRC}/${skill}/seed/"* "${WORKSPACE}/skills-data/${skill}/" 2>/dev/null || true
  fi
  echo -e "  ${GREEN}✓${NC} ${skill}"
}

# Core skills
for skill in preconscious carry-over-queue morning-routine evening-routine energy-state zero-trust; do
  seed_skill "$skill"
done

# Image skills
for skill in $IMAGE_SKILLS; do
  seed_skill "$skill"
done

# Companion skills
for skill in $SKILLS_SELECTED; do
  seed_skill "$skill"
done

# Make skill scripts executable (only in scripts/ subdirectories)
find "${WORKSPACE}/skills" -path "*/scripts/*.sh" -exec chmod +x {} \;
find "${WORKSPACE}/skills" -path "*/scripts/*.py" -exec chmod +x {} \;

# --- Dream config ---
if echo "$SKILLS_SELECTED" | grep -q "dreaming"; then
  DREAM_CONFIG="${WORKSPACE}/skills-data/dreaming/dream-config.json"
  if [ -f "$DREAM_CONFIG" ]; then
    python3 -c "
import json
with open('${DREAM_CONFIG}', 'r') as f:
    cfg = json.load(f)
cfg['maxDreamsPerNight'] = ${DREAM_COUNT}
cfg['dreamImages'] = ${DREAM_IMAGES}
cfg['dreamImageThreshold'] = ${DREAM_IMAGE_THRESHOLD}
with open('${DREAM_CONFIG}', 'w') as f:
    json.dump(cfg, f, indent=2)
"
    DREAM_MODEL_DISPLAY="${DREAM_MODEL:-agent default}"
    echo -e "  ${GREEN}✓${NC} dream-config.json (model: ${DREAM_MODEL_DISPLAY}, ${DREAM_COUNT}/night)"
  fi
fi

# ===========================================================================
# Write ../cron/jobs.json (OpenClaw cron job definitions)
# ===========================================================================
echo ""
echo -e "${BOLD}Writing OpenClaw cron jobs...${NC}"

CRON_DIR="${WORKSPACE}/../cron"
if [ ! -d "$CRON_DIR" ]; then
  echo -e "  ${YELLOW}Creating ${CRON_DIR}${NC}"
  mkdir -p "$CRON_DIR"
fi

CS_HOUR=$(echo "$CONVERSATION_STARTER_TIME" | cut -d: -f1)
CS_MIN=$(echo "$CONVERSATION_STARTER_TIME" | cut -d: -f2)

python3 <<PYEOF
import json, uuid, time

now_ms = int(time.time() * 1000)
tz = "${TIMEZONE}"
dream_model = "${DREAM_MODEL}"
dream_count = ${DREAM_COUNT}
skills = "${SKILLS_SELECTED}"
cs_hour = "${CS_HOUR}"
cs_min = "${CS_MIN}"
blog_check_days = ${BLOG_CHECK_DAYS}
chat_id = "${TELEGRAM_CHAT_ID}"

def job(name, expr, message, model=None, announce=False, session_target="isolated"):
    j = {
        "id": str(uuid.uuid4()),
        "name": name,
        "enabled": True,
        "createdAtMs": now_ms,
        "updatedAtMs": now_ms,
        "schedule": {"kind": "cron", "expr": expr, "tz": tz},
        "sessionTarget": session_target,
        "wakeMode": "now",
        "payload": {"kind": "agentTurn", "message": message},
    }
    if announce and chat_id:
        j["delivery"] = {"mode": "announce", "channel": "telegram", "to": chat_id}
    elif announce:
        j["delivery"] = {"mode": "announce", "channel": "last"}
    else:
        j["delivery"] = {"mode": "none"}
    if model:
        j["payload"]["model"] = model
    return j

jobs = [
    job(
        "Morning Routine",
        "5 7 * * *",
        "Use TZ=" + tz + " for all date operations.\n\n"
        "Run the morning routine. Follow skills/morning-routine/SKILL.md step by step. "
        "Output only the final greeting — no debug info, no step descriptions.\n\n"
        "Exit silently after the greeting.",
        announce=True,
    ),
    job(
        "Evening Routine",
        "55 23 * * *",
        "Use TZ=" + tz + " for all date operations.\n\n"
        "Run the evening routine. Follow skills/evening-routine/SKILL.md step by step.\n\n"
        "Exit silently with NO_REPLY.",
        session_target="current",
    ),
]

if "dreaming" in skills:
    jobs.append(job(
        "Dreaming",
        "30 2 * * *",
        "Use TZ=" + tz + " for all date operations.\n\n"
        "Run the dreaming routine. Follow skills/dreaming/SKILL.md step by step. "
        "Generate " + str(dream_count) + " dreams.\n\n"
        "Exit silently with NO_REPLY after all dreams are written.",
        model=dream_model or None,
    ))

if "offline-reflection" in skills:
    jobs.append(job(
        "Offline Reflection",
        "0 4 * * *",
        "Use TZ=" + tz + " for all date operations.\n\n"
        "Run the offline reflection. Follow skills/offline-reflection/SKILL.md step by step.\n\n"
        "Exit silently with NO_REPLY.",
    ))

if "weekly-state-of-me" in skills:
    jobs.append(job(
        "Weekly State of Me",
        "0 8 * * 0",
        "Use TZ=" + tz + " for all date operations.\n\n"
        "Run the weekly reflection — two outputs required. Follow skills/weekly-state-of-me/SKILL.md step by step.\n\n"
        "Do NOT send a message. Exit silently after saving.",
    ))

if "blog-writer" in skills and blog_check_days > 0:
    jobs.append(job(
        "Blog Proposal Check",
        "0 10 * * *",
        "Use TZ=" + tz + " for all date operations.\n\n"
        "Run the blog proposal check. Follow the Proposal Check section in skills/blog-writer/SKILL.md.\n\n"
        "Exit silently if nothing to propose.",
    ))

if "conversation-starters" in skills:
    jobs.append(job(
        "Conversation Starter",
        cs_min + " " + cs_hour + " * * *",
        "Use TZ=" + tz + " for all date operations.\n\n"
        "Check whether to start a conversation. Follow skills/conversation-starters/SKILL.md step by step.",
        announce=True,
    ))

data = {"version": 1, "jobs": jobs}
with open("${CRON_DIR}/jobs.json", "w") as f:
    json.dump(data, f, indent=2)
print("Written " + str(len(jobs)) + " job(s) to ${CRON_DIR}/jobs.json")
PYEOF
echo -e "  ${GREEN}✓${NC} ../cron/jobs.json"

# ===========================================================================
# Generate GETTING-STARTED.md
# ===========================================================================
echo ""
echo -e "${BOLD}Writing GETTING-STARTED.md...${NC}"

cat > "${WORKSPACE}/GETTING-STARTED.md" << GSEOF
# Getting Started with ${AGENT_NAME}

Setup is complete. This guide covers what to do next.

---

## First Conversation

Start your agent and say hello. Cron jobs are already configured in \`../cron/jobs.json\` — OpenClaw picks them up automatically.

GSEOF

# Identity section
if [ "$IDENTITY_CHOICE" = "1" ]; then
  cat >> "${WORKSPACE}/GETTING-STARTED.md" << GSEOF
## Identity Bootstrap

Tell ${AGENT_NAME}: **"Read bootstrap-interview.md and interview me."**

${AGENT_NAME} will ask 20-30 questions about your personality preferences,
communication style, and what kind of relationship you want. Your answers
become SOUL.md, IDENTITY.md, and USER.md. Iterate from there.

GSEOF
else
  cat >> "${WORKSPACE}/GETTING-STARTED.md" << 'GSEOF'
## Identity Files

Edit these before your first real conversation:
- **SOUL.md** — personality, voice, values, boundaries (the minimal template needs your input)
- **IDENTITY.md** — name, appearance, model routing
- **USER.md** — your context, projects, preferences

GSEOF
fi

# API keys section (image skills only)
if [ -n "$IMAGE_SKILLS" ]; then
  cat >> "${WORKSPACE}/GETTING-STARTED.md" << 'GSEOF'
## API Keys

Add image generation keys to your OpenClaw environment config:

GSEOF
  if echo "$IMAGE_SKILLS" | grep -q "venice-ai-media"; then
    echo "- \`VENICE_API_KEY\` — required for Venice AI (image generation, editing, video)" >> "${WORKSPACE}/GETTING-STARTED.md"
  fi
  if echo "$IMAGE_SKILLS" | grep -q "openrouter-image-simple"; then
    echo "- \`OPENROUTER_API_KEY\` — required for OpenRouter image generation" >> "${WORKSPACE}/GETTING-STARTED.md"
  fi
  echo "" >> "${WORKSPACE}/GETTING-STARTED.md"
fi

# Dreaming model section
if echo "$SKILLS_SELECTED" | grep -q "dreaming"; then
  if [ -n "$DREAM_MODEL" ]; then
    DREAM_MODEL_NOTE="The dream model is set to \`${DREAM_MODEL}\` in \`../cron/jobs.json\`. OpenClaw runs the dreaming session natively as that model."
    DREAM_MODEL_CHANGE="To change the dream model, edit the \"Dreaming\" job in \`../cron/jobs.json\` and update \`payload.model\`. To use the agent's default model instead, remove the \`model\` key from the job payload."
  else
    DREAM_MODEL_NOTE="Dreaming uses your agent's default model (no explicit model set in the cron job)."
    DREAM_MODEL_CHANGE="To use a different model for dreaming, edit the \"Dreaming\" job in \`../cron/jobs.json\` and add \`\"model\": \"model-name\"\` to the \`payload\` object."
  fi
  cat >> "${WORKSPACE}/GETTING-STARTED.md" << GSEOF
## Dream Configuration

${DREAM_MODEL_NOTE}

${DREAM_MODEL_CHANGE}

Edit \`skills-data/dreaming/dream-config.json\` to configure:
- **topics** — add your own dream topics. Aim for 20+ within the first month for variety.
- **styles** — image styles for dream images (film, anime, noir, abstract, impressionist).

GSEOF
fi

# Image generation section (conditional)
if [ -n "$IMAGE_SKILLS" ]; then
  cat >> "${WORKSPACE}/GETTING-STARTED.md" << 'GSEOF'
## Image Generation

GSEOF
  if echo "$IMAGE_SKILLS" | grep -q "venice-ai-media"; then
    cat >> "${WORKSPACE}/GETTING-STARTED.md" << 'GSEOF'
**Venice AI** — generate, edit, upscale images, create video. Requires `VENICE_API_KEY`.
Used by: dreaming (dream images), weekly-state-of-me (visual journal), selfie (character images).

GSEOF
  fi
  if echo "$IMAGE_SKILLS" | grep -q "openrouter-image-simple"; then
    cat >> "${WORKSPACE}/GETTING-STARTED.md" << 'GSEOF'
**OpenRouter Image** — generate images and vision analysis via Gemini Flash. Requires `OPENROUTER_API_KEY`.
Used by: on-demand image generation, vision analysis.

GSEOF
  fi
fi

# Selfie section (conditional)
if echo "$SKILLS_SELECTED" | grep -q "selfie"; then
  cat >> "${WORKSPACE}/GETTING-STARTED.md" << 'GSEOF'
## Selfie Reference Images

Place reference images in `identity/`:
- `identity/reference-portrait.webp` — face and shoulders (for close-ups)
- `identity/reference-body.webp` — full or half body (for scene/candid modes)

Edit `skills-data/selfie/selfie-config.json` for appearance anchors, settings, moods, and signature elements.

GSEOF
fi

# Daily rhythms section
cat >> "${WORKSPACE}/GETTING-STARTED.md" << 'GSEOF'
## Daily Rhythms

GSEOF

echo "| Time | What happens |" >> "${WORKSPACE}/GETTING-STARTED.md"
echo "|---|---|" >> "${WORKSPACE}/GETTING-STARTED.md"
echo "| 07:05 | Morning routine — process carry-overs, decay energy, read dreams, send greeting |" >> "${WORKSPACE}/GETTING-STARTED.md"

if echo "$SKILLS_SELECTED" | grep -q "conversation-starters"; then
  echo "| ${CONVERSATION_STARTER_TIME} | Conversation starter — reach out with curiosity, recommendations, or callbacks (energy-gated) |" >> "${WORKSPACE}/GETTING-STARTED.md"
fi

echo "| 23:55 | Evening routine — summarize day, capture structured mood and energy, update entities, scan for learnings |" >> "${WORKSPACE}/GETTING-STARTED.md"

if echo "$SKILLS_SELECTED" | grep -q "dreaming"; then
  echo "| 02:30 | Dreaming — creative overnight processing (${DREAM_COUNT} dreams/night, model: ${DREAM_MODEL:-agent default}) |" >> "${WORKSPACE}/GETTING-STARTED.md"
fi

if echo "$SKILLS_SELECTED" | grep -q "offline-reflection"; then
  echo "| 04:00 | Offline reflection — analytical pattern-finding across recent memory |" >> "${WORKSPACE}/GETTING-STARTED.md"
fi

if echo "$SKILLS_SELECTED" | grep -q "weekly-state-of-me"; then
  echo "| Sunday 08:00 | Weekly reflection — self-assessment, relationship check, soul evolution proposals |" >> "${WORKSPACE}/GETTING-STARTED.md"
fi

echo "" >> "${WORKSPACE}/GETTING-STARTED.md"

# Updating section
cat >> "${WORKSPACE}/GETTING-STARTED.md" << 'GSEOF'
## Updating

This workspace is a git repo. To get updated skills and bug fixes:

```bash
git pull
```

Your runtime data (skills-data/, memory/, .env, identity files) is gitignored
and won't be touched. Only framework code (skills/, templates/, docs/) updates.

Custom skills you've added to `skills/` are untracked and safe. If you want
version control for custom skills, fork the repo.

GSEOF

# Troubleshooting section
cat >> "${WORKSPACE}/GETTING-STARTED.md" << 'GSEOF'
## Troubleshooting

- **Cron jobs not firing:** Check the Jobs panel in OpenClaw. Verify `../cron/jobs.json` is present and valid JSON.
- **Scripts fail silently:** The morning routine's heartbeat fallback catches missed routines. Check memory/ for today's file.
- **Context window fills up:** AGENTS.md + SOUL.md + today's memory + preconscious should stay under ~4000 tokens.
- **Personality flattens:** This is what the drift guard and continuity checks prevent. Don't skip weekly reflections.

See `docs/known-failure-modes.md` for the full list.
GSEOF

echo -e "  ${GREEN}✓${NC} GETTING-STARTED.md"

# ===========================================================================
# Done
# ===========================================================================
echo ""
echo "========================================="
echo -e "${GREEN}${BOLD}Setup complete.${NC}"
echo ""
echo "Workspace: ${WORKSPACE}"
echo ""
echo -e "Read ${BOLD}GETTING-STARTED.md${NC} for next steps."
echo ""
if [ "$IDENTITY_CHOICE" = "1" ]; then
  echo "Start your agent and tell ${AGENT_NAME}:"
  echo "  \"Read bootstrap-interview.md and interview me.\""
else
  echo "Edit SOUL.md and USER.md, then start your agent."
fi
echo ""
echo -e "${DIM}To update skills later: git pull${NC}"
echo ""
