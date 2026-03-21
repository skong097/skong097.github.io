---
title: "Kevin Smart Home — Phase 4 설계 문서"
date: 2026-03-21
draft: true
tags: ["dev-tools", "pyqt6"]
categories: ["dev-tools"]
description: "> **버전:** v1.0.0 > **작성일:** 2026-02-20 > **작성자:** Stephen Kong"
---

# Kevin Smart Home — Phase 4 설계 문서
## PyQt6 대시보드 + 3D 뷰 내장

> **버전:** v1.0.0  
> **작성일:** 2026-02-20  
> **작성자:** Stephen Kong  
> **참조 문서:** Kevin_Smart_Home_Design.md v1.0.0, DEV_LOG.md v0.4.0  
> **참조 프로젝트:** Kevin Patrol Dashboard (`/home/gjkong/dev_ws/kevin_patrol/`)

---

## 1. 목표 (Goal)

v0.4.0까지 독립 실행 중이던 **PyOpenGL 3D 하우스 모델**을  
**PyQt6 대시보드 내에 내장**하여 하나의 통합 애플리케이션으로 구성한다.

### 완성 시 기능 요약

```
┌─────────────────────────────────────────────────────────────┐
│  Kevin Smart Home Dashboard v1.0          [🌙 테마 선택 ▼]  │
├──────────────────────────┬──────────────────────────────────┤
│                          │  📡 센서 패널                     │
│   [PyOpenGL 3D 뷰]       │  온도: 22.5°C   습도: 55%        │
│                          │  조도: 450lux   가스: 정상        │
│   - LED 점등 시각화       ├──────────────────────────────────┤
│   - PIR 인디케이터        │  🤖 Kevin 상태                   │
│   - 알람 와이어프레임      │  kevin-01: 🟢 외출 중            │
│   - 차고문 애니메이션      │  kevin-02: 🔵 청소 중            │
│                          │  kevin-03: 🟡 대기               │
│   [회전] [줌] [리셋]      ├──────────────────────────────────┤
│                          │  🎬 시나리오                      │
│                          │  현재: ☀️ 낮 시나리오             │
│                          │  [오전] [오후] [저녁] [야간]      │
│                          ├──────────────────────────────────┤
│                          │  💡 공간 LED 제어                 │
│                          │  [현관] [거실] [주방] [욕실]      │
│                          │  [안방] [차고] [전체ON] [전체OFF] │
├──────────────────────────┴──────────────────────────────────┤
│  📋 이벤트 로그                                              │
│  [14:32] kevin-02 청소 완료 — 거실                           │
│  [14:15] 외부 PIR 감지 → 알람 발송                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 핵심 기술 과제

### 2.1 PyQt6 + PyOpenGL 통합 방식

PyQt6에서 OpenGL을 사용하는 표준 방법은 `QOpenGLWidget`을 상속받는 것이다.  
기존 `house_model.py`(GLUT 기반)는 **직접 내장 불가** — 반드시 `QOpenGLWidget`로 재구성해야 한다.

```
기존 구조 (GLUT 기반, 독립 실행)
  glutInit → glutCreateWindow → glutMainLoop
  ❌ PyQt6에 내장 불가

변경 구조 (QOpenGLWidget 기반, PyQt6 내장)
  QOpenGLWidget.initializeGL()    ← GL 초기화
  QOpenGLWidget.paintGL()         ← 매 프레임 렌더링
  QOpenGLWidget.resizeGL()        ← 창 크기 변경 대응
  ✅ PyQt6 레이아웃에 위젯으로 삽입 가능
