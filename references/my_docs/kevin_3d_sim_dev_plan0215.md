# Kevin 3D Patrol Simulator — 개발 문서

**프로젝트**: Kevin 3D Patrol Simulator  
**파일**: `kevin_3d_sim.py` (1,661 lines)  
**플랫폼**: Pygame + PyOpenGL  
**Python**: 3.10+  

---

## 변경 이력

| 날짜 | 버전 | 내용 |
|---|---|---|
| 2025-02-15 | v1.0 | 초기 버전 — 3D 환경, 로봇 모델, LiDAR, 순찰, 낙상 감지, HUD |
| 2025-02-15 | v1.1 | 전체 화면(F11), 마우스 캡처/해제(클릭/ALT), 동적 해상도 대응 |
| 2025-02-15 | v1.2 | SLAM occupancy grid 실시간 맵 빌딩, 공간 해시 충돌 최적화, DisplayList 정적 메시 캐싱 |

---

## 개요

Kevin 자율순찰 로봇을 3D 환경에서 시뮬레이션하는 게임.  
ROS2 토픽 모니터, LiDAR 시각화, Nav2 웨이포인트 순찰, 낙상 감지,  
SLAM occupancy grid 맵 빌딩 등 실제 로봇 시스템의 핵심 기능을 시각적으로 체험할 수 있다.

### 관련 프로젝트

- `ros2_commander.py` — ROS2 학습 게임 (Pygame 2D, Memory Match / Command Rush / Node Builder)
- Home Guard Bot — Kevin 로봇 FastAPI v0.2 + ROS2 Jazzy 실제 구현체

---

## 설치 및 실행

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate numpy
python kevin_3d_sim.py
```

---

## 조작법

### 이동 / 시점

| 키 | 기능 |
|---|---|
| WASD | 로봇 이동 (전/후/좌/우) |
| 마우스 | 시점 회전 (캡처 상태에서) |
| 1 / 2 / 3 | 카메라 모드 전환 (1인칭 / 3인칭 / 탑뷰) |

### 기능 토글

| 키 | 기능 |
|---|---|
| TAB | 자동 순찰 모드 (Nav2 웨이포인트 추종) |
| L | LiDAR 360° 시각화 ON/OFF |
| F | 낙상 이벤트 트리거 |
| M | 미니맵 ON/OFF |
| G | SLAM 3D 시각화 토글 (v1.2) |
| R | SLAM 맵 리셋 (v1.2) |

### 화면 / 마우스 제어

| 키 | 기능 |
|---|---|
| F11 | 전체 화면 ↔ 창 모드 전환 |
| 화면 클릭 | 마우스 캡처 (시점 이동 모드) |
| ALT | 마우스 해제 |
| ESC (1회) | 마우스 해제 / ESC (2회) | 종료 |

---

## 아키텍처

### 클래스 구조

```
Kevin3DSim                — 메인 시뮬레이션 루프 + 디스플레이 관리
│
├── SpatialHash           — 공간 해시 기반 O(1) 충돌 검사 (v1.2)
│
├── StaticMeshCache       — DisplayList 기반 정적 메시 캐싱 (v1.2)
│     build()               — 벽/바닥/장애물을 DisplayList로 사전 컴파일
│     draw_all()            — 단일 glCallList로 전체 정적 씬 렌더링
│
├── SLAMVisualizer        — Occupancy Grid 실시간 맵 빌딩 (v1.2)
│     update_from_lidar()   — LiDAR 스캔 → Bresenham ray march → log-odds 업데이트
│     draw_3d()             — free/occupied/frontier 셀 3D 시각화 (DisplayList 캐싱)
│     draw_on_minimap()     — 미니맵 위 SLAM 오버레이
│     get_exploration_pct() — 탐사율(%) 계산
│     reset()               — 맵 초기화
│
├── TopicMonitor          — ROS2 토픽 10개 상태 시뮬레이션
│     기존: /cmd_vel, /scan, /image_raw, /odom, /detection, /alert, /robot_status, /nav2/path
│     추가: /map (OccupancyGrid), /slam/status (v1.2)
│
├── HUD                   — 2D 오버레이 (OpenGL ortho)
│
└── CameraMode (Enum)     — FIRST_PERSON / THIRD_PERSON / TOP_VIEW
```

### 3D 렌더링 파이프라인

```
매 프레임:
  1. draw_skybox()                  — 배경 그라데이션
  2. mesh_cache.draw_all()          — 벽/바닥/장애물 (DisplayList, 1 draw call)
  3. slam.draw_3d()                 — SLAM occupancy grid (DisplayList, 조건부)
  4. draw_waypoint() × 10           — 웨이포인트 마커
  5. draw_person() × 5              — 사람 모델
  6. draw_lidar_rays_cached()       — LiDAR (캐시된 레이캐스트 결과)
  7. draw_robot()                   — Kevin 로봇 (3인칭/탑뷰 시)
  8. HUD 2D 오버레이                 — 토픽 모니터, 미니맵+SLAM, 상태바
