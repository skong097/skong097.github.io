---
title: "Kevin Multi Patrol Dashboard — MockSim A* 경로 최적화 이식 기록"
date: 2026-03-21
draft: true
tags: ["robotics", "slam", "fleet", "patrol"]
categories: ["robotics"]
description: "**작업일**: 2026-02-17 **기반**: Kevin Patrol Single Dashboard 버그 수정 완료본 (kevin_patrol_mocksim_optimization_log.md) **적용 대상**"
---

# Kevin Multi Patrol Dashboard — MockSim A* 경로 최적화 이식 기록

**작업일**: 2026-02-17  
**기반**: Kevin Patrol Single Dashboard 버그 수정 완료본 (kevin_patrol_mocksim_optimization_log.md)  
**적용 대상**: kevin_multi_patrol / dashboard_fleet v3.3

---

## 1. 개요

Single Dashboard에서 수정한 A* 경로 최적화 + 버그 수정 9건 + 추가 버그 1건을 Multi Patrol Dashboard에 이식.

Single에서 발견된 문제점들이 Fleet 버전에도 동일하게 존재했으며, Fleet 특유의 다중 로봇 환경에서 추가 버그 1건이 발견되어 함께 수정.

---

## 2. 이식 항목 (Single → Fleet)

### 2-1. data_provider.py (core/data_provider.py)

| # | 수정 항목 | 내용 |
|---|----------|------|
| 1 | NavPath에 `original_waypoints` 필드 추가 | A* 경로(waypoints)와 원본 WP(original_waypoints) 분리 |
| 2 | `SimDataProvider.get_nav_path()` 수정 | `full_patrol_path` 우선 반환, 없으면 원본 WP fallback |

```python
# NavPath 구조 변경
@dataclass
class NavPath:
    waypoints: List[Tuple[float, float]]           # A* 경로 (planned path)
    current_index: int = 0
    original_waypoints: List[Tuple[float, float]]   # 원본 WP 15개 (마커용)
    timestamp: float = 0.0

# get_nav_path 변경
def get_nav_path(self) -> NavPath:
    full_path = getattr(s, 'full_patrol_path', [])
    if full_path:
        return NavPath(
            waypoints=list(full_path),              # A* 경로
            current_index=s._patrol_path_index,
            original_waypoints=list(s.waypoints)    # 원본 WP
        )
    return NavPath(                                 # fallback
        waypoints=list(s.waypoints),
        current_index=s.current_waypoint,
        original_waypoints=list(s.waypoints)
    )
```

---

### 2-2. app.py (dashboard_fleet/app.py)

| # | 수정 항목 | 내용 |
|---|----------|------|
| 3 | SLAM Map 경로 렌더링 2레이어 | 파란 실선(planned path) + 주황 대시선(waypoint route) + 마커 |
| 4 | MockSLAM 벽 구조 → generate_map() 동기화 | 외벽+내벽+장애물을 실제 맵과 동일하게 배치 |
| 5 | MockSim에 `full_patrol_path`, `_patrol_path_index` 속성 추가 | A* 경로 저장 및 추적용 |
| 6 | `start_patrol()` — 가장 가까운 WP + A* 경로 생성 | 현재 위치 기준 nearest WP → 순환 순서 재배열 → A* + smoothing |
| 7 | `stop_patrol()` — 경로 초기화 | `full_patrol_path`, `_patrol_path_index` 클리어 |
| 8 | `reset_slam()` — free만 unknown 리셋 | 벽 구조 보존, `grid == 0`인 셀만 `-1`로 |
| 9 | `tick()` — sin/cos 원형 순찰 → A* 경로점 추적 | `full_patrol_path[_patrol_path_index]` 순차 추적 |
| 10 | `tick()` 충돌 체크 — 축 분리 슬라이딩 | XZ 동시 blocked → X만 → Z만 시도 (Fleet 추가 버그) |
| 11 | `_build_mock_patrol_path()` 신규 | Occupancy grid 기반 간이 A* + 구간별 smoothing |
| 12 | `_smooth_mock_path()` 신규 | Line-of-sight 기반 경로 단축 |

---

## 3. Fleet 전용 추가 버그: Kevin-02 이동 불가

### 3-1. 증상

