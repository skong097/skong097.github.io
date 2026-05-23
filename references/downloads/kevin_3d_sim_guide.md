<div align="center">

# 🤖 Kevin 3D Patrol Simulator

**ROS2 자율순찰 로봇 3D 시뮬레이터**

Pygame + OpenGL 기반 · SLAM 맵 빌딩 · LiDAR 시각화 · Nav2 순찰

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.x-00AA00?logo=pygame)
![OpenGL](https://img.shields.io/badge/OpenGL-4.x-5586A4?logo=opengl)
![License](https://img.shields.io/badge/License-MIT-yellow)

</div>

---

## 📋 목차

- [소개](#-소개)
- [주요 기능](#-주요-기능)
- [시스템 요구사항](#-시스템-요구사항)
- [설치](#-설치)
- [빠른 시작](#-빠른-시작)
- [조작 가이드](#-조작-가이드)
- [기능 상세](#-기능-상세)
- [화면 구성](#-화면-구성)
- [ROS2 토픽 시뮬레이션](#-ros2-토픽-시뮬레이션)
- [설정 커스터마이징](#-설정-커스터마이징)
- [트러블슈팅](#-트러블슈팅)
- [프로젝트 구조](#-프로젝트-구조)
- [로드맵](#-로드맵)
- [관련 프로젝트](#-관련-프로젝트)

---

## 🎯 소개

Kevin 3D Patrol Simulator는 ROS2 기반 자율순찰 로봇 **Kevin**의 동작을 3D 환경에서 시뮬레이션하는 교육·개발용 도구입니다.

실제 로봇 시스템에서 사용하는 SLAM, LiDAR, Nav2 네비게이션, 낙상 감지 등의 핵심 기능을 시각적으로 체험하고 학습할 수 있습니다. 모든 데이터 구조는 ROS2 토픽 메시지 포맷과 1:1 대응하도록 설계되어 있어, 향후 실제 로봇 데이터와의 연동을 목표로 합니다.

### 이런 분에게 추천합니다

- ROS2 로봇 시스템의 동작 원리를 시각적으로 이해하고 싶은 분
- SLAM, LiDAR, Nav2 개념을 직접 조작하며 배우고 싶은 분
- 자율순찰 로봇 프로젝트의 프로토타입을 빠르게 확인하고 싶은 분

---

## ✨ 주요 기능

### 🏗 3D 환경
40×40 단위의 실내 맵에서 벽, 복도, 장애물로 구성된 순찰 환경을 탐색합니다. 1인칭, 3인칭, 탑뷰 카메라를 전환하며 다양한 시점에서 관찰할 수 있습니다.

### 📡 LiDAR 360° 시각화
72개 레이의 레이캐스트가 실시간으로 동작합니다. 벽이나 장애물에 부딪힌 지점은 히트 포인트로 표시되고, 거리에 따라 색상이 변합니다.

### 🗺 SLAM 맵 빌딩
로봇이 이동하면 Log-odds 기반 occupancy grid가 실시간으로 생성됩니다. 탐색한 영역(Free), 장애물(Occupied), 탐색 경계(Frontier) 셀이 3D 공간과 미니맵에 동시에 표시됩니다.

### 🧭 Nav2 자동 순찰
TAB 키를 누르면 10개 웨이포인트를 따라 자동으로 순찰합니다. 부드러운 회전과 거리 기반 속도 조절이 적용됩니다.

### 🚨 낙상 감지 시뮬레이션
맵에 배치된 5명의 사람 중 가장 가까운 사람에게 낙상 이벤트를 발생시킬 수 있습니다. 알림 오버레이와 토픽 상태가 실시간으로 변경됩니다.

### 📊 ROS2 토픽 모니터
10개 ROS2 스타일 토픽의 활성 상태, 발행 주기(Hz), 데이터 내용을 HUD 패널에서 실시간으로 확인할 수 있습니다.

---

## 💻 시스템 요구사항

| 항목 | 최소 | 권장 |
|---|---|---|
| OS | Windows 10 / Ubuntu 20.04 / macOS 12 | Ubuntu 22.04+ |
| Python | 3.10 | 3.11+ |
| GPU | OpenGL 3.3 지원 | OpenGL 4.x 지원 |
| RAM | 4GB | 8GB+ |
| 디스플레이 | 1280×800 | 1920×1080+ |

---

## 📦 설치

### 1. 저장소 클론

```bash
git clone https://github.com/skong097/vision_ai.git
cd vision_ai
```

### 2. 의존성 설치

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate numpy
```

> **참고**: `PyOpenGL_accelerate`는 선택 사항이지만 성능 향상을 위해 권장합니다. 설치에 실패하면 `PyOpenGL`과 `numpy`만으로도 동작합니다.

### 3. 실행 확인

```bash
python kevin_3d_sim.py
```

화면 중앙에 **"클릭하여 시점 제어 시작"** 메시지가 나타나면 정상 실행입니다.

---

## 🚀 빠른 시작

### Step 1: 실행 후 화면 클릭

프로그램을 실행하면 3D 환경이 나타납니다. 화면을 **좌클릭**하면 마우스가 캡처되어 시점 이동 모드로 진입합니다.

### Step 2: 로봇 조종

`W` `A` `S` `D` 키로 이동하고, 마우스로 시점을 회전합니다. `L` 키를 눌러 LiDAR 레이저가 사방으로 뻗어나가는 것을 확인합니다.

### Step 3: 자동 순찰

`TAB` 키를 누르면 Kevin 로봇이 미리 설정된 웨이포인트를 따라 자동 순찰을 시작합니다. 미니맵(`M`)에서 경로를 확인하세요.

### Step 4: SLAM 맵 확인

로봇이 이동하면 SLAM 맵이 자동으로 생성됩니다. 바닥에 녹색(Free)과 주황색(Occupied) 셀이 나타납니다. `G` 키로 3D 시각화를 토글할 수 있습니다.

### Step 5: 낙상 감지

`F` 키를 누르면 가장 가까운 사람에게 낙상 이벤트가 발생합니다. 화면이 빨갛게 깜빡이며 경보가 울립니다.

---

## 🎮 조작 가이드

### 이동 및 시점

| 키 | 기능 | 설명 |
|---|---|---|
| `W` | 전진 | 로봇이 바라보는 방향으로 이동 |
| `S` | 후진 | 뒤로 이동 |
| `A` | 좌측 이동 | 좌측 스트레이프 |
| `D` | 우측 이동 | 우측 스트레이프 |
| `마우스` | 시점 회전 | 마우스 캡처 상태에서 상하좌우 시점 제어 |

### 카메라 모드

| 키 | 모드 | 설명 |
|---|---|---|
| `1` | 1인칭 | 로봇 카메라 시점 (eye_y=1.2m) |
| `2` | 3인칭 | 로봇 뒤에서 따라가는 팔로우 카메라 |
| `3` | 탑뷰 | 위에서 내려다보는 전략 뷰 (높이 25m) |

> **팁**: 탑뷰(`3`)에서 전체 맵 구조와 SLAM 진행 상황을 한눈에 파악할 수 있습니다.

### 기능 토글

| 키 | 기능 | 기본 상태 |
|---|---|---|
| `TAB` | 자동 순찰 모드 ON/OFF | OFF |
| `L` | LiDAR 시각화 ON/OFF | ON |
| `M` | 미니맵 ON/OFF | ON |
| `G` | SLAM 3D 시각화 ON/OFF | ON |
| `F` | 낙상 이벤트 트리거 | - |
| `R` | SLAM 맵 리셋 (초기화) | - |

### 화면 / 마우스 제어

| 키 | 기능 |
|---|---|
| `화면 클릭` | 마우스 캡처 → 시점 이동 모드 |
| `ALT` | 마우스 해제 → 커서 자유 이동 |
| `ESC` (1회) | 마우스 캡처 해제 |
| `ESC` (2회) | 프로그램 종료 |
| `F11` | 전체 화면 ↔ 창 모드 전환 |

> **팁**: 마우스 캡처 상태에서 `ALT`를 누르면 커서가 자유로워집니다. 다시 화면을 클릭하면 시점 제어로 돌아갑니다.

---

## 🔍 기능 상세

### SLAM Occupancy Grid

로봇이 이동하면서 LiDAR 스캔 데이터를 기반으로 주변 환경의 지도를 실시간으로 구축합니다.

**동작 원리**:
1. 72개 LiDAR 레이가 주변 벽/장애물까지의 거리를 측정
2. Bresenham 라인 알고리즘으로 레이 경로상의 셀을 Free로 마킹
3. 레이가 충돌한 지점의 셀을 Occupied로 마킹
4. Log-odds 확률 모델로 반복 관측치를 누적하여 신뢰도 향상

**셀 종류**:

| 셀 | 색상 | 의미 |
|---|---|---|
| Unknown | 표시 안 됨 | 아직 스캔되지 않은 영역 |
| Free | 🟢 녹색 (바닥 레이어) | 장애물이 없는 통행 가능 영역 |
| Occupied | 🟠 주황색 (블록) | 벽이나 장애물이 감지된 영역 |
| Frontier | 🔵 청색 (경계) | Free와 Unknown의 경계 (탐색 전선) |

**그리드 사양**:
- 해상도: 0.5m × 0.5m 셀
- 그리드 크기: 88 × 88 (7,744 셀)
- 업데이트 주기: 3프레임마다 (약 20Hz)

> **팁**: `R` 키로 SLAM 맵을 리셋하고, `TAB`으로 자동 순찰을 활성화하면 로봇이 이동하면서 자동으로 맵을 채워나가는 과정을 관찰할 수 있습니다.

### Nav2 자동 순찰

10개 웨이포인트가 맵 전역에 배치되어 있으며, `TAB`으로 자동 순찰을 활성화하면 로봇이 순서대로 방문합니다.

**순찰 특성**:
- 목표 웨이포인트까지 부드러운 회전 (yaw_diff × 0.05)
- 거리 기반 속도 조절 (가까울수록 감속)
- 웨이포인트 1.0m 이내 도달 시 다음 WP로 전환
- 마지막 WP 도달 후 처음부터 반복 (무한 루프)

### 낙상 감지

`F` 키를 누르면 로봇에서 가장 가까운 사람에게 낙상 이벤트가 발생합니다.

**시퀀스**:
1. 가장 가까운 사람의 모델이 쓰러진 상태로 변경
2. 화면에 빨간색 알림 오버레이 표시 (5초)
3. `/detection` 토픽이 `FALL DETECTED!`로 변경
4. `/alert` 토픽이 `⚠ EMERGENCY`로 활성화
5. 5초 후 사람 복구 및 알림 해제

### 카메라 시스템

**1인칭 (키 `1`)**: 로봇 상단 카메라 위치(y=1.2m)에서 바라보는 시점. pitch 제어 가능 (상하 ±60°).

**3인칭 (키 `2`)**: 로봇 뒤 5m, 높이 3m에서 따라가는 카메라. 전체적인 상황 파악에 유리.

**탑뷰 (키 `3`)**: 높이 25m에서 수직으로 내려다보는 뷰. SLAM 맵 빌딩 과정을 전체적으로 관찰할 때 유용.

---

## 🖥 화면 구성

```
┌─────────────────────────────────────────────────────────┐
│  [조작 도움말 바]                                        │
│  WASD:이동  Mouse:시점  TAB:순찰모드  F11:전체화면       │
├───────────────────────────────────────┬─────────────────┤
│                                       │ 📡 ROS2 Topic  │
│                                       │    Monitor      │
│            3D Viewport                │─────────────────│
│                                       │ /cmd_vel   50Hz │
│         로봇 · 맵 · LiDAR · SLAM     │ /scan      10Hz │
│         사람 · 웨이포인트              │ /odom      50Hz │
│                                       │ /map        1Hz │
│                                       │ /detection 10Hz │
│                                       │ ...             │
├──────────┐                            │                 │
│ 🗺 MAP   │                            │                 │
│ 미니맵 + │                            │                 │
│ SLAM     │                            │                 │
│ 오버레이 │                            │                 │
└──────────┴────────────────────────────┴─────────────────┤
│ 🎮 MANUAL │ LiDAR:ON │ CAM:3인칭 │ SLAM:45% │ FPS:60  │
└─────────────────────────────────────────────────────────┘
```

| 영역 | 위치 | 설명 |
|---|---|---|
| 조작 도움말 | 상단 중앙 | 주요 키 안내 (항상 표시) |
| 3D Viewport | 전체 배경 | OpenGL 3D 렌더링 영역 |
| Topic Monitor | 우측 상단 | ROS2 토픽 10개 실시간 상태 |
| 미니맵 | 좌측 하단 | 190×190px, 벽/장애물/WP/로봇/SLAM 오버레이 |
| 상태 바 | 하단 전체 | 모드, LiDAR, 카메라, SLAM 탐사율, FPS |
| 알림 오버레이 | 전체 화면 | 낙상 감지 시 빨간색 플래시 + 경보 메시지 |
| 마우스 힌트 | 중앙 | 마우스 해제 상태일 때만 표시 |

---

## 📡 ROS2 토픽 시뮬레이션

시뮬레이터는 실제 ROS2 시스템을 모사하여 10개 토픽의 상태를 시뮬레이션합니다.

| 토픽 | 메시지 타입 | 발행 주기 | 설명 |
|---|---|---|---|
| `/cmd_vel` | Twist | 50Hz (이동 시) | 로봇 선속도·각속도 명령 |
| `/scan` | LaserScan | 10Hz | 360° LiDAR 스캔 데이터 |
| `/image_raw` | Image | 30Hz | 카메라 영상 (640×480 rgb8) |
| `/odom` | Odometry | 50Hz | 로봇 위치 추정 (x, y) |
| `/detection` | Detection | 10Hz | 낙상 감지 결과 |
| `/alert` | String | 1Hz (알림 시) | 긴급 알림 메시지 |
| `/robot_status` | String | 상시 | 로봇 모드 (auto_patrol / manual) |
| `/nav2/path` | Path | 1Hz (순찰 시) | 순찰 경로 웨이포인트 |
| `/map` | OccupancyGrid | 1Hz (SLAM 시) | SLAM 맵 탐사율 |
| `/slam/status` | String | 1Hz (SLAM 시) | SLAM 상태 (mapping / idle) |

> **참고**: 이 토픽들은 시뮬레이션 내부에서 상태를 관리하며, 실제 ROS2 네트워크에 발행하지는 않습니다. 향후 rosbridge 연동을 통해 실제 로봇 데이터로 교체할 수 있도록 설계되어 있습니다.

---

## ⚙ 설정 커스터마이징

`kevin_3d_sim.py` 상단의 상수를 수정하여 동작을 조정할 수 있습니다.

### 화면 설정

```python
WIDTH, HEIGHT = 1280, 800    # 기본 창 크기 (F11으로 전체 화면 전환 가능)
FPS = 60                      # 목표 프레임 레이트
```

### 로봇 동작

```python
MOVE_SPEED = 0.08             # 이동 속도 (높을수록 빠름)
MOUSE_SENSITIVITY = 0.2       # 마우스 감도 (높을수록 민감)
```

### 맵 환경

```python
MAP_SIZE = 40                 # 맵 크기 (단위: 미터)
WALL_HEIGHT = 2.5             # 벽 높이
GRID_SIZE = 2                 # 벽 블록 간격
```

### SLAM 설정

```python
SLAM_RESOLUTION = 0.5         # occupancy grid 셀 크기 (미터)
# SLAMVisualizer 클래스 내부:
self.l_free = -0.4            # Free 관측 log-odds 감소량
self.l_occ = 0.85             # Occupied 관측 log-odds 증가량
self.l_max = 5.0              # log-odds 상한
self.l_min = -3.0             # log-odds 하한
```

### 웨이포인트 편집

순찰 경로를 변경하려면 `PATROL_WAYPOINTS` 리스트를 수정합니다:

```python
PATROL_WAYPOINTS = [
    (-8, -12), (-8, 0), (-8, 12),
    (0, 12), (8, 12),
    (12, 4), (12, -4),
    (12, -12), (4, -12), (0, -12),
]
```

좌표는 `(x, z)` 형식이며, 맵 중심이 `(0, 0)`, 범위는 `-20 ~ +20`입니다.

---

## 🔧 트러블슈팅

### OpenGL 관련 오류

**증상**: `OpenGL.error.NullFunctionError` 또는 검은 화면

```bash
# GPU 드라이버 확인
glxinfo | grep "OpenGL version"

# Mesa 소프트웨어 렌더러 사용 (GPU 없는 환경)
export LIBGL_ALWAYS_SOFTWARE=1
python kevin_3d_sim.py
```

### PyOpenGL_accelerate 설치 실패

```bash
# accelerate 없이도 동작합니다
pip install pygame PyOpenGL numpy
```

### 한글 폰트가 깨지는 경우

시스템에 다음 폰트 중 하나가 필요합니다:
- NanumGothic (나눔고딕)
- Malgun Gothic (맑은 고딕)
- NotoSansCJK (노토 산스)
- D2Coding

```bash
# Ubuntu에서 나눔고딕 설치
sudo apt install fonts-nanum
```

### 마우스가 잠기는 경우

`ALT` 키 또는 `ESC`를 누르면 마우스 캡처가 해제됩니다. 프로그램이 응답하지 않을 경우 `Ctrl+C` (터미널) 또는 `Alt+F4`를 사용하세요.

### 프레임 레이트가 낮은 경우

1. LiDAR 시각화를 끕니다 (`L` 키)
2. SLAM 3D 시각화를 끕니다 (`G` 키)
3. 전체 화면 대신 작은 창 모드를 사용합니다

---

## 📁 프로젝트 구조

```
kevin_3d_sim.py              ← 메인 시뮬레이션 (1,661 lines)
kevin_3d_sim_guide.md        ← 이 사용 가이드
kevin_3d_sim_dev.md          ← 개발 문서 (아키텍처, 변경 이력, 로드맵)
ros2_commander.py            ← ROS2 학습 게임 (별도 프로젝트)
```

### 주요 클래스

| 클래스 | 역할 |
|---|---|
| `Kevin3DSim` | 메인 시뮬레이션 루프, 이벤트 처리, 렌더링 |
| `SLAMVisualizer` | Occupancy grid 생성·시각화 |
| `SpatialHash` | 공간 해시 기반 충돌 검사 |
| `StaticMeshCache` | DisplayList 정적 메시 캐싱 |
| `TopicMonitor` | ROS2 토픽 상태 시뮬레이션 |
| `HUD` | 2D 오버레이 (토픽 패널, 미니맵, 상태바) |
| `CameraMode` | 카메라 모드 Enum |

---

## 🗺 로드맵

이 시뮬레이터는 실제 Kevin 로봇과의 연동을 목표로 단계적으로 발전합니다.

```
Phase 1  시뮬레이션 고도화        ✅ 현재 (v1.0~v1.2)
Phase 2  데이터 추상화 레이어      🔲 ROS2 브릿지 준비
Phase 3  통합 모니터링 GUI         🔲 실제 로봇 + 시뮬 동시 지원
Phase 4  실전 배포                 🔲 Kevin 로봇 실기 연동
```

향후 실제 로봇의 카메라·LiDAR 센서 데이터가 `rosbridge` 또는 `Foxglove WebSocket`을 통해 실시간으로 대시보드에 반영되는 **통합 모니터링 GUI Dashboard**로 발전할 예정입니다. 자세한 로드맵은 [kevin_3d_sim_dev.md](kevin_3d_sim_dev.md)를 참고하세요.

---

## 🔗 관련 프로젝트

| 프로젝트 | 설명 |
|---|---|
| [ROS2 Commander](ros2_commander.py) | ROS2 개념 학습 게임 (Memory Match, Command Rush, Node Builder) |
| [Home Guard Bot](https://github.com/skong097/vision_ai) | Kevin 로봇 FastAPI + ROS2 Jazzy 실제 구현체 |
| [피노키오 (Pinocchio)](https://github.com/skong097/vision_ai) | 실시간 다중모달 심리분석 시스템 |

---

## 📄 라이선스

MIT License — 자유롭게 사용·수정·배포할 수 있습니다.

---

<div align="center">

**Kevin 3D Patrol Simulator** · Built with Pygame + OpenGL

ROS2 · SLAM · LiDAR · Nav2 · 자율순찰

</div>
