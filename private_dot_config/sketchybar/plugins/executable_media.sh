#!/usr/bin/env bash

source "$CONFIG_DIR/icons.sh"

# Close popup on mouse exit
if [ "$SENDER" = "mouse.exited.global" ]; then
    sketchybar --set media popup.drawing=off
    exit 0
fi

# Right-click play/pause (without opening popup)
if [ "$SENDER" = "mouse.clicked" ] && [ "$BUTTON" = "right" ]; then
    nowplaying-cli togglePlayPause 2>/dev/null
    exit 0
fi

# Poll now-playing info
if ! command -v nowplaying-cli &>/dev/null; then
    sketchybar --set $NAME drawing=off
    exit 0
fi

TITLE="$(nowplaying-cli get title 2>/dev/null)"
ARTIST="$(nowplaying-cli get artist 2>/dev/null)"
RATE="$(nowplaying-cli get playbackRate 2>/dev/null)"

[ "$TITLE" = "null" ] || [ "$TITLE" = "(null)" ] && TITLE=""
[ "$ARTIST" = "null" ] || [ "$ARTIST" = "(null)" ] && ARTIST=""

if [ -n "$TITLE" ]; then
    if [ "$RATE" = "1" ] || [ "$RATE" = "1.0" ]; then
        ICON="$ICON_MEDIA_PLAY"
    else
        ICON="$ICON_MEDIA_PAUSE"
    fi

    if [ -n "$ARTIST" ]; then
        LABEL="${TITLE} - ${ARTIST}"
    else
        LABEL="$TITLE"
    fi

    sketchybar --set $NAME label="$LABEL" icon="$ICON" drawing=on
else
    sketchybar --set $NAME drawing=off
fi
