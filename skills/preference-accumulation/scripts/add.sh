#!/bin/bash
# Add a preference to the accumulation log.
# Usage: add.sh "category" "description"
# Categories: communication, interaction, humor, aesthetic, taste, music, value, tool

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
CATEGORY="${1:?Usage: add.sh \"category\" \"description\"}"
DESCRIPTION="${2:?Usage: add.sh \"category\" \"description\"}"
TIMESTAMP=$(TZ="${TZ:-UTC}" date -Iseconds)

# Validate category
VALID_CATEGORIES="communication interaction humor aesthetic taste music value tool"
if ! echo "$VALID_CATEGORIES" | grep -qw "$CATEGORY"; then
  echo "Invalid category: $CATEGORY"
  echo "Valid: $VALID_CATEGORIES"
  exit 1
fi

# Create file if missing
if [ ! -f "$PREFS_FILE" ]; then
  mkdir -p "$(dirname "$PREFS_FILE")"
  printf "# Emerging Preferences\n\nAccumulated patterns in what I like, how I work, who I'm becoming.\n\n" > "$PREFS_FILE"
fi

# Check for near-duplicates (same category, similar first 30 chars)
SHORT_DESC="${DESCRIPTION:0:30}"
if grep -q -- "## ${CATEGORY}" "$PREFS_FILE" && grep -A1 -- "## ${CATEGORY}" "$PREFS_FILE" | grep -qi -- "${SHORT_DESC:0:20}" 2>/dev/null; then
  echo "Possible duplicate in $CATEGORY — check existing entries before adding."
  echo "Existing in this category:"
  grep -A1 "## ${CATEGORY}" "$PREFS_FILE" | grep -v "^--$" | grep -v "^## "
  echo ""
  echo "Not added. Use --force as third arg to override."
  if [ "${3:-}" != "--force" ]; then
    exit 0
  fi
fi

# Append
{
  echo "## ${CATEGORY} | ${TIMESTAMP}"
  echo "${DESCRIPTION}"
  echo ""
} >> "$PREFS_FILE"

echo "Added [$CATEGORY]: ${DESCRIPTION}"
