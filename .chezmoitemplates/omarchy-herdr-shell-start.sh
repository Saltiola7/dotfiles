# Only a fresh interactive guest pane can start its own client. Mark before
# launching so returning from OpenCode or re-sourcing this rc cannot replay it.
if [[ -z ${_omarchy_herdr_checked+x} ]]; then
    _omarchy_herdr_checked=1
    if [[ $- == *i* && -z ${BASH_EXECUTION_STRING-} && -n ${HERDR_PANE_ID-} && -t 0 && -t 1 &&
          -x $HOME/.local/bin/omarchy-herdr-recovery && -s $HOME/.local/share/dotfiles/herdr-pane-mapping.json ]] && (( SECONDS < 30 )); then
        # Recovery or client exit must not abort initialization of the parent shell.
        "$HOME/.local/bin/omarchy-herdr-recovery" shell-start || :
    fi
fi
