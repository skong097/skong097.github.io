# 한/영 이중 언어 블로그 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hugo 블로그를 한국어(`/`) + 영어(`/en/`) 이중 언어로 전환하고 헤더에 KO ↔ EN 전환 버튼을 넣는다. 기존 한국어 URL은 하나도 바뀌지 않는다.

**Architecture:** Hugo 네이티브 다국어(`languages` 블록)를 쓴다. `defaultContentLanguage: ko` + `defaultContentLanguageInSubdir: false` 이므로 언어 접미사 없는 기존 `content/**/*.md` 260개가 자동으로 `ko` 에 귀속되어 파일명·URL 변경이 0건이다. 영문판은 UI 문구(i18n)와 허브 페이지 5개만 번역하고, 기존 포스트 47편은 한글 원문 그대로 `/en/posts/` 목록에 빌려 노출한다.

**Tech Stack:** Hugo 0.146.0 extended, PaperMod 테마(서브모듈 `3bb0ca2`), Go 템플릿, Hugo i18n YAML

**Spec:** `docs/superpowers/specs/2026-08-05-bilingual-blog-design.md`

## Global Constraints

- **Hugo 버전은 0.146.0 extended 고정** — CI(`.github/workflows/hugo.yml`)와 동일. 다른 버전으로 검증하지 말 것.
- **템플릿에서 `site.Data` 표기 유지.** `hugo.Data` 로 바꾸면 CI 빌드가 깨진다. (`CLAUDE.md`)
- **최우선 성공 기준: 기존 한국어 URL 삭제·변경 0건.** 매 태스크 끝에서 baseline 과 대조한다. 위반 시 즉시 롤백.
- **전 직장 업체명(NCsoft 등) 절대 노출 금지.** (`CLAUDE.md`)
- **브랜치는 `feat/i18n-bilingual`.** `main` 에서 작업하지 않는다. `main` 은 push 시 GitHub Pages 로 자동 배포되므로 미완성 상태가 라이브로 나가면 안 된다.
- **`git add` / `git commit` 은 이 계획 실행 중에 한해 허용된다** (사용자가 2026-08-05 에 명시적으로 승인). 태스크마다 커밋해서 리뷰·롤백 지점을 남긴다.
- **`git push` 는 절대 실행하지 않는다.** 배포 시점은 사용자가 직접 통제한다. (사용자 전역 `CLAUDE.md`)
- **빌드 산출물은 항상 스크래치패드로 낸다.** 저장소의 `public/` 을 건드리지 않는다. `public/` 은 `.gitignore` 대상.
- 작업 디렉터리: `/home/gjkong/skong097.github.io`
- 스크래치패드: `/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad` (이하 `$SP`)
- **번역하지 않는 것**: 기존 포스트 260개 본문, SVG 다이어그램 한글 라벨, 드래프트 203편.

### 사전 확인된 사실 (재조사 불필요)

- `themes/PaperMod` 서브모듈은 **이미 체크아웃 완료** (`3bb0ca2`).
- PaperMod 는 `layouts/partials/partials/header.html` 이 아니라 `themes/PaperMod/layouts/partials/header.html` 에 언어 스위처를 내장하고 있으며, 링크가 `site.Home.Translations` 라서 **항상 홈으로 이동**한다. 이것이 오버라이드가 필요한 이유다.
- PaperMod 는 `i18n/ko.yaml` 과 `i18n/en.yaml` 을 이미 제공한다. 프로젝트 `i18n/` 은 테마와 **병합**되므로 커스텀 키만 추가하면 되고, 테마 키를 다시 쓸 필요가 없다.
- `layouts/index.html`, `layouts/_default/list.html`, `layouts/partials/extend_head.html` 의 한글은 **전부 주석**이다. 건드리지 않는다.
- `layouts/kb-radar/single.html` 은 현재 **커밋되지 않은 수정분(M)** 이 있다. Task 0 에서 처리한다.

---

## File Structure

| 파일 | 책임 | 상태 |
|---|---|---|
| `hugo.yaml` | 언어 정의, 언어별 메뉴/제목/설명 | 수정 |
| `layouts/partials/header.html` | 언어 토글 (현재 페이지 번역본 우선) | **신규** (테마 복사 후 1블록 수정) |
| `i18n/ko.yaml` | 커스텀 템플릿 한국어 문자열 | **신규** |
| `i18n/en.yaml` | 커스텀 템플릿 영어 문자열 | **신규** |
| `layouts/_default/list.html` | 섹션 목록. EN 일 때 ko 포스트 차용 | 수정 |
| `layouts/index.html` | 홈 그리드. EN 일 때 ko 포스트 차용 | 수정 |
| `layouts/kb-radar/single.html` | KB Radar 뷰. 문자열 i18n 화 | 수정 |
| `layouts/partials/hero-3d.html` | 히어로. 설명문 i18n + 링크 langURL | 수정 |
| `layouts/partials/hero-3d_dark.html` | 히어로(다크). 동일 | 수정 |
| `layouts/shortcodes/about-3d.html` | About 3D. 문자열 i18n 화 | 수정 |
| `layouts/shortcodes/github-graph.html` | GitHub 그래프. 문자열 i18n 화 | 수정 |
| `assets/css/extended/custom.css` | 추출한 projects/gallery 고유 클래스 CSS | 수정(추가) |
| `content/projects/_index.md` | 한국어 프로젝트 페이지 | 수정(CSS 축소) |
| `content/gallery/_index.md` | 한국어 갤러리 페이지 | 수정(CSS 축소) |
| `content/about/index.en.md` | 영문 About | **신규** |
| `content/projects/_index.en.md` | 영문 Projects | **신규** |
| `content/gallery/_index.en.md` | 영문 Gallery | **신규** |
| `content/kb-radar/index.en.md` | 영문 KB Radar | **신규** |
| `content/search.en.md` | 영문 Search | **신규** |
| `CLAUDE.md` | 향후 한/영 쌍 작성 규칙 | 수정(섹션 추가) |

---

## Task 0: 검증 환경 구축 + baseline URL 스냅샷

이 태스크가 나머지 전부의 안전망이다. 먼저 끝내지 않으면 회귀를 감지할 수 없다.

**Files:**
- 생성: `$SP/baseline_urls.txt` (저장소 밖)
- 저장소 파일 변경 없음

**Interfaces:**
- Produces: `$SP/baseline_urls.txt` — 변경 전 사이트의 전체 URL 목록. Task 1~8 의 회귀 검사 기준값.
- Produces: `hugo` 실행 파일 (`$HOME/bin/hugo`), 버전 0.146.0 extended.

- [ ] **Step 1: 커밋 안 된 수정분 확인**

`layouts/kb-radar/single.html` 에 미커밋 변경이 있다. baseline 을 오염시키지 않도록 내용을 먼저 확인한다.

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
mkdir -p "$SP"
git diff --stat
git diff layouts/kb-radar/single.html
git diff > "$SP/pre_work.patch"      # 롤백 시 이 미커밋 변경분을 복원하기 위한 백업
wc -l "$SP/pre_work.patch"
```

이 변경분은 **되돌리지 않는다.** 사용자가 의도적으로 작업 중인 내용이므로 그대로 두고, baseline 도 이 상태 기준으로 잡는다. 내용을 사용자에게 한 줄로 보고한다.

`$SP/pre_work.patch` 는 부록의 롤백 절차가 전제하는 파일이다. 반드시 여기서 만들어 둔다.

- [ ] **Step 2: Hugo 0.146.0 extended 설치 (sudo 불필요)**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
mkdir -p "$HOME/bin" "$SP"
wget -q -O "$SP/hugo.tar.gz" \
  https://github.com/gohugoio/hugo/releases/download/v0.146.0/hugo_extended_0.146.0_linux-amd64.tar.gz
tar -xzf "$SP/hugo.tar.gz" -C "$HOME/bin" hugo
"$HOME/bin/hugo" version
```

기대 출력: `hugo v0.146.0 ... extended` 문자열 포함.
`extended` 가 없으면 잘못 받은 것이다 — 다시 받는다.

- [ ] **Step 3: baseline 빌드**

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
"$HOME/bin/hugo" --gc --minify --destination "$SP/public_baseline" 2>&1 | tee "$SP/build_baseline.log"
```

기대: 마지막 줄에 `Total in ...ms`. `ERROR` 0건.
WARN 이 있으면 **내용을 기록해 둔다** — 변경 후 늘어나지 않았는지 비교할 기준이다.

- [ ] **Step 4: baseline URL 목록 저장**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
cd "$SP/public_baseline"
find . -name 'index.html' | sed 's|^\./||; s|index\.html$||' | sort > "$SP/baseline_urls.txt"
wc -l "$SP/baseline_urls.txt"
```

기대: 수백 줄. 0 줄이면 빌드가 실패한 것이다 — Step 3 으로 돌아간다.

- [ ] **Step 5: 회귀 검사 절차 확인 (지금은 결과가 비어야 정상)**

