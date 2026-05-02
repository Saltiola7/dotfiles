#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"

sketchybar --add item clock right \
    --set clock \
        icon=$ICON_CLOCK \
        icon.color=$YELLOW \
        label.font="$FONT:Bold:14.0" \
        update_freq=10 \
        script="$PLUGIN_DIR/clock.sh" \
        click_script="sketchybar --set \$NAME popup.drawing=toggle" \
        popup.background.color=$MANTLE \
        popup.background.corner_radius=12 \
        popup.background.border_color=$SURFACE1 \
        popup.background.border_width=1 \
        popup.blur_radius=20 \
        popup.height=35 \
    --subscribe clock system_woke mouse.exited.global

# Popup: full date + open Calendar link
sketchybar --add item clock.date popup.clock \
    --set clock.date \
        icon="󰃭" \
        icon.color=$YELLOW \
        icon.padding_left=10 \
        label="$(date '+%A, %Y-%m-%d')" \
        label.color=$TEXT \
        label.font="$FONT:Regular:13.0" \
        update_freq=3600 \
        script="sketchybar --set \$NAME label=\"\$(date '+%A, %Y-%m-%d')\""

sketchybar --add item clock.cal popup.clock \
    --set clock.cal \
        icon="󰃶" \
        icon.color=$GREEN \
        icon.padding_left=10 \
        label="Open Calendar" \
        label.color=$SUBTEXT1 \
        label.font="$FONT:Regular:13.0" \
        click_script="open -a Calendar; sketchybar --set clock popup.drawing=off"
