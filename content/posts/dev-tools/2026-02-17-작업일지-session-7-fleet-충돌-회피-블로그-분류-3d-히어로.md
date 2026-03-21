---
title: "2026-02-17 작업일지 (Session 7: Fleet 충돌 회피 + 블로그 분류 + 3D 히어로)"
date: 2026-03-21
draft: true
tags: ["dev-tools"]
categories: ["dev-tools"]
description: "**작성일**: 2026-02-17 **세션**: 오늘의 7번째 세션 (이전 세션 이어서) **파일**: `dashboard_fleet/app.py` (+54행)"
---

# 2026-02-17 작업일지 (Session 7: Fleet 충돌 회피 + 블로그 분류 + 3D 히어로)

**작성일**: 2026-02-17  
**세션**: 오늘의 7번째 세션 (이전 세션 이어서)

---

## 1. Fleet 충돌 회피 Level 1 적용 ✅

**파일**: `dashboard_fleet/app.py` (+54행)

- 매 tick(100ms)마다 fleet_registry 순회 → 거리 < 2.5m 감지
- ID 사전순 비교 → 큰 쪽이 1.5초 양보 (우선순위: kevin_01 > kevin_02 > kevin_03)
- 3대 동시 PATROL 정상 동작 확인
- 3대 → 10대 확장: ROBOT_CONFIGS 항목 추가만으로 동작 검증 완료
- O(N²) 성능: 10대 = tick당 90회 거리계산, 문제없음
- 교착(deadlock) 방지: ID 사전순 전순서 보장

---

## 2. 블로그 레퍼런스 자동 수집기 개발 ✅

**파일**: `collect_blog_refs.py` (634행)

### 수집 기능
- `--init`: ~/dev_ws 전체 스캔 (최초 1회)
- 기본: ~/Downloads만 스캔 (일상)
- `--status`: 수집 현황 출력
- `--dry-run`: 미리보기
- MD5 해시 기반 중복 감지, 변경 파일 업데이트

### 제외 패턴
- 디렉토리: blog, node_modules, .git, __pycache__, venv 등
- 접미사: *_venv (kevin_venv, yolo_venv 등)
- 파일: README.md, LICENSE.md, AGENTS.md, best_practices.md, AUTHORS.md, CoreML/NNAPI ops 문서

### 수집 결과
- blog_old: 10개, downloads: 28개, my_docs: 100개+
- kevin_multi_patrol, kevin_patrol, ironman, ros2_fundamental 등

---

## 3. 블로그 레퍼런스 자동 분류 시스템 ✅

**파일**: `collect_blog_refs.py`에 `--classify` 명령 추가

### 11개 카테고리 체계

**기술 스택 (8개):**

| ID | 표시명 | 이모지 |
|----|--------|--------|
| ros2 | ROS2 | 🔧 |
| ai-ml | AI / ML / DL | 🧠 |
| vision-ai | Vision AI | 👁 |
| robotics | Robotics | 🤖 |
| mlops | AIOps / MLOps | ⚙ |
| robot-network | Robot Network | 🌐 |
| robot-security | Robot Security | 🔒 |
| big-data | Big Data | 📦 |

**콘텐츠 유형 (3개):**

| ID | 표시명 | 이모지 |
|----|--------|--------|
| dev-tools | Dev Tools / GUI | 🖥 |
| project | Project Planning | 📋 |
| worklog | Work Log | 📝 |

