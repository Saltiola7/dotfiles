#!/bin/bash
# Ensure uv (Python package manager) is installed.
# Required by kitty-query.py which uses PEP 723 inline script metadata.
# uv will be installed via mise if available, otherwise via the official installer.

if command -v uv &>/dev/null; then
    exit 0
fi

if command -v mise &>/dev/null; then
    mise use --global uv@latest
elif command -v curl &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "Warning: cannot install uv (no mise or curl). kitty-workspace scripts will not work." >&2
    echo "Install uv manually: https://docs.astral.sh/uv/getting-started/installation/" >&2
fi
