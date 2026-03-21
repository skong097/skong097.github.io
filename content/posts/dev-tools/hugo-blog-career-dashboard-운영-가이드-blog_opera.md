---
title: "Hugo Blog + Career Dashboard — 운영 가이드"
date: 2026-03-21
draft: true
tags: ["dev-tools", "hugo"]
categories: ["dev-tools"]
description: "> **블로그**: ~/dev_ws/blog (Hugo + PaperMod) > **대시보드 데이터**: data/roadmap_data.yaml > **배포**: GitHub Pages (GitHub Actions"
---

# Hugo Blog + Career Dashboard — 운영 가이드

> **블로그**: ~/dev_ws/blog (Hugo + PaperMod)  
> **대시보드 데이터**: data/roadmap_data.yaml  
> **배포**: GitHub Pages (GitHub Actions 자동 빌드)

---

## 1. 프로젝트 구조

```
~/dev_ws/blog/
├── hugo.yaml                          # Hugo 설정 (메뉴, 테마, 사이트 정보)
├── data/
│   └── roadmap_data.yaml              # ★ 대시보드 데이터 (이 파일만 수정)
├── content/
│   ├── dashboard/
│   │   └── index.md                   # 대시보드 페이지 (frontmatter만)
│   ├── posts/                         # 블로그 포스트
│   │   ├── ros2/
│   │   ├── computer-vision/
│   │   ├── robotics/
│   │   ├── ai-ml/
│   │   └── dev-tools/
│   ├── projects/                      # 프로젝트 페이지
│   └── about/                         # 소개 페이지
├── layouts/
│   └── dashboard/
│       └── single.html                # 대시보드 렌더링 레이아웃
├── static/                            # 이미지, CSS 등 정적 파일
├── themes/PaperMod/                   # 테마 (수정 금지)
└── .github/
    └── workflows/
        └── hugo.yml                   # GitHub Actions 자동 배포
```

---

## 2. 대시보드 데이터 업데이트 방법

`data/roadmap_data.yaml` 파일을 텍스트 에디터(VSCode)로 열어서 수정합니다.

### 2-1. 기술 영역 숙련도 변경

```yaml
domains:
  - id: ros2
    name: "ROS2 / Navigation"
    icon: "🤖"
    proficiency: 55        # ← 현재 숙련도 (0-100)
    learning_target: 80    # ← 목표 숙련도
    skills:
      - { name: "ROS2 Core", level: 65 }   # ← 개별 스킬 레벨
      - { name: "Nav2 / SLAM", level: 45 }
```

**수정 예시**: ROS2 수업 완료 후 숙련도 업데이트

```yaml
    proficiency: 65        # 55 → 65로 변경
    skills:
      - { name: "ROS2 Core", level: 80 }   # 65 → 80
      - { name: "Nav2 / SLAM", level: 55 }  # 45 → 55
```

### 2-2. 프로젝트 진행 상태 변경

```yaml
projects:
  - id: proj_02
    name: "Kevin Patrol Dashboard"
    status: active         # done / active / planned
    progress: 85           # 진행률 (0-100)
    milestones:
      - { name: "Single v3.2.1", done: true }
      - { name: "실제 맵 로드", done: false }  # ← false → true로 변경
```

**수정 예시**: 마일스톤 완료 + 진행률 갱신

```yaml
    progress: 90           # 85 → 90
    milestones:
      - { name: "실제 맵 로드", done: true }   # false → true
```

### 2-3. 블로그 포스트 상태 변경

```yaml
blog_posts:
  - title: "ST-GCN으로 낙상감지 91.89% 달성하기"
    project: proj_03
    status: draft          # draft → ready → published
    domain: ai_ml
```

**상태 흐름**: `planned` → `draft` → `ready` → `published`

### 2-4. 학습 로그 추가

