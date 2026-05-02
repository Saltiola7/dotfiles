#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"

ICON_DISK="󰋊"

sketchybar --add item disk right \
    --set disk \
        icon="$ICON_DISK" \
        icon.color=$MAROON \
        label.font="$FONT:Bold:14.0" \
        update_freq=120 \
        script="$PLUGIN_DIR/disk.sh" \
        click_script="open -a 'Disk Utility'"
