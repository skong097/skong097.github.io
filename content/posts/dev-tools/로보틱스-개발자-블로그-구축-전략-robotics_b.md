---
title: "로보틱스 개발자 블로그 — 구축 전략"
date: 2026-03-21
draft: true
tags: ["dev-tools", "pyqt6", "hugo"]
categories: ["dev-tools"]
description: "**작성일**: 2026-02-16 **목표**: ROS2/로보틱스/AI 기술 블로그 + 프로젝트 포트폴리오 + 커뮤니티 인지도 | 플랫폼 | 비용 | 커스터마이징 | 마크다운 | 포트폴리오 활용 | 추천도 |"
---

# 로보틱스 개발자 블로그 — 구축 전략

**작성일**: 2026-02-16  
**목표**: ROS2/로보틱스/AI 기술 블로그 + 프로젝트 포트폴리오 + 커뮤니티 인지도

---

## Phase 1: 플랫폼 선택 (1일)

### 플랫폼 비교

| 플랫폼 | 비용 | 커스터마이징 | 마크다운 | 포트폴리오 활용 | 추천도 |
|--------|------|-------------|---------|-------------|--------|
| **Hugo + GitHub Pages** | 무료 | 높음 | 네이티브 | GitHub 연동 최적 | ★★★★★ |
| **Gatsby + GitHub Pages** | 무료 | 매우 높음 (React) | 플러그인 | SPA 구조 화려 | ★★★★☆ |
| Jekyll + GitHub Pages | 무료 | 보통 | 네이티브 | 전통적 | ★★★☆☆ |
| Velog | 무료 | 없음 | 지원 | 한국 개발자 커뮤니티 | ★★★☆☆ |
| 티스토리 | 무료 | 스킨 수준 | 제한적 | SEO 약간 유리 | ★★☆☆☆ |

### 추천: Hugo + GitHub Pages

추천 이유:

- **빌드 속도**: Go 기반, 수백 개 포스트도 초 단위 빌드 (Jekyll은 글 많아지면 5분+)
- **마크다운 네이티브**: `.md` 파일 그대로 글 작성 — 일일 작업 기록 습관과 완벽 호환
- **GitHub Pages 무료 호스팅**: `skong097.github.io` 도메인 즉시 사용
- **커스터마이징**: 테마 풍부, Go 템플릿으로 원하는 레이아웃 자유롭게
- **코드 하이라이팅**: Python, YAML, ROS2 launch 파일 등 기본 내장
- **윈도우/리눅스/맥 모두 공식 지원**

```bash
# 설치 (Ubuntu)
sudo snap install hugo --channel=extended

# 새 사이트 생성
hugo new site ros2-blog
cd ros2-blog

# 테마 추가 (예: PaperMod — 깔끔한 기술 블로그 테마)
git init
git submodule add https://github.com/adityatelange/hugo-PaperMod themes/PaperMod

# 로컬 미리보기
hugo server -D
# → http://localhost:1313
```

### 테마 추천

| 테마 | 특징 | 적합도 |
|------|------|--------|
| **PaperMod** | 깔끔, 빠름, 다크모드, 검색 내장 | ★★★★★ |
| Stack | 카테고리 사이드바, 다크모드 | ★★★★☆ |
| Blowfish | 모던, 다양한 레이아웃, Tailwind CSS | ★★★★☆ |
| Docsy | 문서화 특화 (프로젝트 docs에 적합) | ★★★☆☆ |

---

## Phase 2: 사이트 구조 설계 (1~2일)

### 카테고리 구조

```
content/
├── posts/
│   ├── ros2/                    ← ROS2 튜토리얼, 팁, 트러블슈팅
│   │   ├── ros2-jazzy-setup.md
│   │   ├── ros2-nav2-costmap-tuning.md
│   │   └── ros2-slam-toolbox-guide.md
│   ├── computer-vision/         ← YOLO, ST-GCN, 낙상감지 등
│   │   ├── stgcn-finetuning-91-accuracy.md
│   │   └── yolo-realtime-detection-pipeline.md
│   ├── robotics/                ← 하드웨어, 시뮬레이션, 통합
│   │   ├── kevin-patrol-robot-overview.md
│   │   └── pyqt6-robot-dashboard.md
│   ├── ai-ml/                   ← LLM, 모델 학습, 파이프라인
│   │   └── ollama-exaone-realtime-analysis.md
│   └── dev-tools/               ← VSCode, Jupyter, Git 팁
│       └── pyqt6-dark-theme-system.md
├── projects/                    ← 프로젝트 포트폴리오 (핵심 페이지)
│   ├── kevin-patrol-dashboard.md
│   ├── eyecon-pinocchio.md
│   ├── home-guard-bot.md
│   ├── ros2-commander.md
│   └── home-safe-solution.md
└── about/
    └── index.md                 ← 자기소개 + 기술 스택 + 연락처
```

