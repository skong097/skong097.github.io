# KB Radar bash 자동완성
# 부트스트랩: ~/.bashrc 에 아래 한 줄 추가
#   [ -f "$HOME/dev_ws/blog/scripts/completion.bash" ] && source "$HOME/dev_ws/blog/scripts/completion.bash"

_run_kb_radar() {
  local cur prev opts
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  opts="-h --help --dry-run --group"

  if [[ "$prev" == "--group" ]]; then
    local kwfile groups
    kwfile="$(dirname "${BASH_SOURCE[0]}")/../data/kb_keywords.yaml"
    if [[ -f "$kwfile" ]]; then
      groups="$(grep -E '^\s*-\s*id:' "$kwfile" | sed -E 's/.*id:\s*//; s/["'\'']//g')"
      COMPREPLY=( $(compgen -W "$groups" -- "$cur") )
    fi
    return 0
  fi

  COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
}
complete -F _run_kb_radar run_kb_radar.sh ./run_kb_radar.sh scripts/run_kb_radar.sh

_fetch_github_repos() {
  local cur prev opts
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  opts="-h --help --user --output"
  case "$prev" in
    --output) COMPREPLY=( $(compgen -f -- "$cur") ); return 0 ;;
    --user) return 0 ;;
  esac
  COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
}
complete -F _fetch_github_repos fetch_github_repos.sh ./fetch_github_repos.sh scripts/fetch_github_repos.sh
