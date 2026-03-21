---
title: "2026-02-18 작업일지 (Session 9: About 페이지 3D 엔티티 + 블로그 UI)"
date: 2026-03-21
draft: true
tags: ["dev-tools", "hugo"]
categories: ["dev-tools"]
description: "**작성일**: 2026-02-18 **세션**: Session 8 이후 추가 작업 - hugo.yaml: 'Dashboard' → '대시보드'"
---

# 2026-02-18 작업일지 (Session 9: About 페이지 3D 엔티티 + 블로그 UI)

**작성일**: 2026-02-18  
**세션**: Session 8 이후 추가 작업

---

## 1. 블로그 UI 개선

### 메뉴 한글화
- hugo.yaml: "Dashboard" → "대시보드"

### breadcrumbs 제거
- hugo.yaml: `ShowBreadCrumbs: false`
- extend_head.html에도 CSS/JS로 이중 보장 시도

### 페이지 제목 중앙 정렬 — 미해결 🔴
- custom.css에 `.post-title { text-align: center !important }` 추가
- extend_head.html에 JS `setProperty` 방식 시도
- PaperMod CSS 우선순위가 모든 시도를 override
- **다음 세션에서 single.html 직접 오버라이드 필요**

---

## 2. 블로그 3D 히어로 — 우주 배경 투명도 튜닝 ✅

**파일**: `layouts/partials/hero-3d.html`

### 투명도 최종값 (희미 → 강함 → 중간)

| 요소 | 최초 | 강화 | 최종 |
|------|------|------|------|
| 오로라 초록 | 0.12 | 0.3 | **0.2** |
| 태양 반사광 | 0.08 | 0.2 | **0.14** |
| 퍼플 네뷸러 | 0.1 | 0.25 | **0.18** |
| 딥블루 | 0.15 | 0.3 | **0.22** |
| 성운 파티클 | 0.08~0.14 | 0.15~0.25 | **0.1~0.18** |

---

## 3. About 페이지 — 3D 엔티티 통합 ✅

**파일**:
- `layouts/shortcodes/about-3d.html` (shortcode)
- `content/about/index.md` (About 콘텐츠)

### 구현 내용
- Claude(퍼플 다면체) + Gemini(골드 구체) 3D 씬을 About 페이지에 삽입
- 왼쪽 라벨: **STEPHEN KONG** + Robotics Engineer / AI Developer / Lifelong Learner
- 상단 타이틀: **About Me**
- Gemini 라벨 제거, BOTH/CLAUDE/GEMINI 모드 버튼 제거
- 우주 배경(오로라 + 별빛 + 성운) 포함
- 드래그 궤도 회전 + 스크롤 줌 인터랙션

### front matter 설정
```yaml
title: About
hideMeta: true          # "1 분 · Stephen Kong" 제거
ShowReadingTime: false
ShowPostNavLinks: false
author: ""
```

### 삽입 방식 변천
1. **Hugo partial** 시도 → about.md는 content 파일이라 partial 직접 호출 불가
2. **iframe** 시도 (`static/about-3d.html`) → iframe 안에서 3D 구체 렌더링 안 됨 (WebGL/크기 이슈)
3. **Hugo shortcode** 최종 채택 → `{{</* about-3d */>}}`로 직접 HTML/JS 삽입 → 성공

### 트러블슈팅
- Hugo 주석 `{{/*` 안에 `{{</*` 중첩 → 파싱 에러 → 주석 제거로 해결
- `hideMeta: true`가 안 먹히는 문제 → `content/about/index.md`가 아닌 `content/about.md`만 수정하고 있었음
- `about (Copy).md` 백업 파일이 충돌 → 삭제로 해결
- Hugo가 `about/index.md`를 `about.md`보다 우선 사용

---

## 최종 파일 구조

```
~/dev_ws/blog/
├── content/
│   └── about/
│       └── index.md              ← About 페이지 (3D shortcode 포함)
├── layouts/
│   ├── index.html                ← 홈: 3D 히어로 + 2열 포스트 그리드
│   ├── shortcodes/
│   │   └── about-3d.html         ← About 3D 엔티티 shortcode ✅
│   ├── partials/
│   │   ├── hero-3d.html          ← 홈 3D 히어로 (우주 배경)
│   │   └── extend_head.html      ← 스타일 주입 (제목 중앙정렬 미해결)
│   └── dashboard/
│       └── single.html           ← 대시보드 레이아웃
├── static/
│   └── about-3d.html             ← (iframe용, 현재 미사용)
├── assets/css/extended/
│   └── custom.css                ← 통합 커스텀 CSS
└── hugo.yaml                     ← 메뉴 한글화, breadcrumbs off
```

---

## 미해결 (다음 세션)

1. **페이지 제목 중앙 정렬** — PaperMod single.html 오버라이드 필요
2. **블로그 첫 포스트 작성** — 분류된 레퍼런스 활용
3. `static/about-3d.html` 정리 — shortcode로 전환했으므로 삭제 가능
