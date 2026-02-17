# Kevin Patrol Dashboard — MockSim A* 경로 최적화 작업 기록

**작업 기간**: 2026-02-17  
**기반 버전**: v3.2.1 (패널 배경 통일 + 입체감 완료 상태)  
**목적**: SLAM Map 경로가 벽을 관통하는 문제 해결 → A* 기반 벽 회피 순찰 경로 시스템 구축  
**적용 대상**: Kevin Patrol Single Dashboard → Kevin Multi Dashboard 이식 예정

---

## 1. 문제 정의

### 1-1. 경로 라인이 벽을 관통

대시보드 SLAM Map 패널에서 waypoint 간 경로 라인이 occupied 셀(벽)을 직선으로 관통하여 표시됨.

**원인**: `SimDataProvider.get_nav_path()`가 원본 `PATROL_WAYPOINTS` 좌표 리스트를 그대로 반환하고, 대시보드가 이를 `(i+1) % len` 순환 직선으로 렌더링.

```python
# Before — data_provider.py
def get_nav_path(self) -> NavPath:
    return NavPath(
        waypoints=list(s.waypoints),    # ← 원본 WP 15개 좌표
        current_index=s.current_waypoint
    )
```

```python
# Before — app.py (SLAM Map paintEvent)
for i in range(len(pts)):
    j = (i + 1) % len(pts)             # ← 모든 점을 순환 직선 연결
    painter.drawLine(w2s(pts[i]), w2s(pts[j]))
```

### 1-2. 로봇이 경로를 따라가지 않음

`_auto_patrol()`에서 로봇은 원본 waypoint만 직선 목표로 추적하고, A* 경로의 중간 포인트를 무시.

```python
# Before — kevin_3d_sim.py
def _auto_patrol(self):
    tx, tz = self.waypoints[self.current_waypoint]  # ← 원본 WP만 추적
```

### 1-3. MockSim 맵 구조 불일치

MockSLAM의 occupancy grid가 실제 `generate_map()` 벽 구조와 완전히 달라서, 대시보드 단독 실행 시 경로 탐색 불가.

```python
# Before — MockSLAM
self.grid[20:60, 20:60] = 0           # 월드 (-12,-12)~(8,8)만 free
self.grid[30:32, 25:50] = 100         # 임의의 벽 2줄
self.grid[44, 20:45] = 100
# → WP 대부분이 unknown(-1) 영역에 위치하여 A* 실패
```

---

## 2. 수정 파일 및 변경 내역

### 2-1. kevin_3d_sim.py (sim/kevin_3d_sim.py)

| 변경 위치 | 변경 내용 |
|-----------|----------|
| `AStarPlanner.plan_full_patrol()` | **신규** — 전체 순찰 경로를 구간별 A* + smoothing으로 생성 |
| `AStarPlanner._plan_segment()` | **신규** — 단일 구간 A* 탐색 (애니메이션 없이 경로만 반환) |
| `AStarPlanner._smooth_path()` | **신규** — Line-of-sight 기반 불필요한 중간점 제거 |
| `AStarPlanner._has_line_of_sight()` | **신규** — 두 점 간 직선 장애물 검사 (3×3 인접셀 포함) |
| `Kevin3DSim.__init__` | `full_patrol_path`, `_patrol_path_index` 속성 추가 |
| `Kevin3DSim._auto_patrol()` | **전면 수정** — A* 경로 중간점 순차 추적으로 변경 |
| `Kevin3DSim` (TAB 키 순찰 시작) | `plan_full_patrol()` 호출 추가 |
| `Kevin3DSim` (TAB 키 순찰 정지) | `full_patrol_path`, `_patrol_path_index` 초기화 |
| `Kevin3DSim` (3D 경로 렌더링) | 순찰 중 `GL_LINE_STRIP` + full_patrol_path, 편집 중 기존 `GL_LINE_LOOP` 유지 |

#### 2-1-1. AStarPlanner 신규 메서드

