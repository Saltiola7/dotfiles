#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"

ICON_BREW="󰏔"

sketchybar --add item brew right \
    --set brew \
        icon="$ICON_BREW" \
        icon.color=$LAVENDER \
        label.font="$FONT:Bold:14.0" \
        update_freq=1800 \
        script="$PLUGIN_DIR/brew.sh" \
        click_script="kitten quick-access-terminal bash -c 'brew update && brew upgrade; echo; echo \"Done. Press enter to close.\"; read'" \
    --subscribe brew system_woke
