#!/usr/bin/env bash
# fetch_github_repos.sh — GitHub 퍼블릭 레포를 그래프 뷰 데이터로 수집
# 옵션:
#   -h, --help        사용법 출력
#   --user <name>     대상 GitHub 사용자 (기본: skong097)
#   --output <path>   출력 JSON 경로 (기본: data/github_repos.json)
# 동작: api.github.com 에서 레포를 받아 fork/archived 제외, 필요한 필드만 추려 JSON 저장.
#       GITHUB_TOKEN 환경변수가 있으면 인증 헤더로 사용(rate limit 완화). git 커밋은 안 함.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GH_USER="skong097"
OUTPUT="$REPO_ROOT/data/github_repos.json"

usage() { sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --user) GH_USER="${2:-}"; shift 2 ;;
    --user=*) GH_USER="${1#*=}"; shift ;;
    --output) OUTPUT="${2:-}"; shift 2 ;;
    --output=*) OUTPUT="${1#*=}"; shift ;;
    *) echo "알 수 없는 옵션: $1" >&2; usage; exit 2 ;;
  esac
done

AUTH=()
if [[ -n "${GITHUB_TOKEN:-}" ]]; then AUTH=(-H "Authorization: Bearer ${GITHUB_TOKEN}"); fi

echo "[gh-graph] ${GH_USER} 레포 수집 중…"
RAW="$(curl -sS "${AUTH[@]}" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/users/${GH_USER}/repos?per_page=100&sort=updated")"

printf '%s' "$RAW" | python3 -c '
import json, sys, datetime
raw = json.load(sys.stdin)
if not isinstance(raw, list):
    sys.stderr.write("GitHub API 응답이 예상과 다릅니다: %s\n" % str(raw)[:300]); sys.exit(1)
user, out_path = sys.argv[1], sys.argv[2]
repos = []
for r in raw:
    if r.get("fork") or r.get("archived"): continue
    repos.append({
        "name": r.get("name",""),
        "description": r.get("description") or "",
        "language": r.get("language") or "Other",
        "url": r.get("html_url",""),
        "stars": r.get("stargazers_count",0),
        "updated": (r.get("updated_at") or "")[:10],
        "topics": r.get("topics") or [],
    })
repos.sort(key=lambda x: x["updated"], reverse=True)
out = {"fetched": datetime.date.today().isoformat(), "user": user, "repos": repos}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("[gh-graph] %d개 레포 저장 → %s" % (len(repos), out_path))
' "$GH_USER" "$OUTPUT"
