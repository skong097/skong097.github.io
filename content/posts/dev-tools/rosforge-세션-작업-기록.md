---
title: "ROSForge — 세션 작업 기록"
date: 2026-03-21
draft: true
tags: ["dev-tools", "pyqt6", "rosforge"]
categories: ["dev-tools"]
description: "**작업일**: 2026-03-18 **작성자**: gjkong **세션**: ROSForge 프로젝트 초기 설계 ~ M04 구현 완료"
---

# ROSForge — 세션 작업 기록

**작업일**: 2026-03-18  
**작성자**: gjkong  
**세션**: ROSForge 프로젝트 초기 설계 ~ M04 구현 완료

---

## 1. 세션 요약

| 단계 | 내용 | 상태 |
|------|------|------|
| 기술 조사 | ROSForge 기술 스택 분석 및 연구 문서 작성 | ✅ |
| 구축 계획서 | ROSForge_plan.md v1.1 작성 (M00~M10 전체) | ✅ |
| 구조 생성 스크립트 | setup_structure.py 작성 및 실행 | ✅ |
| M00 구현 | 환경 설정 패널 전체 구현 | ✅ |
| M01 구현 | Build & Run Panel 전체 구현 | ✅ |
| M02 구현 | Topic Panel 전체 구현 | ✅ |
| M03 구현 | Parameter Panel 전체 구현 | ✅ |
| M04 구현 | Service & Action Panel 전체 구현 | ✅ |

---

## 2. 프로젝트 개요

**프로젝트명**: ROSForge — ROS2 Unified Development & Monitoring Platform  
**홈 폴더**: `~/ROSForge/`  
**기술 스택**: PyQt6, rclpy, asyncio, pyqtgraph, aiosqlite, PyYAML, watchdog, psutil  
**지원 플랫폼**: ROS2 Basic (PC) / Raspberry Pi / GHOST-5 (Swarm) / Custom  
**기준 문서**: ROSForge_research.md v2.0, ROSForge_plan.md v1.1

---

## 3. 산출물 — 구현 파일 전체 목록

### 3.1 프로젝트 루트

| 파일 | 설명 |
|------|------|
| `main.py` | 진입점 — QApplication + MainWindow |
| `requirements.txt` | Python 패키지 의존성 |
| `setup.py` | 패키지 설치 스크립트 |
| `README.md` | 프로젝트 설명 |
| `setup_structure.py` | 전체 디렉토리/파일 구조 생성 스크립트 |

### 3.2 backend — 구현 완료 파일

| 파일 | 마일스톤 | 핵심 기능 |
|------|----------|-----------|
| `ros2_adapter.py` | M00 공통 | Jazzy/Humble 배포판 추상화 계층 |
| `environment_manager.py` | M00-1 | sourced env 추출, colcon/ros2 env 분리, invalidate_cache |
| `bashrc_manager.py` | M00-2,11 | .bashrc 블록 삽입/갱신/백업/충돌 감지 |
| `profile_manager.py` | M00-3 | YAML 프로파일 저장/불러오기, 기본 2종 자동 생성 |
| `build_manager.py` | M01-1,2,2b | colcon build, topological_sort, 에러 파싱+해결책 8종, watch mode |
| `process_manager.py` | M01-3,8 | 노드 프로세스 관리, psutil 모니터링, emergency_stop_all |
| `launch_parser.py` | M01-4 | .launch.py AST 파싱, .launch.xml 파싱, ExcuteProcess 오타 치환 |
| `ros2_introspector.py` | M02 | rclpy MultiThreadedExecutor, 노드/토픽/엔드포인트 폴링 |
| `qos_analyzer.py` | M02-4 | BEST_EFFORT↔RELIABLE, VOLATILE↔TRANSIENT_LOCAL 비호환 감지 |
| `topic_manager.py` | M02-1~3 | Hz/BW 측정, Throttle Queue (20Hz drop-old), 동적 타입 로드, Image/PointCloud2 다운샘플 |
| `param_manager.py` | M03-1~3 | list/get/describe_parameters, /parameter_events 구독, set/atomic, SQLite 히스토리, YAML 저장/로드 |
| `service_manager.py` | M04-1,1b | 서비스 목록, 동적 타입 로드, call_async + asyncio.wait_for 타임아웃, SQLite 히스토리 |
| `action_manager.py` | M04-3,3b | ActionClient, Goal 전송/추적, Feedback 콜백, 실행 타임아웃 자동 Cancel, SQLite 히스토리 |

### 3.3 ui/panels — 구현 완료 파일

