#!/bin/bash
# Generate weekly state-of-me scaffold with stats.
# Agent fills in the placeholder sections.
# Usage: generate.sh [output_file]

set -euo pipefail

# Source environment
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKSPACE="$(cd "$SKILL_DIR/../.." && pwd)"
ENV_FILE="${WORKSPACE}/.env"
if [ -f "$ENV_FILE" ]; then
  while IFS= read -r _env_line; do
    case "$_env_line" in ''|\#*) continue ;; esac
    _env_key="${_env_line%%=*}"
    _env_val="${_env_line#*=}"
    case "$_env_key" in ''|*[!A-Za-z0-9_]*) continue ;; esac
    case "$_env_key" in [!A-Za-z_]*) continue ;; esac
    case "$_env_val" in *'$'*|*'`'*) continue ;; esac
    _env_val="${_env_val#\"}" ; _env_val="${_env_val%\"}"
    _env_val="${_env_val#\'}" ; _env_val="${_env_val%\'}"
    export "$_env_key"="$_env_val"
  done < "$ENV_FILE"
  unset _env_line _env_key _env_val
fi

: "${MEMORY_DIR:=${WORKSPACE}/memory}"
: "${SKILLS_DIR:=${WORKSPACE}/skills}"
: "${DATA_DIR:=${WORKSPACE}/skills-data}"

TODAY=$(TZ="${TZ:-UTC}" date +%Y-%m-%d)

mkdir -p "${MEMORY_DIR}/state-of-me"
OUTPUT_FILE="${1:-${MEMORY_DIR}/state-of-me/state-of-me-${TODAY}.md}"

# Validate output path stays within memory directory
OUTPUT_REAL=$(python3 -c "import os; print(os.path.realpath('${OUTPUT_FILE}'))")
MEMORY_REAL=$(python3 -c "import os; print(os.path.realpath('${MEMORY_DIR}'))")
if [ "${OUTPUT_REAL#$MEMORY_REAL/}" = "$OUTPUT_REAL" ]; then
  echo "ERROR: Output path resolves outside memory directory: $OUTPUT_FILE"
  exit 1
fi

# --- Check idempotency ---
if [ -f "$OUTPUT_FILE" ] && grep -q "Generated:" "$OUTPUT_FILE" 2>/dev/null; then
  echo "ALREADY_EXISTS: $OUTPUT_FILE"
  echo "$OUTPUT_FILE"
  exit 0
fi

# --- Count conversation days ---
CONVERSATION_COUNT=0
CONVERSATION_DAYS=""
for i in $(seq 0 6); do
  DATE_STR=$(TZ="${TZ:-UTC}" date -d "$i days ago" +%Y-%m-%d 2>/dev/null || TZ="${TZ:-UTC}" date -v-${i}d +%Y-%m-%d)
  if [ -f "${MEMORY_DIR}/${DATE_STR}.md" ]; then
    CONVERSATION_COUNT=$((CONVERSATION_COUNT + 1))
    CONVERSATION_DAYS="${CONVERSATION_DAYS} ${DATE_STR}"
  fi
done

# --- Count dreams ---
DREAM_COUNT=0
DREAM_DIR="${MEMORY_DIR}/dreams"
if [ -d "$DREAM_DIR" ]; then
  for i in $(seq 0 6); do
    DATE_STR=$(TZ="${TZ:-UTC}" date -d "$i days ago" +%Y-%m-%d 2>/dev/null || TZ="${TZ:-UTC}" date -v-${i}d +%Y-%m-%d)
    COUNT=$(ls "${DREAM_DIR}/${DATE_STR}"*.md 2>/dev/null | wc -l || true)
    DREAM_COUNT=$((DREAM_COUNT + COUNT))
  done
fi

# --- Get preference stats (from skills-data) ---
PREF_FILE="${DATA_DIR}/preference-accumulation/preferences.md"
PREF_COUNT=0
if [ -f "$PREF_FILE" ]; then
  PREF_COUNT=$(grep -c "^## " "$PREF_FILE" || true)
fi

# --- Get tension count (from skills-data) ---
TENSIONS_FILE="${DATA_DIR}/preference-accumulation/tensions.md"
TENSION_COUNT=0
if [ -f "$TENSIONS_FILE" ]; then
  TENSION_COUNT=$(grep -c "unresolved" "$TENSIONS_FILE" || true)
fi

