#!/usr/bin/env bash
# capstone-labmate installer — copies the skill into a host's skills directory.
# Usage: ./install.sh [DEST_DIR]
set -e
SRC="$(cd "$(dirname "$0")" && pwd)/capstone-labmate"
DEST="${1:-$HOME/.workbuddy/skills/capstone-labmate}"
mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -r "$SRC" "$DEST"
echo "Installed capstone-labmate -> $DEST"
