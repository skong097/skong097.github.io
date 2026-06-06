# /projects/ GitHub 프로젝트 그래프 뷰 — 설계 문서

- **작성일**: 2026-06-06
- **상태**: 승인됨 (구현 대기)
- **목적**: `/projects/` 페이지 상단의 "Projects" 배너(cover)를 제거하고, GitHub 퍼블릭 레포를 가져와 **동적으로 움직이는 force-directed 그래프 뷰**로 보여준다. 하단의 하드코딩 프로젝트 카드(36개)는 **절대 수정하지 않는다**.

---

## 1. 배경 & 제약

- Hugo + PaperMod 정적 사이트, `main` push 시 GitHub Actions가 빌드해 GitHub Pages 배포. 서버 런타임 없음.
- KB Radar와 동일하게 **데이터 파일 → 클라이언트 렌더** 패턴 + **빌드 시 수집**을 따른다.
- 외부 의존성 0 — d3 등 라이브러리 없이 바닐라 JS + SVG(기존 대시보드 SVG 패턴과 동일).
- GitHub 계정: `skong097`. 기존 GitHub 연동 없음.
- **범위 제한**: `content/projects/_index.md`의 하단 하드코딩 카드 영역은 손대지 않는다. 상단 배너만 교체.

## 2. 핵심 결정 요약

| 항목 | 결정 |
|---|---|
| 데이터 소스 | **빌드 시 수집** → `data/github_repos.json` |
| CI 자동 갱신 | **추가** — `hugo_workflow.yml`에 빌드 전 fetch 스텝(`GITHUB_TOKEN` 사용) |
| 그래프 구조 | 중앙 허브(`skong097`) + 언어 노드 + 레포 노드 → 언어별 클러스터 |
| 레이아웃 | force-directed 물리 시뮬레이션, 영구 미세 드리프트로 항상 움직임 |
| 표시 레포 | 퍼블릭 원본만 (`fork=false`, `archived=false`), `updated` 최신순 |
| 렌더 기술 | SVG + 바닐라 JS, PaperMod 다크/라이트 연동 |
| 높이 | 데스크톱 420px / 모바일 300px (반응형) |
| 클릭 | 레포 노드 → 새 탭 repo / 허브 → 프로필 / 언어 노드 → 해당 언어 강조 |
| 호버 | 툴팁(이름·설명·언어·★stars) + 모션 살짝 정지 + 연결 강조 |
| 드래그 | 노드 드래그 이동 |

## 3. 데이터 흐름

```
api.github.com/users/skong097/repos?per_page=100
        │  scripts/fetch_github_repos.sh  (로컬 수동 / CI 자동)
        ▼
data/github_repos.json   (fork·archived 제외, 정제)
        │  Hugo 빌드: layouts/shortcodes/github-graph.html 가 site.Data.github_repos 주입
        ▼
/projects/ 상단 → force-directed 그래프 (SVG)
        │
        ▼  하단 하드코딩 카드 36개 — 변경 없음
```

## 4. 파일 구성

### 신규
| 경로 | 역할 |
|---|---|
| `data/github_repos.json` | 정제된 레포 목록 (스냅샷 커밋 + CI 갱신) |
| `scripts/fetch_github_repos.sh` | GitHub API → JSON 변환 (탭완성 지원) |
| `layouts/shortcodes/github-graph.html` | 그래프 CSS + SVG + JS |

### 수정
| 경로 | 변경 |
|---|---|
| `content/projects/_index.md` | front matter `cover.hiddenInSingle: true`; 본문 **최상단**에 `{{< github-graph >}}` 한 줄 추가. **카드 영역 무수정.** |
| `scripts/completion.bash` | `_fetch_github_repos` 핸들러 + `complete` 등록 추가 |
| `.github/workflows/hugo_workflow.yml` | `hugo` 빌드 전 fetch 스텝 추가 |

## 5. 데이터 스키마 (`data/github_repos.json`)

```json
{
  "fetched": "2026-06-06",
  "user": "skong097",
  "repos": [
    {
      "name": "kevin-patrol",
      "description": "ROS2 autonomous patrol robot",
      "language": "Python",
      "url": "https://github.com/skong097/kevin-patrol",
      "stars": 3,
      "updated": "2026-06-01",
      "topics": ["ros2", "yolo"]
    }
  ]
}
```

- 필터: `fork=false`, `archived=false`. 정렬: `updated` 내림차순.
- `language`가 null이면 `"Other"`로 정규화. `description` 없으면 빈 문자열.
- 최초/폴백용 스냅샷을 커밋해 둔다(데이터 없으면 페이지가 안내 문구만 표시).

## 6. 수집 스크립트 (`scripts/fetch_github_repos.sh`)

