#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"
source "$CONFIG_DIR/icons.sh"

APPLE_ICON="$ICON_APPLE"

# Apple logo with popup menu
sketchybar --add item apple left \
    --set apple \
        icon="$APPLE_ICON" \
        icon.font="$FONT:Bold:18.0" \
        icon.color=$MAUVE \
        icon.padding_left=8 \
        icon.padding_right=4 \
        label.drawing=off \
        background.color=$TRANSPARENT \
        click_script="sketchybar --set \$NAME popup.drawing=toggle" \
        popup.background.color=$MANTLE \
        popup.background.corner_radius=12 \
        popup.background.border_color=$SURFACE1 \
        popup.background.border_width=1 \
        popup.blur_radius=20 \
        popup.height=35

# Popup items
sketchybar --add item apple.about popup.apple \
    --set apple.about \
        icon="󰀵" \
        icon.color=$MAUVE \
        icon.padding_left=10 \
        label="About This Mac" \
        label.color=$TEXT \
        label.font="$FONT:Regular:13.0" \
        click_script="open 'x-apple.systempreferences:com.apple.SystemProfiler.AboutExtension'; sketchybar --set apple popup.drawing=off"

sketchybar --add item apple.settings popup.apple \
    --set apple.settings \
        icon="󰒓" \
        icon.color=$BLUE \
        icon.padding_left=10 \
        label="System Settings..." \
        label.color=$TEXT \
        label.font="$FONT:Regular:13.0" \
        click_script="open -a 'System Settings'; sketchybar --set apple popup.drawing=off"

sketchybar --add item apple.forcequit popup.apple \
    --set apple.forcequit \
        icon="󰅙" \
        icon.color=$RED \
        icon.padding_left=10 \
        label="Force Quit..." \
        label.color=$TEXT \
        label.font="$FONT:Regular:13.0" \
        click_script="open -a 'Force Quit Applications'; sketchybar --set apple popup.drawing=off"

sketchybar --add item apple.lock popup.apple \
    --set apple.lock \
        icon="󰌾" \
        icon.color=$YELLOW \
        icon.padding_left=10 \
        label="Lock Screen" \
        label.color=$TEXT \
        label.font="$FONT:Regular:13.0" \
        click_script="osascript -e 'tell application \"System Events\" to keystroke \"q\" using {command down, control down}'; sketchybar --set apple popup.drawing=off"

sketchybar --add item apple.sleep popup.apple \
    --set apple.sleep \
        icon="󰒲" \
        icon.color=$TEAL \
        icon.padding_left=10 \
        label="Sleep" \
        label.color=$TEXT \
        label.font="$FONT:Regular:13.0" \
        click_script="pmset sleepnow; sketchybar --set apple popup.drawing=off"

sketchybar --add item apple.restart popup.apple \
    --set apple.restart \
        icon="󰜉" \
        icon.color=$PEACH \
        icon.padding_left=10 \
        label="Restart..." \
        label.color=$TEXT \
        label.font="$FONT:Regular:13.0" \
        click_script="osascript -e 'tell application \"loginwindow\" to «event aevtrrst»'; sketchybar --set apple popup.drawing=off"

sketchybar --add item apple.shutdown popup.apple \
    --set apple.shutdown \
        icon="󰐥" \
        icon.color=$RED \
        icon.padding_left=10 \
        label="Shut Down..." \
        label.color=$TEXT \
        label.font="$FONT:Regular:13.0" \
        click_script="osascript -e 'tell application \"loginwindow\" to «event aevtrsdn»'; sketchybar --set apple popup.drawing=off"
