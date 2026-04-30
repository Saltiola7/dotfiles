#!/bin/bash
# Install graphify via uv and configure for Claude Code + OpenCode

if ! command -v uv &>/dev/null; then
    echo "uv not found. Cannot install graphify." >&2
    exit 1
fi

echo "Installing graphify via uv..."
uv tool install --force --python python3.12 graphifyy &&

echo "Installing graphify skill for Claude Code..." &&
graphify install &&

echo "Installing graphify skill for OpenCode..." &&
graphify install --platform opencode &&

# OpenCode loads slash-command skills from ~/.agents/skills/, but
# graphify install --platform opencode writes to ~/.config/opencode/skills/.
# Copy the skill so /graphify shows up in OpenCode's command palette.
echo "Registering graphify in ~/.agents/skills/ for OpenCode slash commands..." &&
mkdir -p ~/.agents/skills/graphify &&
cp ~/.config/opencode/skills/graphify/SKILL.md ~/.agents/skills/graphify/SKILL.md
