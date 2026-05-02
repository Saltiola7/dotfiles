#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"

sketchybar --add item memory right \
    --set memory \
        icon=$ICON_MEMORY \
        icon.color=$GREEN \
        label.font="$FONT:Bold:14.0" \
        update_freq=15 \
        script="$PLUGIN_DIR/memory.sh" \
        click_script="open -a 'Activity Monitor'"
