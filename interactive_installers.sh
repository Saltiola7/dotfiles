#!/bin/bash
# Interactive Installers
# Run this script manually on a new machine after `chezmoi apply`.
# Each section prompts for confirmation before running.
#
# Usage:
#   bash "$(chezmoi source-path)/interactive_installers.sh"
#
# Note: Most installers are now automated via chezmoi run_once scripts:
#   - Homebrew: run_onchange_before_brew-bundle.sh.tmpl
#   - uv:      run_once_before_install-uv.sh
#   - aider:   run_once_install-aider.sh
#   - xonsh:   run_once_install-xonsh.sh
#   - graphify: run_once_install-graphify.sh
#   - skills:  run_once_install-skills.sh
#
# Add sections here only for truly interactive installers that cannot
# be automated with CLI flags.

set -e

echo "=== Interactive Installers ==="
echo "No interactive installers currently configured."
echo "All installers are automated via chezmoi apply."
