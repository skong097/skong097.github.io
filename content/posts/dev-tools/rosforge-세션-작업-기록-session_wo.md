---
title: "ROSForge — 세션 작업 기록"
date: 2026-03-21
draft: true
tags: ["dev-tools", "rosforge"]
categories: ["dev-tools"]
description: "**작업일**: 2026-03-19 **작성자**: gjkong **세션**: ROSForge 검증 및 UI 개선"
---

# ROSForge — 세션 작업 기록

**작업일**: 2026-03-19  
**작성자**: gjkong  
**세션**: ROSForge 검증 및 UI 개선

---

## 1. 세션 요약

| 단계 | 내용 | 상태 |
|------|------|------|
| 환경 검증 | venv + ROS2 Jazzy 환경 구성 | ✅ |
| 실행 오류 수정 | `AA_UseHighDpiPixmaps` 제거 | ✅ |
| UI 구조 개편 | DockWidget → 사이드바 네비게이션 | ✅ |
| 사이드바 토글 | 슬라이드 애니메이션 접기/펼치기 | ✅ |
| 이모지 제거 | 메뉴바, 사이드바, 버튼 전체 | ✅ |
| 테마 시스템 | Navy Professional / Slate Dark Pro 토글 | ✅ |
| 폰트 색상 수정 | 테마별 글자 가시성 문제 해결 | ✅ |
| 폰트 적용 | Pretendard + JetBrains Mono 설치 스크립트 | ✅ |

---

## 2. 주요 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `main.py` | `AA_UseHighDpiPixmaps` 제거, 스플래시 스크린 |
| `rosforge/ui/main_window.py` | 사이드바 구조 전면 개편, 테마 토글, 폰트 로딩 |
| `rosforge/ui/sidebar.py` | 신규 — 고정 네비게이션 사이드바 (토글 가능) |
| `rosforge/assets/theme_navy.qss` | Navy Professional 라이트 테마 |
| `rosforge/assets/theme_slate.qss` | Slate Dark Pro 다크 테마 |
| `install_fonts.sh` | Pretendard + JetBrains Mono 설치 스크립트 |

---

## 3. 아키텍처 변경 — DockWidget → 사이드바

### 변경 전
```
QMainWindow
├── QDockWidget (build)
├── QDockWidget (topic)
├── QDockWidget (log)
└── ... (15개 독립 dock)
```

### 변경 후
```
QMainWindow
├── QMenuBar (네이비)
├── QToolBar — 상단바 (브레드크럼 / 프로파일 / DOMAIN / Launch / Kill All)
└── Central Widget
    ├── SidebarWidget (200px 고정, 토글 시 48px)
    │   ├── 로고 (RF 배지)
    │   ├── 스크롤 네비게이션 (5개 섹션, 15개 항목)
    │   └── 하단 (ROS 상태 + < > 토글 버튼)
    └── QStackedWidget (패널 전환)
        ├── env_panel
        ├── build_panel
        └── ... (15개 패널)
```

---

## 4. 테마 시스템

| 항목 | Navy Professional | Slate Dark Pro |
|------|-------------------|----------------|
| 배경 | `#f5f7fa` (라이트) | `#1e293b` (다크) |
| 텍스트 | `#1a2b45` | `#e2e8f0` |
| 액센트 | `#1a7bbe` | `#3b82f6` |
| 메뉴바 | `#1a2b45` (네이비) | `#0f172a` (딥다크) |
| 상태바 | `#1a2b45` | `#0f172a` |
| 사이드바 | `#1a2b45` (공통 고정) | `#1a2b45` (공통 고정) |

**전환 방법**
- 메뉴 `테마(T)` → `Navy Professional` / `Slate Dark Pro`
- 단축키 `Ctrl + T` — 즉시 토글

---

## 5. 폰트

| 용도 | 폰트 | 비고 |
|------|------|------|
| UI 전체 | Pretendard | 한국어 최적화, SIL 오픈 라이선스 |
| 터미널/코드 | JetBrains Mono | 리가처 지원 |
| 폴백 | 시스템 기본 | 폰트 미설치 시 자동 |

**설치 방법**
```bash
~/ROSForge/install_fonts.sh
```

---

## 6. 실행 방법

```bash
# 매번 실행
source ~/ROSForge/.venv/bin/activate
source /opt/ros/jazzy/setup.bash
cd ~/ROSForge
python3 main.py

# alias 등록 후 (한 번만 설정)
rosforge
```

---

## 7. 다음 작업 후보

| 항목 | 내용 |
|------|------|
| 패널 기능 검증 | Interface, Bag, Launch, Terminal 실제 동작 확인 |
| ROS2 연동 검증 | talker/listener 노드로 토픽/로그/그래프 패널 테스트 |
| GHOST-5 M04 재개 | SROS2 `failed to validate namespace` 오류 해결 |

---

*작성: gjkong | 2026-03-19*
