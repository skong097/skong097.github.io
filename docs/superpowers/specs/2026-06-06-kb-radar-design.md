# KB Radar — 설계 문서

- **작성일**: 2026-06-06
- **상태**: 승인됨 (구현 대기)
- **목적**: 기존 `/dashboard/`(Career Dashboard)를 제거하고, 사전 설정한 키워드로 최신 기술·논문·기사·인물·영상을 주기적으로 수집·요약하고 원본 링크와 함께 보여주는 **KB Radar** 페이지를 구축한다.

---

## 1. 배경 & 제약

- 본 블로그는 **Hugo + PaperMod** 정적 사이트이며, `main` push 시 GitHub Actions가 빌드해 GitHub Pages로 배포한다. **서버 런타임이 없다.**
- 따라서 브라우저에서 실시간 검색은 불가능(CORS·API 키 노출·rate limit)하고, 기존 dashboard와 동일하게 **데이터 파일을 미리 채워 두고 페이지는 그 데이터를 클라이언트 JS로 렌더링**하는 패턴을 따른다.
- 수집·요약은 **Claude Code**(WebSearch/WebFetch)가 수행한다. 별도 검색 API 키·외부 서비스가 필요 없다.
- **커밋 정책**: 사용자 전역 규칙상 자동 `git commit/add/push` 금지. 수집 에이전트는 데이터 파일만 갱신하고, 최종 커밋은 사용자가 직접 한다 → 그러므로 수집은 **로컬에서 cron으로 실행**한다(원격 `/schedule` 루틴 아님).
- **회사명 제약**: 블로그 콘텐츠에 전 직장 등 특정 업체명을 노출하지 않는다. 수집 요약·제목에도 동일 적용.

---

## 2. 핵심 결정 요약

| 항목 | 결정 |
|---|---|
| 페이지 이름 / URL | **KB Radar** / `/kb-radar/` (기존 `/dashboard/` 대체) |
| 수집 엔진 | Claude Code 스케줄 에이전트 (WebSearch/WebFetch) |
| 수집 주기 | **주 2회** (예: 월·목) |
| 실행 방식 | **로컬 cron → 래퍼 스크립트 → claude -p**, 커밋은 사용자가 직접 (A안) |
| 수집 카테고리 | 논문(paper) · 기사/블로그(article) · 영상(video) · 인물/기술동향(person) |
| 누적 방식 | 누적 + 원본 링크 기준 중복 제거 + `collected` 30일 경과분 자동 아카이브 |
| 키워드 구조 | 그룹 + 옵션 (그룹별 검색 카테고리·수집 개수 지정), `data/kb_keywords.yaml` 직접 편집 |
| 페이지 기본 화면 | 키워드 그룹별 섹션 + 카드 그리드, 필터(카테고리·아카이브·검색) 제공 |

---

## 3. 데이터 흐름

```
[data/kb_keywords.yaml]  ← 사용자 편집 (키워드 그룹 + 옵션)
          │
          ▼  (주 2회, 로컬 cron)
[scripts/run_kb_radar.sh] → [claude -p "$(cat scripts/kb_radar/collect.md)"]  (cwd=repo)
          │  WebSearch/WebFetch → 검색·요약·중복제거·아카이브
          ▼
[data/kb_items.json]  ← 에이전트가 갱신 (커밋 안 함)
          │
          ▼  사용자가 git diff 검토 후 직접 커밋·푸시
[GitHub Actions 재빌드]
          │
          ▼
[/kb-radar/ 페이지]  ← 키워드 그룹별 섹션으로 렌더링
```

---

## 4. 파일 구성

### 신규
| 경로 | 역할 | 관리 주체 |
|---|---|---|
| `content/kb-radar/index.md` | 페이지 진입점 (front matter) | 1회 작성 |
| `layouts/kb-radar/single.html` | 레이아웃 + 스타일 + 렌더 JS | 1회 작성 |
| `data/kb_keywords.yaml` | 키워드 그룹 + 옵션 | **사용자** 편집 |
| `data/kb_items.json` | 수집 항목 누적본 | **에이전트** 갱신 |
| `scripts/kb_radar/collect.md` | 수집 에이전트 지시문(프롬프트) | 1회 작성 |
| `scripts/run_kb_radar.sh` | cron이 호출하는 래퍼 런처 (탭 완성 지원) | 1회 작성 |
| `scripts/completion.bash` | bash 자동완성 핸들러 (없으면 신규) | 1회 작성 |