```python
def plan_full_patrol(self, waypoints, start_wx=None, start_wz=None):
    """전체 순찰 경로: 구간별 A* + 구간별 smoothing"""
    # (start → WP0 → WP1 → ... → WP14 → WP0) 각 구간을
    # _plan_segment()로 A* 탐색 후 _smooth_path()로 최적화
    # 반환: [(wx, wz), ...] 벽 회피 + smoothing 적용된 전체 경로

def _plan_segment(self, start_wx, start_wz, goal_wx, goal_wz):
    """단일 구간 A* (애니메이션 없이 경로만 반환)"""
    # 기존 plan()과 동일한 A* 로직, 애니메이션 기록 생략
    # 반환: [(wx, wz), ...] 또는 None (경로 없음)

def _smooth_path(self, path):
    """Line-of-sight 기반 경로 단축"""
    # 현재 점에서 가장 먼 직선 연결 가능 점까지 건너뛰기
    # 결과: 벽 모서리에서만 꺾이는 최적 경로

def _has_line_of_sight(self, x1, z1, x2, z2):
    """두 점 간 장애물 검사 (Bresenham 스타일)"""
    # 그리드 해상도 0.5배 간격으로 샘플링
    # 각 지점의 3×3 인접셀 walkable 체크 (로봇 반경 여유)
```

#### 2-1-2. _auto_patrol() 변경 핵심

```python
# After
def _auto_patrol(self):
    # 1. 목표점 결정: full_patrol_path[_patrol_path_index] 우선
    if self.full_patrol_path and self._patrol_path_index < len(self.full_patrol_path):
        tx, tz = self.full_patrol_path[self._patrol_path_index]

    # 2. 도달 시: _patrol_path_index 증가 + 순환
    #    가장 가까운 원본 WP와 current_waypoint 동기화

    # 3. 이동/회피 로직: 기존 LiDAR 기반 장애물 회피 유지

    # 4. 스턱 복구: full_patrol_path 내에서 2포인트 스킵
```

**핵심 변경**: 로봇이 원본 WP가 아닌 A* 경로의 **모든 중간 포인트를 순서대로 추적**하므로, 벽을 우회하는 경로를 정확히 따라감.

#### 2-1-3. 3D 경로 렌더링 변경

```python
# 순찰 중: A* 벽 회피 경로 (GL_LINE_STRIP)
if self.patrol_mode and self.full_patrol_path:
    glBegin(GL_LINE_STRIP)
    for wx, wz in self.full_patrol_path:
        glVertex3f(wx, 0.1, wz)
    glEnd()
else:
    # 편집 모드: 기존 WP 직선 연결 (GL_LINE_LOOP) 유지
```

---

### 2-2. data_provider.py (core/data_provider.py)

| 변경 위치 | 변경 내용 |
|-----------|----------|
| `NavPath` dataclass | `original_waypoints` 필드 추가 |
| `SimDataProvider.get_nav_path()` | `full_patrol_path` 우선 반환, 원본 WP 별도 포함 |

#### NavPath 구조 변경

```python
@dataclass
class NavPath:
    waypoints: List[Tuple[float, float]]           # A* 경로 (렌더링용)
    current_index: int = 0                          # 현재 추적 인덱스
    original_waypoints: List[Tuple[float, float]]   # 원본 WP 15개 (마커용)  ← 신규
    timestamp: float = 0.0
```

#### get_nav_path() 변경

```python
def get_nav_path(self) -> NavPath:
    full_path = getattr(s, 'full_patrol_path', [])
    if full_path:
        return NavPath(
            waypoints=list(full_path),           # A* 경로
            current_index=s._patrol_path_index,
            original_waypoints=list(s.waypoints) # 원본 WP
        )
    # fallback: 순찰 전에는 원본 WP 반환
    return NavPath(
        waypoints=list(s.waypoints),
        current_index=s.current_waypoint,
        original_waypoints=list(s.waypoints)
    )
```

---

### 2-3. app.py (dashboard/app.py)

| 변경 위치 | 변경 내용 |
|-----------|----------|
| `SLAMMapWidget.paintEvent` | 경로 렌더링 2레이어 분리 (A* 실선 + WP 점선) |
| `MockSLAM.__init__` | **전면 수정** — `generate_map()` 동일 벽 구조 |
| `MockSimForDashboard.__init__` | `full_patrol_path`, `_patrol_path_index` 속성 추가 |
| `MockSimForDashboard.start_patrol()` | A* 전체 경로 생성 (`_build_mock_patrol_path`) |
| `MockSimForDashboard._build_mock_patrol_path()` | **신규** — occupancy grid 기반 간이 A* + 구간별 smoothing |
| `MockSimForDashboard._smooth_mock_path()` | **신규** — MockSim용 LOS 기반 smoothing |
| `MockSimForDashboard.stop_patrol()` | 경로 초기화 추가 |
| `MockSimForDashboard.tick()` | WP 직선 추적 → A* 경로점 추적 + 충돌 체크 |
| `MockSimForDashboard.reset_slam()` | 새 벽 구조에 맞게 재초기화 |