| 파일 | 마일스톤 | 핵심 기능 |
|------|----------|-----------|
| `env_panel.py` | M00-7,8,13 | 4-STEP 환경 설정 UI, 환경 검증 6항목, DOMAIN ID 원클릭 변경 |
| `build_panel.py` | M01-5 | 패키지 체크박스, ANSI 로그, 에러 트리 (더블클릭→VS Code), watch mode 토글 |
| `run_panel.py` | M01-6 | ros2 run/launch GUI, 실행 중 노드 테이블 (PID/CPU/MEM/종료) |
| `node_panel.py` | M01-7 | 노드 목록, 6가지 인트로스펙션 트리 (M02 연결 준비 완료) |
| `topic_panel.py` | M02-5,6 | 토픽 테이블+필터, 발행자/구독자 엔드포인트+QoS 상세, 메시지 뷰어/플롯/발행 탭 |
| `param_panel.py` | M03-6 | 노드 선택, 파라미터 목록, PID 슬라이더 탭, YAML 저장/로드 |
| `service_panel.py` | M04-2 | 서비스 드롭다운, JSON Request, 스피너, ⏱ 타임아웃 경고, 히스토리 |
| `action_panel.py` | M04-4 | 상태 머신 시각화 (7가지), Feedback 플롯, Result 표시, 히스토리 |

### 3.4 ui/widgets — 구현 완료 파일

| 파일 | 마일스톤 | 핵심 기능 |
|------|----------|-----------|
| `m00_widgets.py` | M00-4~6 | PlatformSelector (카드 4종), DomainIdEditor (슬라이더), AliasPreview (bash 하이라이팅) |
| `qos_badge.py` | M02-9 | REL\|VOL\|L10 배지 위젯, 색상 구분 |
| `realtime_plot.py` | M02-7 | pyqtgraph 30Hz 렌더링, 다중 시리즈, float 필드 자동 감지 |
| `topic_publisher.py` | M02-8 | 메시지 필드 자동 생성, 1회/주기 발행 |
| `param_editor.py` | M03-4 | DOUBLE/INTEGER/BOOL/STRING/ARRAY 타입별 위젯, 배열 편집 다이얼로그 |
| `pid_slider_widget.py` | M03-5 | angular/linear P/I/D 6개 슬라이더, 범위 조절, 실시간 적용 |
| `history_table.py` | M03-7 | 범용 히스토리 테이블, 필터/정렬/CSV 내보내기 |

### 3.5 ui/main_window.py (M00-9,10)

- QMainWindow + QDockWidget 패널 시스템
- 상단 툴바: 프로파일 드롭다운, DOMAIN ID 빠른 변경, 🛑 Kill Switch
- 하단 상태 표시줄: 프로파일명, DOMAIN, venv, 소싱 상태, 노드 수

### 3.6 로그 파일

| 파일 | 내용 |
|------|------|
| `logs/M00_environment_setup_2026-03-18.md` | M00 구현 완료 로그 |
| `logs/M01_build_run_panel_2026-03-18.md` | M01 구현 완료 로그 |
| `logs/M02_topic_panel_2026-03-18.md` | M02 구현 완료 로그 |
| `logs/M03_param_panel_2026-03-18.md` | M03 구현 완료 로그 |
| `logs/M04_service_action_panel_2026-03-18.md` | M04 구현 완료 로그 |

---

## 4. 전체 파일 구조 (현재 상태)

```
~/ROSForge/
├── main.py
├── requirements.txt
├── setup.py
├── setup_structure.py
├── README.md
│
├── logs/
│   ├── M00_environment_setup_2026-03-18.md      ✅
│   ├── M01_build_run_panel_2026-03-18.md         ✅
│   ├── M02_topic_panel_2026-03-18.md             ✅
│   ├── M03_param_panel_2026-03-18.md             ✅
│   └── M04_service_action_panel_2026-03-18.md    ✅
│
├── rosforge/
│   ├── __init__.py
│   │
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── ros2_adapter.py          ✅ M00
│   │   ├── environment_manager.py   ✅ M00
│   │   ├── bashrc_manager.py        ✅ M00
│   │   ├── profile_manager.py       ✅ M00
│   │   ├── build_manager.py         ✅ M01
│   │   ├── process_manager.py       ✅ M01
│   │   ├── launch_parser.py         ✅ M01
│   │   ├── ros2_introspector.py     ✅ M02
│   │   ├── qos_analyzer.py          ✅ M02
│   │   ├── topic_manager.py         ✅ M02
│   │   ├── param_manager.py         ✅ M03
│   │   ├── service_manager.py       ✅ M04
│   │   ├── action_manager.py        ✅ M04
│   │   ├── log_manager.py           ⬜ M05
│   │   ├── lifecycle_manager.py     ⬜ M09
│   │   ├── tf_manager.py            ⬜ M06
│   │   ├── bag_manager.py           ⬜ M09
│   │   └── qos_analyzer.py          ✅ M02
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py           ✅ M00
│   │   ├── status_bar.py            ⬜ 스텁
│   │   │
│   │   ├── panels/
│   │   │   ├── __init__.py
│   │   │   ├── env_panel.py         ✅ M00
│   │   │   ├── build_panel.py       ✅ M01
│   │   │   ├── run_panel.py         ✅ M01
│   │   │   ├── node_panel.py        ✅ M01
│   │   │   ├── topic_panel.py       ✅ M02
│   │   │   ├── param_panel.py       ✅ M03
│   │   │   ├── service_panel.py     ✅ M04
│   │   │   ├── action_panel.py      ✅ M04
│   │   │   ├── log_panel.py         ⬜ M05
│   │   │   ├── interface_panel.py   ⬜ M05
│   │   │   ├── map2d_panel.py       ⬜ M06
│   │   │   ├── tf_panel.py          ⬜ M06
│   │   │   ├── graph_panel.py       ⬜ M07
│   │   │   ├── terminal_panel.py    ⬜ M07
│   │   │   ├── lifecycle_panel.py   ⬜ M09
│   │   │   └── bag_panel.py         ⬜ M09
│   │   │
│   │   └── widgets/
│   │       ├── __init__.py
│   │       ├── m00_widgets.py        ✅ M00
│   │       ├── qos_badge.py          ✅ M02
│   │       ├── realtime_plot.py      ✅ M02
│   │       ├── topic_publisher.py    ✅ M02
│   │       ├── param_editor.py       ✅ M03
│   │       ├── pid_slider_widget.py  ✅ M03
│   │       ├── history_table.py      ✅ M03
│   │       ├── lifecycle_state_widget.py ⬜ M09
│   │       └── (기타 스텁들)
│   │
│   ├── db/                          ← rosforge.db (SQLite, 자동 생성)
│   ├── assets/dark_theme.qss
│   └── config/projects/, layouts/
│
├── tests/unit/
│   ├── test_environment_manager.py
│   ├── test_bashrc_manager.py
│   └── test_profile_manager.py
│
└── ~/.rosforge/                     ← 사용자 설정
    ├── projects/
    │   ├── ros2_study.yaml
    │   └── ghost5.yaml
    └── layouts/
```