### 삭제
- `content/dashboard/` (디렉토리)
- `layouts/dashboard/` (디렉토리)
- `data/roadmap_data.yaml`
- `public/dashboard/` (빌드 산출물 — 재빌드 시 사라지나 정리 차원에서 제거)

### 수정
- `hugo.yaml` — `menu.main`의 `dashboard` 항목을 `kb-radar`로 교체(`name: KB Radar`, `url: /kb-radar/`).

> 실제 새로 생성되는 디렉토리: `content/kb-radar/`, `layouts/kb-radar/`, `scripts/kb_radar/`.

---

## 5. 데이터 스키마

### 5.1 `data/kb_keywords.yaml` (사용자 편집)

```yaml
groups:
  - id: physical-ai            # 영문 kebab-case, 데이터 join 키
    name: "Physical AI"        # 화면 표시명
    keywords:                  # 이 그룹에서 검색할 키워드들
      - "Physical AI"
      - "VLA model"
      - "humanoid manipulation"
    categories: [paper, article, video, person]   # 이 그룹에서 수집할 타입
    max_per_run: 6             # 1회 수집 시 이 그룹의 최대 신규 항목 수
  - id: ros2
    name: "ROS2"
    keywords: ["ROS2 Jazzy", "Nav2"]
    categories: [paper, article]
    max_per_run: 4
```

- `categories` 허용값: `paper` | `article` | `video` | `person`
- 그룹 추가/삭제/수정은 이 파일만 편집하면 된다.

### 5.2 `data/kb_items.json` (에이전트 갱신)

```json
{
  "last_collected": "2026-06-06",
  "items": [
    {
      "id": "<sha1(url)>",          // 중복 제거 키
      "group": "physical-ai",        // kb_keywords.yaml의 group id
      "category": "paper",           // paper | article | video | person
      "title": "...",
      "summary": "한국어 2~3문장 요약",
      "source": "arXiv | YouTube | 매체명",
      "authors": "...",              // 선택(없으면 빈 문자열/생략)
      "published": "2026-06-01",     // 원문 발행일(있으면)
      "collected": "2026-06-06",     // 수집일 → 아카이브 기준
      "url": "https://...",          // 원본 링크
      "archived": false              // collected 30일 경과 시 true
    }
  ]
}
```

- 최초 생성 시 `{ "last_collected": null, "items": [] }`로 초기화.

---

## 6. 수집 에이전트 동작 (`scripts/kb_radar/collect.md`)

에이전트가 수행하는 절차:

1. `data/kb_keywords.yaml`을 로드해 그룹·키워드·카테고리·`max_per_run`을 파악한다.
2. `data/kb_items.json`을 로드한다(기존 누적본; 없으면 빈 구조로 시작).
3. 각 그룹의 각 키워드 × 해당 그룹의 `categories`에 대해 **WebSearch**로 최신 결과를 찾고, 유망한 것은 **WebFetch**로 본문을 확인한다.
   - `paper`는 arXiv 등 논문, `video`는 YouTube 등 영상, `article`은 기술 블로그/뉴스, `person`은 주목할 연구자·엔지니어·제품/기술 동향.
4. 각 항목에 대해 **한국어 2~3문장 요약**을 작성한다.
5. `id = sha1(url)`로 기존 항목과 **중복 제거**한다(이미 존재하면 건너뜀).
6. 그룹별 신규 항목은 `max_per_run`을 넘지 않도록 제한한다.
7. 기존 항목 중 `collected`가 **30일 이상 지난 것**은 `archived: true`로 표시한다(삭제하지 않음).
8. 병합 결과를 `data/kb_items.json`에 저장하고 `last_collected`를 오늘 날짜로 갱신한다.
9. **커밋하지 않는다.** 변경 사항은 사용자가 `git diff`로 확인 후 직접 커밋한다.

**제약 (지시문에 명시)**:
- 요약·제목에 전 직장 등 특정 업체명을 노출하지 않는다(원본 링크 도메인은 사실 정보이므로 유지).
- 날짜는 절대 표기(YYYY-MM-DD)로 기록한다.
- 요약은 한국어, 사실 위주, 과장 없이.