```

### 2.2 렌더링 루프 타이머

GLUT의 `glutTimerFunc` 대신 PyQt6의 `QTimer`를 사용한다.

```python
self.timer = QTimer()
self.timer.timeout.connect(self.update)  # update() → paintGL() 호출
self.timer.start(16)  # ~60fps
```

### 2.3 마우스 이벤트 전달

PyQt6 이벤트 시스템으로 OpenGL 뷰 회전/줌을 처리한다.

```python
def mousePressEvent(self, event): ...
def mouseMoveEvent(self, event): ...
def wheelEvent(self, event): ...
```

---

## 3. 파일 구조 (Phase 4 신규/변경)

```
kevin_smart_home/
│
├── gui/
│   ├── main_dashboard.py          ← 🆕 PyQt6 메인 윈도우
│   ├── opengl_widget.py           ← 🆕 QOpenGLWidget 기반 3D 뷰
│   ├── sensor_panel.py            ← 🆕 센서 데이터 패널
│   ├── control_panel.py           ← 🆕 LED / 시나리오 제어
│   └── event_log_widget.py        ← 🆕 이벤트 로그 위젯
│
├── digital_twin/
│   ├── house_model.py             ← ✏️ v0.4 → v0.5 (QOpenGLWidget 호환)
│   ├── sensor_simulator.py        ← ✏️ v0.2 → v0.3 (시그널 연동)
│   └── data_bridge.py             ← 🆕 GUI ↔ 3D 모델 데이터 브릿지
│
└── main_dashboard.py              ← 🆕 진입점 (dashboard 모드)
```

> ⚠️ DEV_RULES 원칙 3 준수: Kevin Patrol 코드는 복사 후 수정

---

## 4. 모듈 설계

### 4.1 `gui/opengl_widget.py` — 핵심 모듈

`QOpenGLWidget`을 상속받아 기존 `house_model.py`의 렌더링 로직을 이식한다.

```python
class HouseGLWidget(QOpenGLWidget):
    """
    PyQt6 QOpenGLWidget 기반 3D 하우스 렌더러
    house_model.py 렌더링 로직을 QOpenGLWidget으로 이식
    """
    # 시그널 정의
    room_clicked = pyqtSignal(str)          # 공간 클릭 시 → 제어 패널 연동
    pir_triggered = pyqtSignal(str, bool)   # PIR 상태 변화 → 센서 패널 연동

    def initializeGL(self): ...   # GL 초기화 (조명, 블렌딩 등)
    def paintGL(self): ...        # 매 프레임 렌더링 (house_model 로직)
    def resizeGL(self, w, h): ... # 뷰포트 조정
    
    # 외부 제어 메서드
    def set_led_state(self, room: str, state: bool): ...
    def set_alarm_state(self, state: str): ...        # armed / disarmed
    def set_pir_state(self, room: str, active: bool): ...
    def trigger_scenario(self, scenario: str): ...   # morning / evening
```

### 4.2 `gui/main_dashboard.py` — 메인 윈도우

```python
class MainDashboard(QMainWindow):
    """
    Kevin Smart Home 메인 대시보드
    레이아웃: 좌측 3D 뷰 (2/3) + 우측 제어 패널 (1/3) + 하단 이벤트 로그
    """
    def __init__(self):
        # 위젯 초기화
        self.gl_widget = HouseGLWidget()       # 3D 뷰
        self.sensor_panel = SensorPanel()      # 센서 현황
        self.control_panel = ControlPanel()    # LED/시나리오 제어
        self.event_log = EventLogWidget()      # 이벤트 로그
        self.kevin_status = KevinStatusPanel() # Kevin 로봇 상태
        
        # 시그널 연결
        self._connect_signals()
        
        # 센서 시뮬레이터 타이머
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self._update_sensor_data)
        self.sim_timer.start(500)  # 0.5초마다 센서 업데이트
```

### 4.3 `digital_twin/data_bridge.py` — 데이터 브릿지

GUI와 3D 모델 사이의 상태 동기화를 담당한다.  
향후 ROS2 연동 시 이 모듈만 수정하면 된다.

```python
class DataBridge(QObject):
    """
    GUI ↔ digital_twin 데이터 동기화
    현재: sensor_simulator.py 연동
    향후: ROS2 TwinSyncNode 연동으로 교체 예정
    """
    # 센서 데이터 변경 시그널
    sensor_updated = pyqtSignal(dict)
    
    # LED 제어 시그널  
    led_changed = pyqtSignal(str, bool)   # room, state
    
    # 알람 상태 시그널
    alarm_changed = pyqtSignal(str)       # armed / disarmed / triggered
    
    # 이벤트 로그 시그널
    event_logged = pyqtSignal(str)        # 로그 메시지
```

### 4.4 `gui/control_panel.py` — 제어 패널

```python
class ControlPanel(QWidget):
    """
    LED 제어 + 시나리오 제어 통합 패널
    """
    # LED 버튼 (1~6 공간)
    # 전체 ON / 전체 OFF
    # 시나리오 버튼 (오전/오후/저녁/야간)
    # 알람 상태 표시 + 수동 제어
```

### 4.5 `gui/sensor_panel.py` — 센서 패널

```python
class SensorPanel(QWidget):
    """
    실시간 센서 데이터 표시
    온도 / 습도 / 조도 / 가스 / PIR 상태
    """
    def update_sensors(self, sensor_data: dict): ...
