# Foundation sources this optional owner snippet; it still owns Starship init.
export STARSHIP_CONFIG="$HOME/.config/remote-workspace/starship.toml"
case ":$PATH:" in
  *":$HOME/.local/libexec/remote-workspace:"*) ;;
  *) export PATH="$HOME/.local/libexec/remote-workspace:$PATH" ;;
esac
alias vim='nvim'
alias python='python3'
alias py='python3'
[[ $- == *i* && -t 0 && -z ${INTELLIJ_ENVIRONMENT_READER:-} ]] || return 0
[[ ${REMOTE_WORKSPACE_HOOKS_INITIALIZED:-} != 1 ]] || return 0
command -v zoxide >/dev/null && eval "$(zoxide init bash)"
command -v direnv >/dev/null && eval "$(direnv hook bash)"
REMOTE_WORKSPACE_HOOKS_INITIALIZED=1
