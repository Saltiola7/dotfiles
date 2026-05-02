#!/usr/bin/env bash

# Get disk usage for APFS Data volume (/ only shows root snapshot on macOS)
DISK_INFO=$(df -H /System/Volumes/Data 2>/dev/null | tail -1)
AVAIL=$(echo "$DISK_INFO" | awk '{print $4}')
PCT=$(echo "$DISK_INFO" | awk '{print $5}' | tr -d '%')

# Color based on usage (higher = worse)
if [ "$PCT" -gt 90 ] 2>/dev/null; then
    COLOR="0xfff38ba8"  # red
elif [ "$PCT" -gt 75 ] 2>/dev/null; then
    COLOR="0xfffab387"  # peach
elif [ "$PCT" -gt 60 ] 2>/dev/null; then
    COLOR="0xfff9e2af"  # yellow
else
    COLOR="0xffeba0ac"  # maroon
fi

sketchybar --set $NAME label="${AVAIL}" icon.color="$COLOR"
