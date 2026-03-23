#!/bin/bash
set -euo pipefail

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

: "${MEMORY_DIR:=${WORKSPACE}/memory}"
: "${TZ:=UTC}"

TODAY=$(TZ="$TZ" date +%Y-%m-%d)
REFLECTIONS_DIR="${MEMORY_DIR}/reflections"

# Idempotency check
if [ -f "${REFLECTIONS_DIR}/${TODAY}.md" ]; then
  echo "ALREADY_RUN"
  exit 0
fi

# Data sufficiency check — need 3+ days of memory files with actual content
# (more than just a morning stamp or empty file)
MIN_DAYS=3
MIN_LINES=5  # A file with fewer lines than this is effectively empty

days_with_content=0
for i in $(seq 0 6); do
  check_date=$(TZ="$TZ" date -d "${TODAY} - ${i} days" +%Y-%m-%d 2>/dev/null || \
               TZ="$TZ" date -v-"${i}"d +%Y-%m-%d 2>/dev/null || echo "")
  if [ -n "$check_date" ] && [ -f "${MEMORY_DIR}/${check_date}.md" ]; then
    line_count=$(wc -l < "${MEMORY_DIR}/${check_date}.md")
    if [ "$line_count" -ge "$MIN_LINES" ]; then
      days_with_content=$((days_with_content + 1))
    fi
  fi
done

if [ "$days_with_content" -lt "$MIN_DAYS" ]; then
  echo "INSUFFICIENT_DATA"
  echo "Found ${days_with_content} days with content (need ${MIN_DAYS})"
  exit 0
fi

# Create reflections directory if needed
mkdir -p "$REFLECTIONS_DIR"

echo "READY"
