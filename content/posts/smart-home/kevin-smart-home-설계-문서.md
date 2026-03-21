---
title: "Kevin Smart Home — 설계 문서"
date: 2026-03-21
draft: true
tags: ["smart-home", "esp32", "fastapi"]
categories: ["smart-home"]
description: "> **프로젝트명:** Kevin Smart Home > **버전:** v1.0.0 > **작성일:** 2026-02-19"
---

# Kevin Smart Home — 설계 문서

> **프로젝트명:** Kevin Smart Home  
> **버전:** v1.0.0  
> **작성일:** 2026-02-19  
> **작성자:** Stephen Kong  
> **기술 스택:** Python, ROS2 Jazzy, micro-ROS, ESP32, PyQt6, PyOpenGL, FastAPI, LangGraph

---

## 1. 프로젝트 개요

### 1.1 목적

실제 IoT 디바이스(ESP32 + 센서)와 PC 3D 시뮬레이터를 연동한 **스마트 홈 디지털 트윈 시스템**.  
가정집 모델 하우스를 3D로 구현하고, 실제 센서 데이터를 실시간으로 반영하며  
시나리오 기반 자동화 + 수동 제어를 PC/모바일 GUI에서 통합 관리한다.

### 1.2 핵심 컨셉

- **디지털 트윈**: 실제 IoT 하우스 ↔ PC 3D 모델 실시간 동기화
- **시나리오 엔진**: 오전/오후/저녁 시간대별 자동화 시나리오
- **Kevin 로봇 3종**: 주인(kevin-01) / 집사(kevin-02) / 이벤트 Agent(kevin-03)
- **멀티 플랫폼 GUI**: PC 대시보드(PyQt6) + 모바일(FastAPI + WebSocket)

---

## 2. 시스템 아키텍처

### 2.1 전체 구조

```
┌─────────────────────────────────────────────────────┐
│                  실제 IoT 하우스                      │
│  ESP32 × N + 센서(LED/온도/습도/조도/IR/초음파/CCTV)  │
│              micro-ROS (WiFi/Serial)                 │
└──────────────────────┬──────────────────────────────┘
                       │ ROS2 토픽 / 서비스 / 액션
┌──────────────────────▼──────────────────────────────┐
│               ROS2 Jazzy 미들웨어                     │
│         /home/sensors  /home/actuators               │
│         /kevin/01  /kevin/02  /kevin/03              │
└───┬──────────────┬───────────────────┬──────────────┘
    │              │                   │
    ▼              ▼                   ▼
[kevin-01]    [kevin-02]          [kevin-03]
주인 노드      집사 로봇            이벤트 Agent
명령 권한      청소+침입감지         시나리오 트리거
    │              │                   │
    └──────────────┴───────────────────┘
                   │
    ┌──────────────▼──────────────────┐
    │       시나리오 엔진 (LangGraph)   │
    │   오전 → 오후 → 저녁 State 전환  │
    └──────────────┬──────────────────┘
                   │
    ┌──────────────▼──────────────────┐
    │         디지털 트윈 레이어        │
    │   ROS2 상태 ↔ 3D 모델 동기화    │
    └──────────┬──────────────────────┘
               │
    ┌──────────▼──────────┐    ┌─────────────────┐
    │  PC 대시보드         │    │  모바일 앱        │
    │  PyQt6 + PyOpenGL   │    │  FastAPI +       │
    │  3D 뷰 + 제어판      │    │  WebSocket       │
    └─────────────────────┘    └─────────────────┘
```

### 2.2 디지털 트윈 동기화

```
실제 디바이스 상태 변화
    → micro-ROS 퍼블리시
    → ROS2 토픽
    → TwinSyncNode 구독
    → 3D 모델 상태 업데이트 (LED 색상, 센서 수치, 로봇 위치)

PC 3D 모델 제어 명령
    → PyQt6 버튼 클릭
    → ROS2 서비스 호출
    → ESP32 액추에이터 실행
```

---

## 3. 3D 모델 하우스 구조

### 3.1 공간 구성 (1층 + 차고)

