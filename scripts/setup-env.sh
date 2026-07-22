#!/usr/bin/env bash
set -euo pipefail

# Ensures $HOME/.local/bin is on PATH for zsh shells.
LINE='export PATH="$HOME/.local/bin:$PATH"'
RC_FILE="$HOME/.zshrc"

touch "$RC_FILE"

if grep -Fxq "$LINE" "$RC_FILE"; then
  echo "PATH export already present in $RC_FILE"
else
  echo "$LINE" >> "$RC_FILE"
  echo "Added PATH export to $RC_FILE"
fi

echo "Run 'source $RC_FILE' (or restart your shell) to apply it now."
