---
title: "ROSForge — 구축 계획서"
date: 2026-03-21
draft: true
tags: ["dev-tools", "pyqt6", "rosforge"]
categories: ["dev-tools"]
description: "**프로젝트명**: ROSForge — ROS2 Unified Development & Monitoring Platform **홈 폴더**: `~/ROSForge/` **작성일**: 2026-03-18"
---

# ROSForge — 구축 계획서

**프로젝트명**: ROSForge — ROS2 Unified Development & Monitoring Platform  
**홈 폴더**: `~/ROSForge/`  
**작성일**: 2026-03-18  
**버전**: v1.1  
**작성자**: gjkong  
**기준 문서**: ROSForge_research.md v2.0

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-03-18 | 초안 작성 |
| v1.1 | 2026-03-18 | 성능 최적화(M02), 환경 격리(M00/M01), 빌드 로그 파싱(M01), 타임아웃 처리(M04), TF 트리 시각화 보완(M06), 배포판 추상화 계층(공통), Global Kill Switch(M01), 레이아웃 저장(M10) 반영 |

---

## 목차

1. [프로젝트 개요 및 목표](#1-프로젝트-개요-및-목표)
2. [전체 아키텍처 설계](#2-전체-아키텍처-설계)
3. [프로젝트 폴더 구조](#3-프로젝트-폴더-구조)
4. [기술 스택 확정](#4-기술-스택-확정)
5. [마일스톤 전체 로드맵](#5-마일스톤-전체-로드맵)
6. [M00 — 환경 설정 (Environment Setup)](#6-m00--환경-설정)
7. [M01 — Build & Run Panel](#7-m01--build--run-panel)
8. [M02 — Topic Panel](#8-m02--topic-panel)
9. [M03 — Parameter Panel](#9-m03--parameter-panel)
10. [M04 — Service & Action Panel](#10-m04--service--action-panel)
11. [M05 — Log & Interface Browser](#11-m05--log--interface-browser)
12. [M06 — 2D Map & TF Panel](#12-m06--2d-map--tf-panel)
13. [M07 — Node Graph & Terminal](#13-m07--node-graph--terminal)
14. [M08 — Launch File GUI](#14-m08--launch-file-gui)
15. [M09 — Lifecycle & Bag Panel](#15-m09--lifecycle--bag-panel)
16. [M10 — Layout & Preset](#16-m10--layout--preset)
17. [공통 개발 규칙](#17-공통-개발-규칙)
18. [완료 조건 체크리스트](#18-완료-조건-체크리스트)

---

## 1. 프로젝트 개요 및 목표

### 1.1 한 줄 정의

ROS2 개발의 **환경 설정 → 빌드 → 실행 → 실시간 모니터링 → 파라미터 수정 → 시각화 → 로깅**을 단 하나의 PyQt6 데스크톱 앱으로 처리하는 통합 도구.

### 1.2 해결하는 문제

| 현재 고통 | ROSForge 해결책 |
|-----------|-----------------|
| `.bashrc` 수동 편집, `source` 반복 | GUI에서 플랫폼 선택 → 버튼 클릭으로 `.bashrc` 자동 적용 |
| `colcon build` + 환경 소싱 반복 | Build Panel에서 빌드 → 자동 재소싱 |
| 여러 터미널에서 노드 개별 실행 | Run Panel에서 일괄 실행/종료 + **Global Kill Switch** |
| rqt/rviz2/gazebo 분산 실행 | 모든 패널이 하나의 창 안에 통합 |
| `ros2 param set` CLI 반복 | 슬라이더/입력창으로 실시간 수정 + 히스토리 |
| 토픽 주파수/대역폭 확인 불편 | Topic Panel에서 Hz/KB 실시간 표시 + **Throttling으로 UI 안정성 보장** |
| 라이프사이클 노드 제어 불편 | Lifecycle Panel에서 버튼 한 번으로 상태 전환 |
| 프로젝트 전환 시 환경 변수 수동 변경 | 프로파일 전환 → **ROS_DOMAIN_ID 원클릭 변경 + subprocess env 즉시 반영** |
| 빌드 실패 원인 파악 어려움 | **빌드 로그 에러 파싱 → 코드 라인 직접 이동 + 해결책 제안** |

### 1.3 지원 플랫폼

| 플랫폼 | 설명 | ROS_DOMAIN_ID | RMW | venv |
|--------|------|:---:|------|:---:|
| **ROS2 Basic (PC)** | 교재 기초/실전 실습 | 13 | fastrtps | 선택 |
| **Raspberry Pi** | RPi 하드웨어 개발 | 13 | fastrtps | OFF |
| **GHOST-5 (Swarm)** | 스웜 로봇 개발 | 42 | zenoh | OFF |
| **Custom** | 사용자 직접 설정 | 입력 | 선택 | 선택 |

---

## 2. 전체 아키텍처 설계

```
┌────────────────────────────────────────────────────────────────────┐
│                   ROSForge Frontend  (PyQt6)                        │
│  ~/ROSForge/rosforge/ui/                                            │
│                                                                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │  Env &  │ │Build &  │ │ Topic / │ │ Service │ │  3D / Plot  │  │
│  │ Bashrc  │ │  Run    │ │  Param  │ │ Action  │ │  Visualizer │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │ Interf  │ │   Log   │ │TF Tree  │ │  Node   │ │  Terminal   │  │
│  │ Browser │ │ Viewer  │ │  Panel  │ │  Graph  │ │    Panel    │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Lifecycle Panel  │  Bag Panel  │  2D Map Panel             │   │
│  └─────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬────────────────────────────────────┘
                                │  rclpy IPC / WebSocket
┌───────────────────────────────┴────────────────────────────────────┐
│                    ROSForge Backend                                  │
│  ~/ROSForge/rosforge/backend/                                        │
│                                                                     │
│  EnvironmentManager  BashrcManager  ProfileManager  ColconManager   │
│  ROS2Introspector    TopicManager   ParamManager    ServiceManager  │
│  ActionManager       LifecycleManager  TFManager    LogManager      │
│  BagManager          QoSAnalyzer    LaunchParser    ProcessManager  │
└───────────────────────────────┬────────────────────────────────────┘
                                │  DDS / rmw (fastrtps / zenoh)
┌───────────────────────────────┴────────────────────────────────────┐
│                      ROS2 Runtime                                    │
│   Nodes · Topics · Services · Actions · TF · Parameters · Logs      │
└────────────────────────────────────────────────────────────────────┘
```

### 2.1 핵심 설계 원칙

- **EnvironmentManager가 모든 subprocess의 env를 책임진다** — `bash -c "source ... && env"` 패턴으로 sourced 환경을 Python dict로 추출, 빌드/실행 모든 프로세스에 주입
- **colcon build는 반드시 venv 비활성화 env로 실행** — `build_colcon_env()`에서 VIRTUAL_ENV, venv PATH 자동 제거
- **빌드 완료 후 자동 재소싱** — `invalidate_cache()` 호출 → 다음 실행 시 새 환경 적용
- **rclpy는 별도 스레드 executor** — `MultiThreadedExecutor` + `asyncio` 분리로 GIL 충돌 방지
- **모든 히스토리는 SQLite에 저장** — 파라미터/서비스/액션 변경 이력 영구 보관
- **UI Throttling 필수** — 고주파 토픽 직접 수신 시 UI 갱신을 초당 10~30회로 제한, 프리징 방지
- **ROS2 배포판 추상화 계층** — `ROS2Adapter` 인터페이스로 Jazzy/Humble/Rolling API 차이를 래핑, 배포판 교체 시 어댑터만 교체
- **Global Kill Switch** — 메인 툴바의 비상 정지 버튼으로 실행 중인 모든 노드/런치 프로세스를 즉시 안전 종료

---

## 3. 프로젝트 폴더 구조

```
~/ROSForge/
├── rosforge/
│   ├── main.py                          # 진입점 — QApplication + MainWindow
│   │
│   ├── backend/                         # ROS2 연동 + 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── ros2_adapter.py              # ★ ROS2 배포판 추상화 계층 (Jazzy/Humble/Rolling)
│   │   ├── environment_manager.py       # source 체인 → env dict 생성
│   │   ├── bashrc_manager.py            # .bashrc 블록 삽입/갱신/충돌 감지
│   │   ├── profile_manager.py           # 프로파일 YAML 저장/불러오기
│   │   ├── build_manager.py             # colcon build 자동화 + watch mode + 에러 파싱
│   │   ├── launch_parser.py             # .launch.py / .launch.xml 파싱
│   │   ├── process_manager.py           # subprocess 노드 프로세스 생명주기 + Kill Switch
│   │   ├── ros2_introspector.py         # 노드/토픽/서비스/액션 전체 인트로스펙션
│   │   ├── topic_manager.py             # 토픽 구독/발행 + Hz/BW 측정 + Throttling
│   │   ├── param_manager.py             # 파라미터 CRUD + describe + events
│   │   ├── service_manager.py           # 서비스 클라이언트 + 응답시간 + 타임아웃 + 히스토리
│   │   ├── action_manager.py            # 액션 클라이언트 + Goal 상태 추적 + 타임아웃
│   │   ├── lifecycle_manager.py         # 라이프사이클 노드 감지 + 상태 전환
│   │   ├── tf_manager.py                # tf2_ros Buffer + 프레임 관리
│   │   ├── log_manager.py               # /rosout 구독 + SQLite 저장 + 레벨 변경
│   │   ├── bag_manager.py               # rosbag2 녹화/재생 subprocess 래퍼
│   │   └── qos_analyzer.py              # QoS 호환성 분석 + 경고 생성
│   │
│   ├── ui/                              # PyQt6 UI 레이어
│   │   ├── __init__.py
│   │   ├── main_window.py               # QMainWindow + QDockWidget 패널 시스템
│   │   ├── status_bar.py                # 하단 상태 표시줄
│   │   │
│   │   ├── panels/                      # 각 기능 패널
│   │   │   ├── __init__.py
│   │   │   ├── env_panel.py             # M00: 환경 설정 + .bashrc 관리
│   │   │   ├── build_panel.py           # M01: colcon 빌드 + 빌드 로그
│   │   │   ├── run_panel.py             # M01: 노드/launch 실행 + 프로세스 관리
│   │   │   ├── node_panel.py            # 노드 목록 + 6가지 인트로스펙션 상세
│   │   │   ├── topic_panel.py           # M02: 토픽 목록+Hz+BW+QoS+뷰어+플롯
│   │   │   ├── param_panel.py           # M03: 파라미터 편집 + PID 슬라이더 + 히스토리
│   │   │   ├── service_panel.py         # M04: 서비스 호출 GUI + 히스토리
│   │   │   ├── action_panel.py          # M04: 액션 Goal/Feedback/Result + 상태머신
│   │   │   ├── lifecycle_panel.py       # M09: 라이프사이클 노드 상태 + 전환 버튼
│   │   │   ├── interface_panel.py       # M05: msg/srv/action 브라우저
│   │   │   ├── log_panel.py             # M05: 통합 로그 뷰어 + 레벨 변경
│   │   │   ├── map2d_panel.py           # M06: Turtlesim 2D 포즈 뷰어 + 트레일
│   │   │   ├── tf_panel.py              # M06: TF 트리 D3.js + 상대 변환
│   │   │   ├── graph_panel.py           # M07: 노드 그래프 토폴로지 (D3.js)
│   │   │   ├── bag_panel.py             # M09: bag 녹화/재생 UI
│   │   │   └── terminal_panel.py        # M07: 내장 터미널 (QProcess)
│   │   │
│   │   └── widgets/                     # 재사용 공통 위젯
│   │       ├── __init__.py
│   │       ├── platform_selector.py     # 플랫폼 선택 카드 위젯 (4종)
│   │       ├── alias_preview.py         # alias 코드 실시간 미리보기
│   │       ├── domain_id_editor.py      # DOMAIN ID 숫자 입력 + 슬라이더
│   │       ├── pid_slider_widget.py     # PID P/I/D 6개 슬라이더 위젯
│   │       ├── param_editor.py          # 파라미터 타입별 위젯 (배열 포함)
│   │       ├── topic_publisher.py       # 메시지 필드 자동 생성 발행 폼
│   │       ├── realtime_plot.py         # pyqtgraph 래퍼 (실시간 플롯)
│   │       ├── qos_badge.py             # QoS 프로파일 배지 위젯
│   │       ├── history_table.py         # 히스토리 테이블 공통 위젯
│   │       └── lifecycle_state_widget.py # 라이프사이클 상태 다이어그램 위젯
│   │
│   ├── db/                              # SQLite 데이터베이스
│   │   └── rosforge.db                  # 로그/히스토리/파라미터 변경 이력
│   │
│   └── assets/
│       ├── dark_theme.qss               # Qt 다크 테마
│       └── icons/                       # 패널 아이콘
│
├── ~/.rosforge/                         # 사용자 설정 (홈 디렉토리)
│   ├── projects/                        # 프로파일 YAML
│   │   ├── ros2_study.yaml
│   │   └── ghost5.yaml
│   └── layouts/                         # 패널 레이아웃 저장
│
├── setup.py
├── requirements.txt
└── README.md
```

---

## 4. 기술 스택 확정

### 4.1 Frontend

| 항목 | 기술 | 버전 |
|------|------|------|
| UI 프레임워크 | PyQt6 | ≥ 6.6.0 |
| 웹뷰 (3D/그래프) | PyQt6-WebEngine | ≥ 6.6.0 |
| 실시간 플롯 | pyqtgraph | ≥ 0.13.0 |
| 노드 그래프 / TF 트리 | D3.js (via WebEngine) | CDN |
| 3D 시각화 | Three.js (via WebEngine) | CDN |
| 스타일링 | Qt Style Sheets | Dark Theme |
| 레이아웃 | QDockWidget 패널 시스템 | — |

### 4.2 Backend

| 항목 | 기술 | 버전 |
|------|------|------|
| ROS2 클라이언트 | rclpy | Jazzy |
| 비동기 처리 | asyncio + MultiThreadedExecutor | Python 3.10+ |
| 프로세스 모니터링 | psutil | ≥ 5.9 |
| 파일 감시 | watchdog | ≥ 4.0 |
| 데이터 검증 | pydantic v2 | ≥ 2.0 |
| 설정 파일 | PyYAML | ≥ 6.0 |
| DB | aiosqlite | ≥ 0.19 |
| bag 파싱 | rosbags | ≥ 0.9 |
| TF 계산 | tf-transformations | ≥ 1.0 |

### 4.3 ROS2 패키지 의존성

| 패키지 | 용도 |
|--------|------|
| `rcl_interfaces` | ParameterEvent, Log, SetParameters, DescribeParameters |
| `lifecycle_msgs` | ChangeState, GetState, TransitionEvent |
| `action_msgs` | GoalStatus, GoalInfo |
| `tf2_ros` | Buffer, TransformListener |
| `tf2_msgs` | TFMessage |
| `foxglove_bridge` | 3D 시각화 WebSocket |
| `rosbridge_server` | 웹 모니터 지원 |
| `rosbag2_py` | bag 녹화/재생 |
| `sensor_msgs`, `nav_msgs`, `geometry_msgs`, `std_msgs` | 교재 기본 메시지 |

### 4.4 requirements.txt

```
PyQt6>=6.6.0
PyQt6-WebEngine>=6.6.0
pyqtgraph>=0.13.0
pydantic>=2.0
watchdog>=4.0
psutil>=5.9
rosbags>=0.9
PyYAML>=6.0
aiosqlite>=0.19
tf-transformations>=1.0
```

---

## 5. 마일스톤 전체 로드맵

```
M00  환경 설정          ██████  (선행 필수 — 모든 마일스톤의 기반)
  └→ M01  Build & Run  ██████
       └→ M02  Topic   ██████
            └→ M03  Param   ██████
                 └→ M04  Svc/Action  ██████
                      └→ M05  Log/Interface  ██████
                           └→ M06  2D Map/TF  ██████
                                └→ M07  Graph/Terminal  ██████
                                     └→ M08  Launch GUI  ██████
                                          └→ M09  Lifecycle/Bag  ██████
                                               └→ M10  Layout/Preset  ██████
```

### 마일스톤 요약표

| 마일스톤 | 핵심 기능 | 기능 코드 | 교재 커버 시나리오 |
|----------|-----------|-----------|-------------------|
| **M00** | 환경 설정 GUI, .bashrc 적용, 프로파일 | F-00~F-00b, F-18~19 | bashrc 편 전체 |
| **M01** | colcon build, ros2 run/launch, 노드 실행 | F-01~06c | ros2_basic 실행 |
| **M02** | 토픽 목록/뷰어/플롯/발행, Hz/BW/QoS | F-07~10, F-07a~07d | Publisher/Subscriber |
| **M03** | 파라미터 편집, PID 슬라이더, 히스토리 | F-11~13, F-11a~12b | PID 튜닝, dist_turtle |
| **M04** | 서비스 호출, 액션 Goal/Feedback/Result | F-14~15d | multi_spawn, dist_turtle 액션 |
| **M05** | 로그 뷰어, 인터페이스 브라우저 | F-16~17c | 전체 교재 디버깅 |
| **M06** | Turtlesim 2D 맵, TF 트리 | F-20, F-21~21a | TF 튜토리얼 |
| **M07** | 노드 그래프, 내장 터미널 | F-22~22b, F-25 | domain test, 복합 예제 |
| **M08** | Launch 파일 파싱 GUI | F-05 확장, F-24 | launch 파일 전체 |
| **M09** | 라이프사이클 제어, bag 녹화/재생 | F-26a~26f | Nav2, Gazebo |
| **M10** | 레이아웃 저장/불러오기, 프리셋 | F-30, 레이아웃 | 전체 |

---

## 6. M00 — 환경 설정

> **선행 조건**: 없음 (첫 번째 마일스톤)  
> **완료 후**: M01 진행 가능

### 6.1 구현 목표

버튼 클릭만으로 `.bashrc`에 ROS2 alias가 적용되고, 결과가 터미널 패널에 즉시 출력된다.  
모든 후속 마일스톤의 빌드/실행/모니터링이 이 환경 위에서 동작한다.

### 6.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M00-1** | `backend/environment_manager.py` | `bash -c "source ... && env"` 패턴으로 sourced 환경 Python dict 추출. `build_ros2_env()`, `build_colcon_env()` (venv PATH 제거), `invalidate_cache()` |
| **M00-2** | `backend/bashrc_manager.py` | `# ── ROSForge START/END ──` 블록 삽입/갱신. 백업 (`~/.bashrc.bak`) 자동 생성. 기존 source 충돌 감지 + 경고 |
| **M00-3** | `backend/profile_manager.py` | 프로파일 YAML 스키마 정의 (`~/.rosforge/projects/*.yaml`). 저장/불러오기/삭제. 기본 프로파일 2종 (ros2_study, ghost5) |
| **M00-4** | `ui/widgets/platform_selector.py` | 플랫폼 카드 위젯 4종 (ROS2 Basic / RPi / GHOST-5 / Custom). 선택 시 STEP 3 미리보기 즉시 갱신 |
| **M00-5** | `ui/widgets/domain_id_editor.py` | ROS_DOMAIN_ID 숫자 입력창 (0~232) + 슬라이더. 값 변경 시 미리보기 갱신 |
| **M00-6** | `ui/widgets/alias_preview.py` | STEP 2 값 변경마다 `.bashrc` 블록 실시간 렌더링. 코드 하이라이팅, [복사] 버튼 |
| **M00-7** | `ui/panels/env_panel.py` | 4-STEP UI 통합. [✅ .bashrc에 적용] 버튼 → BashrcManager 호출 → 터미널 패널 출력. [🔍 환경 검증] 버튼 |
| **M00-8** | `ui/panels/env_panel.py` (검증) | 환경 검증 체크리스트 실행: ros2 CLI / colcon / rclpy import / turtlesim / foxglove_bridge / rosbridge_suite |
| **M00-9** | `ui/main_window.py` (상태 표시줄) | 상단 표시줄: 프로파일명, DOMAIN ID, venv ON/OFF, 소싱 상태, 실행 중 노드 수 |
| **M00-10** | `ui/main_window.py` (드롭다운) | 프로파일 전환 드롭다운. 전환 시 실행 중 노드 경고 후 환경 재적용 |
| **M00-11** | `backend/bashrc_manager.py` | 기존 `.bashrc`에 `source /opt/ros/jazzy/setup.bash` 중복 시 경고 다이얼로그. 사용자 선택: 덮어쓰기 / 주석 처리 / 취소 |
| **M00-12** | `backend/build_manager.py` 연동 | 빌드 완료 후 `env_manager.invalidate_cache()` 자동 호출 → 다음 실행 시 새 환경 적용 |
| **M00-13** | `ui/panels/env_panel.py` + `backend/process_manager.py` | **ROS_DOMAIN_ID 원클릭 변경**: 상단 DOMAIN ID 입력창 수정 → [적용] 버튼 클릭 → `.bashrc` 블록 갱신 + `ProcessManager`의 모든 신규 subprocess env에 즉시 반영. 이미 실행 중인 노드는 재시작 안내 표시 |

### 6.3 .bashrc 생성 블록 형식

```bash
# ── ROSForge START ──────────────────────────────────────
# 이 블록은 ROSForge가 자동 관리합니다. 수동 편집 시 주의.
# Generated: YYYY-MM-DD | Profile: <profile_name>

alias sb="source ~/.bashrc; echo \"bashrc is reloded\""

ID=<DOMAIN_ID>
alias ros_domain="export ROS_DOMAIN_ID=$ID; echo \"ROS_DOMAIN_ID is set to $ID !\""

# [venv 사용 시만 포함]
alias active_venv_jazzy="source ~/venv/jazzy/bin/activate; echo \"Venv Jazzy is activated.\""
alias jazzy="active_venv_jazzy; source /opt/ros/jazzy/setup.bash; ros_domain; echo \"ROS2 Jazzy is activated!\""

# [venv 미사용 시]
# alias jazzy="source /opt/ros/jazzy/setup.bash; ros_domain; echo \"ROS2 Jazzy is activated!\""

# [GHOST-5 플랫폼 시 추가]
# export RMW_IMPLEMENTATION=rmw_zenoh_cpp

ws_setting() { jazzy; source ~/$1/install/local_setup.bash; echo "$1 workspace is activated."; }
get_status() { ... }

alias <ws_name>="ws_setting \"<ws_name>\""
# ── ROSForge END ────────────────────────────────────────
```

### 6.4 프로파일 YAML 스키마

```yaml
profile_name: "ros2_study"
description: "ROS2 기초 교재 실습"
platform: "ros2_basic"           # ros2_basic | rpi | ghost5 | custom
created_at: "2026-03-18"

ros2:
  distro: "jazzy"
  setup_path: "/opt/ros/jazzy/setup.bash"

python:
  use_venv: true
  venv_path: "~/venv/jazzy"

workspace:
  root: "~/ros2_study"
  name: "ros2_study"
  overlay_stack:
    - "/opt/ros/jazzy/setup.bash"
    - "~/ros2_study/install/local_setup.bash"

environment:
  ROS_DOMAIN_ID: 13
  ROS_LOCALHOST_ONLY: 0
  RMW_IMPLEMENTATION: "rmw_fastrtps_cpp"
  RCUTILS_COLORIZED_OUTPUT: "1"

build:
  default_args: ["--symlink-install"]
  auto_venv_deactivate: true

bashrc:
  auto_apply: true
  backup_before_write: true

launch_presets: []
```

### 6.5 M00 완료 조건

- [ ] `ros2 topic list` 실행 시 정상 결과 반환 (소싱 확인)
- [ ] `colcon build` 시 venv 비활성화 env 자동 적용 확인
- [ ] 프로파일 전환 후 `ROS_DOMAIN_ID` 즉시 반영 확인
- [ ] **ROS_DOMAIN_ID 원클릭 변경 → 신규 subprocess env에 즉시 반영 확인**
- [ ] 환경 검증 6개 항목 모두 체크 동작 확인
- [ ] `.bashrc`에 ROSForge 블록 삽입/갱신 정상 동작
- [ ] 기존 source 충돌 감지 및 경고 다이얼로그 동작
- [ ] 터미널 패널에 적용 결과 출력 확인

---

## 7. M01 — Build & Run Panel

> **선행 조건**: M00 완료 (EnvironmentManager, ProfileManager)

### 7.1 구현 목표

colcon 빌드와 노드 실행을 GUI에서 처리한다. 빌드 로그를 실시간으로 확인하고, 여러 노드를 동시에 실행/종료할 수 있다.

### 7.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M01-1** | `backend/build_manager.py` | `asyncio.create_subprocess_exec()` 로 colcon build 실행. `build_colcon_env()` env 주입. 실시간 로그 스트리밍. `--symlink-install` 기본 옵션 |
| **M01-2** | `backend/build_manager.py` | `package.xml` 의존성 파싱 → 빌드 순서 자동 정렬 (msgs 패키지 먼저). `watchdog`으로 소스 파일 변경 감지 → watch mode 자동 빌드 |
| **M01-2b** | `backend/build_manager.py` | **빌드 로그 에러 파싱**: 빌드 실패 시 정규식으로 `파일경로:라인번호: error:` 패턴 추출. 에러 목록을 클릭 가능한 링크로 표시. 클릭 시 해당 파일/라인으로 이동(또는 VS Code `code -g` 실행). 공통 에러 유형 → 해결책 텍스트 매핑 테이블 제공 |
| **M01-3** | `backend/process_manager.py` | 노드 프로세스 `dict[name, subprocess]` 관리. 시작/종료/재시작/강제 kill. `psutil`로 PID/CPU/MEM 모니터링. **`emergency_stop_all()` 메서드**: 등록된 모든 subprocess에 SIGTERM → 1초 대기 → 미종료 시 SIGKILL |
| **M01-4** | `backend/launch_parser.py` | `.launch.py` AST 파싱 (Node, ExecuteProcess, IncludeLaunchDescription 추출). `.launch.xml` ElementTree 파싱. `ExcuteProcess` 오타 자동 치환 |
| **M01-5** | `ui/panels/build_panel.py` | 워크스페이스 패키지 트리 표시. 패키지 선택 체크박스. [빌드] 버튼. 빌드 로그 실시간 텍스트 창 (ANSI 컬러 지원). **빌드 실패 시 에러 목록 패널** (파일명:라인 클릭 가능 링크 + 해결책 제안). 빌드 성공/실패 배너 |
| **M01-6** | `ui/panels/run_panel.py` | 패키지/실행파일 드롭다운 (설치된 패키지 자동 스캔). 추가 args 입력창. [실행] 버튼. 실행 중 노드 목록 (PID/CPU/MEM 표시). 개별/일괄 종료 버튼 |
| **M01-7** | `ui/panels/node_panel.py` | 실행 중 노드 목록 실시간 표시. 노드 클릭 시 6가지 인트로스펙션 상세 (Publishers/Subscribers/Service Servers/Service Clients/Action Servers/Action Clients). [종료][재시작][로그 보기] 버튼 |
| **M01-8** | `ui/main_window.py` | **Global Kill Switch (🛑 비상 정지)**: 메인 툴바 우측 상단 빨간 버튼. 클릭 시 확인 다이얼로그 → `process_manager.emergency_stop_all()` 호출 → 모든 노드/런치 즉시 종료 → 상태 표시줄에 결과 출력 |

### 7.3 빌드 의존성 자동 정렬 로직

```
1. src/ 하위 모든 package.xml 스캔
2. <depend> 태그로 의존성 그래프 구성
3. 위상 정렬 (topological sort)
4. msgs/interfaces 패키지가 먼저 오도록 정렬
5. 정렬된 순서로 개별 colcon build 순차 실행
```

### 7.4 M01 완료 조건

- [ ] `my_first_package_msgs` → `my_first_package` 의존성 순서 빌드 확인
- [ ] 빌드 로그 실시간 스트리밍 확인
- [ ] **빌드 실패 시 에러 파일:라인 클릭 링크 표시 확인**
- [ ] **빌드 에러 해결책 제안 텍스트 표시 확인**
- [ ] `turtlesim_node` run → 노드 목록에 표시 확인
- [ ] 여러 노드 동시 실행 + 개별 종료 확인
- [ ] 노드 클릭 시 Publishers/Subscribers 6가지 상세 표시 확인
- [ ] watch mode: `.py` 파일 수정 → 자동 빌드 트리거 확인
- [ ] **🛑 Global Kill Switch 클릭 → 모든 실행 중 노드 즉시 종료 확인**

---

## 8. M02 — Topic Panel

> **선행 조건**: M01 완료

### 8.1 구현 목표

실행 중인 모든 토픽을 실시간으로 모니터링한다. 주파수/대역폭/QoS 상세를 표시하고, 메시지 스트리밍 뷰어와 실시간 플롯, 토픽 직접 발행 기능을 제공한다.

### 8.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M02-1** | `backend/topic_manager.py` | `get_topic_names_and_types()` 1초 폴링. `get_publishers_info_by_topic()` / `get_subscriptions_info_by_topic()` 로 발행자/구독자 엔드포인트 + QoS 조회. `count_publishers()` / `count_subscribers()` |
| **M02-2** | `backend/topic_manager.py` | 토픽 Hz 측정: `create_subscription()` + 수신 카운터 + 1초 타이머로 계산. 토픽 BW 측정: 메시지 직렬화 크기 × Hz |
| **M02-2b** | `backend/topic_manager.py` | **UI Throttling**: 고주파 토픽 구독 시 수신된 메시지를 즉시 UI로 전달하지 않고 `asyncio.Queue` + 별도 타이머(기본 20Hz, 설정 가능 10~30Hz)로 UI 갱신 배치 처리. 큐 오버플로우 시 최신 메시지만 유지(drop old). 메시지 뷰어/플롯/2D 맵 모두 이 경로를 통해 갱신 |
| **M02-2c** | `backend/topic_manager.py` | **대용량 데이터 처리**: `sensor_msgs/Image`, `sensor_msgs/PointCloud2` 등 대용량 메시지는 백엔드에서 downsample(이미지 리사이즈 → numpy, 포인트 클라우드 → stride 샘플링) 후 UI로 전달. 원본 데이터 복사 최소화 (numpy array 뷰 활용) |
| **M02-3** | `backend/topic_manager.py` | 동적 메시지 타입 구독: `rosidl_runtime_py` + `importlib`으로 런타임 타입 로드. 커스텀 msg 포함 모든 타입 지원 |
| **M02-4** | `backend/qos_analyzer.py` | 발행자-구독자 QoS 호환성 분석 (RELIABLE↔BEST_EFFORT, VOLATILE↔TRANSIENT_LOCAL). 불일치 시 경고 생성 |
| **M02-5** | `ui/panels/topic_panel.py` | 토픽 목록 테이블: 이름/타입/Hz/BW/발행자수/구독자수 컬럼. 1초 자동 갱신. 행 클릭 → 상세 드로어(발행자/구독자 엔드포인트 + QoS + 경고) |
| **M02-6** | `ui/panels/topic_panel.py` | 메시지 뷰어 서브패널: JSON 트리 형태로 실시간 스트리밍 (Throttling 적용). 최신 N개 메시지 보관. 특정 필드 값만 추출 표시 |
| **M02-7** | `ui/widgets/realtime_plot.py` | pyqtgraph 기반 실시간 플롯. 토픽 선택 → float32/float64 필드 자동 감지 → 플롯 추가. 다중 토픽 동시 플롯. 스크롤/줌 지원. **Throttling 적용 (최대 30Hz)** |
| **M02-8** | `ui/widgets/topic_publisher.py` | 토픽 발행 GUI: 선택한 타입의 모든 필드를 입력창으로 자동 생성. 발행 주기(Hz) 설정. [1회 발행] / [주기 발행] / [중지] 버튼 |
| **M02-9** | `ui/widgets/qos_badge.py` | QoS 프로파일을 컴팩트하게 표시하는 배지 위젯 (RELIABLE/VOLATILE/KEEP_LAST 등) |

### 8.3 토픽 상세 UI 설계

```
토픽 행 클릭 시 표시:
┌──────────────────────────────────────────────┐
│ 📡 /turtle1/cmd_vel                          │
│ 타입: geometry_msgs/msg/Twist                │
│ Hz: 2.0  │  BW: 0.08 KB/s                   │
│                                              │
│ 발행자 (1)                                   │
│  teleop_turtle [/]  [RELIABLE|VOLATILE|10]  │
│                                              │
│ 구독자 (2)                                   │
│  turtlesim [/]      [RELIABLE|VOLATILE|10]  │
│  _ros2cli_xxx [/]   [BEST_EFFORT|VOLATILE]  │
│  ⚠️ QoS 불일치: RELIABLE ↔ BEST_EFFORT       │
│                                              │
│ [메시지 보기]  [플롯]  [발행]  [녹화]         │
└──────────────────────────────────────────────┘
```

### 8.4 M02 완료 조건

- [ ] 토픽 목록 1초 갱신 확인
- [ ] `/turtle1/pose` Hz 62.5 표시 확인
- [ ] 발행자/구독자 엔드포인트 + QoS 상세 표시 확인
- [ ] QoS 불일치 경고 표시 확인
- [ ] **고주파 토픽(62Hz) 구독 시 UI 프리징 없음 확인 (Throttling 동작)**
- [ ] **UI 갱신 주기 설정 (10~30Hz) 변경 적용 확인**
- [ ] 메시지 JSON 트리 실시간 스트리밍 확인
- [ ] `/turtle1/pose` x/y/theta 실시간 플롯 확인
- [ ] `/goal_pose` 토픽 수동 발행 (Pose 타입 필드 자동 생성) 확인
- [ ] 커스텀 메시지 타입 `/cmd_and_pose` 뷰어 동작 확인

---

## 9. M03 — Parameter Panel

> **선행 조건**: M02 완료

### 9.1 구현 목표

실행 중인 모든 노드의 파라미터를 실시간으로 조회하고, GUI 슬라이더/입력창으로 즉시 수정한다. PID 파라미터 전용 슬라이더와 변경 히스토리를 제공한다.

### 9.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M03-1** | `backend/param_manager.py` | `/<node>/list_parameters` → `/<node>/get_parameters` → `/<node>/describe_parameters` 순차 호출로 파라미터 목록/값/설명/범위 조회 |
| **M03-2** | `backend/param_manager.py` | `/parameter_events` 구독으로 전체 노드 파라미터 변경 실시간 감지. 변경 시 SQLite 히스토리 저장 (타임스탬프, 노드, 파라미터명, 이전값, 새값, 성공/실패) |
| **M03-3** | `backend/param_manager.py` | `/<node>/set_parameters` 서비스 호출로 파라미터 수정. `set_parameters_atomically` 지원. 수정 후 변경 이벤트 확인 |
| **M03-4** | `ui/widgets/param_editor.py` | 타입별 위젯 자동 생성: DOUBLE → 슬라이더+소수점입력창 / INTEGER → 정수입력창+슬라이더 / BOOL → ON/OFF 토글 / STRING → 텍스트 입력창 / ARRAY 타입 → 배열 편집 다이얼로그 |
| **M03-5** | `ui/widgets/pid_slider_widget.py` | PID 전용 위젯: P/I/D 각각 슬라이더 + 입력창 (범위 조절 가능). angular/linear 두 세트 = 6개 슬라이더. 실시간 적용 |
| **M03-6** | `ui/panels/param_panel.py` | 노드 선택 드롭다운 → 파라미터 목록 표시. 각 파라미터: 이름/타입/현재값/설명/범위. [YAML 저장] / [YAML 로드] 버튼 |
| **M03-7** | `ui/widgets/history_table.py` | 파라미터 변경 히스토리 테이블: 시간/노드/파라미터/이전값/새값/결과. 필터/정렬 지원 |

### 9.3 파라미터 타입 → 위젯 매핑

| 파라미터 타입 | 위젯 | 예시 |
|--------------|------|------|
| `PARAMETER_DOUBLE` | 슬라이더 + 소수점 입력창 | `angular_P = 1.0` |
| `PARAMETER_INTEGER` | 정수 입력창 + 슬라이더 | `background_r = 255` (0~255) |
| `PARAMETER_BOOL` | ON/OFF 토글 | `use_sim_time = False` |
| `PARAMETER_STRING` | 텍스트 입력창 | `robot_name = "turtle1"` |
| `PARAMETER_DOUBLE_ARRAY` | 배열 편집 다이얼로그 | `gains = [1.0, 0.5, 0.1]` |
| `PARAMETER_INTEGER_ARRAY` | 배열 편집 다이얼로그 | — |
| `PARAMETER_BOOL_ARRAY` | 체크박스 배열 | — |
| `PARAMETER_STRING_ARRAY` | 리스트 편집 위젯 | — |

### 9.4 M03 완료 조건

- [ ] `dist_turtle_action_server`의 `quatile_time`, `almost_goal_time` 슬라이더 표시 확인
- [ ] 슬라이더 조정 → 즉시 `/parameter_events` 수신 확인
- [ ] `move_turtle` 노드의 angular_P/I/D, linear_P/I/D 6개 슬라이더 동작 확인
- [ ] 파라미터 변경 히스토리 SQLite 저장 확인
- [ ] YAML 파라미터 파일 저장/로드 확인
- [ ] 배열 타입 파라미터 편집 다이얼로그 동작 확인

---

## 10. M04 — Service & Action Panel

> **선행 조건**: M03 완료

### 10.1 구현 목표

서비스 호출 GUI와 액션 Goal 전송/Feedback 모니터링/Result 표시를 제공한다. 상태 머신 시각화와 히스토리 로깅을 포함한다.

### 10.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M04-1** | `backend/service_manager.py` | `get_service_names_and_types()` 로 서비스 목록 조회. `service_is_ready()` 로 서버 존재 확인. `importlib`으로 서비스 타입 동적 로드. `call_async()` 호출 + 응답 시간 측정. SQLite 히스토리 저장 |
| **M04-1b** | `backend/service_manager.py` | **서비스 타임아웃 처리**: `asyncio.wait_for(client.call_async(...), timeout=<N>초)` 적용. 기본 타임아웃 5초, UI에서 설정 가능 (1~60초). 타임아웃 시 `TimeoutError` 캐치 → UI에 "⏱ 응답 없음 (5.0s 초과)" 표시 + 진행 스피너 중단 |
| **M04-2** | `ui/panels/service_panel.py` | 서비스 목록 드롭다운. Request 필드 자동 생성 (타입 분석 → 입력창 생성). **타임아웃 설정 입력창**. [호출] 버튼 → 진행 스피너 → Response 표시 또는 타임아웃 경고. 호출 히스토리 테이블 |
| **M04-3** | `backend/action_manager.py` | `get_action_names_and_types()` 로 액션 목록 조회. `ActionClient`로 Goal 전송. Feedback 콜백 → UI 실시간 업데이트. Goal 상태 추적 (ACCEPTED→EXECUTING→SUCCEEDED/CANCELED/ABORTED). SQLite 히스토리 저장 |
| **M04-3b** | `backend/action_manager.py` | **액션 타임아웃 처리**: Goal 전송 후 `send_goal_timeout`(기본 10초) 내 ACCEPTED 미수신 시 UI 경고. Goal 실행 중 `execution_timeout`(기본 60초, UI 설정 가능) 초과 시 자동 Cancel 요청 + "⏱ 실행 시간 초과, 자동 취소됨" 표시 |
| **M04-4** | `ui/panels/action_panel.py` | 액션 목록 드롭다운 + 서버 활성 상태 표시. Goal 필드 자동 생성. **타임아웃 설정 입력창 (Goal 전송/실행 각각)**. [전송] / [취소] 버튼. Goal 상태 머신 시각화 (현재 상태 하이라이트). Feedback 실시간 표시 + pyqtgraph 플롯. Result 표시. 히스토리 테이블 |

### 10.3 액션 상태 머신 UI

```
Goal 상태 시각화:
[UNKNOWN] → [ACCEPTED] → [EXECUTING] → [SUCCEEDED]
                        ↘ [CANCELING] → [CANCELED]
                        ↘ [ABORTED]

현재 상태: ██ EXECUTING (파란색 하이라이트)
진행률: ██████░░░░ 60%  (remained_dist 기준)
```

### 10.4 M04 완료 조건

- [ ] `multi_spawn` 서비스 호출 (num=5) → Response `x[]`, `y[]`, `theta[]` 표시 확인
- [ ] 서비스 응답 시간 측정 및 표시 확인
- [ ] **서비스 타임아웃: 응답 없는 서버 호출 시 5초 후 "⏱ 응답 없음" 표시 확인**
- [ ] `dist_turtle` 액션 Goal 전송 → Feedback 실시간 표시 확인
- [ ] Feedback `remained_dist` 실시간 플롯 확인
- [ ] 액션 Cancel 동작 확인
- [ ] **액션 실행 타임아웃: 설정 시간 초과 시 자동 Cancel + 경고 표시 확인**
- [ ] Goal 상태 머신 EXECUTING → SUCCEEDED 전환 시각화 확인
- [ ] 서비스/액션 히스토리 SQLite 저장 확인

---

## 11. M05 — Log & Interface Browser

> **선행 조건**: M04 완료

### 11.1 구현 목표

모든 노드의 로그를 통합 수집/필터링/저장하고, 모든 msg/srv/action 인터페이스를 패키지 트리로 탐색할 수 있다.

### 11.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M05-1** | `backend/log_manager.py` | `/rosout` 토픽 구독 (큐 1000). Log 메시지 파싱: stamp/level/name/msg/file/function/line. SQLite 저장. 버퍼 크기 제한으로 과부하 방지 |
| **M05-2** | `backend/log_manager.py` | `/<node>/set_logger_levels` 서비스 호출로 로거 레벨 동적 변경. 노드가 `enable_logger_service=True`인 경우만 가능. 불가 시 UI 경고 표시 |
| **M05-3** | `ui/panels/log_panel.py` | 로그 테이블: 시간/레벨(색상 구분)/노드명/메시지/파일:라인 컬럼. 레벨/노드/키워드 필터. 실시간 자동 스크롤. [저장] 버튼 (.log, .csv). [지우기] 버튼 |
| **M05-4** | `ui/panels/log_panel.py` | 로거 레벨 변경 UI: 노드 선택 드롭다운 → 레벨 선택 (DEBUG/INFO/WARN/ERROR/FATAL) → [적용] 버튼 |
| **M05-5** | `backend/ros2_introspector.py` | `ros2 interface list` subprocess → 전체 인터페이스 목록. `ros2 interface show <type>` → 타입 정의. 결과 캐싱 (TTL 30초) |
| **M05-6** | `ui/panels/interface_panel.py` | 패키지 트리 (QTreeWidget): 패키지 → msg/srv/action 하위 목록. 타입 선택 시 우측에 필드 정의 표시. [검색] 입력창. [토픽 발행에 사용] / [서비스 호출에 사용] 버튼 → 해당 패널 연결 |

### 11.3 로그 레벨 색상 규칙

| 레벨 | 색상 |
|------|------|
| DEBUG | 회색 |
| INFO | 흰색 |
| WARN | 노란색 |
| ERROR | 빨간색 |
| FATAL | 진빨강 + 굵게 |

### 11.4 M05 완료 조건

- [ ] `parameter_callback` 로그 INFO 표시 확인 (file/function/line 포함)
- [ ] 노드별 필터 동작 확인
- [ ] 로그 .csv 저장 확인
- [ ] 로거 레벨 WARN → DEBUG 변경 후 debug 로그 출력 확인
- [ ] `CmdAndPoseVel.msg` 인터페이스 브라우저에서 탐색 확인
- [ ] 인터페이스 브라우저 → [토픽 발행에 사용] → Topic Panel 연결 확인

---

## 12. M06 — 2D Map & TF Panel

> **선행 조건**: M05 완료

### 12.1 구현 목표

Turtlesim 2D 맵에서 로봇 위치/방향/경로를 실시간 추적하고, TF 프레임 트리를 인터랙티브하게 시각화한다.

### 12.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M06-1** | `backend/tf_manager.py` | `tf2_ros.Buffer` + `TransformListener`. `/tf` + `/tf_static` 모두 구독. `lookup_transform()` 으로 두 프레임 간 변환 계산. `all_frames_as_string()` 으로 프레임 목록 |
| **M06-2** | `ui/panels/map2d_panel.py` | QWebEngineView + Canvas 기반 2D 맵. `/turtle1/pose` 구독 → x/y/theta 실시간 업데이트. 로봇 위치 (원 + 방향 화살표). 경로 트레일 (최근 500개 점). 목표 위치 (빨간 점). 11×11 격자 스케일 |
| **M06-3** | `ui/panels/map2d_panel.py` | `/goal_pose` 토픽 연동: 목표 위치 수신 시 맵에 빨간 원 표시. State Machine 상태 표시 (rotate_to_goal / move_to_goal / rotate_to_final / goal_reached) |
| **M06-4** | `ui/panels/tf_panel.py` | QWebEngineView + D3.js **계층 트리(tree) 레이아웃** (좌→우 방향). 노드: 프레임명 박스. 엣지: 화살표 + translation.x/y/z 수치 표시. 0.5초 자동 갱신. **`view_frames`와 동등한 실시간 트리 구조 렌더링** — TF 프레임 추가/삭제 시 트리 동적 재구성 |
| **M06-5** | `ui/panels/tf_panel.py` | 프레임 박스 클릭 시 우측 상세 패널: translation x/y/z + rotation quaternion → roll/pitch/yaw 변환 표시. **두 프레임 선택 모드**: Ctrl+클릭으로 2개 선택 → 상대 변환 행렬 계산 + 결과 표시. 오래된 TF (>0.1초) 빨간색 테두리 경고 |
| **M06-6** | `backend/tf_manager.py` | **TF 트리 구조 추출**: `all_frames_as_yaml()` 파싱으로 부모-자식 관계 dict 생성. 고아 프레임(부모 없음) 감지 + 경고. 트리 데이터를 JSON으로 직렬화하여 D3.js로 전달 |

### 12.3 M06 완료 조건

- [ ] turtlesim_node 실행 후 2D 맵에 거북이 위치/방향 실시간 표시 확인
- [ ] `move_turtle` 노드 실행 시 이동 경로 트레일 표시 확인
- [ ] `/goal_pose` 발행 시 맵에 목표 위치 표시 확인
- [ ] **`my_tf_1.py` 실행 후 TF 트리에 `world → moving_frame` 계층 구조(트리 레이아웃)로 표시 확인**
- [ ] **프레임 추가/삭제 시 트리 동적 재구성 확인**
- [ ] 두 TF 프레임 선택 → 상대 변환 계산 표시 확인
- [ ] 오래된 TF 빨간색 경고 동작 확인
- [ ] **고아 프레임(부모 없음) 감지 경고 표시 확인**

---

## 13. M07 — Node Graph & Terminal

> **선행 조건**: M06 완료

### 13.1 구현 목표

rqt_graph를 대체하는 인터랙티브 노드 그래프와 ROSForge 내장 터미널을 제공한다.

### 13.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M07-1** | `backend/ros2_introspector.py` | 그래프 데이터 수집: 모든 노드 순회 → `get_publisher_names_and_types_by_node()` / `get_subscriber_names_and_types_by_node()` 로 연결 매핑. 액션/서비스 연결도 포함 |
| **M07-2** | `ui/panels/graph_panel.py` | QWebEngineView + D3.js force-directed graph. 노드: 원형, 색상 = 실행중(녹색)/라이프사이클비활성(노란색)/오류(빨간색). 엣지: 토픽(실선)/서비스(점선)/액션(두꺼운실선). 내부 노드 (`/_ros2cli_xxx`) 숨김 필터. 1초 자동 갱신 |
| **M07-3** | `ui/panels/graph_panel.py` | 노드 클릭 → 사이드 패널에 상세 정보 (Node Panel 내용과 동일). 토픽 엣지 클릭 → Topic Panel 열기. [새로고침] 버튼. [내부 노드 숨김] 토글 |
| **M07-4** | `ui/panels/terminal_panel.py` | `QProcess` 기반 내장 터미널. bash 셸 실행. EnvironmentManager의 sourced env 자동 적용. ANSI 컬러 지원. 탭 다중 터미널 지원 |

### 13.3 M07 완료 조건

- [ ] `turtlesim_node` + `my_publisher` 실행 후 그래프에 노드/토픽 연결 표시 확인
- [ ] 라이프사이클 노드 비활성 상태 노란색 표시 확인
- [ ] 토픽 엣지 클릭 → Topic Panel 연결 확인
- [ ] 내장 터미널에서 `ros2 topic list` 실행 확인 (sourced env 적용)
- [ ] `domain_test.py` 실행 후 멀티 domain 노드 그래프 확인

---

## 14. M08 — Launch File GUI

> **선행 조건**: M07 완료

### 14.1 구현 목표

`.launch.py`와 `.launch.xml` 파일을 파싱하여 GUI에서 실행 전 노드 목록을 미리 보고, 파라미터를 수정한 뒤 실행할 수 있다.

### 14.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M08-1** | `backend/launch_parser.py` | `.launch.py` AST 파싱: `Node()`, `ExecuteProcess()`, `IncludeLaunchDescription()`, `DeclareLaunchArgument()` 추출. `ExcuteProcess` 오타 자동 치환 |
| **M08-2** | `backend/launch_parser.py` | `.launch.xml` ElementTree 파싱: `<node>`, `<arg>`, `<param>`, `<include>` 태그 처리. `$(find-pkg-share ...)` 경로 해석 |
| **M08-3** | `ui/panels/run_panel.py` (확장) | Launch 파일 선택 버튼. 파싱된 노드 목록 미리보기 (패키지/실행파일/네임스페이스/파라미터). 파라미터 오버라이드 입력창. [실행] 버튼 |

### 14.3 교재 launch 파일 파싱 예시

```python
# dist_turtle_action.launch.py 파싱 결과
LaunchPreview:
  Node 1: turtlesim/turtlesim_node
    parameters:
      background_r: 255  [편집 가능]
      background_g: 192  [편집 가능]
      background_b: 203  [편집 가능]
  Node 2: my_first_package/dist_turtle_action_server

# ultrasonic.launch.xml 파싱 결과
LaunchPreview:
  Node: ultrasonic_sensor/ultrasonic_publisher
    param_file: $(find-pkg-share ...)/config/ultra_params.yaml
      trig_pin: 23  [편집 가능]
      echo_pin: 24  [편집 가능]
      ultra_sonic_sample_rate: 0.1  [편집 가능]
```

### 14.4 M08 완료 조건

- [ ] `turtlesim_and_teleop.launch.py` 파싱 → 2개 노드 미리보기 확인
- [ ] `dist_turtle_action.launch.py` 파라미터 GUI 수정 후 실행 확인
- [ ] `ultrasonic.launch.xml` 파싱 → 노드/파라미터 표시 확인
- [ ] `ExcuteProcess` 오타 자동 처리 확인

---

## 15. M09 — Lifecycle & Bag Panel

> **선행 조건**: M08 완료

### 15.1 구현 목표

라이프사이클 노드의 상태를 GUI에서 제어하고, rosbag2 녹화/재생을 통합 관리한다.

### 15.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M09-1** | `backend/lifecycle_manager.py` | `/<node>/get_state` 서비스 존재 여부로 라이프사이클 노드 감지. 1초 폴링으로 상태 모니터링. `/<node>/change_state` 서비스로 전환 요청. `/<node>/transition_event` 토픽 구독으로 이벤트 수집 |
| **M09-2** | `ui/widgets/lifecycle_state_widget.py` | 상태 다이어그램 위젯: UNCONFIGURED/INACTIVE/ACTIVE/FINALIZED 원형 + 화살표. 현재 상태 하이라이트. 상태별 색상 (ACTIVE=녹색, INACTIVE=노란색, UNCONFIGURED=회색) |
| **M09-3** | `ui/panels/lifecycle_panel.py` | 라이프사이클 노드 목록 (일반 노드와 구분). 노드 선택 → 상태 다이어그램 + 전환 버튼 [configure/activate/deactivate/cleanup/shutdown]. 트랜지션 이벤트 로그 |
| **M09-4** | `backend/bag_manager.py` | `ros2 bag record` subprocess 래퍼. 토픽 선택/전체 선택. 저장 경로/파일명/형식(MCAP) 설정. 녹화 중 상태 (경과시간/파일크기) |
| **M09-5** | `backend/bag_manager.py` | `ros2 bag play` subprocess 래퍼. 속도 조절 (0.25x~4x). 타임라인 위치 제어. 반복 재생. 특정 토픽만 재생. `ros2 bag info` 로 파일 정보 조회 |
| **M09-6** | `ui/panels/bag_panel.py` | 녹화 섹션: 토픽 체크박스 목록, 저장 경로, [녹화 시작/중지] 버튼, 실시간 크기 표시. 재생 섹션: 파일 선택, 타임라인 슬라이더, 속도 드롭다운, [재생/정지/처음/끝] 버튼, 포함 토픽 목록 |

### 15.3 M09 완료 조건

- [ ] Nav2 실행 후 lifecycle_manager 노드 감지 확인
- [ ] 라이프사이클 노드 상태 다이어그램 표시 확인
- [ ] [configure] → [activate] 버튼으로 상태 전환 확인
- [ ] `/turtle1/pose` 토픽 녹화 → MCAP 파일 생성 확인
- [ ] 녹화된 bag 재생 → 속도 조절 동작 확인
- [ ] bag 재생 중 타임라인 슬라이더 이동 확인

---

## 16. M10 — Layout & Preset

> **선행 조건**: M09 완료

### 16.1 구현 목표

사용자가 패널 레이아웃을 저장/불러오기하고, 프로젝트 프리셋을 통해 자주 사용하는 실행 구성을 빠르게 복원할 수 있다.

### 16.2 세부 태스크

| 태스크 | 파일 | 세부 내용 |
|--------|------|-----------|
| **M10-1** | `ui/main_window.py` | QDockWidget 상태를 `saveState()` / `restoreState()`로 직렬화. `~/.rosforge/layouts/*.json`에 저장. 레이아웃 이름 입력 + [저장] / [불러오기] / [삭제] |
| **M10-2** | `backend/profile_manager.py` (확장) | 프로파일에 `launch_presets` 필드 추가. 프리셋: 이름/실행할 노드 목록/launch 파일/파라미터 스냅샷. [프리셋 실행] 버튼 → 해당 구성 일괄 실행 |
| **M10-3** | `ui/main_window.py` | 기본 레이아웃 4종 제공: Teaching (교재 실습용) / Monitoring (모니터링 집중) / Development (빌드+실행 집중) / Full (전체 패널). 레이아웃 전환 드롭다운 |

### 16.3 기본 레이아웃 구성

```
Teaching 레이아웃 (교재 실습용):
  좌: Build Panel + Run Panel
  중: Topic Panel + Param Panel
  우: Log Viewer + 2D Map Panel

Monitoring 레이아웃:
  좌: Node Graph
  중: Topic Panel (플롯 집중)
  우: Log Viewer

Development 레이아웃:
  좌: Build Panel + Terminal Panel
  중: Node Panel + Param Panel
  우: Log Viewer
```

### 16.4 M10 완료 조건

- [ ] 현재 레이아웃 저장 → 앱 재시작 후 복원 확인
- [ ] Teaching 기본 레이아웃 전환 확인
- [ ] 프리셋 저장 → [프리셋 실행]으로 노드 일괄 실행 확인

---

## 17. 공통 개발 규칙

### 17.1 환경 규칙

```
1. colcon build는 항상 build_colcon_env() (venv 비활성화 env) 로 실행
2. ros2 run/launch는 build_ros2_env() (sourced env) 로 실행
3. 빌드 완료 후 반드시 env_manager.invalidate_cache() 호출
4. rclpy 노드는 MultiThreadedExecutor + 별도 스레드에서 spin()
5. asyncio 이벤트 루프와 Qt 메인 루프는 분리 (asyncio.run_coroutine_threadsafe 사용)
6. 고주파 토픽 수신 시 UI 갱신은 Throttle Queue를 통해 최대 30Hz로 제한
7. ROS2 API 호출은 반드시 ros2_adapter.py를 통해 간접 호출 (직접 rclpy 호출 금지)
```

### 17.1-B ROS2 배포판 추상화 계층 (ros2_adapter.py)

ROS2 Jazzy/Humble/Rolling 간 CLI 인자나 API 변경점에 대응하기 위해 모든 배포판 의존적 호출을 단일 어댑터로 래핑한다. 배포판 교체 시 어댑터 구현체만 교체하면 나머지 코드는 수정 불필요.

```python
# backend/ros2_adapter.py

from abc import ABC, abstractmethod
from typing import Protocol

class ROS2AdapterBase(ABC):
    """ROS2 배포판 간 API 차이를 추상화하는 어댑터 인터페이스."""

    @abstractmethod
    def get_node_names_and_namespaces(self, node) -> list[tuple[str, str]]:
        """노드 목록 조회 — 배포판별 API 차이 래핑."""
        ...

    @abstractmethod
    def get_action_names_and_types(self, node) -> list[tuple[str, list[str]]]:
        """액션 목록 조회 — Jazzy vs Humble import 경로 차이 처리."""
        ...

    @abstractmethod
    def build_colcon_command(self, packages: list[str], extra_args: list[str]) -> list[str]:
        """배포판별 colcon 명령 인자 차이 처리."""
        ...

    @abstractmethod
    def get_logger_service_name(self, node_name: str) -> str:
        """로거 레벨 서비스명 — Jazzy 신기능 여부 확인."""
        ...


class JazzyAdapter(ROS2AdapterBase):
    """ROS2 Jazzy Jalisco 전용 어댑터."""

    def get_node_names_and_namespaces(self, node):
        return node.get_node_names_and_namespaces()

    def get_action_names_and_types(self, node):
        from rclpy.action import get_action_names_and_types
        return get_action_names_and_types(node)

    def build_colcon_command(self, packages, extra_args):
        cmd = ['colcon', 'build', '--symlink-install']
        if packages:
            cmd += ['--packages-select'] + packages
        return cmd + extra_args

    def get_logger_service_name(self, node_name: str) -> str:
        return f'/{node_name}/set_logger_levels'   # Jazzy 지원


class HumbleAdapter(ROS2AdapterBase):
    """ROS2 Humble Hawksbill 전용 어댑터."""

    def get_node_names_and_namespaces(self, node):
        return node.get_node_names_and_namespaces()

    def get_action_names_and_types(self, node):
        # Humble은 import 경로가 다를 수 있음
        from rclpy.action import get_action_names_and_types
        return get_action_names_and_types(node)

    def build_colcon_command(self, packages, extra_args):
        cmd = ['colcon', 'build', '--symlink-install']
        if packages:
            cmd += ['--packages-select'] + packages
        return cmd + extra_args

    def get_logger_service_name(self, node_name: str) -> str:
        return None   # Humble은 logger service 미지원


def create_adapter(distro: str) -> ROS2AdapterBase:
    """배포판 문자열로 적절한 어댑터 반환."""
    adapters = {
        'jazzy':  JazzyAdapter,
        'kilted': JazzyAdapter,   # Kilted는 Jazzy 호환
        'humble': HumbleAdapter,
        'rolling': JazzyAdapter,  # Rolling은 최신 API 사용
    }
    cls = adapters.get(distro.lower(), JazzyAdapter)
    return cls()
```

### 17.1-C UI Throttling 구현 패턴

```python
# backend/topic_manager.py — Throttle Queue 패턴

import asyncio
from collections import defaultdict

class TopicManager:
    def __init__(self, ui_update_hz: float = 20.0):
        self._throttle_interval = 1.0 / ui_update_hz
        self._latest_msgs: dict[str, dict] = {}     # 토픽별 최신 메시지 보관
        self._pending_topics: set[str] = set()      # UI 갱신 대기 토픽 목록
        self._ui_timer: asyncio.TimerHandle | None = None

    def _on_message_received(self, topic_name: str, msg: dict):
        """rclpy 콜백 — 수신 즉시 최신 메시지 교체 (drop old)."""
        self._latest_msgs[topic_name] = msg
        self._pending_topics.add(topic_name)
        # UI 갱신 타이머는 별도 루프에서 실행 (Throttle)

    async def _ui_flush_loop(self):
        """Throttle 루프 — 설정된 Hz로 주기적으로 UI 시그널 발행."""
        while True:
            await asyncio.sleep(self._throttle_interval)
            for topic in list(self._pending_topics):
                msg = self._latest_msgs.get(topic)
                if msg:
                    self.topic_message_received.emit(topic, msg)
            self._pending_topics.clear()
```

### 17.2 SQLite 스키마

```sql
-- 파라미터 히스토리
CREATE TABLE param_history (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    node_name TEXT NOT NULL,
    param_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    success   INTEGER NOT NULL DEFAULT 1
);

-- 서비스 호출 히스토리
CREATE TABLE service_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT NOT NULL,
    service_name TEXT NOT NULL,
    request_json TEXT NOT NULL,
    response_json TEXT,
    response_ms  REAL,
    success      INTEGER NOT NULL DEFAULT 1
);

-- 액션 Goal 히스토리
CREATE TABLE action_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    action_name TEXT NOT NULL,
    goal_json   TEXT NOT NULL,
    result_json TEXT,
    status      TEXT NOT NULL,  -- SUCCEEDED | CANCELED | ABORTED
    duration_ms REAL
);

-- 로그 저장
CREATE TABLE ros_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    level     INTEGER NOT NULL,
    node_name TEXT NOT NULL,
    message   TEXT NOT NULL,
    file      TEXT,
    function  TEXT,
    line      INTEGER
);
```

### 17.3 코딩 스타일

- Python 3.10+ 문법 사용 (`match`, `|` 타입 힌트 등)
- 모든 백엔드 클래스는 `async def` 메서드 사용
- 타입 힌트 필수 (`from __future__ import annotations`)
- Qt 시그널/슬롯으로 백엔드 ↔ UI 통신 (직접 UI 호출 금지)
- 파일명: `snake_case.py` / 클래스명: `PascalCase`
- 각 마일스톤 완료 후 `.md` 작업 로그 생성 (`~/ROSForge/logs/`)

### 17.4 빌드 에러 파싱 패턴

```python
# backend/build_manager.py — 에러 파싱 로직

import re
from dataclasses import dataclass

@dataclass
class BuildError:
    file_path: str
    line: int
    col: int | None
    message: str
    suggestion: str | None   # 알려진 에러 유형 → 해결책

# 정규식 패턴
_ERROR_PATTERN = re.compile(
    r'^(.+?):(\d+)(?::(\d+))?:\s*(error|fatal error):\s*(.+)$',
    re.MULTILINE
)

# 공통 에러 → 해결책 매핑 테이블
_KNOWN_ERRORS: dict[str, str] = {
    "cannot find package":
        "package.xml의 <depend> 태그를 확인하고 rosdep install을 실행하세요.",
    "No module named":
        "Python 패키지가 설치되지 않았습니다. pip install 또는 rosdep install을 실행하세요.",
    "undefined reference":
        "CMakeLists.txt의 target_link_libraries()에 누락된 라이브러리를 추가하세요.",
    "No such file or directory":
        "헤더/소스 파일 경로를 확인하세요. include_directories() 설정이 필요할 수 있습니다.",
    "implicit declaration":
        "헤더 파일 include가 누락되었습니다.",
    "ExcuteProcess":
        "'ExcuteProcess'는 오타입니다. 'ExecuteProcess'로 수정하세요.",
}

def parse_build_errors(log_text: str) -> list[BuildError]:
    errors = []
    for match in _ERROR_PATTERN.finditer(log_text):
        file_path, line, col, _, message = match.groups()
        suggestion = next(
            (sol for key, sol in _KNOWN_ERRORS.items() if key in message),
            None
        )
        errors.append(BuildError(
            file_path=file_path,
            line=int(line),
            col=int(col) if col else None,
            message=message,
            suggestion=suggestion,
        ))
    return errors
```

### 17.5 Qt 시그널 규칙

```python
# 백엔드에서 UI로 데이터 전달 — 항상 시그널 사용 (직접 UI 호출 절대 금지)

class TopicManager(QObject):
    topic_list_updated    = pyqtSignal(list)           # 토픽 목록 갱신
    topic_message_received = pyqtSignal(str, dict)     # (토픽명, 메시지) — Throttled
    hz_updated            = pyqtSignal(str, float)     # (토픽명, Hz)
    bw_updated            = pyqtSignal(str, float)     # (토픽명, KB/s)
    qos_warning           = pyqtSignal(str, str)       # (토픽명, 경고메시지)

class ServiceManager(QObject):
    call_completed        = pyqtSignal(str, dict, float)  # (서비스명, response, ms)
    call_timeout          = pyqtSignal(str, float)        # (서비스명, timeout초)
    call_failed           = pyqtSignal(str, str)          # (서비스명, 에러메시지)

class ActionManager(QObject):
    goal_accepted         = pyqtSignal(str, str)          # (액션명, goal_id)
    feedback_received     = pyqtSignal(str, dict)         # (액션명, feedback)
    goal_completed        = pyqtSignal(str, str, dict)    # (액션명, status, result)
    goal_timeout          = pyqtSignal(str, str)          # (액션명, goal_id)

class ProcessManager(QObject):
    node_started          = pyqtSignal(str, int)          # (노드명, PID)
    node_stopped          = pyqtSignal(str, int)          # (노드명, PID)
    emergency_stop_done   = pyqtSignal(int)               # 종료된 프로세스 수
    resource_updated      = pyqtSignal(str, float, float) # (노드명, CPU%, MEM_MB)

class BuildManager(QObject):
    log_line              = pyqtSignal(str)               # 빌드 로그 한 줄
    build_errors_parsed   = pyqtSignal(list)              # list[BuildError]
    build_finished        = pyqtSignal(bool, str)         # (성공여부, 패키지명)
```

### 17.6 리스크 및 대응 전략

| 리스크 | 내용 | 대응 |
|--------|------|------|
| **rclpy 스레드 안전성** | GIL + executor 스레드 충돌 | MultiThreadedExecutor + asyncio 분리 |
| **colcon venv 충돌** | venv 활성화 시 colcon 오작동 | `build_colcon_env()`에서 자동 venv PATH 제거 |
| **.bashrc 기존 내용 충돌** | 기존 jazzy source 중복 | 충돌 감지 + 경고 다이얼로그 |
| **고주파 토픽 UI 프리징** | 62Hz+ 토픽 직접 수신 시 Qt 이벤트 루프 블로킹 | Throttle Queue (10~30Hz 제한) + asyncio.Queue drop-old |
| **대용량 메시지 메모리** | Image/PointCloud2 복사 오버헤드 | 백엔드에서 downsample + numpy view 전달 |
| **서비스/액션 무한 대기** | 서버 응답 없을 때 UI 무한 로딩 | `asyncio.wait_for()` 타임아웃 + 시각적 피드백 |
| **ROS2 배포판 API 차이** | Jazzy/Humble CLI 인자 또는 import 경로 차이 | `ros2_adapter.py` 추상화 계층으로 격리 |
| **foxglove_bridge 의존성** | 별도 ROS2 노드로 실행 필요 | subprocess로 자동 시작/관리 |
| **동적 메시지 타입** | 커스텀 msg 런타임 import | `rosidl_runtime_py` + importlib 동적 로드 |
| **커스텀 메시지 빌드 순서** | msgs 패키지 먼저 빌드 필요 | package.xml 의존성 위상 정렬 자동화 |
| **ExcuteProcess 오타** | 교재 launch 파일 오타 | 파싱 + 에러 파싱 테이블에서 자동 감지/치환 |
| **QoS 불일치** | pub-sub QoS 호환성 문제 | `get_publishers_info_by_topic()` 비교 + 경고 |
| **라이프사이클 노드 감지** | 일반 노드와 구분 필요 | `get_state` 서비스 존재 여부로 감지 |
| **파라미터 배열 타입 UI** | DOUBLE_ARRAY 등 복잡한 타입 | 배열 편집 전용 다이얼로그 위젯 |
| **/rosout 과부하** | 노드 수 증가 시 로그 폭주 | 레벨 필터 + 버퍼 크기 제한 |

---

## 18. 완료 조건 체크리스트

### 전체 프로젝트 완료 기준

**교재 시나리오 A (ros2_basic 기초편) 완주 가능:**
- [ ] 환경 설정 → 빌드 → turtlesim 실행 → Publisher/Subscriber 실행 → 토픽 모니터링 → 서비스 호출 → 액션 실행 → 파라미터 실시간 수정 → 로그 확인

**교재 시나리오 B (PID 제어) 완주 가능:**
- [ ] 빌드 → turtlesim + move_turtle 실행 → /goal_pose 발행 → PID 슬라이더 실시간 조정 → /error 플롯 → 2D 맵 추적

**교재 시나리오 C (TF 튜토리얼) 완주 가능:**
- [ ] my_tf 빌드 → 노드 실행 → TF 트리 계층 구조 시각화 → 프레임 상대 변환 확인

**성능 및 안정성 확인:**
- [ ] 62Hz 토픽 구독 시 UI 프리징 없음 (Throttling 동작)
- [ ] UI 갱신 주기 10~30Hz 설정 변경 적용
- [ ] 서비스 타임아웃 5초 후 "⏱ 응답 없음" 표시
- [ ] 액션 실행 타임아웃 자동 Cancel 동작
- [ ] 🛑 Global Kill Switch 클릭 → 모든 노드 즉시 종료

**환경 관리 확인:**
- [ ] `.bashrc` 버튼 클릭 적용 + 터미널 출력
- [ ] ROS_DOMAIN_ID 원클릭 변경 → 신규 subprocess env 즉시 반영
- [ ] 빌드 에러 파일:라인 클릭 링크 + 해결책 제안 표시
- [ ] 배포판 전환 시 `ros2_adapter` 자동 교체 동작

**핵심 모니터링 기능 확인:**
- [ ] 토픽 Hz/BW 실시간 표시
- [ ] QoS 불일치 경고
- [ ] 파라미터 슬라이더 실시간 적용 + /parameter_events 수신
- [ ] 파라미터/서비스/액션 히스토리 SQLite 저장
- [ ] TF 트리 실시간 계층 구조 렌더링 + 고아 프레임 감지
- [ ] 라이프사이클 노드 상태 전환 버튼
- [ ] bag 녹화/재생
- [ ] 레이아웃 프로젝트별 저장/복원

---

*작성: gjkong | 2026-03-18 | v1.1*  
*기준 문서: ROSForge_research.md v2.0*  
*반영 사항: 성능 최적화(Throttling/Zero-copy), 환경 격리(원클릭 DOMAIN ID), 빌드 에러 파싱, 서비스/액션 타임아웃, TF 트리 구조 시각화, ROS2 추상화 계층, Global Kill Switch, 레이아웃 저장*  
*다음 단계: M00 구현 시작*

