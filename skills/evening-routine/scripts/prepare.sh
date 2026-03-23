#!/bin/bash
# Evening routine preparation: idempotency check and memory file creation.
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
if grep -q "Evening summary written" "$MEMORY_FILE" 2>/dev/null; then
  echo "ALREADY_RUN"
  exit 2
fi

echo "READY"