이 명령이 앞으로 매 태스크 끝에서 쓰는 **회귀 게이트**다.

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
cd "$SP/public_baseline"
find . -name 'index.html' | sed 's|^\./||; s|index\.html$||' | sort > "$SP/after_urls.txt"
comm -23 "$SP/baseline_urls.txt" "$SP/after_urls.txt"
```

기대: **출력 0줄** (자기 자신과 비교하므로 당연히 비어야 한다). 여기서 뭔가 나오면 명령이 잘못된 것이다.

- [ ] **Step 6: 커밋 — 없음**

이 태스크는 저장소 파일을 바꾸지 않는다. 커밋할 것이 없다.
단, 서브모듈이 새로 체크아웃되었으므로 상태만 확인해 사용자에게 보고한다.

```bash
cd /home/gjkong/skong097.github.io && git status --short
```

---

## Task 1: hugo.yaml 다국어 전환

**Files:**
- Modify: `hugo.yaml` (전면 재구성)

**Interfaces:**
- Produces: `languages.ko` / `languages.en` 정의. 이후 모든 태스크가 `site.Language.Lang` 으로 `"ko"` / `"en"` 을 분기한다.
- Produces: `params.mainSections: ["posts"]` — Task 4 의 `where ... "Type" "in" site.Params.mainSections` 가 EN 사이트에서도 결정적으로 동작하게 하는 값. **명시하지 않으면 EN 은 콘텐츠가 없어 Hugo 의 자동 추론이 빈 값을 내고 홈 그리드가 비어버린다.**
- Produces: `params.displayFullLangName: true` — Task 2 의 토글이 "한국어"/"English" 로 표시되게 한다.

- [ ] **Step 1: 현재 hugo.yaml 백업**

```bash
cd /home/gjkong/skong097.github.io
cp hugo.yaml /tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad/hugo.yaml.bak
```

- [ ] **Step 2: hugo.yaml 전체 교체**

아래 내용으로 `hugo.yaml` 을 통째로 바꾼다.

```yaml
baseURL: https://skong097.github.io/
theme: PaperMod

defaultContentLanguage: ko
defaultContentLanguageInSubdir: false

googleAnalytics: ""

languages:
  ko:
    languageName: 한국어
    languageCode: ko
    weight: 1
    title: Stephen's Robotics Lab
    params:
      description: ROS2 · AI/ML · AI Agent · Computer Vision · Robotics 프로젝트 기록
      homeInfoParams:
        Title: Robotics × AI × ROS2
        Content: '자율순찰 로봇, 컴퓨터 비전, 로보틱스 시뮬레이션을 다루는 개발 블로그입니다. ROS2 기반 로봇 시스템, PyQt6 대시보드,
          YOLO/ST-GCN 비전 파이프라인, LLM 통합 등 실전 프로젝트 경험을 공유합니다. AI Agent 기반 자동화 도구 개발과 에이전트
          협업 Flow 구축도 함께 다룹니다. '
    menu:
      main:
      - identifier: home
        name: 홈
        url: /
        weight: 5
      - identifier: projects
        name: 프로젝트
        url: /projects/
        weight: 10
      - identifier: gallery
        name: 갤러리
        url: /gallery/
        weight: 15
      - identifier: posts
        name: 포스트
        url: /posts/
        weight: 20
      - identifier: kb-radar
        name: KB Radar
        url: /kb-radar/
        weight: 25
      - identifier: categories
        name: 카테고리
        url: /categories/
        weight: 30
      - identifier: search
        name: 검색
        url: /search/
        weight: 50
      - identifier: about
        name: About me
        url: /about/
        weight: 60
  en:
    languageName: English
    languageCode: en
    weight: 2
    title: Stephen's Robotics Lab
    params:
      description: ROS2 · AI/ML · AI Agent · Computer Vision · Robotics project notes
      homeInfoParams:
        Title: Robotics × AI × ROS2
        Content: 'A development blog on autonomous patrol robots, computer vision, and robotics simulation.
          Covers ROS2-based robot systems, PyQt6 dashboards, YOLO/ST-GCN vision pipelines, and LLM integration
          from hands-on projects, along with AI-agent automation tooling and multi-agent collaboration flows. '
    menu:
      main:
      - identifier: home
        name: Home
        url: /
        weight: 5
      - identifier: projects
        name: Projects
        url: /projects/
        weight: 10
      - identifier: gallery
        name: Gallery
        url: /gallery/
        weight: 15
      - identifier: posts
        name: Posts
        url: /posts/
        weight: 20
      - identifier: kb-radar
        name: KB Radar
        url: /kb-radar/
        weight: 25
      - identifier: categories
        name: Categories
        url: /categories/
        weight: 30
      - identifier: search
        name: Search
        url: /search/
        weight: 50
      - identifier: about
        name: About me
        url: /about/
        weight: 60

params:
  env: production
  author: Stephen Kong
  mainSections:
  - posts
  displayFullLangName: true
  ShowReadingTime: true
  ShowPostNavLinks: true
  ShowBreadCrumbs: false
  ShowCodeCopyButtons: true
  ShowToc: true
  defaultTheme: dark
  disableThemeToggle: false
  # ── 검색(Fuse.js) 튜닝 ──────────────────────────────
  # ignoreLocation: 긴 본문 어디서든 매치(기본은 앞부분 위주) → recall 대폭↑
  # threshold 0.3: 느슨한 기본 0.4 대비 잡음↓ (오타 허용은 유지)
  # keys: title·tags·categories 가중↑ (인덱스에 tags/categories 추가됨)
  fuseOpts:
    isCaseSensitive: false
    shouldSort: true
    location: 0
    distance: 1000
    threshold: 0.3
    minMatchCharLength: 2
    ignoreLocation: true
    keys:
    - {name: title, weight: 0.5}
    - {name: tags, weight: 0.2}
    - {name: categories, weight: 0.1}
    - {name: summary, weight: 0.1}
    - {name: content, weight: 0.1}
  socialIcons:
  - name: github
    url: https://github.com/skong097
  assets:
    favicon: /favicon.ico
  cover:
    image: images/covers/hero-banner.png
    alt: Stephen's Robotics Lab
    hidden: false
    hiddenInList: false
    hiddenInSingle: false

outputs:
  home:
  - HTML
  - RSS
  - JSON
# 날짜 디렉터리(0710/ 등)로 옮기기 전에 auto_drive 루트에 남은 레거시 원본 초안.
# front matter가 없어 그대로 두면 라이브 페이지로 발행된다. 파일은 보존하고 빌드에서만 제외.
# (날짜 디렉터리 초안은 각 디렉터리의 _index.md 에서 build.render:never 로 처리)
ignoreFiles:
- content/posts/auto_drive/blog-\d{4}-\d{2}-\d{2}-.*\.md$
- content/posts/auto_drive/nav2-costmap-amcl-notes-\d{4}-\d{2}-\d{2}\.md$
markup:
  goldmark:
    renderer:
      unsafe: true
  highlight:
    style: dracula
```

주의: `menu` 의 `url` 은 `/projects/` 처럼 **언어 접두사 없이** 둔다. PaperMod 헤더가 `.URL | absLangURL` 로 렌더하므로 EN 에서는 자동으로 `/en/projects/` 가 된다. 여기에 `/en/` 을 직접 쓰면 `/en/en/projects/` 가 된다.

- [ ] **Step 3: 빌드 + 회귀 게이트**

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
"$HOME/bin/hugo" --gc --minify --destination "$SP/public_after" 2>&1 | tee "$SP/build_after.log"
grep -c ERROR "$SP/build_after.log" || true
cd "$SP/public_after"
find . -name 'index.html' | sed 's|^\./||; s|index\.html$||' | sort > "$SP/after_urls.txt"
echo "── 사라진 URL (0줄이어야 함) ──"
comm -23 "$SP/baseline_urls.txt" "$SP/after_urls.txt"
echo "── 새로 생긴 URL (전부 en/ 으로 시작해야 함) ──"
comm -13 "$SP/baseline_urls.txt" "$SP/after_urls.txt" | head -20
```

기대:
- ERROR 0건
- **사라진 URL 0줄** — 1줄이라도 나오면 즉시 중단하고 원인을 찾는다
- 새 URL 은 전부 `en/` 접두사

- [ ] **Step 4: EN 홈이 실제로 생성됐는지 확인**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
test -f "$SP/public_after/en/index.html" && echo "OK: /en/ 생성됨" || echo "FAIL: /en/ 없음"
grep -o '<title>[^<]*</title>' "$SP/public_after/en/index.html"
```

기대: `OK: /en/ 생성됨`

- [ ] **Step 5: 커밋**

```bash
git add hugo.yaml
```

```bash
git commit -m "i18n: hugo.yaml 다국어 전환 (ko 기본 + en 서브패스)

