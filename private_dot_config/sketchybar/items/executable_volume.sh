#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"

sketchybar --add item volume right \
    --set volume \
        icon.color=$SAPPHIRE \
        icon.font="$FONT:Bold:18.0" \
        label.font="$FONT:Bold:14.0" \
        script="$PLUGIN_DIR/volume.sh" \
    --subscribe volume volume_change mouse.clicked mouse.scrolled
