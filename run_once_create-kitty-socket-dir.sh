#!/bin/bash
# Ensure the kitty remote control socket directory exists.
# Kitty's listen_on directive (kitty.conf) writes its socket here;
# the directory must exist before kitty starts.
mkdir -p ~/.local/share/kitty
