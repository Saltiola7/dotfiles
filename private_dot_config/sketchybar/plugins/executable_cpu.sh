#!/usr/bin/env bash

CPU_USAGE=$(top -l 2 -n 0 | grep -E "^CPU" | tail -1 | awk '{ printf "%.0f%%", $3 + $5 }')

sketchybar --set $NAME label="$CPU_USAGE"
