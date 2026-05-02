#!/usr/bin/env bash

# Close popup on mouse exit
if [ "$SENDER" = "mouse.exited.global" ]; then
    sketchybar --set docker popup.drawing=off
    exit 0
fi

COUNT=$(docker ps --format '{{.Names}}' 2>/dev/null | wc -l | tr -d ' ')

if [ "$COUNT" -gt 0 ]; then
    sketchybar --set $NAME label="$COUNT" drawing=on

    # Rebuild popup with container list grouped by compose project
    # First remove old popup items
    EXISTING=$(sketchybar --query $NAME 2>/dev/null | grep -o '"docker\.container\.[^"]*"' | tr -d '"')
    for old in $EXISTING; do
        sketchybar --remove "$old" 2>/dev/null
    done

    # Add containers grouped by project prefix
    INDEX=0
    docker ps --format '{{.Names}}|{{.Status}}' 2>/dev/null | sort | while IFS='|' read -r CNAME STATUS; do
        # Extract short status (e.g. "Up 2 minutes" -> "Up 2m")
        SHORT_STATUS=$(echo "$STATUS" | sed 's/ minutes\?/m/;s/ hours\?/h/;s/ days\?/d/;s/ seconds\?/s/;s/ (healthy)//;s/ (unhealthy)/!/;s/Up /↑/')
        sketchybar --add item "docker.container.$INDEX" popup.docker \
            --set "docker.container.$INDEX" \
                icon.drawing=off \
                label="$CNAME  $SHORT_STATUS" \
                label.font="Monofur Nerd Font:Regular:12.0" \
                label.color="0xffcdd6f4" \
                label.padding_left=10 \
                label.padding_right=10
        INDEX=$((INDEX + 1))
    done
else
    sketchybar --set $NAME drawing=off
fi