languages 블록으로 ko/en 분리. defaultContentLanguageInSubdir: false 로
기존 한국어 URL 무변경 유지. mainSections·displayFullLangName 명시."
```

---

## Task 2: 언어 토글 (헤더 오버라이드)

사용자의 명시적 필수 요구사항이다.

**Files:**
- Create: `layouts/partials/header.html` (테마 파일 복사 후 `lang-switch` 블록만 수정)

**Interfaces:**
- Consumes: Task 1 의 `languages.ko` / `languages.en`, `params.displayFullLangName: true`
- Produces: 모든 페이지 헤더 우상단의 `ul.lang-switch` 링크. 현재 페이지 번역본 우선, 없으면 상대 언어 홈.

- [ ] **Step 1: 테마 헤더를 그대로 복사**

```bash
cd /home/gjkong/skong097.github.io
cp themes/PaperMod/layouts/partials/header.html layouts/partials/header.html
wc -l layouts/partials/header.html
```

기대: 약 100줄.

- [ ] **Step 2: `lang-switch` 블록만 교체**

`layouts/partials/header.html` 에서 아래 **기존 블록**을 찾는다.

```gotemplate
                {{- if (not site.Params.disableLangToggle) }}
                    {{- $lang := .Lang}}
                    {{- $separator := or $label_text (not site.Params.disableThemeToggle)}}
                    {{- with site.Home.Translations }}
```

이 4줄을 아래로 바꾼다. **나머지 줄(`<ul class="lang-switch">` 이하)은 손대지 않는다.**

```gotemplate
                {{- if (not site.Params.disableLangToggle) }}
                    {{- $lang := .Lang}}
                    {{- $separator := or $label_text (not site.Params.disableThemeToggle)}}
                    {{/* ── 오버라이드: 현재 페이지의 번역본을 우선한다 ──
                         테마 원본은 site.Home.Translations 라서 어느 페이지에서 눌러도
                         상대 언어의 홈으로 튕긴다. 같은 글의 반대 언어판이 있으면 그쪽으로,
                         없으면(=기존 한글 포스트) 홈으로 폴백한다. */}}
                    {{- $translations := .Translations }}
                    {{- if not $translations }}
                        {{- $translations = site.Home.Translations }}
                    {{- end }}
                    {{- with $translations }}
```

- [ ] **Step 3: 빌드 + 토글 렌더 확인**

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
"$HOME/bin/hugo" --gc --minify --destination "$SP/public_after" 2>&1 | tail -5
echo "── ko 홈의 토글 ──"
grep -o 'lang-switch.\{0,220\}' "$SP/public_after/index.html"
echo "── en 홈의 토글 ──"
grep -o 'lang-switch.\{0,220\}' "$SP/public_after/en/index.html"
```

기대:
- ko 홈: `href="https://skong097.github.io/en/"` + `English`
- en 홈: `href="https://skong097.github.io/"` + `한국어`

`Ko` / `En` 로 나오면 Task 1 의 `displayFullLangName: true` 가 빠진 것이다.

- [ ] **Step 4: 번역본 없는 페이지의 폴백 확인**

기존 한글 포스트에는 EN 판이 없다. 홈으로 폴백해야 하고, **404 링크가 나오면 안 된다.**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
POST=$(find "$SP/public_after/posts" -name index.html | head -1)
echo "대상: $POST"
grep -o 'lang-switch.\{0,220\}' "$POST"
```

기대: `href="https://skong097.github.io/en/"` (상대 언어 홈).
`/en/posts/...` 같은 존재하지 않는 경로가 나오면 폴백 로직이 잘못된 것이다.

- [ ] **Step 5: 회귀 게이트**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
cd "$SP/public_after"
find . -name 'index.html' | sed 's|^\./||; s|index\.html$||' | sort > "$SP/after_urls.txt"
comm -23 "$SP/baseline_urls.txt" "$SP/after_urls.txt"
```

기대: **0줄**

- [ ] **Step 6: 커밋**

```bash
git add layouts/partials/header.html
```

```bash
git commit -m "i18n: 헤더 언어 토글 추가 (현재 페이지 번역본 우선)

PaperMod 내장 스위처는 site.Home.Translations 라서 어느 페이지에서 눌러도
홈으로 이동한다. .Translations 우선 + 홈 폴백으로 오버라이드."
```

---

## Task 3: i18n 문자열 파일 + 커스텀 템플릿 문자열 교체

**Files:**
- Create: `i18n/ko.yaml`
- Create: `i18n/en.yaml`
- Modify: `layouts/kb-radar/single.html` (11개 지점)
- Modify: `layouts/partials/hero-3d.html` (설명문 2줄 + 링크 2개)
- Modify: `layouts/partials/hero-3d_dark.html` (동일)
- Modify: `layouts/shortcodes/about-3d.html` (6개 문자열)
- Modify: `layouts/shortcodes/github-graph.html` (3개 문자열)

**Interfaces:**
- Produces: i18n 키 집합. Task 4 가 `koPostsNotice` 를, Task 6 의 EN 콘텐츠가 나머지를 전제한다.
- 프로젝트 `i18n/` 은 테마 `i18n/` 과 **병합**된다. 테마가 이미 제공하는 키(`search`, `read_time` 등)는 **다시 정의하지 않는다** — 덮어쓰면 테마 번역이 깨진다.

- [ ] **Step 1: `i18n/ko.yaml` 생성**

```yaml
# 커스텀 템플릿 전용 문자열. PaperMod 테마 i18n 과 병합되므로
# 테마가 이미 가진 키(search, read_time 등)는 여기 두지 않는다.

kbRadarSubtitle: "지식 레이더"
kbrCatPaper: "논문"
kbrCatArticle: "기사"
kbrCatVideo: "영상"
kbrCatPerson: "인물"
kbrArchiveToggle: "아카이브 포함"
kbrSearchPlaceholder: "제목·요약·그룹 검색…"
kbrFooterTagline: "키워드 기반 지식 수집"
kbrUntitled: "(제목 없음)"
kbrEmptyNoItems: "아직 수집된 항목이 없습니다."
kbrEmptyNoItemsHint: "를 실행하면 항목이 채워집니다."
kbrEmptyNoMatch: "필터 조건에 맞는 항목이 없습니다."
kbrPagerPrev: "이전"
kbrPagerNext: "다음"

heroDescLine1: "로보틱스 엔지니어의 기술 블로그"
heroDescLine2: "자율주행, 낙상 감지, Fleet 시스템 그리고 그 너머"

aboutFloatLine1: "사람을 돕는 Physical AI"
aboutFloatLine2: "신뢰받는 로봇을 만듭니다."
aboutName: "공국진"
aboutTraitLine1: "로봇·자율주행 엔지니어 —"
aboutTraitLine2: "23년 시스템 인프라의"
aboutTraitLine3: "내공을 더하다"

ghGraphAriaLabel: "GitHub 프로젝트 그래프"
ghGraphEmpty: "GitHub 프로젝트를 준비 중입니다"
ghGraphProfile: "GitHub 프로필"

koPostsNotice: ""
```

`koPostsNotice` 는 한국어 사이트에서는 배너를 띄우지 않으므로 빈 문자열이다.

- [ ] **Step 2: `i18n/en.yaml` 생성**

```yaml
# Custom template strings. Merged with PaperMod's own i18n —
# do not redefine theme-provided keys (search, read_time, ...).

kbRadarSubtitle: "Knowledge Radar"
kbrCatPaper: "Papers"
kbrCatArticle: "Articles"
kbrCatVideo: "Videos"
kbrCatPerson: "People"
kbrArchiveToggle: "Include archive"
kbrSearchPlaceholder: "Search title, summary, group…"
kbrFooterTagline: "Keyword-driven knowledge collection"
kbrUntitled: "(untitled)"
kbrEmptyNoItems: "No items collected yet."
kbrEmptyNoItemsHint: "to populate this view."
kbrEmptyNoMatch: "No items match the current filters."
kbrPagerPrev: "Prev"
kbrPagerNext: "Next"

heroDescLine1: "A robotics engineer's technical blog"
heroDescLine2: "Autonomous driving, fall detection, fleet systems, and beyond"

aboutFloatLine1: "Physical AI that helps people"
aboutFloatLine2: "Building robots people can trust."
aboutName: "Stephen Kong"
aboutTraitLine1: "Robotics & Autonomous Driving Engineer —"
aboutTraitLine2: "backed by 23 years"
aboutTraitLine3: "of systems infrastructure"

ghGraphAriaLabel: "GitHub project graph"
ghGraphEmpty: "GitHub projects coming soon"
ghGraphProfile: "GitHub profile"

koPostsNotice: "Posts are currently written in Korean. English translations are in progress."
```

- [ ] **Step 3: `layouts/kb-radar/single.html` — HTML 부분 교체**

103행 부근:

```html
      <h2>KB Radar <span>| {{ i18n "kbRadarSubtitle" }}</span></h2>
```

110~115행:

```html
      <span class="kbr-chip on" data-cat="paper">{{ i18n "kbrCatPaper" }}</span>
      <span class="kbr-chip on" data-cat="article">{{ i18n "kbrCatArticle" }}</span>
      <span class="kbr-chip on" data-cat="video">{{ i18n "kbrCatVideo" }}</span>
      <span class="kbr-chip on" data-cat="person">{{ i18n "kbrCatPerson" }}</span>
      <span class="kbr-chip" id="kbrArchive" data-archive>{{ i18n "kbrArchiveToggle" }}</span>
      <input class="kbr-search" id="kbrSearch" type="search" placeholder="{{ i18n "kbrSearchPlaceholder" }}">
```

