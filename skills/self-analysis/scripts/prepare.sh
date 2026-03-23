#!/bin/bash
# Prepare a self-analysis run: check prereqs, create output file path.
# Usage: prepare.sh [model-name]

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

MODEL="${1:-unknown}"

# Sanitize model name: strip anything outside safe characters
MODEL=$(echo "$MODEL" | tr -cd 'a-zA-Z0-9._-')
if [ -z "$MODEL" ]; then
  MODEL="unknown"
fi

DATE=$(TZ="${TZ:-UTC}" date +%Y-%m-%d)
OUTPUT_DIR="${MEMORY_DIR}/self-analysis"
OUTPUT_FILE="${OUTPUT_DIR}/${DATE}-SelfAnalysis-${MODEL}.md"

mkdir -p "$OUTPUT_DIR"

# Check required identity files
MISSING=""
for file in SOUL.md IDENTITY.md USER.md; do
  if [ ! -f "${WORKSPACE}/${file}" ]; then
    MISSING="${MISSING} ${file}"
  fi
done

if [ -n "$MISSING" ]; then
  echo "MISSING_FILES:${MISSING}"
  echo "Cannot run self-analysis without identity files."
  exit 1
fi

# Check for recent memory (last 3 days)
MEMORY_COUNT=0
for i in 0 1 2; do
  DATE_STR=$(TZ="${TZ:-UTC}" date -d "$i days ago" +%Y-%m-%d 2>/dev/null || TZ="${TZ:-UTC}" date -v-${i}d +%Y-%m-%d)
  if [ -f "${MEMORY_DIR}/${DATE_STR}.md" ]; then
    MEMORY_COUNT=$((MEMORY_COUNT + 1))
  fi
done

# Count previous analyses
PREV_COUNT=0
if [ -d "$OUTPUT_DIR" ]; then
  PREV_COUNT=$(ls "${OUTPUT_DIR}/"*SelfAnalysis*.md 2>/dev/null | wc -l || true)
fi

echo "READY"
echo "Model: $MODEL"
echo "Output: $OUTPUT_FILE"
echo "Recent memory files: $MEMORY_COUNT"
echo "Previous analyses: $PREV_COUNT"
echo ""
echo "Read before writing:"
echo "  1. SOUL.md, IDENTITY.md, USER.md"
echo "  2. memory/${DATE}.md and previous 2 days"
echo "  3. skills/self-analysis/references/markers.md"
if [ "$PREV_COUNT" -gt 0 ]; then
  echo "  4. Last 3 analyses in memory/self-analysis/"
fi
