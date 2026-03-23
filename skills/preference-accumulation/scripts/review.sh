#!/bin/bash
# Review accumulated preferences.
# Usage: review.sh [category]
# No args = show all. With category = filter.

set -euo pipefail

# Source environment
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_NAME="$(basename "$SKILL_DIR")"
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

: "${DATA_DIR:=${WORKSPACE}/skills-data}"
SKILL_DATA="${DATA_DIR}/${SKILL_NAME}"

PREFS_FILE="${SKILL_DATA}/preferences.md"
CATEGORY="${1:-all}"

if [ ! -f "$PREFS_FILE" ]; then
  echo "No preferences accumulated yet."
  exit 0
fi

if [ "$CATEGORY" = "all" ]; then
  cat "$PREFS_FILE"
else
  echo "=== Preferences: ${CATEGORY} ==="
  echo ""
  # Print header line and the following description line for matching categories
  awk -v cat="## ${CATEGORY}" '
    /^## / { found = match($0, cat); if (found) print $0 }
    found && !/^## / { print; if (/^$/) found=0 }
  ' "$PREFS_FILE"
fi