122행:

```html
    KB Radar &mdash; {{ i18n "kbrFooterTagline" }} &middot; Stephen Kong &middot; {{ now.Year }}
```

- [ ] **Step 4: `layouts/kb-radar/single.html` — JS 부분 교체**

JS 문자열에는 반드시 `| jsonify` 를 쓴다. 따옴표까지 포함한 안전한 JSON 리터럴이 나오므로 따옴표를 직접 감싸면 안 된다.

129행:

```js
const CAT_LABEL = {
  paper:   {{ i18n "kbrCatPaper"   | jsonify }},
  article: {{ i18n "kbrCatArticle" | jsonify }},
  video:   {{ i18n "kbrCatVideo"   | jsonify }},
  person:  {{ i18n "kbrCatPerson"  | jsonify }}
};
```

155행:

```js
  const title = it.title ? esc(it.title) : {{ i18n "kbrUntitled" | jsonify }};
```

173~174행 — 원본은 백틱 템플릿 리터럴이다. `${...}` 보간과 Go 템플릿이 충돌하기 쉬우므로 **작은따옴표 문자열 연결로 바꾼다.**

```js
    main.innerHTML = '<div class="kbr-empty">' + {{ i18n "kbrEmptyNoItems" | jsonify }}
      + '<br><code>scripts/run_kb_radar.sh</code> ' + {{ i18n "kbrEmptyNoItemsHint" | jsonify }}
      + '</div>';
```

178행:

```js
    main.innerHTML = '<div class="kbr-empty">' + {{ i18n "kbrEmptyNoMatch" | jsonify }} + '</div>';
```

192·194행 — 이 두 줄은 백틱 템플릿 리터럴 안에 있다. 문자열 연결로 바꾼다:

```js
    html += '<nav class="kbr-pager">'
      + '<button type="button" data-page="prev"' + (state.page === 1 ? ' disabled' : '') + '>&lsaquo; ' + {{ i18n "kbrPagerPrev" | jsonify }} + '</button>'
      + '<span class="kbr-pageinfo"><strong>' + state.page + '</strong> / ' + pages + '</span>'
      + '<button type="button" data-page="next"' + (state.page === pages ? ' disabled' : '') + '>' + {{ i18n "kbrPagerNext" | jsonify }} + ' &rsaquo;</button>'
      + '</nav>';
```

- [ ] **Step 5: `hero-3d.html` / `hero-3d_dark.html` 교체**

두 파일 모두 20~22행 부근이 동일하다. **양쪽 다** 바꾼다.

```html
      <p class="hero-desc">
        {{ i18n "heroDescLine1" }}<br>
        {{ i18n "heroDescLine2" }}
      </p>
      <div class="hero-cta">
        <a href="{{ "/posts/" | relLangURL }}" class="btn-primary">Explore Posts</a>
        <a href="{{ "/kb-radar/" | relLangURL }}" class="btn-secondary">KB Radar</a>
      </div>
```

`relLangURL` 을 쓰는 이유: EN 홈의 버튼이 `/posts/`(한국어)가 아니라 `/en/posts/` 로 가야 한다.

- [ ] **Step 6: `about-3d.html` 교체 (126~136행)**

```html
<div class="about-3d-title-bar">
  <div class="about-3d-floating">{{ i18n "aboutFloatLine1" }}</div>
  <div class="about-3d-floating second">{{ i18n "aboutFloatLine2" }}</div>
</div>

<div class="about-3d-label">
  <div class="name">{{ i18n "aboutName" }}</div>
  <div class="trait">
    {{ i18n "aboutTraitLine1" }}<br>
    {{ i18n "aboutTraitLine2" }}<br>
    {{ i18n "aboutTraitLine3" }}
  </div>
</div>
```

- [ ] **Step 7: `github-graph.html` 교체 (9·12·143행)**

```html
  <svg class="gh-graph-svg" id="ghGraphSvg" viewBox="0 0 960 420" preserveAspectRatio="xMidYMid meet" aria-label="{{ i18n "ghGraphAriaLabel" }}"></svg>
```

```html
  <div class="gh-graph-empty" id="ghGraphEmpty" hidden>
    {{ i18n "ghGraphEmpty" }} &middot;
    <a href="https://github.com/skong097" target="_blank" rel="noopener">github.com/skong097</a>
  </div>
```

143행(JS):

```js
      html += '<div class="t-meta">' + {{ i18n "ghGraphProfile" | jsonify }} + '</div>';
```

- [ ] **Step 8: 빌드 + 한글 잔존 검사**

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
"$HOME/bin/hugo" --gc --minify --destination "$SP/public_after" 2>&1 | tail -5
echo "── ko 페이지: 한글 유지되어야 함 ──"
grep -c "지식 레이더" "$SP/public_after/kb-radar/index.html"
echo "── en 페이지에 한글이 남아 있으면 실패 ──"
grep -o "[가-힣]\+" "$SP/public_after/en/index.html" | sort -u
```

기대:
- ko `kb-radar` 에 `지식 레이더` 1건 이상
- **EN 홈의 한글 출력 0줄.** 나오면 그 문자열이 아직 i18n 화되지 않은 것이다.

- [ ] **Step 9: JS 문법 검사 (중요)**

문자열 연결로 바꾼 JS 가 깨지지 않았는지 확인한다.

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
python3 - <<'PY'
import re, sys, pathlib
p = pathlib.Path("/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad/public_after/kb-radar/index.html")
html = p.read_text(encoding="utf-8")
scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
print("script blocks:", len(scripts))
for i, s in enumerate(scripts):
    if "CAT_LABEL" in s:
        print("found KB script, length", len(s))
        print("has unbalanced braces:", s.count("{") != s.count("}"))
PY
```

기대: `has unbalanced braces: False`

브라우저 콘솔 검증이 가능하면 `hugo server` 로 띄워 `/kb-radar/` 와 `/en/kb-radar/` 에서 **JS 에러 0건**과 카드 렌더를 눈으로 확인한다.

- [ ] **Step 10: 회귀 게이트**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
cd "$SP/public_after"
find . -name 'index.html' | sed 's|^\./||; s|index\.html$||' | sort > "$SP/after_urls.txt"
comm -23 "$SP/baseline_urls.txt" "$SP/after_urls.txt"
```

기대: **0줄**

- [ ] **Step 11: 커밋**

```bash
git add i18n/ layouts/kb-radar/single.html layouts/partials/hero-3d.html layouts/partials/hero-3d_dark.html layouts/shortcodes/about-3d.html layouts/shortcodes/github-graph.html
```

```bash
git commit -m "i18n: 커스텀 템플릿 문자열을 i18n 키로 분리

KB Radar·히어로·About 3D·GitHub 그래프의 하드코딩 한글 24개를
i18n/{ko,en}.yaml 로 옮김. JS 문자열은 jsonify 로 안전하게 주입.
히어로 CTA 링크는 relLangURL 처리."
```

---

## Task 4: EN 사이트에 한국어 포스트 노출

**Files:**
- Modify: `layouts/_default/list.html:7-14` (페이지 수집부) 및 배너 삽입
- Modify: `layouts/index.html:10-12` (페이지 수집부) 및 배너 삽입

**Interfaces:**
- Consumes: Task 1 의 `params.mainSections: ["posts"]`, Task 3 의 i18n 키 `koPostsNotice`
- Produces: `/en/posts/` 와 `/en/` 에 한국어 포스트 47편 노출 + 영문 안내 배너

- [ ] **Step 1: `layouts/_default/list.html` 페이지 수집부 교체**

7~14행의 아래 블록을

```gotemplate
{{- $pages := union .RegularPages .Sections }}
{{- if .IsHome }}
{{- $pages = where site.RegularPages "Type" "in" site.Params.mainSections }}
{{- $pages = where $pages "Params.hiddenInHomeList" "!=" "true" }}
{{- end }}

{{- $paginator := .Paginate $pages }}
```

아래로 바꾼다.

```gotemplate
{{- $pages := union .RegularPages .Sections }}
{{- if .IsHome }}
{{- $pages = where site.RegularPages "Type" "in" site.Params.mainSections }}
{{- $pages = where $pages "Params.hiddenInHomeList" "!=" "true" }}
{{- end }}

{{/* ── EN: 영문 포스트가 아직 없으므로 한국어 포스트를 빌려 노출한다 ──
     대상은 홈과 posts 섹션으로만 한정한다. 카테고리/태그 term 페이지까지
     차용하면 언어가 뒤섞여 오히려 혼란스럽다. */}}
{{- $isHome := .IsHome }}
{{- $borrowedKo := false }}
{{- if and (eq site.Language.Lang "en") (or .IsHome (eq .Type "posts")) }}
  {{- if eq (len $pages) 0 }}
    {{- range site.Sites }}
      {{- if eq .Language.Lang "ko" }}
        {{- $koPages := where .RegularPages "Type" "in" site.Params.mainSections }}
        {{/* hiddenInHomeList 필터는 원본과 동일하게 홈에서만 적용한다 */}}
        {{- if $isHome }}
          {{- $koPages = where $koPages "Params.hiddenInHomeList" "!=" "true" }}
        {{- end }}
        {{- if gt (len $koPages) 0 }}
          {{- $pages = $koPages }}
          {{- $borrowedKo = true }}
        {{- end }}
      {{- end }}
    {{- end }}
  {{- end }}
{{- end }}