- `curl -s "https://api.github.com/users/<user>/repos?per_page=100&sort=updated"` 호출(있으면 `GITHUB_TOKEN`을 `Authorization` 헤더로 사용해 rate limit 완화).
- `python3`로 JSON 파싱 → `fork`/`archived` 제외 → 필요한 필드만 추려 `data/github_repos.json` 작성(2칸 들여쓰기).
- **탭 자동완성 지원**(CLAUDE.md 규칙): 옵션 헤더 주석 + `case` 파싱 + `-h/--help`.
  - `-h, --help`: 사용법
  - `--user <name>`: 대상 사용자 (기본 `skong097`)
  - `--output <path>`: 출력 경로 (기본 `data/github_repos.json`)
- **git 커밋 안 함** — 파일만 작성, 변경 요약 출력.

## 7. CI 자동 갱신 (`.github/workflows/hugo_workflow.yml`)

- `hugo` 실행 스텝 **직전**에 fetch 스텝 추가:
  - `env: GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` (Actions 기본 토큰, rate limit 1000/hr+)
  - `run: bash scripts/fetch_github_repos.sh || echo "fetch 실패 — 커밋된 스냅샷으로 빌드"`
- fetch 실패해도 커밋된 스냅샷으로 빌드되어 사이트가 깨지지 않는다.

## 8. 그래프 렌더링 (`layouts/shortcodes/github-graph.html`)

`{{ site.Data.github_repos | jsonify }}`로 데이터 주입, 클라이언트 SVG 렌더.

### 8.1 그래프 구조 (노드/엣지)
- **허브 노드** 1개: `skong097` (중앙).
- **언어 노드** N개: 데이터에 등장한 주 언어별 1개. 허브와 엣지로 연결.
- **레포 노드** M개: 각 레포는 자신의 `language` 노드와 엣지로 연결.
- 결과: 언어별로 레포가 클러스터링됨.

### 8.2 물리 시뮬레이션 (force-directed)
- 매 프레임(`requestAnimationFrame`):
  - **반발력**: 모든 노드 쌍 사이 거리 제곱 반비례 척력.
  - **인력**: 엣지로 연결된 노드 사이 스프링 인력.
  - **중력**: 전체를 SVG 중심으로 약하게 당김(허브는 더 강하게 고정).
  - **감쇠**: 속도에 damping 적용하되 **완전히 0으로 수렴하지 않게** 미세 난수 드리프트를 더해 항상 살아 움직이는 효과.
- 노드는 SVG viewBox 경계 안에 클램프.

### 8.3 인터랙션
- **호버**: 해당 노드와 직접 연결된 엣지/노드 강조(나머지 흐리게), 툴팁 표시(이름·설명·언어·★stars), 호버 중 모션 일시 감속.
- **클릭**: 레포 노드 → `url` 새 탭(`target=_blank rel=noopener`); 허브 → GitHub 프로필; 언어 노드 → 해당 언어 레포만 강조 토글.
- **드래그**: 노드를 끌어 위치 이동(놓으면 다시 물리 적용).

### 8.4 스타일/접근성
- 언어별 색상 팔레트(대시보드 DOMAIN_COLORS 톤 재사용). 다크/라이트 모드 CSS 변수 연동.
- 컨테이너 높이: 데스크톱 420px, 모바일(≤768px) 300px.
- `prefers-reduced-motion: reduce`면 드리프트/애니메이션을 멈추고 정적 배치로 표시(접근성).
- 텍스트 라벨은 레포 노드에 이름, 호버 시 상세.

### 8.5 폴백
- `repos`가 비었거나 데이터 없으면: "GitHub 프로젝트를 불러오는 중이거나 준비 중입니다" + `github.com/skong097` 링크.

## 9. 페이지 통합 (`content/projects/_index.md`)

- front matter `cover:`에 `hiddenInSingle: true` 추가(상단 배너 숨김). 나머지 front matter·하단 카드 HTML/CSS는 그대로.
- 본문 최상단(현재 `<style>` 블록 또는 intro 앞)에 `{{< github-graph >}}` 한 줄 삽입.
- shortcode가 자체 `<style>`/`<script>`를 포함하므로 기존 카드 스타일과 클래스 충돌 없도록 `.gh-graph-*` 네임스페이스 사용.

## 10. 컴포넌트 경계

| 단위 | 책임 | 입력 | 출력 |
|---|---|---|---|
| `fetch_github_repos.sh` | 레포 수집·정제 | GitHub API | `github_repos.json` |
| `github_repos.json` | 레포 데이터 계약 | (스크립트) | repos 배열 |
| `github-graph.html` | 그래프 렌더·물리·인터랙션 | `site.Data.github_repos` | SVG 그래프 |
| `_index.md` | shortcode 배치 + 배너 숨김 | shortcode | 페이지 상단 |
| `hugo_workflow.yml` | 빌드 전 자동 갱신 | (CI) | 최신 데이터 파일 |

## 11. 범위 밖 (YAGNI)

- 하단 하드코딩 카드 수정/연동 — **금지**.
- 레포 상세 페이지·커밋 히스토리 그래프 — 범위 밖.
- 실시간 브라우저 fetch(rate limit) — 빌드 시 수집으로 대체.
- 외부 그래프 라이브러리(d3 등) — 바닐라로 구현.
