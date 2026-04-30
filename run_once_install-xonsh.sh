#!/bin/bash
# Install xonsh via uv (with xontribs bundled)

if ! command -v uv &>/dev/null; then
    echo "uv not found. Cannot install xonsh." >&2
    exit 1
fi

echo "Installing xonsh via uv..."
uv tool install --force --python python3.12 \
    --with xontrib-kitty \
    'xonsh[full]'
