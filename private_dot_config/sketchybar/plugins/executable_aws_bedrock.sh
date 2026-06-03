#!/usr/bin/env bash

AWS_PROFILE="BedrockDeveloperAccess-302432775606"
AWS_BIN="/usr/local/bin/aws"
LOGIN_EPOCH_FILE="/tmp/sketchybar_aws_login_epoch"
RECOVERY_LOCKFILE="/tmp/sketchybar_aws_recovery_lock"
BROWSER_LOCKFILE="/tmp/sketchybar_aws_browser_lock"
SESSION_ESTIMATE_HOURS=8  # Tune this if sessions consistently die earlier/later

# ── 0. Handle mouse events for popup ──
if [ "$SENDER" = "mouse.exited.global" ]; then
    sketchybar --set aws_bedrock popup.drawing=off
    exit 0
fi

# ── 1. STS Probe: single source of truth ──
STS_OUTPUT=$("$AWS_BIN" sts get-caller-identity --profile "$AWS_PROFILE" 2>&1)
STS_RC=$?

# ── 2. STS works — session is alive ──
if [ $STS_RC -eq 0 ]; then

    # If we had no login epoch saved, this is a fresh detection (e.g., after kitty terminal login).
    # Record now as the login time so the countdown starts.
    if [ ! -f "$LOGIN_EPOCH_FILE" ]; then
        date +%s > "$LOGIN_EPOCH_FILE"
    fi

    # Clean up recovery lockfiles — session is alive
    rm -f "$RECOVERY_LOCKFILE" "$BROWSER_LOCKFILE"

    # Calculate countdown from saved login epoch
    LOGIN_EPOCH="$(cat "$LOGIN_EPOCH_FILE" 2>/dev/null)"
    NOW_EPOCH="$(date +%s)"

    if [ -n "$LOGIN_EPOCH" ]; then
        SESSION_S=$((SESSION_ESTIMATE_HOURS * 3600))
        ELAPSED_S=$((NOW_EPOCH - LOGIN_EPOCH))
        REMAINING_S=$((SESSION_S - ELAPSED_S))
        REMAINING_MIN=$((REMAINING_S / 60))

        if [ $REMAINING_MIN -le 0 ]; then
            # Past 8h estimate but STS still works — trust the probe
            LABEL="active"
            COLOR="0xffa6e3a1"  # green
        else
            REMAINING_H=$((REMAINING_MIN / 60))
            REMAINING_M=$((REMAINING_MIN % 60))

            if [ $REMAINING_H -gt 0 ]; then
                LABEL="${REMAINING_H}h${REMAINING_M}m"
            else
                LABEL="${REMAINING_M}m"
            fi

            if [ $REMAINING_MIN -ge 180 ]; then
                COLOR="0xffa6e3a1"  # green (≥3h)
            elif [ $REMAINING_MIN -ge 90 ]; then
                COLOR="0xfff9e2af"  # yellow (≥1.5h)
            elif [ $REMAINING_MIN -ge 45 ]; then
                COLOR="0xfffab387"  # peach (≥45m)
            else
                COLOR="0xfff38ba8"  # red (<45m)
            fi
        fi
    else
        # No login epoch — shouldn't happen but show active
        LABEL="active"
        COLOR="0xffa6e3a1"
    fi

    sketchybar --set $NAME icon.color="$COLOR" label="$LABEL" label.color="$COLOR" drawing=on
    exit 0
fi

# ── 3. STS failed — session is dead ──
# Remove login epoch so next successful login starts a fresh countdown
rm -f "$LOGIN_EPOCH_FILE"

# ── Check if browser auth is already in progress (prevents loop) ──
if [ -f "$BROWSER_LOCKFILE" ]; then
    BROWSER_LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$BROWSER_LOCKFILE") ))
    if [ "$BROWSER_LOCK_AGE" -lt 600 ]; then
        sketchybar --set $NAME icon.color="0xfff38ba8" label="auth" label.color="0xfff38ba8" drawing=on
        exit 0
    fi
    rm -f "$BROWSER_LOCKFILE"
fi

# ── Check if silent recovery is already in progress ──
if [ -f "$RECOVERY_LOCKFILE" ]; then
    LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$RECOVERY_LOCKFILE") ))
    if [ "$LOCK_AGE" -lt 120 ]; then
        sketchybar --set $NAME icon.color="0xfff9e2af" label="renew..." label.color="0xfff9e2af" drawing=on
        exit 0
    fi
    rm -f "$RECOVERY_LOCKFILE"
