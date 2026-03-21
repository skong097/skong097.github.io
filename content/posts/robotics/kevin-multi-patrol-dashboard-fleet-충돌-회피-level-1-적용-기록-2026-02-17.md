---
title: "Kevin Multi Patrol Dashboard — Fleet 충돌 회피 (Level 1) 적용 기록"
date: 2026-03-21
draft: true
tags: ["robotics", "fleet", "patrol"]
categories: ["robotics"]
description: "**작업일**: 2026-02-17 **기반 버전**: Kevin Patrol Dashboard v3.3 (Multi-Robot Fleet) **적용 대상**: `dashboard_fleet/app.py` (2601"
---

# Kevin Multi Patrol Dashboard — Fleet 충돌 회피 (Level 1) 적용 기록

**작업일**: 2026-02-17  
**기반 버전**: Kevin Patrol Dashboard v3.3 (Multi-Robot Fleet)  
**적용 대상**: `dashboard_fleet/app.py` (2601행 → 2655행, +54행)

---

## 1. 목적

3대 로봇(kevin_01~03)이 동일한 waypoint 리스트 + occupancy grid에서 독립 A* 경로를 생성하여 순찰 중, **경로 교차 지점에서 로봇 간 충돌을 방지**하기 위한 Level 1 근접 감지 + 우선순위 양보 메커니즘 적용.

---

## 2. 충돌 회피 레벨 정의

| Level | 방식 | 난이도 | 상태 |
|-------|------|--------|------|
| **Level 1** | **실시간 근접 감지 + ID 기반 우선순위 양보** | 낮음 | ✅ 적용 완료 |
| Level 2 | 시간 오프셋 + 구간 예약 + 속도 조절 | 중간 | 미적용 |
| Level 3 | Cooperative A* / CBS (시공간 3D 그래프) | 높음 | 미적용 |

---

## 3. Level 1 동작 원리

### 3-1. 매 tick (100ms) 흐름

```
tick() 진입
  │
  ├─ 양보 중? (_yield_state == True)
  │   ├─ 타이머 감소 (0.1초)
  │   ├─ 타이머 만료 → 양보 해제, 정상 진행
  │   └─ 타이머 남음 → 이동 중단, 센서만 업데이트, return
  │
  ├─ 근접 감지: fleet_registry 전체 순회
  │   ├─ 자기 자신 skip
  │   ├─ 정지 중인 로봇 skip
  │   ├─ 거리 < COLLISION_RADIUS (2.5m)?
  │   │   ├─ self.robot_id > other_id → 양보 (YIELD)
  │   │   └─ self.robot_id < other_id → 통과 (우선권)
  │   └─ 근접 로봇 없음 → 통과
  │
  └─ 기존 A* 경로 추적 진행
```

### 3-2. 우선순위 규칙

ID 사전순(lexicographic) 비교. **ID가 작을수록 높은 우선순위**.

```
kevin_01 vs kevin_02 근접 → kevin_02 양보
kevin_01 vs kevin_03 근접 → kevin_03 양보
kevin_02 vs kevin_03 근접 → kevin_03 양보
```

10대 확장 시:
```
kevin_01 — 최고 우선순위 (양보 안 함)
kevin_02 — 01에게만 양보
kevin_03 — 01, 02에게 양보
...
kevin_10 — 01~09 모두에게 양보 (최저 우선순위)
```

### 3-3. 3대 동시 근접 시 (교착 방지 검증)

```
kevin_01, 02, 03이 한 지점에 모일 경우:
  → kevin_03: 01, 02 둘 다 보고 양보 (OK)
  → kevin_02: 01 보고 양보 (OK)
  → kevin_01: 누구에게도 양보 안 함 → 통과
  → kevin_01 이탈 후 kevin_02 양보 해제 → 진행
  → kevin_02 이탈 후 kevin_03 양보 해제 → 진행
  → 교착(deadlock) 없음 ✅
```

---

## 4. 설정 상수

```python
COLLISION_RADIUS = 2.5     # 충돌 감지 반경 (m)
YIELD_DURATION = 1.5       # 양보 시 정지 시간 (초)
```

---

## 5. 수정 내역

### 5-1. MockSimForDashboard.__init__() — 속성 추가

