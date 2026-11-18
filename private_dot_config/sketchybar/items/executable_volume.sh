#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"

sketchybar --add item volume right \
    --set volume \
        icon.color=$SAPPHIRE \
        icon.font="$FONT:Bold:18.0" \
        label.drawing=off \
        script="$PLUGIN_DIR/volume.sh" \
        popup.drawing=off \
        popup.align=center \
        popup.height=35 \
        popup.background.color=$MANTLE \
        popup.background.corner_radius=12 \
        popup.background.border_color=$SURFACE1 \
        popup.background.border_width=1 \
    --subscribe volume volume_change system_woke mouse.clicked mouse.scrolled mouse.exited.global

sketchybar --add slider volume.slider popup.volume 120 \
    --set volume.slider \
        icon.drawing=off \
        label.font="$FONT:Bold:14.0" \
        label.width=45 \
        slider.highlight_color=$SAPPHIRE \
        slider.background.color=$SURFACE1 \
        slider.background.height=5 \
        slider.background.corner_radius=3 \
        slider.knob="●" \
        slider.knob.color=$TEXT \
        padding_left=12 \
        padding_right=12 \
        script="$PLUGIN_DIR/volume.sh" \
    --subscribe volume.slider mouse.clicked

sketchybar --add item volume.mute popup.volume \
    --set volume.mute \
        icon="$ICON_VOLUME_MUTE" \
        label=Mute \
        padding_left=12 \
        script="$PLUGIN_DIR/volume.sh" \
    --subscribe volume.mute mouse.clicked
