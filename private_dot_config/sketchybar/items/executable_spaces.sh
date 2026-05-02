#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"

# Register aerospace workspace change event
sketchybar --add event aerospace_workspace_change

# Create space items for each AeroSpace workspace
for sid in $(aerospace list-workspaces --all); do
    sketchybar --add item space.$sid left \
        --subscribe space.$sid aerospace_workspace_change \
        --set space.$sid \
            background.color=$SURFACE0 \
            background.corner_radius=5 \
            background.height=22 \
            background.drawing=off \
            icon.drawing=off \
            label="$sid" \
            label.font="$FONT:Bold:13.0" \
            label.color=$SUBTEXT0 \
            label.padding_left=8 \
            label.padding_right=8 \
            padding_left=2 \
            padding_right=2 \
            click_script="aerospace workspace $sid" \
            script="$PLUGIN_DIR/aerospace.sh $sid"
done

# Separator after workspaces
sketchybar --add item space_separator left \
    --set space_separator \
        icon="│" \
        icon.color=$OVERLAY0 \
        icon.font="$FONT:Regular:16.0" \
        icon.padding_left=8 \
        icon.padding_right=4 \
        label.drawing=off \
        background.drawing=off
