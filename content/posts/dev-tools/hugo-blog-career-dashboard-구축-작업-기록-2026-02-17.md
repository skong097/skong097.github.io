---
title: "Hugo Blog + Career Dashboard 구축 작업 기록"
date: 2026-03-21
draft: true
tags: ["dev-tools", "pyqt6", "hugo"]
categories: ["dev-tools"]
description: "> **날짜**: 2026-02-17 > **프로젝트**: Stephen's Robotics Lab (Hugo + PaperMod + Career Dashboard) > **저장소**: https://github.c"
---

# Hugo Blog + Career Dashboard 구축 작업 기록

> **날짜**: 2026-02-17  
> **프로젝트**: Stephen's Robotics Lab (Hugo + PaperMod + Career Dashboard)  
> **저장소**: https://github.com/skong097/skong097.github.io

---

## 1. Hugo 블로그 초기 생성

- Hugo + PaperMod 테마로 블로그 프로젝트 생성
- 프로젝트 경로: `~/dev_ws/blog/`
- `hugo server -D`로 로컬 서버 구동 확인
- 기본 홈페이지 렌더링 확인 (라이트/다크 토글 정상)

---

## 2. Career Dashboard 통합

### 2-1. Hugo 레이아웃 구조 설정

- `layouts/dashboard/single.html` — 대시보드 전용 레이아웃 생성
- `content/dashboard/index.md` — 대시보드 콘텐츠 페이지 (frontmatter: type=dashboard)
- `data/roadmap_data.yaml` — 대시보드 데이터 소스 (12 도메인, 10 프로젝트, 10 블로그, 8 학습로그)

### 2-2. 데이터 연동 이슈 해결

- **문제**: `{{ $data | jsonify }}`가 JSON 객체가 아닌 문자열로 이중 인코딩됨
- **원인**: Hugo의 jsonify가 YAML 데이터를 문자열로 감싸서 출력
- **해결**: `const DATA = JSON.parse({{ $data | jsonify }});`로 수정
- 브라우저 콘솔에서 `DATA` 객체 정상 로드 확인

### 2-3. 대시보드 렌더링 확인

- Overview: 요약 카드 4개 + Skill Radar(SVG) + Project Status 리스트
- Tech Domains: 12개 도메인 카드 그리드 + 스킬별 프로그레스 바
- Projects: 10개 프로젝트 카드 + 필터(All/Done/Active/Planned)
- Blog: 요약 바(Draft/Ready/Published/Planned) + 포스트 카드
- Learning: 히트맵(4주) + 영역별 학습 시간

---

## 3. 라이트/다크 모드 지원

### 3-1. 문제

- 대시보드 CSS가 다크 색상으로 하드코딩되어 PaperMod의 라이트/다크 토글이 적용되지 않음
- 블로그 다른 페이지는 정상 전환되지만 Dashboard만 항상 다크 모드

### 3-2. 해결