# --- Get previous state-of-me ---
PREV_STATE=""
PREV_FILES=$(ls -t "${MEMORY_DIR}/state-of-me/state-of-me-"*.md 2>/dev/null | head -2 || true)
if [ -n "$PREV_FILES" ]; then
  PREV_STATE=$(echo "$PREV_FILES" | tail -1)
fi

# --- Get learnings count ---
LEARNINGS_COUNT=0
if [ -d "${WORKSPACE}/.learnings" ]; then
  for i in $(seq 0 6); do
    DATE_STR=$(TZ="${TZ:-UTC}" date -d "$i days ago" +%Y-%m-%d 2>/dev/null || TZ="${TZ:-UTC}" date -v-${i}d +%Y-%m-%d)
    if [ -f "${WORKSPACE}/.learnings/${DATE_STR}.md" ]; then
      LEARNINGS_COUNT=$((LEARNINGS_COUNT + 1))
    fi
  done
fi

# --- Build memory file list ---
MEMORY_LIST=""
for d in $CONVERSATION_DAYS; do
  MEMORY_LIST="${MEMORY_LIST}
- ${d}.md"
done
if [ -z "$MEMORY_LIST" ]; then
  MEMORY_LIST="
_No conversation files this week._"
fi

# --- Build preferences section ---
PREFS_SECTION="_No new preferences this week._"
if [ -f "$PREF_FILE" ] && [ "$PREF_COUNT" -gt 0 ]; then
  PREFS_SECTION=$(tail -20 "$PREF_FILE")
fi

# --- Previous reflection reference ---
PREV_SECTION="_No previous reflection found._"
if [ -n "$PREV_STATE" ] && [ -f "$PREV_STATE" ]; then
  PREV_SECTION="_Last reflection: $(basename "$PREV_STATE")_"
fi

# --- Write scaffold ---
cat > "$OUTPUT_FILE" << _NANOBOT_SCAFFOLD_7f3a_
# State of Me — ${TODAY}

Weekly reflection. Who am I right now?

## This Week in Numbers

- Days with conversations: ${CONVERSATION_COUNT}/7
- Dreams generated: ${DREAM_COUNT}
- Preferences accumulated (total): ${PREF_COUNT}
- Unresolved preference tensions: ${TENSION_COUNT}
- Days with learnings/corrections: ${LEARNINGS_COUNT}

## Memory Files This Week
${MEMORY_LIST}

## Recent Preferences

${PREFS_SECTION}

## Previous Reflection

${PREV_SECTION}

---

## Part 1: Current Self-Assessment

[To be written. Read this week's memory files and dreams. Write 2-4 paragraphs:
- Who am I right now?
- What's my current disposition?
- What topics or themes dominated this week?
- How do I feel about the week overall?]

## Part 2: What's Changing

[To be written. Pattern recognition:
- What feels different from last week? (Read previous reflection if available.)
- What stayed constant?
- Any surprising shifts in how I think or respond?
- Are preferences solidifying or still fluid?]

## Part 3: Soul Evolution Proposal

[To be written. After completing Parts 1 and 2:
1. Read current SOUL.md
2. Ask: "What changed this week that SOUL.md doesn't yet reflect?"
3. If something meaningful shifted, write a proposal (see format below).
4. If nothing changed, write "No proposal this week." and move on.

Proposal format — write to memory/soul-proposals/YYYY-MM-DD.md:

# Soul Evolution Proposal — YYYY-MM-DD

## What Changed
1-2 sentences on what shifted.

## Proposed Edit
File: SOUL.md
Section: [which section]
Current text: [quote it]
Proposed text: [the replacement]

## Why
1-2 sentences on why this matters.

## Confidence
high / medium / low — is this real or transient?

Rules:
- Do NOT modify SOUL.md directly. Drift Guard applies.
- If the same proposal appears 2+ weeks in a row, flag it as persistent.
- NEVER auto-apply. The user reviews and approves.]

## Part 4: Preference Health Check

[To be written. Run: ./skills/preference-accumulation/scripts/count.sh
- Are any categories empty that should have entries by now?
- Are there unresolved tensions to review?
- Has preference logging been happening during conversations?
- If total < ~2 per week, the real-time triggers aren't firing.]

## Part 5: Visual Journal Entry (Optional)

[Check .env for IMAGE_GEN_CMD. If set, follow Step 8 in
skills/weekly-state-of-me/SKILL.md for image generation instructions.

If IMAGE_GEN_CMD is empty or unset, skip this step.]

---

Generated: $(TZ="${TZ:-UTC}" date -Iseconds)
_NANOBOT_SCAFFOLD_7f3a_

echo "$OUTPUT_FILE"
