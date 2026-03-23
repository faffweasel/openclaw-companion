#!/bin/bash
# Morning routine preparation: idempotency check, memory file creation,
# carry-over processing, preconscious decay.
# Returns exit code 2 if already run today (agent should stop).
# Usage: prepare.sh [YYYY-MM-DD]

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

DATE="${1:-$(TZ="${TZ:-UTC}" date +%Y-%m-%d)}"

# --- Validate date format ---
if ! [[ "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "ERROR: Invalid date format: $DATE (expected YYYY-MM-DD)"
  exit 1
fi

MEMORY_FILE="${MEMORY_DIR}/${DATE}.md"

# --- Ensure memory file exists ---
mkdir -p "$MEMORY_DIR"
if [ ! -f "$MEMORY_FILE" ]; then
  echo "# ${DATE}" > "$MEMORY_FILE"
  echo "" >> "$MEMORY_FILE"
  echo "Created memory file: $MEMORY_FILE"
fi

# --- Idempotency check ---
if grep -q "Morning message sent" "$MEMORY_FILE" 2>/dev/null; then
  echo "ALREADY_RUN"
  exit 2
fi

# --- Process carry-over queue ---
CARRYOVER_SCRIPT="${SKILLS_DIR}/carry-over-queue/scripts/append-to-memory.py"
if [ -f "$CARRYOVER_SCRIPT" ]; then
  echo "--- Carry-over ---"
  python3 "$CARRYOVER_SCRIPT" "$DATE"
else
  echo "Carry-over script not found, skipping."
fi

# --- Decay preconscious buffer ---
DECAY_SCRIPT="${SKILLS_DIR}/preconscious/scripts/decay.py"
if [ -f "$DECAY_SCRIPT" ]; then
  echo "--- Preconscious decay ---"
  python3 "$DECAY_SCRIPT"
else
  echo "Preconscious decay script not found, skipping."
fi

# --- Read preconscious for agent context ---
READ_SCRIPT="${SKILLS_DIR}/preconscious/scripts/read.py"
if [ -f "$READ_SCRIPT" ]; then
  echo "--- Current preconscious ---"
  python3 "$READ_SCRIPT"
fi

echo ""
echo "READY"
