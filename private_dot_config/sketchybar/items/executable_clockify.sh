#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"

ICON_CLOCKIFY="󱎫"

sketchybar --add item clockify center \
    --set clockify \
        icon="$ICON_CLOCKIFY" \
        icon.color=$GREEN \
        icon.font="$FONT:Bold:16.0" \
        label.font="$FONT:Regular:13.0" \
        label.color=$SUBTEXT1 \
        label.max_chars=40 \
        update_freq=30 \
        drawing=off \
        script="$PLUGIN_DIR/clockify.sh" \
        click_script="sketchybar --set \$NAME popup.drawing=toggle" \
        popup.background.color=$MANTLE \
        popup.background.corner_radius=12 \
        popup.background.border_color=$SURFACE1 \
        popup.background.border_width=1 \
        popup.blur_radius=20 \
        popup.height=35 \
        popup.align=center \
    --subscribe clockify mouse.clicked mouse.exited.global

# Popup: stop timer
sketchybar --add item clockify.stop popup.clockify \
    --set clockify.stop \
        icon="󰓛  Stop Timer" \
        icon.color=$RED \
        icon.padding_left=10 \
        icon.font="$FONT:Bold:14.0" \
        label.drawing=off \
        click_script="$PLUGIN_DIR/clockify.sh stop; sketchybar --set clockify popup.drawing=off"

# Popup: open Clockify
sketchybar --add item clockify.open popup.clockify \
    --set clockify.open \
        icon="󰏌  Open Clockify" \
        icon.color=$SAPPHIRE \
        icon.padding_left=10 \
        icon.font="$FONT:Bold:14.0" \
        label.drawing=off \
        click_script="open 'https://app.clockify.me/tracker'; sketchybar --set clockify popup.drawing=off"
