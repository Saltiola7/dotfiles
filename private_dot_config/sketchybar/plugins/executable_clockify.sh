#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"

CLOCKIFY_API="https://api.clockify.me/api/v1"
CACHE_DIR="/tmp/sketchybar_clockify"
mkdir -p "$CACHE_DIR"

# Load API key (cached to avoid repeated 1Password calls)
get_api_key() {
    if [ -f "$CACHE_DIR/api_key" ]; then
        cat "$CACHE_DIR/api_key"
    else
        local key
        key="$(op read 'op://Personal/Clockify API Key/credential' 2>/dev/null)"
        if [ -n "$key" ]; then
            echo "$key" > "$CACHE_DIR/api_key"
            chmod 600 "$CACHE_DIR/api_key"
            echo "$key"
        fi
    fi
}

# Get and cache user info (workspace ID + user ID)
get_user_info() {
    if [ -f "$CACHE_DIR/workspace_id" ] && [ -f "$CACHE_DIR/user_id" ]; then
        return 0
    fi
    local api_key="$1"
    local user_json
    user_json="$(curl -sf -H "X-Api-Key: $api_key" "$CLOCKIFY_API/user" 2>/dev/null)"
    if [ -n "$user_json" ]; then
        echo "$user_json" | jq -r '.activeWorkspace' > "$CACHE_DIR/workspace_id"
        echo "$user_json" | jq -r '.id' > "$CACHE_DIR/user_id"
        return 0
    fi
    return 1
}

# Format seconds into H:MM:SS
format_duration() {
    local total_seconds="$1"
    local hours=$((total_seconds / 3600))
    local minutes=$(( (total_seconds % 3600) / 60))
    local seconds=$((total_seconds % 60))
    printf "%d:%02d:%02d" "$hours" "$minutes" "$seconds"
}

# Stop the running timer
stop_timer() {
    local api_key
    api_key="$(get_api_key)"
    [ -z "$api_key" ] && exit 1

    get_user_info "$api_key" || exit 1
    local workspace_id user_id
    workspace_id="$(cat "$CACHE_DIR/workspace_id")"
    user_id="$(cat "$CACHE_DIR/user_id")"

    local now
    now="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

    curl -sf -X PATCH \
        -H "X-Api-Key: $api_key" \
        -H "Content-Type: application/json" \
        -d "{\"end\": \"$now\"}" \
        "$CLOCKIFY_API/workspaces/$workspace_id/user/$user_id/time-entries" \
        >/dev/null 2>&1

    sketchybar --set clockify drawing=off
    exit 0
}

# Handle stop command
if [ "$1" = "stop" ]; then
    stop_timer
fi

# Close popup on mouse exit
if [ "$SENDER" = "mouse.exited.global" ]; then
    sketchybar --set clockify popup.drawing=off
    exit 0
fi

# Poll Clockify for running timer
api_key="$(get_api_key)"
if [ -z "$api_key" ]; then
    sketchybar --set $NAME drawing=off
    exit 0
fi

get_user_info "$api_key" || { sketchybar --set $NAME drawing=off; exit 0; }
workspace_id="$(cat "$CACHE_DIR/workspace_id")"
user_id="$(cat "$CACHE_DIR/user_id")"

# Get most recent time entry for this user
running_json="$(curl -sf -H "X-Api-Key: $api_key" \
    "$CLOCKIFY_API/workspaces/$workspace_id/user/$user_id/time-entries?page-size=1" 2>/dev/null)"

if [ -z "$running_json" ] || [ "$running_json" = "[]" ]; then
    sketchybar --set $NAME drawing=off
    exit 0
fi

# Check if the entry is actually in-progress (end is null)
end_time="$(echo "$running_json" | jq -r '.[0].timeInterval.end // empty' 2>/dev/null)"
if [ -n "$end_time" ] && [ "$end_time" != "null" ]; then
    sketchybar --set $NAME drawing=off
    exit 0
fi

# Parse the running entry
start_time="$(echo "$running_json" | jq -r '.[0].timeInterval.start' 2>/dev/null)"
description="$(echo "$running_json" | jq -r '.[0].description // empty' 2>/dev/null)"
project_id="$(echo "$running_json" | jq -r '.[0].projectId // empty' 2>/dev/null)"

if [ -z "$start_time" ] || [ "$start_time" = "null" ]; then
    sketchybar --set $NAME drawing=off
    exit 0
fi

# Calculate elapsed time (TZ=UTC because Clockify returns UTC timestamps)
start_epoch="$(TZ=UTC date -jf '%Y-%m-%dT%H:%M:%SZ' "$start_time" '+%s' 2>/dev/null)"
if [ -z "$start_epoch" ]; then
    # Try alternate format with fractional seconds
    clean_time="$(echo "$start_time" | sed 's/\.[0-9]*Z$/Z/')"
    start_epoch="$(TZ=UTC date -jf '%Y-%m-%dT%H:%M:%SZ' "$clean_time" '+%s' 2>/dev/null)"
fi

if [ -z "$start_epoch" ]; then
    sketchybar --set $NAME drawing=off
    exit 0
fi

now_epoch="$(date -u '+%s')"
elapsed=$((now_epoch - start_epoch))
duration="$(format_duration $elapsed)"

# Get project name if available (cached)
project_label=""
if [ -n "$project_id" ] && [ "$project_id" != "null" ]; then
    cache_file="$CACHE_DIR/project_$project_id"
    if [ -f "$cache_file" ]; then
        project_label="$(cat "$cache_file")"
    else
        project_json="$(curl -sf -H "X-Api-Key: $api_key" \
            "$CLOCKIFY_API/workspaces/$workspace_id/projects/$project_id" 2>/dev/null)"
        if [ -n "$project_json" ]; then
            project_label="$(echo "$project_json" | jq -r '.name // empty')"
            [ -n "$project_label" ] && echo "$project_label" > "$cache_file"
        fi
    fi
fi

# Build display label
if [ -n "$description" ]; then
    label="$description $duration"
elif [ -n "$project_label" ]; then
    label="$project_label $duration"
else
    label="$duration"
fi

# Color based on elapsed time (green < 2h, yellow < 4h, peach < 6h, red 6h+)
if [ $elapsed -ge 21600 ]; then
    icon_color="$RED"
elif [ $elapsed -ge 14400 ]; then
    icon_color="$PEACH"
elif [ $elapsed -ge 7200 ]; then
    icon_color="$YELLOW"
else
    icon_color="$GREEN"
fi

sketchybar --set $NAME \
    label="$label" \
    icon.color="$icon_color" \
    drawing=on
