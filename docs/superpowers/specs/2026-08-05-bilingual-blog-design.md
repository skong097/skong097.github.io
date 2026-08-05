# 한/영 이중 언어 블로그 설계

작성일: 2026-08-05

## 목표

`https://skong097.github.io/` 를 한국어(기본) + 영어 이중 언어 사이트로 전환한다.
헤더에서 KO ↔ EN 토글이 가능해야 하고, **기존 한국어 URL은 하나도 바뀌지 않아야 한다.**
앞으로 작성하는 새 포스트는 한/영 두 벌로 만든다.

## 범위 결정 (확정)

| 항목 | 결정 |
|---|---|
| 번역 범위 | UI 문구 + 허브 페이지(About·Projects·Gallery·KB Radar·Search)만 |
| 기존 라이브 포스트 47편 | **번역하지 않음.** 한글 원문 유지 |
| `/en/posts/` | 한글 포스트를 그대로 목록에 노출 + 영문 안내 배너 |
| 향후 새 포스트 | 한/영 쌍으로 생성. 규칙은 `CLAUDE.md` 에 명문화 |
| projects/gallery 인라인 CSS | `assets/css/extended/custom.css` 로 추출해 중복 제거 |

번역하지 않기로 한 것: 드래프트 포스트 203편, 라이브 포스트 47편 본문(약 66,700단어),
포스트 내 SVG 다이어그램의 한글 라벨.

## 아키텍처

### 언어 배치

Hugo 네이티브 다국어(`languages` 블록)를 사용한다.

```
defaultContentLanguage: ko
defaultContentLanguageInSubdir: false
```

- **ko** — weight 1. `/`, `/posts/...`, `/about/` … (현행과 동일)
- **en** — weight 2. `/en/`, `/en/posts/...`, `/en/about/` …

언어 접미사가 없는 기존 `content/**/*.md` 260개는 Hugo 규칙에 따라 자동으로 `ko` 에
귀속된다. **파일명 변경 0건, 기존 URL 변경 0건.**

대안으로 검토했다가 탈락시킨 것:
- 별도 EN 저장소/사이트 — 콘텐츠·템플릿 이중 관리 비용
- JS 런타임 번역 — SEO 손실, 크롤러가 영문판을 인덱싱하지 못함

### 구성 요소

#### 1. `hugo.yaml` — 언어 블록

루트의 `languageCode: ko`, `title`, `params.description`, `params.homeInfoParams`,
`menu.main` 을 `languages.ko` / `languages.en` 아래로 분리한다.

언어와 무관한 설정(`baseURL`, `theme`, `outputs`, `ignoreFiles`, `markup`,
`params.fuseOpts`, `params.assets`, `params.cover`, `params.socialIcons`,
불리언 표시 옵션들)은 루트에 그대로 둔다.

`en` 메뉴 항목: Home / Projects / Gallery / Posts / KB Radar / Categories / Search / About me
(weight 는 ko 와 동일하게 유지해 순서 일치)

#### 2. 언어 토글 (필수 요구사항)

헤더에 KO ↔ EN 전환 버튼을 **반드시** 넣는다.

**조사 결과 (확인 완료)**: PaperMod `layouts/partials/header.html` 에 언어 스위처가
내장돼 있다. `.logo-switches` 안, 다크모드 토글 옆에 `ul.lang-switch` 로 렌더되고
`site.Params.disableLangToggle` 로 꺼진다. 테마 `i18n/ko.yaml`·`en.yaml` 도 이미
있어 "Search"·"Read Time" 등 테마 자체 문구는 자동으로 번역된다.

**그대로 쓰지 않는 이유**: 내장 스위처의 링크가 `site.Home.Translations` 라서
**어느 페이지에서 눌러도 상대 언어의 홈으로 이동**한다. `/en/about/` 에서 KO 를
누르면 `/about/` 이 아니라 `/` 로 간다.

**구현**: `layouts/partials/header.html` 오버라이드 (테마 파일 복사 후 `lang-switch`
블록만 수정). 링크 결정 우선순위:

1. 현재 페이지에 상대 언어 번역본이 있으면 → 그 페이지 (`.Translations`)
2. 없으면 → 상대 언어 홈 (`site.Home.Translations`)

