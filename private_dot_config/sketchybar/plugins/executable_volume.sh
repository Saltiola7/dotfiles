#!/usr/bin/env bash

source "$CONFIG_DIR/icons.sh"
source "$CONFIG_DIR/colors.sh"

valid_volume() {
    [[ "$1" =~ ^([0-9]|[1-9][0-9]|100)$ ]]
}

read_state() {
    VOLUME=$(osascript -e 'output volume of (get volume settings)' 2>/dev/null) &&
        MUTED=$(osascript -e 'output muted of (get volume settings)' 2>/dev/null) &&
        valid_volume "$VOLUME" && [[ "$MUTED" = true || "$MUTED" = false ]]
}

show_error() {
    sketchybar --set volume icon="$ICON_VOLUME_MUTE" icon.color="$OVERLAY0" \
        --set volume.slider slider.background.drawing=off slider.knob.drawing=off \
            label="$1" label.width=150 \
        --set volume.mute label=Mute
}

if [[ "$SENDER" = mouse.exited.global ]]; then
    sketchybar --set volume popup.drawing=off
    exit 0
fi

if [[ "$SENDER" = mouse.clicked && "$NAME" = volume ]]; then
    case "$BUTTON" in
        left) sketchybar --set volume popup.drawing=toggle ;;
        right) open "x-apple.systempreferences:com.apple.Sound-Settings.extension" ;;
    esac
fi

if ! read_state; then
    if [[ "$SENDER" = mouse.clicked && "$NAME" = volume.mute ]]; then
        open "x-apple.systempreferences:com.apple.Sound-Settings.extension"
    fi
    show_error Unavailable
    exit 0
fi

REQUESTED_VOLUME=""
REQUESTED_MUTE=""
case "$SENDER:$NAME" in
    mouse.clicked:volume.slider)
        if [[ "$BUTTON" = left ]] && valid_volume "${PERCENTAGE:-}"; then
            REQUESTED_VOLUME=$PERCENTAGE
        fi
        ;;
    mouse.clicked:volume.mute)
        if [[ "$BUTTON" = left ]]; then
            if [[ "$MUTED" = true ]]; then REQUESTED_MUTE=false; else REQUESTED_MUTE=true; fi
        fi
        ;;
    mouse.scrolled:volume)
        if [[ "${SCROLL_DELTA:-}" =~ ^-?[0-9]{1,4}$ ]]; then
            DELTA=$((10#${SCROLL_DELTA#-}))
            [[ "$SCROLL_DELTA" = -* ]] && DELTA=$((-DELTA))
            REQUESTED_VOLUME=$((VOLUME + DELTA * 5))
            (( REQUESTED_VOLUME > 100 )) && REQUESTED_VOLUME=100
            (( REQUESTED_VOLUME < 0 )) && REQUESTED_VOLUME=0
        fi
        ;;
esac

if [[ -n "$REQUESTED_VOLUME" ]]; then
    # Preserve mute; the popup exposes a separate explicit mute action.
    if ! osascript -e "set volume output volume $REQUESTED_VOLUME" \
        -e "set volume output muted $MUTED" >/dev/null 2>&1; then
        show_error Device-controlled
        exit 0
    fi
elif [[ -n "$REQUESTED_MUTE" ]]; then
    if ! osascript -e 'set volume output muted (not (output muted of (get volume settings)))' >/dev/null 2>&1; then
        show_error Device-controlled
        exit 0
    fi
fi

if [[ -n "$REQUESTED_VOLUME$REQUESTED_MUTE" ]]; then
    if ! read_state; then show_error Unavailable; exit 0; fi
    if { [[ -n "$REQUESTED_VOLUME" ]] && (( VOLUME < REQUESTED_VOLUME - 1 || VOLUME > REQUESTED_VOLUME + 1 )); } ||
        { [[ -n "$REQUESTED_MUTE" && "$MUTED" != "$REQUESTED_MUTE" ]]; }; then
        show_error Device-controlled
        exit 0
    fi
fi

COLOR=$SAPPHIRE
MUTE_LABEL=Mute
if [[ "$MUTED" = true ]]; then
    ICON=$ICON_VOLUME_MUTE
    COLOR=$OVERLAY0
    MUTE_LABEL=Unmute
elif (( VOLUME > 66 )); then ICON=$ICON_VOLUME_HIGH
elif (( VOLUME > 33 )); then ICON=$ICON_VOLUME_MED
elif (( VOLUME > 0 )); then ICON=$ICON_VOLUME_LOW
else ICON=$ICON_VOLUME_MUTE
fi

sketchybar --set volume icon="$ICON" icon.color="$COLOR" \
    --set volume.slider slider.percentage="$VOLUME" label="${VOLUME}%" label.width=45 \
        slider.background.drawing=on slider.knob.drawing=on \
    --set volume.mute label="$MUTE_LABEL"
