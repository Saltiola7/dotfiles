#!/bin/bash
# Install aider via uv

if ! command -v uv &>/dev/null; then
    echo "uv not found. Cannot install aider." >&2
    exit 1
fi

echo "Installing aider via uv..."
uv tool install --force --python python3.12 --with pip aider-chat@latest