"""Shared .env loader matching the bash parser's strictness.

Bash parser (prepare.sh) validates:
  1. Skip empty lines and # comments
  2. Key must match [A-Za-z_][A-Za-z0-9_]* (no spaces, no special chars)
  3. Value must NOT contain $ or backticks (shell injection vectors)
  4. Strip surrounding quotes

This module mirrors all four checks. Only sets vars not already in os.environ
so real environment variables always win.

Usage:
    from lib.env import load_env
    load_env(workspace)  # workspace is the resolved path to the repo root
"""

import os
import re

_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def load_env(workspace: str) -> None:
    """Parse workspace/.env with the same rules as the bash scripts."""
    env_file = os.path.join(workspace, ".env")
    if not os.path.isfile(env_file):
        return
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            if not _KEY_RE.match(key):
                continue
            if "$" in value or "`" in value:
                continue
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            if key not in os.environ:
                os.environ[key] = value
