---
title: "GHOST-5 M10 — Multi-Robot SLAM + Delta Map Merger 작업 로그"
date: 2026-03-21
draft: true
tags: ["ros2", "slam"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **Phase**: 3 — 군집 지능 **모듈**: M10"
---

# GHOST-5 M10 — Multi-Robot SLAM + Delta Map Merger 작업 로그

**날짜**: 2026-03-18  
**Phase**: 3 — 군집 지능  
**모듈**: M10  
**작업자**: Stephen Kong (`gjkong`)

---

## 개요

5대 로컬 맵을 글로벌 맵으로 통합, Delta Update로 대역폭 10~20% 사용.  
3-레이어 병합 (2D OccupancyGrid + Elevation + LowObstacle) +  
PoseGraphPublisher (TF fallback용 pose 공유).

---

## 생성 파일

| 파일 경로 | 설명 |
|---|---|
| `ghost5_slam/ghost5_slam/map_merger_node.py` | 3-레이어 Delta 병합 노드 |
| `ghost5_slam/ghost5_slam/pose_graph_publisher.py` | 로봇 pose 수집 → /map_merge/pose_graph |
| `ghost5_slam/setup.py` | pose_graph_publisher entry_point 추가 |
| `tests/unit/test_map_merger_m10.py` | M10 완료 조건 검증 스크립트 |

---

## 핵심 설계

### Delta Update 전략
```
prev_maps[robot_id] vs 현재 맵 비교
→ 변경 셀 수 / 전체 셀 수 = Delta 비율 로그
→ Delta > 20% 시 warn 출력
→ 변경 있을 때만 robot_maps 갱신
```

### 병합 원칙 (Layer 1: 2D)
```
TF lookup → 로컬 → 글로벌 좌표 변환
동일 셀 복수 로봇 데이터 → Majority Vote
  occupied(>0) 다수 → 100
  free(0) 다수 → 0
  동수 → free 우선
```

### Layer 2+3 병합 (Elevation + LowObstacle)
```
최대 비용(max) 우선 채택
TF 실패 시 origin offset으로 fallback
```

### [B1] TF Buffer 30s
```
tf2_ros.Buffer(cache_time=Duration(seconds=30))
드론 좌표 지연 최대 3초 후에도 TF 조회 성공
```

---

## 빌드

```bash
cd ~/ghost5/ghost5_ws
colcon build --packages-select ghost5_slam --symlink-install
source install/setup.bash

# 실행 (Leader 로봇에서)
ros2 run ghost5_slam map_merger_node 5
ros2 run ghost5_slam pose_graph_publisher 5
```

---

## 완료 조건 검증

```bash
# 로직 단위 테스트
python3 tests/unit/test_map_merger_m10.py
```

| 완료 조건 | 하드웨어 필요 | 상태 |
|---|---|---|
| /map_merge/global_map 토픽 퍼블리시 | ✅ | ⬜ |
| 2대 로봇 지도 글로벌 맵 통합 확인 | ✅ | ⬜ |
| Delta Update 비율 < 20% 로그 | ✅ | ⬜ |

---

## 카피 위치

```bash
cp ~/Downloads/ghost5_ws/src/ghost5_slam/ghost5_slam/map_merger_node.py \
   ~/ghost5/ghost5_ws/src/ghost5_slam/ghost5_slam/

cp ~/Downloads/ghost5_ws/src/ghost5_slam/ghost5_slam/pose_graph_publisher.py \
   ~/ghost5/ghost5_ws/src/ghost5_slam/ghost5_slam/

cp ~/Downloads/ghost5_ws/src/ghost5_slam/setup.py \
   ~/ghost5/ghost5_ws/src/ghost5_slam/

cp ~/Downloads/ghost5_ws/tests/unit/test_map_merger_m10.py \
   ~/ghost5/ghost5_ws/tests/unit/
```

---

## 비고

- `colcon build` 및 `ros2` CLI는 **venv 비활성화 상태**에서 실행
- `map_merger_node`는 Leader 로봇에서만 실행 (M08 Leader Election 연동)
- `pose_graph_publisher`는 전체 로봇에서 실행
- TF 미준비 시 origin offset fallback 적용 (하드웨어 없는 환경 안전 처리)
