# Kevin 3D Patrol Simulator — 개발 문서

**프로젝트**: Kevin 3D Patrol Simulator  
**파일**: `kevin_3d_sim.py` (1,187 lines)  
**플랫폼**: Pygame + PyOpenGL  
**Python**: 3.10+  

---

## 변경 이력

| 날짜 | 버전 | 내용 |
|---|---|---|
| 2025-02-15 | v1.0 | 초기 버전 — 3D 환경, 로봇 모델, LiDAR, 순찰, 낙상 감지, HUD |
| 2025-02-15 | v1.1 | 전체 화면(F11), 마우스 캡처/해제(클릭/ALT), 동적 해상도 대응 |

---

## 개요

Kevin 자율순찰 로봇을 3D 환경에서 시뮬레이션하는 게임.  
ROS2 토픽 모니터, LiDAR 시각화, Nav2 웨이포인트 순찰, 낙상 감지 등  
실제 로봇 시스템의 핵심 기능을 시각적으로 체험할 수 있다.

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
| F | 낙상 이벤트 트리거 (가장 가까운 사람) |
| M | 미니맵 ON/OFF |

### 화면 / 마우스 제어 (v1.1 추가)

| 키 | 기능 |
|---|---|
| F11 | 전체 화면 ↔ 창 모드 전환 |
| 화면 클릭 | 마우스 캡처 (시점 이동 모드 진입) |
| ALT | 마우스 해제 (커서 자유 이동) |
| ESC (1회) | 마우스 캡처 해제 |
| ESC (2회) | 프로그램 종료 (이미 해제 상태에서) |

---

## 아키텍처

### 클래스 구조

```
Kevin3DSim              — 메인 시뮬레이션 루프 + 디스플레이 관리
│   _toggle_fullscreen()  — 전체 화면 / 창 모드 전환 (v1.1)
│   _capture_mouse()      — 마우스 캡처 (v1.1)
│   _release_mouse()      — 마우스 해제 (v1.1)
│   _check_collision()    — 벽/장애물 충돌 판정
│   _auto_patrol()        — Nav2 스타일 웨이포인트 추종
│   _trigger_fall_event() — 낙상 이벤트 발생
│   _render()             — 3D + HUD 통합 렌더링
│
├── TopicMonitor        — ROS2 토픽 8개 상태 시뮬레이션
│     /cmd_vel, /scan, /image_raw, /odom
│     /detection, /alert, /robot_status, /nav2/path
│
├── HUD                 — 2D 오버레이 (OpenGL ortho)
│     draw_topic_monitor()  — 토픽 패널 (활성/비활성, Hz, 데이터)
│     draw_minimap()        — 미니맵 (벽, 장애물, WP, 로봇)
│     draw_status_bar()     — 하단 상태 바
│     draw_alert_overlay()  — 낙상 알림 화면 효과
│     draw_mouse_hint()     — 마우스 해제 시 안내 (v1.1)
│     draw_controls_help()  — 조작 도움말
│
└── CameraMode (Enum)   — FIRST_PERSON / THIRD_PERSON / TOP_VIEW
```

### 3D 렌더링 함수

| 함수 | 설명 |
|---|---|
| `draw_box()` | 범용 3D 박스 — 6면 개별 색상, 벽/장애물/로봇 부품 |
| `draw_cylinder()` | N-각형 원기둥 근사 — LiDAR 센서 모델 |
| `draw_robot()` | Kevin 로봇 — 본체 + 4바퀴 + 카메라(렌즈) + LiDAR + LED 2개 |
| `draw_person()` | 사람 모델 — 서있는/쓰러진 상태, 몸통+머리+다리 |
| `draw_lidar_rays()` | 72-ray 레이캐스트, 거리 기반 색상 그라데이션, 히트포인트 |
| `draw_waypoint()` | Nav2 마커 — 지면 펄스 원 + 상하 떠다니는 큐브 + 기둥 |
| `draw_floor()` | 바닥면 + 2단위 그리드 라인 |
| `draw_skybox()` | 그라데이션 배경 (ortho fallback) |

### 맵 구조