Kevin-02가 순찰 시작 후 제자리에서 이동하지 않음. Status 패널에는 AUTO_PATROL 모드로 표시되나 로봇 위치 변화 없음.

### 3-2. 원인

Kevin-02 시작 위치 `(8.0, -5.0)`이 z=-6 수평벽의 `mark_wall(8, -6, radius=1)` 확장 영역 바로 위.

```
Kevin-02 주변 그리드 (R=로봇, █=벽):
  z=-6.5: ███·███·██   ← 벽 radius=1 확장
  z=-6.0: ███·███·██   ← z=-6 수평벽 본체
  z=-5.5: ███·███·██   ← 벽 radius=1 확장
  z=-5.0: ·····R····   ← Kevin-02 시작 위치 (free)
  z=-4.5: ··········   ← free
```

A* 경로 계산은 성공하지만, `tick()`에서 이동 시 목표 방향(남쪽)으로 0.25m 전진하면 `(7.898, -5.228)` → grid `(59, 33)` = **벽(100)**. 단순 충돌 체크가 이동 자체를 차단하여 매 tick BLOCKED.

### 3-3. 수정: 축 분리 슬라이딩

```python
# Before — 단순 충돌 체크
new_x = robot_x + move_x
new_z = robot_z + move_z
gx, gz = w2g(new_x, new_z)
if grid[gx, gz] != 100:       # XZ 동시 이동만 시도
    robot_x, robot_z = new_x, new_z
# → 벽 옆에서 대각 이동 시 매번 BLOCKED

# After — 축 분리 슬라이딩
new_x = robot_x + move_x
new_z = robot_z + move_z

if is_free(new_x, new_z):          # 1) XZ 동시 이동
    robot_x = new_x
    robot_z = new_z
elif is_free(new_x, robot_z):      # 2) X축만 이동 (벽 따라 슬라이딩)
    robot_x = new_x
elif is_free(robot_x, new_z):      # 3) Z축만 이동
    robot_z = new_z
# → 벽 옆에서 X축으로 슬라이딩 → 벽 끝에서 정상 이동 재개
```

### 3-4. 검증 결과

```
step 0: (7.90,-5.00) X-ONLY    ← X축 슬라이딩으로 벽 회피
step 1: (7.81,-5.00) X-ONLY
step 2: (7.73,-5.00) X-ONLY
...
step 6: (7.50,-5.25) FULL      ← 벽 영역 벗어남, 정상 대각 이동
step 7: (7.45,-5.49) FULL
step 8: ARRIVED                 ← 다음 경로점 도달
```

---

## 4. Fleet 특이사항: tick() 변경 비교

Fleet의 기존 `tick()`은 sin/cos 기반 원형 궤적이었으나, A* 경로 추적으로 전면 교체.

```python
# Before (Fleet 원본) — sin/cos 원형 순찰
def tick(self):
    if self.patrol_mode:
        angle = self._t * self._patrol_speed * 0.3 + self._patrol_phase
        self.robot_x = self._patrol_offset_x + self._patrol_radius * math.sin(angle)
        self.robot_z = self._patrol_offset_z + self._patrol_radius * math.cos(angle)
        # → 벽 무시, 원형 궤적만 따라감

# After — A* 경로점 순차 추적
def tick(self):
    if self.patrol_mode:
        tx, tz = self.full_patrol_path[self._patrol_path_index]
        # 목표 방향 이동 + 축 분리 충돌 체크
        # 도달 시 _patrol_path_index++ (순환)
        # current_waypoint 동기화 (가장 가까운 원본 WP)
```

---

## 5. SLAM Map 렌더링 변경

### Before (Fleet 원본)

```python
# GL_LINE_LOOP — 모든 WP를 순환 직선 연결 (벽 관통)
for i in range(len(pts)):
    j = (i + 1) % len(pts)
    painter.drawLine(w2s(pts[i]), w2s(pts[j]))
```

### After

```python
# Layer 1: Planned Path (파란 실선) — A* 벽 회피 경로
painter.setPen(QPen(QColor(ACCENT_BLUE), 1.5))
for i in range(len(pts) - 1):                         # LINE_STRIP
    painter.drawLine(w2s(pts[i]), w2s(pts[i+1]))

# Layer 2: Waypoint Route (주황 대시선) — 순서 참고용
wp_pen = QPen(QColor(255, 180, 50, 180), 1.5, Qt.PenStyle.DashLine)
for i in range(len(orig_wps)):                         # LINE_LOOP (순환)
    j = (i + 1) % len(orig_wps)
    painter.drawLine(w2s(orig_wps[i]), w2s(orig_wps[j]))

# Layer 3: Waypoint Marker (파란 동그라미) — 원본 WP 15개만
for wx, wz in orig_wps:
    painter.drawEllipse(...)
```