```

---

## v1.2 핵심 변경사항

### 1. SLAM Occupancy Grid 실시간 맵 빌딩

**알고리즘**: Log-odds 기반 확률적 occupancy grid 업데이트

```
LiDAR 스캔 (72 rays, 12m range)
  → 공간 해시 기반 레이캐스트
  → Bresenham 라인으로 free/occupied 셀 결정
  → Log-odds 누적 (l_free=-0.4, l_occ=0.85)
  → 임계값 변환 (-0.5 이하=free, 0.5 이상=occupied)
```

- 그리드 해상도: 0.5m/셀 (88×88 = 7,744 셀)
- 3프레임마다 업데이트 (성능 균형)
- 3종류 셀 시각화: Free(녹색 바닥), Occupied(주황 블록), Frontier(청색 경계)
- 미니맵에 SLAM 오버레이 동시 표시
- 탐사율(%) 실시간 표시 (상태바 + /map 토픽)

### 2. 성능 최적화

#### DisplayList 정적 메시 캐싱 (StaticMeshCache)

```
Before: 매 프레임 벽 ~160개 × 6면 × glBegin/glEnd  → 수백 회 드로우콜
After:  사전 컴파일된 DisplayList 1회 glCallList     → 3 드로우콜 (바닥/벽/장애물)
```

#### 공간 해시 충돌 검사 (SpatialHash)

```
Before: 충돌 시 벽 160개 + 장애물 12개 전수 순회   → O(n) per query
After:  cell_size=3.0 해시 → 인접 9셀만 검사       → O(1) amortized
```

- LiDAR 레이캐스트에서도 공간 해시 사용 → 72 rays × 60 steps 에서 대폭 절감

#### LiDAR 결과 캐싱 (raycast_lidar + draw_lidar_rays_cached)

```
Before: 레이캐스트를 레이 그리기/히트포인트 2회 중복 수행
After:  raycast_lidar()로 1회 계산 → 결과를 렌더링 + SLAM 양쪽에 재사용
```

#### SLAM DisplayList

- SLAM 3D 시각화도 DisplayList로 캐싱
- 10프레임마다 리빌드 (occupancy 변경 시에만)

### 3. 추가된 ROS2 토픽

| 토픽 | 메시지 타입 | 데이터 예시 |
|---|---|---|
| `/map` | OccupancyGrid | `explored:45%` |
| `/slam/status` | String | `mapping` / `idle` |

---

## 개발 로드맵

### 설계 원칙

> 현재 시뮬레이션의 모든 데이터 구조(occupancy grid, LiDAR scan, odom, cmd_vel 등)는
> 실제 ROS2 토픽의 메시지 포맷과 1:1 대응하도록 설계한다.
> 이를 통해 **시뮬레이션 ↔ 실제 로봇** 간 데이터 소스만 교체하면
> 동일한 모니터링 GUI가 양쪽 모두에서 동작할 수 있도록 한다.

```
[Phase 1] 시뮬레이션 고도화        ← 현재 (v1.0~v1.2)
[Phase 2] 데이터 추상화 레이어      ← ROS2 브릿지 준비
[Phase 3] 통합 모니터링 GUI         ← 실제 로봇 + 시뮬 동시 지원
[Phase 4] 실전 배포                 ← Kevin 로봇 실기 연동
```

---

### Phase 1: 시뮬레이션 고도화 (현재 ~ v1.x)

v1.0~v1.2에서 완료된 항목과 남은 시뮬레이션 기능 보강.

| 항목 | 상태 | 설명 |
|---|---|---|
| 3D 환경 + 로봇 모델 | ✅ v1.0 | Pygame + OpenGL, Kevin 4륜 로봇 |
| LiDAR 360° 시각화 | ✅ v1.0 | 72-ray 레이캐스트, 거리 색상 |
| Nav2 웨이포인트 순찰 | ✅ v1.0 | 10개 WP 자동 추종 |
| 낙상 감지 이벤트 | ✅ v1.0 | 5명 사람, 알림 오버레이 |
| 전체 화면 / 마우스 제어 | ✅ v1.1 | F11, 클릭 캡처, ALT 해제 |
| SLAM occupancy grid | ✅ v1.2 | Log-odds, Bresenham, 3D + 미니맵 |
| 성능 최적화 | ✅ v1.2 | DisplayList, SpatialHash, LiDAR 캐시 |
| 사운드 효과 | 🔲 | 경보음, 모터, LiDAR 스캔 |
| Costmap 시각화 | 🔲 | global/local costmap 레이어 |
| A*/DWA 경로 계획 시각화 | 🔲 | 경로 탐색 과정 애니메이션 |
| 순찰 경로 편집기 | 🔲 | 웨이포인트 드래그 추가/삭제 |

---

### Phase 2: 데이터 추상화 레이어 (ROS2 브릿지 준비)

**핵심 목표**: 시뮬레이션 내부 데이터와 실제 ROS2 토픽 데이터를  
동일한 인터페이스로 접근할 수 있는 추상화 레이어를 구축한다.

#### 2-1. DataProvider 인터페이스 설계

```python
class DataProvider(ABC):
    """시뮬레이션과 실제 로봇 양쪽에서 구현하는 공통 인터페이스"""

    @abstractmethod
    def get_robot_pose(self) -> Tuple[float, float, float]:
        """(x, z, yaw) — /odom 또는 /tf에서 추출"""

    @abstractmethod
    def get_lidar_scan(self) -> List[float]:
        """ranges[] — /scan (sensor_msgs/LaserScan)"""

    @abstractmethod
    def get_occupancy_grid(self) -> np.ndarray:
        """/map (nav_msgs/OccupancyGrid) → 2D numpy array"""

    @abstractmethod
    def get_camera_image(self) -> Optional[np.ndarray]:
        """/image_raw (sensor_msgs/Image) → RGB numpy array"""

    @abstractmethod
    def get_cmd_vel(self) -> Tuple[float, float]:
        """(linear.x, angular.z) — /cmd_vel"""

    @abstractmethod
    def get_detections(self) -> List[dict]:
        """/detection — 낙상/얼굴 감지 결과 리스트"""

    @abstractmethod
    def get_nav_path(self) -> List[Tuple[float, float]]:
        """/nav2/path — 현재 계획된 경로 웨이포인트"""

    @abstractmethod
    def get_robot_status(self) -> dict:
        """배터리, 모드, 에러 등 종합 상태"""
