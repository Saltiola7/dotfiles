#!/usr/bin/env bash

MEMORY_USAGE=$(memory_pressure | grep "System-wide memory free percentage:" | awk '{ printf "%02.0f%%", 100 - $5 }')

sketchybar --set $NAME label="$MEMORY_USAGE"
