#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"

sketchybar --add item front_app left \
    --set front_app \
        icon.font="sketchybar-app-font:Regular:16.0" \
        icon.color=$TEXT \
        icon.padding_left=8 \
        icon.padding_right=4 \
        label.font="$FONT:Bold:14.0" \
        label.color=$TEXT \
        background.color=$SURFACE0 \
        background.corner_radius=5 \
        background.height=22 \
        label.padding_left=4 \
        label.padding_right=8 \
        script="$PLUGIN_DIR/front_app.sh" \
        click_script="open -a \"\$(sketchybar --query front_app | jq -r '.label.value')\"" \
    --subscribe front_app front_app_switched
