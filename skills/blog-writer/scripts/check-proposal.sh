#!/bin/bash
# Check if enough time has passed to propose a new blog topic.
# Reads BLOG_CHECK_DAYS from .env (default 3).
# Usage: check-proposal.sh

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
: "${DATA_DIR:=${WORKSPACE}/skills-data}"
: "${BLOG_CHECK_DAYS:=3}"
SKILL_DATA="${DATA_DIR}/${SKILL_NAME}"

# If disabled
if [ "$BLOG_CHECK_DAYS" -eq 0 ]; then
  echo "DISABLED"
  echo "BLOG_CHECK_DAYS=0 in .env. Auto-proposals disabled."
  exit 0
fi

TODAY_EPOCH=$(TZ="${TZ:-UTC}" date +%s)

# Find most recent proposal or published post
LAST_DATE=""

# Check proposals
LATEST_PROPOSAL=$(ls -t "${MEMORY_DIR}/blog-proposals/"*.md 2>/dev/null | head -1 || true)
if [ -n "$LATEST_PROPOSAL" ]; then
  # Extract date from filename (YYYY-MM-DD-*.md)
  LAST_DATE=$(basename "$LATEST_PROPOSAL" | grep -oP '^\d{4}-\d{2}-\d{2}' || true)
fi

# Check published posts (now in skills-data)
POSTS_DIR="${SKILL_DATA}/published"
LATEST_POST=$(ls -t "${POSTS_DIR}/"*.md 2>/dev/null | head -1 || true)
if [ -n "$LATEST_POST" ]; then
  POST_DATE=$(basename "$LATEST_POST" | grep -oP '^\d{4}-\d{2}-\d{2}' || true)
  # Use whichever is more recent
  if [ -n "$POST_DATE" ]; then
    if [ -z "$LAST_DATE" ] || [[ "$POST_DATE" > "$LAST_DATE" ]]; then
      LAST_DATE="$POST_DATE"
    fi
  fi
fi

# If nothing found, eligible
if [ -z "$LAST_DATE" ]; then
  echo "ELIGIBLE"
  echo "No previous proposals or posts found. First proposal."
  exit 0
fi

LAST_EPOCH=$(TZ="${TZ:-UTC}" date -d "$LAST_DATE" +%s 2>/dev/null || echo "0")
DAYS_SINCE=$(( (TODAY_EPOCH - LAST_EPOCH) / 86400 ))

if [ "$DAYS_SINCE" -ge "$BLOG_CHECK_DAYS" ]; then
  echo "ELIGIBLE"
  echo "Last activity: $LAST_DATE ($DAYS_SINCE days ago). Threshold: $BLOG_CHECK_DAYS days."

  # Count memory files since last activity for the agent's context
  MEM_COUNT=0
  for i in $(seq 0 $((DAYS_SINCE - 1))); do
    DATE_STR=$(TZ="${TZ:-UTC}" date -d "$i days ago" +%Y-%m-%d 2>/dev/null || TZ="${TZ:-UTC}" date -v-${i}d +%Y-%m-%d)
    if [ -f "${MEMORY_DIR}/${DATE_STR}.md" ]; then
      MEM_COUNT=$((MEM_COUNT + 1))
    fi
  done
  echo "Memory files since then: $MEM_COUNT"
else
  echo "TOO_RECENT"
  echo "Last activity: $LAST_DATE ($DAYS_SINCE days ago). Threshold: $BLOG_CHECK_DAYS days. Wait $((BLOG_CHECK_DAYS - DAYS_SINCE)) more day(s)."
fi