#### SLAM Map 경로 렌더링 (2레이어)

```python
# Layer 1: A* 벽 회피 경로 (시안 실선)
painter.setPen(QPen(QColor(ACCENT_BLUE), 1.5))
for i in range(len(pts) - 1):                    # LINE_STRIP (순환 아님)
    painter.drawLine(w2s(pts[i]), w2s(pts[i+1]))

# Layer 2: 원본 WP 연결선 (주황 점선 — 순서 확인용)
wp_pen = QPen(QColor(255, 180, 50, 100), 1.0, Qt.PenStyle.DotLine)
for i in range(len(orig_wps)):
    j = (i + 1) % len(orig_wps)                  # LINE_LOOP (순환)
    painter.drawLine(w2s(orig_wps[i]), w2s(orig_wps[j]))

# Layer 3: 원본 WP 마커 (파란 동그라미 — 15개만)
for wx, wz in orig_wps:
    painter.drawEllipse(...)
```

#### MockSLAM 벽 구조 (generate_map 동기화)

```python
class MockSLAM:
    def __init__(self):
        self.grid = np.full((88, 88), -1, dtype=np.int8)
        self.resolution = 0.5
        self.grid_size = 88
        self.origin = -22.0

        # 외벽 내부 전체 free
        self.grid[4:84, 4:84] = 0

        # generate_map()과 동일한 벽 배치
        # 외벽 (MAP_SIZE=40, ±20)
        for i in range(-20, 21, 2):
            mark_wall(i, -20); mark_wall(i, 20)
            mark_wall(-20, i); mark_wall(20, i)

        # 내부 수평벽 (z=6, z=-6) — 갭 위치 보존
        # z=6:  x=-12~-2 (좌), x=4~12 (우) → 갭 x=-1~3
        # z=-6: x=-14~-6 (좌), x=0~12 (우) → 갭 x=-5~-1

        # 내부 수직벽
        # x=-14: z=-6~4   x=0: z=-14~-8   x=8: z=6~12

        # 장애물 12개 (가구 등)
```

#### MockSim tick() 경로 추적 + 충돌 체크

```python
def tick(self):
    if self.patrol_mode:
        # A* 경로점 추적
        if self.full_patrol_path:
            tx, tz = self.full_patrol_path[self._patrol_path_index]

        # 도달 시 → _patrol_path_index++ + 순환
        # 미도달 시 → 목표 방향 이동 + occupancy grid 충돌 체크
        gx, gz = w2g(new_x, new_z)
        if grid[gx, gz] != 100:    # occupied가 아닐 때만 이동
            self.robot_x = new_x
            self.robot_z = new_z
```

---

## 3. Path Smoothing 알고리즘

### 3-1. 원리

A* 결과는 그리드 셀 단위 계단형 경로(215+ 포인트). Smoothing으로 직선 연결 가능한 중간점을 제거하여 벽 모서리에서만 꺾이는 최적 경로로 단축.

```
Before (A* raw):    ·-·-·-·      After (smoothed):  ·-------·
                    |     |                            \     |
                    ·-·-·-·                             ·---·
```

### 3-2. Line-of-Sight 검사

```python
def _has_line_of_sight(self, x1, z1, x2, z2):
    # 1. 두 점 간 거리 계산
    # 2. 그리드 해상도 × 0.5 간격으로 샘플링
    # 3. 각 샘플 지점의 3×3 인접셀 walkable 체크
    #    → 로봇 반경(~0.5m) 여유 확보
    # 4. 하나라도 occupied → False (직선 불가)
```

### 3-3. 핵심 주의사항: 구간별 적용