```
┌─────────────────────────────────────────┐
│                 현관                     │
│  ┌──────────┐  ┌──────────────────────┐ │
│  │  욕실    │  │       거실           │ │
│  └──────────┘  │                      │ │
│  ┌──────────┐  └──────────────────────┘ │
│  │  주방    │  ┌──────────────────────┐ │
│  └──────────┘  │       안방           │ │
│                └──────────────────────┘ │
├─────────────────────────────────────────┤
│              차고 (지상)                 │
│  ┌──────────────────────────────────┐   │
│  │  주차 공간 × 1  +  차고문        │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 3.2 공간별 센서 배치

| 공간 | 센서 | 액추에이터 |
|------|------|-----------|
| 현관 | PIR(적외선), 초음파, 조도 | LED, 도어락 |
| 거실 | PIR, 온도/습도, CCTV | LED × 3, 에어컨 |
| 주방 | PIR, 온도, 가스 | LED, 환풍기 |
| 욕실 | PIR, 온도/습도 | LED, 온수기 |
| 안방 | PIR, 온도/습도 | LED, 커튼 |
| 차고 | 초음파(차량감지), PIR, CCTV | LED, 차고문 |
| 외부 | PIR, CCTV × 2, 조도 | 외부 LED, 경보 |

---

## 4. Kevin 로봇 역할 정의

### 4.1 kevin-01 (주인)

- **역할**: 시스템 최고 권한자, 전체 제어 명령 발행
- **주요 기능**: 시나리오 승인/거부, 긴급 Override, 모바일 알림 수신
- **ROS2 노드**: `home_master_node`
- **토픽**: `/kevin/01/command`, `/kevin/01/status`

### 4.2 kevin-02 (집사 로봇)

- **역할**: 낮 시간 청소 + 침입 감지 + 순찰
- **주요 기능**:
  - 오전 출근 후 자동 청소 루틴 실행
  - 외부인 감지 시 CCTV 연동 + 알림
  - 공간별 순찰 패턴 (Kevin Patrol 응용)
- **ROS2 노드**: `guardian_node`
- **토픽**: `/kevin/02/patrol`, `/kevin/02/alert`, `/kevin/02/clean`

### 4.3 kevin-03 (이벤트 Agent)

- **역할**: 시나리오 트리거 + 이벤트 시뮬레이션
- **주요 기능**:
  - 외부인 침입 이벤트 발생
  - 화재 이벤트 발생
  - 차량 도착 이벤트 발생
  - 사용자 지시에 따라 커스텀 이벤트 실행
- **ROS2 노드**: `event_agent_node`
- **토픽**: `/kevin/03/event`, `/kevin/03/trigger`

---

## 5. 시나리오 엔진

### 5.1 LangGraph State Machine

```python
class HomeState(TypedDict):
    time_period: str          # morning / afternoon / evening / night
    occupancy: str            # home / away / sleeping
    alarm_status: str         # armed / disarmed / triggered
    sensor_states: Dict       # 전체 센서 현재 상태
    active_scenario: str      # 현재 실행 중인 시나리오
    event_log: List[dict]     # 이벤트 로그
    kevin02_mode: str         # patrol / clean / standby / alert
```

### 5.2 시나리오 상세

#### 🌅 오전 시나리오 (06:00 ~ 09:00)

```
사람 동선 감지 (PIR 순서)
  안방 → 욕실 → 주방 → 거실
    ↓
  각 공간 LED 자동 점등 (동선 추적)
  욕실 진입 → 온수기 자동 가동 (3분 예열)
  주방 진입 → 환풍기 대기 상태
  조도 센서 → 외부 밝기에 따라 LED 밝기 자동 조절

출근 감지 (현관 → 외부 PIR 순서)
  → 전체 LED 소등
  → 도어락 잠금 확인
  → kevin-02 청소 모드 시작
  → 알람 Armed 상태 전환
```

#### ☀️ 낮 시나리오 (09:00 ~ 17:00)

```
kevin-02 청소 루틴
  거실 → 주방 → 욕실 → 안방 순서 청소

외부 침입 감지
  외부 PIR + CCTV 동시 감지
    → kevin-01 모바일 알림 즉시 발송
    → 경보 LED 점멸
    → kevin-02 해당 구역 이동 + CCTV 촬영

알람 해제
  kevin-01 모바일 승인
    → 알람 Disarmed
    → kevin-02 복귀
