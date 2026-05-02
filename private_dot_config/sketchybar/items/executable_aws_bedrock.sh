#!/usr/bin/env bash

source "$CONFIG_DIR/colors.sh"

# AWS Bedrock icon (cloud with lock)
ICON_AWS="󰸏"

sketchybar --add item aws_bedrock right \
    --set aws_bedrock \
        icon="$ICON_AWS" \
        icon.font="$FONT:Bold:16.0" \
        label.font="$FONT:Bold:12.0" \
        update_freq=60 \
        script="$PLUGIN_DIR/aws_bedrock.sh" \
    --subscribe aws_bedrock system_woke
