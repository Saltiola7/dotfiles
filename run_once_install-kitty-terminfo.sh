#!/bin/bash
# Install the xterm-kitty terminfo entry into ~/.terminfo so that SSH-ing into
# this machine from a kitty terminal does not error with:
#   'xterm-kitty': unknown terminal type.
#
# The entry is derived dynamically from the locally installed kitty (no vendored
# copy in the repo), so each machine gets the version that matches its kitty.
# Idempotent and non-fatal: if the entry already exists or kitty is absent, it
# exits 0 without failing `chezmoi apply`.

# Already installed? Nothing to do.
if infocmp xterm-kitty >/dev/null 2>&1; then
    exit 0
fi

# tic is required to compile the entry.
if ! command -v tic >/dev/null 2>&1; then
    echo "Warning: tic not found; cannot install xterm-kitty terminfo." >&2
    exit 0
fi

# Find kitty's bundled terminfo directory (macOS app bundle or Linux share dir).
TERMINFO_SRC=""
for dir in \
    /Applications/kitty.app/Contents/Resources/terminfo \
    "$HOME/Applications/kitty.app/Contents/Resources/terminfo" \
    /usr/local/share/kitty/terminfo \
    /usr/share/kitty/terminfo; do
    if [ -f "$dir/78/xterm-kitty" ] || [ -f "$dir/x/xterm-kitty" ]; then
        TERMINFO_SRC="$dir"
        break
    fi
done

if [ -n "$TERMINFO_SRC" ]; then
    # Read the compiled entry from kitty's bundle and recompile into ~/.terminfo.
    if TERMINFO="$TERMINFO_SRC" infocmp -x xterm-kitty 2>/dev/null | tic -x -o "$HOME/.terminfo" - 2>/dev/null; then
        exit 0
    fi
fi

# Fallback: let the kitten helper emit the terminfo source and compile it.
if command -v kitten >/dev/null 2>&1; then
    if kitten show-config >/dev/null 2>&1; then : ; fi
    # kitty ships the entry under its lib dir; try infocmp via kitty's own TERMINFO.
    KITTY_BIN="$(command -v kitty 2>/dev/null)"
    if [ -n "$KITTY_BIN" ]; then
        KITTY_TI="$(dirname "$KITTY_BIN")/../lib/kitty/terminfo"
        if [ -f "$KITTY_TI/78/xterm-kitty" ] || [ -f "$KITTY_TI/x/xterm-kitty" ]; then
            if TERMINFO="$KITTY_TI" infocmp -x xterm-kitty 2>/dev/null | tic -x -o "$HOME/.terminfo" - 2>/dev/null; then
                exit 0
            fi
        fi
    fi
fi

echo "Warning: kitty terminfo source not found; xterm-kitty terminfo not installed." >&2
exit 0