```

#### 🌆 오후 시나리오 (17:00 ~ 20:00)

```
조도 센서 → 외부 어두워짐 감지
  → 외부 미등 자동 점등
  → 차고 조명 자동 점등

차량 도착 감지
  차고 초음파 센서 → 차량 접근 감지
    → 차고 LED 밝기 최대
    → 차고문 자동 Open
    → 현관 LED 점등 대기

귀가 후 동선 (현관 → 거실 → 욕실 → 주방 → 거실 → 안방)
  PIR 순서 감지
    → 각 공간 LED 자동 점등/소등
    → 온도/습도 에어컨 자동 조절
```

#### 🌙 저녁 시나리오 (22:00 ~ )

```
안방 PIR 감지 (취침 감지)
  → 전체 LED 순차 소등
  → 도어락 잠금 확인
  → 외부 CCTV 야간 모드
  → kevin-02 Standby 충전
  → 알람 Armed (야간 모드)
```

---

## 6. ROS2 토픽 / 서비스 구조

### 6.1 센서 토픽

```
/home/sensor/pir/{room}          # Bool — 동작 감지
/home/sensor/temperature/{room}  # Float32 — 온도
/home/sensor/humidity/{room}     # Float32 — 습도
/home/sensor/light/{room}        # Float32 — 조도(lux)
/home/sensor/ultrasonic/garage   # Float32 — 차량 거리(cm)
/home/sensor/gas/kitchen         # Float32 — 가스 농도
/home/sensor/cctv/{location}     # Image — 카메라 영상
```

### 6.2 액추에이터 토픽

```
/home/actuator/led/{room}        # Int32 — 밝기 0~255
/home/actuator/door/{location}   # Bool — 열림/닫힘
/home/actuator/heater/bathroom   # Bool — 온수기 ON/OFF
/home/actuator/fan/kitchen       # Bool — 환풍기 ON/OFF
/home/actuator/alarm             # String — armed/disarmed/triggered
/home/actuator/garage_door       # Bool — 열림/닫힘
```

### 6.3 시나리오 서비스

```
/scenario/trigger     # 시나리오 강제 실행
/scenario/status      # 현재 시나리오 조회
/kevin/02/set_mode    # 집사 로봇 모드 설정
/kevin/03/fire_event  # 이벤트 발생 요청
```

---

## 7. ESP32 디바이스 구성

### 7.1 MCU 배치

| MCU | 담당 공간 | 연결 센서 |
|-----|-----------|-----------|
| ESP32-01 | 거실 + 현관 | PIR × 2, LED × 3, 조도, 온습도, CCTV |
| ESP32-02 | 주방 + 욕실 | PIR × 2, LED × 2, 온도, 가스, 온수기 |
| ESP32-03 | 안방 | PIR, LED, 온습도, 커튼 모터 |
| ESP32-04 | 차고 + 외부 | 초음파, PIR × 2, LED × 2, CCTV × 2, 차고문 |

### 7.2 통신 방식

```
ESP32 → micro-ROS Agent (WiFi UDP)
  → ROS2 토픽 브릿지
  → PC ROS2 네트워크
