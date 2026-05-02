#!/usr/bin/env bash

# Close popups on global mouse exit
if [ "$SENDER" = "mouse.exited.global" ]; then
    sketchybar --set clock popup.drawing=off
    exit 0
fi

sketchybar --set $NAME label="$(date '+%a %Y-%m-%d  %H:%M')"
