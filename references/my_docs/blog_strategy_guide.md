# Blog Strategy & Posting Guide

> **Robotics Engineering Portfolio Blog — 운영 전략 및 포스팅 가이드**
>
> Platform: Hugo + GitHub Pages
>
> Author: Stephen Kong | github.com/skong097
>
> Created: February 2026

---

## 1. 블로그 운영 목적

### 1.1 핵심 목표

- **포트폴리오 증명:** 10개 프로젝트의 기술적 깊이와 실행력을 체계적으로 기록
- **기술 브랜딩:** "ROS2 × AI/ML × Physical AI" 1인 개발자로서의 전문성 확립
- **지식 아카이빙:** 개발 과정에서 겪은 문제 해결, 설계 결정, 성능 최적화 경험을 재활용 가능한 형태로 축적
- **커뮤니티 기여:** 한국어 ROS2/Physical AI 자료가 부족한 상황에서 실질적인 참고 자료 제공

### 1.2 타겟 독자

| 독자층 | 관심 포인트 | 콘텐츠 방향 |
|--------|-----------|------------|
| 로보틱스 개발자 | ROS2, SLAM, Navigation | 기술 구현 상세 + 코드 스니펫 |
| AI/ML 엔지니어 | 모델 학습, 파인튜닝, 배포 | 성능 비교 + 파이프라인 설계 |
| 취업 준비생/학생 | 프로젝트 구조, 포트폴리오 | 설계 과정 + 의사결정 근거 |
| 산업 엔지니어 | Smart Factory, PdM, Digital Twin | 비즈니스 가치 + 적용 사례 |

---

## 2. 포스팅 순환 전략

### 2.1 핵심 원칙: 10-5-5 순환

```
[10개 프로젝트 축적] → [5편 포스팅 + 5편 예비]
      ↓                       ↓
[1주일간 포스팅]          [다음 주 5개 프로젝트 수행]
      ↓                       ↓
[10개 다시 축적] → [반복...]
```

- 프로젝트 10개를 먼저 완성한 뒤, 주간 단위로 5편 포스팅 + 5편 예비를 운영
- 예비 5편은 다음 주기에 포스팅으로 승격, 그 사이 새로운 5개 프로젝트를 수행
- 항상 "쓸 거리가 넘치는" 상태를 유지하여 포스팅 압박 없이 품질에 집중

### 2.2 1차 포스팅 (주간 1: 기존 프로젝트 5편)

| 요일 | 프로젝트 | 포스트 제목 (안) | 타겟 키워드 |
|------|---------|----------------|------------|
| 월 | Kevin Patrol Dashboard | PyQt6로 로봇 모니터링 대시보드 만들기 | ROS2, PyQt6, Dashboard |
| 화 | Home Safe Solution | ST-GCN 파인튜닝으로 낙상감지 91.89% 달성기 | ST-GCN, Fall Detection |
| 수 | Home Guard Bot | ROS2 + FastAPI로 Guard Brain LLM 노드 만들기 | ROS2, FastAPI, LLM |
| 목 | EyeCon (피노키오) | Ollama EXAONE 7.8B로 실시간 대화 분석 만들기 | LLM, Emotion AI |
| 금 | ROS2 Commander | 게임으로 배우는 ROS2 — Pygame 학습 게임 개발기 | ROS2, Education, Game |

### 2.3 예비 포스팅 (주간 1 예비 → 주간 2 포스팅)

| 프로젝트 | 포스트 제목 (안) | 타겟 키워드 |
|---------|----------------|------------|
| Kevin 3D Sim | Pygame + OpenGL로 3D 순찰 로봇 시뮬레이터 만들기 | Robotics, OpenGL, SLAM |
| MyPet | 핸드 제스처 인식 가상 반려견 개발기 | MediaPipe, CV, Gesture |
| Smart Factory Dashboard | Physical AI 공장 모니터링 대시보드 구축기 | Digital Twin, IoT, PyQt6 |
| Isaac Sim Integration | NVIDIA Isaac Sim으로 Kevin 로봇 디지털 트윈 구축기 | NVIDIA, Isaac Sim, Sim-to-Real |
| Predictive Maintenance | IoT 센서 + ML로 설비 고장 예측 AI 만들기 | PdM, LSTM, XGBoost |

