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

# Poll now-playing info. Controls above never wait for a metadata refresh.
if ! command -v nowplaying-cli &>/dev/null ||
   ! command -v jq &>/dev/null ||
   ! command -v lockf &>/dev/null; then
    sketchybar --set "$NAME" drawing=off
    exit 0
fi

# Keep descriptor 9 open so kernel ownership covers this refresh and its children.
# Retain the file: removing it would let another refresh lock a different inode.
umask 077
exec 9<>"${TMPDIR:-/tmp}/sketchybar-media-${UID}.lock" || exit 0
lockf -s -t 0 9 2>/dev/null || exit 0

METADATA="$(nowplaying-cli get --json title artist playbackRate 2>/dev/null)" || METADATA=""
TITLE="$(printf '%s' "$METADATA" | jq -r '.title | strings' 2>/dev/null)" || TITLE=""
ARTIST="$(printf '%s' "$METADATA" | jq -r '.artist | strings' 2>/dev/null)" || ARTIST=""
RATE="$(printf '%s' "$METADATA" | jq -r '.playbackRate | select(type == "number" or type == "string")' 2>/dev/null)" || RATE=""

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

    sketchybar --set "$NAME" label="$LABEL" icon="$ICON" drawing=on
else
    sketchybar --set "$NAME" drawing=off
fi
