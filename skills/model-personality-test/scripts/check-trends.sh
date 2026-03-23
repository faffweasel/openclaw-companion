#!/bin/bash
# Check if enough test files exist for trend generation.
# If 5+, output the filenames for the agent to read and synthesise.
# Usage: check-trends.sh

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

ANALYSIS_DIR="${MEMORY_DIR}/self-analysis"

if [ ! -d "$ANALYSIS_DIR" ]; then
  echo "NO_TESTS"
  echo "No self-analysis directory found."
  exit 0
fi

# Count personality test files (they contain "SelfAnalysis" in name)
TEST_FILES=$(ls "$ANALYSIS_DIR/"*SelfAnalysis*.md 2>/dev/null || true)
COUNT=$(echo "$TEST_FILES" | grep -c "." 2>/dev/null || true)

if [ "$COUNT" -lt 5 ]; then
  echo "INSUFFICIENT"
  echo "$COUNT test(s) found. Need 5+ for trend analysis."
  exit 0
fi

echo "READY"
echo "$COUNT tests found. Generate trend summary."
echo ""
echo "Files (newest last):"
echo "$TEST_FILES" | sort
echo ""
echo "Write trend summary to: ${ANALYSIS_DIR}/trend-summary.md"