기존 47편 한글 포스트에는 EN 번역본이 없으므로 2번으로 폴백한다. 향후 한/영 쌍으로
작성한 포스트는 1번이 걸려 같은 글의 반대 언어판으로 바로 넘어간다.

표기는 `params.displayFullLangName: true` 를 켜서 "Ko"/"En" 대신
**"한국어" / "English"** 로 보이게 한다.

오버라이드 범위는 `lang-switch` 블록 한 곳으로 제한한다. 로고·다크모드 토글·메뉴
루프는 테마 원본 그대로 복사만 하고 손대지 않는다.

#### 3. `/en/posts/` 에 한글 포스트 노출

Hugo 는 언어별로 콘텐츠를 격리하므로 그냥 두면 `/en/posts/` 가 빈 목록이 된다.
두 템플릿에 분기를 넣어 EN 사이트에서 ko 페이지를 빌려온다.

- `layouts/_default/list.html` (터미널 스타일 목록)
- `layouts/index.html` (홈 2열 포스트 그리드)

분기 조건: 현재 언어가 `en` 이고, 해당 컬렉션에 자기 언어 페이지가 없을 때
`site.Sites` 에서 `ko` 사이트를 찾아 그쪽 페이지 컬렉션으로 대체한다.

목록 상단에 EN 일 때만 안내 배너를 출력한다 (i18n 키 `koPostsNotice`):
> Posts are currently written in Korean. English translations are in progress.

**알려진 리스크**: 교차 사이트 페이지 컬렉션에 `.Paginate` 를 거는 부분.
문법상 허용되지만 Hugo 0.146 에서 실제 렌더로 확인해야 한다. 페이지네이션이
깨지면 EN 목록에 한해 `first N` 로 잘라 페이지네이션 없이 출력하는 것으로 후퇴한다.

부가 효과: EN 목록의 각 포스트 링크는 ko 퍼멀링크(`/posts/...`)를 가리키므로
클릭하면 한국어 사이트로 이동한다. 의도된 동작이다.

#### 4. UI 문구 i18n

`i18n/ko.yaml` + `i18n/en.yaml` 을 신설하고, **화면에 실제로 보이는** 하드코딩
한글만 `{{ i18n "key" }}` 로 교체한다.

| 파일 | 교체 대상 |
|---|---|
| `layouts/kb-radar/single.html` | 칩 4종(논문·기사·영상·인물), 아카이브 칩, 검색 placeholder, 서브타이틀, 푸터, JS 의 `CAT_LABEL`·페이저 버튼·빈 상태 메시지 2종·"(제목 없음)" — 약 15개 |
| `layouts/partials/hero-3d.html`<br>`layouts/partials/hero-3d_dark.html` | 히어로 설명문 2줄. 추가로 하드코딩된 `/posts/`·`/kb-radar/` 링크를 `relLangURL` 처리 |
| `layouts/shortcodes/about-3d.html` | 플로팅 문구 2줄, 이름("공국진" → "Stephen Kong"), 소개 3줄 — 6개 |
| `layouts/shortcodes/github-graph.html` | SVG `aria-label`, 빈 상태 문구, "GitHub 프로필" — 3개 |

`layouts/index.html`, `layouts/_default/list.html`, `layouts/partials/extend_head.html`
의 한글은 **전부 주석**이므로 건드리지 않는다 (확인 완료).

#### 5. EN 콘텐츠 파일 (신규 5개)

- `content/about/index.en.md`
- `content/projects/_index.en.md`
- `content/gallery/_index.en.md`
- `content/kb-radar/index.en.md`
- `content/search.en.md`

front matter 는 대응하는 ko 파일과 동일한 구조를 쓰되 `title` 만 영문화한다.
`url:` 필드는 ko 파일에만 두고 en 파일에서는 뺀다 (Hugo 가 `/en/` 접두사를 붙이도록).

#### 6. 인라인 CSS 추출

`content/projects/_index.md` 와 `content/gallery/_index.md` 의 `<style>` 블록을
`assets/css/extended/custom.css` 로 옮긴다. PaperMod 가 이 파일을 자동 포함한다.

- 셀렉터는 그대로 옮긴다. 이름을 바꾸거나 정리하지 않는다.
- 두 파일의 셀렉터가 충돌하면 페이지 스코프 클래스로 감싸되, 충돌이 없으면 그대로 둔다.
- 옮긴 뒤 ko 페이지 두 개의 렌더 결과를 **눈으로 확인**한다 (스크린샷 또는 로컬 브라우저).

