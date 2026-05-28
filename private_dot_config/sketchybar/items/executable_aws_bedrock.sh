#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"

# AWS Bedrock icon (cloud with lock)
ICON_AWS="󰸏"

# Register custom event so aws-sso-refresh can trigger immediate updates
sketchybar --add event aws_sso_refreshed

sketchybar --add item aws_bedrock right \
    --set aws_bedrock \
        icon="$ICON_AWS" \
        icon.font="$FONT:Bold:16.0" \
        label.font="$FONT:Bold:12.0" \
        update_freq=60 \
        script="$PLUGIN_DIR/aws_bedrock.sh" \
        click_script="sketchybar --set \$NAME popup.drawing=toggle" \
        popup.background.color=$MANTLE \
        popup.background.corner_radius=12 \
        popup.background.border_color=$SURFACE1 \
        popup.background.border_width=1 \
        popup.blur_radius=20 \
        popup.height=35 \
        popup.align=center \
    --subscribe aws_bedrock system_woke aws_sso_refreshed mouse.exited.global

# Popup: login via kitty terminal
sketchybar --add item aws_bedrock.terminal popup.aws_bedrock \
    --set aws_bedrock.terminal \
        icon="󰆍  Login via Terminal" \
        icon.color=$GREEN \
        icon.padding_left=10 \
        icon.font="$FONT:Bold:14.0" \
        label.drawing=off \
        click_script="kitten quick-access-terminal --instance-group aws-sso bash -c '/usr/local/bin/aws sso login --profile BedrockDeveloperAccess-302432775606; echo; echo \"Done. Press enter to close.\"; read'; sketchybar --set aws_bedrock popup.drawing=off"