---

## 7. 실행 자동화 (로컬 cron + 래퍼 스크립트)

### 7.1 `scripts/run_kb_radar.sh`
- cron이 호출하는 런처. cwd를 repo 루트로 고정하고 `claude -p "$(cat scripts/kb_radar/collect.md)"`를 실행, 로그를 남긴다.
- **탭 자동완성 지원**(CLAUDE.md 규칙): 옵션 명세 헤더 주석 + `case` 파싱 + `-h/--help`.
  - `-h, --help` : 사용법 출력
  - `--dry-run` : 수집은 하되 파일 저장 생략(검증용)
  - `--group <id>` : 특정 그룹만 수집 (value 후보 = `kb_keywords.yaml`의 group id)
- 종료 후 `data/kb_items.json`의 변경 여부와 신규 항목 수를 출력해, 사용자가 커밋 판단을 쉽게 하도록 한다.

### 7.2 `scripts/completion.bash`
- `_run_kb_radar()` 핸들러 추가: `--group`은 `compgen -W "<group ids>"`, 경로 옵션은 `compgen -f`.
- `complete -F _run_kb_radar run_kb_radar.sh ./run_kb_radar.sh` 등록.
- `~/.bashrc` 부트스트랩 안내: `[ -f "<repo>/scripts/completion.bash" ] && source "<repo>/scripts/completion.bash"`

### 7.3 cron 등록 (사용자 안내)
- 주 2회 예시(월·목 09:00): `0 9 * * 1,4 cd <repo> && scripts/run_kb_radar.sh >> <repo>/scripts/kb_radar/collect.log 2>&1`
- 등록은 사용자가 직접(`crontab -e`). 커밋도 사용자가 직접.

---

## 8. 페이지 UI (`/kb-radar/`)

`layouts/kb-radar/single.html` — 기존 dashboard와 동일하게 `site.Data.kb_items`를 `jsonify`로 주입해 클라이언트 JS로 렌더링.

- **헤더**: "KB Radar" 타이틀 + 부제 "지식 레이더", 마지막 수집일(`last_collected`), 전체/카테고리별 항목 수.
- **필터 바**:
  - 카테고리 토글: 논문 · 기사 · 영상 · 인물 (다중 선택)
  - 아카이브 표시 on/off (기본 off → 최근 30일만)
  - 키워드 그룹/제목 텍스트 검색
- **본문**: 키워드 그룹별 섹션 → 각 섹션 안에 카드 그리드.
- **카드 구성**: 카테고리 뱃지 / 제목(원본 링크, `target=_blank`) / 한국어 요약 / 출처·발행일 / 그룹 태그.
- **테마**: PaperMod 다크·라이트 모드 연동(dashboard의 CSS 변수 패턴 재사용), full-bleed 레이아웃, "레이더" 감성의 미니멀 톤.
- 데이터가 비어 있을 때(최초)는 "아직 수집된 항목이 없습니다 — `scripts/run_kb_radar.sh` 실행 후 표시됩니다" 안내.

---

## 9. 컴포넌트 경계 (단위별 책임)

| 단위 | 책임 | 입력 | 출력 |
|---|---|---|---|
| `kb_keywords.yaml` | 무엇을 수집할지 선언 | (사용자) | 키워드 그룹 + 옵션 |
| `collect.md` (지시문) | 수집·요약·중복제거·아카이브 규칙 | keywords.yaml, 기존 items.json | 갱신된 items.json |
| `run_kb_radar.sh` | 실행 진입점 + 옵션 + 로그 | CLI 옵션 | claude 실행, 변경 요약 출력 |
| `single.html` | items.json 렌더링 + 필터 UI | site.Data.kb_items | HTML 화면 |

각 단위는 파일 경계로 분리되어 독립적으로 이해·수정 가능하다.

---

## 10. 범위 밖 (YAGNI)

- 인페이지 키워드 편집 저장(백엔드 부재로 불가) — 키워드는 YAML 직접 편집.
- 항목 읽음 표시·별점·개인 메모(추후 필요 시 스키마에 필드 추가로 확장 가능).
- 원격 `/schedule` 루틴(커밋 정책상 로컬 cron 채택).
- 외부 검색 API 연동(Claude Code WebSearch로 충분).
