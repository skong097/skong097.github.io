---
title: "GHOST-5 구현 단계 로드맵"
date: 2026-03-21
draft: true
tags: ["ros2", "nav2", "slam", "zenoh"]
categories: ["ros2"]
description: "> GPS-denied Hazard Operation with Swarm Team — 5 Units > 작성일: 2026-03-17 | 기반 문서: GHOST5_plan_v2.md > 총 20개 모듈 / 7개 Pha"
---

# GHOST-5 구현 단계 로드맵

> GPS-denied Hazard Operation with Swarm Team — 5 Units  
> 작성일: 2026-03-17 | 기반 문서: GHOST5_plan_v2.md  
> 총 20개 모듈 / 7개 Phase / 지상 5대 + 가상 드론 통합

---

## 목차

1. [전체 모듈 개요](#1-전체-모듈-개요)
2. [의존 관계 및 병렬 구현 전략](#2-의존-관계-및-병렬-구현-전략)
3. [Phase 1 — 기반 인프라](#3-phase-1--기반-인프라-m01m04)
4. [Phase 2 — 단일 로봇 자율주행](#4-phase-2--단일-로봇-자율주행-m05m07)
5. [Phase 3 — 군집 지능](#5-phase-3--군집-지능-m08m10)
6. [Phase 4 — 생존자 감지](#6-phase-4--생존자-감지-m11m12)
7. [Phase 5 — GCS + 시각화](#7-phase-5--gcs--시각화-m13m14)
8. [Phase 6 — 드론 통합 3-A](#8-phase-6--드론-통합-3-a-m15m17)
9. [Phase 7 — PX4 SITL + 최종 검증](#9-phase-7--px4-sitl--최종-검증-m18m20)
10. [진입 조건 체크리스트](#10-진입-조건-체크리스트)
11. [개발 세션 로그 규칙](#11-개발-세션-로그-규칙)

---

## 1. 전체 모듈 개요

| 모듈 | Phase | 기술 영역 | 핵심 파일 | 병렬 가능 |
|------|-------|-----------|-----------|-----------|
| M01 | 1 | 미들웨어 | `qos_profiles.py`, `zenoh_config.json5` | — |
| M02 | 1 | 인터페이스 | `ghost5_interfaces/` 전체 | M01 완료 후 |
| M03 | 1 | 공유 상태 | `blackboard.py`, `semantic_memory.py` | M02 완료 후 |
| M04 | 1 | 보안 | `setup_sros2.sh`, `ghost5_policy.xml` | M01 완료 후 |
| M05 | 2 | SLAM | `slam_toolbox_params.yaml` | M01~M04 완료 후 |
| M06 | 2 | 자율주행 | `nav2_params.yaml`, `slip_aware_ekf.py` | M05와 병렬 |
| M07 | 2 | 인지 | `lidar_elevation_node.py` | M05 완료 후 |
| M08 | 3 | 군집 지능 | `leader_election.py`, `election_guard.py` | M09, M10과 병렬 |
| M09 | 3 | 탐색 | `frontier_detector.py`, `frontier_manager.py` | M08, M10과 병렬 |
| M10 | 3 | 지도 | `map_merger_node.py`, `pose_graph_publisher.py` | M08, M09와 병렬 |
| M11 | 4 | 감지 | `proximity_detector.py`, `victim_fuser.py` | M12와 병렬 |
| M12 | 4 | 통신 | `comm_monitor.py` | M11과 병렬 |
| M13 | 5 | API | `gcs_api.py`, `paged_query.py` | M14와 병렬 |
| M14 | 5 | 시각화 | `foxglove_publisher.py` | M13과 병렬 |
| M15 | 6 | 드론 시뮬 | `fake_drone_node.py` | Phase 5 완료 후 |
| M16 | 6 | 드론 연동 | `drone_nav_bridge.py`, `drone_gossip_bridge.py` | M15 완료 후 |
| M17 | 6 | 드론 Fallback | `drone_fallback_monitor.py` | M16과 병렬 |
| M18 | 7 | PX4 SITL | `px4_topic_bridge.py` | M17 완료 후 |
| M19 | 7 | NPU 가속 | `vision_detector_npu.py` | M18과 병렬 (선택) |
| M20 | 7 | 통합 검증 | `benchmark/` 전체 | M18, M19 완료 후 |

---

## 2. 의존 관계 및 병렬 구현 전략

```
M01 (rmw_zenoh)
  ├── M02 (메시지 정의)
  │     └── M03 (Redis Blackboard)
  │           ├── M08 (Leader Election)  ─┐
  │           ├── M09 (MMPF Frontier)    ─┼─ Phase 3 병렬
  │           └── M10 (Map Merger)       ─┘
  └── M04 (SROS2)  ← M01 완료 직후 병렬 가능

M05 (SLAM) ─┬─ M07 (Elevation Map)
             └─ M06 (Nav2 + EKF)  ← M05와 병렬

M11 (생존자 감지) ─┐
M12 (Rendezvous)  ─┘  ← Phase 4 병렬

M13 (GCS API)   ─┐
M14 (Foxglove)  ─┘  ← Phase 5 병렬

M15 → M16 → M17  ← Phase 6 순차
M18 → M20        ← Phase 7 순차
M19              ← M18과 병렬 (선택 모듈)
```

**병렬 구현 권장 조합:**
- `M08 + M09 + M10`: 각각 독립 구현 후 통합 테스트
- `M11 + M12`: 센서 노드와 통신 노드 분리 개발
- `M13 + M14`: API 서버와 시각화 레이어 분리 개발
- `M16 + M17`: 드론 브릿지와 Fallback 모니터 분리 개발

---

## 3. Phase 1 — 기반 인프라 (M01~M04)

> **완료 기준**: rmw_zenoh 통신 확인, Redis 정상 동작, SROS2 keystore 생성 완료

### M01 — rmw_zenoh + QoS 프로파일

**목표**: 모든 로봇 간 기반 통신 레이어 구축

**구현 파일**
- `ghost5_bringup/config/qos_profiles.py`
- `ghost5_bringup/config/zenoh_config.json5`

**핵심 작업**
```bash
# 설치
sudo apt install ros-jazzy-rmw-zenoh-cpp

# 환경변수 등록 (~/.bashrc)
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
export ROS_DOMAIN_ID=42

# Leader 로봇에서 Zenoh 라우터 실행
ros2 run rmw_zenoh_cpp init_rmw_zenoh_router
```

**QoS 3종 정의**
| 프로파일 | 용도 | Reliability | Durability |
|----------|------|-------------|------------|
| `POSE_QOS` | 위치/상태 (10Hz) | BEST_EFFORT | VOLATILE |
| `MAP_QOS` | 지도/Elevation (1~2Hz) | RELIABLE | TRANSIENT_LOCAL |
| `EVENT_QOS` | 생존자/선거/이벤트 | RELIABLE | TRANSIENT_LOCAL + KEEP_ALL |

**완료 조건**
- [ ] `ros2 topic list`에서 `/swarm/*` 토픽 확인
- [ ] 두 노드 간 POSE_QOS 통신 지연 < 50ms 확인
- [ ] Zenoh 라우터 정상 실행 확인

---

### M02 — 커스텀 메시지/서비스/액션 정의

**목표**: GHOST-5 전용 통신 인터페이스 완전 정의

**구현 파일** (`ghost5_interfaces/`)
```
msg/
  RobotState.msg
  FrontierList.msg
  VictimDetection.msg
  SwarmStatus.msg
  DroneStatus.msg        # Phase 6 드론용
srv/
  ClaimFrontier.srv
  GetGlobalMap.srv
action/
  ExploreRegion.action
```

**메시지 정의 핵심**
```
# RobotState.msg
int32   robot_id
geometry_msgs/Pose2D pose
string  status          # EXPLORING | VICTIM_FOUND | RETURNING | DOWN
float32 battery_percent
float32 coverage_percent
builtin_interfaces/Time timestamp

# VictimDetection.msg
int32  detected_by_robot
geometry_msgs/Point location
float32 us_confidence
float32 ir_confidence
float32 vision_confidence
float32 combined_confidence
string  source          # ground | drone
builtin_interfaces/Time timestamp

# DroneStatus.msg  (Phase 6 신규)
geometry_msgs/Point enu_position
float32 battery_percent
bool    wifi_relay_active
string  mode            # PATROL | RESPONDING | FALLBACK
builtin_interfaces/Time timestamp
```

**완료 조건**
- [ ] `colcon build --packages-select ghost5_interfaces` 성공
- [ ] `ros2 interface show ghost5_interfaces/msg/RobotState` 정상 출력
- [ ] 모든 메시지 타입 Python import 테스트 통과

---

### M03 — Redis Blackboard + Semantic Event Memory

**목표**: 리더 교체 시 컨텍스트 완전 승계, 원자적 Frontier Claim

**구현 파일**
- `ghost5_swarm/ghost5_swarm/blackboard.py`
- `ghost5_swarm/ghost5_swarm/semantic_memory.py`
- `ghost5_swarm/ghost5_swarm/election_guard.py`

**Redis 구조**
```
robot:{id}:state         → RobotState JSON (TTL 5s)
frontier:claims          → Hash {frontier_id: robot_id}
victims                  → Hash {victim_id: VictimDetection JSON}
events:timeline          → Sorted Set {event_id: timestamp}
event:{id}               → SemanticEvent JSON
swarm:election:write_lock → 선거 중 쓰기 잠금 (TTL 10s)
```

**핵심 구현 포인트**
- `claim_frontier()`: Redis SET NX (원자적 Claim, 중복 방지)
- `add_victim()`: WAIT(1, 100ms) 동기 쓰기 (복제 지연 대응)
- `promote_replica_to_master()`: 리더 교체 시 Replica 승격
- `ElectionGuard`: 선거 중 Write Lock + 재시도 로직
- `SemanticMemory.get_context_summary()`: 새 리더 즉시 상황 파악

**완료 조건**
- [ ] Redis PING/PONG 정상 확인
- [ ] Frontier Claim 원자성 테스트 (동시 5개 요청 → 1개만 성공)
- [ ] Leader 교체 후 SemanticMemory 컨텍스트 승계 확인
- [ ] `check_slave_lag_and_warn()` 복제 지연 모니터링 동작 확인

---

### M04 — SROS2 보안 설정

**목표**: DDS 트래픽 AES-GCM 암호화, 로봇별 X.509 인증

**구현 파일**
- `scripts/setup_sros2.sh`
- `ghost5_policy.xml`

**설정 순서**
```bash
# 1. Keystore 초기화 (GCS에서 1회)
ros2 security create_keystore ~/ghost5_keystore

# 2. 로봇별 노드 인증서 생성
for i in 1 2 3 4 5; do
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/slam_node
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/swarm_node
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/victim_detector
done

# 3. 권한 정책 적용
ros2 security generate_artifacts -k ~/ghost5_keystore -p ghost5_policy.xml

# 4. 환경변수 (모든 로봇 .bashrc)
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=~/ghost5_keystore
```

**SROS2 알려진 취약점 대응**
| 취약점 | 대응 |
|--------|------|
| V1: 인증서 만료 미갱신 | 정책 변경 시 전체 keystore 재생성 스크립트 |
| V2: 정책 업데이트 레이스 | 배포 전 모든 노드 중단 → 배포 → 재시작 |
| V3: 기본값 취약성 | `rtps_protection_kind: ENCRYPT` 강제 설정 |
| V4: 도메인 격리 우회 | `ROS_DOMAIN_ID=42` 고정 + 네트워크 분리 |

**완료 조건**
- [ ] 인증서 없는 노드의 토픽 수신 차단 확인
- [ ] SROS2 적용 후 통신 지연 증가 < 10ms 확인
- [ ] `ros2 security check_policy` 경고 없음 확인

---

## 4. Phase 2 — 단일 로봇 자율주행 (M05~M07)

> **완료 기준**: Pinky Pro 1대가 미지 공간을 자율 SLAM + Nav2로 탐색, Elevation Map 생성

### M05 — slam_toolbox 단일 로봇 SLAM

**목표**: RPLiDAR C1 기반 실시간 지도 생성

**구현 파일**
- `ghost5_bringup/config/slam_toolbox_params.yaml`

**핵심 파라미터**
```yaml
slam_toolbox:
  ros__parameters:
    odom_frame:  robot_1/odom
    base_frame:  robot_1/base_link
    map_frame:   map
    resolution:  0.05          # 5cm 해상도
    max_laser_range: 12.0      # RPLiDAR C1 최대 범위
    do_loop_closing: true
    loop_match_minimum_chain_size: 3
    mode: mapping
```

**완료 조건**
- [ ] RViz2에서 실시간 지도 생성 확인
- [ ] Loop Closure 동작 확인 (같은 구간 재방문 시)
- [ ] 지도 저장/로드 (`map_saver_cli`) 정상 동작

---

### M06 — Nav2 + EKF 오도메트리 + 슬립 감지

**목표**: 단일 로봇 자율 목적지 주행 + 미끄러운 재난 환경 대응

**구현 파일**
- `ghost5_bringup/config/nav2_params.yaml`
- `ghost5_navigation/ghost5_navigation/slip_aware_ekf.py`

**SlipAwareEKFTuner 동작**
```
IMU 선속도 vs 엔코더 선속도 차이 > 0.15 m/s
  → 슬립 감지
  → encoder_noise_cov: 0.01 → 5.0 (엔코더 신뢰도 하락)
  → IMU 우선 융합 전환

슬립 해제
  → encoder_noise_cov: 5.0 → 0.01 복귀
```

**완료 조건**
- [ ] `NavigateToPose` Action으로 목적지 이동 성공
- [ ] 미끄러운 바닥에서 슬립 감지 로그 출력 확인
- [ ] EKF 오도메트리 정확도 < 5cm (1m 이동 기준)

---

### M07 — 2.5D Elevation Map + IMU 동적 보정

**목표**: RPLiDAR 단일 수평 스캔으로 높이 정보 추출, Ghost Obstacle 제거

**구현 파일**
- `ghost5_slam/ghost5_slam/lidar_elevation_node.py`

**IMU 보정 로직**
```
|pitch| 또는 |roll| > 15°  → 스캔 전체 폐기
5° ~ 15°                   → R_imu 회전 행렬 보정 적용
< 5°                       → 보정 없이 직접 사용
```

**Temporal Consistency Filter**
```
hits >= 3  AND  지속 시간 >= 2초  → 장애물 확정
last_seen 후 10초 경과            → 셀 자동 소멸 (Decay)
```

**Ray-casting Clearing**
```
LiDAR 빔 통과 시 해당 셀 hits 감소
hits <= 0 → 셀 삭제 (Ghost Trail 제거)
```

**비용 할당**
| 높이 | Costmap 비용 |
|------|-------------|
| h < 10cm | 10 (통과 가능) |
| 10cm ≤ h < 22cm | 60 (주의) |
| h ≥ 22cm | 100 (통과 불가) |

**완료 조건**
- [ ] `/robot_1/elevation_layer` 토픽 퍼블리시 확인
- [ ] 경사로 주행 시 Ghost Obstacle 미생성 확인
- [ ] RViz2에서 Elevation Layer Costmap 시각화 확인

---

## 5. Phase 3 — 군집 지능 (M08~M10)

> **완료 기준**: 2대 이상에서 리더 선출, Frontier 중복 없이 탐색, 지도 병합 확인
> **병렬 구현 가능**: M08 + M09 + M10 각각 독립 개발 후 통합

### M08 — Bully Algorithm Leader Election

**목표**: 5대 중 생존 로봇 중 최고 ID가 3초 내 리더로 선출

**구현 파일**
- `ghost5_swarm/ghost5_swarm/leader_election.py`
- `ghost5_swarm/ghost5_swarm/election_guard.py`

**핵심 파라미터**
```python
HEARTBEAT_INTERVAL_SEC = 1.0
LEADER_TIMEOUT_SEC     = 3.0    # 미수신 시 선거 발동
ELECTION_TIMEOUT_SEC   = 3.0    # 응답 없으면 VICTORY 선언
QUORUM_SIZE            = 3      # Split-Brain 방지 최소 합의 수
BACKOFF_STEP_SEC       = 0.1    # Election Storm 방지 ID 기반 지연
```

**Election Storm 방지 (Backoff)**
```
delay = (MAX_ROBOT_ID - my_id) × BACKOFF_STEP_SEC
Robot-5: 0.0s → Robot-4: 0.1s → Robot-3: 0.2s → Robot-1: 0.4s
```

**Split-Brain 방지 (Quorum)**
```
VICTORY 선언 전 최소 3대가 /swarm/leader_dead 투표
쿼럼 미달 → QUORUM_TIMEOUT(5s) 대기 후 재시도 (최대 3회)
```

**완료 조건**
- [ ] 5대 시뮬 → Robot-5가 Leader 선출 확인
- [ ] Robot-5 강제 종료 → Robot-4가 3초 내 선출 확인
- [ ] 동시 선거 발동 시 Election Storm 없음 확인
- [ ] Split-Brain 시나리오에서 쿼럼 미달로 승격 차단 확인

---

### M09 — MMPF Frontier 탐색 + Claim Blackboard

**목표**: 5대가 중복 없이 분산 탐색, 3회 실패 구역 자동 스킵

**구현 파일**
- `ghost5_navigation/ghost5_navigation/frontier_detector.py`
- `ghost5_navigation/ghost5_navigation/frontier_manager.py`

**MMPF 포텐셜 함수**
```
U(f) = α × attraction(f) - β × robot_repulsion(f)

attraction(f)    = info_gain(f) / dist_to_frontier
robot_repulsion  = Σ 1 / dist_to_other_robot(f)

α = 1.0, β = 0.5
```

**Claim 흐름**
```
compute_mmpf_goal()
  → 드론 우선 좌표 있으면 해당 위치 우선 선택
  → skip_zones 제외
  → MMPF 점수 최고 Frontier 선택
  → Redis SET NX로 원자적 Claim
  → /swarm/frontier_claims 브로드캐스트
  → 30초 TTL 자동 만료
```

**완료 조건**
- [ ] 5대 동시 실행 시 동일 Frontier Claim 없음 확인
- [ ] 3회 실패 zone이 skip_zones에 추가되는지 확인
- [ ] 표준 맵에서 10분 내 80% 이상 커버리지 달성

---

### M10 — Multi-Robot SLAM + Delta Map Merger

**목표**: 5대 로컬 맵을 글로벌 맵으로 통합, 대역폭 10~20% 사용

**구현 파일**
- `ghost5_slam/ghost5_slam/map_merger_node.py`
- `ghost5_slam/ghost5_slam/pose_graph_publisher.py`

**3-레이어 병합**
```
Layer 1: 2D OccupancyGrid  (slam_toolbox, LiDAR 수평)
Layer 2: Elevation Layer   (lidar_elevation_node, Z-stack)
Layer 3: LowObstacle Layer (camera_low_obstacle_node, 15cm 이하)
```

**Delta Update 전략**
```
각 로봇의 이전 맵 vs 현재 맵 비교
→ 변경된 셀만 추출하여 병합
→ 전체 맵 대비 10~20% 대역폭 사용
```

**완료 조건**
- [ ] `/map_merge/global_map` 토픽 퍼블리시 확인
- [ ] 2대 로봇 지도가 글로벌 맵에 통합되는지 확인
- [ ] Delta Update 비율 < 20% 로그 확인

---

## 6. Phase 4 — 생존자 감지 (M11~M12)

> **완료 기준**: 3-센서 교차 검증으로 오탐 최소화, 통신 단절 시 자율 복귀
> **병렬 구현 가능**: M11 + M12 독립 개발

### M11 — 3-센서 생존자 감지 (US-016 + TCRT5000 + YOLOv8n)

**목표**: 오탐 최소화를 위한 3-센서 교차 검증 융합

**구현 파일**
- `ghost5_victim/ghost5_victim/proximity_detector.py`
- `ghost5_victim/ghost5_victim/vision_detector.py`
- `ghost5_victim/ghost5_victim/victim_fuser.py`
- `ghost5_victim/ghost5_victim/triangulation.py`

**센서 스펙 및 감지 조건**
| 센서 | 범위 | 감지 조건 |
|------|------|-----------|
| US-016 초음파 | 2cm ~ 400cm | 20~150cm 범위에서 연속 5회 이상 |
| TCRT5000 IR | ~30cm | ADC 300~700 (현장 캘리브레이션) |
| 5MP YOLOv8n | 전방 | 인체 클래스 confidence > 0.6 |

**융합 신뢰도 계산**
```
combined = 0.6 × us_confidence + 0.4 × ir_confidence
단일 센서 단독:     < 0.6  → 무시
2개 센서 교차:      0.6~0.8 → 의심 (추적 시작)
3개 센서 모두:      > 0.8  → 확정 보고
3대 이상 동시 감지: 삼각측량으로 위치 정밀도 향상
```

**완료 조건**
- [ ] 실제 사람 앞 20~150cm에서 US-016 감지 확인
- [ ] YOLOv8n 인체 감지 confidence > 0.6 확인
- [ ] 3-센서 융합 후 `/swarm/victim` 퍼블리시 확인
- [ ] 오탐률 < 5% (비어있는 공간에서 10분 테스트)

---

### M12 — Rendezvous 프로토콜 + RSSI Gradient Map

**목표**: 통신 단절 시 신호 강도 지도 기반 자율 복귀

**구현 파일**
- `ghost5_swarm/ghost5_swarm/comm_monitor.py`

**RSSI 4단계 대응**
```
RSSI ≥ -70dBm  (Safe)    → 정상 탐색
RSSI ≥ -75dBm  (Warn)    → 속도 50% 감속
RSSI ≥ -80dBm  (Danger)  → Gradient Rendezvous 진입
RSSI < -80dBm  (Lost)    → RSSI 지도 기반 자율 복귀
```

**로컬 미니마 탈출 전략**
```
① Gradient 방향 탐색 → Safe Zone 발견 시 이동
② 로컬 미니마 감지 → Random Perturbation 2회
③ Best-History Fallback → 상위 3셀 평균 좌표 복귀
④ 모든 전략 실패 → home position 복귀
```

**RSSI 지도 갱신**
```
지수 이동 평균: α=0.3 (최신 30% 반영)
격자 해상도: 0.5m
RSSI -100~-60dBm → Costmap 비용 100~0 매핑
```

**완료 조건**
- [ ] WiFi 신호 약화 구역 진입 시 속도 감속 확인
- [ ] RSSI < -80dBm에서 Rendezvous 모드 진입 확인
- [ ] 통신 복구 후 탐색 자동 재개 + 고립 중 감지 생존자 일괄 보고 확인

---

## 7. Phase 5 — GCS + 시각화 (M13~M14)

> **완료 기준**: GCS API로 실시간 조회, Foxglove Studio에서 전체 상황 시각화
> **병렬 구현 가능**: M13 + M14 독립 개발

### M13 — FastAPI GCS API + 커서 기반 페이징

**목표**: 실시간 데이터 추가/삭제 중에도 중복/누락 없는 조회

**구현 파일**
- `ghost5_viz/ghost5_viz/gcs_api.py`
- `ghost5_swarm/ghost5_swarm/paged_query.py`
- `ghost5_swarm/ghost5_swarm/election_guard.py`

**API 엔드포인트**
| 엔드포인트 | 설명 |
|------------|------|
| `GET /events` | 이벤트 로그 (커서 페이징, 타임스탬프 기준) |
| `GET /robots` | 로봇 상태 (커서 페이징, robot_id 기준) |
| `GET /victims` | 생존자 기록 (커서 페이징, confidence 필터) |
| `GET /election/status` | 현재 선거 상태 조회 |

**Election-Aware 응답 헤더**
```
선거 진행 중:
  X-Election-Status: in_progress
  X-Data-Staleness: possible
  X-Retry-After-Ms: 500

정상 상태:
  X-Election-Status: stable
```

**커서 형식**
```
이벤트: "<timestamp_score>:<event_id>"
로봇:   "robot_{id}"
생존자: "<victim_id>"
```

**완료 조건**
- [ ] `GET /events` 커서 순회 시 중복/누락 없음 확인
- [ ] 선거 진행 중 API 응답에 경고 헤더 포함 확인
- [ ] confidence 필터 적용 생존자 조회 확인

---

### M14 — Foxglove Studio 통합 시각화

**목표**: 실시간 멀티 로봇 + 드론 위치 통합 모니터링

**구현 파일**
- `ghost5_viz/ghost5_viz/foxglove_publisher.py`
- `ghost5_viz/ghost5_viz/victim_marker.py`

**시각화 항목**
| 토픽 | Foxglove 패널 |
|------|---------------|
| `/map_merge/global_map` | 2D Map |
| `/map_merge/elevation_global` | 3D Point Cloud |
| `/robot_N/pose` | 로봇 위치 마커 |
| `/swarm/victim` | 생존자 위치 마커 (빨간 원) |
| `/drone/gps_pose` | 드론 위치 마커 (파란 삼각형) |
| `/robot_N/rssi_map` | RSSI Gradient 히트맵 |

**Foxglove Studio 연결**
```bash
# Foxglove Bridge 실행
ros2 launch foxglove_bridge foxglove_bridge_launch.xml

# Studio 연결
ws://leader_robot_ip:8765
```

**완료 조건**
- [ ] Foxglove에서 5대 로봇 위치 실시간 확인
- [ ] 생존자 감지 시 빨간 마커 즉시 표시 확인
- [ ] RSSI Gradient Map 색상 히트맵 표시 확인

---

## 8. Phase 6 — 드론 통합 3-A (M15~M17)

> **완료 기준**: Fake 드론이 순찰하며 생존자 탐지 → 지상 로봇 자동 파견, Fallback 전환 동작

### M15 — Fake Drone 노드

**목표**: PX4 없이 드론 행동 즉시 시뮬, rmw_zenoh 직접 통신

**구현 파일**
- `ghost5_drone_sim/ghost5_drone_sim/fake_drone_node.py`

**퍼블리시 토픽**
| 토픽 | QoS | 주기 |
|------|-----|------|
| `/drone/gps_pose` | BEST_EFFORT | 10Hz |
| `/drone/survivor_pose` | RELIABLE + KEEP_ALL | 이벤트 |
| `/drone/wifi_ap_status` | RELIABLE | 1Hz |
| `/drone/battery_percent` | BEST_EFFORT | 1Hz |
| `/swarm/drone_relay_active` | RELIABLE + KEEP_ALL | 이벤트 |

**순찰 경로 (ENU, 고도 3.0m)**
```python
PATROL_WAYPOINTS = [
    (0.0, 0.0, 3.0),
    (5.0, 0.0, 3.0),
    (5.0, 5.0, 3.0),
    (0.0, 5.0, 3.0),
    (0.0, 0.0, 3.0),  # 홈 복귀
]
DETECTION_DIST = 1.5m  # 생존자 탐지 유효 거리
BATTERY_DRAIN  = 0.05% / sec
```

**완료 조건**
- [ ] `/drone/gps_pose` 10Hz 퍼블리시 확인
- [ ] 생존자 좌표 근방 접근 시 `/drone/survivor_pose` 퍼블리시 확인
- [ ] 배터리 선형 감소 → 0% 도달 시 비활성화 확인

---

### M16 — 드론-Nav2 브릿지 + Gossip 브릿지

**목표**: 드론 생존자 탐지 → 가장 가까운 지상 로봇 자동 파견 + 군집 전파

**구현 파일**
- `ghost5_drone_integration/ghost5_drone_integration/drone_nav_bridge.py`
- `ghost5_drone_integration/ghost5_drone_integration/drone_gossip_bridge.py`

**DroneNavBridge 흐름**
```
/drone/survivor_pose 수신
  → 각 로봇 위치 캐시에서 유클리드 거리 최소 로봇 선택
  → NavigateToPose Action Goal 전송
  → /swarm/victim 군집 알림
```

**DroneGossipBridge 흐름**
```
/drone/survivor_pose 수신
  → event_id 중복 확인 (중복 전파 방지)
  → /swarm/gossip 3회 반복 전파 (신뢰도 향상)
  → /swarm/frontier_priority 우선 탐색 좌표 퍼블리시
```

**완료 조건**
- [ ] 드론 생존자 탐지 후 5초 이내 가장 가까운 로봇 이동 시작
- [ ] `/swarm/gossip` 3회 반복 퍼블리시 확인
- [ ] Redis에 드론 발견 생존자 기록 확인

---

### M17 — 드론 Fallback 모니터 + Zenoh Router 인수

**목표**: 드론 장애 5초 감지 → 지상 독립 운영 자동 전환

**구현 파일**
- `ghost5_drone_integration/ghost5_drone_integration/drone_fallback_monitor.py`

**Fallback 전환 조건**
```
/drone/gps_pose 또는 /drone/wifi_ap_status
  → 5초(DRONE_TIMEOUT_SEC) 이상 미수신
  → /swarm/drone_relay_active = {"active": false} 퍼블리시
  → Bully 리더: Zenoh Router 추가 실행 (드론 대체)
  → 지상 로봇: Zenoh peer 모드 직접 통신 전환
  → FrontierManager: MMPF 자율 탐색 복귀
```

**Fallback 후 복구**
```
드론 토픽 재수신
  → drone_relay_active = true 퍼블리시
  → 드론 협동 모드 자동 복귀
```

**완료 조건**
- [ ] 드론 노드 강제 종료 후 5초 이내 Fallback 전환 확인
- [ ] Fallback 중 지상 5대 탐색 중단 없음 확인
- [ ] 드론 재시작 후 협동 모드 자동 복귀 확인

---

## 9. Phase 7 — PX4 SITL + 최종 검증 (M18~M20)

> **완료 기준**: PX4 X500 드론 + TurtleBot3 5대 통합 시뮬, 모든 벤치마크 지표 달성

### M18 — PX4 SITL + px4_sitl_zenoh + NED→ENU 변환

**목표**: 실제 PX4 드론 통신 연동, Zenoh + uXRCE-DDS 충돌 해결

**구현 파일**
- `ghost5_drone_sim/ghost5_drone_sim/px4_topic_bridge.py`
- `ghost5_bringup/worlds/ghost5_disaster.sdf`

**핵심 이슈: Zenoh + uXRCE-DDS 충돌**
```
문제: PX4 기본값 uXRCE-DDS ↔ rmw_zenoh 포트 충돌
해결: px4_sitl_zenoh 빌드 타겟 사용
      → uXRCE-DDS 비활성화
      → Zenoh 직접 통신 활성화
```

**설치 및 빌드**
```bash
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot
git checkout v1.16.0   # Jazzy + Zenoh 호환
make px4_sitl_zenoh gz_x500
```

**NED → ENU 변환 공식**
```
PX4 NED:  x=North, y=East,  z=Down
ROS2 ENU: x=East,  y=North, z=Up

enu_x =  ned_y
enu_y =  ned_x
enu_z = -ned_z
```

**버전 호환 매트릭스**
| 컴포넌트 | 버전 |
|----------|------|
| Ubuntu | 24.04 LTS |
| ROS2 | Jazzy |
| Gazebo | Harmonic |
| PX4 | v1.16.0+ |
| Python | 3.12+ |

**완료 조건**
- [ ] `make px4_sitl_zenoh gz_x500` 빌드 성공
- [ ] `/drone/gps_pose` ENU 좌표 오차 < 0.1m 확인
- [ ] 드론 이동 중 토픽 손실 < 5% 확인

---

### M19 — Hailo NPU YOLOv8n 오프로딩 (선택 모듈)

**목표**: CPU 부하 ~25% → ~3% 절감, Raspberry Pi 5 처리 여력 확보

**구현 파일**
- `ghost5_victim/ghost5_victim/vision_detector_npu.py`

**성능 목표**
| 항목 | CPU 모드 | NPU 모드 |
|------|----------|----------|
| YOLOv8n 추론 | ~25% CPU | ~3% CPU |
| 처리 속도 | ~10 FPS | ~30 FPS |
| 지연 | ~100ms | ~33ms |

**설치**
```bash
# Hailo AI HAT+ 드라이버
pip install hailort --break-system-packages

# YOLOv8n → HEF 변환 (Hailo Model Zoo)
hailomz compile yolov8n --hw-arch hailo8l
```

**완료 조건** (선택)
- [ ] HEF 파일 변환 성공
- [ ] NPU 추론 CPU 사용률 < 5% 확인
- [ ] CPU 모드 대비 감지 정확도 차이 < 2% 확인

---

### M20 — 5대 군집 통합 벤치마크 + 시나리오 검증

**목표**: 모든 성능 지표 달성, 전체 재난 시나리오 통과

**구현 파일**
- `scripts/benchmark/measure_latency.py`
- `scripts/benchmark/measure_coverage.py`
- `scripts/benchmark/measure_victim_detection.py`

**성능 목표 (합격 기준)**
| 항목 | 목표값 |
|------|--------|
| Pose 통신 지연 | < 50ms (P95) |
| 지도 Delta 전송 | < 500ms (1Hz) |
| Leader Election 수렴 | < 3초 |
| 생존자 알림 전파 | < 200ms |
| 탐색 커버리지 (10분) | > 80% |
| 내결함성 (1대 다운) | 임무 계속 |
| 중복 탐색 비율 | < 5% |
| CPU 부하 (Phase 1) | < 75% |
| CPU 부하 (Phase 2, NPU) | < 65% |

**통합 시나리오 6가지**
```
시나리오 1: Fake 드론 단독 토픽 검증
시나리오 2: 드론 생존자 탐지 → Nav2 파견
시나리오 3: Gossip 전파 + Redis 기록 확인
시나리오 4: 드론 Fallback 전환 + 지상 독립 운영
시나리오 5: PX4 SITL 호버링 + ENU 좌표 정확성
시나리오 6: 전체 통합 재난 시나리오 (ghost5_disaster.sdf)
```

**완료 조건**
- [ ] 6가지 시나리오 전체 통과
- [ ] 성능 목표 9가지 전체 달성
- [ ] 로봇 1대 강제 종료 후 임무 지속 확인
- [ ] 전체 벤치마크 결과 문서화

---

## 10. 진입 조건 체크리스트

각 Phase 진입 전 아래 조건을 모두 만족해야 함.

### Phase 2 진입 조건 (Phase 1 완료 확인)
- [ ] `ros2 topic list`에서 `/swarm/*` 토픽 확인
- [ ] Redis `redis-cli ping` → PONG
- [ ] SROS2 keystore 생성 완료
- [ ] 단위 테스트 전체 통과 (`pytest tests/unit/`)

### Phase 3 진입 조건 (Phase 2 완료 확인)
- [ ] 단일 로봇 SLAM + Nav2 자율주행 성공
- [ ] Elevation Map 퍼블리시 확인
- [ ] SlipAwareEKF 슬립 감지 동작 확인

### Phase 4 진입 조건 (Phase 3 완료 확인)
- [ ] 2대 로봇 Frontier 탐색 중복 없음 확인
- [ ] Leader Election 수렴 < 3초 확인
- [ ] Delta Map Merge 정상 동작 확인

### Phase 5 진입 조건 (Phase 4 완료 확인)
- [ ] 3-센서 생존자 감지 fusion 동작 확인
- [ ] Rendezvous 프로토콜 통신 복귀 확인

### Phase 6 진입 조건 (Phase 5 완료 확인)
- [ ] GCS API 전체 엔드포인트 응답 확인
- [ ] Foxglove 실시간 시각화 확인

### Phase 7 진입 조건 (Phase 6 완료 확인)
- [ ] Fake 드론 6가지 시나리오 1~4 통과
- [ ] DroneNavBridge + GossipBridge 정상 동작
- [ ] Fallback 전환 5초 이내 확인

---

## 11. 개발 세션 로그 규칙

매 개발 세션 종료 시 아래 형식으로 DEV_LOG 작성:

```markdown
# GHOST-5 DEV_LOG — YYYY-MM-DD

## 진행 모듈
- Phase X / M0X — [모듈명]

## 완료 항목
- [ ] 

## 이슈 및 해결
- 

## 다음 세션 TODO
- 

## 브랜치 / 커밋
git branch: feature/M0X-[모듈명]
commit: 
```

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-03-17 | 최초 작성 — GHOST5_plan_v2.md 기반 20개 모듈 / 7개 Phase 분할. 기술별 구현 모듈화, 진입 조건 체크리스트 포함 |

---

*M01부터 순서대로 진행하되, 같은 Phase 내 병렬 구현 가능한 모듈은 동시 진행 권장.*  
*각 모듈 완료 후 단위 테스트 통과 확인 → 다음 Phase 진입 조건 충족 시 진행.*
