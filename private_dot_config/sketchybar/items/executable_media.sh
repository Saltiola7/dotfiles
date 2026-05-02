#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"

sketchybar --add item media center \
    --set media \
        icon=$ICON_MEDIA_MUSIC \
        icon.color=$MAUVE \
        label.font="$FONT:Regular:13.0" \
        label.color=$SUBTEXT1 \
        label.max_chars=50 \
        scroll_texts=on \
        update_freq=5 \
        script="$PLUGIN_DIR/media.sh" \
        click_script="sketchybar --set \$NAME popup.drawing=toggle" \
        popup.background.color=$MANTLE \
        popup.background.corner_radius=12 \
        popup.background.border_color=$SURFACE1 \
        popup.background.border_width=1 \
        popup.blur_radius=20 \
        popup.height=35 \
        popup.align=center \
    --subscribe media mouse.clicked mouse.exited.global

# Popup: play/pause toggle
sketchybar --add item media.playpause popup.media \
    --set media.playpause \
        icon="󰐊  Play / Pause" \
        icon.color=$MAUVE \
        icon.padding_left=10 \
        icon.font="$FONT:Bold:14.0" \
        label.drawing=off \
        click_script="nowplaying-cli togglePlayPause 2>/dev/null; sketchybar --set media popup.drawing=off"

# Popup: next track
sketchybar --add item media.next popup.media \
    --set media.next \
        icon="󰒭  Next Track" \
        icon.color=$TEAL \
        icon.padding_left=10 \
        icon.font="$FONT:Bold:14.0" \
        label.drawing=off \
        click_script="nowplaying-cli next 2>/dev/null; sketchybar --set media popup.drawing=off"

# Popup: open app
sketchybar --add item media.open popup.media \
    --set media.open \
        icon="󰏌  Open Brain.fm" \
        icon.color=$SAPPHIRE \
        icon.padding_left=10 \
        icon.font="$FONT:Bold:14.0" \
        label.drawing=off \
        click_script="open -b 'com.electron.brain.fm'; sketchybar --set media popup.drawing=off"