```
❌ 전체 경로에 한 번 적용:
   순환 경로이므로 첫점≈끝점 → LOS 통과 → 215pt → 2pt (거의 전부 제거)

✅ 구간별(WP→WP) 적용:
   각 구간 내에서만 smoothing → 벽 회피 중간점은 보존, 직선 구간만 단축
   결과: 215pt → 18pt (적절한 밀도)
```

---

## 4. 데이터 흐름 요약

### 4-1. 순찰 시작 시 (TAB / PATROL 버튼)

```
start_patrol() / TAB 키
  → plan_full_patrol(waypoints, robot_x, robot_z)
     → 각 구간: _plan_segment(WPi, WPi+1)     # A* 탐색
              → _smooth_path(segment)            # LOS smoothing
     → full_patrol_path (18~25 포인트)
  → _patrol_path_index = 0
```

### 4-2. 매 프레임 (tick / _auto_patrol)

```
tick() / _auto_patrol()
  → tx, tz = full_patrol_path[_patrol_path_index]
  → 목표 방향 이동 (LiDAR 장애물 회피 / 충돌 체크)
  → 도달 시: _patrol_path_index++ (순환)
           → current_waypoint 동기화 (가장 가까운 원본 WP)
```

### 4-3. 대시보드 업데이트 (10Hz)

```
DashboardWindow._update_dashboard()
  → provider.get_nav_path()
     → NavPath(waypoints=full_patrol_path,
               original_waypoints=원본 WP 15개)
  → slam_map.update_data(...)
     → paintEvent:
        시안 실선 = A* 벽 회피 경로 (full_patrol_path)
        주황 점선 = 원본 WP 직선 연결 (순서 참고용)
        파란 마커 = 원본 WP 15개 위치
```

---

## 5. 수정 전후 비교

| 항목 | Before (v3.2.1) | After |
|------|-----------------|-------|
| 경로 생성 | 없음 (원본 WP 좌표 그대로) | A* + LOS smoothing |
| 경로 라인 | WP 직선 연결 (벽 관통) | A* 벽 회피 경로 (실선) + WP 직선 (점선) |
| 로봇 이동 | 원본 WP 직선 추적 | A* 경로 중간점 순차 추적 |
| 충돌 방지 | 3D Sim만 (LiDAR+SpatialHash) | MockSim에도 occupancy grid 충돌 체크 추가 |
| MockSLAM 벽 | 임의 2줄 벽 + 제한 free 영역 | generate_map() 동일 구조 (외벽+내벽+장애물) |
| NavPath 구조 | waypoints만 | waypoints + original_waypoints 분리 |
| Smoothing | 없음 | 구간별 LOS smoothing (215pt → 18pt) |

---

## 6. 최종 파일 구조 및 라인 수

```
kevin_patrol/
├── sim/
│   └── kevin_3d_sim.py          ← v3.2.1+ (~2872 lines, +203 lines)
│       ├── AStarPlanner
│       │   ├── plan_full_patrol()     ← 신규
│       │   ├── _plan_segment()        ← 신규
│       │   ├── _smooth_path()         ← 신규
│       │   └── _has_line_of_sight()   ← 신규
│       └── Kevin3DSim
│           ├── full_patrol_path       ← 신규 속성
│           ├── _patrol_path_index     ← 신규 속성
│           └── _auto_patrol()         ← 전면 수정
│
├── core/
│   └── data_provider.py         ← v3.2.1+ (~441 lines, +13 lines)
│       ├── NavPath.original_waypoints ← 신규 필드
│       └── SimDataProvider.get_nav_path() ← 수정
│
└── dashboard/
    └── app.py                   ← v3.2.1+ (~2004 lines, +219 lines)
        ├── SLAMMapWidget.paintEvent   ← 경로 렌더링 2레이어
        ├── MockSLAM                   ← 전면 수정 (generate_map 동기화)
        └── MockSimForDashboard
            ├── full_patrol_path       ← 신규 속성
            ├── _build_mock_patrol_path() ← 신규
            ├── _smooth_mock_path()    ← 신규
            └── tick()                 ← 경로 추적 + 충돌 체크
```

---

## 7. Multi Dashboard 이식 시 체크리스트

Kevin Multi Dashboard에 본 최적화를 적용할 때 확인할 항목:

### 7-1. 데이터 구조