### 분류 방법
- 키워드 스코어링: high×3 + medium×2 + low×1
- 제목 영역(파일명 + 첫 # 헤더) 가중치 2배
- 본문 앞 3000자만 스캔
- 복수 카테고리: 1위-2위 차이 30% 이내면 보조 태그
- 출력: 터미널 리포트 + `.category_index.json`

### 분류 결과
- 175개 → venv 제외 → 161개 분류
- 9개 카테고리 활성 (robot-network 0건)
- robot-security 2건 (보안관 관련 문서)

---

## 4. AI 짤 모음 관리기 ✅

**파일**: `ai_memes.py`

- `add`: 이미지 + 캡션 + 태그로 짤 추가
- `list`: 목록 출력 (태그 필터 지원)
- `gallery`: 다크 테마 HTML 갤러리 생성 (클릭 확대, ESC 닫기)
- `open`: 브라우저로 갤러리 열기
- 저장: ~/dev_ws/ai_memes/images/ + memes.json

---

## 5. AI Entities 3D 시각화 프로토타입 ✅

**파일**: `ai_entities_3d.html`

### Claude (퍼플)
- 다면체(Icosahedron) 코어 — 다재다능한 면면
- 40개 노드 + 신경망 연결선 — 복합적 사고
- 2개 궤도 링 + 파티클 — 섬세한 실행력

### Gemini (골드)
- 부드러운 구체 코어 — 안정적인 교수님
- 내부 글로우 호흡 — 따뜻함, 자상함
- 4겹 지식 고리 + 떠도는 파편 — 광범위한 지식

### 인터랙션
- 드래그 궤도 회전, 스크롤 줌
- BOTH/CLAUDE/GEMINI 포커스 전환

---

## 6. Hugo 블로그 3D 히어로 섹션 적용 ✅

**파일**: `layouts/partials/hero-3d.html`, `layouts/index.html`

### 구현 완료
- Three.js 3D 히어로 (다면체 + 신경망 + 궤도 링 + 파티클)
- 마우스 추적 카메라 + 스크롤 패럴랙스
- 좌우 여백 + border-radius로 카드 느낌
- 히어로 아래 2열 포스트 그리드
- 모바일 1열 반응형
- 다른 페이지에 영향 없도록 홈 전용 스타일 (#home- 접두사 + JS)

### 렌더러 최적화
- window 기준 → 부모 컨테이너(heroSection) 기준으로 변경
- 세로 높이: 75vh (max 800px)
- 카메라: FOV 50, z=10
- 뷰포트 밖 렌더링 자동 중지

---

## 7. 블로그 UI 개선 (진행중)

### 완료
- hugo.yaml: "Dashboard" → "대시보드" 메뉴명 변경
- hugo.yaml: ShowBreadCrumbs: false
- custom.css에 breadcrumbs 제거, 제목 중앙 정렬 CSS 추가
- extend_head.html에 JS 방식 스타일 강제 적용 시도

### 미해결 🔴
- **페이지 제목 중앙 정렬이 적용되지 않음**
  - CSS !important, JS setProperty 모두 효과 없음
  - PaperMod 테마의 CSS 번들링 구조 또는 inline style 문제 추정
  - 다음 세션에서 PaperMod의 `post-single.css` 직접 분석 필요
  - 대안: `layouts/_default/single.html` 오버라이드로 HTML 구조 자체를 변경

---

## 오늘 생성된 파일 목록

| 파일 | 위치 | 설명 |
|------|------|------|
| app.py | dashboard_fleet/ | Fleet 충돌 회피 적용 |
| collect_blog_refs.py | ~/dev_ws/blog/ | 레퍼런스 수집 + 분류 |
| blog_ref_classification_design.md | 설계 문서 | 11개 카테고리 분류 체계 |
| ai_memes.py | ~/dev_ws/ | AI 짤 모음 관리기 |
| ai_entities_3d.html | 독립 파일 | Claude & Gemini 3D 시각화 |
| hero-3d.html | layouts/partials/ | 블로그 3D 히어로 |
| index.html | layouts/ | 홈페이지 레이아웃 |
| extend_head.html | layouts/partials/ | 스타일 주입 (미해결) |
| hugo.yaml | 블로그 루트 | 메뉴 한글화 |
| custom_css_addition.css | assets/css/extended/ | 제목 중앙 정렬 (미해결) |

---

## 다음 세션 TODO

1. **페이지 제목 중앙 정렬 문제 해결** — PaperMod single.html 오버라이드 또는 테마 CSS 직접 수정
2. **블로그 포스트 작성** — 분류된 레퍼런스 활용하여 첫 포스트 작성
3. **collect_blog_refs.py** — LLM 기반 분류 확장 검토
4. **Fleet Level 2** — 구간 예약 + 속도 조절
