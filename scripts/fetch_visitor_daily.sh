#!/usr/bin/env bash
# fetch_visitor_daily.sh — GoatCounter 일별 조회수를 그래프 데이터로 수집
# 옵션:
#   -h, --help        사용법 출력
#   --days <n>        수집 기간(일). 기본 30
#   --code <name>     GoatCounter 사이트 코드 (기본: skong097)
#   --output <path>   출력 JSON 경로 (기본: data/visitor_daily.json)
# 동작: GOATCOUNTER_TOKEN(API 토큰)으로 /api/v0/stats/total 을 조회해 일별 조회수를 저장한다.
#       토큰이 없으면 아무것도 쓰지 않고 정상 종료한다(그래프만 안 그려지고 빌드는 성공).
#       비어 있는 날짜는 0 으로 채워 축이 끊기지 않게 한다. git 커밋은 안 함.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DAYS=30
CODE="skong097"
OUTPUT="$REPO_ROOT/data/visitor_daily.json"

usage() { sed -n '2,9p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --days) DAYS="${2:-}"; shift 2 ;;
    --days=*) DAYS="${1#*=}"; shift ;;
    --code) CODE="${2:-}"; shift 2 ;;
    --code=*) CODE="${1#*=}"; shift ;;
    --output) OUTPUT="${2:-}"; shift 2 ;;
    --output=*) OUTPUT="${1#*=}"; shift ;;
    *) echo "알 수 없는 옵션: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${GOATCOUNTER_TOKEN:-}" ]]; then
  echo "[visitor-trend] GOATCOUNTER_TOKEN 이 없어 건너뜁니다 (그래프 미표시)." >&2
  exit 0
fi

START="$(date -u -d "-$((DAYS - 1)) days" +%Y-%m-%d)"
END="$(date -u +%Y-%m-%d)"

echo "[visitor-trend] ${CODE}: ${START} ~ ${END} (${DAYS}일) 조회 중…"
RAW="$(curl -sS --fail-with-body \
  -H "Authorization: Bearer ${GOATCOUNTER_TOKEN}" \
  -H "Content-Type: application/json" \
  "https://${CODE}.goatcounter.com/api/v0/stats/total?start=${START}&end=${END}")"

printf '%s' "$RAW" | python3 -c '
import json, sys, datetime

raw = json.load(sys.stdin)
start, end, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
if not isinstance(raw, dict) or "stats" not in raw:
    sys.stderr.write("GoatCounter 응답이 예상과 다릅니다: %s\n" % str(raw)[:300]); sys.exit(1)

by_day = {}
for s in raw.get("stats") or []:
    day = (s.get("day") or "")[:10]
    if day:
        by_day[day] = int(s.get("daily") or 0)

d0 = datetime.date.fromisoformat(start)
d1 = datetime.date.fromisoformat(end)
days = []
d = d0
while d <= d1:                      # 빈 날짜는 0 으로 채운다 (시간축을 끊지 않는다)
    iso = d.isoformat()
    days.append({"date": iso, "views": by_day.get(iso, 0)})
    d += datetime.timedelta(days=1)

payload = {
    "fetched": datetime.date.today().isoformat(),
    "start": start,
    "end": end,
    "days": days,
}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("[visitor-trend] %s 저장 — %d일, 합계 %d" % (out_path, len(days), sum(x["views"] for x in days)))
' "$START" "$END" "$OUTPUT"
