---
title: "Kevin Smart Home — 개발 일지"
date: 2026-03-21
draft: true
tags: ["dev-tools", "pyqt6"]
categories: ["dev-tools"]
description: "| 파일 | 버전 | 변경 내용 | |------|------|-----------| | `docs/Kevin_Smart_Home_Phase4_Dashboard_Design.md` | v1.0.0 | Phase 4 "
---

# Kevin Smart Home — 개발 일지

## 2026-02-20 | Phase 4 설계 — PyQt6 대시보드 + 3D 뷰 내장

### 작업 내용

#### 변경된 파일 목록

| 파일 | 버전 | 변경 내용 |
|------|------|-----------|
| `docs/Kevin_Smart_Home_Phase4_Dashboard_Design.md` | v1.0.0 | Phase 4 설계 문서 신규 작성 |
| `docs/Kevin_Smart_Home_DEV_LOG.md` | v0.5.0 | 오늘 작업 내용 추가 |

#### 핵심 설계 결정사항

**1. PyOpenGL 통합 방식 확정**
- GLUT 기반 독립 실행 → `QOpenGLWidget` 상속 방식으로 전환
- `house_model.py` 렌더링 로직 100% 재사용, GLUT 인터페이스만 교체
- `glutMainLoop` → `QTimer(16ms, ~60fps)`로 대체

**2. 모듈 분리 구조 확정**
```
gui/opengl_widget.py      ← QOpenGLWidget 기반 3D 뷰 (핵심)
gui/main_dashboard.py     ← PyQt6 메인 윈도우
gui/sensor_panel.py       ← 센서 데이터 표시
gui/control_panel.py      ← LED / 시나리오 제어
gui/event_log_widget.py   ← 이벤트 로그
digital_twin/data_bridge.py ← GUI ↔ 3D 상태 동기화
```

**3. DataBridge 설계 — 향후 ROS2 연동 고려**
- 현재: `sensor_simulator.py` 직접 연동
- Phase 2 이후: `data_bridge.py` 내부만 수정하면 ROS2 전환 가능
- GUI / 3D 렌더링 코드 변경 없음

**4. 시그널-슬롯 아키텍처**
```
ControlPanel ──→ HouseGLWidget.set_led_state()
HouseGLWidget ──→ SensorPanel.update_pir()
DataBridge ──→ 전체 패널 브로드캐스트
SensorSimulator (500ms) ──→ DataBridge ──→ 각 패널
```

**5. 레이아웃 구조**
```
QMainWindow
├── top_layout (QHBoxLayout)
│   ├── HouseGLWidget (좌측 2/3)
│   └── right_panel (우측 1/3)
│       ├── SensorPanel
│       ├── KevinStatusPanel
│       ├── ScenarioPanel
│       └── ControlPanel
└── EventLogWidget (하단 150px 고정)
```

**6. 테마 시스템**
- Kevin Patrol 참조: Cyber / Classic / Ironman 3가지 테마 적용 예정

### 다음 작업 (오늘 구현 예정)

- [ ] Step 1: `gui/opengl_widget.py` — house_model.py QOpenGLWidget 이식
- [ ] Step 2: `digital_twin/data_bridge.py` — 시그널-슬롯 브릿지
- [ ] Step 3: `gui/sensor_panel.py` + `gui/control_panel.py` — 패널 UI
- [ ] Step 4: `gui/event_log_widget.py` — 이벤트 로그
- [ ] Step 5: `gui/main_dashboard.py` — 전체 조립 + 시그널 연결
- [ ] Step 6: 테마 + 통합 테스트

### 오늘의 작업 요약 (2026-02-20)

- Phase 4 PyQt6 대시보드 + 3D 뷰 내장 설계 완료
- QOpenGLWidget 기반 통합 아키텍처 확정
- DataBridge 패턴으로 향후 ROS2 연동 포인트 확보
- 시그널-슬롯 연결도 및 구현 순서 정의

---

## 2026-02-19 | v0.4.0 센서 시뮬레이션 + 외출 자동화

### 작업 내용

#### 변경된 파일 목록

| 파일 | 버전 | 변경 내용 |
|------|------|-----------|
| `digital_twin/house_model.py` | v0.4 | 센서 통합, PIR 인디케이터, 알람 상태 시각화 |
| `digital_twin/sensor_simulator.py` | v0.2 | 외출 LED 소등, 알람 Armed 연동 |
| `docs/DEV_RULES.md` | v1.0 | 개발 원칙 문서 신규 작성 |
| `docs/Kevin_Smart_Home_Design.md` | v1.0 | 전체 설계 문서 신규 작성 |

#### 핵심 구현 사항

**1. 3D 하우스 모델 (house_model.py)**
- PyOpenGL 기반 1층 + 차고 6개 공간 박스 렌더링
- 반투명 벽 + 와이어프레임 외곽선
- LED 점등 시각화 (천장 발광 + 바닥 반사광)
- PIR 감지 인디케이터 (천장 빨간 원)
- 알람 상태별 와이어프레임 색상 (Disarmed: 기본 / Armed: 빨간색)
- HUD 오버레이 (센서현황 / 알람상태 / 이벤트로그)

**2. 센서 시뮬레이터 (sensor_simulator.py)**
- PIR / 온도 / 습도 / 조도 실시간 시뮬레이션
- 시간대별 환경값 자동 변화 (오전/오후/저녁/야간)
- 사람 동선 자동 PIR 트리거

**3. 오전 동선 시나리오**
```
안방 → 욕실 → 주방 → 거실 → 현관 → 차고
                                      ↓
                              🚗 외출 완료
                              💡 전체 LED 자동 소등
                              🔒 알람 Armed
```

**4. 저녁 귀가 동선**
```
현관 → 거실 → 욕실 → 주방 → 거실 → 안방
                                      ↓
                              🏠 귀가 완료
                              🔓 알람 Disarmed
```

#### 조작키 정리

| 키 | 기능 |
|----|------|
| `1~6` | 각 공간 LED 토글 |
| `A` | 전체 LED ON |
| `S` | 전체 LED OFF |
| `M` | 오전 동선 시작 (→차고→외출→소등) |
| `E` | 저녁 동선 시작 (귀가) |
| `T` | 시간대 전환 (오전→오후→저녁→야간) |
| 마우스 드래그 | 3D 뷰 회전 |
| 스크롤 | 줌 인/아웃 |

### 개발 원칙 확인 (DEV_RULES)

- [x] 원칙 1: 통합 버전으로 파일 전체 제공
- [x] 원칙 2: 일일 작업 DEV_LOG 기록
- [x] 원칙 3: 기존 프로젝트 파일 수정 없음

### 다음 작업 (Phase 2 후보)

- [ ] PyQt6 대시보드에 3D 뷰 내장 ← **2026-02-20 진행 중**
- [ ] ROS2 노드 구성 (kevin-01/02/03)
- [ ] 시나리오 엔진 (LangGraph)
- [ ] 낮 시간 침입 감지 시나리오
- [ ] 저녁 차량 도착 → 차고문 자동 개방 시나리오

### 오늘의 작업 요약 (2026-02-19)

- Kevin Smart Home 프로젝트 설계 및 구조 세팅 완료
- DEV_RULES 개발 원칙 문서 작성
- 3D 하우스 모델 v0.1 → v0.4 까지 반복 개선
- 센서 시뮬레이터 구현 (PIR/온도/습도/조도)
- 오전 동선 → 외출 → LED 소등 → 알람 Armed 자동화 완성
- 전체 정상 동작 확인

---

*Kevin Smart Home | 2026-02-20 | Phase 4 설계 완료*
