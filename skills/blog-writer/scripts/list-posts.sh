#!/bin/bash
# List published posts and their metadata for style guide regeneration.
# The agent reads the output and rewrites skills-data/blog-writer/style-guide.md.
# Usage: list-posts.sh

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

POSTS_DIR="${SKILL_DATA}/published"

if [ ! -d "$POSTS_DIR" ]; then
  echo "NO_POSTS"
  echo "No published posts yet. Style guide will be seeded from SOUL.md on first write."
  exit 0
fi

POST_COUNT=$(ls "${POSTS_DIR}/"*.md 2>/dev/null | wc -l || true)

if [ "$POST_COUNT" -eq 0 ]; then
  echo "NO_POSTS"
  echo "No published posts yet."
  exit 0
fi

echo "POSTS_FOUND: $POST_COUNT"
echo ""
echo "Published posts (newest first):"
ls -t "${POSTS_DIR}/"*.md 2>/dev/null | while read -r f; do
  TITLE=$(head -5 "$f" | grep -i "^title:" | sed 's/^title: *//' || basename "$f" .md)
  echo "  $(basename "$f") — $TITLE"
done
echo ""
echo "Read these posts, then rewrite skills-data/blog-writer/style-guide.md based on:"
echo "  - What opening patterns work"
echo "  - What vocabulary feels natural"
echo "  - What paragraph/structure rhythms recur"
echo "  - What to avoid (things that felt forced in retrospect)"
