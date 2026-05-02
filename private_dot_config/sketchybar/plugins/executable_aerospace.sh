#!/usr/bin/env bash

# Count windows in this workspace
WINDOW_COUNT=$(aerospace list-windows --workspace "$1" 2>/dev/null | wc -l | tr -d ' ')

# Convert count to Unicode superscript for badge effect
to_superscript() {
    echo "$1" | sed 'y/0123456789/⁰¹²³⁴⁵⁶⁷⁸⁹/'
}

# Build label: workspace ID + superscript badge if windows exist
if [ "$WINDOW_COUNT" -gt 0 ] 2>/dev/null; then
    BADGE="$(to_superscript "$WINDOW_COUNT")"
    LABEL="$1$BADGE"
else
    LABEL="$1"
fi

# Highlight the focused AeroSpace workspace
if [ "$1" = "$FOCUSED_WORKSPACE" ]; then
    sketchybar --set $NAME \
        label="$LABEL" \
        background.drawing=on \
        background.color=0xffcba6f7 \
        label.color=0xff1e1e2e
else
    sketchybar --set $NAME \
        label="$LABEL" \
        background.drawing=off \
        label.color=0xffa6adc8
fi