```

#### 2-2. 두 가지 구현체

```
DataProvider (ABC)
├── SimDataProvider      — 현재 시뮬레이션 내부 변수에서 데이터 추출
│                          (kevin_3d_sim.py의 robot_x/z, slam.grid 등)
│
└── ROS2DataProvider     — 실제 ROS2 토픽 구독으로 데이터 수신
                           rclpy + rosbridge_suite 또는 Foxglove WebSocket
```

#### 2-3. 실제 로봇 데이터 수신 경로

```
[Kevin 로봇 (ROS2 Jazzy)]
  │
  ├── /scan          (LiDAR)  ──────┐
  ├── /image_raw     (카메라) ──────┤
  ├── /odom          (위치)   ──────┤
  ├── /map           (SLAM)   ──────┼──→ [rosbridge_server]
  ├── /cmd_vel       (속도)   ──────┤        │
  ├── /detection     (감지)   ──────┤        ↓ WebSocket (JSON)
  ├── /alert         (알림)   ──────┤        │
  └── /robot_status  (상태)   ──────┘    [ROS2DataProvider]
                                             │
                                             ↓
                                     [통합 모니터링 GUI]
```

**카메라 + LiDAR 맵 데이터 실시간 반영**:
- `/map` 토픽 (nav_msgs/OccupancyGrid)을 구독하면 SLAM 툴박스가 생성한
  occupancy grid가 실시간으로 수신됨
- `/image_raw`를 통해 카메라 영상도 대시보드에 실시간 스트리밍
- `/scan`의 LaserScan 데이터로 3D LiDAR 포인트 시각화
- 이 모든 데이터가 DataProvider 인터페이스를 통해 동일한 방식으로
  시뮬레이션과 실제 로봇 양쪽에서 GUI에 전달됨

---

### Phase 3: 통합 모니터링 GUI Dashboard

**핵심 목표**: Kevin 로봇의 모든 센서·액추에이터·비전·네비게이션 상태를  
하나의 화면에서 실시간 모니터링하는 통합 대시보드를 구축한다.

#### 3-1. 기술 스택 후보

| 옵션 | 장점 | 단점 |
|---|---|---|
| **PyQt6 + PyQtGraph + OpenGL** | Python 생태계 통일, GPU 가속 차트, OpenGL 3D 내장 | 배포 크기, 웹 비지원 |
| **FastAPI + React + Three.js** | 웹 기반 원격 접속, 크로스 플랫폼 | 백엔드-프론트 분리 복잡도 |
| **Foxglove Studio 커스텀 패널** | ROS2 네이티브, 즉시 사용 가능 | 커스텀 한계, 유료 기능 |

→ 1차: **PyQt6 기반** (로컬 모니터링 + OpenGL 3D 재활용)  
→ 2차: **FastAPI + WebSocket** 확장 (원격 모니터링)

#### 3-2. 대시보드 레이아웃 설계

```
┌─────────────────────────────────────────────────────────────┐
│  Kevin Patrol Dashboard          [SIM] [LIVE] [REC]  │ ⚙ │
├──────────────────┬──────────────────┬───────────────────────┤
│                  │                  │  📡 Topic Monitor     │
│   3D Viewport    │  Camera Feed     │  ─────────────────── │
│   (OpenGL)       │  /image_raw      │  /cmd_vel    50Hz ● │
│                  │                  │  /scan       10Hz ● │
│   로봇 + 맵 +    │  낙상감지 바운딩  │  /odom       50Hz ● │
│   LiDAR + 경로   │  박스 오버레이    │  /map         1Hz ● │
│                  │                  │  /detection  10Hz ● │
│                  │                  │  /alert       0Hz ○ │
├──────────────────┼──────────────────┤  ...                 │
│                  │  📊 Sensor Plot  ├───────────────────────┤
│   🗺 SLAM Map    │  ───────────────│  🤖 Robot Status     │
│   (2D top-down)  │  IMU angular_vel│  Battery: 78%        │
│                  │  LiDAR min_dist │  Mode: Auto Patrol   │
│   occupancy grid │  Motor current  │  Speed: 0.3 m/s     │
│   + robot pose   │  (실시간 그래프) │  WP: 3/10           │
│   + nav path     │                  │  SLAM: 67% explored │
│   + costmap      │                  │  Uptime: 02:34:12   │
├──────────────────┴──────────────────┴───────────────────────┤
│  ▶ PATROL  ⏸ STOP  📍 SET_GOAL  🔄 SLAM_RESET  ⚠ ALERTS │
└─────────────────────────────────────────────────────────────┘
```

#### 3-3. 대시보드 패널 상세

| 패널 | 데이터 소스 | 기능 |
|---|---|---|
| **3D Viewport** | /odom, /scan, /map, /nav2/path | 현재 시뮬레이션의 OpenGL 뷰를 그대로 임베드. 실제 로봇 시에는 수신된 맵/포즈 데이터로 3D 재구성 |
| **Camera Feed** | /image_raw, /detection | 카메라 영상 실시간 스트리밍 + 감지 결과 바운딩 박스 오버레이 |
| **SLAM Map** | /map (OccupancyGrid) | 2D 탑다운 뷰. 로봇 위치, 계획 경로, costmap 레이어 중첩 표시. 클릭으로 Nav2 goal 전송 가능 |
| **Topic Monitor** | 모든 토픽 | 토픽별 활성 상태, 발행 주기(Hz), 최근 데이터 요약 |
| **Sensor Plot** | /scan, /imu, /joint_states | IMU 각속도, LiDAR 최소 거리, 모터 전류 등 시계열 그래프 (최근 30초) |
| **Robot Status** | /robot_status, /battery, /diagnostics | 배터리, 모드, 속도, 웨이포인트 진행률, SLAM 탐사율, 가동 시간 |
| **Command Bar** | /cmd_vel, /nav2/goal, SLAM 제어 | 순찰 시작/정지, 목표 지점 설정, SLAM 리셋, 알림 확인 |

#### 3-4. 데이터 모드 전환

```python
class DashboardApp:
    def __init__(self):
        self.mode = "SIM"  # "SIM" | "LIVE" | "REC"

    def set_mode(self, mode):
        if mode == "SIM":
            self.provider = SimDataProvider(simulation)
        elif mode == "LIVE":
            self.provider = ROS2DataProvider(rosbridge_url)
        elif mode == "REC":
            self.provider = BagDataProvider(bag_file_path)