### 필수 페이지

**About 페이지**: 로보틱스 개발자로서의 전문성, 기술 스택(Python, ROS2, PyQt6, YOLO, ST-GCN 등), 프로젝트 요약, GitHub/LinkedIn 링크

**Projects 페이지**: 각 프로젝트별 개요, 스크린샷/GIF, 기술 스택, GitHub 링크. Kevin Patrol Dashboard 같은 프로젝트는 스크린샷+영상이 임팩트 큼

**Tags 시스템**: `ros2`, `nav2`, `slam`, `python`, `pyqt6`, `yolo`, `stgcn`, `gazebo`, `micro-ros` 등 세분화

---

## Phase 3: 초기 콘텐츠 전략 (1~2주)

### 런칭 시 최소 5~7개 포스트로 시작

블로그를 빈 상태로 공개하면 안 됩니다. 처음 방문자가 왔을 때 읽을 거리가 있어야 합니다.

### 즉시 작성 가능한 포스트 (기존 프로젝트 기반)

이미 프로젝트를 진행하면서 쌓인 경험이 풍부합니다. 기존 작업 기록(work_log.md)을 블로그 포스트로 확장하면 됩니다.

| 순번 | 제목 (안) | 카테고리 | 소스 |
|------|----------|---------|------|
| 1 | Kevin 자율순찰 로봇 — PyQt6 대시보드 만들기 | robotics | Kevin Patrol Dashboard v3.2 |
| 2 | ST-GCN 파인튜닝으로 낙상감지 91.89% 달성기 | computer-vision | ST-GCN 프로젝트 |
| 3 | ROS2 Jazzy + FastAPI로 Guard Brain 만들기 | ros2 | Home Guard Bot |
| 4 | PyQt6에서 3테마 시스템 구축하기 (Cyber/Classic/JARVIS) | dev-tools | 대시보드 테마 작업 |
| 5 | Ollama EXAONE 7.8B로 실시간 대화 분석 만들기 | ai-ml | EyeCon v3.5 |
| 6 | ROS2 Commander — 게임으로 ROS2 배우기 | ros2 | ROS2 Commander |
| 7 | Random Forest vs ST-GCN — 낙상감지 모델 비교 | computer-vision | 모델 비교 프로젝트 |

### 포스트 작성 템플릿

```markdown
---
title: "ST-GCN 파인튜닝으로 낙상감지 91.89% 달성기"
date: 2026-02-20
tags: ["st-gcn", "computer-vision", "fall-detection", "python"]
categories: ["computer-vision"]
summary: "ST-GCN 모델을 3클래스 낙상감지에 맞춰 파인튜닝하고 84.21% → 91.89%로 끌어올린 과정"
cover:
  image: "images/stgcn-accuracy-chart.png"
  alt: "ST-GCN 정확도 개선 그래프"
draft: false
---

## 배경
(왜 이 프로젝트를 했는지)

## 접근 방법
(어떤 기술적 선택을 했는지)

## 구현
(핵심 코드 + 설명)

## 결과
(숫자로 보여주기 — 정확도, 속도, 비교)

## 배운 점 / 삽질 기록
(트러블슈팅, 실패→성공 과정)

## 다음 단계
(향후 계획)
```

---

## Phase 4: 배포 & CI/CD (반나절)

### GitHub Pages 배포

```bash
# 1. GitHub 저장소 생성
#    skong097.github.io (또는 원하는 이름)

# 2. GitHub Actions 자동 배포 설정
# .github/workflows/deploy.yml
```

```yaml
name: Deploy Hugo

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true
          fetch-depth: 0

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: 'latest'
          extended: true

      - name: Build
        run: hugo --minify

      - name: Deploy
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./public
```

이렇게 설정하면 `main` 브랜치에 push할 때마다 자동으로 빌드+배포됩니다.

### 작업 플로우

```
VSCode에서 .md 작성 → git push → GitHub Actions 자동 빌드 → 블로그 업데이트
```

---

## Phase 5: 커뮤니티 확산 전략

### 타겟 커뮤니티