{{- $paginator := .Paginate $pages }}
```

`$isHome` 를 미리 뽑아두는 이유: `range site.Sites` 안에서는 `.` 이 각 Site 로 바뀌어 `.IsHome` 을 쓸 수 없다.

- [ ] **Step 2: `layouts/_default/list.html` 에 배너 삽입**

41행의 `<p class="term-total">` **바로 위**에 넣는다.

```gotemplate
  {{- if $borrowedKo }}
  <p class="term-doc-line">// {{ i18n "koPostsNotice" }}</p>
  {{- end }}

  <p class="term-total">// total {{ $paginator.TotalNumberOfElements }} · page {{ $paginator.PageNumber }}/{{ $paginator.TotalPages }}</p>
```

- [ ] **Step 3: `layouts/index.html` 페이지 수집부 교체**

10~12행의

```gotemplate
  {{- $pages := where site.RegularPages "Type" "in" site.Params.mainSections }}
  {{- $paginator := .Paginate $pages }}
```

를 아래로 바꾼다.

```gotemplate
  {{- $pages := where site.RegularPages "Type" "in" site.Params.mainSections }}

  {{/* ── EN 홈: 영문 포스트가 없으면 한국어 포스트를 빌려 노출 ── */}}
  {{- $borrowedKo := false }}
  {{- if and (eq site.Language.Lang "en") (eq (len $pages) 0) }}
    {{- range site.Sites }}
      {{- if eq .Language.Lang "ko" }}
        {{- $koPages := where .RegularPages "Type" "in" site.Params.mainSections }}
        {{- if gt (len $koPages) 0 }}
          {{- $pages = $koPages }}
          {{- $borrowedKo = true }}
        {{- end }}
      {{- end }}
    {{- end }}
  {{- end }}

  {{- if $borrowedKo }}
  <p class="home-ko-notice">{{ i18n "koPostsNotice" }}</p>
  {{- end }}

  {{- $paginator := .Paginate $pages }}
```

- [ ] **Step 4: 배너 스타일 추가**

`assets/css/extended/custom.css` 끝에 붙인다.

```css

/* ── EN 홈: 한국어 포스트 안내 배너 ───────────────────── */
.home-ko-notice {
  max-width: 1100px;
  margin: 0 auto 1.4rem;
  padding: .7rem 1rem;
  border-radius: 8px;
  border: 1px solid rgba(128, 128, 128, .25);
  background: var(--entry);
  color: var(--secondary);
  font-size: 13px;
  line-height: 1.6;
  text-align: center;
}
```

- [ ] **Step 5: 빌드 + EN 포스트 노출 확인**

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
"$HOME/bin/hugo" --gc --minify --destination "$SP/public_after" 2>&1 | tail -5
echo "── /en/posts/ 존재 ──"
test -f "$SP/public_after/en/posts/index.html" && echo OK || echo FAIL
echo "── /en/posts/ 항목 수 (0 이면 실패) ──"
grep -c 'class="term-row"' "$SP/public_after/en/posts/index.html"
echo "── 안내 배너 ──"
grep -c "English translations are in progress" "$SP/public_after/en/posts/index.html"
grep -c "English translations are in progress" "$SP/public_after/en/index.html"
echo "── ko 목록은 배너가 없어야 함 (0 이어야 정상) ──"
grep -c "English translations are in progress" "$SP/public_after/posts/index.html" || true
```

기대:
- `/en/posts/` 존재
- 항목 수 > 0
- EN 목록·EN 홈에 배너 각 1건
- **ko 목록에 배너 0건**

- [ ] **Step 6: 페이지네이션 동작 확인 (스펙에 명시된 리스크)**

교차 사이트 페이지 컬렉션에 `.Paginate` 를 건 부분이다. 여기서 깨질 수 있다.

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
ls "$SP/public_after/en/posts/" | head
echo "── 페이저 렌더 ──"
grep -o 'term-pager.\{0,200\}' "$SP/public_after/en/posts/index.html" | head -2
```

기대: `page/2/` 디렉터리 생성 + 페이저 렌더.

**실패 시 후퇴 방안** (스펙에 명시): EN 목록에 한해 페이지네이션을 포기하고 `first 24` 로 자른다. `list.html` 의 `$paginator` 사용부를 EN 분기에서만 아래로 대체한다.

```gotemplate
{{- if $borrowedKo }}{{ $pages = first 24 $pages }}{{ end }}
```

이 경우 사용자에게 "EN 목록은 최근 24편만 노출된다"고 **명시적으로 보고**한다. 조용히 자르지 말 것.

- [ ] **Step 7: 회귀 게이트**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
cd "$SP/public_after"
find . -name 'index.html' | sed 's|^\./||; s|index\.html$||' | sort > "$SP/after_urls.txt"
comm -23 "$SP/baseline_urls.txt" "$SP/after_urls.txt"
```

기대: **0줄**

- [ ] **Step 8: 커밋**

```bash
git add layouts/_default/list.html layouts/index.html assets/css/extended/custom.css
```

```bash
git commit -m "i18n: EN 사이트에 한국어 포스트 노출 + 안내 배너

영문 번역본이 없어 /en/posts/ 가 비는 문제 해결. site.Sites 에서
ko 페이지를 차용하고 koPostsNotice 배너를 띄운다. 홈·posts 섹션 한정."
```

---

## Task 5: projects/gallery 인라인 CSS 추출

**스펙에서 조정된 사항** — 스펙 6번은 `<style>` 블록 전체를 옮기라고 했으나, 조사 결과 두 파일 모두 `header.post-header` 를 **서로 다른 값으로** 정의한다. 전체를 옮기면 (1) 이 규칙이 전 사이트에 적용되어 모든 포스트/목록 페이지가 바뀌고 (2) 두 정의가 충돌해 마지막 것만 남는다. 인라인이었기 때문에 페이지 스코프가 유지되던 것이다.

**따라서 고유 클래스만 추출하고 `header.post-header` 관련 규칙은 인라인으로 남긴다.** 목표(번역으로 인한 CSS 2벌 유지 제거)는 그대로 달성되며, 중복은 페이지당 3~5줄로 줄어든다.

**Files:**
- Modify: `assets/css/extended/custom.css` (추가)
- Modify: `content/projects/_index.md:17-178` (`<style>` 축소)
- Modify: `content/gallery/_index.md:11-49` (`<style>` 축소)

**Interfaces:**
- Produces: `.projects-intro`, `.projects-grid`, `.project-card*`, `.status-*` (projects 고유) 및 `.gal-*`, `#wasab/#moca/#araseo/#homecare` (gallery 고유) 규칙이 전역 CSS 에 존재. Task 6 의 EN 콘텐츠 파일이 이 클래스들을 그대로 재사용한다.

- [ ] **Step 1: 추출 전 렌더 스냅샷 확보**