```

- **SIM 모드**: 현재 시뮬레이션 데이터 사용 (개발/테스트)
- **LIVE 모드**: 실제 Kevin 로봇의 ROS2 토픽 실시간 구독
- **REC 모드**: ros2 bag 녹화 파일 재생 (디버깅/분석)

---

### Phase 4: 실전 배포 (Kevin 로봇 연동)

#### 4-1. 시스템 아키텍처 (최종)

```
[Kevin 로봇 — Jetson/RPi]
  ├── camera_node        → /image_raw
  ├── lidar_node         → /scan
  ├── slam_toolbox       → /map
  ├── nav2               → /cmd_vel, /nav2/path
  ├── fall_detector      → /detection
  ├── face_detector      → /face_event
  ├── guard_brain (LLM)  → /alert, /robot_status
  ├── motor_controller   → 모터 PWM
  ├── micro-ROS (ESP32)  → /sensor_data
  └── rosbridge_server   → WebSocket :9090
         │
         ↓  WiFi / LAN
         │
[모니터링 PC / 웹 브라우저]
  └── Kevin Patrol Dashboard
        ├── 3D Viewport (OpenGL / Three.js)
        ├── Camera Feed (MJPEG / WebRTC)
        ├── SLAM Map (OccupancyGrid 실시간)
        ├── Sensor Plots (실시간 차트)
        ├── Topic Monitor
        ├── Robot Control (Goal 전송, 순찰 제어)
        └── guard_brain 대화 인터페이스
