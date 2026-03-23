#!/bin/bash
# Count preferences per category. Useful for health checks.
# Usage: count.sh

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
TENSIONS_FILE="${SKILL_DATA}/tensions.md"

if [ ! -f "$PREFS_FILE" ]; then
  echo "No preferences accumulated yet."
  exit 0
fi

TOTAL=$(grep -c "^## " "$PREFS_FILE" || true)

echo "=== Preference Accumulation Health ==="
echo "Total entries: $TOTAL"
echo ""

for CAT in communication interaction humor aesthetic taste music value tool; do
  COUNT=$(grep -c "^## ${CAT} " "$PREFS_FILE" || true)
  if [ "$COUNT" -eq 0 ]; then
    echo "  $CAT: $COUNT  ⚠️ empty"
  else
    echo "  $CAT: $COUNT"
  fi
done

# Tensions count
if [ -f "$TENSIONS_FILE" ]; then
  UNRESOLVED=$(grep -c "unresolved" "$TENSIONS_FILE" || true)
  if [ "$UNRESOLVED" -gt 0 ]; then
    echo ""
    echo "Unresolved tensions: $UNRESOLVED"
  fi
fi
