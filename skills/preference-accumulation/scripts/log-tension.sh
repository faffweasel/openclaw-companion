#!/bin/bash
# Log a tension between existing and new preferences.
# Usage: log-tension.sh "category" "existing preference" "new preference"

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

TENSIONS_FILE="${SKILL_DATA}/tensions.md"
CATEGORY="${1:?Usage: log-tension.sh \"category\" \"existing\" \"new\"}"
EXISTING="${2:?Usage: log-tension.sh \"category\" \"existing\" \"new\"}"
NEW_PREF="${3:?Usage: log-tension.sh \"category\" \"existing\" \"new\"}"
TODAY=$(TZ="${TZ:-UTC}" date +%Y-%m-%d)

# Create file if missing
if [ ! -f "$TENSIONS_FILE" ]; then
  mkdir -p "$(dirname "$TENSIONS_FILE")"
  printf "# Preference Tensions\n\nContradictions between existing and new preferences. Review during weekly reflection.\n\n" > "$TENSIONS_FILE"
fi

{
  echo "## ${TODAY} — Tension Detected"
  echo "**Category:** ${CATEGORY}"
  echo "**Existing:** ${EXISTING}"
  echo "**New:** ${NEW_PREF}"
  echo "**Status:** unresolved"
  echo ""
} >> "$TENSIONS_FILE"

echo "Tension logged [$CATEGORY]: \"$EXISTING\" vs \"$NEW_PREF\""
