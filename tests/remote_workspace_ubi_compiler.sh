#!/bin/bash
# Installed ONLY as temporary compiler aliases in the disposable smoke HOME.
set -euo pipefail
compiler="/usr/bin/${0##*/}"
fixture=$(dirname "$(readlink -f "$0")")
args=("$@")
parser= output= shared=0
while (($#)); do
  case "$1" in
    -E|-S|-M|-MM|-fsyntax-only) exec "$compiler" "${args[@]}";;
    -o) output=$2; shift;;
    -o?*) output=${1#-o};;
    -shared) shared=1;;
    parser.c|*/parser.c) parser=$1;;
  esac
  shift
done
if [[ ! -f "$parser" ]] || ! grep -Fq 'tree_sitter/parser.h' "$parser"; then parser=; fi
if [[ -z "$output" || ( -z "$parser" && $shared == 0 ) ]]; then
  exec "$compiler" "${args[@]}"
fi

state="$HOME/.local/state/remote-workspace"
attempt=attempt-0002
if [[ -f "$fixture/reject.h" ]]; then attempt=attempt-0001; fi
generation="$state/editor-attempts/$attempt"
if [[ ${XDG_DATA_HOME:-} != "$generation/candidate" || -e "$state/editor-ready.json" || -L "$state/editor-ready.json" ]] ||
    ! grep -Eq '"state"[[:space:]]*:[[:space:]]*"running"' "$generation/record.json"; then
  # Never inject outside a journaled private attempt. Detect unexpected later
  # parser builds, including during the ordinary owner startup.
  if [[ -n "$parser" ]]; then printf 'outside\n' >>"$fixture/outside"; fi
  exec "$compiler" "${args[@]}"
fi

if [[ -n "$parser" && -f "$fixture/reject.h" ]] &&
    grep -Eq '(^|[^[:alnum:]_])tree_sitter_sql[[:space:]]*\(' "$parser"; then
  # An authentic compiler diagnostic, not a wrapper returning an arbitrary 1.
  status=0
  LC_ALL=C "$compiler" "${args[@]}" -include "$fixture/reject.h" -fdiagnostics-color=never -fmax-errors=1 \
    >"$fixture/error.$$" 2>&1 || status=$?
  if ((status != 0)) && grep -Fq 'error: #error RRW_UBI_CONTROLLED_PARSER_FAULT' "$fixture/error.$$"; then
    printf 'compiler rejected SQL parser.c\n' >>"$fixture/rejected"
  fi
  rm -f "$fixture/error.$$"
  exit "$status"
fi

# Observe the real UBI compiler's results, including split compile/link commands.
"$compiler" "${args[@]}"
[[ ! -f "$fixture/reject.h" ]] || exit 0
symbols=$(LC_ALL=C readelf --wide --syms "$output" | awk '
  $4 == "FUNC" && $5 == "GLOBAL" && $7 != "UND" && $8 ~ /^tree_sitter_[a-z0-9_]+$/ {
    sub(/^tree_sitter_/, "", $8); print $8
  }' | sort -u)
[[ -n "$symbols" ]] || exit 0
if [[ -n "$parser" ]]; then printf '%s\n' "$symbols" >>"$fixture/compiled"; fi
if ((shared)); then
  digest=$(sha256sum <"$output")
  while IFS= read -r symbol; do printf '%s %s\n' "$symbol" "${digest%% *}"; done <<<"$symbols" >>"$fixture/linked"
fi