### 2.4 2차 포스팅 이후 순환

```
주간 2: 예비 5편 포스팅 + 새 프로젝트 5개 수행 → 예비 5편 추가 축적
주간 3: 새 예비 5편 포스팅 + 또 다시 5개 수행 → ...
```

---

## 3. 포스트 작성 원칙

### 3.1 구조 원칙

모든 포스트는 다음 뼈대를 따르되, 프로젝트 성격에 따라 비중을 조절한다.

```
1. Hook (1~2문장)        — 이 프로젝트가 왜 필요한지, 어떤 문제를 해결하는지
2. 프로젝트 개요          — 목표, 기술 스택, 기간, 결과 요약
3. 핵심 설계 결정         — 왜 이 구조/라이브러리/알고리즘을 선택했는지
4. 구현 상세 (코드 포함)   — 가장 중요한 모듈 1~2개에 집중
5. 결과 및 성능           — 스크린샷, 숫자, 비교 테이블
6. 회고 / Lessons Learned — 삽질 경험, 개선 방향, 다음 단계
7. 참고 자료              — 논문, 공식 문서, 관련 프로젝트 링크
```

### 3.2 작성 톤 & 스타일

**기본 톤: "옆자리 동료한테 설명하듯이"**

딱딱한 기술 문서 말고, 카페에서 같이 개발하는 친구한테 "나 이거 이렇게 했거든?" 하는 느낌으로 쓴다. 반말까지는 아니고, 편한 존댓말 정도.

| 원칙 | 이렇게 쓰자 | 이렇게 쓰지 말자 |
|------|-----------|----------------|
| **내 얘기로 쓰기** | "처음에 TCP로 직접 쏴봤는데, 연결 끊기면 답이 없더라고요. 그래서 DDS Discovery로 갈아탔습니다" | "TCP 통신 방식은 연결 안정성 측면에서 DDS 대비 열위에 있어 DDS를 채택하였다" |
| **왜?를 먼저** | "라벨 데이터가 없었어요. 그래서 비지도 학습인 Isolation Forest를 골랐습니다" | "Isolation Forest는 비지도 학습 기반 이상치 탐지 알고리즘으로서..." |
| **숫자는 확실하게** | "84.21%에서 91.89%까지 올렸어요. +7.68%p면 꽤 의미 있는 차이죠" | "성능이 유의미하게 향상되었다" |
| **삽질도 솔직하게** | "이거 3일 날렸습니다. 원인은 좌표계를 반대로 넣은 거였어요..." | (삽질 경험 생략) |
| **코드는 핵심만** | "전체 코드는 GitHub에 있고, 여기선 제일 중요한 부분만 볼게요" | (전체 소스 코드 붙여넣기) |
| **기술 용어는 영문** | "DDS(Data Distribution Service) 미들웨어를 통해서..." | "데이터 분배 서비스 중간소프트웨어를 활용하여..." |

**톤 예시:**

> ❌ 나쁜 예: "본 프로젝트에서는 PyQt6 프레임워크를 활용하여 실시간 모니터링 대시보드를 구현하였으며, DataProvider 추상화 패턴을 적용하여 시뮬레이션과 실제 로봇 간의 전환을 용이하게 하였다."
>
> ✅ 좋은 예: "대시보드를 PyQt6로 만들었는데, 나중에 실제 로봇 연결할 때 코드를 다 뜯어고치기 싫어서 DataProvider라는 추상화 레이어를 하나 끼워넣었어요. 덕분에 SIM/LIVE 모드 전환이 스위치 하나로 됩니다."

### 3.3 금지 사항

