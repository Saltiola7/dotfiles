#!/usr/bin/env bash

COUNT=$(brew outdated --quiet 2>/dev/null | wc -l | tr -d ' ')

if [ "$COUNT" -gt 0 ]; then
    sketchybar --set $NAME label="$COUNT" drawing=on
    if [ "$COUNT" -gt 10 ]; then
        sketchybar --set $NAME icon.color="0xfff38ba8"  # red
    elif [ "$COUNT" -gt 5 ]; then
        sketchybar --set $NAME icon.color="0xfffab387"  # peach
    else
        sketchybar --set $NAME icon.color="0xffb4befe"  # lavender
    fi
else
    sketchybar --set $NAME drawing=off
fi
