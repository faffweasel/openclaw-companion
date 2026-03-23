#!/bin/bash
# Stamp today's memory file to mark evening routine as complete.
# Usage: stamp.sh [YYYY-MM-DD]

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
TIME=$(TZ="${TZ:-UTC}" date +%H:%M)
MEMORY_FILE="${MEMORY_DIR}/${DATE}.md"

if [ ! -f "$MEMORY_FILE" ]; then
  echo "Memory file not found: $MEMORY_FILE"
  exit 1
fi

echo "" >> "$MEMORY_FILE"
echo "Evening summary written: ${TIME} ${TZ:-UTC}" >> "$MEMORY_FILE"
echo "Stamped: Evening summary written at ${TIME}"