| 플랫폼 | 활용법 | 우선순위 |
|--------|-------|---------|
| **ROS Discourse** | ROS2 튜토리얼/팁 공유, 질문 답변 시 블로그 링크 | ★★★★★ |
| **GitHub** | 프로젝트 README에 블로그 링크, 코드와 글 연결 | ★★★★★ |
| **Reddit r/robotics, r/ROS** | 프로젝트 공유, 질문 답변 | ★★★★☆ |
| **LinkedIn** | 프로젝트 완료 시 포스트 + 블로그 링크 | ★★★★☆ |
| **X (Twitter)** | #ROS2 #robotics 해시태그로 짧은 공유 | ★★★☆☆ |
| **YouTube** | 대시보드 데모 영상 + 블로그 상세 설명 연결 | ★★★☆☆ |

### 콘텐츠 연결 전략

프로젝트 하나가 여러 채널로 확산되는 구조를 만드는 게 핵심입니다.

```
Kevin Patrol Dashboard 완성
    ├── GitHub: 소스코드 + README
    ├── 블로그: 상세 개발기 (3~4편 시리즈)
    ├── YouTube: 30초~1분 데모 영상
    ├── ROS Discourse: "ROS2 기반 순찰 로봇 대시보드 만들었습니다" 공유
    └── LinkedIn: 프로젝트 요약 + 영상 + 블로그 링크
```

### SEO 기본 설정

```toml
# hugo.toml (config)
baseURL = "https://skong097.github.io/"
languageCode = "ko"
title = "Stephen's Robotics Lab"
theme = "PaperMod"

[params]
  description = "ROS2, Computer Vision, AI 기반 로보틱스 개발 블로그"
  author = "Stephen Kong"
  ShowReadingTime = true
  ShowPostNavLinks = true
  ShowBreadCrumbs = true
  ShowCodeCopyButtons = true
  ShowShareButtons = true

[params.homeInfoParams]
  Title = "Robotics × AI × ROS2"
  Content = "자율순찰 로봇, 컴퓨터 비전, 로보틱스 시뮬레이션을 다루는 개발 블로그"

[[params.socialIcons]]
  name = "github"
  url = "https://github.com/skong097"
```

---

## Phase 6: 지속 운영 전략

### 포스팅 주기

현실적으로 프로젝트 병행하면서 유지할 수 있는 주기가 중요합니다.

| 빈도 | 내용 |
|------|------|
| **격주 1편** (최소) | 기술 포스트 — 프로젝트 진행 중 배운 것, 트러블슈팅 |
| 월 1편 | 프로젝트 업데이트 — 버전 릴리즈, 새 기능 |
| 분기 1편 | 회고/로드맵 — 지난 3개월 정리, 앞으로 계획 |

### 콘텐츠 유형별 효과

| 유형 | 트래픽 | 작성 난이도 | 지속성 |
|------|--------|-----------|--------|
| **트러블슈팅 ("~했더니 ~에러, 해결법")** | 높음 | 낮음 | 길다 (검색 유입) |
| 튜토리얼 ("~하는 방법") | 높음 | 중간 | 길다 |
| 프로젝트 개발기 ("~만들기") | 중간 | 높음 | 중간 |
| 기술 비교 ("A vs B") | 높음 | 중간 | 길다 |
| 도구/라이브러리 리뷰 | 중간 | 낮음 | 중간 |

**가장 효율적인 전략**: 프로젝트 진행하면서 만난 에러와 해결 과정을 바로 포스트로 작성. 일일 작업 기록(work_log.md)을 이미 쓰고 있으니, 이걸 블로그 포스트로 확장하는 것이 가장 자연스럽습니다.

---

## 전체 타임라인

| Phase | 기간 | 산출물 |
|-------|------|--------|
| Phase 1: 플랫폼 선택 | 1일 | Hugo 설치, 테마 선정 |
| Phase 2: 구조 설계 | 1~2일 | 카테고리, 메뉴, About/Projects 페이지 |
| Phase 3: 초기 콘텐츠 | 1~2주 | 5~7개 포스트 작성 |
| Phase 4: 배포 | 반나절 | GitHub Actions CI/CD, 도메인 설정 |
| Phase 5: 확산 | 지속 | 커뮤니티 공유, SEO |
| Phase 6: 운영 | 지속 | 격주 1편+ 포스팅 |

**런칭까지 약 2~3주**, 이후 프로젝트와 병행하며 꾸준히 운영.

---

## 즉시 시작 체크리스트

- [ ] Hugo 설치 (`snap install hugo --channel=extended`)
- [ ] PaperMod 테마로 사이트 생성
- [ ] `skong097.github.io` 저장소 생성
- [ ] About 페이지 작성
- [ ] Kevin Patrol Dashboard 포스트 초안 작성 (첫 글)
- [ ] GitHub Actions 배포 설정
- [ ] ROS Discourse 계정 확인 / 프로필 업데이트
