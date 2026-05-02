#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"

ICON_DOCKER="󰡨"

sketchybar --add item docker right \
    --set docker \
        icon="$ICON_DOCKER" \
        icon.color=$BLUE \
        icon.font="$FONT:Bold:18.0" \
        label.font="$FONT:Bold:14.0" \
        update_freq=30 \
        script="$PLUGIN_DIR/docker.sh" \
        click_script="sketchybar --set \$NAME popup.drawing=toggle" \
        popup.background.color=$MANTLE \
        popup.background.corner_radius=12 \
        popup.background.border_color=$SURFACE1 \
        popup.background.border_width=1 \
        popup.blur_radius=20 \
        popup.height=28 \
        popup.align=right \
    --subscribe docker mouse.exited.global
