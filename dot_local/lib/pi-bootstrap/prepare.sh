#!/bin/sh
# Edit private image files as the existing unprivileged Lima owner.
set -eu
umask 077
exec python3 "$(dirname "$0")/prepare.py" "$@"