- 논문 투 느낌의 딱딱한 문체 (→ 편하게 말하듯이)
- "~한 것 같습니다", "~로 사료된다" 같은 모호한 표현 (→ "~했습니다", "~입니다"로 확실하게)
- 전체 소스 코드 붙여넣기 (→ 핵심 스니펫 + GitHub 링크)
- 스크린샷 없이 "잘 돌아갑니다" (→ 반드시 캡처 첨부)
- 프로젝트를 뚝 떼어서 소개 (→ 포트폴리오 전체 흐름 속에서 위치 설명)
- AI가 뱉어낸 것 같은 뻔한 서론/결론 (→ 내 경험과 감상 중심)

---

## 4. 카테고리 & 태그 체계

### 4.1 카테고리 (대분류, 6개 이내)

| 카테고리 | 설명 | 해당 프로젝트 |
|---------|------|------------|
| `Robotics` | ROS2, SLAM, Navigation, 로봇 시뮬레이션 | Kevin Sim/Dashboard, Home Guard Bot, ROS2 Commander |
| `AI/ML` | 모델 학습, 파인튜닝, 추론, 성능 비교 | Home Safe Solution, Predictive Maintenance, EyeCon |
| `Smart Factory` | Digital Twin, IoT, 예측정비, 공장 자동화 | Smart Factory Dashboard, Isaac Sim, PdM AI |
| `DevOps` | MLOps, AIOps, CI/CD, 배포, 모니터링 | MLflow 파이프라인, Docker, GitHub Actions |
| `Side Project` | 실험적/학습 목적 프로젝트 | MyPet, ROS2 Commander |
| `Paper Review` | 논문 리뷰, 기술 트렌드 분석 | AIOps, Robot Network, Robot Security 논문 |

### 4.2 태그 (세부 기술, 자유 형식)

자주 사용할 태그 목록:

```yaml
# 프레임워크
tags: [ROS2, PyQt6, FastAPI, Isaac-Sim, Omniverse]

# AI/ML
tags: [ST-GCN, LSTM, XGBoost, YOLO, Isolation-Forest, Autoencoder, Random-Forest]

# LLM
tags: [Ollama, EXAONE, LLM, RAG, Prompt-Engineering]

# 인프라
tags: [DDS, Zenoh, MQTT, SROS2, Docker, MLflow, Grafana]

# 도메인
tags: [Physical-AI, Digital-Twin, Predictive-Maintenance, Smart-Factory, IoT]

# 언어/도구
tags: [Python, OpenCV, MediaPipe, OpenGL, Pygame, pyqtgraph]
```

### 4.3 태그 사용 규칙

- 포스트당 태그 5~8개 (너무 많으면 희석, 너무 적으면 검색 누락)
- 카테고리는 1개만 선택, 태그로 교차 분류 보완
- 새 기술 도입 시 태그 먼저 추가 후 포스트 작성
- 태그명은 영문 케밥 케이스 (`Predictive-Maintenance`, `Smart-Factory`)

---

## 5. Hugo 사이트 구성

### 5.1 플랫폼 선택 근거

| 항목 | Hugo | Jekyll | 선택 이유 |
|------|------|--------|----------|
| 빌드 속도 | ~50ms/페이지 | ~300ms/페이지 | 프로젝트 수 증가 시 빌드 속도 중요 |
| 언어 | Go | Ruby | Go 바이너리 하나로 설치 완료 |
| 테마 생태계 | 풍부 | 풍부 | 동급 |
| GitHub Pages | 지원 | 네이티브 | GitHub Actions로 자동 배포 |
| 코드 하이라이팅 | 내장 (Chroma) | Rouge | Python/YAML/bash 네이티브 지원 |

### 5.2 디렉토리 구조

```
blog/
├── config.toml              # Hugo 설정
├── content/
│   ├── posts/               # 블로그 포스트
│   │   ├── 2026-02-kevin-dashboard.md
│   │   ├── 2026-02-stgcn-fall-detection.md
│   │   └── ...
│   ├── projects/            # 프로젝트 소개 (정적 페이지)
│   │   ├── kevin-patrol.md
│   │   ├── home-safe-solution.md
│   │   └── ...
│   └── about.md             # 자기 소개
├── static/
│   ├── images/              # 스크린샷, 다이어그램
│   │   ├── kevin-dashboard-screenshot.png
│   │   └── ...
│   └── files/               # 다운로드 자료 (PDF 등)
├── themes/                  # Hugo 테마
└── .github/
    └── workflows/
        └── deploy.yml       # GitHub Actions 자동 배포
```