---

## 5. 마일스톤 진행 현황

```
M00  환경 설정          ██████ 21/21  ✅ 완료
M01  Build & Run        ██████ 44/44  ✅ 완료
M02  Topic Panel        ██████ 57/57  ✅ 완료
M03  Parameter Panel    ██████ 완료   ✅ 완료
M04  Service & Action   ██████ 완료   ✅ 완료
─────────────────────────────────────────
M05  Log & Interface    ░░░░░░        ⬜ 미구현
M06  2D Map & TF        ░░░░░░        ⬜ 미구현
M07  Node Graph & Term  ░░░░░░        ⬜ 미구현
M08  Launch File GUI    ░░░░░░        ⬜ 미구현
M09  Lifecycle & Bag    ░░░░░░        ⬜ 미구현
M10  Layout & Preset    ░░░░░░        ⬜ 미구현
```

---

## 6. 핵심 구현 규칙 (공통)

| 규칙 | 내용 |
|------|------|
| colcon 빌드 환경 | `build_colcon_env()` — venv PATH 자동 제거 |
| ros2 실행 환경 | `build_ros2_env()` — sourced env 주입 |
| 빌드 후 캐시 | `invalidate_cache()` 자동 호출 |
| rclpy 스레드 | MultiThreadedExecutor + 별도 스레드 spin() |
| UI Throttling | asyncio.Queue drop-old, 기본 20Hz 플러시 |
| 서비스 타임아웃 | asyncio.wait_for(), 기본 5초, 설정 가능 |
| 액션 타임아웃 | send 10초 / exec 60초, 초과 시 자동 Cancel |
| 배포판 추상화 | ros2_adapter.py — Jazzy/Humble 분기 |
| Global Kill Switch | emergency_stop_all() SIGTERM→1s→SIGKILL |
| SQLite 히스토리 | param_history, service_history, action_history |

---

## 7. 다음 세션 작업 계획

### M05 — Log & Interface Browser

| 태스크 | 파일 |
|--------|------|
| M05-1,2 | `backend/log_manager.py` — /rosout 구독, SQLite 저장, 로거 레벨 변경 |
| M05-3,4 | `ui/panels/log_panel.py` — 통합 로그 뷰어, 레벨 필터, 색상 구분 |
| M05-5 | `backend/ros2_introspector.py` 확장 — 인터페이스 목록/정의 조회, TTL 캐싱 |
| M05-6 | `ui/panels/interface_panel.py` — 패키지 트리, 필드 정의 표시 |

### M06 — 2D Map & TF Panel

| 태스크 | 파일 |
|--------|------|
| M06-1 | `backend/tf_manager.py` — tf2_ros Buffer, 프레임 관리 |
| M06-2,3 | `ui/panels/map2d_panel.py` — Canvas 2D 맵, 경로 트레일 |
| M06-4,5,6 | `ui/panels/tf_panel.py` — D3.js 계층 트리, 고아 프레임 감지 |

---

*작성: gjkong | 2026-03-18*  
*다음 세션 시작점: M05 — Log & Interface Browser*
