# Hugo Blog 디자인 보완 작업 기록

> **날짜**: 2026-02-17 (오후)  
> **프로젝트**: Stephen's Robotics Lab (Hugo + PaperMod)  
> **저장소**: https://github.com/skong097/skong097.github.io  
> **이전 작업**: 블로그 초기 생성 + Dashboard 통합 + 라이트/다크 모드 + 콘텐츠 마이그레이션

---

## 1. 커버 이미지 생성 및 적용

### 1-1. 이미지 생성 (Python Pillow)

- 총 **13개** 커버 이미지 생성 (1200x630, OG 표준)
- 스타일: 테크/사이버 톤, 다크/라이트 모드 중립 색상
- 그래디언트 배경 + 그리드 + 회로 패턴 + 파티클 + 헥사곤 장식

| # | 파일명 | 용도 |
|---|--------|------|
| 1 | hero-banner.png | 홈페이지 히어로 (로봇 아이콘 + 중앙 글로우) |
| 2 | dashboard-banner.png | Dashboard (차트/그래프 시각화) |
| 3 | about-cover.png | About 페이지 (기술스택 뱃지) |
| 4 | projects-cover.png | Projects 페이지 (카드 추상화) |
| 5 | cover-computer-vision.png | CV 카테고리 (보라 accent) |
| 6 | cover-ros2.png | ROS2 카테고리 (초록 accent) |
| 7 | cover-robotics.png | Robotics 카테고리 (시안 accent) |
| 8 | cover-dev-tools.png | Dev Tools 카테고리 (오렌지 accent) |
| 9 | post-stgcn-finetuning.png | ST-GCN 포스트 (신경망 아이콘) |
| 10 | post-rf-vs-stgcn.png | RF vs ST-GCN 포스트 (VS 비교 아이콘) |
| 11 | post-pyqt6-dark-theme.png | PyQt6 포스트 (팔레트 아이콘) |
| 12 | post-kevin-patrol-fleet.png | Kevin Patrol 포스트 (로봇 플릿 아이콘) |
| 13 | post-ros2-guard-brain.png | ROS2 Guard Brain 포스트 (기어+화살표) |

### 1-2. 자동 배치 스크립트 (`setup_covers.py`)

- `covers/` → `static/images/covers/` 이미지 복사
- 포스트 5개 + About + Projects frontmatter에 `cover:` 자동 삽입
- `hugo.yaml`에 홈페이지 기본 커버 설정 추가

---

## 2. 홈페이지 커스텀 CSS

### 2-1. 파일 위치

- `assets/css/extended/custom.css` (PaperMod 자동 로드)

### 2-2. 적용 항목

- **홈 히어로**: 타이틀 시안→블루 그래디언트, 넉넉한 여백
- **소셜 아이콘**: 원형 배경 + hover 글로우 효과
- **네비게이션**: backdrop-filter 블러 + hover 하이라이트
- **코드 블록**: 둥근 모서리 + 인라인 코드 시안 강조
- **태그**: pill 스타일 + hover 애니메이션
- **TOC**: 카드형 디자인
- **Selection**: 시안/블루 하이라이트
- **라이트/다크 모드**: 다크=시안 accent, 라이트=블루 accent

---

## 3. 포스트 목록 반응형 그리드

### 3-1. 레이아웃 변경

- PaperMod 기본 세로 리스트 → **CSS Grid 카드 레이아웃**
- **컨테이너 확장**: PaperMod 기본 ~720px → `max-width: 1200px`

### 3-2. 반응형 breakpoints

| 화면 너비 | 열 수 |
|----------|-------|
| 1100px 이상 | 3열 |
| 580~1099px | 2열 |
| 579px 이하 | 1열 |

### 3-3. 카드 스타일

- 커버 이미지 16:9 비율 고정 + hover 시 scale(1.05)
- 제목 2줄 / 요약 2줄 텍스트 클램핑
- hover: translateY(-4px) + 시안 보더 글로우
- 히어로 카드, 페이지 헤더, 페이지네이션은 `grid-column: 1 / -1`

