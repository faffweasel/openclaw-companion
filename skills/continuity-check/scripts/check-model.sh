#!/bin/bash
# Check if the current model differs from the last continuity-checked model.
# Used at session start to detect model switches.
# Usage: check-model.sh "current-model-name"
# Exit codes: 0 = same model (no check needed), 1 = different model (run continuity check)

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

: "${DATA_DIR:=${WORKSPACE}/skills-data}"
SKILL_DATA="${DATA_DIR}/${SKILL_NAME}"

LAST_MODEL_FILE="${SKILL_DATA}/last-model.txt"
CURRENT_MODEL="${1:?Usage: check-model.sh \"current-model-name\"}"

if [ ! -f "$LAST_MODEL_FILE" ]; then
  # First run — no previous model recorded
  echo "FIRST_RUN"
  echo "No previous model recorded. Run continuity check to establish baseline."
  exit 1
fi

LAST_MODEL=$(cat "$LAST_MODEL_FILE" 2>/dev/null || echo "")

if [ "$CURRENT_MODEL" = "$LAST_MODEL" ]; then
  echo "SAME_MODEL: $CURRENT_MODEL"
  exit 0
else
  echo "MODEL_CHANGED: $LAST_MODEL → $CURRENT_MODEL"
  echo "Run continuity check."
  exit 1
fi
