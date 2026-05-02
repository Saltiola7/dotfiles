#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"

sketchybar --add item cpu right \
    --set cpu \
        icon=$ICON_CPU \
        icon.color=$PEACH \
        label.font="$FONT:Bold:14.0" \
        update_freq=5 \
        script="$PLUGIN_DIR/cpu.sh" \
        click_script="open -a 'Activity Monitor'"