```yaml
learning_log:
  # 기존 항목들...
  - { date: "2026-02-18", topic: "ROS2 수업 Day 1", domain: ros2, hours: 6 }
  - { date: "2026-02-19", topic: "Nav2 실습", domain: ros2, hours: 4 }
```

### 2-5. 새 프로젝트 추가

```yaml
projects:
  # 기존 프로젝트들...
  - id: proj_11
    name: "새 프로젝트 이름"
    number: 11
    status: planned
    progress: 0
    domains: [ros2, ai_ml]          # 연관 기술 영역 ID
    description: "프로젝트 설명"
    github: ""
    milestones:
      - { name: "Phase 1", done: false }
      - { name: "Phase 2", done: false }
```

### 2-6. 새 기술 영역 추가

```yaml
domains:
  # 기존 영역들...
  - id: new_domain                   # 고유 ID (영문 소문자)
    name: "영역 이름"
    icon: "🆕"
    proficiency: 0
    learning_target: 50
    skills:
      - { name: "스킬1", level: 0 }
      - { name: "스킬2", level: 0 }
```

---

## 3. 블로그 포스트 작성

### 3-1. 새 포스트 생성

```bash
cd ~/dev_ws/blog

# 카테고리별 포스트 생성
hugo new posts/ros2/새-포스트-제목.md
hugo new posts/ai-ml/새-포스트-제목.md
hugo new posts/computer-vision/새-포스트-제목.md
hugo new posts/robotics/새-포스트-제목.md
hugo new posts/dev-tools/새-포스트-제목.md
```

### 3-2. 포스트 frontmatter

```yaml
---
title: "포스트 제목"
date: 2026-02-18
draft: true                # true: 비공개, false: 공개
tags: ["ros2", "robotics", "dashboard"]
categories: ["ros2"]
description: "포스트 요약"
---

본문 내용 (Markdown)
```

### 3-3. 비공개 → 공개 전환

포스트 공개 시 `draft: true` → `draft: false`로 변경

```yaml
draft: false               # 이것만 바꾸면 공개
```

---

## 4. 로컬 미리보기

```bash
cd ~/dev_ws/blog

# draft 포함 미리보기 (개발용)
hugo server -D

# draft 제외 미리보기 (배포 상태 확인)
hugo server
```

브라우저에서 확인:
- 블로그 홈: http://localhost:1313/
- 대시보드: http://localhost:1313/dashboard/
- 포스트 목록: http://localhost:1313/posts/

---

## 5. GitHub 배포

### 5-1. 최초 1회 — 저장소 설정

```bash
cd ~/dev_ws/blog

# Git 초기화 (이미 했으면 생략)
git init

# GitHub 저장소 연결 (private 권장)
git remote add origin https://github.com/skong097/skong097.github.io.git

# 첫 커밋 + 푸시
git add .
git commit -m "initial blog + career dashboard setup"
git branch -M main
git push -u origin main
```

### 5-2. GitHub Pages 활성화

1. GitHub 저장소 → **Settings** → **Pages**
2. Source → **GitHub Actions** 선택
3. `.github/workflows/hugo.yml`이 자동으로 감지됨
4. 첫 빌드 후 `https://skong097.github.io/` 에서 확인

### 5-3. 일상적인 업데이트 → 배포 흐름

```bash
cd ~/dev_ws/blog

# 1. 데이터 수정 (YAML 편집)
code data/roadmap_data.yaml

# 2. 로컬 미리보기로 확인
hugo server -D
# 브라우저에서 http://localhost:1313/dashboard/ 확인
# Ctrl+C로 종료

# 3. 변경 커밋
git add .
git commit -m "update: 대시보드 숙련도 업데이트 / ROS2 학습 로그 추가"

# 4. 푸시 → 자동 배포
git push
```

push하면 GitHub Actions가 자동으로 Hugo 빌드 → GitHub Pages 배포합니다.
보통 1-2분 내에 반영됩니다.

---

## 6. 커밋 메시지 컨벤션

일관된 커밋 메시지를 위한 권장 포맷:

```bash
# 대시보드 데이터 업데이트
git commit -m "dashboard: ROS2 숙련도 65% 갱신"
git commit -m "dashboard: proj_02 Fleet v3.3 마일스톤 완료"
git commit -m "dashboard: 학습 로그 2/18-2/20 추가"

# 블로그 포스트
git commit -m "post: ST-GCN 낙상감지 포스트 초안 작성"
git commit -m "publish: PyQt6 대시보드 포스트 공개"

# 설정 변경
git commit -m "config: 메뉴에 Projects 페이지 추가"
git commit -m "style: 대시보드 모바일 레이아웃 개선"
```

---

## 7. 블로그 공개 전략

로드맵 기준 "10개 축적 → 5개 공개 + 매주 추가" 전략:

```
[Phase 1: 축적] — private repo + draft: true
  ├── 포스트 10개 작성 (draft: true)
  ├── 대시보드 데이터 완성
  └── 로컬에서 최종 확인

[Phase 2: 공개 전환]
  ├── 저장소 public 전환 (또는 유지)
  ├── 5개 포스트 draft: false
  └── git push → 자동 배포

[Phase 3: 운영] — 매주 반복
  ├── 월: YAML 데이터 업데이트 (학습 로그, 프로젝트 진척)
  ├── 수: 신규 포스트 1개 작성 (draft: true)
  ├── 금: 1개 포스트 공개 (draft: false)
  └── 금: git push
```

---

## 8. 자주 쓰는 명령어 요약

| 작업 | 명령어 |
|------|--------|
| 로컬 미리보기 (draft 포함) | `hugo server -D` |
| 로컬 미리보기 (공개만) | `hugo server` |
| 새 포스트 생성 | `hugo new posts/카테고리/제목.md` |
| 빌드만 (배포 없이) | `hugo --minify` |
| 변경 확인 | `git status` |
| 커밋 | `git add . && git commit -m "메시지"` |
| 배포 | `git push` |
| 빌드 상태 확인 | GitHub → Actions 탭 |
| 빌드 출력 로컬 확인 | `ls public/` |

---

## 9. 트러블슈팅

### hugo.toml과 hugo.yaml 충돌

둘 다 있으면 `hugo.toml`이 우선됩니다. 하나만 사용하세요:

```bash
mv hugo.toml hugo.toml.bak    # yaml 사용 시
# 또는
rm hugo.yaml                   # toml 사용 시
```

### 대시보드 페이지가 안 보일 때

`layouts/dashboard/single.html` 파일이 존재하는지 확인:

```bash
ls layouts/dashboard/single.html
```

`content/dashboard/index.md`의 frontmatter 확인:

```yaml
---
layout: "dashboard"
type: "dashboard"
---
```

### GitHub Actions 빌드 실패

1. GitHub → 저장소 → Actions 탭에서 에러 로그 확인
2. Hugo 버전 확인: `.github/workflows/hugo.yml`의 `HUGO_VERSION`
3. 로컬에서 `hugo --minify`로 빌드 에러 먼저 확인

### YAML 문법 오류

```bash
# Python으로 YAML 검증
python3 -c "import yaml; yaml.safe_load(open('data/roadmap_data.yaml')); print('OK')"
```

---

## 10. 일일 워크플로우 예시

```bash
# ── 작업 시작 ──
cd ~/dev_ws/blog

# ── 프로젝트 작업 후 YAML 업데이트 ──
code data/roadmap_data.yaml
# → 숙련도 변경, 마일스톤 체크, 학습 로그 추가

# ── 확인 ──
hugo server -D
# → 브라우저에서 대시보드 확인 → Ctrl+C

# ── 커밋 + 배포 ──
git add data/roadmap_data.yaml
git commit -m "dashboard: 2/18 학습 로그 + Fleet v3.3 마일스톤 완료"
git push

# 1-2분 후 https://skong097.github.io/dashboard/ 에서 확인
```