- [ ] `NavPath`에 `original_waypoints` 필드 추가
- [ ] 각 로봇별 `full_patrol_path`, `_patrol_path_index` 관리
- [ ] Multi에서 로봇별 독립 `AStarPlanner` 인스턴스 필요

### 7-2. 경로 생성

- [ ] 각 로봇의 `spatial_hash` 또는 `occupancy_grid`에 맞는 A* 플래너 연결
- [ ] `plan_full_patrol()` 호출 시점: 순찰 시작 시 1회
- [ ] 구간별 smoothing 적용 (전체 경로 한 번에 적용 ❌)
- [ ] 로봇 간 경로 충돌 회피 (추가 과제)

### 7-3. 경로 추적

- [ ] `_auto_patrol()` 또는 `tick()`에서 `full_patrol_path[_patrol_path_index]` 추적
- [ ] `current_waypoint` 동기화 로직 (가장 가까운 원본 WP 매칭)
- [ ] 충돌 체크: occupancy grid 또는 spatial_hash 기반

### 7-4. 시각화

- [ ] SLAM Map에 2레이어 렌더링: A* 경로 (실선) + 원본 WP (점선+마커)
- [ ] Multi에서 로봇별 경로 색상 구분 필요
- [ ] 3D 뷰포트: 순찰 중 `GL_LINE_STRIP` (full_patrol_path), 편집 중 `GL_LINE_LOOP` (원본 WP)

### 7-5. MockSim

- [ ] MockSLAM 벽 구조를 실제 맵과 동기화 (generate_map 기반)
- [ ] 외벽 내부 전체를 free(0)로 설정 후 벽만 occupied(100)
- [ ] 각 로봇별 독립 MockSim 또는 공유 맵 + 개별 경로

---

## 8. 해결된 이슈 / 잔여 과제

### 해결

| 이슈 | 상태 |
|------|------|
| SLAM Map 경로 라인 벽 관통 | ✅ A* 벽 회피 경로로 교체 |
| 로봇이 경로를 따라가지 않음 | ✅ A* 중간점 순차 추적 |
| MockSLAM 맵 구조 불일치 | ✅ generate_map() 동기화 |
| 경로가 너무 크게 돌아감 | ✅ LOS path smoothing (215→18pt) |
| Smoothing이 경로 전체를 제거 | ✅ 구간별(WP→WP) smoothing |
| MockSim 벽 통과 | ✅ occupancy grid 충돌 체크 추가 |
| WP 연결선 소실 | ✅ 주황 점선 + 파란 마커 레이어 분리 |
| SLAM Reset 작동 안 함 | ✅ free 영역만 unknown 리셋 (벽 구조 보존) |
| Stop→Start 시 출발점 회귀 | ✅ 가장 가까운 WP부터 순환 경로 빌드 |

### 잔여 과제 (Multi Dashboard 구현 시)

| 과제 | 우선순위 |
|------|---------|
| 로봇 간 경로 충돌 회피 (cooperative A*) | 높음 |
| 동적 장애물 대응 (실시간 경로 재계획) | 중간 |
| 대시보드 경로 편집 기능 (SET GOAL 확장) | 중간 |
| ROS2DataProvider A* 연동 (Nav2 planner 사용) | Phase 4 |
| BagDataProvider 경로 재생 | Phase 4 |

---

## 9. 추가 버그 수정 (테스트 중 발견)

### 9-1. SLAM Reset 작동 안 함

**증상**: SLAM RESET 버튼 클릭 시 free(녹색) 영역이 초기화되지 않음.

**원인**: MockSLAM 벽 구조를 `generate_map()` 기반으로 전면 수정하면서, `reset_slam()`을 `self.slam.__init__()`으로 변경했는데, 이 호출이 벽 포함 전체를 재생성하여 free 영역이 즉시 다시 열림 (리셋 효과 없음).

```python
# Before (버그)
def reset_slam(self):
    self.slam.__init__()
    # → 벽(100) + free(0) 전체 재생성 → 리셋 전과 동일하게 보임
```

**수정**: free(0) 셀만 선택하여 unknown(-1)으로 되돌림. occupied(100) 벽은 유지.

