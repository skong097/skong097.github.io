---
title: "GHOST-5 M05 — slam_toolbox 단일 로봇 SLAM 작업 로그"
date: 2026-03-21
draft: true
tags: ["ros2", "nav2", "slam"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **Phase**: 2 — 단일 로봇 자율주행 **모듈**: M05"
---

# GHOST-5 M05 — slam_toolbox 단일 로봇 SLAM 작업 로그

**날짜**: 2026-03-18  
**Phase**: 2 — 단일 로봇 자율주행  
**모듈**: M05  
**작업자**: Stephen Kong (`gjkong`)

---

## 개요

RPLiDAR C1 기반 실시간 2D 지도 생성 구현.  
`slam_toolbox async_slam_toolbox_node` 를 GHOST-5 멀티 로봇 네임스페이스(`robot_N/`)에 통합.

---

## 생성 파일 목록

| 파일 경로 | 설명 |
|---|---|
| `ghost5_bringup/config/slam_toolbox_params.yaml` | SLAM 핵심 파라미터 (RPi 5 최적화) |
| `ghost5_bringup/launch/slam.launch.py` | 단일 로봇 SLAM 전용 런치파일 |
| `ghost5_bringup/setup.py` | ghost5_bringup 패키지 설치 설정 |
| `ghost5_bringup/package.xml` | ghost5_bringup 패키지 의존성 정의 |
| `ghost5_slam/setup.py` | ghost5_slam 패키지 설치 설정 |
| `ghost5_slam/package.xml` | ghost5_slam 패키지 의존성 정의 |
| `tests/unit/test_slam_m05.py` | M05 완료 조건 자동 검증 스크립트 |

---

## 핵심 파라미터 요약

```yaml
# slam_toolbox_params.yaml 핵심 설정
resolution:           0.05    # 5cm 해상도
max_laser_range:      12.0    # RPLiDAR C1 최대 범위
minimum_travel_distance: 0.2  # 불필요한 업데이트 방지
do_loop_closing:      true
loop_match_minimum_chain_size: 3
mode:                 mapping
solver_plugin:        solver_plugins::CeresSolver
```

---

## 빌드 및 실행 방법

```bash
# ① colcon 빌드 (venv 비활성화 상태 필수)
cd ~/ghost5/ghost5_ws
colcon build --packages-select ghost5_bringup ghost5_slam --symlink-install
source install/setup.bash

# ② SLAM 단독 실행 (robot_id=1)
ros2 launch ghost5_bringup slam.launch.py robot_id:=1

# ③ 시뮬레이션 모드
ros2 launch ghost5_bringup slam.launch.py robot_id:=1 use_sim_time:=true
```

---

## M05 완료 조건 검증

```bash
# 기본 검증 (조건 1~2: /map 수신 + 지도 성장)
python3 tests/unit/test_slam_m05.py --robot-id 1 --timeout 30

# 전체 검증 (조건 1~3: 지도 저장 포함)
python3 tests/unit/test_slam_m05.py --robot-id 1 --timeout 30 --save-map
```

| 완료 조건 | 검증 방법 | 상태 |
|---|---|---|
| RViz2 실시간 지도 생성 확인 | `/robot_1/map` 토픽 수신 확인 | ⬜ |
| Loop Closure 동작 확인 | 지도 셀 증가 + 동일 구간 재방문 | ⬜ |
| 지도 저장/로드 정상 동작 | `map_saver_cli` 파일 생성 확인 | ⬜ |

---

## 다음 단계

- **M06** (병렬 가능): Nav2 + EKF 오도메트리 + 슬립 감지  
  → `ghost5_bringup/config/nav2_params.yaml`  
  → `ghost5_navigation/ghost5_navigation/slip_aware_ekf.py`

- **M07** (M05 완료 후): 2.5D Elevation Map + IMU 동적 보정  
  → `ghost5_slam/ghost5_slam/lidar_elevation_node.py`

---

## 비고

- `colcon build` 및 `ros2` CLI는 **venv 비활성화 상태**에서 실행
- SROS2 keystore 경로: `~/ghost5_keystore`
- 프레임 네이밍: `robot_{N}/odom`, `robot_{N}/base_link`, 공통 `map`
- `slam_toolbox_params.yaml` 의 `odom_frame` / `base_frame` 은  
  `slam.launch.py` 에서 `robot_id` 인자로 런타임에 동적 치환됨
