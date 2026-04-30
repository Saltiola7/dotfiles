#!/bin/bash
# Install agent skills via npx skills CLI (non-interactive)

if ! command -v npx &>/dev/null; then
    echo "npx not found. Cannot install skills." >&2
    exit 1
fi

echo "Installing find-skills..."
npx -y skills add vercel-labs/skills --skill find-skills -g --all &&

echo "Installing caveman skills..."
npx -y skills add JuliusBrussee/caveman -g --all