fi

# ── Outside work hours (00:00-07:59) → show off, don't recover ──
HOUR=$(date +%H)
if [ "$HOUR" -lt 8 ]; then
    sketchybar --set $NAME icon.color="0xff6c7086" label="off" label.color="0xff6c7086" drawing=on
    rm -f "$RECOVERY_LOCKFILE" "$BROWSER_LOCKFILE"
    exit 0
fi

# ── 4. Try silent recovery ──
touch "$RECOVERY_LOCKFILE"
sketchybar --set $NAME icon.color="0xfff9e2af" label="renew..." label.color="0xfff9e2af" drawing=on

RECOVERY_OUTPUT=$(timeout 10 "$AWS_BIN" sso login --profile "$AWS_PROFILE" 2>&1)
RECOVERY_RC=$?

if [ $RECOVERY_RC -eq 0 ]; then
    rm -f "$RECOVERY_LOCKFILE" "$BROWSER_LOCKFILE"
    # Record fresh login time
    date +%s > "$LOGIN_EPOCH_FILE"
    # Warm CLI cache
    "$AWS_BIN" sts get-caller-identity --profile "$AWS_PROFILE" >/dev/null 2>&1
    /usr/bin/osascript -e 'display notification "Token refreshed silently" with title "AWS SSO" subtitle "Bedrock access restored"' 2>/dev/null
    sketchybar --set $NAME icon.color="0xffa6e3a1" label="renewed" label.color="0xffa6e3a1" drawing=on
    exit 0
fi

rm -f "$RECOVERY_LOCKFILE"

# ── 5. Silent recovery failed → Microsoft session expired ──
touch "$BROWSER_LOCKFILE"

/usr/bin/osascript -e 'display notification "Microsoft session expired. Opening Zen for authentication." with title "AWS SSO" subtitle "1Password autofill + AWS SSO will run automatically"' 2>/dev/null

# Single-flow recovery:
#
# 1. Start `aws sso login` in the background. It opens its own OIDC URL in
#    the default browser (Zen). Zen redirects through AWS SSO portal →
#    Microsoft Entra → MS sign-in if the MS session is dead.
# 2. Wait ~3s for the OIDC redirect chain to land on the MS sign-in page.
# 3. Fire 1Password autofill keystrokes (Alt+Period → Enter → Enter) to
#    populate and submit the MS form. Note: 1Password binding in Zen is
#    Alt+Period (Cmd+\ is desktop-app only — see
#    ~/Library/Application Support/zen/Profiles/<p>/extension-settings.json).
# 4. `aws sso login` keeps polling its OIDC callback. As soon as MS auth
#    + AWS "Allow access" complete, the CLI exits 0. Default CLI timeout
#    is ~10 minutes — plenty for slow MFA approvals.
# 5. On success: clean up lockfile, refresh login epoch, warm STS, post
#    notification, fire aws_sso_refreshed trigger so the bar flips green
#    within 1 second.
#
# Edge cases NOT handled (by design):
#   - "Pick an account" page after explicit logout — user clicks manually.
#   - MFA prompt — covered by aws sso login's own ~10min polling.
(
    "$AWS_BIN" sso login --profile "$AWS_PROFILE" >/tmp/sketchybar_aws_bg_login.log 2>&1 &
    AWS_LOGIN_PID=$!

    sleep 3
    /usr/bin/osascript -e '
    tell application "Zen" to activate
    delay 0.5
    tell application "System Events"
        keystroke "." using option down
        delay 1.5
        key code 36
        delay 1.0
        key code 36
    end tell
    ' 2>/dev/null

    wait "$AWS_LOGIN_PID"
    if [ $? -eq 0 ]; then
        rm -f "$BROWSER_LOCKFILE"
        date +%s > "$LOGIN_EPOCH_FILE"
        "$AWS_BIN" sts get-caller-identity --profile "$AWS_PROFILE" >/dev/null 2>&1
        /usr/bin/osascript -e 'display notification "AWS SSO restored automatically" with title "AWS SSO" subtitle "Bedrock access ready"' 2>/dev/null
        sketchybar --trigger aws_sso_refreshed 2>/dev/null
    fi
) &

# DO NOT delete browser_lockfile — persists 10 min to prevent re-triggering
# (background subshell deletes it on success).
sketchybar --set $NAME icon.color="0xfff38ba8" label="auth" label.color="0xfff38ba8" drawing=on