이 작업의 목적은 "번역 때문에 생기는 CSS 2벌 유지"를 제거하는 것이다.
목적 범위 밖의 CSS 정리·리팩터링은 하지 않는다.

#### 7. `CLAUDE.md` — 향후 포스트 규칙

새 섹션 "포스트는 한/영 두 벌로 작성한다" 를 추가한다.

- 파일명: `<english-slug>.md` (ko) + `<english-slug>.en.md` (en) 쌍
- ko 파일 front matter 에 `slug: <한글-슬러그>` 를 넣어 기존 한글 URL 관례를 유지
- en 파일은 `slug` 없이 영문 basename 을 그대로 URL 로 사용
- 같은 basename 이므로 Hugo 가 번역 링크를 자동 연결한다 (`translationKey` 불필요)
- `date`·`categories`·`tags` 는 두 파일이 동일해야 한다
- SVG 다이어그램: 라벨이 한글이면 `<name>-en.svg` 를 따로 만들어 en 파일에서 참조.
  라벨이 영문·기호뿐이면 같은 SVG 를 공유한다.
- 기존 47편 소급 번역은 하지 않는다

## 영향 범위

| 바뀌는 것 | 안 바뀌는 것 |
|---|---|
| `hugo.yaml` 구조 (언어별 분리) | 기존 한국어 URL 전부 |
| 신규: `layouts/partials/header.html` 오버라이드 | 테마 서브모듈 커밋 해시 |
| 커스텀 템플릿 4개의 문자열 → i18n | 포스트 본문 260개 |
| projects/gallery 의 `<style>` 위치 | 포스트 파일명·front matter |
| `custom.css` 에 규칙 추가 | CI 워크플로 |
| 신규: `i18n/*.yaml`, EN 콘텐츠 5개 | `blog_publish.py`, `collect_blog_refs.py` |

## 검증

로컬 검증 환경을 먼저 갖춘다.

1. ~~`git submodule update --init --recursive`~~ — **완료** (2026-08-05, `3bb0ca2` 체크아웃됨)
2. Hugo **0.146.0 extended** 설치 (CI 와 동일 버전) — 미완료

그다음 순서대로 확인한다.

| # | 확인 항목 | 통과 기준 |
|---|---|---|
| 1 | 변경 전 baseline URL 목록 확보 | `public/` 의 `index.html` 경로 전체를 파일로 저장 |
| 2 | `hugo --gc --minify` | WARN 0건, ERROR 0건 |
| 3 | **기존 한국어 URL 회귀** | baseline 대비 삭제·변경된 URL **0건** (신규 `/en/*` 추가만 허용) |
| 4 | `/en/` 홈 | 포스트 그리드에 47편 노출, 안내 배너 표시 |
| 5 | `/en/posts/` | 목록 47편 + 페이지네이션 동작 + 안내 배너 |
| 6 | `/en/about/` `/en/projects/` `/en/gallery/` `/en/kb-radar/` | 각 페이지 렌더, 한글 UI 문구 잔존 0건 |
| 7 | 언어 토글 표시 | 모든 페이지 헤더에 "English"/"한국어" 링크 렌더 |
| 7b | 토글 동작 — 번역본 있음 | `/about/` ↔ `/en/about/` 상호 이동 (홈으로 튕기지 않을 것) |
| 7c | 토글 동작 — 번역본 없음 | 한글 포스트에서 토글 → `/en/` 홈으로 폴백 (404 아님) |
| 8 | KB Radar EN | 칩·검색·페이저 영문, 항목 데이터는 양쪽 동일 |
| 9 | projects·gallery ko 페이지 | CSS 추출 후 렌더 깨짐 없음 (육안 확인) |
| 10 | 코드펜스 | `class="goat` 0건 (기존 규칙 유지) |

3번이 가장 중요하다. 실패하면 즉시 롤백한다.

## 하지 않는 것

- 기존 포스트 47편 본문 번역
- 드래프트 203편 관련 작업
- SVG 다이어그램 영문판 제작 (향후 새 포스트에만 적용)
- `blog_publish.py` / `collect_blog_refs.py` 수정
- 목적 범위 밖의 CSS·템플릿 리팩터링