### 5.3 Front Matter 템플릿

모든 포스트는 아래 front matter를 포함한다:

```yaml
---
title: "PyQt6로 로봇 모니터링 대시보드 만들기"
date: 2026-02-17
draft: false
categories: ["Robotics"]
tags: ["ROS2", "PyQt6", "Dashboard", "SLAM", "Digital-Twin"]
summary: "Kevin 순찰 로봇의 7패널 통합 모니터링 대시보드를 PyQt6로 구축한 과정"
cover:
  image: "/images/kevin-dashboard-screenshot.png"
  alt: "Kevin Patrol Dashboard v3.1"
project: "kevin-patrol-dashboard"
series: ["Kevin Patrol System"]
toc: true
---
```

### 5.4 Front Matter 필드 규칙

| 필드 | 필수 | 설명 |
|------|------|------|
| `title` | ✅ | 50자 이내, 핵심 기술 키워드 포함 |
| `date` | ✅ | 포스팅 날짜 (YYYY-MM-DD) |
| `draft` | ✅ | 예비 포스트는 `true`, 포스팅 시 `false` 전환 |
| `categories` | ✅ | 1개만 선택 |
| `tags` | ✅ | 5~8개, 영문 케밥 케이스 |
| `summary` | ✅ | 1~2문장, SNS 공유 시 표시 |
| `cover.image` | ✅ | 대표 이미지 경로 |
| `project` | 권장 | 연관 프로젝트 slug (프로젝트 페이지 링크용) |
| `series` | 선택 | 시리즈물일 경우 시리즈명 |
| `toc` | 선택 | 목차 자동 생성 (긴 포스트에 권장) |

---

## 6. 포스트 품질 체크리스트

포스팅 전 아래 항목을 확인한다:

### 6.1 필수 체크

- [ ] 제목에 핵심 기술 키워드가 포함되어 있는가?
- [ ] Hook (첫 1~2문장)이 "왜 이 프로젝트인가"를 즉시 전달하는가?
- [ ] 아키텍처 다이어그램 또는 시스템 구조도가 포함되어 있는가?
- [ ] 스크린샷/결과 이미지가 최소 3장 이상인가?
- [ ] 핵심 코드 스니펫이 포함되어 있는가? (전체 코드 X)
- [ ] 정량적 결과 (accuracy, 속도, 비교 수치)가 제시되어 있는가?
- [ ] GitHub 저장소 링크가 포함되어 있는가?
- [ ] 포트폴리오 내 다른 프로젝트와의 연결이 언급되어 있는가?
- [ ] front matter가 템플릿 규칙에 맞는가?
- [ ] 태그 5~8개가 적절히 설정되어 있는가?

### 6.2 품질 향상

- [ ] "Why" 설명이 "How" 설명보다 비중이 큰가?
- [ ] 삽질 경험 / 실패 → 해결 과정이 포함되어 있는가?
- [ ] 다음 단계 / 개선 방향이 명시되어 있는가?
- [ ] 관련 논문이나 공식 문서 참조가 있는가?
- [ ] 코드 블록에 언어 태그가 지정되어 있는가? (```python, ```yaml 등)
- [ ] 이미지에 alt 텍스트가 설정되어 있는가?

---

## 7. SEO & 키워드 전략

### 7.1 타겟 검색 키워드

블로그 전체에서 노리는 검색 유입 키워드:

| 우선순위 | 키워드 | 예상 검색 의도 | 대응 포스트 |
|---------|--------|--------------|-----------|
| 높음 | ROS2 대시보드 | ROS2 모니터링 UI 구현 | Kevin Dashboard |
| 높음 | ST-GCN 파인튜닝 | 행동 인식 모델 개선 | Home Safe Solution |
| 높음 | Isaac Sim ROS2 연동 | NVIDIA 시뮬레이터 튜토리얼 | Isaac Sim Integration |
| 높음 | 예측 정비 ML | Smart Factory AI | Predictive Maintenance |
| 중간 | PyQt6 실시간 그래프 | GUI 개발 가이드 | Kevin Dashboard |
| 중간 | ROS2 보안 SROS2 | 로봇 사이버보안 | Robot Security 리뷰 |
| 중간 | DDS Zenoh 비교 | ROS2 미들웨어 선택 | Robot Network 리뷰 |
| 낮음 | Ollama EXAONE | 한국어 LLM 활용 | EyeCon |
| 낮음 | MLOps 로보틱스 | 로봇 ML 파이프라인 | AIOps 리뷰 |

### 7.2 SEO 작성 규칙

- 제목(H1)에 주요 키워드 1~2개 포함
- 첫 문단(100자 이내)에 핵심 키워드 자연스럽게 삽입
- H2/H3 소제목에 보조 키워드 배치
- 이미지 파일명에 키워드 포함 (`kevin-dashboard-slam-map.png`)
- 내부 링크: 관련 포스트 간 상호 참조 (시리즈물 네비게이션)
- summary 필드를 meta description으로 활용

---

## 8. 논문 리뷰 포스트 가이드

논문 리뷰는 일반 프로젝트 포스트와 구조가 다르다.

### 8.1 논문 리뷰 구조

```
1. 논문 기본 정보     — 제목, 저자, 출처, 년도, 키워드
2. 한줄 요약          — 이 논문이 말하는 것을 한 문장으로
3. 배경 / 문제 정의    — 왜 이 연구가 필요한지
4. 핵심 방법론         — 제안한 방법을 다이어그램 포함하여 설명
5. 실험 결과          — 주요 수치 + 비교 테이블
6. 내 프로젝트 적용점  — ★ 가장 중요: 이 논문을 어떻게 활용할 건지
7. 한계 / 향후 연구    — 논문의 한계와 개선 가능성
```

### 8.2 논문 리뷰 대상 (현재)

| # | 논문 | Keyword | 프로젝트 연결 |
|---|------|---------|------------|
| P1 | MLOps & AIOps Challenges (SLR) | AIOps/MLOps | #10 MLOps Pipeline |
| P2 | MLOps/LLMOps Roadmap 2026 | AIOps/MLOps | #5 LLMOps |
| P3 | Multi-Robot Comm. Isolation | Robot Network | #8 Factory Network |
| P4 | ROS2 RMW Mesh Comparison | Robot Network | #9 Isaac Sim RMW |
| P5 | DDS Middleware in Robotics (SLR) | Robot Network | #8 DDS Architecture |
| P6 | ROS2 DDS Delay Optimization | Robot Network | #8/#9 QoS Tuning |
| P7 | (In)Security of Secure ROS2 | Robot Security | Kevin SROS2 적용 |
| P8 | ROS2 Comm. Vuln. Analysis (7) | Robot Security | IDS 구축 Phase 3 |
| P9 | Supply Chain Exploitation PoC | Robot Security | 공급망 보안 Phase 4 |
| P10 | ROS 2 in a Nutshell (435편) | All Keywords | 전체 아키텍처 |

---

## 9. 시리즈 운영 계획

관련 프로젝트를 묶어 시리즈로 운영하면 독자 체류 시간과 내부 링크 효과가 증가한다.

### 9.1 시리즈 목록

| 시리즈명 | 포함 프로젝트 | 예상 편수 |
|---------|------------|----------|
| Kevin Patrol System | Kevin 3D Sim → Dashboard → Isaac Sim | 3~5편 |
| Home AI Solutions | Home Safe Solution → Home Guard Bot | 2~3편 |
| Smart Factory AI | Factory Dashboard → PdM AI → AIOps | 3~4편 |
| Robot Infra Deep Dive | Robot Network → Robot Security → DDS | 2~3편 (논문 리뷰 중심) |
| AI/ML 실전 파이프라인 | ST-GCN 파인튜닝 → 모델 비교 → MLOps | 2~3편 |

### 9.2 시리즈 네비게이션

