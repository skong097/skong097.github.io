# KB Radar — 사용법

키워드 기반 **지식 레이더**. 사전 설정한 키워드로 최신 논문·기사·영상·인물/기술동향을 주기적으로 수집·요약하고, 원본 링크와 함께 `/kb-radar/` 페이지에 보여준다.

- **라이브**: https://skong097.github.io/kb-radar/
- **수집 엔진**: Claude Code (`claude -p`, WebSearch/WebFetch) — 별도 API 키 불필요
- **커밋 정책**: 수집 에이전트는 **데이터 파일만 갱신**하고 커밋하지 않는다. 커밋·푸시는 **사람이 직접** (`git diff` 확인 후).

---

## 동작 구조

```
data/kb_keywords.yaml   ← 사람이 편집 (키워드 그룹 + 옵션)
        │
        ▼  scripts/run_kb_radar.sh  (로컬 cron, 주 2회)
   claude -p "$(cat scripts/kb_radar/collect.md)"   ─ WebSearch/WebFetch ─▶ 검색·요약·중복제거·아카이브
        │
        ▼  (병합 결과 기록, 커밋 안 함)
data/kb_items.json      ← 에이전트가 갱신
        │
        ▼  사람이 git diff 확인 → 커밋·푸시 → GitHub Actions 재빌드
/kb-radar/ 페이지        ← 키워드 그룹별 섹션 + 카드로 렌더
```

## 파일 구성

| 경로 | 역할 | 편집 주체 |
|---|---|---|
| `data/kb_keywords.yaml` | 키워드 그룹 + 옵션 | **사람** |
| `data/kb_items.json` | 수집 항목 누적본 | 에이전트(자동) |
| `scripts/kb_radar/collect.md` | 수집 에이전트 지시문 | (거의 고정) |
| `scripts/run_kb_radar.sh` | 수집 런처(cron 진입점) | (거의 고정) |
| `scripts/completion.bash` | bash 탭 자동완성 | (거의 고정) |
| `layouts/kb-radar/single.html` | 페이지 렌더링 | (거의 고정) |
| `content/kb-radar/index.md` | 페이지 진입점 | (거의 고정) |
| `scripts/kb_radar/collect.log` | 실행 로그 (`.gitignore` 대상) | 자동 |

---

## 1. 수집 실행

저장소 루트에서 실행한다. **`-p`(print) 모드라 실행 중 수 분간 화면이 조용할 수 있다 — 중단하지 말고 기다린다.**

```bash
cd ~/dev_ws/blog

scripts/run_kb_radar.sh                  # 전체 그룹 수집
scripts/run_kb_radar.sh --group ai-agent # 특정 그룹만 수집
scripts/run_kb_radar.sh --dry-run        # 수집만 하고 파일 저장은 생략(검증용)
scripts/run_kb_radar.sh --help           # 사용법
```

| 옵션 | 설명 |
|---|---|
| `-h`, `--help` | 사용법 출력 |
| `--dry-run` | 검색·요약까지만, `data/kb_items.json` 저장 생략 |
| `--group <id>` | 특정 그룹만 수집 (`<id>` 탭 자동완성 지원) |

실행이 끝나면 변경 여부와 총 항목 수가 출력된다. 그 뒤:

```bash
git diff data/kb_items.json     # 내용 확인
git add data/kb_items.json
git commit -m "chore(kb-radar): 수집 데이터 갱신"
git push origin main            # → GitHub Actions가 사이트 재빌드
```

## 2. 키워드 편집

`data/kb_keywords.yaml`만 고치면 수집 대상이 바뀐다.

```yaml
groups:
  - id: physical-ai            # 영문 kebab-case, 고유 식별자(데이터 join 키)
    name: "Physical AI"        # 화면 표시명
    keywords:                  # 이 그룹에서 검색할 키워드들
      - "Physical AI"
      - "VLA vision language action model"
    categories: [paper, article, video, person]   # 수집할 타입
    max_per_run: 6             # 1회 실행 시 이 그룹의 최대 신규 항목 수
```

- `categories` 허용값: `paper`(논문) · `article`(기사/블로그) · `video`(영상) · `person`(인물/기술동향)
- 그룹 추가/삭제/키워드 수정 모두 이 파일에서. 저장 후 다음 수집부터 반영된다.

## 3. 데이터 구조 (`data/kb_items.json`)

```json
{
  "last_collected": "2026-06-06",
  "items": [
    {
      "id": "<sha1(url)>",       // 중복 제거 키
      "group": "physical-ai",     // kb_keywords.yaml의 group id
      "category": "paper",        // paper | article | video | person
      "title": "...",
      "summary": "한국어 2~3문장 요약",
      "source": "arXiv | YouTube | 매체명",
      "authors": "...",           // 없으면 ""
      "published": "2026-06-01",  // 원문 발행일(있으면)
      "collected": "2026-06-06",  // 수집일 → 아카이브 기준
      "url": "https://...",       // 원본 링크
      "archived": false           // collected 30일 경과 시 true
    }
  ]
}
```

**누적 규칙**: 새 항목은 누적하되 `id`(원본 URL의 SHA1)로 중복 제거. `collected` 후 **30일 경과** 항목은 `archived: true`로 내려가고(삭제 안 함), 페이지 기본 화면에서는 숨겨진다(필터에서 "아카이브 포함" 토글로 표시).

## 4. 페이지 보기

- 키워드 그룹별 섹션 + 카드 그리드
- 필터: 카테고리(논문·기사·영상·인물) 토글 / "아카이브 포함" 토글 / 제목·요약·그룹 텍스트 검색
- PaperMod 다크·라이트 모드 연동

---

## 자동화 (1회 셋업)

**탭 자동완성** — `~/.bashrc`에 추가 후 `source ~/.bashrc`:
```bash
[ -f "$HOME/dev_ws/blog/scripts/completion.bash" ] && source "$HOME/dev_ws/blog/scripts/completion.bash"
```

**주 2회 cron** — `crontab -e` (예: 월·목 09:00):
```
0 9 * * 1,4 cd $HOME/dev_ws/blog && scripts/run_kb_radar.sh >> $HOME/dev_ws/blog/scripts/kb_radar/collect.log 2>&1
```
> cron은 `data/kb_items.json`만 갱신한다. 주기적으로 `git diff`를 확인하고 직접 커밋·푸시하면 사이트가 재빌드된다.

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| 실행 중 화면이 한참 조용함 | `-p` 모드는 중간 로그를 스트리밍하지 않음. **정상** — 중단하지 말고 기다린다(수 분 소요). |
| 푸시했는데 라이브에 안 보임 | 브라우저/CDN 캐시(`max-age=600`). **강력 새로고침**(Ctrl+Shift+R) 또는 시크릿 창, `?v=1` 캐시버스터, 또는 10분 후. |
| `video` 카테고리가 비어 있음 | YouTube는 WebFetch로 본문·업로드일 메타데이터가 안 잡혀, 추측 요약 대신 보류함(의도된 동작). 필요 시 `collect.md`의 영상 수집 전략을 보강. |
| 수집이 0건 / 빈 결과 | `data/kb_keywords.yaml` 형식 확인. `scripts/kb_radar/collect.log` 확인. 런처는 저장소 루트에서 실행해야 함. |
| 항목이 너무 많이/적게 수집됨 | 그룹의 `max_per_run` 조정. |

## 제약

- 요약·제목에 **특정 업체명을 노출하지 않는다**(원본 URL 도메인은 사실 정보이므로 유지).
- 모든 날짜는 `YYYY-MM-DD`.
- 요약은 한국어, 사실 위주(추측·홍보성 표현 금지).
