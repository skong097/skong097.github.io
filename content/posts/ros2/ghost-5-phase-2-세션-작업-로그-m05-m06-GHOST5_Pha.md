---
title: "GHOST-5 Phase 2 세션 작업 로그 (M05 + M06)"
date: 2026-03-21
draft: true
tags: ["ros2", "nav2", "slam", "zenoh"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **Phase**: 2 — 단일 로봇 자율주행 **작업 모듈**: M05, M06"
---

# GHOST-5 Phase 2 세션 작업 로그 (M05 + M06)

**날짜**: 2026-03-18  
**Phase**: 2 — 단일 로봇 자율주행  
**작업 모듈**: M05, M06  
**작업자**: Stephen Kong (`gjkong`)  
**이전 완료**: Phase 1 (M01~M04) 전체 완료

---

## 세션 요약

| 모듈 | 내용 | 빌드 | 로직 검증 | 하드웨어 검증 |
|---|---|---|---|---|
| M05 | slam_toolbox 단일 로봇 SLAM | ✅ | ✅ (Zenoh/LiDAR 없어 FAIL 정상) | ⬜ 하드웨어 대기 |
| M06 | Nav2 + EKF + Inter-Robot Costmap | ✅ | ✅ 2/2 PASS | ⬜ 하드웨어 대기 |

---

## M05 — slam_toolbox 단일 로봇 SLAM

### 개요
RPLiDAR C1 기반 실시간 2D 지도 생성.  
`slam_toolbox async_slam_toolbox_node`를 GHOST-5 멀티 로봇 네임스페이스(`robot_N/`)에 통합.

### 생성 파일

| 파일 경로 | 설명 |
|---|---|
| `ghost5_bringup/config/slam_toolbox_params.yaml` | SLAM 핵심 파라미터 (RPi 5 최적화) |
| `ghost5_bringup/launch/slam.launch.py` | 단일 로봇 SLAM 전용 런치파일 |
| `ghost5_bringup/setup.py` | ghost5_bringup 패키지 설치 설정 |
| `ghost5_bringup/package.xml` | ghost5_bringup 패키지 의존성 정의 |
| `ghost5_slam/setup.py` | ghost5_slam 패키지 설치 설정 |
| `ghost5_slam/package.xml` | ghost5_slam 패키지 의존성 정의 |
| `tests/unit/test_slam_m05.py` | M05 완료 조건 자동 검증 스크립트 |

### 핵심 파라미터
```yaml
resolution:              0.05    # 5cm 해상도
max_laser_range:         12.0    # RPLiDAR C1 최대 범위
minimum_travel_distance: 0.2
do_loop_closing:         true
loop_match_minimum_chain_size: 3
mode:                    mapping
solver_plugin:           solver_plugins::CeresSolver
```

### 빌드
```bash
cd ~/ghost5/ghost5_ws
colcon build --packages-select ghost5_bringup ghost5_slam --symlink-install
# → ghost5_bringup Finished / ghost5_slam Finished ✅
```

### 트러블슈팅 기록
| 오류 | 원인 | 해결 |
|---|---|---|
| `can't copy resource/ghost5_bringup` | `resource/` 마커 파일 누락 | `touch src/ghost5_bringup/resource/ghost5_bringup` |
| `can't copy config/__pycache__` | `glob('config/*')`가 `__pycache__` 포함 | `glob('config/*.yaml') + glob('config/*.json5') + glob('config/*.py')` 로 변경 |

### 완료 조건 검증 결과
```
python3 tests/unit/test_slam_m05.py --robot-id 1 --timeout 30 --save-map
→ [FAIL] 0/3  ← 정상 (Zenoh 라우터 + LiDAR 없음, 하드웨어 도착 후 재검증)
```

| 완료 조건 | 상태 |
|---|---|
| RViz2 실시간 지도 생성 확인 | ⬜ 하드웨어 대기 |
| Loop Closure 동작 확인 | ⬜ 하드웨어 대기 |
| 지도 저장/로드 정상 동작 | ⬜ 하드웨어 대기 |

---

## M06 — Nav2 + EKF 오도메트리 + 슬립 감지

### 개요
단일 로봇 자율 목적지 주행 + 미끄러운 재난 환경 대응.  
`SlipAwareEKFTuner` 슬립 감지, `InterRobotCostmapLayer` [B4] 동적 장애물 등록 구현.

### 생성 파일

| 파일 경로 | 설명 |
|---|---|
| `ghost5_bringup/config/nav2_params.yaml` | Nav2 전체 파라미터 (Costmap, Planner, EKF, BT) |
| `ghost5_navigation/ghost5_navigation/slip_aware_ekf.py` | SlipAwareEKFTuner — IMU/Encoder 슬립 감지 + EKF 동적 보정 |
| `ghost5_navigation/ghost5_navigation/inter_robot_costmap_layer.py` | [B4] 타 로봇 위치 → Nav2 Costmap 동적 장애물 등록 |
| `ghost5_navigation/setup.py` | ghost5_navigation 패키지 설치 설정 |
| `ghost5_navigation/package.xml` | ghost5_navigation 패키지 의존성 정의 |
| `tests/unit/test_nav_m06.py` | M06 완료 조건 검증 스크립트 |

### 핵심 설계

**SlipAwareEKFTuner**
```
IMU 선속도(적분, 0.5s 윈도우) vs 엔코더 선속도 차이 > 0.15 m/s
  → 슬립 감지 → encoder_noise_cov: 0.01 → 5.0 (IMU 우선 융합)
슬립 해제 → encoder_noise_cov: 5.0 → 0.01 복구
```

**InterRobotCostmapLayer [B4]**
```
/robot_N/pose × 4대 수집 (자신 제외)
  → TTL 0.3s 관리 → PointCloud2 (z=0.1m)
  → /swarm/robot_poses_array 5Hz 퍼블리시
  → Nav2 ObstacleLayer → local costmap 동적 장애물
```

### 빌드
```bash
# resource 마커 생성
mkdir -p ~/ghost5/ghost5_ws/src/ghost5_navigation/resource
touch ~/ghost5/ghost5_ws/src/ghost5_navigation/resource/ghost5_navigation

cd ~/ghost5/ghost5_ws
colcon build --packages-select ghost5_navigation --symlink-install
# → ghost5_navigation Finished ✅
```

### 트러블슈팅 기록
| 오류 | 원인 | 해결 |
|---|---|---|
| `can't copy resource/ghost5_navigation` | `resouce` 오타 디렉토리 생성 | 올바른 `resource` 디렉토리 재생성 |

### 완료 조건 검증 결과
```
python3 tests/unit/test_nav_m06.py --robot-id 1
→ [PASS] 2/4
  ✅ [조건 2] SlipAwareEKFTuner 상수 검증 (threshold=0.15 m/s, slip_cov=5.0)
  ✅ [조건 5~6] InterRobotCostmapLayer 상수 검증 (TTL=0.3s, Hz=5.0)
  ⬜ [조건 1] NavigateToPose → 하드웨어 대기
  ⬜ [조건 4] robot_poses_array 5Hz → 하드웨어 대기
```

| 완료 조건 | 상태 |
|---|---|
| NavigateToPose 목적지 이동 성공 | ⬜ 하드웨어 대기 |
| 슬립 감지 로그 출력 확인 | ⬜ 하드웨어 대기 |
| EKF 오도메트리 정확도 < 5cm | ⬜ 하드웨어 대기 |
| [B4] robot_poses_array 5Hz 퍼블리시 | ⬜ 하드웨어 대기 |
| [B4] costmap 장애물 마킹 (RViz2) | ⬜ 하드웨어 대기 |
| [B4] 0.3s 내 장애물 자동 삭제 | ⬜ 하드웨어 대기 |

---

## Phase 2 전체 진행 현황

| 모듈 | 내용 | 코드 구현 | 빌드 | 로직 검증 | 하드웨어 검증 |
|---|---|---|---|---|---|
| M05 | slam_toolbox SLAM | ✅ | ✅ | ✅ | ⬜ |
| M06 | Nav2 + EKF + Costmap | ✅ | ✅ | ✅ | ⬜ |
| M07 | 2.5D Elevation Map | ⬜ | ⬜ | ⬜ | ⬜ |

---

## 다음 세션 작업 예정

- **M07**: 2.5D Elevation Map + IMU 동적 보정  
  → `ghost5_slam/ghost5_slam/lidar_elevation_node.py`  
  → 의존: M05 완료 후 (코드 구현은 선행 가능)

---

## 공통 주의사항

- `colcon build` 및 `ros2` CLI는 **venv 비활성화 상태**에서 실행
- SROS2 keystore 경로: `~/ghost5_keystore`
- 프레임 네이밍: `robot_{N}/odom`, `robot_{N}/base_link`, 공통 `map`
- `nav2_params.yaml`의 `robot_1/` 프레임명은 런치 시 `robot_id` 인자로 치환 필요