비교 기준이 없으면 회귀를 못 잡는다.

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
cp "$SP/public_after/projects/index.html" "$SP/projects_before.html"
cp "$SP/public_after/gallery/index.html"  "$SP/gallery_before.html"
```

- [ ] **Step 2: projects 의 고유 클래스 CSS 를 custom.css 로 이동**

`content/projects/_index.md` 의 **35~177행** (`.projects-intro {` 부터 `</style>` 직전까지)을 잘라내어 `assets/css/extended/custom.css` 끝에 붙인다.

구조 확인:

| 행 | 내용 | 처리 |
|---|---|---|
| 17 | `<style>` | 유지 |
| 18 | `/* ── Projects Page Custom Styles ── */` | 유지 |
| 19–34 | `header.post-header` 3개 규칙 | **인라인 유지** |
| **35–177** | `.projects-intro` ~ 마지막 미디어쿼리 | **custom.css 로 이동** |
| 178 | `</style>` | 유지 |

옮길 내용을 먼저 파일로 뽑아두면 안전하다.

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
sed -n '35,177p' content/projects/_index.md > "$SP/projects_extract.css"
head -3 "$SP/projects_extract.css"; echo "..."; tail -3 "$SP/projects_extract.css"
wc -l "$SP/projects_extract.css"
```

기대: 143줄. 첫 줄 `.projects-intro {`, 마지막 줄 `}`.

이 내용을 아래 헤더 주석과 함께 `custom.css` 끝에 붙인다.

```css

/* ══════════════════════════════════════════════════════
   Projects 페이지 (content/projects/_index.{md,en.md} 공용)
   ko/en 두 파일이 같은 마크업을 쓰므로 CSS 는 여기 한 곳에서만 관리한다.
   header.post-header 규칙은 페이지 스코프 유지를 위해 각 .md 에 인라인으로 남겨둔다.
   ══════════════════════════════════════════════════════ */

/* ← $SP/projects_extract.css 의 143줄을 그대로 붙여 넣는다 */
```

**규칙: 셀렉터 이름과 속성값을 바꾸지 않는다. 정리·최적화하지 않는다. 순수 이동만 한다.**

- [ ] **Step 3: `content/projects/_index.md` 의 `<style>` 축소**

`<style>` 블록을 아래만 남긴다.

```html
<style>
/* 이 페이지 전용 헤더 스타일. 전역 custom.css 로 옮기면 모든 페이지에 적용되므로
   인라인으로 유지한다. 나머지 .projects-* 규칙은 custom.css 에 있다. */
header.post-header {
  text-align: center;
  width: 100%;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}
header.post-header h1 {
  font-size: 40px;
  text-align: center;
}
[data-theme="light"] header.post-header {
  text-align: center;
  width: 100%;
  border-bottom-color: rgba(0,0,0,0.1);
}
</style>
```

- [ ] **Step 4: gallery 의 고유 클래스 CSS 를 custom.css 로 이동**

`content/gallery/_index.md` 의 **15~48행** (`.gal-intro` 부터 `.gal-note` 규칙 끝까지)을 옮긴다.

| 행 | 내용 | 처리 |
|---|---|---|
| 11 | `<style>` | 유지 |
| 12–13 | `header.post-header` 2개 규칙 | **인라인 유지** |
| 14 | 빈 줄 | 유지 |
| **15–48** | `.gal-intro` ~ `.gal-note` (`#wasab`·`#moca`·`#araseo`·`#homecare` 포함) | **custom.css 로 이동** |
| 49 | `</style>` | 유지 |

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
sed -n '15,48p' content/gallery/_index.md > "$SP/gallery_extract.css"
grep -c '^#wasab\|^#moca\|^#araseo\|^#homecare' "$SP/gallery_extract.css"
wc -l "$SP/gallery_extract.css"
```

기대: 34줄, `#` 시작 규칙 4건.

```css

/* ══════════════════════════════════════════════════════
   Gallery 페이지 (content/gallery/_index.{md,en.md} 공용)
   header.post-header 는 각 .md 에 인라인 유지.
   ══════════════════════════════════════════════════════ */

/* ← $SP/gallery_extract.css 의 34줄을 그대로 붙여 넣는다 */
```

- [ ] **Step 5: `content/gallery/_index.md` 의 `<style>` 축소**

```html
<style>
/* 이 페이지 전용 헤더 스타일. 나머지 .gal-* 규칙은 custom.css 에 있다. */
header.post-header { text-align:center; width:100%; border-bottom:1px solid rgba(128,128,128,.2); padding-bottom:1rem; margin-bottom:1.2rem; }
header.post-header h1 { font-size:40px; text-align:center; }
</style>
```

- [ ] **Step 6: 빌드 + CSS 규칙 존재 확인**

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
"$HOME/bin/hugo" --gc --minify --destination "$SP/public_after" 2>&1 | tail -5
CSS=$(find "$SP/public_after/assets" -name '*.css' | head -1)
echo "번들 CSS: $CSS"
for sel in projects-intro project-card-title status-active gal-sec gal-grid gal-cap; do
  printf "%-20s %s\n" "$sel" "$(grep -c "$sel" "$CSS")"
done
echo "── #wasab 계열 ──"
grep -o '#wasab[^}]*}' "$CSS"
```

기대: 모든 셀렉터 카운트 ≥ 1. `#wasab ... background:#0F766E` 확인.

- [ ] **Step 7: 렌더 회귀 확인 (육안 필수)**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
echo "── projects: 카드 수 (before/after 같아야 함) ──"
grep -c 'class="project-card"' "$SP/projects_before.html"
grep -c 'class="project-card"' "$SP/public_after/projects/index.html"
echo "── gallery: 섹션 수 + 앵커 ──"
grep -c 'class="gal-sec"' "$SP/gallery_before.html"
grep -c 'class="gal-sec"' "$SP/public_after/gallery/index.html"
grep -o 'id="\(wasab\|moca\|araseo\|homecare\)"' "$SP/public_after/gallery/index.html"
```

기대: before/after 카운트 동일, 앵커 4개 모두 존재(포트폴리오 QR 연결용이라 절대 사라지면 안 된다).

**추가로 반드시 눈으로 볼 것**: `hugo server` 로 띄워 `/projects/` 와 `/gallery/` 를 다크·라이트 모드 양쪽에서 확인한다. 카드 테두리·강조색·갤러리 제목 배경색(#0F766E 등)이 이전과 같아야 한다. 이 태스크는 번역과 무관한 유일한 렌더 회귀 위험 구간이다.

- [ ] **Step 8: 회귀 게이트**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
cd "$SP/public_after"
find . -name 'index.html' | sed 's|^\./||; s|index\.html$||' | sort > "$SP/after_urls.txt"
comm -23 "$SP/baseline_urls.txt" "$SP/after_urls.txt"
```

기대: **0줄**

- [ ] **Step 9: 커밋**

```bash
git add assets/css/extended/custom.css content/projects/_index.md content/gallery/_index.md
```

```bash
git commit -m "refactor: projects/gallery 고유 클래스 CSS 를 custom.css 로 추출

영문판이 같은 마크업을 쓰므로 CSS 를 한 곳에서 관리하기 위함.
header.post-header 는 전역 적용·상호 충돌을 피해 각 .md 에 인라인 유지."
```

---

## Task 6: 영문 콘텐츠 파일 5개

**Files:**
- Create: `content/about/index.en.md`
- Create: `content/projects/_index.en.md`
- Create: `content/gallery/_index.en.md`
- Create: `content/kb-radar/index.en.md`
- Create: `content/search.en.md`

**Interfaces:**
- Consumes: Task 5 의 전역 CSS 클래스(`.projects-*`, `.gal-*`), Task 3 의 i18n 키
- Produces: `/en/about/`, `/en/projects/`, `/en/gallery/`, `/en/kb-radar/`, `/en/search/`

**공통 번역 규칙 (5개 파일 전부에 적용):**

1. front matter 는 대응 ko 파일에서 **그대로 복사**하되, `title` 만 영문화하고 **`url:` 필드는 삭제**한다. `url:` 을 남기면 `/en/` 접두사가 붙지 않아 ko 페이지와 URL 이 충돌한다.
2. HTML 구조·클래스명·`id` 속성·`style="--card-accent: ..."` 인라인 값은 **한 글자도 바꾸지 않는다.**
3. `src` / `href` 경로는 **그대로 둔다.** 이미지·동영상 파일명에 한글이 들어 있어도 바꾸지 않는다(`/images/gallery/demo/카페닌자.mp4` 등). 포스트 링크(`/posts/robotics/moca-...`)도 한국어 포스트를 가리킨 채로 둔다 — 영문 번역본이 없으므로 의도된 동작이다.
4. **갤러리 섹션 앵커 `#wasab` `#moca` `#araseo` `#homecare` 는 반드시 동일하게 유지한다.** 포트폴리오 QR 코드가 이 앵커로 연결된다.
5. `<style>` 블록은 Task 5 에서 축소된 ko 파일의 것을 **그대로 복사**한다(3~5줄).
6. 번역은 의미 1:1. 기술 용어(ROS2, Nav2, BehaviorTree.CPP, YOLOv8n, MediaPipe, FastAPI 등)는 원문 유지.
7. **전 직장 업체명은 어떤 형태로도 넣지 않는다.**

- [ ] **Step 1: `content/kb-radar/index.en.md` 생성 (가장 작음 — 여기서 규칙 검증)**

먼저 ko 원본을 확인한다.

```bash
cat /home/gjkong/skong097.github.io/content/kb-radar/index.md
```

그 구조를 그대로 따르되 `title` 만 영문화하고 `url:` 을 뺀다. 본문 문구가 있으면 영역한다.

- [ ] **Step 2: 빌드해서 규칙이 맞는지 즉시 확인**

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
"$HOME/bin/hugo" --gc --minify --destination "$SP/public_after" 2>&1 | tail -3
test -f "$SP/public_after/en/kb-radar/index.html" && echo "OK: /en/kb-radar/ 생성" || echo "FAIL"
test -f "$SP/public_after/kb-radar/index.html" && echo "OK: /kb-radar/ 유지" || echo "FAIL: ko 페이지 사라짐"
```

**둘 다 OK 여야 한다.** ko 쪽이 사라지면 `url:` 필드를 en 파일에 남겨둔 것이다.

- [ ] **Step 3: `content/search.en.md` 생성**

```bash
cat /home/gjkong/skong097.github.io/content/search.md
```

동일 규칙으로 영문판을 만든다. `layout: search` 는 그대로 유지한다.

- [ ] **Step 4: `content/about/index.en.md` 생성**

ko 원본은 662줄이며 13~346행이 `<style>`, 349행이 `{{< about-3d >}}` 쇼트코드다.

```bash
sed -n '1,12p' /home/gjkong/skong097.github.io/content/about/index.md   # front matter
sed -n '347,662p' /home/gjkong/skong097.github.io/content/about/index.md # 본문
```

- `<style>` 블록(13~346행)은 **그대로 복사**한다. About 은 Task 5 의 CSS 추출 대상이 아니다.
- `{{< about-3d >}}` 쇼트코드는 그대로 둔다 — 내부 문자열은 Task 3 에서 이미 i18n 화되어 언어에 맞게 렌더된다.
- 본문 산문만 영역한다.

- [ ] **Step 5: `content/projects/_index.en.md` 생성**

번역 대상은 아래 9장의 카드다. `project-card-title` 은 이미 영문이므로 **그대로 두고**, `project-card-subtitle` 과 `project-card-desc`, 링크 라벨만 영역한다.

| 카드 title (변경 없음) | subtitle ko → en |
|---|---|
| MOCA — Cafe Service Robot | 카페 모객·서빙·안내 자율 로봇 → Autonomous cafe robot for greeting, serving, and guidance |
| ARASEO — Autonomous Taxi | 미니시티 자율주행 택시 시스템 → Mini-city autonomous taxi system |
| Kevin Patrol Fleet Dashboard | 다중 로봇 플릿 모니터링 시스템 → Multi-robot fleet monitoring system |
| Kevin Patrol Dashboard | 자율 순찰 로봇 모니터링 대시보드 → Autonomous patrol robot monitoring dashboard |
| Home Safe Solution | Vision AI 기반 낙상 감지 시스템 → Vision-AI fall detection system |
| EyeCon (피노키오) v3.5 | 실시간 대화 분석 시스템 → Real-time conversation analysis system |
| Home Guard Bot | LLM + ROS2 통합 가드 로봇 → LLM + ROS2 integrated guard robot |
| ROS2 Commander | 게임형 ROS2 학습 애플리케이션 → Gamified ROS2 learning application |

`EyeCon (피노키오) v3.5` 의 title 은 `EyeCon (Pinocchio) v3.5` 로 바꾼다 — title 중 유일하게 한글이 있다.
`status-active` / `status-done` 의 텍스트("Active"/"Done")는 이미 영문이므로 그대로 둔다.
`project-card-tag` 값(ROS2 Jazzy, C++, Nav2 등)도 그대로 둔다.
`project-card-link` 라벨(`감정 인식 BT →` 등)은 영역하되 **`href` 는 그대로** 둔다.
`{{< github-graph >}}` 쇼트코드는 그대로 유지한다.
`<p class="projects-intro">` 는 "Projects in robotics, computer vision, and AI." 로 영역한다.

- [ ] **Step 6: `content/gallery/_index.en.md` 생성**

섹션 제목 번역 매핑:

| ko | en |
|---|---|
| `WaSaB — 다중 로봇 통합관제 <span class="tag">심화과정 · 단독 수행</span>` | `WaSaB — Multi-Robot Integrated Control <span class="tag">Advanced course · Solo</span>` |
| `MOCA — 카페 서빙·모객 로봇 <span class="tag">6인 팀 · 최우수상</span>` | `MOCA — Cafe Serving & Greeting Robot <span class="tag">Team of 6 · Grand prize</span>` |
| `ARASEO / DALIMI — 자율주행 택시 <span class="tag">팀 프로젝트</span>` | `ARASEO / DALIMI — Autonomous Taxi <span class="tag">Team project</span>` |
| `Home Care-Vision AI — 낙상 감지 <span class="tag">5인 팀</span>` | `Home Care-Vision AI — Fall Detection <span class="tag">Team of 5</span>` |

- `<div class="gal-sec" id="...">` 의 `id` 는 **절대 바꾸지 않는다.**
- `.gal-cap .n` / `.t` / `.s` 안의 캡션 문구를 영역한다.
- `<video src="...">` / `<img src="...">` 경로는 한글 파일명 포함 **그대로**.
- `.gal-note` 문구를 영역한다.

- [ ] **Step 7: 전체 빌드 + EN 페이지 5개 확인**

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
"$HOME/bin/hugo" --gc --minify --destination "$SP/public_after" 2>&1 | tail -5
for p in about projects gallery kb-radar search; do
  printf "%-10s en:%s ko:%s\n" "$p" \
    "$(test -f "$SP/public_after/en/$p/index.html" && echo OK || echo FAIL)" \
    "$(test -f "$SP/public_after/$p/index.html" && echo OK || echo FAIL)"
done
```

기대: 10개 전부 OK.

- [ ] **Step 8: 갤러리 앵커·미디어 무결성 확인**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
echo "── EN 갤러리 앵커 4개 ──"
grep -o 'id="\(wasab\|moca\|araseo\|homecare\)"' "$SP/public_after/en/gallery/index.html"
echo "── ko/en 미디어 src 개수 일치 확인 ──"
grep -o 'src="/images/gallery[^"]*"' "$SP/public_after/gallery/index.html" | sort > "$SP/g_ko.txt"
grep -o 'src="/images/gallery[^"]*"' "$SP/public_after/en/gallery/index.html" | sort > "$SP/g_en.txt"
diff "$SP/g_ko.txt" "$SP/g_en.txt" && echo "OK: 미디어 경로 동일" || echo "FAIL: 미디어 경로가 다름"
```

기대: 앵커 4개, `OK: 미디어 경로 동일`.

- [ ] **Step 9: EN 페이지 한글 잔존 검사**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
for p in about projects kb-radar search; do
  echo "── /en/$p/ ──"
  grep -o "[가-힣]\+" "$SP/public_after/en/$p/index.html" | sort -u | head -10
done
```

기대: 출력 없음.
`/en/gallery/` 는 미디어 파일명에 한글이 있어 여기서 제외했다. 대신 아래로 확인한다.

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
grep -o '>[^<]*[가-힣][^<]*<' "$SP/public_after/en/gallery/index.html" | head -20
```

기대: 출력 없음(태그 사이의 표시 텍스트에 한글이 없어야 한다).

- [ ] **Step 10: 회귀 게이트**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
cd "$SP/public_after"
find . -name 'index.html' | sed 's|^\./||; s|index\.html$||' | sort > "$SP/after_urls.txt"
comm -23 "$SP/baseline_urls.txt" "$SP/after_urls.txt"
```

기대: **0줄**

- [ ] **Step 11: 커밋**

```bash
git add content/about/index.en.md content/projects/_index.en.md content/gallery/_index.en.md content/kb-radar/index.en.md content/search.en.md
```

```bash
git commit -m "i18n: 영문 허브 페이지 5개 추가

About·Projects·Gallery·KB Radar·Search 영문판. 갤러리 섹션 앵커와
미디어 경로는 ko 와 동일하게 유지(포트폴리오 QR 연결 보존)."
```

---

## Task 7: CLAUDE.md 향후 포스트 규칙

**Files:**
- Modify: `CLAUDE.md` (섹션 추가)

**Interfaces:**
- Consumes: Task 1~6 이 확립한 파일 명명 규칙
- Produces: 앞으로 포스트를 쓸 때 따를 규칙. 코드 산출물 없음.

- [ ] **Step 1: `CLAUDE.md` 의 `## 기타` 섹션 **바로 앞**에 아래 섹션 삽입**

```markdown
## 포스트는 한/영 두 벌로 작성한다 (필수)

이 블로그는 한국어(`/`) + 영어(`/en/`) 이중 언어다. **새 포스트는 반드시 한/영 쌍으로 만든다.**

### 파일 명명

| | 파일 | URL |
|---|---|---|
| 한국어 | `content/posts/<category>/<english-slug>.md` | `/posts/<category>/<한글-슬러그>/` |
| 영어 | `content/posts/<category>/<english-slug>.en.md` | `/en/posts/<category>/<english-slug>/` |

- **두 파일의 basename 이 같아야** Hugo 가 번역본으로 연결하고 헤더 토글이 서로를 가리킨다. `translationKey` 는 불필요하다.
- 한국어 파일 front matter 에 `slug: <한글-슬러그>` 를 넣어 기존 한글 URL 관례를 유지한다.
- 영어 파일에는 `slug` 를 넣지 않는다 — 영문 basename 이 그대로 URL 이 된다.

### front matter

`date` · `categories` · `tags` · `draft` 는 두 파일이 **동일해야 한다.** 다르면 목록 정렬과 분류가 어긋난다.
`title` · `description` · `summary` 만 각 언어로 쓴다.

### 다이어그램

- SVG 라벨이 한글이면 `<name>-en.svg` 를 따로 만들어 영문 파일에서 참조한다.
- 라벨이 영문·기호뿐이면 두 언어가 같은 SVG 를 공유한다.
- SVG 작성 규칙은 위의 "다이어그램 박스 → SVG 변환" 절을 따른다.

### 하지 않는 것

- 기존 포스트(2026-08-05 이전 발행분)를 소급 번역하지 않는다. 한국어 원문 그대로 두고, `/en/posts/` 에는 안내 배너와 함께 노출된다.
- UI 문구를 템플릿에 하드코딩하지 않는다. `i18n/ko.yaml` · `i18n/en.yaml` 에 키를 추가하고 `{{ i18n "key" }}` 로 쓴다. JS 안에서는 `{{ i18n "key" | jsonify }}` 를 쓴다.
```

- [ ] **Step 2: 빌드 영향 없음 확인**

`CLAUDE.md` 는 Hugo 콘텐츠가 아니므로 빌드에 영향이 없어야 한다.

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
"$HOME/bin/hugo" --gc --minify --destination "$SP/public_after" 2>&1 | tail -3
cd "$SP/public_after"
find . -name 'index.html' | sed 's|^\./||; s|index\.html$||' | sort > "$SP/after_urls.txt"
comm -23 "$SP/baseline_urls.txt" "$SP/after_urls.txt"
```

기대: **0줄**

- [ ] **Step 3: 커밋**

```bash
git add CLAUDE.md
```

```bash
git commit -m "docs: 새 포스트 한/영 쌍 작성 규칙 추가

<slug>.md + <slug>.en.md 명명, front matter 동기화 항목,
SVG 영문판 처리, 기존 포스트 소급 번역 제외를 명문화."
```

---

## Task 8: 최종 통합 검증

**Files:**
- 변경 없음. 검증만 한다.

**Interfaces:**
- Consumes: Task 0~7 전부
- Produces: 스펙 "검증" 표 10개 항목의 통과/실패 보고

- [ ] **Step 1: 클린 빌드**

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
rm -rf "$SP/public_final"
"$HOME/bin/hugo" --gc --minify --destination "$SP/public_final" 2>&1 | tee "$SP/build_final.log"
echo "── ERROR ──"; grep -c "ERROR" "$SP/build_final.log" || echo 0
echo "── WARN ──";  grep "WARN" "$SP/build_final.log" || echo "none"
```

기대: ERROR 0. WARN 은 Task 0 Step 3 에서 기록한 baseline WARN 보다 **늘지 않아야** 한다.

- [ ] **Step 2: 최종 회귀 게이트 (가장 중요)**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
cd "$SP/public_final"
find . -name 'index.html' | sed 's|^\./||; s|index\.html$||' | sort > "$SP/final_urls.txt"
echo "── 사라진 URL (반드시 0줄) ──"
comm -23 "$SP/baseline_urls.txt" "$SP/final_urls.txt"
echo "── 추가된 URL 수 ──"
comm -13 "$SP/baseline_urls.txt" "$SP/final_urls.txt" | wc -l
echo "── 추가된 것 중 en/ 으로 시작하지 않는 것 (반드시 0줄) ──"
comm -13 "$SP/baseline_urls.txt" "$SP/final_urls.txt" | grep -v '^en/' || echo "(없음)"
```

기대: 사라진 URL 0줄, 추가분은 전부 `en/` 접두사.

- [ ] **Step 3: 스펙 검증표 항목별 확인**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
P="$SP/public_final"

echo "[4] /en/ 홈 포스트 그리드 + 배너"
grep -c 'class="home-post-card"' "$P/en/index.html"
grep -c "English translations are in progress" "$P/en/index.html"

echo "[5] /en/posts/ 목록 + 페이저"
grep -c 'class="term-row"' "$P/en/posts/index.html"
test -d "$P/en/posts/page" && echo "페이저 OK" || echo "페이저 없음(1페이지이거나 후퇴안 적용)"

echo "[6] EN 허브 4종"
for p in about projects gallery kb-radar; do
  printf "  /en/%s/ %s\n" "$p" "$(test -f "$P/en/$p/index.html" && echo OK || echo FAIL)"
done

echo "[7] 토글 — ko 홈"
grep -o 'lang-switch.\{0,200\}' "$P/index.html" | head -1
echo "[7] 토글 — en 홈"
grep -o 'lang-switch.\{0,200\}' "$P/en/index.html" | head -1

echo "[7b] 토글 — /about/ ↔ /en/about/"
grep -o 'lang-switch.\{0,200\}' "$P/about/index.html" | head -1
grep -o 'lang-switch.\{0,200\}' "$P/en/about/index.html" | head -1

echo "[8] KB Radar EN 칩"
grep -o 'kbr-chip[^>]*>[^<]*' "$P/en/kb-radar/index.html"

echo "[10] goat 코드펜스 (반드시 0)"
grep -rl 'class="goat' "$P" | wc -l
```

기대:
- [4] 카드 수 > 0, 배너 1
- [5] 항목 수 > 0
- [6] 4개 전부 OK
- [7] ko 홈 → `/en/` + `English`, en 홈 → `/` + `한국어`
- **[7b] `/about/` → `/en/about/` 이고 `/en/` 이 아니어야 한다.** 여기가 홈으로 튕기면 Task 2 의 오버라이드가 동작하지 않은 것이다.
- [8] 칩이 `Papers`/`Articles`/`Videos`/`People`
- [10] 0

- [ ] **Step 4: [7c] 번역본 없는 페이지 폴백**

```bash
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
P="$SP/public_final"
POST=$(find "$P/posts" -name index.html | head -1)
grep -o 'lang-switch.\{0,200\}' "$POST" | head -1
```

기대: `/en/` (홈). 존재하지 않는 `/en/posts/...` 가 나오면 실패.

- [ ] **Step 5: [9] projects·gallery 육안 확인 (자동 검사로 대체 불가)**

```bash
cd /home/gjkong/skong097.github.io
"$HOME/bin/hugo" server --port 1313
```

브라우저에서 다음을 **직접 눈으로** 확인한다.

| URL | 확인 항목 |
|---|---|
| `/projects/` | 카드 8장, 강조색 테두리, 다크·라이트 양쪽 |
| `/gallery/` | 섹션 4개, 제목 배경색(#0F766E·#6B4FE0·#2563EB·#0E7C7B), 영상 재생 |
| `/en/projects/` | 동일 레이아웃, 영문 텍스트 |
| `/en/gallery/` | 동일 레이아웃·앵커, 영문 캡션 |
| `/kb-radar/` `/en/kb-radar/` | JS 콘솔 에러 0건, 카드 렌더, 필터·페이저 동작 |
| 헤더 토글 | `/about/` ↔ `/en/about/` 왕복 |

**콘솔 에러가 1건이라도 있으면 통과가 아니다.** Task 3 의 JS 문자열 연결 변경이 원인일 가능성이 높다.

- [ ] **Step 6: 결과 보고**

스펙 검증표 10개 항목 각각에 대해 통과/실패를 사용자에게 보고한다.
실패·미확인 항목이 있으면 **숨기지 말고 명시**한다. Task 4 Step 6 의 후퇴 방안을 적용했다면 그것도 함께 보고한다.

- [ ] **Step 7: 최종 커밋**

앞선 태스크에서 개별 커밋을 했다면 추가 커밋은 없다. 한꺼번에 커밋하려면:

```bash
git add hugo.yaml i18n/ layouts/ assets/css/extended/custom.css \
        content/about/index.en.md content/projects/_index.en.md \
        content/gallery/_index.en.md content/kb-radar/index.en.md \
        content/search.en.md content/projects/_index.md content/gallery/_index.md \
        CLAUDE.md docs/superpowers/
```

```bash
git commit -m "feat: 블로그 한/영 이중 언어 전환

- hugo.yaml 다국어 (ko 기본 / + en 서브패스 /en/)
- 헤더 KO↔EN 토글 (현재 페이지 번역본 우선, 없으면 홈 폴백)
- 커스텀 템플릿 문자열 24개를 i18n/{ko,en}.yaml 로 분리
- /en/posts/ 에 한국어 포스트 차용 노출 + 영문 안내 배너
- 영문 허브 페이지 5개 (About·Projects·Gallery·KB Radar·Search)
- projects/gallery 고유 CSS 를 custom.css 로 추출 (ko/en 공용)
- CLAUDE.md 에 새 포스트 한/영 쌍 작성 규칙 명문화

기존 한국어 URL 변경 0건 확인."
```

---

## 부록: 롤백

회귀 게이트가 실패하면 즉시 되돌린다.

```bash
cd /home/gjkong/skong097.github.io
git checkout -- hugo.yaml layouts/ content/ assets/ CLAUDE.md
rm -rf i18n/
rm -f content/about/index.en.md content/projects/_index.en.md \
      content/gallery/_index.en.md content/kb-radar/index.en.md content/search.en.md
```

주의: 위 `git checkout --` 은 `layouts/kb-radar/single.html` 의 **작업 시작 시점 미커밋 변경분까지 함께 날린다.** Task 0 Step 1 에서 만들어 둔 백업으로 복원한다.

```bash
cd /home/gjkong/skong097.github.io
SP=/tmp/claude-1000/-home-gjkong-skong097-github-io/e5bcc788-b593-47b6-8c24-b053c01bd287/scratchpad
git apply "$SP/pre_work.patch"
git diff --stat        # 원래의 미커밋 변경분이 돌아왔는지 확인
```
