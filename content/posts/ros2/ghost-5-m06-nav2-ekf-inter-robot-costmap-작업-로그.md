---
title: "GHOST-5 M06 — Nav2 + EKF + Inter-Robot Costmap 작업 로그"
date: 2026-03-21
draft: true
tags: ["ros2", "nav2"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **Phase**: 2 — 단일 로봇 자율주행 **모듈**: M06"
---

# GHOST-5 M06 — Nav2 + EKF + Inter-Robot Costmap 작업 로그

**날짜**: 2026-03-18  
**Phase**: 2 — 단일 로봇 자율주행  
**모듈**: M06  
**작업자**: Stephen Kong (`gjkong`)

---

## 개요

단일 로봇 자율 목적지 주행 + 미끄러운 재난 환경 대응 구현.  
`nav2_params.yaml` 설정, `SlipAwareEKFTuner` 슬립 감지 노드,  
`InterRobotCostmapLayer` [B4] 타 로봇 동적 장애물 등록 노드 구현 완료.

---

## 생성 파일 목록

| 파일 경로 | 설명 |
|---|---|
| `ghost5_bringup/config/nav2_params.yaml` | Nav2 전체 파라미터 (Costmap, Planner, EKF, BT) |
| `ghost5_navigation/ghost5_navigation/slip_aware_ekf.py` | SlipAwareEKFTuner — IMU/Encoder 슬립 감지 + EKF 동적 보정 |
| `ghost5_navigation/ghost5_navigation/inter_robot_costmap_layer.py` | [B4] 타 로봇 위치 → Nav2 Costmap 동적 장애물 등록 |
| `ghost5_navigation/setup.py` | ghost5_navigation 패키지 설치 설정 |
| `ghost5_navigation/package.xml` | ghost5_navigation 패키지 의존성 정의 |
| `tests/unit/test_nav_m06.py` | M06 완료 조건 검증 스크립트 |

---

## 핵심 설계 요약

### SlipAwareEKFTuner
```
IMU 선속도(적분) vs 엔코더 선속도 차이 > 0.15 m/s
  → 슬립 감지
  → encoder_noise_cov: 0.01 → 5.0 (엔코더 신뢰도 하락, IMU 우선)

슬립 해제
  → encoder_noise_cov: 5.0 → 0.01 복구
```

### InterRobotCostmapLayer [B4]
```
/robot_N/pose × 4대 수집 (자신 제외)
  → TTL 0.3s 관리 (이동 후 잔상 자동 제거)
  → PointCloud2 변환 (z=0.1m 고정)
  → /swarm/robot_poses_array 5Hz 퍼블리시
  → Nav2 ObstacleLayer → local costmap 동적 장애물 반영
```

---

## 빌드 및 실행

```bash
# ① resource 마커 생성 (최초 1회)
mkdir -p ~/ghost5/ghost5_ws/src/ghost5_navigation/resource
touch ~/ghost5/ghost5_ws/src/ghost5_navigation/resource/ghost5_navigation

# ② colcon 빌드 (venv 비활성화 상태 필수)
cd ~/ghost5/ghost5_ws
colcon build --packages-select ghost5_navigation --symlink-install
source install/setup.bash

# ③ 슬립 감지 노드 실행 (robot_id=1)
ros2 run ghost5_navigation slip_aware_ekf_tuner 1

# ④ Inter-Robot Costmap Layer 실행
ros2 run ghost5_navigation inter_robot_costmap_layer 1 5
```

---

## M06 완료 조건 검증

```bash
# 로직 단위 테스트 (하드웨어 불필요)
python3 tests/unit/test_nav_m06.py --robot-id 1

# Nav2 실행 시 전체 검증
python3 tests/unit/test_nav_m06.py --robot-id 1 --check-nav --check-costmap
```

| 완료 조건 | 검증 방법 | 하드웨어 필요 | 상태 |
|---|---|---|---|
| NavigateToPose 목적지 이동 성공 | Action 결과 STATUS_SUCCEEDED | ✅ | ⬜ |
| 슬립 감지 로그 출력 확인 | warn 로그 "슬립 감지!" 출력 | ✅ | ⬜ |
| EKF 오도메트리 정확도 < 5cm | 1m 이동 후 오차 측정 | ✅ | ⬜ |
| [B4] robot_poses_array 5Hz | Hz 샘플 평균 4~6Hz | ❌ (로컬 테스트 가능) | ⬜ |
| [B4] costmap 장애물 마킹 | RViz2 시각 확인 | ✅ | ⬜ |
| [B4] 0.3s 내 장애물 자동 삭제 | TTL 초과 후 costmap 확인 | ✅ | ⬜ |

---

## 다음 단계

- **M07** (M05 완료 후): 2.5D Elevation Map + IMU 동적 보정  
  → `ghost5_slam/ghost5_slam/lidar_elevation_node.py`

---

## 비고

- `colcon build` 및 `ros2` CLI는 **venv 비활성화 상태**에서 실행
- `nav2_params.yaml`의 `robot_1/` 프레임명은 런치 시 `robot_id` 인자로 치환 필요
- `InterRobotCostmapLayer` qos_profiles 임포트 실패 시 BEST_EFFORT fallback 적용
- `SlipAwareEKFTuner._set_ekf_encoder_noise()` → ekf_node SetParameters 서비스  
  미준비 시 debug 로그만 출력 (하드웨어 없는 환경 안전 처리)
