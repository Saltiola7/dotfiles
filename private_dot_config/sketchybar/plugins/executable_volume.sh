#!/usr/bin/env bash

source "$CONFIG_DIR/icons.sh"

update_icon() {
    VOLUME="$1"
    MUTED="$2"

    if [ "$MUTED" = "true" ]; then
        ICON="$ICON_VOLUME_MUTE"
        COLOR="0xff6c7086"  # overlay0
    elif [ "$VOLUME" -gt 66 ]; then
        ICON="$ICON_VOLUME_HIGH"
        COLOR="0xff74c7ec"  # sapphire
    elif [ "$VOLUME" -gt 33 ]; then
        ICON="$ICON_VOLUME_MED"
        COLOR="0xff74c7ec"
    elif [ "$VOLUME" -gt 0 ]; then
        ICON="$ICON_VOLUME_LOW"
        COLOR="0xff74c7ec"
    else
        ICON="$ICON_VOLUME_MUTE"
        COLOR="0xff6c7086"
    fi

    if [ "$MUTED" = "true" ]; then
        sketchybar --set $NAME icon="$ICON" icon.color="$COLOR" label="muted"
    else
        sketchybar --set $NAME icon="$ICON" icon.color="$COLOR" label="${VOLUME}%"
    fi
}

case "$SENDER" in
    mouse.clicked)
        if [ "$BUTTON" = "left" ]; then
            # Toggle mute
            osascript -e 'set volume output muted (not (output muted of (get volume settings)))'
        elif [ "$BUTTON" = "right" ]; then
            # Open Sound settings
            open "x-apple.systempreferences:com.apple.Sound-Settings.extension"
        fi
        ;;
    mouse.scrolled)
        VOLUME="$(osascript -e 'output volume of (get volume settings)')"
        NEW_VOL=$((VOLUME + SCROLL_DELTA * 5))
        [ $NEW_VOL -gt 100 ] && NEW_VOL=100
        [ $NEW_VOL -lt 0 ] && NEW_VOL=0
        osascript -e "set volume output volume $NEW_VOL"
        ;;
esac

# Always update the display
VOLUME="$(osascript -e 'output volume of (get volume settings)')"
MUTED="$(osascript -e 'output muted of (get volume settings)')"
update_icon "$VOLUME" "$MUTED"