---

## 6. MockSLAM 벽 구조 변경

### Before

```python
self.grid[20:60, 20:60] = 0        # 월드 (-12,-12)~(8,8)만 free
self.grid[30:32, 25:50] = 100      # 임의 벽 2줄
self.grid[44, 20:45] = 100
```

### After

```python
self.grid[4:84, 4:84] = 0          # 외벽 내부 전체 free

# generate_map() 동일 벽 배치
# 외벽 (±20), 내부 수평벽 (z=6, z=-6 갭 보존),
# 내부 수직벽 (x=-14, x=0, x=8), 장애물 12개
```

---

## 7. 수정 파일 요약

| 파일 | 위치 | 원본 라인 | 최종 라인 | 변경량 |
|------|------|:---------:|:---------:|:------:|
| data_provider.py | core/ | 429 | 441 | +12 |
| app.py (fleet) | dashboard_fleet/ | 2360 | ~2600 | +240 |
| app.py (single) | dashboard/ | ~2005 | ~2030 | +25 (충돌 체크만) |
| robot_manager.py | core/ | 180 | 180 | 변경 없음 |

---

## 8. 해결 이슈 총괄

| # | 이슈 | 출처 | 상태 |
|---|------|------|------|
| 1 | SLAM Map 경로 라인 벽 관통 | Single | ✅ A* 벽 회피 경로로 교체 |
| 2 | 로봇이 경로를 따라가지 않음 | Single | ✅ A* 중간점 순차 추적 |
| 3 | MockSLAM 맵 구조 불일치 | Single | ✅ generate_map() 동기화 |
| 4 | 경로가 너무 크게 돌아감 | Single | ✅ LOS path smoothing |
| 5 | Smoothing이 경로 전체를 제거 | Single | ✅ 구간별(WP→WP) smoothing |
| 6 | MockSim 벽 통과 | Single | ✅ occupancy grid 충돌 체크 |
| 7 | WP 연결선 소실 | Single | ✅ 주황 대시선 + 파란 마커 레이어 분리 |
| 8 | SLAM Reset 작동 안 함 | Single | ✅ free만 unknown 리셋 (벽 보존) |
| 9 | Stop→Start 시 출발점 회귀 | Single | ✅ 가장 가까운 WP부터 순환 경로 빌드 |
| 10 | Kevin-02 벽 옆 이동 불가 | **Fleet** | ✅ 축 분리 슬라이딩 (양쪽 적용) |

---

## 9. Multi Dashboard 추가 확인 사항

### 9-1. PATROL/STOP 적용 범위

현재 PATROL/STOP 버튼은 **활성 로봇(선택된 로봇)에만** 적용됨. 전체 로봇 일괄 순찰 시작/정지는 미구현.

```python
def _on_patrol(self):
    p = self._get_active_provider()     # 선택된 로봇만
    sim_ref = getattr(p, '_sim', None)
    sim_ref.start_patrol()
```

### 9-2. 각 로봇 독립 A* 경로

3대 로봇이 동일한 waypoint 리스트와 동일한 occupancy grid를 사용하지만, 시작 위치가 다르므로 각각 다른 A* 경로가 생성됨.

```
Kevin-01: start(-5,-10) → nearest WP1  → 경로 18pt
Kevin-02: start( 8, -5) → nearest WP12 → 경로 24pt
Kevin-03: start(-3,  8) → nearest WP5  → 경로 20pt
```

### 9-3. 잔여 과제

| 과제 | 우선순위 |
|------|---------|
| 전체 로봇 일괄 PATROL/STOP | 중간 |
| 로봇 간 경로 충돌 회피 (cooperative A*) | 높음 |
| 로봇별 독립 waypoint 세트 | 중간 |
| Fleet Overview에 A* 경로 표시 | 낮음 |
| SET GOAL → 선택 로봇 이동 연동 | Phase 4 |
