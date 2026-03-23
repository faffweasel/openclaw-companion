#!/bin/bash
# Stamp is implicit — the reflection file's existence IS the stamp.
# This script exists for consistency with the morning/evening routine pattern.
# It appends a completion marker to the reflection file.

set -euo pipefail

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
: "${TZ:=UTC}"

TODAY=$(TZ="$TZ" date +%Y-%m-%d)
REFLECTION_FILE="${MEMORY_DIR}/reflections/${TODAY}.md"

if [ -f "$REFLECTION_FILE" ]; then
  echo "" >> "$REFLECTION_FILE"
  echo "---" >> "$REFLECTION_FILE"
  echo "_Reflection complete: $(TZ="$TZ" date '+%Y-%m-%d %H:%M')_" >> "$REFLECTION_FILE"
fi
