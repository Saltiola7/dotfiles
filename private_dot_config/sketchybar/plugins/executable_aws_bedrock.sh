#!/usr/bin/env bash

AWS_PROFILE="BedrockDeveloperAccess-302432775606"
AWS_BIN="/usr/local/bin/aws"
LOG_FILE="$HOME/Library/Logs/aws-sso-login.log"
SESSION_HOURS=8
RECOVERY_LOCKFILE="/tmp/sketchybar_aws_recovery_lock"

# ── 1. STS Probe: is the token actually valid right now? ──
STS_OUTPUT=$("$AWS_BIN" sts get-caller-identity --profile "$AWS_PROFILE" 2>&1)
STS_RC=$?

if [ $STS_RC -eq 0 ]; then
    # ── Token is ACTIVE ──
    # Parse log for last SSO login time to estimate remaining
    LAST_LOGIN=""
    if [ -f "$LOG_FILE" ]; then
        # Find the last successful "done in" line
        LAST_LINE=$(grep "done in.*—" "$LOG_FILE" 2>/dev/null | tail -1)
        if [ -n "$LAST_LINE" ]; then
            # Extract timestamp: 2026-05-01T15:59:11-06:00
            LAST_LOGIN=$(echo "$LAST_LINE" | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}')
        fi
    fi

    if [ -n "$LAST_LOGIN" ]; then
        # Compute remaining time
        LOGIN_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$LAST_LOGIN" "+%s" 2>/dev/null)
        NOW_EPOCH=$(date +%s)

        if [ -n "$LOGIN_EPOCH" ]; then
            ELAPSED_S=$((NOW_EPOCH - LOGIN_EPOCH))
            SESSION_S=$((SESSION_HOURS * 3600))
            REMAINING_S=$((SESSION_S - ELAPSED_S))
            REMAINING_H=$((REMAINING_S / 3600))
            REMAINING_M=$(( (REMAINING_S % 3600) / 60 ))

            LOGIN_TIME=$(echo "$LAST_LOGIN" | grep -oE '[0-9]{2}:[0-9]{2}' | head -1)

            if [ $REMAINING_S -le 0 ]; then
                # Estimate says expired but STS says active - session is longer than assumed
                LABEL="$LOGIN_TIME"
                COLOR="0xffa6e3a1"  # green (STS says active, trust it)
            elif [ $REMAINING_H -ge 4 ]; then
                LABEL="$LOGIN_TIME ~${REMAINING_H}h"
                COLOR="0xffa6e3a1"  # green
            elif [ $REMAINING_H -ge 2 ]; then
                LABEL="$LOGIN_TIME ~${REMAINING_H}h"
                COLOR="0xfff9e2af"  # yellow
            elif [ $REMAINING_H -ge 1 ]; then
                LABEL="$LOGIN_TIME ~${REMAINING_H}h${REMAINING_M}m"
                COLOR="0xfffab387"  # peach
            else
                LABEL="$LOGIN_TIME ~${REMAINING_M}m"
                COLOR="0xfff38ba8"  # red
            fi
        else
            LABEL="active"
            COLOR="0xffa6e3a1"
        fi
    else
        LABEL="active"
        COLOR="0xffa6e3a1"
    fi

    # Clean up recovery lock
    rm -f "$RECOVERY_LOCKFILE"

    sketchybar --set $NAME icon.color="$COLOR" label="$LABEL" label.color="$COLOR" drawing=on
    exit 0
fi

# ── 2. Token is EXPIRED ──

HOUR=$(date +%H)

# Outside work hours (00:00-07:59) → show off, don't recover
if [ "$HOUR" -lt 8 ]; then
    sketchybar --set $NAME icon.color="0xff6c7086" label="off" label.color="0xff6c7086" drawing=on
    rm -f "$RECOVERY_LOCKFILE"
    exit 0
fi

# ── 3. Auto-recovery during work hours (08:00-23:59) ──

# Prevent concurrent recovery attempts
if [ -f "$RECOVERY_LOCKFILE" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$RECOVERY_LOCKFILE") ))
    if [ "$LOCK_AGE" -lt 120 ]; then
        # Recovery in progress (less than 2 min old)
        sketchybar --set $NAME icon.color="0xfff9e2af" label="auth..." label.color="0xfff9e2af" drawing=on
        exit 0
    fi
    # Stale lock, remove
    rm -f "$RECOVERY_LOCKFILE"
fi

touch "$RECOVERY_LOCKFILE"

# Show "recovering..." state
sketchybar --set $NAME icon.color="0xfff9e2af" label="renew..." label.color="0xfff9e2af" drawing=on

# Try silent recovery (10 second timeout)
RECOVERY_OUTPUT=$(timeout 10 "$AWS_BIN" sso login --profile "$AWS_PROFILE" 2>&1)
RECOVERY_RC=$?

if [ $RECOVERY_RC -eq 0 ]; then
    # Silent recovery succeeded (Microsoft cookie was alive)
    rm -f "$RECOVERY_LOCKFILE"
    /usr/bin/osascript -e 'display notification "Token refreshed silently" with title "AWS SSO" subtitle "Bedrock access restored"' 2>/dev/null
    sketchybar --set $NAME icon.color="0xffa6e3a1" label="renewed" label.color="0xffa6e3a1" drawing=on
    exit 0
fi

# ── 4. Silent recovery failed → Microsoft session expired ──
# Open Zen Browser to myapps.microsoft.com for re-auth

# Notify user
/usr/bin/osascript -e 'display notification "Microsoft session expired. Opening Zen Browser for authentication." with title "AWS SSO" subtitle "Manual auth required"' 2>/dev/null

# Open myapps.microsoft.com in Zen Browser
open -a "Zen" "https://myapps.microsoft.com" 2>/dev/null

# Wait for page to load, then trigger 1Password autofill (Cmd+\)
(
    sleep 4
    /usr/bin/osascript -e '
    tell application "Zen" to activate
    delay 0.5
    tell application "System Events"
        keystroke "\\" using command down
    end tell
    ' 2>/dev/null
) &

rm -f "$RECOVERY_LOCKFILE"
sketchybar --set $NAME icon.color="0xfff38ba8" label="auth" label.color="0xfff38ba8" drawing=on