```python
# 기존 파라미터에 robot_id 추가
def __init__(self, robot_id="kevin_01", patrol_radius=5.0, ...):
    self.robot_id = robot_id

    # Fleet 충돌 회피 (Level 1)
    self._fleet_registry: dict[str, 'MockSimForDashboard'] = {}
    self._yield_state = False       # 현재 양보 중 여부
    self._yield_timer = 0.0         # 양보 남은 시간 (초)
    self.COLLISION_RADIUS = 2.5     # 충돌 감지 반경 (m)
    self.YIELD_DURATION = 1.5       # 양보 시 정지 시간 (초)
    self._yield_count = 0           # 양보 횟수 (모니터링용)
```

### 5-2. tick() — 충돌 회피 로직 삽입

```python
def tick(self):
    self._t += 0.1

    if self.patrol_mode:
        # ── 양보 타이머 처리 ──
        if self._yield_state:
            self._yield_timer -= 0.1
            if self._yield_timer <= 0:
                self._yield_state = False
                self._yield_timer = 0.0
            else:
                self.robot_speed = 0.0
                self._update_sensors()
                return

        # ── 근접 감지 ──
        if self._fleet_registry and self.patrol_mode:
            for other_id, other_sim in self._fleet_registry.items():
                if other_id == self.robot_id:
                    continue
                if not other_sim.patrol_mode:
                    continue
                d = math.sqrt((self.robot_x - other_sim.robot_x)**2 +
                              (self.robot_z - other_sim.robot_z)**2)
                if d < self.COLLISION_RADIUS:
                    if self.robot_id > other_id:  # ID 큰 쪽이 양보
                        self._yield_state = True
                        self._yield_timer = self.YIELD_DURATION
                        self._yield_count += 1
                        self.robot_speed = 0.0
                        self._update_sensors()
                        return

        # 이하 기존 A* 경로 추적 로직 동일...
```

### 5-3. _update_sensors() — 신규 메서드

기존 tick() 하단의 LiDAR/감지/사람 상태 업데이트를 별도 메서드로 분리. tick()과 양보 상태 모두에서 호출.

```python
def _update_sensors(self):
    """LiDAR, 감지, 사람 상태 업데이트 (tick/양보 공용)"""
    # LiDAR, detection, persons 업데이트
```

### 5-4. main() — fleet registry 주입

```python
all_sims: dict[str, MockSimForDashboard] = {}

for cfg in ROBOT_CONFIGS:
    sim = MockSimForDashboard(
        robot_id=cfg["id"],     # ← robot_id 전달
        ...
    )
    all_sims[cfg["id"]] = sim
    ...

# Fleet registry를 각 sim에 주입
for sim in all_sims.values():
    sim._fleet_registry = all_sims
```

---

## 6. 확장성 검증

| 항목 | 결과 |
|------|------|
| 3대 → 10대 확장 | ✅ ROBOT_CONFIGS에 항목 추가만으로 동작 |
| fleet_registry 자동 인식 | ✅ dict 참조 공유 — 추가된 로봇 즉시 감지 |
| 교착(deadlock) 방지 | ✅ ID 사전순 전순서(total order) 보장 |
| O(N²) 성능 | ✅ 10대 = tick당 90회 거리계산, 문제없음 |
| 20대 이상 | ⚠️ 공간 해싱(spatial hash) 도입 검토 필요 |

---

## 7. 수정 파일 요약

| 파일 | 원본 라인 | 최종 라인 | 변경량 |
|------|:---------:|:---------:|:------:|
| app.py (fleet) | 2601 | 2655 | +54 |

---

## 8. 테스트 결과

- 3대 동시 PATROL 시작 → 정상 순찰 ✅
- 경로 교차 지점에서 우선순위 낮은 로봇 양보 → 정상 동작 ✅
- 양보 후 재진행 → 정상 복귀 ✅

---

## 9. 향후 개선 과제

| 과제 | 우선순위 | 비고 |
|------|---------|------|
| 동적 우선순위 (목표 잔여 거리 기반) | 낮음 | 고정 ID 순위가 불공평할 경우 |
| 양보 타이머 순위 기반 점진 증가 | 낮음 | 다수 로봇 밀림 방지 |
| 공간 해싱 (20대+) | 낮음 | O(N²) → O(N) |
| Level 2: 구간 예약 + 속도 조절 | 중간 | 좁은 통로 교행 최적화 |
| Level 3: Cooperative A* / CBS | 높음 | 시공간 최적 경로 계획 |
