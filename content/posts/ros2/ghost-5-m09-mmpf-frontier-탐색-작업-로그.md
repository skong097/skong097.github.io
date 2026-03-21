---
title: "GHOST-5 M09 — MMPF Frontier 탐색 작업 로그"
date: 2026-03-21
draft: true
tags: ["ros2"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **Phase**: 3 — 군집 지능 **모듈**: M09"
---

# GHOST-5 M09 — MMPF Frontier 탐색 작업 로그

**날짜**: 2026-03-18  
**Phase**: 3 — 군집 지능  
**모듈**: M09  
**작업자**: Stephen Kong (`gjkong`)

---

## 개요

5대가 중복 없이 분산 탐색, 3회 실패 구역 자동 스킵 구현.  
FrontierDetector (OccupancyGrid → Frontier 추출 + 클러스터링) +  
FrontierManager (MMPF 포텐셜 함수 + Redis 원자적 Claim Blackboard).

---

## 생성 파일

| 파일 경로 | 설명 |
|---|---|
| `ghost5_navigation/ghost5_navigation/frontier_detector.py` | OccupancyGrid → Frontier 추출 + 클러스터링 |
| `ghost5_navigation/ghost5_navigation/frontier_manager.py` | MMPF + Redis Claim + skip_zones + 드론 우선 탐색 |
| `tests/unit/test_frontier_m09.py` | M09 완료 조건 검증 스크립트 |

---

## 핵심 설계

### MMPF 포텐셜 함수
```
U(f) = α × attraction(f) - β × robot_repulsion(f)

attraction(f)      = info_gain(f) / dist_to_frontier
robot_repulsion(f) = Σ 1 / dist_to_other_robot(f)

α = 1.0, β = 0.5
```

### Claim 흐름
```
compute_mmpf_goal()
  → 드론 우선 좌표(/swarm/frontier_priority) 있으면 우선 선택
  → skip_zones(3회 실패) 제외
  → MMPF 점수 최고 Frontier 선택
  → Redis SET NX 원자적 Claim (30초 TTL)
  → /swarm/frontier_claims 브로드캐스트
```

### skip_zones
```
탐색 실패 3회 이상 → skip_zone 등록 (5분 유효)
TTL 만료 후 자동 해제
```

---

## 빌드

```bash
# ghost5_navigation은 M06 때 이미 빌드됨
# frontier_detector.py, frontier_manager.py 파일 복사 후 재빌드
cd ~/ghost5/ghost5_ws
colcon build --packages-select ghost5_navigation --symlink-install
source install/setup.bash

# frontier_detector 실행
ros2 run ghost5_navigation frontier_detector 1

# frontier_manager 실행
ros2 run ghost5_navigation frontier_manager 1 5
```

---

## 완료 조건 검증

```bash
python3 tests/unit/test_frontier_m09.py
```

| 완료 조건 | 하드웨어 필요 | 상태 |
|---|---|---|
| 5대 동시 실행 시 동일 Frontier Claim 없음 | ✅ (멀티 프로세스) | ⬜ |
| 3회 실패 zone → skip_zones 등록 | ❌ (로직 검증 가능) | ⬜ |
| 표준 맵 10분 내 80% 커버리지 | ✅ | ⬜ |

---

## 카피 위치

```bash
cp ~/Downloads/ghost5_ws/src/ghost5_navigation/ghost5_navigation/frontier_detector.py \
   ~/ghost5/ghost5_ws/src/ghost5_navigation/ghost5_navigation/

cp ~/Downloads/ghost5_ws/src/ghost5_navigation/ghost5_navigation/frontier_manager.py \
   ~/ghost5/ghost5_ws/src/ghost5_navigation/ghost5_navigation/

cp ~/Downloads/ghost5_ws/tests/unit/test_frontier_m09.py \
   ~/ghost5/ghost5_ws/tests/unit/
```

---

## 비고

- `ghost5_navigation/setup.py`의 `frontier_detector`, `frontier_manager` entry_point는 M06 때 이미 선언됨
- Redis 미연결 시 로컬 dict로 fallback (단일 로봇 테스트 가능)
- 드론 우선 좌표 (`/swarm/frontier_priority`) 수신 시 해당 좌표 최인접 Frontier 1회 우선 선택
- `colcon build` 및 `ros2` CLI는 **venv 비활성화 상태**에서 실행