```

---

## 8. GUI 구성

### 8.1 PC 대시보드 (PyQt6 + PyOpenGL)

```
┌─────────────────────────────────────────────────────┐
│  Kevin Smart Home Dashboard              [테마 선택] │
├──────────────────────┬──────────────────────────────┤
│                      │  센서 패널                    │
│   3D 모델 하우스      │  온도: 22.5°C  습도: 55%     │
│   (PyOpenGL)         │  조도: 450lux  가스: 정상     │
│                      ├──────────────────────────────┤
│   - LED 점등 시각화   │  Kevin 상태                  │
│   - 동선 표시         │  kevin-01: 🟢 외출 중        │
│   - 센서 위치 표시    │  kevin-02: 🔵 청소 중        │
│   - 차고문 애니메이션 │  kevin-03: 🟡 대기           │
│                      ├──────────────────────────────┤
│                      │  시나리오                     │
│                      │  현재: ☀️ 낮 시나리오         │
│                      │  [오전] [오후] [저녁] [야간]  │
├──────────────────────┴──────────────────────────────┤
│  이벤트 로그                                         │
│  [14:32] kevin-02 청소 완료 — 거실                   │
│  [14:15] 외부 PIR 감지 → 알람 발송                   │
│  [13:00] 청소 시작                                   │
└─────────────────────────────────────────────────────┘
```

### 8.2 모바일 앱 (FastAPI + WebSocket)

```
- 실시간 센서 데이터 조회
- LED / 도어락 / 차고문 원격 제어
- 알람 승인 / 해제
- 이벤트 로그 확인
- 푸시 알림 (침입, 화재, 차량 도착)
```

---

## 9. 디렉토리 구조

```
kevin_smart_home/
├── main.py                        # 전체 시스템 진입점
├── config.py                      # 환경 설정
├── requirements.txt
│
├── ros2_nodes/
│   ├── home_master_node.py        # kevin-01 주인 노드
│   ├── guardian_node.py           # kevin-02 집사 노드
│   ├── event_agent_node.py        # kevin-03 이벤트 노드
│   ├── sensor_bridge_node.py      # ESP32 ↔ ROS2 브릿지
│   └── twin_sync_node.py          # 디지털 트윈 동기화
│
├── scenario/
│   ├── home_state.py              # LangGraph HomeState
│   ├── scenario_graph.py          # StateGraph 정의
│   ├── morning_scenario.py        # 오전 시나리오
│   ├── afternoon_scenario.py      # 오후 시나리오
│   ├── evening_scenario.py        # 저녁 시나리오
│   └── night_scenario.py          # 야간 시나리오
│
├── digital_twin/
│   ├── house_model.py             # 3D 하우스 모델 (PyOpenGL)
│   ├── room_renderer.py           # 공간별 렌더링
│   ├── sensor_visualizer.py       # 센서 상태 시각화
│   └── animation.py               # LED 점등, 차고문 애니메이션
│
├── gui/
│   ├── main_dashboard.py          # PyQt6 메인 대시보드
│   ├── control_panel.py           # 제어 패널
│   ├── event_log_widget.py        # 이벤트 로그
│   └── scenario_panel.py          # 시나리오 제어
│
├── api/
│   ├── fastapi_server.py          # FastAPI 서버
│   ├── websocket_manager.py       # WebSocket 실시간 통신
│   └── mobile_routes.py           # 모바일 API 엔드포인트
│
├── devices/
│   ├── esp32_01/                  # 거실+현관 펌웨어
│   ├── esp32_02/                  # 주방+욕실 펌웨어
│   ├── esp32_03/                  # 안방 펌웨어
│   └── esp32_04/                  # 차고+외부 펌웨어
│
└── docs/
    ├── Kevin_Smart_Home_Design.md
    └── DEV_LOG.md
```

---

## 10. 개발 로드맵

| Phase | 내용 | 우선순위 |
|-------|------|---------|
| **Phase 1** | 3D 모델 하우스 기본 구현 (PyOpenGL, 1층+차고) | 🔴 High |
| **Phase 2** | ROS2 노드 구성 (kevin-01/02/03 + sensor_bridge) | 🔴 High |
| **Phase 3** | 시나리오 엔진 (LangGraph, 오전/오후/저녁) | 🔴 High |
| **Phase 4** | PC 대시보드 PyQt6 통합 (3D + 제어판 + 로그) | 🟡 Medium |
| **Phase 5** | FastAPI 모바일 서버 + WebSocket | 🟡 Medium |
| **Phase 6** | ESP32 micro-ROS 펌웨어 연동 (실제 디바이스) | 🟡 Medium |
| **Phase 7** | 디지털 트윈 동기화 완성 | 🟢 Low |
| **Phase 8** | E2E 전체 시나리오 테스트 | 🟢 Low |

---

## 11. 기존 프로젝트 재사용 자산

| 기존 프로젝트 | 재사용 항목 |
|--------------|------------|
| Kevin Patrol Dashboard | PyQt6 대시보드 구조, PyOpenGL 3D 렌더링, RobotManager |
| Home Guard Bot | FastAPI 서버, ROS2 노드 구조, guard_brain |
| AI Drama Agent | LangGraph StateGraph (시나리오 엔진) |
| micro-ROS ESP32 | ESP32 펌웨어 기반 (현재 작업 중) |

---

*Kevin Smart Home | 2026-02-19 | 설계 v1.0.0*