```

---

## 5. 레이아웃 구조 (PyQt6)

```python
# 전체 레이아웃
QMainWindow
├── centralWidget (QWidget)
│   └── main_layout (QVBoxLayout)
│       ├── top_layout (QHBoxLayout)          # 상단: 3D뷰 + 우측패널
│       │   ├── gl_widget (HouseGLWidget)      # 좌측 2/3
│       │   └── right_panel (QVBoxLayout)      # 우측 1/3
│       │       ├── sensor_panel (SensorPanel)
│       │       ├── kevin_status (KevinStatusPanel)
│       │       ├── scenario_panel (QGroupBox)
│       │       └── control_panel (ControlPanel)
│       └── event_log (EventLogWidget)         # 하단 고정 높이 150px
└── statusBar
    └── 현재 시나리오 / 알람 상태
```

---

## 6. 시그널-슬롯 연결도

```
[ControlPanel]                  [HouseGLWidget]
  led_toggle_btn.clicked ──────→ gl_widget.set_led_state()
  scenario_btn.clicked   ──────→ gl_widget.trigger_scenario()
  alarm_btn.clicked      ──────→ gl_widget.set_alarm_state()

[HouseGLWidget]                 [UI 패널]
  room_clicked           ──────→ control_panel.highlight_room()
  pir_triggered          ──────→ sensor_panel.update_pir()

[DataBridge]                    [전체]
  sensor_updated         ──────→ sensor_panel.update_sensors()
  led_changed            ──────→ gl_widget.set_led_state()
  alarm_changed          ──────→ gl_widget.set_alarm_state()
  event_logged           ──────→ event_log.append_log()

[SensorSimulator → DataBridge]
  500ms 타이머           ──────→ bridge.update_simulation()
                         ──────→ sensor_updated 시그널 발생
```

---

## 7. house_model.py v0.5 변경 사항

| 항목 | v0.4 (GLUT) | v0.5 (QOpenGLWidget) |
|------|-------------|----------------------|
| 초기화 | `glutInit()` | `initializeGL()` |
| 렌더 루프 | `glutMainLoop()` | `QTimer → update()` |
| 마우스 | `glutMouseFunc()` | `mousePressEvent()` |
| 키보드 | `glutKeyboardFunc()` | 외부 시그널로 대체 |
| 창 생성 | `glutCreateWindow()` | PyQt6가 관리 |
| 렌더링 | `glutDisplayFunc()` | `paintGL()` |

> ✅ 렌더링 로직(박스, LED, PIR, 알람 색상 등)은 **100% 재사용**  
> ✅ GLUT 의존성만 제거하고 QOpenGLWidget 인터페이스로 교체

---

## 8. 테마 시스템

Kevin Patrol 참조: 3가지 테마 (Cyber / Classic / Ironman) 방식 적용

```python
THEMES = {
    "cyber": {
        "bg": "#0a0f1e",
        "panel_bg": "#0d1526",
        "accent": "#00d4ff",
        "text": "#e0f0ff",
        "border": "#1a3a5c",
    },
    "classic": {
        "bg": "#1e1e2e",
        "panel_bg": "#252535",
        "accent": "#7c3aed",
        "text": "#e0e0f0",
        "border": "#3a3a5c",
    },
    "ironman": {
        "bg": "#1a0a0a",
        "panel_bg": "#2a0f0f",
        "accent": "#ff4444",
        "text": "#ffe0e0",
        "border": "#5c1a1a",
    }
}
```

---

## 9. 구현 순서 (오늘 작업 계획)

```
Step 1. opengl_widget.py 구현
  └─ house_model.py v0.4 → QOpenGLWidget 이식
  └─ 렌더링 정상 확인

Step 2. data_bridge.py 구현
  └─ sensor_simulator.py 연동
  └─ 시그널-슬롯 정의

Step 3. sensor_panel.py / control_panel.py 구현
  └─ 기본 UI 구성

Step 4. event_log_widget.py 구현
  └─ 스크롤 가능한 로그 텍스트

Step 5. main_dashboard.py 구현
  └─ 전체 레이아웃 조립
  └─ 시그널 연결

Step 6. 테마 적용 + 통합 테스트
```

---

## 10. 의존성 (requirements.txt 추가)

```
# 기존 유지
PyOpenGL>=3.1.7
PyOpenGL_accelerate>=3.1.7
numpy>=1.24.0

# Phase 4 추가
PyQt6>=6.4.0
PyQt6-Qt6>=6.4.0
PyQt6-sip>=13.4.0
```

---

## 11. 다음 Phase 연동 포인트

Phase 4 완료 후 Phase 2 (ROS2) 연동 시:

```python
# data_bridge.py 내부만 수정
# GUI / 3D 렌더링 코드는 변경 없음

# 현재 (Phase 4)
self.sim_timer.timeout.connect(self._update_from_simulator)

# Phase 2 연동 후
self.ros2_subscriber.callback.connect(self._update_from_ros2)
```

---

*Kevin Smart Home | Phase 4 설계 v1.0.0 | 2026-02-20*