---

## 4. About 페이지 보완

### 4-1. 레이아웃 변경

- 마크다운 기본 → **HTML 카드 레이아웃** (hugo unsafe 렌더링)
- 컨테이너 `max-width: 1200px` 확장

### 4-2. 구성

- **히어로**: 중앙 정렬 이름 + 소개
- **기술 스택**: 5개 카테고리 카드 그리드 + 태그 뱃지
  - 넓은 화면 5열 → 중간 3열 → 모바일 2열 → 작은 화면 1열
- **프로젝트 목록**: 링크 카드 그리드 (hover 슬라이드 효과)
  - 넓은 화면 3열 → 중간 2열 → 모바일 1열
- **연락처**: GitHub/LinkedIn SVG 아이콘 버튼

---

## 5. Projects 페이지 보완

### 5-1. 레이아웃 변경

- 마크다운 구분선 리스트 → **카드 그리드 레이아웃**
- 컨테이너 `max-width: 1200px` 확장

### 5-2. 구성

- `auto-fill, minmax(340px, 1fr)` 반응형 그리드
- 각 카드: 상태 뱃지(Active/Done) + accent 상단 바 + hover 효과
- 프로젝트별 고유 `--card-accent` 색상 (시안/블루/보라/오렌지/초록/로즈)
- 기술 태그 + 링크(상세보기/GitHub) 분리

---

## 6. Dashboard 컨테이너 확장

- PaperMod 외부 컨테이너 → `width: 100%` 전체 해제
- 내부 요소(`dash-header-inner`, `dash-nav-tabs`, `dash-main`) → `max-width: 1400px` + `margin: 0 auto` 중앙 정렬 유지

---

## 7. CSS 통합 정리

### 7-1. 문제 해결

- v1 그리드(2열 고정)와 v2(반응형) 공존 → v2로 통합
- `.post-entry` 중복 선언 → 단일화
- 싱글 포스트 보호 규칙 누락 → `display: block` + `max-width: 800px` 추가
- Dashboard `margin: 0` → `margin: 0 auto` 중앙 정렬 수정

### 7-2. 최종 CSS 구조 (`custom.css`)

```
1. CSS Variables
2. Global Typography
3. Container Width (1200px)
4. Home Info (Hero)
5. Social Icons
6. Post List Grid (반응형 3/2/1열)
7. Post Card Styling + Hover + Light Mode
8. Single Post (800px 복원)
9. Navigation
10. Cover Images / Code Blocks / TOC / Tags / Pagination
11. Global Responsive
12. Page-Specific Overrides
    - Dashboard: 100% full-bleed
    - About: 1200px 확장
    - Projects: 1200px 확장
```

---

## 8. 현재 파일 구조 (업데이트)

```
~/dev_ws/blog/
├── hugo.yaml
├── data/roadmap_data.yaml
├── assets/
│   └── css/
│       └── extended/
│           └── custom.css              # 통합 커스텀 CSS
├── static/
│   └── images/
│       └── covers/                     # 커버 이미지 13개
├── content/
│   ├── dashboard/index.md
│   ├── posts/
│   │   ├── computer-vision/ (2개)
│   │   ├── dev-tools/ (1개)
│   │   ├── robotics/ (1개)
│   │   └── ros2/ (1개)
│   ├── projects/_index.md              # HTML 카드 레이아웃
│   ├── about/index.md                  # HTML 카드 레이아웃
│   └── search.md
├── layouts/dashboard/single.html
└── themes/PaperMod/
```

---

## 9. 다음 작업

- [ ] 개별 포스트 본문 스타일 보완
- [ ] Dashboard 배너 이미지 수동 적용 (`layouts/dashboard/single.html`)
- [ ] 포스트 5개 본문 완성 (현재 draft 골격 상태)
- [ ] 포스트 추가 5개 작성 (planned → draft)
- [ ] 10개 포스트 축적 완료 시 5개 공개
- [ ] GitHub 저장소 public 전환 + GitHub Pages 활성화