```

#### 4-2. 실제 로봇 데이터 반영 포인트

| 센서/데이터 | ROS2 토픽 | 대시보드 반영 |
|---|---|---|
| LiDAR 스캔 | `/scan` (LaserScan) | 3D 포인트 클라우드 + 미니맵 레이 표시 |
| 카메라 영상 | `/image_raw` (Image) | Camera Feed 패널 실시간 스트리밍 |
| SLAM 맵 | `/map` (OccupancyGrid) | SLAM Map 패널에 즉시 반영, 3D에도 오버레이 |
| 로봇 위치 | `/odom` + `/tf` | 3D/2D 뷰 로봇 아이콘 위치 업데이트 |
| 네비게이션 경로 | `/nav2/path` (Path) | 3D 뷰 + SLAM Map에 경로 라인 표시 |
| 낙상 감지 | `/detection` | Camera Feed에 바운딩 박스 + 알림 |
| 얼굴 인식 | `/face_event` | Camera Feed에 얼굴 마커 + 식별 결과 |
| 모터 상태 | `/joint_states` | Sensor Plot 전류/속도 그래프 |
| ESP32 센서 | `/sensor_data` | 온도, 습도, 배터리 전압 표시 |
| LLM 판단 | `/alert`, `/robot_status` | 상태 패널 + 알림 팝업 + 대화 로그 |

#### 4-3. 마일스톤

| 단계 | 목표 | 검증 기준 |
|---|---|---|
| 4-A | rosbridge 연결 + /odom 실시간 수신 | 대시보드에서 로봇 위치 실시간 표시 |
| 4-B | /scan + /map 시각화 | LiDAR 포인트 + SLAM 맵이 대시보드에 반영 |
| 4-C | /image_raw 스트리밍 | Camera Feed 30fps 이상 표시 |
| 4-D | Nav2 Goal 전송 | 대시보드 클릭 → 로봇이 해당 위치로 이동 |
| 4-E | 전체 시스템 통합 테스트 | SIM/LIVE 모드 전환 시 대시보드 동일하게 동작 |

---

## 파일 구조

```
kevin_3d_sim.py          — 메인 시뮬레이션 (1,661 lines)
kevin_3d_sim_dev.md      — 이 개발 문서
ros2_commander.py        — ROS2 학습 게임 (1,216 lines, 별도 프로젝트)
```