```python
# After
def reset_slam(self):
    mask = self.slam.grid == 0      # free 셀만 선택
    self.slam.grid[mask] = -1       # unknown으로 리셋
    # → 벽 구조 보존 + 탐색 영역만 초기화
    # → 순찰 재시작 시 로봇 주변부터 점진적으로 free 확장
```

**SLAM Reset 전후 비교**:

```
Before reset:              After reset:
┌──────────────┐          ┌──────────────┐
│▓▓▓▓▓▓▓▓▓▓▓▓▓│ 외벽     │▓▓▓▓▓▓▓▓▓▓▓▓▓│ 외벽 (유지)
│▓ ░░░░▓░░░░ ▓│ 내벽+free │▓ ····▓···· ▓│ 내벽 (유지) + unknown
│▓ ░░░░▓░░░░ ▓│          │▓ ····▓···· ▓│
│▓▓▓▓▓▓▓▓▓▓▓▓▓│          │▓▓▓▓▓▓▓▓▓▓▓▓▓│
└──────────────┘          └──────────────┘
  ▓=wall(100)               ▓=wall(100) 유지
  ░=free(0)                 ·=unknown(-1) 리셋
```

---

### 9-2. Stop → Start 시 출발점으로 회귀

**증상**: 순찰 중 STOP 후 다시 START하면, 현재 위치에서 계속 진행하지 않고 WP0(초기 출발점) 방향으로 되돌아감.

**원인**: `start_patrol()` → `_build_mock_patrol_path()`에서 항상 WP0부터 순서대로 경로를 빌드.

```python
# Before (버그)
def _build_mock_patrol_path(self):
    points = [(self.robot_x, self.robot_z)] + list(self.waypoints)
    # → 현재위치 → WP0 → WP1 → ... → WP14
    # → WP7에서 정지 후 재시작해도 WP0까지 되돌아감
```

**수정 — 2단계**:

**Step 1**: `start_patrol()`에서 현재 위치와 가장 가까운 WP 탐색

```python
# After — start_patrol()
def start_patrol(self):
    self.patrol_mode = True
    self.robot_speed = 0.3

    # 현재 위치에서 가장 가까운 WP 찾기
    min_dist = float('inf')
    nearest_wp = 0
    for i, (wx, wz) in enumerate(self.waypoints):
        d = math.sqrt((self.robot_x - wx)**2 + (self.robot_z - wz)**2)
        if d < min_dist:
            min_dist = d
            nearest_wp = i
    self.current_waypoint = nearest_wp

    self.full_patrol_path = self._build_mock_patrol_path()
    self._patrol_path_index = 0
```

**Step 2**: `_build_mock_patrol_path()`에서 `current_waypoint`부터 순환 순서로 WP 재배열

```python
# After — _build_mock_patrol_path()
n = len(self.waypoints)
ordered_wps = []
for i in range(n):
    idx = (self.current_waypoint + i) % n
    ordered_wps.append(self.waypoints[idx])

points = [(self.robot_x, self.robot_z)] + ordered_wps
# → WP7 근처에서 재시작 시:
#   현재위치 → WP7 → WP8 → ... → WP14 → WP0 → ... → WP6 → WP7
```

**3D 시뮬(kevin_3d_sim.py)에도 동일 적용**:

TAB 키 순찰 시작 시 가장 가까운 WP를 찾고, 해당 WP부터 순환 순서로 `plan_full_patrol(ordered, robot_x, robot_z)` 호출.

**수정 전후 경로 비교** (WP7 근처에서 Stop→Start):

```
Before:
  Robot(5,16) → WP0(-8,-12) → WP1(-3,-8) → ... → WP7(5,16) → ...
  ↑ 맵 반대편까지 되돌아간 후 다시 돌아옴

After:
  Robot(5,16) → WP7(5,16) → WP8(10,16) → ... → WP14(-5,-17) → WP0(-8,-12) → ... → WP6(-6,16) → WP7
  ↑ 현재 위치에서 바로 다음 순서로 진행
```

---

## 10. 수정 파일 최종 라인 수

| 파일 | 원본 (v3.2.1) | 최종 | 변경량 |
|------|:---:|:---:|:---:|
| kevin_3d_sim.py | 2669 | ~2880 | +211 |
| data_provider.py | 429 | ~442 | +13 |
| app.py | 1785 | ~2010 | +225 |