각 시리즈의 첫 포스트에 전체 목차를 배치하고, 포스트 하단에 이전/다음 링크를 삽입한다:

```markdown
---
> **Kevin Patrol System 시리즈**
> 1. [Pygame + OpenGL로 3D 시뮬레이터 만들기](/posts/kevin-3d-sim/) ← 현재
> 2. [PyQt6로 모니터링 대시보드 만들기](/posts/kevin-dashboard/)
> 3. [Isaac Sim으로 디지털 트윈 구축하기](/posts/kevin-isaac-sim/)
---
```

---

## 10. 배포 & 자동화

### 10.1 GitHub Actions 자동 배포

```yaml
# .github/workflows/deploy.yml
name: Deploy Hugo to GitHub Pages

on:
  push:
    branches: [main]

jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true
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

### 10.2 작업 흐름

```
1. 로컬에서 포스트 작성 (content/posts/YYYY-MM-title.md)
2. hugo server -D 로 로컬 프리뷰 확인
3. draft: false 로 변경
4. git commit & push → GitHub Actions 자동 빌드/배포
5. GitHub Pages에 즉시 반영
```

### 10.3 이미지 관리

- 원본 이미지는 `static/images/프로젝트명/` 하위에 저장
- 파일명 규칙: `프로젝트-설명-번호.png` (예: `kevin-dashboard-slam-map-01.png`)
- 최대 해상도: 1920px (가로), 용량 500KB 이내 (필요시 압축)
- 다이어그램은 가능하면 Mermaid 또는 ASCII art로 작성하여 유지보수성 확보

---

## 11. 월간 운영 리듬

### 11.1 주간 스케줄

| 요일 | 활동 |
|------|------|
| 월~금 | 프로젝트 개발 + 포스트 초안 작성 (개발 중 메모) |
| 토 | 포스트 다듬기 + 스크린샷/다이어그램 제작 |
| 일 | 포스팅 예약 + 다음 주 계획 |

### 11.2 포스트 작성 타이밍

- 하루 마지막 코드 작성 후 `.md` 파일로 개발 기록 → 포스트 초안 소재로 활용
- 프로젝트 1개 완료 시점에 포스트 초안 작성 (기억이 생생할 때)
- 주말에 초안 → 완성본 다듬기 + 이미지 추가

### 11.3 KPI

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| 월간 포스트 수 | 8~10편 | Hugo 빌드 로그 |
| 포스트당 평균 길이 | 1,500~3,000자 | 워드 카운트 |
| 시각 자료 비율 | 포스트당 3장+ | 이미지 카운트 |
| GitHub 스타 | 프로젝트당 5+ | GitHub Insights |
| 시리즈 완성률 | 시작한 시리즈 100% 완결 | 수동 체크 |

---

## Appendix: 포스트 템플릿

새 포스트 작성 시 아래 파일을 복사하여 시작한다:

```markdown
---
title: "[프로젝트명] 한줄 설명"
date: YYYY-MM-DD
draft: true
categories: ["Robotics"]
tags: ["tag1", "tag2", "tag3", "tag4", "tag5"]
summary: "한두 문장 요약"
cover:
  image: "/images/프로젝트명/cover.png"
  alt: "대표 이미지 설명"
project: "프로젝트-slug"
series: ["시리즈명"]
toc: true
---

## 왜 이 프로젝트를 만들었나

(Hook: 문제 정의 + 동기)

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| Tech Stack | ... |
| Duration | ... |
| GitHub | [repo](https://github.com/skong097/...) |

## 핵심 설계 결정

### 왜 A를 선택했나 (vs B, C)

(의사결정 근거 + 비교)

## 구현 상세

### 모듈 1: ...

```python
# 핵심 코드 스니펫
```

### 모듈 2: ...

## 결과

(스크린샷 + 성능 수치)

| 모델 | Accuracy | 추론 시간 |
|------|---------|---------|
| ... | ...% | ...ms |

## 회고 & 다음 단계

### 잘한 점
- ...

### 삽질 경험
- ...

### 다음 단계
- ...

## 참고 자료

- [논문/문서 1](URL)
- [논문/문서 2](URL)
```
