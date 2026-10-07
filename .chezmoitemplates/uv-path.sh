{{ if eq .machine_type "mac-mini" -}}
# Select installed uv only; broad mise activation also changes Python/Node.
if [ -f "/Volumes/ext/state/.dotfiles-ai-state" ]; then
    export MISE_DATA_DIR="/Volumes/ext/state/xdg/data/mise"
    if command -v mise >/dev/null 2>&1; then
        __dotfiles_uv=$(mise which uv 2>/dev/null) || __dotfiles_uv=
        case "$__dotfiles_uv" in
            "$MISE_DATA_DIR"/installs/uv/*/uv)
                if [ -x "$__dotfiles_uv" ] && [ -x "${__dotfiles_uv%/*}/uvx" ]; then
                    case "$PATH" in
                        "${__dotfiles_uv%/*}:"*) ;;
                        *) export PATH="${__dotfiles_uv%/*}:$PATH" ;;
                    esac
                fi
                ;;
        esac
        unset __dotfiles_uv
    fi
elif [ "${MISE_DATA_DIR:-}" = "/Volumes/ext/state/xdg/data/mise" ]; then
    unset MISE_DATA_DIR
fi
{{ end -}}
