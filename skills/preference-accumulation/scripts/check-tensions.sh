#!/bin/bash
# Check for potential tensions before adding a new preference.
# Outputs existing preferences in the same category for agent review.
# Usage: check-tensions.sh "category" "new preference description"

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
CATEGORY="${1:?Usage: check-tensions.sh \"category\" \"new preference description\"}"
NEW_PREF="${2:?Usage: check-tensions.sh \"category\" \"new preference description\"}"

if [ ! -f "$PREFS_FILE" ]; then
  echo "NO_TENSIONS"
  exit 0
fi

# Extract existing preferences in this category
EXISTING=$(awk -v cat="## ${CATEGORY}" '
  /^## / { if (match($0, cat)) { found=1 } else { found=0 } }
  found && !/^## / && !/^$/ { print }
' "$PREFS_FILE")

if [ -z "$EXISTING" ]; then
  echo "NO_TENSIONS"
  exit 0
fi

COUNT=$(echo "$EXISTING" | wc -l)
echo "REVIEW_FOR_TENSIONS"
echo ""
echo "New preference ($CATEGORY):"
echo "  $NEW_PREF"
echo ""
echo "$COUNT existing preference(s) in $CATEGORY:"
echo "$EXISTING" | while read -r line; do echo "  $line"; done
echo ""
echo "Do any of these contradict the new preference?"
echo "If yes, call: ./scripts/log-tension.sh \"$CATEGORY\" \"existing text\" \"$NEW_PREF\""
echo "Then decide: add the new preference anyway (context-dependent) or skip it (replaced)."