```
40×40 단위 실내 환경
├── 외벽: 사방 경계
├── 내부 벽: 복도 구조 (수평 2구간 + 수직 3구간)
├── 장애물: 12개 (가구/박스, 높이 랜덤 0.8~1.4)
├── 웨이포인트: 10개 순찰 경로 (반시계 루프)
└── 사람: 5명 (낙상 감지 대상, 맵 전역 분포)
```

---

## v1.0 → v1.1 변경 상세

### 1. 전체 화면 지원 (F11)

```python
def _toggle_fullscreen(self):
    self.fullscreen = not self.fullscreen
    if self.fullscreen:
        # 현재 모니터 해상도 자동 감지
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode(
            (info.current_w, info.current_h), DOUBLEBUF | OPENGL | FULLSCREEN
        )
    else:
        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT), DOUBLEBUF | OPENGL | RESIZABLE
        )
    glViewport(0, 0, self.display_w, self.display_h)
    self._init_gl()
```

- `RESIZABLE` 플래그 추가로 창 모드에서 드래그 리사이즈도 지원
- `VIDEORESIZE` 이벤트 핸들링으로 리사이즈 시 GL 뷰포트 자동 갱신

### 2. 마우스 캡처 / 해제

| 상태 | 트리거 | 동작 |
|---|---|---|
| 해제 → 캡처 | 화면 좌클릭 | 커서 숨김, grab, 중앙 워프 + 잔여 모션 소거 |
| 캡처 → 해제 | ALT 키 또는 ESC | 커서 표시, grab 해제 |

```python
def _capture_mouse(self):
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    pygame.mouse.set_pos(self.display_w // 2, self.display_h // 2)
    pygame.event.get(MOUSEMOTION)  # 잔여 이벤트 소거 → 시점 점프 방지

def _release_mouse(self):
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
```

- 시작 시 마우스 해제 상태 (mouse_captured=False)
- 화면 중앙에 "클릭하여 시점 제어 시작" 힌트 박스 표시
- ESC 2단계: 1차 = 마우스 해제, 2차 = 프로그램 종료

### 3. 동적 해상도 대응

- 모든 HUD 함수에 `screen_w`, `screen_h` 파라미터 추가
- `begin_2d(w, h)` → `glOrtho(0, w, h, 0, ...)` 동적 설정
- `gluPerspective(65, w/h, ...)` 종횡비 동적 계산
- 토픽 모니터, 미니맵, 상태바 위치가 화면 크기에 맞춰 재배치

---

## ROS2 토픽 시뮬레이션 상세

| 토픽 | 메시지 타입 | 발행 조건 | 데이터 예시 |
|---|---|---|---|
| `/cmd_vel` | Twist | 이동 시 50Hz | `lin:0.08 ang:1.2` |
| `/scan` | LaserScan | 항상 10Hz | `ranges: 360 pts` |
| `/image_raw` | Image | 항상 30Hz | `640x480 rgb8` |
| `/odom` | Odometry | 항상 50Hz | `x:3.2 y:-8.1` |
| `/detection` | Detection | 감지 시 10Hz | `FALL DETECTED!` / `monitoring...` |
| `/alert` | String | 알림 시 1Hz | `⚠ EMERGENCY` / `no alert` |
| `/robot_status` | String | 항상 | `auto_patrol` / `manual` |
| `/nav2/path` | Path | 순찰 모드 시 1Hz | `waypoints: 10` |

---

## 파일 구조

```
kevin_3d_sim.py          — 메인 시뮬레이션 (1,187 lines)
kevin_3d_sim_dev.md      — 이 개발 문서
ros2_commander.py        — ROS2 학습 게임 (1,216 lines, 별도 프로젝트)
```

---

## 향후 개선 방향

- SLAM 맵 빌딩 시각화 (occupancy grid 실시간 생성)
- 얼굴 인식 시뮬레이션 (face_detect 노드)
- guard_brain LLM 대화 통합 (Ollama EXAONE 연동)
- 다중 로봇 시뮬레이션
- 사운드 효과 (경보음, 모터 소리)
- 성능 최적화 (디스플레이 리스트 / VBO)
- 미니맵 확대/축소
- 순찰 경로 편집기 (웨이포인트 추가/삭제)
