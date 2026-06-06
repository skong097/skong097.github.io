#!/usr/bin/env bash
# run_kb_radar.sh — KB Radar 수집 런처
# 옵션:
#   -h, --help        사용법 출력
#   --dry-run         수집을 시뮬레이션하되 data/kb_items.json 저장은 생략
#   --group <id>      특정 키워드 그룹만 수집 (kb_keywords.yaml의 group id)
# 동작: repo 루트에서 claude -p 로 scripts/kb_radar/collect.md 지시문을 실행한다.
#       git 커밋은 하지 않는다(사용자가 직접). 변경 요약을 출력한다.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COLLECT_MD="$REPO_ROOT/scripts/kb_radar/collect.md"
ITEMS_JSON="$REPO_ROOT/data/kb_items.json"

DRY_RUN=0
GROUP=""

usage() {
  sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --group) GROUP="${2:-}"; shift 2 ;;
    --group=*) GROUP="${1#*=}"; shift ;;
    *) echo "알 수 없는 옵션: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ ! -f "$COLLECT_MD" ]]; then
  echo "지시문이 없습니다: $COLLECT_MD" >&2; exit 1
fi

PROMPT="$(cat "$COLLECT_MD")"
if [[ -n "$GROUP" ]]; then
  PROMPT="$PROMPT

## 이번 실행 한정 지시
오직 group id 가 \"$GROUP\" 인 그룹만 수집한다. 나머지 그룹은 건너뛴다."
fi
if [[ "$DRY_RUN" -eq 1 ]]; then
  PROMPT="$PROMPT

## 이번 실행 한정 지시 (DRY RUN)
검색·요약까지만 수행하고, data/kb_items.json 파일은 절대 저장하지 마라. 무엇을 추가할지 요약만 출력하라."
fi

BEFORE_HASH="$( [[ -f "$ITEMS_JSON" ]] && md5sum "$ITEMS_JSON" | cut -d' ' -f1 || echo none )"

echo "[KB Radar] 수집 시작 (dry-run=$DRY_RUN, group=${GROUP:-all})"
echo "[KB Radar] 진행 중입니다… claude -p(print) 모드라 완료까지 중간 로그가 보이지 않습니다."
echo "[KB Radar] 키워드/그룹 수에 따라 수 분 걸릴 수 있습니다. 중단하지 말고 기다려 주세요."
cd "$REPO_ROOT"
# 무인(cron) 실행을 위해 필요한 도구를 미리 허용한다. (WebSearch/WebFetch=수집, Read/Write/Edit=JSON 갱신, Bash=sha1sum 등)
# 로그는 collect.log 에 누적(.gitignore 대상). pipefail 환경에서도 아래 요약이 출력되도록 실패를 흡수한다.
LOG="$REPO_ROOT/scripts/kb_radar/collect.log"
claude -p "$PROMPT" --allowedTools "WebSearch,WebFetch,Read,Write,Edit,Bash" 2>&1 | tee -a "$LOG" \
  || echo "[KB Radar] 경고: claude 실행이 0이 아닌 코드로 종료됨 (로그: $LOG)" >&2

AFTER_HASH="$( [[ -f "$ITEMS_JSON" ]] && md5sum "$ITEMS_JSON" | cut -d' ' -f1 || echo none )"
if [[ "$BEFORE_HASH" != "$AFTER_HASH" ]]; then
  COUNT="$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["items"]))' "$ITEMS_JSON" 2>/dev/null || echo '?')"
  echo "[KB Radar] data/kb_items.json 변경됨 — 총 항목 $COUNT 개. 'git diff data/kb_items.json' 확인 후 커밋하세요."
else
  echo "[KB Radar] data/kb_items.json 변경 없음."
fi