- CSS 변수를 라이트 모드(기본)와 다크 모드(`[data-theme="dark"]`)로 이중 정의
- 라이트 모드: 밝은 배경(#f0f2f5) + 진한 accent 색상
- 다크 모드: 기존 디자인 유지(#0a0e17 배경 + 네온 accent)
- `MutationObserver`로 `data-theme` 속성 변경 감지 → 레이더 차트/도메인 색상 자동 재렌더링
- 도메인 색상을 `DOMAIN_COLORS`(다크)와 `DOMAIN_COLORS_LIGHT`(라이트) 이중 관리

### 3-3. 이모지 제거

- 탭 메뉴, 헤더, 카드 타이틀, 상태 표시, 블로그 메타 등 모든 이모지를 텍스트/기호로 대체
- 체크마크: `[v]` / `[ ]`, 상태 도트: `[v]` / `[~]` / `[o]`

---

## 4. 이전 블로그 콘텐츠 마이그레이션

### 4-1. 이전 블로그 (blog_old) 콘텐츠

| 파일 | 카테고리 | 제목 |
|------|----------|------|
| stgcn-finetuning-fall-detection.md | computer-vision | ST-GCN 파인튜닝으로 낙상감지 91.89% 달성기 |
| rf-vs-stgcn-fall-detection.md | computer-vision | RF vs ST-GCN 낙상감지 모델 비교 실전 가이드 |
| pyqt6-dark-theme-system.md | dev-tools | PyQt6에서 3테마 다크 시스템 구축하기 |
| kevin-patrol-fleet-dashboard.md | robotics | 다중 로봇 플릿 모니터링 대시보드 만들기 |
| ros2-guard-brain-fastapi.md | ros2 | ROS2 Jazzy + FastAPI로 Guard Brain 만들기 |

### 4-2. 추가 페이지 마이그레이션

- `content/about/index.md` — About 페이지 (기술 스택, 주요 프로젝트, 연락처)
- `content/projects/_index.md` — 프로젝트 목록 페이지 (6개 프로젝트 소개)
- `content/search.md` — 검색 페이지

### 4-3. hugo.yaml 업데이트

- 사이트 타이틀: "Stephen's Robotics Lab"
- 메뉴 구성: 홈 / 프로젝트 / 포스트 / **Dashboard** / 카테고리 / 태그 / 검색 / About
- Dashboard 메뉴 유지 (`/dashboard/` → weight: 25)
- 홈 정보: "Robotics × AI × ROS2" + 블로그 소개 문구
- 소셜: GitHub + LinkedIn

### 4-4. roadmap_data.yaml 동기화

- 블로그 포스트 상태를 실제 파일과 동기화
  - draft 5개: 실제 .md 파일이 존재하는 포스트
  - planned 5개: 아직 파일 미생성 포스트
- 각 포스트에 url 필드 추가 (파일 경로와 매핑)

---

## 5. 현재 프로젝트 파일 구조

```
~/dev_ws/blog/
├── hugo.yaml                          # 사이트 설정
├── data/
│   └── roadmap_data.yaml              # 대시보드 데이터
├── content/
│   ├── dashboard/
│   │   └── index.md                   # 대시보드 페이지
│   ├── posts/
│   │   ├── computer-vision/
│   │   │   ├── stgcn-finetuning-fall-detection.md
│   │   │   └── rf-vs-stgcn-fall-detection.md
│   │   ├── dev-tools/
│   │   │   └── pyqt6-dark-theme-system.md
│   │   ├── robotics/
│   │   │   └── kevin-patrol-fleet-dashboard.md
│   │   └── ros2/
│   │       └── ros2-guard-brain-fastapi.md
│   ├── projects/
│   │   └── _index.md
│   ├── about/
│   │   └── index.md
│   └── search.md
├── layouts/
│   └── dashboard/
│       └── single.html                # 대시보드 레이아웃 (라이트/다크)
├── themes/PaperMod/
├── static/
└── .github/
    └── workflows/
        └── hugo.yml                   # GitHub Actions 자동 배포
```

---

## 6. 배포 정보

- **로컬 미리보기**: `hugo server -D` → http://localhost:1313/
- **대시보드**: http://localhost:1313/dashboard/
- **GitHub Pages (배포 후)**: https://skong097.github.io/
- **배포 방식**: GitHub Actions 자동 빌드 (push → build → deploy)

---

## 7. 다음 작업

- [ ] 포스트 5개 본문 완성 (현재 draft + 골격만 있는 상태)
- [ ] 포스트 추가 5개 작성 (planned → draft)
- [ ] 커버 이미지 생성 및 `static/images/` 배치
- [ ] 10개 포스트 축적 완료 시 5개 공개 (draft: false)
- [ ] GitHub 저장소 public 전환 + GitHub Pages 활성화
- [ ] ROS2 수업 진행에 따라 roadmap_data.yaml 숙련도 업데이트
