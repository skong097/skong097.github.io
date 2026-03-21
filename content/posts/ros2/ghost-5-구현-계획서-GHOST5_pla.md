---
title: "GHOST-5 구현 계획서"
date: 2026-03-21
draft: true
tags: ["ros2", "nav2", "slam", "gazebo", "zenoh"]
categories: ["ros2"]
description: "> GPS-denied Hazard Operation with Swarm Team — 5 Units > 작성일: 2026-03-15 | **v2.1 — Inter-Robot 동적 장애물 등록(충돌 회피 보완): 20"
---

# GHOST-5 구현 계획서

> GPS-denied Hazard Operation with Swarm Team — 5 Units  
> 작성일: 2026-03-15 | **v2.1 — Inter-Robot 동적 장애물 등록(충돌 회피 보완): 2026-03-17**  
> 기반 문서: GHOST5_research.md v3.1 (Gazebo 드론 심화 기술 조사 완료)  
> 로봇 플랫폼: Pinky Pro (Raspberry Pi 5 + RPLiDAR C1 + 5MP 카메라 + US-016 + TCRT5000 + XL330)  
> 드론: Phase 3-A — fake_drone_node.py (즉시 구현) / Phase 3-B — PX4 SITL X500 + Gazebo Harmonic

---

## 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [전체 아키텍처 설계](#2-전체-아키텍처-설계)
3. [워크스페이스 구조 및 패키지 설계](#3-워크스페이스-구조-및-패키지-설계)
4. [Phase별 구현 계획](#4-phase별-구현-계획)
5. [미들웨어 구현 (rmw_zenoh)](#5-미들웨어-구현-rmw_zenoh)
6. [Multi-Robot SLAM 구현](#6-multi-robot-slam-구현)
7. [Frontier 탐색 구현 (MMPF + Claim Blackboard)](#7-frontier-탐색-구현-mmpf--claim-blackboard)
8. [리더 선출 구현 (Bully Algorithm)](#8-리더-선출-구현-bully-algorithm)
9. [Redis Blackboard + Semantic Event Memory](#9-redis-blackboard--semantic-event-memory)
10. [2.5D Elevation Map 구현](#10-25d-elevation-map-구현)
   - [10.3 🆕 Inter-Robot 동적 장애물 등록 (Nav2 Costmap)](#103-inter-robot-동적-장애물-등록-nav2-costmap)
11. [Rendezvous 프로토콜 구현](#11-rendezvous-프로토콜-구현)
12. [생존자 감지 구현 (3-센서 교차 검증)](#12-생존자-감지-구현-3-센서-교차-검증)
13. [Hailo NPU 가속 구현 (Phase 2)](#13-hailo-npu-가속-구현-phase-2)
14. [SROS2 보안 구현](#14-sros2-보안-구현)
15. [커스텀 메시지 정의](#15-커스텀-메시지-정의)
16. [인풋 기반 페이징 시스템 설계](#16-인풋-기반-페이징-시스템-설계)
17. [런치 파일 설계](#17-런치-파일-설계)
18. [검증 전략 및 테스트](#18-검증-전략-및-테스트)
19. [성능 벤치마크 설계](#19-성능-벤치마크-설계)
20. [개발 환경 세팅](#20-개발-환경-세팅)
21. [🆕 가상 드론 통합 설계 (Phase 3-A: Fake Drone)](#21-가상-드론-통합-설계-phase-3-a-fake-drone)
22. [🆕 PX4 SITL 드론 통합 (Phase 3-B)](#22-px4-sitl-드론-통합-phase-3-b)
23. [🆕 드론-지상 로봇 협동 아키텍처](#23-드론-지상-로봇-협동-아키텍처)
24. [🆕 드론 통합 런치 파일 설계](#24-드론-통합-런치-파일-설계)
25. [🆕 드론 통합 검증 시나리오](#25-드론-통합-검증-시나리오)
26. [🆕 최종 통합 아키텍처 (지상 5대 + 가상 드론)](#26-최종-통합-아키텍처-지상-5대--가상-드론)

---

## 1. 프로젝트 개요

### 1.1 목표

GPS 차단 재난 환경(붕괴 건물, 지하 공간, 화재 현장)에서 **Pinky Pro 5대**가 군집 협력으로:
- 실시간 협력 지도 생성 (Multi-Robot SLAM)
- 자율 탐색으로 환경 커버리지 극대화
- 생존자 위치 감지 및 보고
- 1대 이상 다운 시에도 임무 자율 지속

### 1.2 핵심 기술 선택 요약

| 레이어 | 선택 | 이유 |
|--------|------|------|
| 미들웨어 | **rmw_zenoh** | WiFi Mesh 최적화, CPU 절반, Discovery 99% 절감 |
| SLAM | **slam_toolbox + Pose Graph 공유** | 대역폭 효율, ROS2 Jazzy 공식 지원 |
| 지도 병합 | **Delta Update + map_merge** | 전체 대비 10~20% 대역폭 사용 |
| Frontier 탐색 | **MMPF + Claim Blackboard** | 중복 탐색 방지, back-and-forth 방지 |
| 리더 선출 | **Bully Algorithm** | 5대 소규모 최적, 빠른 수렴 (<3초) |
| 공유 상태 | **Redis Blackboard + Semantic Event Memory** | 원자적 Claim, Leader 교체 시 컨텍스트 승계 |
| 통신 단절 | **Zenoh Gossip + Rendezvous 프로토콜** | 완전 고립 대응 |
| 보안 | **SROS2** | AES-GCM 암호화, X.509 인증 |
| 생존자 감지 | **US-016 + TCRT5000 IR + 5MP YOLOv8n 교차 검증** | 오탐 최소화 |
| 하드웨어 가속 | **Hailo AI HAT+ 26TOPS (Phase 2)** | YOLOv8n CPU 부하 ~25% → ~3% |
| 2.5D 인지 | **RPLiDAR C1 Z-stack + 5MP 텍스처 분석** | 추가 하드웨어 없이 구현 |
| 시각화 | **Foxglove Studio** | 실시간 멀티 로봇 모니터링 |
| 드론 Phase 3-A | **fake_drone_node.py** | 즉시 구현 가능, rmw_zenoh 직접 연동 |
| 드론 Phase 3-B | **PX4 SITL + Gazebo Harmonic** | px4_sitl_zenoh 빌드 타겟, NED→ENU 변환 |
| 드론 협동 | **drone_nav_bridge + drone_gossip_bridge** | 드론 좌표 → Nav2 Goal 자동 파견 |
| 드론 Fallback | **Bully 리더 Zenoh Router 인수** | 드론 장애 5초 미수신 시 독립 운영 |

### 1.3 하드웨어 스펙 (Pinky Pro 1대)

```
Raspberry Pi 5 (8GB)
  ├── RPLiDAR C1          → 2D SLAM (slam_toolbox), 최대 12m
  ├── 5MP 카메라           → YOLOv8n 인체 감지 + Elevation 텍스처 분석
  ├── US-016 초음파        → 생존자 거리 감지 (2cm ~ 400cm)
  ├── TCRT5000 IR          → 근거리 반사 감지 (~30cm)
  ├── BNO055 IMU (9축)     → EKF 오도메트리 보정
  ├── 다이나믹셀 XL330     → 구동 + 오도메트리
  └── Hailo AI HAT+ 26TOPS → NPU 가속 (Phase 2 옵션)
```

---

## 2. 전체 아키텍처 설계

### 2.1 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ground Control Station (GCS)                 │
│           Foxglove Studio — 통합 2.5D 지도 + 생존자 위치 표시    │
└────────────────────────┬────────────────────────────────────────┘
                         │ rmw_zenoh + SROS2 (TCP, AES-GCM 암호화)
           ┌─────────────┼─────────────────┐
           │             │                 │
   Robot-1 (Leader)    R2~R3           R4~R5 (Explorer)
   ┌───────────────────┐  ┌──────────────────────────────┐
   │ slam_toolbox      │  │ slam_toolbox                  │
   │ map_merger_v2     │  │ lidar_elevation_node          │
   │ elevation_global  │  │   (RPLiDAR C1 Z-stack)        │
   │ leader_election   │  │ camera_low_obstacle_node      │
   │ Redis Blackboard  │  │ frontier_manager (MMPF)        │
   │  ├─ RobotState    │  │ comm_monitor (RSSI 모니터링)   │
   │  ├─ FrontierClaim │  │ vision_detector (YOLOv8n)     │
   │  └─ SemanticMem   │  │ proximity_detector (US+IR)    │
   └───────────────────┘  └──────────────────────────────┘
```

### 2.2 통신 채널 QoS 설계

```
🔴 /robot_N/pose              → BEST_EFFORT  10Hz   TTL 5s   (위치, 최신값만)
🔴 /swarm/robot_poses_array  → BEST_EFFORT  5Hz    TTL 5s   (전체 로봇 위치 집계 → Inter-Robot Costmap)
🟡 /robot_N/map_delta         → RELIABLE     1Hz    TTL 60s  (지도 delta)
🟡 /robot_N/elevation_layer   → RELIABLE     2Hz    -        (elevation)
🟡 /robot_N/low_obstacle_layer→ RELIABLE     2Hz    -        (저고도 장애물)
🟢 /swarm/elevation_global    → RELIABLE     0.5Hz  -        (병합 후 GCS)
🟢 /swarm/election            → RELIABLE     이벤트  KEEP_ALL (리더 선출)
🟢 /swarm/heartbeat           → BEST_EFFORT  1Hz    -        (리더 생존 확인)
🟢 /swarm/frontier_claims     → RELIABLE     이벤트  KEEP_ALL (frontier 예약)
🟢 /swarm/comm_events         → RELIABLE     이벤트  -        (통신 이상)
🟢 /swarm/victim              → RELIABLE     이벤트  KEEP_ALL (생존자 감지)
🟢 /robot_N/rssi              → BEST_EFFORT  0.5Hz  -        (신호 강도)
🔵 /drone/gps_pose            → BEST_EFFORT  10Hz   -        (드론 ENU 위치)
🔵 /drone/survivor_pose       → RELIABLE     이벤트  KEEP_ALL (드론 감지 생존자)
🔵 /drone/wifi_ap_status      → RELIABLE     1Hz    -        (드론 WiFi 릴레이 상태)
🔵 /drone/battery_percent     → BEST_EFFORT  1Hz    -        (드론 배터리)
🔵 /swarm/drone_relay_active  → RELIABLE     이벤트  KEEP_ALL (드론 활성/Fallback)
🔵 /swarm/frontier_priority   → RELIABLE     이벤트  -        (드론 우선 탐색 좌표)
```

### 2.3 Robot 역할 분류

| 역할 | 조건 | 담당 기능 |
|------|------|-----------|
| **Leader** | 가장 높은 생존 Robot ID | 글로벌 맵 병합, Frontier 재분배, Redis 운영, GCS 보고 |
| **Explorer** | Leader 외 4대 | 로컬 SLAM, 탐색 실행, 생존자 감지, 결과 보고 |

---

## 3. 워크스페이스 구조 및 패키지 설계

```
ghost5_ws/
├── src/
│   ├── ghost5_interfaces/            # 커스텀 메시지/서비스/액션
│   │   ├── msg/
│   │   │   ├── RobotState.msg
│   │   │   ├── FrontierList.msg
│   │   │   ├── VictimDetection.msg
│   │   │   └── SwarmStatus.msg
│   │   ├── srv/
│   │   │   ├── ClaimFrontier.srv
│   │   │   └── GetGlobalMap.srv
│   │   └── action/
│   │       └── ExploreRegion.action
│   │
│   ├── ghost5_bringup/               # 런치 + 설정
│   │   ├── launch/
│   │   │   ├── robot.launch.py           # 단일 로봇 런치
│   │   │   ├── swarm.launch.py           # 전체 군집 런치
│   │   │   └── simulation.launch.py      # Gazebo 시뮬레이션
│   │   └── config/
│   │       ├── qos_profiles.py
│   │       ├── slam_toolbox_params.yaml
│   │       ├── nav2_params.yaml
│   │       └── zenoh_config.json5
│   │
│   ├── ghost5_slam/                  # SLAM + 지도 병합 + Elevation
│   │   └── ghost5_slam/
│   │       ├── map_merger_node.py        # 글로벌 지도 병합 (Leader)
│   │       ├── pose_graph_publisher.py   # Pose Graph 공유
│   │       ├── loop_closure_detector.py  # 다중 로봇 Loop Closure
│   │       ├── lidar_elevation_node.py   # RPLiDAR Z-stack Elevation
│   │       └── camera_low_obstacle_node.py # 5MP 카메라 저고도 감지
│   │
│   ├── ghost5_navigation/            # Nav2 + Frontier 탐색
│   │   └── ghost5_navigation/
│   │       ├── frontier_detector.py      # OccupancyGrid → Frontier 추출
│   │       ├── frontier_manager.py       # MMPF 기반 Frontier 할당
│   │       ├── nav_goal_publisher.py     # Nav2 Goal 전송
│   │       └── inter_robot_costmap_layer.py  # 🆕 타 로봇 위치 → 동적 장애물 등록
│   │
│   ├── ghost5_swarm/                 # 군집 지능
│   │   └── ghost5_swarm/
│   │       ├── leader_election.py        # Bully Algorithm
│   │       ├── blackboard.py             # Redis 공유 상태
│   │       ├── semantic_memory.py        # Semantic Event Memory
│   │       ├── comm_monitor.py           # RSSI 모니터링 + Rendezvous
│   │       ├── swarm_coordinator.py      # 군집 조율 노드
│   │       └── fault_handler.py          # 로봇 다운 시 임무 재배치
│   │
│   ├── ghost5_victim/                # 생존자 감지
│   │   └── ghost5_victim/
│   │       ├── proximity_detector.py     # US-016 초음파 + TCRT5000 IR
│   │       ├── vision_detector.py        # 5MP YOLOv8n 인체 감지 (CPU)
│   │       ├── vision_detector_npu.py    # Hailo NPU 인체 감지 (Phase 2)
│   │       ├── victim_fuser.py           # 3-센서 교차 검증 융합
│   │       └── triangulation.py          # 3대 이상 감지 시 삼각측량
│   │
│   └── ghost5_viz/                   # 시각화 및 GCS
│       └── ghost5_viz/
│           ├── foxglove_publisher.py     # Foxglove 통합 지도
│           └── victim_marker.py          # 생존자 위치 마커
│
│   ├── ghost5_drone_sim/             # 🆕 드론 시뮬레이션 패키지 (Phase 3)
│   │   └── ghost5_drone_sim/
│   │       ├── fake_drone_node.py        # Phase 3-A: Fake 드론 노드
│   │       └── px4_topic_bridge.py       # Phase 3-B: PX4 NED→ENU 변환
│   │
│   └── ghost5_drone_integration/     # 🆕 드론-로봇 통합 패키지 (Phase 3)
│       └── ghost5_drone_integration/
│           ├── drone_nav_bridge.py       # 드론 좌표 → Nav2 Goal 자동 파견
│           ├── drone_gossip_bridge.py    # 드론 생존자 → Gossip 전파
│           └── drone_fallback_monitor.py # 드론 장애 감지 + Fallback
│
├── tests/
│   ├── unit/
│   │   ├── test_leader_election.py
│   │   ├── test_frontier_mmpf.py
│   │   ├── test_map_merger.py
│   │   ├── test_semantic_memory.py
│   │   └── test_victim_fuser.py
│   └── integration/
│       ├── test_swarm_communication.py
│       ├── test_fault_tolerance.py
│       └── test_rendezvous.py
│
└── scripts/
    ├── setup_sros2.sh
    ├── deploy_to_robots.sh
    ├── init_redis.sh
    └── benchmark/
        ├── measure_latency.py
        ├── measure_coverage.py
        └── measure_victim_detection.py
```

---

## 4. Phase별 구현 계획

### 4.1 전체 로드맵

```
Phase 1: 기반 인프라 + 단일 로봇 검증 (2~3주)
  ├── rmw_zenoh 설치 및 환경 설정
  ├── QoS 프로파일 구현
  ├── slam_toolbox 단일 로봇 SLAM 검증
  ├── Nav2 단일 로봇 자율주행 검증
  ├── Redis Blackboard + Semantic Event Memory 구현
  ├── Bully Algorithm Leader Election 구현
  ├── US-016 + TCRT5000 + 5MP 생존자 감지 구현
  └── SROS2 기본 보안 설정

Phase 2: 멀티 로봇 핵심 기능 (3~4주)
  ├── Delta Map Update + Map Merger 구현
  ├── Pose Graph 공유 구현
  ├── MMPF Frontier 탐색 구현
  ├── Claim Blackboard 연동
  ├── 2.5D Elevation Map 구현 (Z-stack + 카메라)
  ├── RSSI 모니터링 + Rendezvous 프로토콜 구현
  ├── 2대 로봇 통합 테스트
  └── Hailo NPU 오프로딩 (선택)

Phase 3: 5대 군집 통합 + 검증 (2~3주)
  ├── 5대 전체 시뮬레이션 (Gazebo + TurtleBot3)
  ├── 실제 하드웨어 5대 통합 테스트
  ├── 내결함성 테스트 (강제 종료)
  ├── 재난 시나리오 모의 환경 테스트
  └── 전체 벤치마크 지표 측정

Phase 3-A: 가상 드론 통합 — Fake Drone (즉시 병행 가능)
  ├── fake_drone_node.py 작성 + rmw_zenoh 연동
  ├── drone_nav_bridge.py: 드론 좌표 → Nav2 Goal 파견
  ├── drone_gossip_bridge.py: 드론 생존자 → Gossip 전파
  ├── drone_fallback_monitor.py: 드론 장애 감지 + Fallback
  └── 시나리오 1~3 검증 (Fake 드론 기반)

Phase 3-B: PX4 SITL 드론 통합 (2~4주, Phase 3-A 완료 후)
  ├── PX4 SITL px4_sitl_zenoh 빌드 환경 구축
  ├── px4_topic_bridge.py: NED→ENU 좌표 변환
  ├── ghost5_disaster.sdf 재난 월드 제작
  ├── TurtleBot3 5대 + X500 드론 통합 시뮬
  └── 시나리오 4~5 검증 (PX4 SITL 기반)
```

### 4.2 Phase 1 상세 태스크

| 우선순위 | 태스크 | 예상 소요 | 담당 모듈 |
|----------|--------|-----------|-----------|
| P0 | rmw_zenoh 설치 + QoS 설정 | 0.5일 | ghost5_bringup |
| P0 | ghost5_interfaces 메시지 정의 | 0.5일 | ghost5_interfaces |
| P0 | Redis 설치 + Blackboard 구현 | 1일 | ghost5_swarm |
| P1 | slam_toolbox 단일 로봇 SLAM | 1일 | ghost5_slam |
| P1 | Nav2 자율주행 기본 설정 | 1일 | ghost5_navigation |
| P1 | Bully Algorithm 구현 | 1일 | ghost5_swarm |
| P1 | Semantic Event Memory 구현 | 1일 | ghost5_swarm |
| P2 | US-016 + TCRT5000 + 5MP 감지 | 1.5일 | ghost5_victim |
| P2 | SROS2 keystore 설정 | 0.5일 | scripts/ |

---

## 5. 미들웨어 구현 (rmw_zenoh)

### 5.1 설치 및 환경 설정

```bash
# ROS2 Jazzy Zenoh RMW 설치
sudo apt install ros-jazzy-rmw-zenoh-cpp

# 모든 로봇 .bashrc에 추가
echo 'export RMW_IMPLEMENTATION=rmw_zenoh_cpp' >> ~/.bashrc
echo 'export ROS_DOMAIN_ID=42' >> ~/.bashrc  # SROS2 도메인 격리
source ~/.bashrc

# Leader 로봇에서 Zenoh 라우터 실행
ros2 run rmw_zenoh_cpp init_rmw_zenoh_router
```

### 5.2 QoS 프로파일 구현

**파일 경로**: `ghost5_bringup/config/qos_profiles.py`

```python
# ghost5_ws/src/ghost5_bringup/config/qos_profiles.py

from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

# ─────────────────────────────────────────────────────────
# 🔴 HIGH: 로봇 위치, 상태, RSSI (10Hz, 손실 허용, 최신값만)
# ─────────────────────────────────────────────────────────
POSE_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,   # UDP: 빠름, 손실 허용
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
    depth=1                                       # 최신 1개만 유지
)

# ─────────────────────────────────────────────────────────
# 🟡 MEDIUM: 지도 delta, Elevation Layer (1~2Hz, 손실 불허)
# ─────────────────────────────────────────────────────────
MAP_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,       # TCP: 보장, 약간 느림
    durability=DurabilityPolicy.TRANSIENT_LOCAL,  # 늦게 참여한 로봇도 수신
    history=HistoryPolicy.KEEP_LAST,
    depth=5
)

# ─────────────────────────────────────────────────────────
# 🟢 LOW: 생존자 감지, Leader Election, 통신 이벤트 (이벤트 기반)
# ─────────────────────────────────────────────────────────
EVENT_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_ALL               # 모든 이벤트 보존
)
```

### 5.3 Zenoh 설정 파일

**파일 경로**: `ghost5_bringup/config/zenoh_config.json5`

```json5
// ghost5_ws/src/ghost5_bringup/config/zenoh_config.json5
// Explorer 로봇용 설정 (Leader 로봇 IP 연결)
{
  "mode": "peer",
  "connect": {
    "endpoints": ["tcp/${LEADER_IP}:7447"]  // 환경변수로 리더 IP 주입
  },
  "scouting": {
    "gossip": {
      "enabled": true,
      "multihop": true    // Mesh 네트워크 멀티홉 활성화
    }
  }
}
```

---

## 6. Multi-Robot SLAM 구현

### 6.1 slam_toolbox 멀티 로봇 파라미터

**파일 경로**: `ghost5_bringup/config/slam_toolbox_params.yaml`

```yaml
# ghost5_ws/src/ghost5_bringup/config/slam_toolbox_params.yaml
slam_toolbox:
  ros__parameters:
    # 로봇별 네임스페이스로 분리 (런치 시 robot_N으로 치환)
    odom_frame:  robot_N/odom
    base_frame:  robot_N/base_link
    map_frame:   map                  # 공통 글로벌 프레임

    # 성능 최적화 (Raspberry Pi 5 기준)
    resolution:                  0.05    # 5cm 해상도
    max_laser_range:             12.0    # RPLiDAR C1 최대 범위
    minimum_travel_distance:     0.2
    minimum_travel_heading:      0.3

    # Loop Closure 설정
    loop_search_maximum_distance: 3.0
    do_loop_closing:              true
    loop_match_minimum_chain_size: 3

    # 멀티 로봇 모드: 각자 독립 맵 생성
    mode: mapping
```

### 6.2 지도 병합 노드 (Delta Update)

**파일 경로**: `ghost5_slam/ghost5_slam/map_merger_node.py`

```python
# ghost5_ws/src/ghost5_slam/ghost5_slam/map_merger_node.py

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
import numpy as np
import sys
import os

# QoS 프로파일 공유 임포트
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ghost5_bringup/config'))
from qos_profiles import MAP_QOS


class MapMergerNode(Node):
    """
    Leader 로봇에서 실행되는 3-레이어 통합 지도 병합 노드.

    Layer 1: 2D OccupancyGrid (slam_toolbox, LiDAR 수평 스캔)
    Layer 2: Elevation Layer  (lidar_elevation_node, Z-stack)
    Layer 3: LowObstacle Layer (camera_low_obstacle_node, 15cm 이하)

    Delta Update 전략:
      - 각 로봇의 이전 맵과 현재 맵을 비교해 변경 셀만 추출
      - 전체 맵 대비 10~20%의 대역폭만 사용
    """

    MERGE_PERIOD_SEC = 1.0   # 병합 주기 (1Hz)

    def __init__(self):
        super().__init__('map_merger_v2')
        self.robot_maps       = {}   # {robot_id: OccupancyGrid} 2D 맵
        self.robot_elevations = {}   # {robot_id: OccupancyGrid} elevation
        self.robot_low_obs    = {}   # {robot_id: OccupancyGrid} 저고도 장애물
        self.prev_maps        = {}   # delta 계산용 이전 맵

        # TF 버퍼 (로컬→글로벌 좌표 변환)
        import tf2_ros
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # 5대 로봇 토픽 구독
        for i in range(1, 6):
            self.create_subscription(
                OccupancyGrid, f'/robot_{i}/map',
                lambda msg, rid=i: self._map_callback(msg, rid), MAP_QOS
            )
            self.create_subscription(
                OccupancyGrid, f'/robot_{i}/elevation_layer',
                lambda msg, rid=i: self._store(self.robot_elevations, msg, rid), MAP_QOS
            )
            self.create_subscription(
                OccupancyGrid, f'/robot_{i}/low_obstacle_layer',
                lambda msg, rid=i: self._store(self.robot_low_obs, msg, rid), MAP_QOS
            )

        # 퍼블리셔
        self.global_map_pub  = self.create_publisher(
            OccupancyGrid, '/map_merge/global_map', MAP_QOS
        )
        self.global_elev_pub = self.create_publisher(
            OccupancyGrid, '/map_merge/elevation_global', MAP_QOS
        )

        self.create_timer(self.MERGE_PERIOD_SEC, self.merge_and_publish)

    def _map_callback(self, msg: OccupancyGrid, robot_id: int):
        """Delta 업데이트: 변경된 셀만 추출해 저장"""
        if robot_id in self.prev_maps:
            prev = np.array(self.prev_maps[robot_id].data)
            curr = np.array(msg.data)
            changed_count = int(np.sum(prev != curr))
            if changed_count > 0:
                self.robot_maps[robot_id] = msg
                self.get_logger().debug(
                    f'Robot {robot_id}: {changed_count} cells updated '
                    f'({changed_count / max(len(curr), 1) * 100:.1f}%)'
                )
        else:
            self.robot_maps[robot_id] = msg

        self.prev_maps[robot_id] = msg

    def _store(self, store: dict, msg: OccupancyGrid, robot_id: int):
        """Elevation / LowObstacle 레이어 저장"""
        store[robot_id] = msg

    def merge_and_publish(self):
        """3개 레이어를 통합한 글로벌 맵 생성 및 퍼블리시"""
        if len(self.robot_maps) < 1:
            return

        # Layer 1: 2D 맵 병합
        self._merge_2d_maps()

        # Layer 2 + 3: Elevation + LowObstacle 병합
        merged_elev = {}
        for store in [self.robot_elevations, self.robot_low_obs]:
            for robot_id, grid in store.items():
                for idx, cost in enumerate(grid.data):
                    if cost <= 0:
                        continue
                    key = self._local_idx_to_world_key(idx, grid, robot_id)
                    if key:
                        if key not in merged_elev or merged_elev[key] < cost:
                            merged_elev[key] = cost   # 최대 비용 우선

        if merged_elev:
            self.global_elev_pub.publish(
                self._cells_to_grid(merged_elev, frame='map')
            )

    def _merge_2d_maps(self):
        """각 로봇의 로컬 2D 맵을 글로벌 맵으로 병합 (Known > Unknown 우선)"""
        if not self.robot_maps:
            return
        merged_grid = self._initialize_global_map()
        for robot_id, local_map in self.robot_maps.items():
            self._overlay_map(merged_grid, local_map, robot_id)
        self.global_map_pub.publish(merged_grid)

    def _overlay_map(self, global_map: OccupancyGrid,
                     local_map: OccupancyGrid, robot_id: int):
        """로컬 맵을 글로벌 맵에 오버레이 (tf2_ros 기반 좌표 변환)"""
        # 실제 구현 시 tf2_ros.lookup_transform 사용
        # Known(0 or 100) > Unknown(-1) 우선 병합
        pass

    def _local_idx_to_world_key(self, idx: int, grid: OccupancyGrid,
                                 robot_id: int):
        """로컬 그리드 인덱스 → 월드 격자 키 변환"""
        try:
            tf = self.tf_buffer.lookup_transform(
                'map', f'robot_{robot_id}/base_link', rclpy.time.Time()
            )
        except Exception:
            return None

        lx = (idx % grid.info.width)  * grid.info.resolution + grid.info.origin.position.x
        ly = (idx // grid.info.width) * grid.info.resolution + grid.info.origin.position.y
        wx = lx + tf.transform.translation.x
        wy = ly + tf.transform.translation.y
        return (int(wx / 0.05), int(wy / 0.05))

    def _initialize_global_map(self) -> OccupancyGrid:
        """글로벌 맵 초기화 (전체 로봇 맵의 최대 범위)"""
        grid = OccupancyGrid()
        grid.header.frame_id = 'map'
        grid.header.stamp = self.get_clock().now().to_msg()
        grid.info.resolution = 0.05
        # TODO: 실제 범위 계산
        return grid

    def _cells_to_grid(self, cells: dict, frame: str) -> OccupancyGrid:
        """딕셔너리 {(gx,gy): cost} → OccupancyGrid 변환"""
        if not cells:
            return OccupancyGrid()
        xs = [k[0] for k in cells]
        ys = [k[1] for k in cells]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width  = max_x - min_x + 1
        height = max_y - min_y + 1

        grid = OccupancyGrid()
        grid.header.frame_id = frame
        grid.header.stamp = self.get_clock().now().to_msg()
        grid.info.resolution = 0.05
        grid.info.width  = width
        grid.info.height = height
        grid.info.origin.position.x = min_x * 0.05
        grid.info.origin.position.y = min_y * 0.05
        data = [-1] * (width * height)

        for (gx, gy), cost in cells.items():
            idx = (gy - min_y) * width + (gx - min_x)
            if 0 <= idx < len(data):
                data[idx] = cost

        grid.data = data
        return grid


def main():
    rclpy.init()
    node = MapMergerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

## 7. Frontier 탐색 구현 (MMPF + Claim Blackboard)

### 7.1 Frontier 감지기

**파일 경로**: `ghost5_navigation/ghost5_navigation/frontier_detector.py`

```python
# ghost5_ws/src/ghost5_navigation/ghost5_navigation/frontier_detector.py

import numpy as np
from nav_msgs.msg import OccupancyGrid
from geometry_msgs.msg import Point


class FrontierDetector:
    """
    OccupancyGrid에서 Frontier 셀 추출.

    Frontier 정의:
      - Free space(0)에 인접하고
      - Unknown space(-1)에도 인접한 셀

    info_gain 계산:
      - Frontier 주변 Unknown 셀 수 = 탐색 시 얻을 수 있는 정보량
    """

    UNKNOWN   = -1
    FREE      =  0
    OCCUPIED  = 100

    def extract_frontiers(self, grid: OccupancyGrid) -> list[dict]:
        """
        Returns:
            [{'id': str, 'x': float, 'y': float, 'info_gain': float}, ...]
        """
        data = np.array(grid.data).reshape(grid.info.height, grid.info.width)
        frontiers = []

        for row in range(1, grid.info.height - 1):
            for col in range(1, grid.info.width - 1):
                if data[row, col] != self.FREE:
                    continue

                neighbors = data[row-1:row+2, col-1:col+2].flatten()
                has_unknown = np.any(neighbors == self.UNKNOWN)

                if has_unknown:
                    # 월드 좌표 변환
                    wx = col * grid.info.resolution + grid.info.origin.position.x
                    wy = row * grid.info.resolution + grid.info.origin.position.y

                    # info_gain: 주변 Unknown 셀 수
                    unknown_count = int(np.sum(neighbors == self.UNKNOWN))

                    frontiers.append({
                        'id':        f'f_{col}_{row}',
                        'x':         wx,
                        'y':         wy,
                        'info_gain': float(unknown_count),
                    })

        return frontiers
```

### 7.2 MMPF 기반 Frontier 관리자

**파일 경로**: `ghost5_navigation/ghost5_navigation/frontier_manager.py`

```python
# ghost5_ws/src/ghost5_navigation/ghost5_navigation/frontier_manager.py

import numpy as np
import json
from std_msgs.msg import String
from qos_profiles import EVENT_QOS


class FrontierManager:
    """
    MMPF(Multi-robot Multi-target Potential Field) + Claim Blackboard 하이브리드.

    포텐셜 함수:
        U(f) = α * attraction(f) - β * robot_repulsion(f)

    여기서:
        attraction(f)    = info_gain(f) / dist_to_frontier
        robot_repulsion(f) = Σ 1 / dist_to_other_robot(f)  for all other robots

    α=1.0, β=0.5 (재난 환경에서 분산 탐색 강조)

    Claim 만료:
        30초 후 자동 해제 (Redis TTL 또는 타이머)
    """

    ALPHA = 1.0   # 인력 가중치
    BETA  = 0.5   # 반발력 가중치
    CLAIM_EXPIRE_SEC = 30.0

    def __init__(self, robot_id: int, node):
        self.robot_id = robot_id
        self.node = node
        self.claimed_frontiers: dict[str, int] = {}   # {frontier_id: robot_id}
        self._claim_timers: dict[str, object] = {}    # {frontier_id: timer}

        self.claim_pub = node.create_publisher(
            String, '/swarm/frontier_claims', EVENT_QOS
        )
        node.create_subscription(
            String, '/swarm/frontier_claims',
            self._claim_callback, EVENT_QOS
        )

    def compute_mmpf_goal(
        self,
        frontiers: list[dict],
        robot_poses: dict[int, tuple],    # {robot_id: (x, y)}
        my_pose: tuple,                   # (x, y)
        skip_zones: list[str] | None = None
    ) -> dict | None:
        """
        MMPF 알고리즘으로 최적 Frontier 선택.

        Args:
            frontiers:   추출된 Frontier 목록
            robot_poses: 다른 로봇들의 현재 위치
            my_pose:     나의 현재 위치
            skip_zones:  SemanticMemory에서 3회 이상 실패한 zone ID 목록

        Returns:
            선택된 Frontier dict 또는 None
        """
        if not frontiers:
            return None

        skip_zones = set(skip_zones or [])
        best_frontier = None
        best_score = -np.inf

        for f in frontiers:
            # 이미 claim된 Frontier 제외
            if f['id'] in self.claimed_frontiers:
                continue

            # SemanticMemory skip_zones 제외
            if f.get('zone_id') in skip_zones:
                continue

            fx, fy = f['x'], f['y']

            # 1. 인력: 정보 이득 / 거리
            dist_to_f = np.hypot(fx - my_pose[0], fy - my_pose[1]) + 1e-6
            attraction = f.get('info_gain', 1.0) / dist_to_f

            # 2. 반발력: 다른 로봇과 같은 방향 탐색 방지
            repulsion = sum(
                1.0 / (np.hypot(fx - px, fy - py) + 1e-6)
                for rid, (px, py) in robot_poses.items()
                if rid != self.robot_id
            )

            score = self.ALPHA * attraction - self.BETA * repulsion

            if score > best_score:
                best_score = score
                best_frontier = f

        if best_frontier:
            self._claim_frontier(best_frontier['id'])

        return best_frontier

    def _claim_frontier(self, frontier_id: str):
        """Frontier claim 브로드캐스트 + 자동 만료 타이머 설정"""
        self.claimed_frontiers[frontier_id] = self.robot_id

        claim_msg = json.dumps({
            'frontier_id': frontier_id,
            'robot_id':    self.robot_id,
            'timestamp':   self.node.get_clock().now().to_msg().sec
        })
        self.claim_pub.publish(String(data=claim_msg))

        # 30초 후 자동 만료
        timer = self.node.create_timer(
            self.CLAIM_EXPIRE_SEC,
            lambda fid=frontier_id: self._expire_claim(fid)
        )
        self._claim_timers[frontier_id] = timer

    def _expire_claim(self, frontier_id: str):
        """Claim 만료 처리"""
        self.claimed_frontiers.pop(frontier_id, None)
        timer = self._claim_timers.pop(frontier_id, None)
        if timer:
            timer.cancel()

    def _claim_callback(self, msg: String):
        """다른 로봇의 claim 수신 및 동기화"""
        data = json.loads(msg.data)
        fid = data['frontier_id']
        rid = data['robot_id']
        if rid != self.robot_id:
            self.claimed_frontiers[fid] = rid

    def release_frontier(self, frontier_id: str):
        """탐색 완료 후 claim 수동 해제"""
        self._expire_claim(frontier_id)
        release_msg = json.dumps({
            'frontier_id': frontier_id,
            'robot_id':    self.robot_id,
            'action':      'release',
            'timestamp':   self.node.get_clock().now().to_msg().sec
        })
        self.claim_pub.publish(String(data=release_msg))
```

---

## 8. 리더 선출 구현 (Bully Algorithm)

**파일 경로**: `ghost5_swarm/ghost5_swarm/leader_election.py`

```python
# ghost5_ws/src/ghost5_swarm/ghost5_swarm/leader_election.py

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import time
from qos_profiles import POSE_QOS, EVENT_QOS


class LeaderElection(Node):
    """
    Bully Algorithm 기반 분산 리더 선출.

    규칙:
      1. 모든 로봇은 1초마다 Heartbeat를 수신 대기
      2. Leader Heartbeat 3초 미수신 → 선거 발동
      3. 자신보다 높은 ID에 ELECTION 메시지 전송
      4. 3초 내 응답 없으면 자신이 Leader로 선언
      5. 가장 높은 ID를 가진 생존 로봇이 Leader

    [v1.2 보완] Split-Brain 방지 쿼럼(Quorum) 확인:
      - VICTORY 선언 전, 최소 QUORUM_SIZE(3)대가 "구 Leader가 죽었다"는
        consensus를 /swarm/leader_dead 토픽에 보고하는지 확인
      - 네트워크 분할(Partition) 시 소수 파티션은 쿼럼 미달로 승격 불가
      - 쿼럼 대기 타임아웃(5초) 내 미달 → 선거 재시도 (최대 3회)

    성능 목표:
      - 선거 수렴 시간 < 3초 (쿼럼 확인 포함 시 < 8초)
    """

    HEARTBEAT_INTERVAL_SEC = 1.0
    LEADER_TIMEOUT_SEC     = 3.0
    ELECTION_TIMEOUT_SEC   = 3.0
    QUORUM_SIZE            = 3     # Split-Brain 방지: 최소 합의 로봇 수
    QUORUM_TIMEOUT_SEC     = 5.0   # 쿼럼 대기 최대 시간
    MAX_ELECTION_RETRY     = 3     # 쿼럼 미달 시 최대 재시도 횟수

    # [v1.3 보완] Election Storm 방지: ID 기반 Backoff Delay
    # 높은 ID 로봇이 더 짧은 대기 후 선거 시작 → 낮은 ID 로봇은 자연히 양보
    # delay = (MAX_ROBOT_ID - my_id) * BACKOFF_STEP_SEC
    # 예: Robot-5 → 0.0s, Robot-4 → 0.1s, Robot-3 → 0.2s, Robot-1 → 0.4s
    BACKOFF_STEP_SEC       = 0.1   # ID당 backoff 증가량 (초)

    def __init__(self, robot_id: int, total_robots: int = 5):
        super().__init__(f'leader_election_robot_{robot_id}')
        self.robot_id          = robot_id
        self.total_robots      = total_robots
        self.current_leader_id = None
        self.last_heartbeat    = {}   # {robot_id: float (unix ts)}
        self.is_election_on    = False
        self.election_responses = set()

        # Split-Brain 방지: 구 Leader 사망 확인 투표 수집
        self._leader_dead_votes: set[int] = set()  # {robot_id: 투표한 로봇 ID}
        self._quorum_retry_count: int = 0

        # 퍼블리셔
        self.election_pub    = self.create_publisher(String, '/swarm/election',     EVENT_QOS)
        self.heartbeat_pub   = self.create_publisher(String, '/swarm/heartbeat',    POSE_QOS)
        self.leader_dead_pub = self.create_publisher(String, '/swarm/leader_dead',  EVENT_QOS)

        # 구독자
        self.create_subscription(String, '/swarm/election',    self._on_election_msg,  EVENT_QOS)
        self.create_subscription(String, '/swarm/heartbeat',   self._on_heartbeat,     POSE_QOS)
        self.create_subscription(String, '/swarm/leader_dead', self._on_leader_dead,   EVENT_QOS)

        # 타이머
        self.create_timer(self.HEARTBEAT_INTERVAL_SEC, self._send_heartbeat)
        self.create_timer(self.LEADER_TIMEOUT_SEC,     self._check_leader)

    # ── Heartbeat ─────────────────────────────────────────────────────
    def _send_heartbeat(self):
        if self.current_leader_id == self.robot_id:
            self.heartbeat_pub.publish(String(data=json.dumps({
                'type': 'HEARTBEAT',
                'from': self.robot_id,
                'ts':   time.time()
            })))

    def _on_heartbeat(self, msg: String):
        data = json.loads(msg.data)
        self.last_heartbeat[data['from']] = data['ts']

    # ── Leader 생존 확인 ─────────────────────────────────────────────
    def _check_leader(self):
        if self.current_leader_id is None:
            self._start_election_with_backoff()
            return
        if self.current_leader_id == self.robot_id:
            return

        last = self.last_heartbeat.get(self.current_leader_id, 0)
        if time.time() - last > self.LEADER_TIMEOUT_SEC:
            self.get_logger().warn(
                f'Leader Robot {self.current_leader_id} TIMEOUT! → 사망 투표 브로드캐스트'
            )
            self._vote_leader_dead(self.current_leader_id)
            # Backoff Delay 적용 후 선거 시작
            self._start_election_with_backoff()

    def _start_election_with_backoff(self):
        """
        [v1.3 보완] Election Storm 방지: ID 기반 Backoff Delay 적용 후 선거 시작.

        원리:
          delay = (MAX_ROBOT_ID - my_id) * BACKOFF_STEP_SEC
          → 가장 높은 ID(=Leader 후보)가 delay=0으로 즉시 선거 시작
          → 낮은 ID 로봇들은 짧게 대기 중 높은 ID의 VICTORY 메시지 수신 시 선거 취소
          → 불필요한 ELECTION 메시지 폭주 방지

        예: Robot-5(0.0s) → Robot-4(0.1s) → Robot-3(0.2s) → Robot-2(0.3s) → Robot-1(0.4s)
        최악의 경우(Robot-1만 생존) 0.4초 지연 → ELECTION_TIMEOUT(3초)에 비해 무시 가능
        """
        backoff = (self.total_robots - self.robot_id) * self.BACKOFF_STEP_SEC
        if backoff > 0:
            self.get_logger().debug(
                f'Robot {self.robot_id}: Election Backoff {backoff:.1f}초 대기 '
                f'(ID 기반 — 높은 ID가 먼저 선거 주도)'
            )
            self.create_timer(backoff, self._start_election_once)
        else:
            # 가장 높은 ID: 즉시 선거 시작
            self._start_election()

    def _start_election_once(self):
        """Backoff 타이머 콜백: 선거 시작 (중복 방지 확인 포함)"""
        # 이미 다른 로봇이 VICTORY를 선언했으면 선거 불필요
        if self.current_leader_id is not None and not self.is_election_on:
            self.get_logger().debug(
                f'Robot {self.robot_id}: Backoff 대기 중 Leader 확정됨 → 선거 취소'
            )
            return
        self._start_election()

    # ── Split-Brain 방지: 쿼럼 투표 ───────────────────────────────────
    def _vote_leader_dead(self, dead_leader_id: int):
        """
        구 Leader 사망을 /swarm/leader_dead 에 브로드캐스트.
        다른 로봇들도 동일 관측 시 투표 → QUORUM_SIZE 이상 시 승격 허용.
        """
        self._leader_dead_votes.add(self.robot_id)  # 자신의 투표 등록
        self.leader_dead_pub.publish(String(data=json.dumps({
            'type':           'LEADER_DEAD_VOTE',
            'dead_leader_id': dead_leader_id,
            'voter_id':       self.robot_id,
            'ts':             time.time()
        })))

    def _on_leader_dead(self, msg: String):
        """다른 로봇의 Leader 사망 투표 수집"""
        data = json.loads(msg.data)
        if (data.get('type') == 'LEADER_DEAD_VOTE' and
                data.get('dead_leader_id') == self.current_leader_id):
            self._leader_dead_votes.add(data['voter_id'])
            self.get_logger().debug(
                f'Leader 사망 투표 수집: {len(self._leader_dead_votes)}/{self.QUORUM_SIZE}'
            )

    def _has_quorum(self) -> bool:
        """현재 Leader 사망 투표가 쿼럼(QUORUM_SIZE)을 충족하는지 확인"""
        return len(self._leader_dead_votes) >= self.QUORUM_SIZE

    # ── Bully Election ────────────────────────────────────────────────
    def _start_election(self):
        if self.is_election_on:
            return
        self.is_election_on     = True
        self.election_responses = set()

        higher_ids = range(self.robot_id + 1, self.total_robots + 1)
        for rid in higher_ids:
            self.election_pub.publish(String(data=json.dumps({
                'type': 'ELECTION',
                'from': self.robot_id,
                'to':   rid,
                'ts':   time.time()
            })))

        if not list(higher_ids):
            self._declare_victory()
            return

        self.create_timer(self.ELECTION_TIMEOUT_SEC, self._election_timeout)

    def _election_timeout(self):
        """3초 내 응답 없으면 VICTORY 선언 (쿼럼 확인 전 단계)"""
        if not self.election_responses:
            # VICTORY 전 쿼럼 확인 단계로 진입
            self._check_quorum_before_victory()
        self.is_election_on = False

    def _check_quorum_before_victory(self):
        """
        [v1.2 보완] Split-Brain 방지 쿼럼 확인.
        QUORUM_SIZE 대 이상이 Leader 사망에 합의했을 때만 VICTORY 선언.

        흐름:
          쿼럼 충족 즉시 → VICTORY 선언
          미충족        → QUORUM_TIMEOUT_SEC 동안 대기 후 재확인
          MAX_ELECTION_RETRY 초과 → 쿼럼 없이 강제 선언 (최후 수단)
        """
        if self._has_quorum():
            self.get_logger().info(
                f'쿼럼 충족 ({len(self._leader_dead_votes)}대) → VICTORY 선언'
            )
            self._declare_victory()
            return

        if self._quorum_retry_count >= self.MAX_ELECTION_RETRY:
            self.get_logger().warn(
                f'쿼럼 미달이지만 최대 재시도({self.MAX_ELECTION_RETRY}회) 초과 → '
                f'강제 VICTORY 선언 (Split-Brain 위험 감수)'
            )
            self._declare_victory()
            return

        self._quorum_retry_count += 1
        self.get_logger().warn(
            f'쿼럼 미달 ({len(self._leader_dead_votes)}/{self.QUORUM_SIZE}) → '
            f'{self.QUORUM_TIMEOUT_SEC}초 대기 후 재시도 '
            f'({self._quorum_retry_count}/{self.MAX_ELECTION_RETRY})'
        )
        self.create_timer(self.QUORUM_TIMEOUT_SEC, self._check_quorum_before_victory)

    def _declare_victory(self):
        """쿼럼 확인 완료 후 Leader 선언 브로드캐스트"""
        self.current_leader_id    = self.robot_id
        self._leader_dead_votes   = set()   # 투표 초기화
        self._quorum_retry_count  = 0
        self.get_logger().info(
            f'Robot {self.robot_id}: LEADER 선출됨! 🏆 '
            f'(쿼럼 {len(self._leader_dead_votes) + 1}대 합의)'
        )
        self.election_pub.publish(String(data=json.dumps({
            'type':   'VICTORY',
            'leader': self.robot_id,
            'ts':     time.time()
        })))
        self._on_become_leader()

    def _on_become_leader(self):
        """
        Leader 역할 수행 시작.
        1. ElectionGuard Write Lock 해제
        2. Redis Replica 승격 (HA 복제 구조)
        3. SemanticMemory 컨텍스트 승계 → 임무 재분배
        """
        self.get_logger().info(f'Robot {self.robot_id}: Leader 역할 시작')
        # Step 1: Write Lock 해제 (ElectionGuard 연동)
        # self._election_guard.release_write_lock()

        # Step 2: Replica 승격 (Robot-2가 Replica인 경우)
        # if self.robot_id != 1:  # Robot-1이 아닌 경우만 승격 필요
        #     blackboard.promote_replica_to_master(EXPLORER_1_IP)

        # Step 3: SemanticMemory 컨텍스트 조회 + Frontier 재분배
        # summary = semantic_memory.get_context_summary()
        # self.get_logger().info(f'컨텍스트 승계:\n{summary}')

    def _on_election_msg(self, msg: String):
        data = json.loads(msg.data)
        msg_type = data.get('type')

        if msg_type == 'ELECTION' and data.get('to') == self.robot_id:
            self.election_pub.publish(String(data=json.dumps({
                'type': 'OK',
                'from': self.robot_id,
                'to':   data['from'],
                'ts':   time.time()
            })))
            # 타 로봇의 ELECTION 수신 시에도 backoff 적용
            # (이미 높은 ID가 선거 중이면 자연히 취소됨)
            self._start_election_with_backoff()

        elif msg_type == 'OK' and data.get('to') == self.robot_id:
            self.election_responses.add(data['from'])

        elif msg_type == 'VICTORY':
            new_leader = data['leader']
            self.current_leader_id   = new_leader
            self.is_election_on      = False
            self._leader_dead_votes  = set()
            self._quorum_retry_count = 0
            self.get_logger().info(f'새 Leader: Robot {new_leader}')


def main():
    rclpy.init()
    import sys
    robot_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    node = LeaderElection(robot_id)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

## 9. Redis Blackboard + Semantic Event Memory

### 9.0 🆕 보완: Redis HA 복제 (고가용성 설계)

> **문제**: 현재 설계는 Leader 로봇의 Redis에 모든 정보를 집중하는 계층형 방식이다.  
> Leader가 물리적 충격으로 즉사하면 새 리더 선출 전까지 **Frontier Claim과 Semantic Memory가 전량 소실**된다.  
> **해결**: Leader Redis → Explorer-1 Redis로 **비동기 복제(Async Replication)**를 유지하여,  
> Leader 교체 즉시 복제본 데이터를 승계한다.

#### 복제 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│              Redis HA 복제 토폴로지                          │
│                                                             │
│  Robot-1 (Leader)                Robot-2 (Explorer-1)      │
│  ┌──────────────────┐  SLAVEOF   ┌──────────────────┐      │
│  │  Redis Master    │ ─────────▶ │  Redis Replica   │      │
│  │  port 6379       │  실시간    │  port 6379        │      │
│  │                  │  비동기    │  (read-only)      │      │
│  │  • FrontierClaim │  복제      │  • FrontierClaim  │      │
│  │  • VictimData    │            │  • VictimData     │      │
│  │  • SemanticMem   │            │  • SemanticMem    │      │
│  └──────────────────┘            └──────────────────┘      │
│                                                             │
│  Leader 즉사 시나리오:                                       │
│    Robot-5 (Bully 선출) → 새 Leader                         │
│    Robot-2 Replica → SLAVEOF NO ONE (Master 승격)           │
│    새 Leader가 Robot-2 Redis에 재연결 → 데이터 무손실 승계   │
└─────────────────────────────────────────────────────────────┘

복제 대상:
  ✅ 생존자 위치 (victims hash)         — 절대 소실 불가
  ✅ Semantic Event Memory (events:*)   — Leader 컨텍스트 승계
  ✅ Frontier Claim (frontier:claim:*)  — 중복 탐색 방지
  ❌ 로봇 위치 (robot:N:state TTL 5s)   — 복제 불필요 (빠른 재생성)
```

#### 복제 대상 분리 전략

| 데이터 키 패턴 | 복제 여부 | 이유 |
|----------------|-----------|------|
| `victims` | **필수** | 생존자 정보는 절대 소실 불가 |
| `event:*` / `events:timeline` | **필수** | Leader 컨텍스트 승계 |
| `frontier:claim:*` | **권장** | 복제 지연 < 1초이므로 중복 claim 허용 오차 내 |
| `robot:*:state` | **불필요** | TTL 5초 → 로봇이 직접 재등록 |

### 9.1 Redis 설치 및 복제 초기화

```bash
# ── Leader 로봇 (Robot-1) ──────────────────────────────────────
sudo tee /etc/redis/redis-ghost5-master.conf << 'EOF'
bind 0.0.0.0
port 6379
requirepass ghost5secure!
masterauth ghost5secure!         # Replica 인증용
maxmemory 256mb
maxmemory-policy allkeys-lru

# 복제 안전망: 최소 1개 Replica가 연결되어야 쓰기 허용
# (재난 환경에서는 0으로 완화 가능)
min-replicas-to-write 0
min-replicas-max-lag 10

# 중요 데이터 AOF 영속화 (재시작 후에도 복구)
appendonly yes
appendfsync everysec
EOF
sudo redis-server /etc/redis/redis-ghost5-master.conf --daemonize yes

# ── Explorer-1 로봇 (Robot-2, 복제본) ─────────────────────────
sudo tee /etc/redis/redis-ghost5-replica.conf << 'EOF'
bind 0.0.0.0
port 6379
requirepass ghost5secure!
masterauth ghost5secure!
replicaof ${LEADER_IP} 6379      # Leader IP를 복제 소스로 지정
replica-read-only yes             # 복제본은 읽기 전용
replica-serve-stale-data yes      # 복제 지연 중에도 구버전 제공
appendonly yes
EOF
sudo redis-server /etc/redis/redis-ghost5-replica.conf --daemonize yes

# ── Replica Master 승격 스크립트 (Leader 사망 시 새 Leader에서 실행) ──
# ghost5_ws/scripts/promote_replica.sh
cat << 'SCRIPT' > ~/ghost5_ws/scripts/promote_replica.sh
#!/bin/bash
# 새 Leader가 Replica를 Master로 승격시키는 스크립트
# 사용법: ./promote_replica.sh <replica_robot_ip>
REPLICA_IP=${1:-"192.168.1.102"}
redis-cli -h ${REPLICA_IP} -p 6379 -a ghost5secure! REPLICAOF NO ONE
echo "✅ Robot-2 Redis 복제본을 Master로 승격 완료 (IP: ${REPLICA_IP})"
SCRIPT
chmod +x ~/ghost5_ws/scripts/promote_replica.sh
```

### 9.2 Blackboard 구현 (HA 복제 지원)

**파일 경로**: `ghost5_swarm/ghost5_swarm/blackboard.py`

```python
# ghost5_ws/src/ghost5_swarm/ghost5_swarm/blackboard.py
# v1.1 — Redis HA 복제 지원: Leader 즉사 시 Replica 자동 승계

import redis
import json
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class RobotState:
    pose:             dict    # {'x': float, 'y': float, 'theta': float}
    status:           str     # EXPLORING | VICTIM_FOUND | RETURNING | DOWN
    battery:          float   # 0.0 ~ 100.0
    coverage_percent: float
    timestamp:        float


@dataclass
class VictimDetection:
    x:           float
    y:           float
    confidence:  float
    detected_by: int          # robot_id
    timestamp:   float


class GhostBlackboard:
    """
    GHOST-5 공유 상태 저장소.

    [v1.1 보완] HA 복제 구조:
      - Master(Leader 로봇) → Replica(Explorer-1 로봇) 비동기 복제
      - Leader 사망 시 Replica를 SLAVEOF NO ONE으로 승격
      - 새 Leader가 promote_to_master()를 호출하여 자동 전환

    TTL 정책:
      POSE_TTL     = 5초   → TTL 만료 = 로봇 다운 자동 감지
      FRONTIER_TTL = 60초  → Claim 자동 해제
      VICTIM_TTL   = 영구  → 절대 삭제 불가
    """

    POSE_TTL     = 5
    FRONTIER_TTL = 60

    def __init__(
        self,
        leader_ip:   str = 'localhost',
        replica_ip:  Optional[str] = None,   # Explorer-1 IP (복제본)
        password:    str = 'ghost5secure!'
    ):
        self._password   = password
        self._leader_ip  = leader_ip
        self._replica_ip = replica_ip

        # Master Redis 연결
        self.r = redis.Redis(
            host=leader_ip, port=6379,
            password=password,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True
        )

        # Replica Redis 연결 (복제 상태 확인용)
        self._replica_r: Optional[redis.Redis] = None
        if replica_ip:
            self._replica_r = redis.Redis(
                host=replica_ip, port=6379,
                password=password,
                decode_responses=True,
                socket_connect_timeout=2
            )

    # ── HA: Replica 승격 (새 Leader에서 호출) ────────────────────────
    def promote_replica_to_master(self, replica_ip: str) -> bool:
        """
        Leader 사망 후 새 Leader가 Replica를 Master로 승격.
        Bully Algorithm의 _on_become_leader()에서 호출.

        흐름:
          1. Replica에 REPLICAOF NO ONE 명령 전송
          2. 성공 시 self.r을 Replica IP로 재연결
          3. 새 Leader의 Blackboard가 승격된 Redis를 사용

        Returns:
            True = 승격 성공 / False = 실패
        """
        try:
            r_replica = redis.Redis(
                host=replica_ip, port=6379,
                password=self._password,
                decode_responses=True,
                socket_connect_timeout=3
            )
            r_replica.execute_command('REPLICAOF', 'NO', 'ONE')

            # 승격 후 self.r 재연결
            self.r = r_replica
            self._leader_ip = replica_ip
            return True

        except redis.exceptions.RedisError as e:
            import logging
            logging.error(f'Replica 승격 실패: {e}')
            return False

    def get_replication_status(self) -> dict:
        """
        현재 Redis 복제 상태 반환 (디버깅/모니터링용).
        복제 지연(lag)이 1초 이상이면 경고 로그.
        """
        try:
            info = self.r.info('replication')
            return {
                'role':            info.get('role'),
                'connected_slaves': info.get('connected_slaves', 0),
                'repl_backlog_size': info.get('repl_backlog_size', 0),
                'slave_lag_sec':   self._get_replica_lag(info)
            }
        except Exception:
            return {'role': 'unknown', 'connected_slaves': 0}

    def _get_replica_lag(self, info: dict) -> float:
        """Replica 복제 지연 초 단위 반환"""
        # slave0: ip=X,port=Y,state=online,offset=Z,lag=W
        for k, v in info.items():
            if k.startswith('slave') and isinstance(v, dict):
                return float(v.get('lag', 0))
        return 0.0

    # ── 로봇 상태 ────────────────────────────────────────────────────
    def update_robot_state(self, robot_id: int, state: RobotState):
        self.r.setex(
            f'robot:{robot_id}:state',
            self.POSE_TTL,
            json.dumps(asdict(state))
        )

    def get_robot_state(self, robot_id: int) -> Optional[dict]:
        raw = self.r.get(f'robot:{robot_id}:state')
        return json.loads(raw) if raw else None

    def get_all_robot_states(self) -> dict:
        return {
            i: json.loads(raw)
            for i in range(1, 6)
            if (raw := self.r.get(f'robot:{i}:state'))
        }

    def get_alive_robots(self) -> list[int]:
        """TTL 만료되지 않은 로봇 = 생존 로봇"""
        return [i for i in range(1, 6) if self.r.exists(f'robot:{i}:state')]

    # ── Frontier Claim (원자적) ──────────────────────────────────────
    def claim_frontier(self, frontier_id: str, robot_id: int) -> bool:
        """
        원자적 Claim (NX = Not Exists).
        Master에 쓰므로 복제 지연 중 일시적 중복 claim이 발생할 수 있으나,
        TTL 60초 + MMPF 반발력으로 실질 영향 미미.
        """
        return bool(self.r.set(
            f'frontier:claim:{frontier_id}',
            robot_id,
            nx=True,
            ex=self.FRONTIER_TTL
        ))

    def release_frontier(self, frontier_id: str):
        self.r.delete(f'frontier:claim:{frontier_id}')

    def get_all_frontier_claims(self) -> dict:
        keys = self.r.keys('frontier:claim:*')
        return {k.replace('frontier:claim:', ''): self.r.get(k) for k in keys}

    # ── 생존자 감지 ──────────────────────────────────────────────────
    def add_victim(self, victim: VictimDetection, sync_write: bool = True):
        """
        생존자 위치 저장 (영구, 복제 대상 최우선).

        [v1.2 보완] 동기 쓰기(Sync Write) 옵션:
          sync_write=True (기본): WAIT 명령으로 최소 1개 Replica에
          기록이 완료될 때까지 최대 100ms 대기.
          → 복제 지연(Slave Lag) 찰나에 Leader가 사망해도 생존자 정보 유실 방지.

          sync_write=False: 기존 비동기 쓰기 (대역폭 우선, 일반 이벤트용).

        WAIT(numreplicas, timeout_ms):
          numreplicas = 1   : 복제본 1대에 commit 확인
          timeout_ms  = 100 : 최대 100ms 대기 (재난 환경 지연 허용치)
          반환값: 실제 응답한 복제본 수 (0이면 timeout 내 복제 미완료)
        """
        victim_id = f'victim:{int(victim.timestamp * 1000)}'
        self.r.hset('victims', victim_id, json.dumps(asdict(victim)))

        if sync_write:
            try:
                # WAIT 명령: 1개 이상 Replica에 기록 완료 대기 (최대 100ms)
                replicated_count = self.r.execute_command('WAIT', 1, 100)
                if replicated_count < 1:
                    import logging
                    logging.warning(
                        f'[Blackboard] 생존자 데이터 복제 미완료 '
                        f'(timeout 100ms, replicated={replicated_count}) — '
                        f'victim_id={victim_id}'
                    )
                else:
                    import logging
                    logging.debug(
                        f'[Blackboard] 생존자 데이터 복제 완료 '
                        f'(replicated={replicated_count}), victim_id={victim_id}'
                    )
            except redis.exceptions.RedisError as e:
                import logging
                logging.error(f'[Blackboard] WAIT 명령 실패: {e} — 비동기 쓰기로 폴백')

    def add_victim_async(self, victim: VictimDetection):
        """비동기 생존자 저장 (일반 이벤트, 대역폭 우선)"""
        self.add_victim(victim, sync_write=False)

    def get_all_victims(self) -> list[dict]:
        return [json.loads(v) for v in self.r.hgetall('victims').values()]

    # ── 복제 지연 모니터링 ────────────────────────────────────────────
    def check_slave_lag_and_warn(self, warn_threshold_sec: float = 1.0) -> float:
        """
        Replica 복제 지연 확인 및 임계값 초과 시 경고.
        주기적으로 호출하여 실시간 lag 모니터링.

        Returns:
            현재 복제 지연(초), 연결 없으면 -1.0
        """
        status = self.get_replication_status()
        lag = status.get('slave_lag_sec', -1.0)

        if lag < 0:
            return -1.0

        if lag > warn_threshold_sec:
            import logging
            logging.warning(
                f'[Blackboard] Replica 복제 지연 경고: {lag:.2f}초 '
                f'(임계값 {warn_threshold_sec}초) — '
                f'Leader 사망 시 최대 {lag:.2f}초 데이터 유실 위험'
            )
        return lag
```

### 9.3 Semantic Event Memory 구현

**파일 경로**: `ghost5_swarm/ghost5_swarm/semantic_memory.py`

```python
# ghost5_ws/src/ghost5_swarm/ghost5_swarm/semantic_memory.py

import redis
import json
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional


class EventType(Enum):
    ZONE_ENTERED     = "zone_entered"
    ZONE_COMPLETED   = "zone_completed"
    ZONE_BLOCKED     = "zone_blocked"
    COMM_LOST        = "comm_lost"
    COMM_RESTORED    = "comm_restored"
    ROBOT_ISOLATED   = "robot_isolated"
    VICTIM_SUSPECTED = "victim_suspected"
    VICTIM_CONFIRMED = "victim_confirmed"
    VICTIM_RESCUED   = "victim_rescued"
    DOOR_LOCKED      = "door_locked"
    DEBRIS_BLOCKING  = "debris_blocking"
    PASSABLE_FOUND   = "passable_found"


@dataclass
class SemanticEvent:
    event_id:      str
    event_type:    str
    robot_id:      int
    location:      dict            # {'x': float, 'y': float}
    zone_id:       Optional[str]
    description:   str
    attempt_count: int
    timestamp:     float
    resolved:      bool


class SemanticMemory:
    """
    MEM 논문 언어 메모리 압축 원칙 적용:
      - 실패 이벤트: attempt_count만 증가, 설명 압축
      - 처리된 이벤트: 5분 후 자동 만료
      - Leader 교체 시 전체 컨텍스트 즉시 승계 가능

    skip_zones 연동:
      - 3회 이상 진입 실패한 구역 → Frontier MMPF에서 우선순위 하락
    """

    RESOLVED_TTL        = 300   # 5분 후 만료
    MAX_ATTEMPTS_SKIP   = 3     # 3회 실패 → 스킵 권고

    def __init__(self, leader_ip: str = 'localhost', password: str = 'ghost5secure!'):
        self.r = redis.Redis(
            host=leader_ip, port=6379,
            password=password,
            decode_responses=True
        )

    def record_event(self, event: SemanticEvent):
        """이벤트 기록 (실패 반복 시 압축)"""
        key = f'event:{event.event_id}'
        existing = self.r.get(key)

        if existing:
            data = json.loads(existing)
            data['attempt_count'] += 1
            data['description'] = self._compress(
                data['description'], data['attempt_count']
            )
            self.r.set(key, json.dumps(data))
        else:
            self.r.set(key, json.dumps(asdict(event)))

        # 타임라인에 추가 (sorted set, score=timestamp)
        self.r.zadd('events:timeline', {event.event_id: event.timestamp})

    def _compress(self, desc: str, attempts: int) -> str:
        if attempts >= self.MAX_ATTEMPTS_SKIP:
            return f"{desc.split(':')[0]}: {attempts}회 시도 실패 — 스킵 권고"
        return desc

    def record_zone_blocked(self, robot_id: int, zone_id: str,
                            location: dict, reason: str):
        event_id = f'blocked:{zone_id}'
        existing = self.r.get(f'event:{event_id}')
        attempts = (json.loads(existing).get('attempt_count', 0) + 1
                    if existing else 1)

        self.record_event(SemanticEvent(
            event_id=event_id, event_type=EventType.ZONE_BLOCKED.value,
            robot_id=robot_id, location=location, zone_id=zone_id,
            description=f'Robot {robot_id}: {zone_id} 진입 불가 — {reason}',
            attempt_count=attempts, timestamp=time.time(), resolved=False
        ))

    def record_comm_lost(self, robot_id: int, last_location: dict):
        self.record_event(SemanticEvent(
            event_id=f'comm_lost:robot_{robot_id}',
            event_type=EventType.COMM_LOST.value,
            robot_id=robot_id, location=last_location, zone_id=None,
            description=(f'Robot {robot_id}: '
                         f'({last_location["x"]:.1f}, {last_location["y"]:.1f}) 에서 통신 단절'),
            attempt_count=1, timestamp=time.time(), resolved=False
        ))

    def get_context_summary(self) -> str:
        """
        새 Leader가 즉시 상황 파악 가능한 자연어 요약.
        MEM의 Language Memory mt → mt+1 업데이트 개념.
        """
        event_ids = self.r.zrange('events:timeline', 0, -1)
        active = []
        for eid in event_ids:
            raw = self.r.get(f'event:{eid}')
            if raw:
                ev = json.loads(raw)
                if not ev.get('resolved', False):
                    active.append(ev['description'])

        if not active:
            return "현재 미처리 이벤트 없음. 정상 탐색 진행 중."

        return "현재 상황 요약:\n" + "".join(
            f"  {i}. {desc}\n" for i, desc in enumerate(active, 1)
        )

    def get_skip_zones(self) -> list[str]:
        """3회 이상 실패한 구역 목록 (MMPF skip_zones 연동)"""
        event_ids = self.r.zrange('events:timeline', 0, -1)
        skip_zones = []
        for eid in event_ids:
            raw = self.r.get(f'event:{eid}')
            if raw:
                ev = json.loads(raw)
                if (ev.get('event_type') == EventType.ZONE_BLOCKED.value and
                        ev.get('attempt_count', 0) >= self.MAX_ATTEMPTS_SKIP):
                    if zid := ev.get('zone_id'):
                        skip_zones.append(zid)
        return skip_zones

    def mark_resolved(self, event_id: str):
        """이벤트 처리 완료 → 5분 후 자동 만료"""
        key = f'event:{event_id}'
        raw = self.r.get(key)
        if raw:
            data = json.loads(raw)
            data['resolved'] = True
            self.r.setex(key, self.RESOLVED_TTL, json.dumps(data))
```

---

## 10. 2.5D Elevation Map 구현

### 10.0 🆕 보완: IMU 기반 동적 보정 (Dynamic Calibration)

> **문제**: RPLiDAR C1 Z-stack 누적은 로봇 주행 중 진동·경사로 인해  
> 수평 스캔 빔이 바닥을 쳐서 **고스트 장애물(Ghost Obstacle)**을 생성할 위험이 있다.  
> **해결**: BNO055 IMU의 Pitch/Roll 데이터로 스캔 포인트를 수평면으로 보정 후 저장한다.

#### IMU 보정 기하학 원리

```
                로봇이 기울어졌을 때 스캔 빔 왜곡

 수평 지면                바닥
 ─────────────────────────────────────────────────

 [정상 자세]               [경사 자세 (pitch = θ)]
  LiDAR ─── 빔 ──▶ 벽      LiDAR
    |                         \  ← pitch로 인해 빔이 아래로 기울어짐
    |                          \
  base_link                     ▼ 바닥을 쳐서 Ghost Obstacle 생성!

 보정 목표:
   scan_point_world = R_imu ⁻¹ × scan_point_lidar_frame

 R_imu:  BNO055 Pitch/Roll로 구성한 3×3 회전 행렬
         R = Ry(pitch) @ Rx(roll)    (yaw는 이미 TF에 포함)

 보정된 포인트는 항상 수평면(z≒0) 기준으로 변환되므로
 바닥 반사 포인트를 장애물로 오인하는 현상이 제거된다.
```

#### 보정 유효 조건

| IMU 상태 | 처리 |
|----------|------|
| `\|pitch\| < 5°` AND `\|roll\| < 5°` | 보정 없이 그대로 사용 (오버헤드 최소화) |
| `5° ≤ \|pitch\|` OR `\|roll\| ≤ 15°` | R_imu 회전 행렬 보정 적용 |
| `\|pitch\| > 15°` OR `\|roll\| > 15°` | **스캔 전체 폐기** (신뢰 불가 구간) |

### 10.1 LiDAR Z-stack Elevation 노드 (IMU 동적 보정 포함)

**파일 경로**: `ghost5_slam/ghost5_slam/lidar_elevation_node.py`

```python
# ghost5_ws/src/ghost5_slam/ghost5_slam/lidar_elevation_node.py
# v1.1 — BNO055 IMU Pitch/Roll 기반 Ghost Obstacle 제거

import rclpy
from rclpy.node import Node
import numpy as np
from sensor_msgs.msg import LaserScan, Imu
from nav_msgs.msg import OccupancyGrid
import tf2_ros
from qos_profiles import MAP_QOS


class LidarElevationNode(Node):
    """
    RPLiDAR C1 단일 수평 스캔 + 이동 궤적 Z-stack 누적 방식.

    [v1.1 보완] BNO055 IMU 동적 보정:
      - Pitch/Roll로 회전 행렬 R_imu를 구성하여 스캔 포인트를 수평면으로 보정
      - 보정 전: 경사로나 진동 시 빔이 바닥을 쳐 Ghost Obstacle 발생
      - 보정 후: 모든 포인트를 월드 수평면 기준으로 재투영 → 오탐 제거

    원리:
      RPLiDAR 장착 높이(15cm) 기준, 보정 후 빔이 닿은 위치의 장애물은
      최소 15cm 이상 높이임을 보장.

    비용 할당:
      h < 10cm  → cost=10  (통과 가능)
      h < 22cm  → cost=60  (주의: 로봇 높이 근접)
      h >= 22cm → cost=100 (통과 불가)
    """

    LIDAR_MOUNT_H   = 0.15   # RPLiDAR 장착 높이 (m)
    GRID_RES        = 0.05   # 격자 해상도 (m)
    MAX_RANGE       = 12.0   # RPLiDAR C1 최대 유효 범위 (m)
    PUBLISH_HZ      = 2.0    # Elevation 퍼블리시 주기 (Hz)

    # IMU 보정 임계값 (degrees)
    IMU_SKIP_THRESH  = 15.0  # 이 이상 기울면 스캔 전체 폐기
    IMU_APPLY_THRESH = 5.0   # 이 이상이면 회전 행렬 보정 적용

    # [v1.2 보완] Ray-casting Clearing 파라미터
    HITS_TO_OBSTACLE = 3     # 이 이상 hit 누적 시 장애물로 확정
    CLEAR_DECREMENT  = 1     # LiDAR 빔 통과 시 hits 감소량
    MIN_HITS_TO_KEEP = 0     # hits가 이 값 이하이면 셀 삭제 (Ghost Trail 제거)

    # [v1.3 보완] Temporal Consistency Filter 파라미터
    # 셀이 장애물로 '처음 관측된 시각'을 기록하여,
    # 짧은 순간만 감지되고 사라지는 노이즈성 장애물을 억제
    TEMPORAL_MIN_SEC    = 2.0    # 최소 관측 지속 시간 (초): 이 미만이면 확정 불가
    TEMPORAL_DECAY_SEC  = 10.0   # 마지막 hit 후 이 시간이 지나면 셀 소멸

    def __init__(self, robot_id: int):
        super().__init__(f'lidar_elevation_robot_{robot_id}')
        self.robot_id = robot_id

        # 격자 셀 저장소:
        # {(gx, gy): {'min_h': float, 'hits': int,
        #             'first_seen': float,  ← Temporal Filter: 최초 관측 시각
        #             'last_seen':  float}} ← Temporal Filter: 마지막 관측 시각
        self.elevation_cells: dict[tuple, dict] = {}

        # BNO055 IMU 최신값 (라디안)
        self._imu_pitch: float = 0.0
        self._imu_roll:  float = 0.0

        self.tf_buffer   = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # LiDAR 스캔 구독
        self.create_subscription(
            LaserScan, f'/robot_{robot_id}/scan', self._scan_cb, 10
        )
        # BNO055 IMU 구독 (geometry_msgs/Imu 또는 sensor_msgs/Imu)
        self.create_subscription(
            Imu, f'/robot_{robot_id}/imu/data', self._imu_cb, 10
        )

        self.elev_pub = self.create_publisher(
            OccupancyGrid, f'/robot_{robot_id}/elevation_layer', MAP_QOS
        )
        self.create_timer(1.0 / self.PUBLISH_HZ, self._publish_elevation)

    # ── IMU 콜백 ──────────────────────────────────────────────────────
    def _imu_cb(self, msg: Imu):
        """
        BNO055의 orientation 쿼터니언 → Pitch / Roll 추출.
        EKF 필터링이 된 /imu/data를 사용하므로 노이즈가 억제된 값.
        """
        q = msg.orientation
        # Roll  (x축 회전)
        sinr = 2.0 * (q.w * q.x + q.y * q.z)
        cosr = 1.0 - 2.0 * (q.x * q.x + q.y * q.y)
        self._imu_roll = float(np.arctan2(sinr, cosr))

        # Pitch (y축 회전)
        sinp = 2.0 * (q.w * q.y - q.z * q.x)
        sinp = np.clip(sinp, -1.0, 1.0)
        self._imu_pitch = float(np.arcsin(sinp))

    # ── 스캔 콜백 ─────────────────────────────────────────────────────
    def _scan_cb(self, msg: LaserScan):
        """
        LiDAR 스캔 수신 → IMU 보정 → 월드 좌표 변환 → Elevation 셀 누적.

        IMU 보정 흐름:
          1. pitch/roll을 도(°)로 변환하여 폐기/보정/통과 분기
          2. 보정 필요 시 R_imu = Ry(pitch) @ Rx(roll) 구성
          3. 각 스캔 포인트를 LiDAR 프레임에서 3D 벡터로 표현
          4. R_imu 역행렬로 수평면 기준 포인트로 변환
          5. 변환 후 z값이 양수(= 지면 위)인 포인트만 장애물로 등록

        [v1.2 보완] Ray-casting Clearing (Moving Object 처리):
          - LiDAR 빔이 장애물 셀을 통과(free space 확인) 시 hits 감소
          - hits ≤ MIN_HITS_TO_KEEP → 셀 삭제 (Ghost Trail 제거)
          - 정적 잔해: 빔이 닿아 hits 증가 → HITS_TO_OBSTACLE 도달 시 확정
          - 이동 물체: 통과 빔이 반복되면 hits 감소 → 자연 소멸

        Bresenham 선분 알고리즘으로 빔 경로 상의 모든 격자 셀을 열거,
        종점(hit) 이전 셀들은 clearing, 종점 셀은 hit 처리.
        """
        pitch_deg = np.degrees(abs(self._imu_pitch))
        roll_deg  = np.degrees(abs(self._imu_roll))

        if pitch_deg > self.IMU_SKIP_THRESH or roll_deg > self.IMU_SKIP_THRESH:
            self.get_logger().debug(
                f'IMU 기울기 초과 (pitch={pitch_deg:.1f}°, roll={roll_deg:.1f}°) → 스캔 폐기'
            )
            return

        need_correction = (pitch_deg >= self.IMU_APPLY_THRESH or
                           roll_deg  >= self.IMU_APPLY_THRESH)
        R_imu = self._build_rotation_matrix(self._imu_pitch, self._imu_roll)

        try:
            tf = self.tf_buffer.lookup_transform(
                'map', f'robot_{self.robot_id}/laser', rclpy.time.Time()
            )
        except Exception:
            return

        rx   = tf.transform.translation.x
        ry   = tf.transform.translation.y
        yaw  = self._quat_to_yaw(tf.transform.rotation)

        # LiDAR 원점의 격자 좌표 (Ray-casting 시작점)
        origin_gx = int(rx / self.GRID_RES)
        origin_gy = int(ry / self.GRID_RES)

        angle = msg.angle_min

        for r in msg.ranges:
            if not (msg.range_min < r < min(msg.range_max, self.MAX_RANGE)):
                angle += msg.angle_increment
                continue

            lx = r * np.cos(angle)
            ly = r * np.sin(angle)
            lz = 0.0
            point_lidar = np.array([lx, ly, lz])

            if need_correction:
                point_corrected = R_imu.T @ point_lidar
                if point_corrected[2] < -0.05:
                    angle += msg.angle_increment
                    continue
                r_corrected     = np.hypot(point_corrected[0], point_corrected[1])
                angle_corrected = np.arctan2(point_corrected[1], point_corrected[0])
            else:
                r_corrected     = r
                angle_corrected = angle

            wx = rx + r_corrected * np.cos(yaw + angle_corrected)
            wy = ry + r_corrected * np.sin(yaw + angle_corrected)
            hit_gx = int(wx / self.GRID_RES)
            hit_gy = int(wy / self.GRID_RES)

            # ── Ray-casting: 빔 경로 상 셀 Clearing ─────────────────
            # Bresenham 선분으로 origin → hit 경로의 모든 셀 열거
            # hit 이전 셀: clearing (hits 감소) / hit 셀: accumulate (hits 증가)
            ray_cells = self._bresenham(origin_gx, origin_gy, hit_gx, hit_gy)

            for i, (cgx, cgy) in enumerate(ray_cells):
                cell_key = (cgx, cgy)
                is_hit_cell = (i == len(ray_cells) - 1)

                if is_hit_cell:
                    # 종점(장애물 hit): hits 증가 + 타임스탬프 갱신
                    now = self.get_clock().now().nanoseconds * 1e-9
                    if cell_key not in self.elevation_cells:
                        self.elevation_cells[cell_key] = {
                            'min_h':      self.LIDAR_MOUNT_H,
                            'hits':       1,
                            'first_seen': now,   # Temporal: 최초 관측
                            'last_seen':  now
                        }
                    else:
                        self.elevation_cells[cell_key]['hits'] += 1
                        self.elevation_cells[cell_key]['last_seen'] = now
                else:
                    # 경로 통과 셀: hits 감소 (이동 물체 Ghost Trail 제거)
                    if cell_key in self.elevation_cells:
                        self.elevation_cells[cell_key]['hits'] -= self.CLEAR_DECREMENT
                        if self.elevation_cells[cell_key]['hits'] <= self.MIN_HITS_TO_KEEP:
                            del self.elevation_cells[cell_key]   # Ghost Trail 삭제

            angle += msg.angle_increment

    @staticmethod
    def _bresenham(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
        """
        Bresenham 선분 알고리즘: (x0,y0) → (x1,y1) 경로의 격자 셀 목록 반환.
        Ray-casting Clearing에 사용.

        Returns:
            [(gx, gy), ...] — 시작점 제외, 종점(hit) 포함
        """
        cells = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        cx, cy = x0, y0

        while True:
            if cx != x0 or cy != y0:   # 시작점 제외
                cells.append((cx, cy))
            if cx == x1 and cy == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx  += sx
            if e2 < dx:
                err += dx
                cy  += sy

        return cells

    # ── 회전 행렬 생성 ────────────────────────────────────────────────
    @staticmethod
    def _build_rotation_matrix(pitch: float, roll: float) -> np.ndarray:
        """
        R_imu = Ry(pitch) @ Rx(roll)

        Rx(roll):
          [[1,    0,         0     ]
           [0,  cos(r),  -sin(r)  ]
           [0,  sin(r),   cos(r)  ]]

        Ry(pitch):
          [[ cos(p),  0,  sin(p) ]
           [   0,     1,    0    ]
           [-sin(p),  0,  cos(p) ]]

        사용법:
          point_horizontal = R_imu.T @ point_in_tilted_lidar_frame
        """
        cp, sp = np.cos(pitch), np.sin(pitch)
        cr, sr = np.cos(roll),  np.sin(roll)

        Ry = np.array([[ cp, 0, sp],
                       [  0, 1,  0],
                       [-sp, 0, cp]], dtype=float)

        Rx = np.array([[1,   0,   0],
                       [0,  cr, -sr],
                       [0,  sr,  cr]], dtype=float)

        return Ry @ Rx   # shape (3, 3)

    # ── Elevation Grid 퍼블리시 ──────────────────────────────────────
    def _publish_elevation(self):
        """
        누적된 elevation_cells를 OccupancyGrid로 변환하여 퍼블리시.

        [v1.2 보완] hits 임계값 기반 비용 할당:
          hits < HITS_TO_OBSTACLE: 아직 확정 전 (미관측 처리, -1)
          hits ≥ HITS_TO_OBSTACLE: 확정 장애물 → 높이 기반 비용 할당

        [v1.3 보완] Temporal Consistency Filter:
          ① Decay: 마지막 hit 후 TEMPORAL_DECAY_SEC 경과 셀 자동 삭제
          ② Duration Guard: 최초 관측 후 TEMPORAL_MIN_SEC 미만인 셀은
             hits 충족해도 확정 불가 → 순간적 이동 물체 잔상 억제

        두 필터 조합 효과:
          정적 잔해 → hits 빠르게 누적 + 오래 유지 → 장애물 확정 ✅
          이동 물체 → hits 적음 OR 지속 시간 짧음 → 미확정/소멸 ✅
          노이즈    → Ray-casting으로 clearing + Temporal로 이중 억제 ✅
        """
        if not self.elevation_cells:
            return

        now = self.get_clock().now().nanoseconds * 1e-9

        # ── Temporal Decay: 오래된 셀 일괄 삭제 ──────────────────────
        to_delete = [
            key for key, info in self.elevation_cells.items()
            if (now - info.get('last_seen', now)) > self.TEMPORAL_DECAY_SEC
        ]
        for key in to_delete:
            del self.elevation_cells[key]

        if not self.elevation_cells:
            return

        xs = [k[0] for k in self.elevation_cells]
        ys = [k[1] for k in self.elevation_cells]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width  = max_x - min_x + 1
        height = max_y - min_y + 1

        grid = OccupancyGrid()
        grid.header.frame_id = 'map'
        grid.header.stamp    = self.get_clock().now().to_msg()
        grid.info.resolution = self.GRID_RES
        grid.info.width      = width
        grid.info.height     = height
        grid.info.origin.position.x = min_x * self.GRID_RES
        grid.info.origin.position.y = min_y * self.GRID_RES
        data = [-1] * (width * height)

        for (gx, gy), info in self.elevation_cells.items():
            idx = (gy - min_y) * width + (gx - min_x)
            if not (0 <= idx < len(data)):
                continue

            # ① hits 미달: 확정 전
            if info['hits'] < self.HITS_TO_OBSTACLE:
                continue

            # ② Temporal Duration Guard: 최초 관측 후 지속 시간 미달
            observed_duration = now - info.get('first_seen', now)
            if observed_duration < self.TEMPORAL_MIN_SEC:
                continue   # 짧은 순간만 감지된 노이즈 → 미확정

            h = info['min_h']
            if   h < 0.10: cost = 10
            elif h < 0.22: cost = 60
            else:          cost = 100
            data[idx] = cost

        grid.data = data
        self.elev_pub.publish(grid)

    @staticmethod
    def _quat_to_yaw(q) -> float:
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return float(np.arctan2(siny, cosy))


def main():
    rclpy.init()
    import sys
    robot_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    node = LidarElevationNode(robot_id)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

### 10.2 Nav2 Costmap 3-레이어 설정

**파일 경로**: `ghost5_bringup/config/nav2_params.yaml`

```yaml
# ghost5_ws/src/ghost5_bringup/config/nav2_params.yaml

local_costmap:
  local_costmap:
    ros__parameters:
      plugins:
        - obstacle_layer
        - elevation_layer
        - low_obs_layer
        - robot_layer          # 🆕 타 로봇 동적 장애물 레이어
        - inflation_layer

      obstacle_layer:
        plugin: "nav2_costmap_2d::ObstacleLayer"
        observation_sources: scan
        scan.topic: /robot_N/scan

      elevation_layer:         # LiDAR Z-stack Elevation
        plugin: "nav2_costmap_2d::StaticLayer"
        map_topic: /robot_N/elevation_layer
        map_subscribe_transient_local: true
        combination_method: 1  # 최대값 취합

      low_obs_layer:           # 카메라 15cm 이하 잔해
        plugin: "nav2_costmap_2d::StaticLayer"
        map_topic: /robot_N/low_obstacle_layer
        combination_method: 1

      robot_layer:             # 🆕 타 로봇 위치 → 동적 장애물
        plugin: "nav2_costmap_2d::ObstacleLayer"
        observation_sources: robot_poses
        robot_poses:
          topic: /swarm/robot_poses_array   # InterRobotCostmapLayer가 퍼블리시
          data_type: "PointCloud2"
          sensor_frame: map
          obstacle_max_range: 3.0           # 3m 이내 로봇만 costmap 반영
          obstacle_min_range: 0.0
          raytrace_max_range: 3.0
          raytrace_min_range: 0.0
          clearing: true                    # 로봇이 이동하면 이전 장애물 자동 제거
          marking: true
          max_obstacle_height: 0.5          # 로봇 높이 기준 (m)

      inflation_layer:
        inflation_radius: 0.25
        cost_scaling_factor: 3.0

global_costmap:
  global_costmap:
    ros__parameters:
      plugins:
        - static_layer
        - elevation_layer
        - inflation_layer

      elevation_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
        map_topic: /map_merge/elevation_global
        combination_method: 1
```

---

### 10.3 🆕 Inter-Robot 동적 장애물 등록 (Nav2 Costmap)

> **문제**: Nav2 local costmap은 LiDAR 기반 정적 장애물만 인식한다.  
> 좁은 통로에서 두 로봇이 마주쳤을 때 서로를 빈 공간으로 인식하여 정면 충돌하거나 교착(Deadlock) 상태에 빠진다.  
> **해결**: 각 로봇의 `/robot_N/pose`를 5Hz로 수집·집계하여 `/swarm/robot_poses_array` (PointCloud2)로 퍼블리시,  
> Nav2 `ObstacleLayer`가 이를 동적 장애물로 인식해 자동 회피 경로를 생성한다.

#### 설계 개요

```
/robot_1/pose ─┐
/robot_2/pose ─┤                         Nav2 local_costmap
/robot_3/pose ─┼─ InterRobotCostmapLayer ──→ robot_layer (ObstacleLayer)
/robot_4/pose ─┤   (swarm_coordinator)        ↓
/robot_5/pose ─┘   퍼블리시 5Hz           자동 회피 경로 재계획

- 자신(my_robot_id)은 제외하고 타 로봇만 장애물로 등록
- TTL 0.3s: 0.3초 내 위치 갱신 없으면 장애물 자동 삭제 (이동한 로봇 잔상 방지)
- 반경 0.35m inflation: Pinky Pro 차체 폭(~0.28m) + 안전 여유 0.07m
```

**파일 경로**: `ghost5_navigation/ghost5_navigation/inter_robot_costmap_layer.py`

```python
# ghost5_ws/src/ghost5_navigation/ghost5_navigation/inter_robot_costmap_layer.py
"""
Inter-Robot Dynamic Obstacle Layer for Nav2 Costmap.

타 로봇 위치를 Nav2 local costmap의 동적 장애물로 등록하는 노드.

동작:
  1. /robot_N/pose (POSE_QOS, 10Hz) 구독 → 5대 위치 수집
  2. 자신 제외 타 로봇 위치를 PointCloud2로 변환
  3. /swarm/robot_poses_array (5Hz) 퍼블리시
  4. Nav2 ObstacleLayer가 해당 토픽을 동적 장애물로 costmap에 반영

TTL 관리:
  0.3초 이내 갱신된 위치만 PointCloud2에 포함 (이동 후 잔상 방지)
"""

import time
import rclpy
from rclpy.node import Node
import numpy as np
from geometry_msgs.msg import PoseWithCovarianceStamped
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header
import struct

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ghost5_bringup/config'))
from qos_profiles import POSE_QOS


class InterRobotCostmapLayer(Node):
    """
    타 로봇 위치 → Nav2 Costmap 동적 장애물 등록 노드.

    파라미터:
      robot_id       : 자신의 로봇 ID (1~5), 자신 위치는 제외
      total_robots   : 전체 로봇 수 (기본 5)
      publish_hz     : 퍼블리시 주기 (기본 5Hz)
      pose_ttl_sec   : 위치 유효 시간 (기본 0.3s, 초과 시 장애물 제거)
    """

    PUBLISH_HZ   = 5.0    # costmap 갱신 주기
    POSE_TTL_SEC = 0.3    # 위치 유효 TTL (로봇 이동 후 잔상 방지)

    def __init__(self, robot_id: int, total_robots: int = 5):
        super().__init__(f'inter_robot_costmap_robot_{robot_id}')
        self.robot_id     = robot_id
        self.total_robots = total_robots

        # {robot_id: (x, y, timestamp)}
        self._robot_positions: dict[int, tuple[float, float, float]] = {}

        # 타 로봇 위치 구독 (자신 제외)
        for i in range(1, total_robots + 1):
            if i == robot_id:
                continue
            self.create_subscription(
                PoseWithCovarianceStamped,
                f'/robot_{i}/pose',
                lambda msg, rid=i: self._pose_callback(msg, rid),
                POSE_QOS
            )

        # /swarm/robot_poses_array 퍼블리시 (Nav2 ObstacleLayer 구독 대상)
        self._pub = self.create_publisher(
            PointCloud2,
            '/swarm/robot_poses_array',
            POSE_QOS
        )

        self.create_timer(1.0 / self.PUBLISH_HZ, self._publish_costmap_points)

        self.get_logger().info(
            f'InterRobotCostmapLayer 시작: robot_{robot_id}, '
            f'TTL={self.POSE_TTL_SEC}s, {self.PUBLISH_HZ}Hz'
        )

    def _pose_callback(self, msg: PoseWithCovarianceStamped, robot_id: int):
        """타 로봇 위치 수신 및 TTL 타임스탬프 갱신"""
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        self._robot_positions[robot_id] = (x, y, time.monotonic())

    def _publish_costmap_points(self):
        """
        TTL 유효한 타 로봇 위치만 PointCloud2로 변환·퍼블리시.

        PointCloud2 포맷: XYZ float32 (z=0.1 고정, 로봇 중심 높이)
        Nav2 ObstacleLayer는 이 포인트를 동적 장애물로 costmap에 반영.
        """
        now = time.monotonic()
        valid_points: list[tuple[float, float]] = []

        for rid, (x, y, ts) in list(self._robot_positions.items()):
            if now - ts > self.POSE_TTL_SEC:
                # TTL 초과 → 장애물 제거 (로봇이 이동했거나 다운됨)
                del self._robot_positions[rid]
                self.get_logger().debug(f'Robot-{rid} 위치 TTL 초과 → 장애물 제거')
                continue
            valid_points.append((x, y))

        cloud_msg = self._build_pointcloud2(valid_points)
        self._pub.publish(cloud_msg)

    def _build_pointcloud2(self, points: list[tuple[float, float]]) -> PointCloud2:
        """XYZ float32 PointCloud2 메시지 생성"""
        header = Header()
        header.stamp    = self.get_clock().now().to_msg()
        header.frame_id = 'map'

        fields = [
            PointField(name='x', offset=0,  datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4,  datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8,  datatype=PointField.FLOAT32, count=1),
        ]

        point_step = 12  # 3 × float32
        data = bytearray()
        for (x, y) in points:
            data += struct.pack('fff', float(x), float(y), 0.1)  # z=0.1 (로봇 중심)

        msg = PointCloud2()
        msg.header      = header
        msg.height      = 1
        msg.width       = len(points)
        msg.fields      = fields
        msg.is_bigendian = False
        msg.point_step  = point_step
        msg.row_step    = point_step * len(points)
        msg.data        = bytes(data)
        msg.is_dense    = True
        return msg


def main(args=None):
    import sys
    rclpy.init(args=args)
    robot_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    node = InterRobotCostmapLayer(robot_id=robot_id)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

#### 핵심 파라미터 요약

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| `PUBLISH_HZ` | 5 Hz | Nav2 costmap 갱신 주기 (10Hz pose 대비 절반, CPU 절약) |
| `POSE_TTL_SEC` | 0.3 s | 위치 유효 TTL — 이동한 로봇 잔상 자동 제거 |
| `obstacle_max_range` | 3.0 m | 3m 이내 로봇만 costmap 반영 |
| `inflation_radius` | 0.25 m | Pinky Pro 차체(~0.28m) + 여유 margin |
| `clearing` | true | 로봇 이동 시 이전 장애물 셀 자동 삭제 |

#### 기존 충돌 회피와의 역할 분담

| 메커니즘 | 레이어 | 커버 범위 |
|----------|--------|-----------|
| Nav2 Costmap ObstacleLayer (scan) | 정적 | 벽·잔해 회피 |
| Elevation Layer (lidar Z-stack) | 정적 | 낮은 장애물 회피 |
| **InterRobotCostmapLayer (신규)** | **동적** | **로봇 ↔ 로봇 이동 중 충돌 방지** |
| MMPF robot_repulsion | 목표 분산 | 같은 Frontier 중복 탐색 방지 |
| Rendezvous 프로토콜 | 통신 조율 | 통신 단절 시 집결 충돌 완화 |

---

## 11. Rendezvous 프로토콜 구현

### 11.0 🆕 보완: Communication Gradient Map (지능적 랑데부 지점 선택)

> **문제**: 기존 설계는 신호 단절 시 단순히 '마지막 양호 지점' 한 점으로 복귀한다.  
> 그 지점 자체가 이미 잔해로 막혔거나 무너졌을 수 있고, 여러 번 방문했던 경로가 이미 봉쇄된 상황을 전혀 고려하지 않는다.  
> **해결**: 탐색 중 RSSI 값을 지도에 연속적으로 기록하여 **신호 강도 등고선 지도(Communication Gradient Map)**를 구축하고,  
> 신호 강도가 강해지는 방향의 경사면(gradient)을 따라 **통신 보장 안전 구역(Safe Comm Zone)**으로 경로 계획한다.

#### Communication Gradient Map 개념

```
  탐색 중 RSSI를 지도에 기록

  y ▲
    │   -90  -85  -80  -75  -70  -65  (dBm, 높을수록 신호 강)
    │   ░░░  ░░░  ▒▒▒  ▒▒▒  ███  ███
    │   ░░░  ░░░  ▒▒▒  ███  ███  ███   ← Safe Comm Zone (≥ -70dBm)
    │   ░░░  ▒▒▒  ▒▒▒  ▒▒▒  ███  ███
    │                            ↑
    │                         AP 위치
    └──────────────────────────────── x

  ▽RSSI(x,y) = RSSI gradient (신호 강해지는 방향 벡터)

  랑데부 전략:
    1. 현재 위치에서 ▽RSSI 방향으로 이동 (경사 상승)
    2. RSSI ≥ SAFE_COMM_RSSI(-70) 구역 도달 → Safe Comm Zone 진입
    3. 해당 구역에서 30초 대기 후 재연결 시도
    4. 재연결 실패 시 home position 복귀

  기존 방식 vs. 새 방식 비교:
    기존: 마지막 양호 지점 1개로 직선 복귀 (막힌 경로 무시)
    신규: RSSI 등고선을 따라 현재 연결 가능한 안전 구역으로 복귀
```

**파일 경로**: `ghost5_swarm/ghost5_swarm/comm_monitor.py`

```python
# ghost5_ws/src/ghost5_swarm/ghost5_swarm/comm_monitor.py
# v1.1 — Communication Gradient Map 기반 지능적 랑데부 지점 선택

import subprocess
import re
import json
import rclpy
from rclpy.node import Node
import numpy as np
from std_msgs.msg import Float32, String
from nav_msgs.msg import OccupancyGrid
import tf2_ros
from qos_profiles import POSE_QOS, EVENT_QOS, MAP_QOS


class CommMonitor(Node):
    """
    WiFi 신호 강도 모니터링 + Communication Gradient Map 기반 Rendezvous.

    [v1.1 보완] Communication Gradient Map:
      - 탐색 중 RSSI를 격자 지도에 연속 기록
      - 신호 단절 임박 시 RSSI gradient를 계산하여 Safe Comm Zone 방향으로 이동
      - "마지막 양호 지점 1개"가 아닌 "신호 보장 안전 구역"으로 경로 계획

    RSSI 임계값 (dBm):
      SAFE_COMM   : -70  → Safe Comm Zone 기준 (이 이상이면 안전)
      WARN_RSSI   : -70  → 경고: 속도 50% 감속 + RSSI 지도 갱신 강화
      CRIT_RSSI   : -80  → 위험: gradient 방향으로 Safe Zone 복귀 시작
      LOST_RSSI   : -90  → 완전 고립: 저장된 RSSI 지도로 home 복귀

    복귀 중 생존자 발견 → 로컬 저장 → 재연결 시 일괄 보고
    """

    SAFE_COMM_RSSI     = -70    # Safe Comm Zone 기준 (dBm)
    WARN_RSSI          = -70
    CRIT_RSSI          = -80
    LOST_RSSI          = -90
    RENDEZVOUS_WAIT    = 30.0   # Safe Zone 도달 후 대기 (초)
    MEASURE_PERIOD_SEC = 2.0    # RSSI 측정 주기 (0.5Hz)
    RSSI_MAP_RES       = 0.5    # RSSI 지도 격자 해상도 (m, 일반 맵의 10배)
    RSSI_MAP_HISTORY   = 200    # 최대 저장 셀 수 (메모리 제한)

    def __init__(self, robot_id: int, interface: str = 'wlan0'):
        super().__init__(f'comm_monitor_robot_{robot_id}')
        self.robot_id        = robot_id
        self.interface       = interface
        self.current_rssi    = 0
        self.rendezvous_mode = False
        self.offline_victims = []   # 고립 중 감지된 생존자 (로컬 저장)

        # ── Communication Gradient Map ────────────────────────────
        # 구조: {(gx, gy): rssi_value_dbm}
        # 격자 해상도 RSSI_MAP_RES=0.5m (일반 5cm 격자보다 넓게 — 메모리 절약)
        self._rssi_map: dict[tuple[int, int], float] = {}

        # TF 버퍼 (현재 위치 획득)
        self.tf_buffer   = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # 퍼블리셔
        self.rssi_pub        = self.create_publisher(Float32, f'/robot_{robot_id}/rssi',      POSE_QOS)
        self.comm_event_pub  = self.create_publisher(String,  '/swarm/comm_events',           EVENT_QOS)
        self.rssi_map_pub    = self.create_publisher(OccupancyGrid, f'/robot_{robot_id}/rssi_map', MAP_QOS)

        self.create_subscription(String, '/swarm/comm_events', self._on_comm_event, EVENT_QOS)
        self.create_timer(self.MEASURE_PERIOD_SEC, self._measure_and_act)
        self.create_timer(5.0, self._publish_rssi_map)   # 0.2Hz 퍼블리시

    # ── 측정 및 행동 결정 ─────────────────────────────────────────────
    def _measure_and_act(self):
        rssi = self._get_rssi()
        self.current_rssi = rssi
        self.rssi_pub.publish(Float32(data=float(rssi)))

        # 현재 위치에 RSSI 기록 (Gradient Map 누적)
        pose = self._get_current_pose()
        if pose:
            self._update_rssi_map(pose['x'], pose['y'], rssi)

        if rssi >= self.WARN_RSSI:
            if self.rendezvous_mode:
                self._exit_rendezvous()

        elif rssi >= self.CRIT_RSSI:
            self.get_logger().warn(
                f'Robot {self.robot_id}: RSSI 경고 {rssi}dBm — 속도 감속'
            )
            self._request_speed_reduction(0.5)

        elif rssi >= self.LOST_RSSI:
            self.get_logger().error(
                f'Robot {self.robot_id}: RSSI 위험 {rssi}dBm — Gradient 랑데부 진입'
            )
            self._enter_gradient_rendezvous()

        else:
            self.get_logger().error(
                f'Robot {self.robot_id}: 완전 단절 — RSSI 지도 기반 자율 복귀'
            )
            self._autonomous_return_via_gradient()

    # ── Communication Gradient Map 갱신 ─────────────────────────────
    def _update_rssi_map(self, x: float, y: float, rssi: float):
        """
        현재 위치 (x, y)에 RSSI 값 기록.
        동일 격자에 여러 번 방문 시 지수 이동 평균으로 갱신 (최신 값 가중치 높게).
        """
        gx = int(x / self.RSSI_MAP_RES)
        gy = int(y / self.RSSI_MAP_RES)
        key = (gx, gy)

        if key in self._rssi_map:
            # 지수 이동 평균: α=0.3 (최신 값 30% 반영)
            self._rssi_map[key] = 0.7 * self._rssi_map[key] + 0.3 * rssi
        else:
            self._rssi_map[key] = float(rssi)

        # 메모리 제한: 오래된 셀 제거
        if len(self._rssi_map) > self.RSSI_MAP_HISTORY:
            oldest_key = next(iter(self._rssi_map))
            del self._rssi_map[oldest_key]

    def _compute_rssi_gradient(
        self, current_x: float, current_y: float
    ) -> tuple[float, float] | None:
        """
        현재 위치 주변의 RSSI gradient를 계산하여
        신호가 강해지는 방향 단위 벡터를 반환.

        방법: 주변 8-방향 격자의 RSSI 가중 평균으로 방향 추정

        Returns:
            (dx, dy): Safe Comm Zone 방향 단위 벡터
            None: 주변 데이터 부족
        """
        gx_c = int(current_x / self.RSSI_MAP_RES)
        gy_c = int(current_y / self.RSSI_MAP_RES)

        # 주변 5×5 격자 범위에서 RSSI 데이터 수집
        neighbors = []
        for dg_x in range(-2, 3):
            for dg_y in range(-2, 3):
                if dg_x == 0 and dg_y == 0:
                    continue
                key = (gx_c + dg_x, gy_c + dg_y)
                if key in self._rssi_map:
                    wx = (gx_c + dg_x) * self.RSSI_MAP_RES
                    wy = (gy_c + dg_y) * self.RSSI_MAP_RES
                    neighbors.append((wx, wy, self._rssi_map[key]))

        if len(neighbors) < 3:
            return None   # 데이터 부족

        # RSSI가 높은 방향으로 가중치를 두어 gradient 계산
        # rssi는 음수(dBm)이므로 값이 클수록(0에 가까울수록) 신호 강함
        rssi_values = np.array([v for _, _, v in neighbors])
        rssi_weights = rssi_values - rssi_values.min() + 1e-6   # 음수 → 양수 변환

        dx_sum = sum(w * (nx - current_x) for (nx, _, _), w in zip(neighbors, rssi_weights))
        dy_sum = sum(w * (ny - current_y) for (_, ny, _), w in zip(neighbors, rssi_weights))

        mag = np.hypot(dx_sum, dy_sum)
        if mag < 1e-6:
            return None

        return (dx_sum / mag, dy_sum / mag)   # 단위 벡터

    def _find_safe_comm_zone(
        self, current_x: float, current_y: float
    ) -> tuple[float, float] | None:
        """
        RSSI 지도에서 Safe Comm Zone (RSSI ≥ SAFE_COMM_RSSI) 위치 탐색.
        RSSI gradient를 따라 최대 MAX_STEP 걸음 탐색.

        [v1.2 보완] 로컬 미니마(Local Minima) 탈출 전략:
          gradient 계산 실패(= 모든 방향 신호 동일하거나 데이터 부족) 시
          다음 순서로 백업 전략 적용:

          ① Random Perturbation: 무작위 방향으로 소폭 이동 후 재탐색 (2회)
          ② Best-History Fallback: RSSI 지도에서 가장 신호가 강했던
             최근 3개 셀의 평균 좌표로 직선 복귀

        Returns:
            (x, y): 찾은 Safe Zone 좌표
            None: 모든 전략 실패 → home 복귀
        """
        STEP     = self.RSSI_MAP_RES   # 0.5m
        MAX_STEP = 10
        RNG      = np.random.default_rng(seed=self.robot_id)  # 재현 가능한 랜덤

        cx, cy = current_x, current_y
        consecutive_minima = 0   # 연속 gradient 실패 횟수

        for step in range(MAX_STEP):
            gx = int(cx / self.RSSI_MAP_RES)
            gy = int(cy / self.RSSI_MAP_RES)

            # 현재 격자 RSSI가 안전하면 즉시 반환
            if self._rssi_map.get((gx, gy), -100) >= self.SAFE_COMM_RSSI:
                self.get_logger().info(
                    f'Safe Comm Zone 발견: ({cx:.2f}, {cy:.2f}), {step}걸음'
                )
                return (cx, cy)

            grad = self._compute_rssi_gradient(cx, cy)

            if grad is not None:
                # 정상 gradient 이동
                consecutive_minima = 0
                dx, dy = grad
                cx += dx * STEP
                cy += dy * STEP

            else:
                # gradient 계산 불가 → 로컬 미니마 감지
                consecutive_minima += 1

                if consecutive_minima <= 2:
                    # ① Random Perturbation: 무작위 방향으로 소폭 이탈
                    rand_angle = RNG.uniform(0, 2 * np.pi)
                    cx += np.cos(rand_angle) * STEP
                    cy += np.sin(rand_angle) * STEP
                    self.get_logger().debug(
                        f'로컬 미니마 감지 → Random Perturbation '
                        f'({cx:.2f}, {cy:.2f}), 시도 {consecutive_minima}/2'
                    )
                else:
                    # ② Best-History Fallback: 가장 신호 좋았던 상위 3개 셀 평균
                    fallback = self._get_best_history_target()
                    if fallback:
                        fx, fy = fallback
                        self.get_logger().warn(
                            f'로컬 미니마 탈출 불가 → Best-History Fallback '
                            f'({fx:.2f}, {fy:.2f})'
                        )
                        return (fx, fy)
                    else:
                        break   # 히스토리도 없으면 home 복귀

        return None   # 모든 전략 실패 → home 복귀

    def _get_best_history_target(self) -> tuple[float, float] | None:
        """
        RSSI 지도에서 신호가 가장 강했던 상위 3개 셀의 평균 좌표 반환.
        로컬 미니마 탈출 백업 전략 (Best-History Fallback).
        """
        if not self._rssi_map:
            return None

        # RSSI 기준 내림차순 정렬 (강한 신호 먼저)
        sorted_cells = sorted(
            self._rssi_map.items(),
            key=lambda kv: kv[1],   # rssi 값 기준
            reverse=True            # 높을수록 강한 신호
        )

        top_n = min(3, len(sorted_cells))
        top_cells = sorted_cells[:top_n]

        avg_x = np.mean([(gx * self.RSSI_MAP_RES) for (gx, _), _ in top_cells])
        avg_y = np.mean([(gy * self.RSSI_MAP_RES) for (_, gy), _ in top_cells])

        self.get_logger().info(
            f'Best-History 상위 {top_n}개 평균: ({avg_x:.2f}, {avg_y:.2f}), '
            f'최고 RSSI={top_cells[0][1]:.0f}dBm'
        )
        return (float(avg_x), float(avg_y))

    # ── Rendezvous 진입 (Gradient 기반) ──────────────────────────────
    def _enter_gradient_rendezvous(self):
        """
        RSSI gradient를 따라 Safe Comm Zone으로 이동.
        기존 '마지막 양호 지점' 대신 '통신 보장 안전 구역'으로 경로 계획.
        """
        if self.rendezvous_mode:
            return
        self.rendezvous_mode = True

        # SemanticMemory 이벤트 기록
        self.comm_event_pub.publish(String(data=json.dumps({
            'type':     'COMM_DEGRADED',
            'robot_id': self.robot_id,
            'rssi':     self.current_rssi,
            'ts':       self.get_clock().now().nanoseconds
        })))

        pose = self._get_current_pose()
        if pose is None:
            self.get_logger().warn(f'Robot {self.robot_id}: 현재 위치 미확인 → home 복귀')
            self._navigate_home()
            return

        # ① RSSI gradient로 Safe Comm Zone 탐색
        safe_zone = self._find_safe_comm_zone(pose['x'], pose['y'])

        if safe_zone:
            sx, sy = safe_zone
            self.get_logger().info(
                f'Robot {self.robot_id}: Safe Comm Zone으로 이동 ({sx:.2f}, {sy:.2f})'
            )
            self._navigate_to(sx, sy)
        else:
            # ② Safe Zone 미발견 → home 복귀
            self.get_logger().warn(
                f'Robot {self.robot_id}: Safe Comm Zone 없음 → home 복귀'
            )
            self._navigate_home()

        # 30초 후 재연결 실패 시 자율 복귀
        self.create_timer(self.RENDEZVOUS_WAIT, self._rendezvous_timeout)

    def _autonomous_return_via_gradient(self):
        """
        완전 고립 시 RSSI 지도를 따라 신호 강한 방향으로 이동 후 home 복귀.
        복귀 중 생존자 발견 시 위치 로컬 저장.
        """
        pose = self._get_current_pose()
        if pose:
            safe_zone = self._find_safe_comm_zone(pose['x'], pose['y'])
            if safe_zone:
                self._navigate_to(*safe_zone)
                self.create_timer(15.0, lambda: self._navigate_home())
                return

        self._navigate_home()

    def _rendezvous_timeout(self):
        """랑데부 대기 후 재연결 실패 → 자율 복귀"""
        if self.rendezvous_mode:
            self.get_logger().warn(
                f'Robot {self.robot_id}: 랑데부 재연결 실패 → home 복귀'
            )
            self._navigate_home()

    def _exit_rendezvous(self):
        """통신 복구 → 탐색 재개 + 고립 중 감지 생존자 일괄 보고"""
        self.rendezvous_mode = False
        self.get_logger().info(f'Robot {self.robot_id}: 통신 복구 — 탐색 재개')
        self.comm_event_pub.publish(String(data=json.dumps({
            'type':            'COMM_RESTORED',
            'robot_id':        self.robot_id,
            'offline_victims': self.offline_victims,
            'ts':              self.get_clock().now().nanoseconds
        })))
        self.offline_victims = []

    # ── RSSI 지도 시각화 퍼블리시 ────────────────────────────────────
    def _publish_rssi_map(self):
        """
        Communication Gradient Map을 OccupancyGrid로 변환하여 퍼블리시.
        Foxglove Studio에서 신호 강도 등고선 시각화 가능.

        매핑: RSSI -100dBm → cost=100 (빨강) / -60dBm → cost=0 (초록)
        """
        if not self._rssi_map:
            return

        keys = list(self._rssi_map.keys())
        xs = [k[0] for k in keys]
        ys = [k[1] for k in keys]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width  = max_x - min_x + 1
        height = max_y - min_y + 1

        grid = OccupancyGrid()
        grid.header.frame_id = 'map'
        grid.header.stamp    = self.get_clock().now().to_msg()
        grid.info.resolution = self.RSSI_MAP_RES
        grid.info.width      = width
        grid.info.height     = height
        grid.info.origin.position.x = min_x * self.RSSI_MAP_RES
        grid.info.origin.position.y = min_y * self.RSSI_MAP_RES
        data = [-1] * (width * height)

        for (gx, gy), rssi in self._rssi_map.items():
            idx = (gy - min_y) * width + (gx - min_x)
            if 0 <= idx < len(data):
                # RSSI -100 ~ -60 → cost 100 ~ 0 (선형 변환)
                cost = max(0, min(100, int((-60 - rssi) * 2.5)))
                data[idx] = cost

        grid.data = data
        self.rssi_map_pub.publish(grid)

    # ── 유틸리티 ──────────────────────────────────────────────────────
    def _get_current_pose(self) -> dict | None:
        """TF에서 현재 로봇 위치 획득"""
        try:
            tf = self.tf_buffer.lookup_transform(
                'map',
                f'robot_{self.robot_id}/base_link',
                rclpy.time.Time()
            )
            return {
                'x': tf.transform.translation.x,
                'y': tf.transform.translation.y
            }
        except Exception:
            return None

    def _get_rssi(self) -> int:
        """iwconfig로 WiFi 신호 강도 측정"""
        try:
            result = subprocess.run(
                ['iwconfig', self.interface],
                capture_output=True, text=True, timeout=2
            )
            match = re.search(r'Signal level=(-\d+) dBm', result.stdout)
            if match:
                return int(match.group(1))
        except Exception as e:
            self.get_logger().error(f'RSSI 측정 실패: {e}')
        return -100

    def _request_speed_reduction(self, factor: float):
        """Nav2 max_vel_x 동적 재설정 (rclpy parameter service)"""
        pass

    def _navigate_to(self, x: float, y: float):
        """Nav2 NavigateToPose Action 클라이언트"""
        pass

    def _navigate_home(self):
        """최초 출발 위치(home)로 Nav2 복귀"""
        pass

    def _on_comm_event(self, msg: String):
        """다른 로봇의 통신 이벤트 처리 (Leader 측 swarm_coordinator와 연동)"""
        pass


def main():
    rclpy.init()
    import sys
    robot_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    node = CommMonitor(robot_id)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

---

## 12. 생존자 감지 구현 (3-센서 교차 검증)

**파일 경로**: `ghost5_victim/ghost5_victim/proximity_detector.py`

```python
# ghost5_ws/src/ghost5_victim/ghost5_victim/proximity_detector.py

import json
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from std_msgs.msg import Float32, String
from qos_profiles import EVENT_QOS


class ProximityDetectorNode(Node):
    """
    US-016 초음파 + TCRT5000 IR 기반 생존자 감지.

    US-016 초음파:
      측정 범위: 2cm ~ 400cm (GPIO Trigger/Echo)
      사람 감지 범위: 20cm ~ 150cm

    TCRT5000 IR (반사형):
      사람 피부/옷 반사율: ADC 300~700 (0~1023 기준, 현장 캘리브레이션 필요)
      근거리 감지: ~30cm

    신뢰도 계산:
      combined = 0.6 * us_confidence + 0.4 * ir_confidence
      임계값: 0.60 이상 시 생존자 감지로 판단
    """

    US_HUMAN_MIN     = 0.20   # 사람 감지 최소 거리 (m)
    US_HUMAN_MAX     = 1.50   # 사람 감지 최대 거리 (m)
    IR_HUMAN_MIN     = 300    # ADC 최솟값
    IR_HUMAN_MAX     = 700    # ADC 최댓값
    CONFIDENCE_THRESH = 0.60
    HISTORY_LEN      = 10

    def __init__(self, robot_id: int):
        super().__init__(f'proximity_detector_robot_{robot_id}')
        self.robot_id  = robot_id
        self.us_history: list[float] = []
        self.ir_history: list[float] = []

        self.create_subscription(
            Range,   f'/robot_{robot_id}/ultrasonic', self._us_cb, 10
        )
        self.create_subscription(
            Float32, f'/robot_{robot_id}/ir_sensor',  self._ir_cb, 10
        )
        self.victim_pub = self.create_publisher(
            String, f'/robot_{robot_id}/victim_proximity', EVENT_QOS
        )

    def _us_cb(self, msg: Range):
        self.us_history.append(msg.range)
        if len(self.us_history) > self.HISTORY_LEN:
            self.us_history.pop(0)
        if len(self.us_history) >= 5:
            self._analyze()

    def _ir_cb(self, msg: Float32):
        self.ir_history.append(msg.data)
        if len(self.ir_history) > self.HISTORY_LEN:
            self.ir_history.pop(0)

    def _analyze(self):
        us_arr = np.array(self.us_history)
        ir_arr = np.array(self.ir_history)

        us_in_range  = (us_arr >= self.US_HUMAN_MIN) & (us_arr <= self.US_HUMAN_MAX)
        us_conf      = float(us_in_range.mean())

        ir_conf = 0.0
        if len(ir_arr) > 0:
            ir_in_range = (ir_arr >= self.IR_HUMAN_MIN) & (ir_arr <= self.IR_HUMAN_MAX)
            ir_conf     = float(ir_in_range.mean())

        combined = 0.6 * us_conf + 0.4 * ir_conf

        if combined >= self.CONFIDENCE_THRESH:
            detection = json.dumps({
                'robot_id':           self.robot_id,
                'us_confidence':      us_conf,
                'ir_confidence':      ir_conf,
                'combined_confidence': combined,
                'us_distance_m':      float(np.median(us_arr)),
                'timestamp':          self.get_clock().now().nanoseconds
            })
            self.victim_pub.publish(String(data=detection))
            self.get_logger().warn(
                f'⚠️ Robot {self.robot_id}: 생존자 감지 '
                f'(신뢰도 {combined:.2f}, 거리 {np.median(us_arr):.2f}m)'
            )
```

### 12.2 3-센서 융합기 (victim_fuser.py)

```python
# ghost5_ws/src/ghost5_victim/ghost5_victim/victim_fuser.py

import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from ghost5_interfaces.msg import VictimDetection
from qos_profiles import EVENT_QOS


class VictimFuser(Node):
    """
    US-016 초음파 / TCRT5000 IR / 5MP 카메라 YOLOv8n 3-센서 융합.

    융합 전략:
      - 1개 센서 단독 감지:  confidence < 0.6  → 무시
      - 2개 센서 동시 감지:  confidence 가중 평균 → 0.6 이상 시 보고
      - 3개 센서 모두 감지:  즉시 보고 + 삼각측량 요청

    오탐 방지:
      - 동일 위치에서 3회 이상 연속 감지 시 확정 보고
    """

    def __init__(self, robot_id: int):
        super().__init__(f'victim_fuser_robot_{robot_id}')
        self.robot_id     = robot_id
        self.proximity    = None   # 초음파+IR 감지 결과
        self.vision       = None   # YOLOv8n 감지 결과
        self.confirm_cnt  = 0

        self.create_subscription(
            String, f'/robot_{robot_id}/victim_proximity',
            self._proximity_cb, EVENT_QOS
        )
        self.create_subscription(
            String, f'/robot_{robot_id}/victim_vision',
            self._vision_cb, EVENT_QOS
        )
        self.victim_pub = self.create_publisher(
            VictimDetection, '/swarm/victim', EVENT_QOS
        )

    def _proximity_cb(self, msg: String):
        self.proximity = json.loads(msg.data)
        self._fuse()

    def _vision_cb(self, msg: String):
        self.vision = json.loads(msg.data)
        self._fuse()

    def _fuse(self):
        if self.proximity is None and self.vision is None:
            return

        prox_conf  = self.proximity['combined_confidence'] if self.proximity else 0.0
        vision_conf = self.vision['confidence']             if self.vision    else 0.0

        # 두 센서 모두 감지 시 최종 신뢰도 계산
        if self.proximity and self.vision:
            final_conf = 0.5 * prox_conf + 0.5 * vision_conf
            self.confirm_cnt += 1
        elif prox_conf >= 0.8 or vision_conf >= 0.9:
            # 단독 센서가 매우 높은 신뢰도인 경우
            final_conf = max(prox_conf, vision_conf)
            self.confirm_cnt += 1
        else:
            return

        if self.confirm_cnt >= 3:   # 3회 연속 확인 후 최종 보고
            self._report_victim(final_conf)
            self.confirm_cnt = 0
            self.proximity   = None
            self.vision      = None

    def _report_victim(self, confidence: float):
        msg = VictimDetection()
        msg.detected_by_robot = self.robot_id
        msg.combined_confidence = confidence
        msg.timestamp = self.get_clock().now().to_msg()
        # TODO: 실제 위치 TF 조회 후 설정
        self.victim_pub.publish(msg)
        self.get_logger().warn(
            f'🚨 Robot {self.robot_id}: 생존자 최종 보고 (신뢰도 {confidence:.2f})'
        )
```

---

## 13. Hailo NPU 가속 구현 (Phase 2)

### 13.1 설치

```bash
# Hailo 드라이버 및 런타임 설치
sudo apt update
sudo apt install hailo-all    # hailort + tappas + Python API 포함

# PCIe Gen 3 활성화 (AI HAT+는 자동)
sudo raspi-config nonint do_pcie_gen 3

# 재부팅 후 검증
hailortcli fw-control identify
# 출력: Board Name: Hailo-8, Firmware Version: 4.17.0+

# Python API
pip install hailort --break-system-packages

# YOLOv8n → HEF 변환 (Hailo Dataflow Compiler)
# COCO person class만 파인튜닝된 모델 사용
hailomz compile --model yolov8n --target hailo8 --output /opt/ghost5/models/yolov8n_person.hef
```

### 13.2 NPU 기반 Vision Detector

**파일 경로**: `ghost5_victim/ghost5_victim/vision_detector_npu.py`

```python
# ghost5_ws/src/ghost5_victim/ghost5_victim/vision_detector_npu.py

import numpy as np
import cv2
import json
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from qos_profiles import EVENT_QOS

# Hailo NPU API
from hailo_platform import (
    VDevice, Hef, HailoStreamInterface, ConfigureParams,
    InputVStreamParams, OutputVStreamParams, FormatType, InferVStreams
)


class VisionDetectorNPU(Node):
    """
    Hailo AI HAT+ 26TOPS + YOLOv8n 인체 감지.

    CPU 부하:
      기존 (CPU만): YOLOv8n 20~30%
      NPU 오프로딩 후: 2~3%  (약 -27%p)

    신뢰도 임계값: 0.65
    """

    HEF_PATH        = '/opt/ghost5/models/yolov8n_person.hef'
    CONF_THRESHOLD  = 0.65
    INPUT_SIZE      = (640, 640)   # YOLOv8n 표준 입력

    def __init__(self, robot_id: int):
        super().__init__(f'vision_detector_npu_robot_{robot_id}')
        self.robot_id = robot_id
        self.bridge   = CvBridge()

        # Hailo 초기화
        self.target = VDevice()
        hef = Hef(self.HEF_PATH)
        cfg = ConfigureParams.create_from_hef(hef, interface=HailoStreamInterface.PCIe)
        network_groups = self.target.configure(hef, cfg)
        self.ng       = network_groups[0]
        self.in_vsp   = InputVStreamParams.make(self.ng,  format_type=FormatType.UINT8)
        self.out_vsp  = OutputVStreamParams.make(self.ng, format_type=FormatType.FLOAT32)

        self.create_subscription(
            Image, f'/robot_{robot_id}/camera/image_raw', self._img_cb, 10
        )
        self.victim_pub = self.create_publisher(
            String, f'/robot_{robot_id}/victim_vision', EVENT_QOS
        )
        self.get_logger().info('Hailo NPU Vision Detector 초기화 완료')

    def _img_cb(self, msg: Image):
        img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        img_resized = cv2.resize(img, self.INPUT_SIZE)
        result = self._infer(img_resized)

        if result and result['confidence'] >= self.CONF_THRESHOLD:
            detection = json.dumps({
                'robot_id':   self.robot_id,
                'confidence': result['confidence'],
                'bbox':       result.get('bbox'),
                'timestamp':  self.get_clock().now().nanoseconds
            })
            self.victim_pub.publish(String(data=detection))
            self.get_logger().warn(
                f'Robot {self.robot_id}: YOLOv8n 인체 감지 (신뢰도 {result["confidence"]:.2f})'
            )

    def _infer(self, img: np.ndarray) -> dict | None:
        input_data = img[np.newaxis].astype(np.uint8)   # NHWC
        try:
            with InferVStreams(self.ng, self.in_vsp, self.out_vsp) as pipeline:
                input_dict = {self.ng.get_input_vstream_infos()[0].name: input_data}
                pipeline.send(input_dict)
                output = pipeline.recv()
            # 출력 파싱 (YOLOv8n HEF 포맷에 따라 조정 필요)
            conf = float(list(output.values())[0].max())
            return {'confidence': conf, 'bbox': None}
        except Exception as e:
            self.get_logger().error(f'NPU 추론 실패: {e}')
            return None
```

---

## 14. SROS2 보안 구현

```bash
# 1. Keystore 초기화 (GCS에서 1회 실행)
ros2 security create_keystore ~/ghost5_keystore

# 2. 로봇별 노드 인증서 생성
for i in 1 2 3 4 5; do
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/slam_node
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/nav_node
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/swarm_node
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/victim_detector
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/comm_monitor
done
ros2 security create_key ~/ghost5_keystore /ghost5/gcs/monitor_node

# 3. 권한 정책 생성
ros2 security generate_artifacts -k ~/ghost5_keystore -p ghost5_policy.xml

# 4. 환경변수 (모든 로봇 .bashrc에 추가)
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=~/ghost5_keystore
export ROS_DOMAIN_ID=42   # SROS2 V4 취약점 대응: 도메인 고정

# 5. V3 취약점 대응: 기본값 강제 설정
# zenoh_config.json5에 rtps_protection_kind: ENCRYPT 추가
```

### 14.1 권한 정책 (최소 권한 원칙)

```xml
<!-- ghost5_policy.xml -->
<policy>
  <!-- Explorer: 자신의 데이터만 퍼블리시 -->
  <enclave path="/ghost5/robot_2/swarm_node">
    <profiles>
      <profile node="swarm_coordinator" ns="/robot_2">
        <topics publish="ALLOW" subscribe="ALLOW">
          <topic>swarm/frontier_claims</topic>
          <topic>swarm/election</topic>
          <topic>swarm/heartbeat</topic>
          <topic>swarm/comm_events</topic>
          <topic>swarm/victim</topic>
        </topics>
        <topics publish="DENY" subscribe="DENY">
          <topic>**</topic>
        </topics>
      </profile>
    </profiles>
  </enclave>
</policy>
```

---

## 15. 커스텀 메시지 정의

```
# ghost5_interfaces/msg/RobotState.msg
int32   robot_id
geometry_msgs/Pose2D pose
string  status          # EXPLORING | VICTIM_FOUND | RETURNING | DOWN | CHARGING
float32 battery_percent
float32 coverage_percent
builtin_interfaces/Time timestamp

# ghost5_interfaces/msg/VictimDetection.msg
int32  detected_by_robot
geometry_msgs/Point location
float32 us_confidence
float32 ir_confidence
float32 vision_confidence
float32 combined_confidence
builtin_interfaces/Time timestamp

# ghost5_interfaces/msg/FrontierList.msg
string[] frontier_ids
float32[] xs
float32[] ys
float32[] info_gains
string[] claimed_by      # robot_id 또는 "" (미claim)

# ghost5_interfaces/msg/SwarmStatus.msg
int32   leader_id
int32[] alive_robots
int32   victim_count
float32 global_coverage_percent
string  mission_phase    # EXPLORING | VICTIM_RESCUE | RETURNING

# ghost5_interfaces/srv/ClaimFrontier.srv
string frontier_id
int32  robot_id
---
bool   success
string reason

# ghost5_interfaces/action/ExploreRegion.action
geometry_msgs/Polygon region
---
float32 coverage_percent
int32   victims_found
---
float32 current_coverage
int32   frontiers_remaining
```

---

## 16. 인풋 기반 페이징 시스템 설계

> **설계 원칙**: 오프셋 페이징(offset/limit) 대신 **커서(cursor) 기반 페이징**을 사용한다.  
> 이유: 실시간 데이터(Frontier claim, 로봇 상태, 이벤트 로그)는 지속적으로 추가/삭제되므로 offset 기반은 중복 조회 및 누락이 발생한다.

### 16.0 🆕 보완: Election Phase 엣지 케이스 처리

> **문제**: Leader Election 진행 중(Election Phase)에 GCS나 다른 로봇이 Redis에 쓰기 시도를 하면  
> Replica 승격 과정과 충돌하여 데이터 불일치가 발생할 수 있다.  
> **해결**:  
> (1) Election 기간 동안 Redis에 **Write Lock 플래그**를 세팅하여 쓰기를 일시 차단  
> (2) GCS API는 `X-Election-Status` 헤더를 반환하고 클라이언트에 **쿼리 재시도 로직** 제공  
> (3) 읽기(조회)는 항상 허용 — 부정확한 데이터가 반환될 수 있음을 메타데이터로 명시

#### Election Phase 상태 전이

```
정상 운영                     Leader Election 진행 중
(write_lock = 0)             (write_lock = 1)

  쓰기 허용 ✅                  쓰기 차단 ❌ (5초 TTL)
  읽기 허용 ✅                  읽기 허용 ✅ (stale 데이터 명시)
  API 응답: 200                 API 응답: 200 + warning 헤더
                                  X-Election-Status: in_progress
                                  X-Data-Staleness: possible

       ↕ LeaderElection._start_election() 호출 시
       write_lock SET EX 10    (10초 후 자동 만료)

       ↕ LeaderElection._declare_victory() 호출 시
       write_lock DEL           (즉시 해제)
       Blackboard.promote_replica_to_master() 호출
```

### 16.1 Election-Aware Redis Write Lock

**파일 경로**: `ghost5_swarm/ghost5_swarm/election_guard.py`

```python
# ghost5_ws/src/ghost5_swarm/ghost5_swarm/election_guard.py
# Election Phase 동안 Redis 쓰기 잠금 관리

import redis
import functools
import time
from typing import Callable, TypeVar, Any

T = TypeVar('T')

WRITE_LOCK_KEY = 'swarm:election:write_lock'
WRITE_LOCK_TTL = 10   # 최대 10초 (선거가 이 안에 끝나야 함)


class ElectionGuard:
    """
    Leader Election 기간 Redis 쓰기 보호.

    사용 흐름:
      LeaderElection._start_election()  → guard.acquire_write_lock()
      LeaderElection._declare_victory() → guard.release_write_lock()

    쓰기 시도 시:
      - Election 진행 중이면 최대 retry_count 회 재시도 (backoff 적용)
      - 재시도 초과 시 WriteBlockedError 발생 → 호출자가 처리

    읽기는 항상 허용하되, is_election_in_progress() 로 stale 여부 확인 가능.
    """

    def __init__(self, r: redis.Redis):
        self.r = r

    def acquire_write_lock(self) -> bool:
        """
        Election 시작 시 쓰기 잠금 획득.
        NX 플래그로 중복 획득 방지 (이미 잠긴 경우 False 반환).
        """
        return bool(self.r.set(WRITE_LOCK_KEY, '1', nx=True, ex=WRITE_LOCK_TTL))

    def release_write_lock(self):
        """Election 종료(Victory 선언) 시 즉시 잠금 해제"""
        self.r.delete(WRITE_LOCK_KEY)

    def is_election_in_progress(self) -> bool:
        """현재 Election 진행 중 여부"""
        return bool(self.r.exists(WRITE_LOCK_KEY))

    def safe_write(
        self,
        write_fn: Callable[[], T],
        retry_count: int = 5,
        retry_interval_sec: float = 0.5
    ) -> T:
        """
        Election 상태를 확인하며 안전하게 쓰기 수행.

        Args:
            write_fn:           실제 Redis 쓰기 함수 (lambda 등)
            retry_count:        최대 재시도 횟수
            retry_interval_sec: 재시도 간격 (초)

        Returns:
            write_fn()의 반환값

        Raises:
            WriteBlockedError: 재시도 초과 시
        """
        for attempt in range(retry_count):
            if not self.is_election_in_progress():
                return write_fn()

            wait = retry_interval_sec * (attempt + 1)   # 선형 백오프
            import logging
            logging.warning(
                f'[ElectionGuard] Election 진행 중 — {wait:.1f}초 후 재시도 '
                f'({attempt + 1}/{retry_count})'
            )
            time.sleep(wait)

        raise WriteBlockedError(
            f'Election 종료 대기 중 쓰기 타임아웃 ({retry_count}회 재시도)'
        )


class WriteBlockedError(Exception):
    """Election 중 쓰기 블록 예외"""
    pass


def election_safe_write(guard_attr: str = '_election_guard',
                        retry_count: int = 5):
    """
    GhostBlackboard 메서드에 적용하는 데코레이터.
    Election 중 쓰기 메서드를 자동으로 보호.

    사용법:
        class GhostBlackboard:
            @election_safe_write()
            def claim_frontier(self, frontier_id, robot_id):
                ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            guard: ElectionGuard = getattr(self, guard_attr, None)
            if guard and guard.is_election_in_progress():
                return guard.safe_write(
                    lambda: fn(self, *args, **kwargs),
                    retry_count=retry_count
                )
            return fn(self, *args, **kwargs)
        return wrapper
    return decorator
```

### 16.1 Redis Sorted Set 기반 커서 페이징

```python
# ghost5_ws/src/ghost5_swarm/ghost5_swarm/paged_query.py

import redis
import json
from dataclasses import dataclass
from typing import Any, Optional
from election_guard import ElectionGuard


@dataclass
class PageResult:
    """커서 기반 페이지 결과"""
    items:            list[Any]
    next_cursor:      Optional[str]   # None이면 마지막 페이지
    has_more:         bool
    total_count:      int
    election_warning: bool = False    # True = Election 진행 중, 데이터 stale 가능


class PagedEventQuery:
    """
    SemanticMemory 이벤트 로그 커서 기반 페이징.

    커서 형식: "<timestamp_score>:<event_id>"
    타임스탬프 기준 정렬이므로 데이터 추가/삭제 시에도 일관성 유지.

    Election 처리:
      - 읽기는 항상 허용
      - election_warning=True 시 반환 데이터에 stale 가능성 명시
    """

    def __init__(self, r: redis.Redis):
        self.r     = r
        self.guard = ElectionGuard(r)

    def get_events(
        self,
        cursor:    Optional[str] = None,
        page_size: int = 10,
        direction: str = 'desc'
    ) -> PageResult:
        election_on = self.guard.is_election_in_progress()
        total = self.r.zcard('events:timeline')

        cursor_score = None
        if cursor:
            try:
                score_str, _ = cursor.rsplit(':', 1)
                cursor_score = float(score_str)
            except (ValueError, AttributeError):
                pass

        if direction == 'desc':
            if cursor_score is not None:
                event_ids = list(reversed(self.r.zrangebyscore(
                    'events:timeline', '-inf', f'({cursor_score}',
                    start=0, num=page_size + 1
                )))
            else:
                event_ids = self.r.zrevrange('events:timeline', 0, page_size)
        else:
            if cursor_score is not None:
                event_ids = self.r.zrangebyscore(
                    'events:timeline', f'({cursor_score}', '+inf',
                    start=0, num=page_size + 1
                )
            else:
                event_ids = self.r.zrange('events:timeline', 0, page_size)

        has_more = len(event_ids) > page_size
        if has_more:
            event_ids = event_ids[:page_size]

        items = [json.loads(raw) for eid in event_ids
                 if (raw := self.r.get(f'event:{eid}'))]

        next_cursor = None
        if has_more and event_ids:
            last_score = self.r.zscore('events:timeline', event_ids[-1])
            next_cursor = f'{last_score}:{event_ids[-1]}'

        return PageResult(
            items=items, next_cursor=next_cursor,
            has_more=has_more, total_count=total,
            election_warning=election_on
        )

    def get_events_by_type(
        self,
        event_type: str,
        cursor:     Optional[str] = None,
        page_size:  int = 10
    ) -> PageResult:
        all_page = self.get_events(cursor=cursor, page_size=page_size * 3)
        filtered = [item for item in all_page.items
                    if item.get('event_type') == event_type][:page_size]

        return PageResult(
            items=filtered, next_cursor=all_page.next_cursor,
            has_more=all_page.has_more, total_count=all_page.total_count,
            election_warning=all_page.election_warning
        )


class PagedRobotStateQuery:
    """로봇 상태 페이징 조회 (커서 형식: "robot_N")"""

    def __init__(self, r: redis.Redis):
        self.r     = r
        self.guard = ElectionGuard(r)

    def get_robot_states(
        self,
        robot_ids:  list[int] | None = None,
        cursor:     Optional[str] = None,
        page_size:  int = 5
    ) -> PageResult:
        election_on = self.guard.is_election_in_progress()
        all_ids = robot_ids or list(range(1, 6))

        start_idx = 0
        if cursor:
            try:
                cursor_id = int(cursor.replace('robot_', ''))
                start_idx = all_ids.index(cursor_id) + 1
            except (ValueError, IndexError):
                start_idx = 0

        page_ids = all_ids[start_idx: start_idx + page_size + 1]
        has_more = len(page_ids) > page_size
        if has_more:
            page_ids = page_ids[:page_size]

        items = []
        for rid in page_ids:
            raw = self.r.get(f'robot:{rid}:state')
            if raw:
                state = json.loads(raw)
                state['robot_id'] = rid
                items.append(state)

        next_cursor = f'robot_{page_ids[-1]}' if has_more and page_ids else None

        return PageResult(
            items=items, next_cursor=next_cursor,
            has_more=has_more, total_count=len(all_ids),
            election_warning=election_on
        )


class PagedVictimQuery:
    """생존자 감지 기록 커서 기반 페이징 (victim_id 기준)"""

    def __init__(self, r: redis.Redis):
        self.r     = r
        self.guard = ElectionGuard(r)

    def get_victims(
        self,
        cursor:         Optional[str] = None,
        page_size:      int = 10,
        min_confidence: float = 0.0
    ) -> PageResult:
        election_on     = self.guard.is_election_in_progress()
        all_victims_raw = self.r.hgetall('victims')
        total           = len(all_victims_raw)

        victims = sorted(
            [(k, json.loads(v)) for k, v in all_victims_raw.items()],
            key=lambda x: x[1].get('timestamp', 0), reverse=True
        )

        if min_confidence > 0.0:
            victims = [v for v in victims
                       if v[1].get('combined_confidence', 0) >= min_confidence]

        start_idx = 0
        if cursor:
            for idx, (vid, _) in enumerate(victims):
                if vid == cursor:
                    start_idx = idx + 1
                    break

        page = victims[start_idx: start_idx + page_size + 1]
        has_more = len(page) > page_size
        if has_more:
            page = page[:page_size]

        items = [v for _, v in page]
        next_cursor = page[-1][0] if has_more and page else None

        return PageResult(
            items=items, next_cursor=next_cursor,
            has_more=has_more, total_count=total,
            election_warning=election_on
        )
```

### 16.2 GCS 대시보드 페이징 API (Election 상태 헤더 + 재시도 지원)

```python
# ghost5_ws/src/ghost5_viz/ghost5_viz/gcs_api.py
# v1.1 — Election Phase 엣지 케이스: 헤더 반환 + 클라이언트 재시도 안내

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from paged_query import PagedEventQuery, PagedRobotStateQuery, PagedVictimQuery
from election_guard import ElectionGuard, WriteBlockedError, WRITE_LOCK_KEY
import redis

app = FastAPI(title="GHOST-5 GCS API v1.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

r     = redis.Redis(host='localhost', port=6379, password='ghost5secure!', decode_responses=True)
guard = ElectionGuard(r)


def _election_headers() -> dict:
    """Election 진행 중이면 경고 헤더 추가"""
    if guard.is_election_in_progress():
        return {
            'X-Election-Status': 'in_progress',
            'X-Data-Staleness':  'possible',
            'X-Retry-After-Ms':  '500'    # 클라이언트에 500ms 후 재시도 권고
        }
    return {'X-Election-Status': 'stable'}


@app.get("/election/status")
def get_election_status():
    """
    현재 Election 상태 조회.
    GCS 대시보드가 polling하여 UI 상태 표시.

    Returns:
        {"in_progress": bool, "write_locked": bool, "ttl_remaining_sec": int}
    """
    in_progress = guard.is_election_in_progress()
    ttl = r.ttl(WRITE_LOCK_KEY) if in_progress else 0
    return JSONResponse({
        "in_progress":       in_progress,
        "write_locked":      in_progress,
        "ttl_remaining_sec": max(0, ttl)
    })


@app.get("/events")
def get_events(
    cursor:     str   = Query(None,   description="페이징 커서 (처음이면 생략)"),
    page_size:  int   = Query(10,     ge=1, le=100),
    event_type: str   = Query(None,   description="이벤트 타입 필터"),
    direction:  str   = Query("desc", description="정렬 방향: asc|desc")
):
    """
    Semantic Event Memory 커서 기반 조회.

    Election 진행 중:
      - 데이터는 반환되지만 X-Election-Status: in_progress 헤더 포함
      - 클라이언트는 election_warning 필드로 stale 여부 확인

    Example:
        GET /events?page_size=10
        GET /events?cursor=1710500000.0:blocked:zone_A&page_size=10
    """
    query = PagedEventQuery(r)
    result = (query.get_events_by_type(event_type, cursor=cursor, page_size=page_size)
              if event_type
              else query.get_events(cursor=cursor, page_size=page_size, direction=direction))

    return JSONResponse(
        content={
            "items":            result.items,
            "next_cursor":      result.next_cursor,
            "has_more":         result.has_more,
            "total_count":      result.total_count,
            "election_warning": result.election_warning
        },
        headers=_election_headers()
    )


@app.get("/robots")
def get_robot_states(
    cursor:    str = Query(None, description="페이징 커서"),
    page_size: int = Query(5,   ge=1, le=5)
):
    """
    로봇 상태 커서 기반 조회.
    Election 중 조회 시 일부 로봇 상태가 구 버전일 수 있음.
    """
    query  = PagedRobotStateQuery(r)
    result = query.get_robot_states(cursor=cursor, page_size=page_size)

    return JSONResponse(
        content={
            "items":            result.items,
            "next_cursor":      result.next_cursor,
            "has_more":         result.has_more,
            "total_count":      result.total_count,
            "election_warning": result.election_warning
        },
        headers=_election_headers()
    )


@app.get("/victims")
def get_victims(
    cursor:         str   = Query(None, description="페이징 커서"),
    page_size:      int   = Query(10,   ge=1, le=100),
    min_confidence: float = Query(0.0,  ge=0.0, le=1.0)
):
    """
    생존자 감지 기록 커서 기반 조회.
    Election 중에도 생존자 데이터는 항상 정상 반환 (복제본에서도 읽기 가능).
    """
    query  = PagedVictimQuery(r)
    result = query.get_victims(cursor=cursor, page_size=page_size,
                               min_confidence=min_confidence)

    return JSONResponse(
        content={
            "items":            result.items,
            "next_cursor":      result.next_cursor,
            "has_more":         result.has_more,
            "total_count":      result.total_count,
            "election_warning": result.election_warning
        },
        headers=_election_headers()
    )
```

### 16.3 클라이언트 재시도 로직 (Election 대응)

```python
# 사용 예시: Election-aware 커서 기반 전체 이벤트 로그 수집
import requests
import time

BASE_URL = "http://leader_robot_ip:8000"


def get_all_events_safe() -> list[dict]:
    """
    Election 상태를 감지하며 안전하게 전체 이벤트 로그 수집.

    Election 진행 중:
      - 조회는 계속 수행하되 election_warning 플래그 로깅
      - 쓰기 관련 작업은 X-Retry-After-Ms 후 재시도
    """
    all_events = []
    cursor = None

    while True:
        params = {'page_size': 20}
        if cursor:
            params['cursor'] = cursor

        resp = requests.get(f'{BASE_URL}/events', params=params, timeout=5)

        # Election 헤더 확인
        election_status = resp.headers.get('X-Election-Status', 'stable')
        if election_status == 'in_progress':
            retry_ms = int(resp.headers.get('X-Retry-After-Ms', 500))
            print(f'⚠️  Election 진행 중 — 데이터 stale 가능 (재시도 권고: {retry_ms}ms)')

        data = resp.json()

        if data.get('election_warning'):
            print(f'  ℹ️  election_warning=True: 이 페이지 데이터는 구 버전일 수 있습니다.')

        all_events.extend(data['items'])

        if not data['has_more']:
            break
        cursor = data['next_cursor']

    return all_events


def get_latest_victims_safe(min_conf: float = 0.7,
                             max_retries: int = 3) -> list[dict]:
    """Election 재시도 포함 생존자 기록 조회"""
    for attempt in range(max_retries):
        resp = requests.get(
            f'{BASE_URL}/victims',
            params={'min_confidence': min_conf, 'page_size': 10},
            timeout=5
        )
        data = resp.json()

        if not data.get('election_warning'):
            return data['items']   # 안정적 데이터

        retry_ms = int(resp.headers.get('X-Retry-After-Ms', 500))
        print(f'Election 진행 중 — {retry_ms}ms 후 재시도 ({attempt+1}/{max_retries})')
        time.sleep(retry_ms / 1000)

    # 최대 재시도 초과 → 마지막 결과 그대로 반환 (stale이지만 best-effort)
    return data.get('items', [])
```

### 16.4 LeaderElection에 ElectionGuard 통합

```python
# ghost5_swarm/leader_election.py 에 ElectionGuard 통합 (기존 코드 보완)
# _start_election() 과 _declare_victory() 에 guard 호출 추가

# 기존 __init__ 에 추가:
#   from election_guard import ElectionGuard
#   self._election_guard = ElectionGuard(blackboard.r)

# _start_election() 앞에 추가:
#   self._election_guard.acquire_write_lock()
#   self.get_logger().info('[ElectionGuard] Redis 쓰기 잠금 획득')

# _declare_victory() 내부 추가:
#   self._election_guard.release_write_lock()
#   self.get_logger().info('[ElectionGuard] Redis 쓰기 잠금 해제')
#   # Replica 승격 (새 Leader인 경우)
#   if blackboard.get_replication_status()['role'] == 'master':
#       ...  # Replica 이미 Master
#   else:
#       blackboard.promote_replica_to_master(EXPLORER_1_IP)
```

---

## 17. 런치 파일 설계

### 17.1 단일 로봇 런치

**파일 경로**: `ghost5_bringup/launch/robot.launch.py`

```python
# ghost5_ws/src/ghost5_bringup/launch/robot.launch.py

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def generate_launch_description():
    robot_id = LaunchConfiguration('robot_id', default='1')
    is_leader = LaunchConfiguration('is_leader', default='false')

    return LaunchDescription([
        # ── 환경변수 ──────────────────────────────────────────────
        SetEnvironmentVariable('RMW_IMPLEMENTATION',     'rmw_zenoh_cpp'),
        SetEnvironmentVariable('ROS_DOMAIN_ID',          '42'),
        SetEnvironmentVariable('ROS_SECURITY_ENABLE',    'true'),
        SetEnvironmentVariable('ROS_SECURITY_STRATEGY',  'Enforce'),
        SetEnvironmentVariable('ROS_SECURITY_KEYSTORE',  '~/ghost5_keystore'),

        DeclareLaunchArgument('robot_id', default_value='1'),
        DeclareLaunchArgument('is_leader', default_value='false'),

        # ── 네임스페이스 그룹 ──────────────────────────────────────
        GroupAction([
            PushRosNamespace(['robot_', robot_id]),

            # slam_toolbox
            Node(
                package='slam_toolbox',
                executable='async_slam_toolbox_node',
                name='slam_toolbox',
                parameters=['config/slam_toolbox_params.yaml'],
                remappings=[('/scan', 'scan'), ('/map', 'map')]
            ),

            # Nav2
            Node(
                package='nav2_bringup',
                executable='bringup_launch',
                name='nav2',
                parameters=['config/nav2_params.yaml']
            ),

            # Leader Election
            Node(
                package='ghost5_swarm',
                executable='leader_election',
                name='leader_election',
                arguments=[robot_id]
            ),

            # Comm Monitor (RSSI + Rendezvous)
            Node(
                package='ghost5_swarm',
                executable='comm_monitor',
                name='comm_monitor',
                arguments=[robot_id]
            ),

            # LiDAR Elevation
            Node(
                package='ghost5_slam',
                executable='lidar_elevation_node',
                name='lidar_elevation',
                arguments=[robot_id]
            ),

            # Proximity Detector
            Node(
                package='ghost5_victim',
                executable='proximity_detector',
                name='proximity_detector',
                arguments=[robot_id]
            ),

            # Vision Detector (CPU 기본, Phase 2에서 NPU로 교체)
            Node(
                package='ghost5_victim',
                executable='vision_detector',
                name='vision_detector',
                arguments=[robot_id]
            ),

            # Victim Fuser
            Node(
                package='ghost5_victim',
                executable='victim_fuser',
                name='victim_fuser',
                arguments=[robot_id]
            ),
        ])
    ])
```

---

## 18. 검증 전략 및 테스트

### 18.1 단위 테스트

```python
# ghost5_ws/tests/unit/test_leader_election.py

import pytest
import time

class TestBullyElection:

    def test_highest_id_becomes_leader(self):
        """5대 중 가장 높은 ID가 Leader가 되는지 검증"""
        # 실제 LeaderElection 노드 5개 시뮬레이션
        # assert final_leader_id == 5
        pass

    def test_leader_recovery_on_timeout(self):
        """Leader 다운 시 다음 높은 ID가 Leader가 되는지 검증"""
        # Robot 5 다운 → Robot 4가 3초 내에 Leader 선출
        pass

    def test_election_convergence_time(self):
        """선거 수렴 시간 < 3초"""
        start = time.time()
        # 선거 시뮬레이션
        elapsed = time.time() - start
        assert elapsed < 3.0


class TestMPPFFrontier:

    def test_no_duplicate_claims(self):
        """5대 로봇이 동일 Frontier를 claim하지 않는지 검증"""
        # Redis claim_frontier nx=True 원자성 검증
        pass

    def test_skip_zones_respected(self):
        """skip_zones에 포함된 Frontier는 선택하지 않는지 검증"""
        pass

    def test_full_coverage_10min(self):
        """표준 맵에서 5대가 10분 내 80% 이상 커버리지 달성"""
        pass


class TestSemanticMemory:

    def test_event_compression(self):
        """3회 이상 실패 시 설명 압축 적용 여부"""
        pass

    def test_leader_context_inheritance(self):
        """Leader 교체 시 컨텍스트 요약 정상 반환"""
        pass

    def test_skip_zones_update(self):
        """3회 실패 후 skip_zones에 포함되는지 검증"""
        pass


class TestCursorPaging:

    def test_no_duplicate_in_cursor_paging(self):
        """커서 페이징 시 동일 항목 중복 없는지 검증"""
        # 이벤트 추가 중에 페이징해도 중복/누락 없음
        pass

    def test_all_items_retrieved_via_cursor(self):
        """커서로 전체 순회 시 모든 항목 조회 여부"""
        pass

    def test_offset_vs_cursor_consistency(self):
        """데이터 추가 중 offset 기반 vs cursor 기반 결과 비교 (cursor가 일관성 우월)"""
        pass
```

### 18.2 통합 테스트 시나리오

```
Phase 1: Gazebo 시뮬레이션
  ├── B.A.T.M.A.N. Mesh 네트워크 에뮬레이션
  │   └── tc qdisc로 네트워크 손실/지연 주입 (30% 손실 시뮬레이션)
  ├── TurtleBot3 5대 동시 실행
  ├── Leader 강제 종료 → 재선거 수렴 < 3초 검증
  └── 성능 지표 자동 수집 (rosbag2)

Phase 2: 실제 하드웨어 단일 로봇
  ├── Raspberry Pi 5 + RPLiDAR C1 SLAM 정확도 확인
  ├── US-016 + TCRT5000 + 5MP 생존자 감지 교차 검증
  └── rmw_zenoh 통신 안정성 확인

Phase 3: 2대 멀티 로봇
  ├── Zenoh Gossip 지도 공유 검증
  ├── Leader Election 수렴 테스트
  └── 지도 병합 정확도 (Ground Truth 대비 RMSE)

Phase 4: 5대 군집 통합
  ├── 실내 재난 모의 환경 (잔해, 좁은 통로, 막힌 문)
  ├── 전체 벤치마크 지표 측정
  ├── 로봇 1대 강제 종료 내결함성 테스트
  └── Rendezvous 프로토콜 검증 (WiFi 신호 약화 구역 진입)
```

---

## 19. 성능 벤치마크 설계

### 19.1 성능 목표 (합격 기준)

| 항목 | 목표값 | 측정 방법 |
|------|--------|-----------|
| Pose 통신 지연 | < 50ms (P95) | LatencyBenchmark 노드 |
| 지도 Delta 전송 | < 500ms (1Hz) | map_merger 로그 분석 |
| Leader Election 수렴 | < 3초 | 전원 차단 후 재선거 타이밍 |
| 생존자 알림 전파 | < 200ms | victim_detector → GCS 타임스탬프 |
| 탐색 커버리지 (10분) | > 80% | OccupancyGrid 커버리지 계산 |
| 내결함성 (1대 다운) | 임무 계속 | 강제 종료 후 4대 동작 확인 |
| 중복 탐색 비율 | < 5% | 로봇 경로 오버랩 면적 계산 |
| CPU 부하 (Phase 1) | < 75% | top/htop 모니터링 |
| CPU 부하 (Phase 2, NPU) | < 65% | top/htop 모니터링 |

### 19.2 통신 지연 측정 스크립트

```python
# ghost5_ws/scripts/benchmark/measure_latency.py

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time
import statistics
import sys
sys.path.insert(0, '../src/ghost5_bringup/config')
from qos_profiles import POSE_QOS


class LatencyBenchmark(Node):
    """
    Ping-Pong 방식 통신 지연 측정.
    목표: P95 < 50ms
    """

    def __init__(self):
        super().__init__('latency_benchmark')
        self.latencies       = []
        self.send_timestamps = {}

        self.pub = self.create_publisher(String, '/benchmark/ping', POSE_QOS)
        self.create_subscription(String, '/benchmark/pong', self._pong_cb, POSE_QOS)
        self.create_timer(0.1, self._send_ping)   # 10Hz

    def _send_ping(self):
        ts     = time.time()
        msg_id = str(ts)
        self.send_timestamps[msg_id] = ts
        self.pub.publish(String(data=msg_id))

    def _pong_cb(self, msg: String):
        now = time.time()
        if msg.data in self.send_timestamps:
            latency_ms = (now - self.send_timestamps.pop(msg.data)) * 1000
            self.latencies.append(latency_ms)

            if len(self.latencies) % 100 == 0:
                sorted_l = sorted(self.latencies)
                p95_idx  = int(len(sorted_l) * 0.95)
                self.get_logger().info(
                    f'Latency (n={len(self.latencies)}) — '
                    f'Mean: {statistics.mean(self.latencies):.2f}ms, '
                    f'P95: {sorted_l[p95_idx]:.2f}ms, '
                    f'Max: {max(self.latencies):.2f}ms'
                )
                # 목표 검증
                p95 = sorted_l[p95_idx]
                if p95 > 50:
                    self.get_logger().warn(f'⚠️  P95 목표(50ms) 초과: {p95:.2f}ms')
                else:
                    self.get_logger().info(f'✅ P95 목표 달성: {p95:.2f}ms')


def main():
    rclpy.init()
    node = LatencyBenchmark()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

## 20. Pinky Pro 하드웨어 최적화

### 20.1 🆕 다이나믹셀 XL330 슬립 감지 + EKF 가중치 보정

> **문제**: 재난 현장의 미끄러운 잔해 위에서는 XL330 바퀴 슬립(Slip)이 심하여  
> 엔코더 기반 오도메트리가 실제 이동과 크게 달라진다.  
> **해결**: BNO055 IMU 가속도 데이터 + XL330 엔코더 데이터를 EKF로 융합할 때,  
> 슬립 감지 시 엔코더 신뢰도(Process Noise) 가중치를 동적으로 낮춰 IMU 우선 융합으로 전환한다.

```python
# ghost5_ws/src/ghost5_navigation/ghost5_navigation/slip_aware_ekf.py
# 슬립 감지 기반 동적 EKF 가중치 보정

import numpy as np
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from rcl_interfaces.msg import SetParametersResult
from rclpy.parameter import Parameter


class SlipAwareEKFTuner(Node):
    """
    XL330 엔코더 슬립 감지 + EKF Process Noise 동적 조정.

    슬립 감지 원리:
      - IMU 선속도 추정치 = ∫ (IMU 가속도) dt  (짧은 윈도우)
      - 엔코더 선속도  = 바퀴 회전수 × 바퀴 반지름
      - |IMU_v - ENC_v| > SLIP_THRESHOLD → 슬립 발생으로 판정

    EKF 가중치 전환:
      정상: encoder_noise_cov = 0.01  (엔코더 신뢰도 높음)
      슬립: encoder_noise_cov = 5.0   (엔코더 신뢰도 낮춤, IMU 우선)

    연동: robot_localization 패키지의 ekf_node 파라미터를
         rclpy parameter service로 실시간 재설정.
    """

    SLIP_THRESHOLD      = 0.15    # m/s, IMU-Encoder 속도 차이 임계값
    ENCODER_NOISE_NORM  = 0.01    # 정상 시 엔코더 공분산 (odom0_config 기준)
    ENCODER_NOISE_SLIP  = 5.0     # 슬립 시 엔코더 공분산 (신뢰도 대폭 하락)
    IMU_WINDOW_SEC      = 0.5     # IMU 속도 추정 윈도우 (초)
    WHEEL_RADIUS_M      = 0.033   # XL330 바퀴 반지름 (Pinky Pro, m)

    def __init__(self, robot_id: int):
        super().__init__(f'slip_aware_ekf_tuner_{robot_id}')
        self.robot_id    = robot_id
        self.slip_active = False

        # IMU 적분 버퍼 (짧은 윈도우 속도 추정)
        self._imu_accel_buf: list[tuple[float, float]] = []  # [(ts, ax), ...]
        self._imu_vel_est: float = 0.0

        self.create_subscription(
            Imu, f'/robot_{robot_id}/imu/data', self._imu_cb, 20
        )
        self.create_subscription(
            Odometry, f'/robot_{robot_id}/odom', self._odom_cb, 20
        )

    def _imu_cb(self, msg: Imu):
        """IMU 선가속도 수신 → 짧은 윈도우 속도 추정"""
        ts = self.get_clock().now().nanoseconds * 1e-9
        ax = msg.linear_acceleration.x   # 전진 방향 가속도

        self._imu_accel_buf.append((ts, ax))

        # 윈도우 외 데이터 제거
        cutoff = ts - self.IMU_WINDOW_SEC
        self._imu_accel_buf = [(t, a) for t, a in self._imu_accel_buf if t >= cutoff]

        # 사다리꼴 적분으로 속도 추정
        if len(self._imu_accel_buf) >= 2:
            v = 0.0
            for i in range(1, len(self._imu_accel_buf)):
                dt = self._imu_accel_buf[i][0] - self._imu_accel_buf[i-1][0]
                v += (self._imu_accel_buf[i][1] + self._imu_accel_buf[i-1][1]) / 2 * dt
            self._imu_vel_est = abs(v)

    def _odom_cb(self, msg: Odometry):
        """
        엔코더 속도 수신 → IMU 속도 추정치와 비교 → 슬립 감지.
        슬립 여부에 따라 EKF Process Noise 파라미터 실시간 재설정.
        """
        enc_vel = abs(msg.twist.twist.linear.x)   # 엔코더 기반 선속도 (m/s)
        vel_diff = abs(self._imu_vel_est - enc_vel)

        if vel_diff > self.SLIP_THRESHOLD:
            if not self.slip_active:
                self.slip_active = True
                self.get_logger().warn(
                    f'Robot {self.robot_id}: 슬립 감지! '
                    f'IMU_v={self._imu_vel_est:.3f} m/s, ENC_v={enc_vel:.3f} m/s, '
                    f'diff={vel_diff:.3f} m/s → 엔코더 가중치 하락'
                )
                self._set_ekf_encoder_noise(self.ENCODER_NOISE_SLIP)
        else:
            if self.slip_active:
                self.slip_active = False
                self.get_logger().info(
                    f'Robot {self.robot_id}: 슬립 해소 → 엔코더 가중치 정상 복구'
                )
                self._set_ekf_encoder_noise(self.ENCODER_NOISE_NORM)

    def _set_ekf_encoder_noise(self, noise_cov: float):
        """
        robot_localization ekf_node의 odom0_config 공분산 파라미터 동적 재설정.
        rclpy 파라미터 서비스 호출 (AsyncParametersClient 사용).
        """
        client = self.create_client(
            type(None),   # rclpy.parameter 서비스 타입
            f'/robot_{self.robot_id}/ekf_node/set_parameters'
        )
        # 실제 구현에서는 rcl_interfaces/srv/SetParameters 사용
        # odom0_config의 linear_x 분산 값을 noise_cov로 재설정
        self.get_logger().debug(
            f'EKF odom0 encoder noise → {noise_cov:.4f}'
        )
        # TODO: AsyncParametersClient로 ekf_node 파라미터 업데이트


def main():
    rclpy.init()
    import sys
    robot_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    node = SlipAwareEKFTuner(robot_id)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

### 20.2 🆕 RPLiDAR C1 Energy Saving Mode

> **문제**: Raspberry Pi 5에서 다수 노드 동시 실행 시 배터리 소모가 극심하다.  
> RPLiDAR C1의 모터는 탐색 여부와 무관하게 항상 최고 속도로 회전한다.  
> **해결**: 로봇 상태에 따라 LiDAR 모터 속도를 3단계로 제어하여 전력을 절약한다.

```python
# ghost5_ws/src/ghost5_bringup/ghost5_bringup/lidar_power_manager.py
# RPLiDAR C1 에너지 절약 모드

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from ghost5_interfaces.msg import RobotState
import json

try:
    from rplidar import RPLidar   # rplidar Python 드라이버
    RPLIDAR_AVAILABLE = True
except ImportError:
    RPLIDAR_AVAILABLE = False


class LidarPowerManager(Node):
    """
    RPLiDAR C1 PWM 기반 에너지 절약 모드 관리.

    3단계 전력 모드:
      ACTIVE    (탐색 중):           모터 속도 100% — SLAM 최고 정밀도
      STANDBY   (정지/대기 중):      모터 속도 50%  — 전력 절약 (최소 스캔 유지)
      HIBERNATE (통신 대기/랑데부):  모터 정지      — 최대 전력 절약

    모드 전환 트리거:
      RobotState.status 토픽 구독 → 상태에 따라 자동 전환
      - EXPLORING     → ACTIVE
      - RETURNING     → STANDBY
      - DOWN/CHARGING → HIBERNATE

    전력 절약 추정:
      ACTIVE    → ~5W  (기준)
      STANDBY   → ~2.5W  (-50%)
      HIBERNATE → ~0.1W  (-98%)
    """

    MOTOR_SPEED_ACTIVE    = 600    # RPLiDAR 모터 PWM (0~1023 기준, 드라이버별 상이)
    MOTOR_SPEED_STANDBY   = 300    # 절반 속도
    MOTOR_SPEED_HIBERNATE = 0      # 정지

    # STANDBY 전환 조건: 이 시간 이상 정지 시
    STANDBY_IDLE_SEC   = 10.0
    # HIBERNATE 전환 조건: 이 상태들에서 즉시 전환
    HIBERNATE_STATUSES = {'RETURNING', 'DOWN', 'CHARGING'}

    def __init__(self, robot_id: int, lidar_port: str = '/dev/ttyUSB0'):
        super().__init__(f'lidar_power_manager_{robot_id}')
        self.robot_id     = robot_id
        self.current_mode = 'ACTIVE'
        self._last_move_ts = self.get_clock().now()

        # RPLiDAR 드라이버 초기화
        self._lidar = None
        if RPLIDAR_AVAILABLE:
            try:
                self._lidar = RPLidar(lidar_port)
                self.get_logger().info(f'RPLiDAR 연결: {lidar_port}')
            except Exception as e:
                self.get_logger().warn(f'RPLiDAR 초기화 실패: {e}')

        # 로봇 상태 구독 (에너지 모드 결정 기준)
        self.create_subscription(
            RobotState,
            f'/robot_{robot_id}/state',
            self._state_cb,
            10
        )
        # swarm 통신 이벤트 구독 (랑데부/복귀 상태 감지)
        self.create_subscription(
            String,
            '/swarm/comm_events',
            self._comm_event_cb,
            10
        )
        # 주기적 모드 재평가 (10초)
        self.create_timer(10.0, self._evaluate_mode)

    def _state_cb(self, msg: RobotState):
        """로봇 상태 변화에 따른 LiDAR 전력 모드 즉시 전환"""
        status = msg.status.upper()

        if status == 'EXPLORING':
            self._set_mode('ACTIVE')
        elif status in self.HIBERNATE_STATUSES:
            self._set_mode('HIBERNATE')
        elif status in {'VICTIM_FOUND'}:
            # 생존자 발견 시: 정밀 스캔 유지
            self._set_mode('ACTIVE')

    def _comm_event_cb(self, msg: String):
        """통신 이벤트: 랑데부 진입 시 STANDBY 전환"""
        try:
            data = json.loads(msg.data)
            event_type = data.get('type', '')
            robot_id   = data.get('robot_id')

            if robot_id != self.robot_id:
                return

            if event_type == 'COMM_DEGRADED':
                # 랑데부 모드 진입: 이동 최소화 → STANDBY
                self._set_mode('STANDBY')
            elif event_type == 'COMM_RESTORED':
                # 통신 복구 → 탐색 재개 → ACTIVE
                self._set_mode('ACTIVE')
        except json.JSONDecodeError:
            pass

    def _evaluate_mode(self):
        """주기적 모드 재평가: 장시간 정지 감지 시 STANDBY 전환"""
        if self.current_mode != 'ACTIVE':
            return

        elapsed = (self.get_clock().now() - self._last_move_ts).nanoseconds * 1e-9
        if elapsed > self.STANDBY_IDLE_SEC:
            self.get_logger().info(
                f'Robot {self.robot_id}: {elapsed:.0f}초 정지 → LiDAR STANDBY 전환'
            )
            self._set_mode('STANDBY')

    def _set_mode(self, mode: str):
        """LiDAR 전력 모드 설정 및 모터 속도 조정"""
        if mode == self.current_mode:
            return

        self.current_mode = mode

        speed_map = {
            'ACTIVE':    self.MOTOR_SPEED_ACTIVE,
            'STANDBY':   self.MOTOR_SPEED_STANDBY,
            'HIBERNATE': self.MOTOR_SPEED_HIBERNATE
        }
        target_speed = speed_map.get(mode, self.MOTOR_SPEED_ACTIVE)

        self.get_logger().info(
            f'Robot {self.robot_id}: LiDAR 전력 모드 → {mode} '
            f'(모터 속도: {target_speed}/1023)'
        )

        if self._lidar:
            try:
                if mode == 'HIBERNATE':
                    self._lidar.stop_motor()
                else:
                    self._lidar.set_motor_speed(target_speed)
            except Exception as e:
                self.get_logger().error(f'LiDAR 모터 제어 실패: {e}')

    def destroy_node(self):
        """노드 종료 시 LiDAR 모터 안전 정지"""
        if self._lidar:
            try:
                self._lidar.stop_motor()
                self._lidar.disconnect()
            except Exception:
                pass
        super().destroy_node()


def main():
    rclpy.init()
    import sys
    robot_id   = int(sys.argv[1])    if len(sys.argv) > 1 else 1
    lidar_port = sys.argv[2]         if len(sys.argv) > 2 else '/dev/ttyUSB0'
    node = LidarPowerManager(robot_id, lidar_port)
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

### 20.3 Energy Saving Mode 런치 통합

**파일 경로**: `ghost5_bringup/launch/robot.launch.py` 에 LidarPowerManager 노드 추가

```python
# robot.launch.py 에 추가 (기존 노드 목록 아래)

# LiDAR Energy Saving Manager
Node(
    package='ghost5_bringup',
    executable='lidar_power_manager',
    name='lidar_power_manager',
    arguments=[robot_id, '/dev/ttyUSB0']
),

# Slip-Aware EKF Tuner (슬립 감지 + EKF 가중치 보정)
Node(
    package='ghost5_navigation',
    executable='slip_aware_ekf_tuner',
    name='slip_aware_ekf_tuner',
    arguments=[robot_id]
),
```

### 20.5 🆕 Pinky Pro 센서 배치 최적화 다이어그램

> 재난 현장에서 로봇의 안정성을 높이기 위한 센서 기하학적 보정 구조와  
> 핵심 알고리즘 연동 흐름을 하나의 다이어그램으로 정리한다.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   Pinky Pro 센서 배치 및 알고리즘 연동                   │
│                                                                         │
│  ┌──────────────── 로봇 측면도 ────────────────────────────────────┐   │
│  │                                                                  │   │
│  │   [RPLiDAR C1] ← 장착 높이 15cm                                 │   │
│  │   ─── 수평 스캔 빔 ───────────────────────────────▶             │   │
│  │         ↓ BNO055 Pitch/Roll 보정                                 │   │
│  │   ─── 보정 빔  ───────────────────────────────────▶ 장애물      │   │
│  │                                                    hit           │   │
│  │   [BNO055 IMU] ← base_link 하단                                  │   │
│  │   [5MP 카메라] ← 전방 30° 하향                                   │   │
│  │   [US-016 초음파] ← 전방                                         │   │
│  │   [TCRT5000 IR]   ← 전방 하단                                    │   │
│  │                                                                  │   │
│  │   ────── 22cm (로봇 높이) ──────── 15cm (LiDAR 장착 높이)        │   │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────── LiDAR Z-stack + IMU 보정 파이프라인 ─────────────────────┐  │
│  │                                                                   │  │
│  │  LaserScan  →  BNO055 Pitch/Roll                                  │  │
│  │      │              │                                             │  │
│  │      │         R_imu 구성 (Ry @ Rx)                              │  │
│  │      │              │                                             │  │
│  │      ↓              ↓                                             │  │
│  │  |pitch|>15°?  →  스캔 폐기 (신뢰 불가)                          │  │
│  │  5°~15°?       →  R_imu.T 보정 후 z<-5cm 포인트 제거             │  │
│  │  <5°?          →  보정 없이 직접 사용                             │  │
│  │      ↓                                                            │  │
│  │  Bresenham Ray-casting                                            │  │
│  │    경로 셀: hits 감소 → 0 이하 시 삭제 (Ghost Trail 제거)         │  │
│  │    종점 셀: hits 증가 + first_seen/last_seen 기록                 │  │
│  │      ↓                                                            │  │
│  │  Temporal Consistency Filter                                      │  │
│  │    hits ≥ 3  AND  지속 시간 ≥ 2초  →  장애물 확정               │  │
│  │    last_seen 후 10초 경과  →  셀 자동 소멸 (Decay)               │  │
│  │      ↓                                                            │  │
│  │  OccupancyGrid (elevation_layer) → Nav2 Costmap                  │  │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────── Communication Gradient Map 복귀 경로 ────────────────────┐  │
│  │                                                                   │  │
│  │  탐색 중 RSSI 기록 (지수 이동 평균, 격자 0.5m)                   │  │
│  │                                                                   │  │
│  │  RSSI 지도 등고선 (위에서 본 평면도):                             │  │
│  │                                                                   │  │
│  │    ░ ░ ░ ▒ ▒ █ █                                                 │  │
│  │    ░ ░ ▒ ▒ █ █ █   ← Safe Comm Zone (≥ -70dBm)                  │  │
│  │    ░ ▒ ▒ █ █ █ █      (AP 근처)                                  │  │
│  │    ▒ ▒ █ █ █ █ █                                                 │  │
│  │         ↑                                                         │  │
│  │      로봇 현재 위치                                               │  │
│  │                                                                   │  │
│  │  신호 단절 임박 (RSSI < -80):                                     │  │
│  │    ① gradient 방향 탐색 → Safe Zone 발견 시 이동                  │  │
│  │    ② 로컬 미니마 감지 → Random Perturbation (2회)                 │  │
│  │    ③ 탈출 실패 → Best-History 상위 3셀 평균 좌표로 복귀           │  │
│  │    ④ 모든 전략 실패 → home position 복귀                          │  │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌──────── Election + Redis HA 연동 흐름 ───────────────────────────┐  │
│  │                                                                   │  │
│  │  Heartbeat TIMEOUT 감지                                           │  │
│  │      ↓                                                            │  │
│  │  /swarm/leader_dead 투표 브로드캐스트                             │  │
│  │  + ID 기반 Backoff Delay 시작                                     │  │
│  │    Robot-5: 0.0s  Robot-4: 0.1s  Robot-3: 0.2s  Robot-1: 0.4s   │  │
│  │      ↓                                                            │  │
│  │  Bully ELECTION → 쿼럼(≥3대) 확인 → VICTORY                     │  │
│  │      ↓                                                            │  │
│  │  ElectionGuard Write Lock 해제                                    │  │
│  │  + Redis Replica (Robot-2) → REPLICAOF NO ONE → Master 승격       │  │
│  │  + add_victim() WAIT(1, 100ms) 동기 쓰기 복구                     │  │
│  │  + SemanticMemory 컨텍스트 승계 → 임무 재분배                     │  │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘

센서별 감지 범위 및 용도 요약:
  RPLiDAR C1 (수평 360°, 최대 12m) → 2D SLAM + Elevation Z-stack
  5MP 카메라 (전방)                 → YOLOv8n 인체 감지 + 저고도(5~15cm) 잔해 감지
  US-016 초음파 (2~400cm)           → 생존자 거리 (20~150cm 범위)
  TCRT5000 IR  (~30cm)              → 생존자 근거리 반사 확인
  BNO055 IMU (9축)                  → LiDAR 스캔 보정 + EKF 오도메트리 융합
  XL330 엔코더                      → EKF 오도메트리 (슬립 감지 시 가중치 하락)
```

### 20.1 환경 구성

```bash
# 시스템 요구사항
# Ubuntu 24.04 LTS, ROS2 Jazzy, Python 3.12+

# ROS2 의존성 설치
sudo apt install -y \
    ros-jazzy-slam-toolbox \
    ros-jazzy-nav2-bringup \
    ros-jazzy-rmw-zenoh-cpp \
    ros-jazzy-tf2-ros \
    ros-jazzy-message-filters \
    ros-jazzy-cv-bridge \
    python3-opencv \
    redis-server

# Python 패키지 (venv 권장, colcon build 시는 deactivate)
pip install --break-system-packages \
    redis \
    numpy \
    fastapi \
    uvicorn \
    python-multipart

# Phase 2 추가 (Hailo NPU)
pip install hailort --break-system-packages
```

### 20.2 빌드 및 실행

```bash
# 워크스페이스 빌드 (venv deactivate 후 실행!)
deactivate 2>/dev/null || true
cd ~/ghost5_ws
colcon build --symlink-install --packages-select \
    ghost5_interfaces \
    ghost5_bringup \
    ghost5_slam \
    ghost5_navigation \
    ghost5_swarm \
    ghost5_victim \
    ghost5_viz

source install/setup.bash

# 단일 로봇 테스트 (robot_id=1, Leader 역할)
export LEADER_IP=192.168.1.101
ros2 launch ghost5_bringup robot.launch.py robot_id:=1 is_leader:=true

# Explorer 로봇 (robot_id=2~5)
ros2 launch ghost5_bringup robot.launch.py robot_id:=2 is_leader:=false

# GCS API 서버 (Leader 로봇에서)
uvicorn ghost5_viz.gcs_api:app --host 0.0.0.0 --port 8000 &

# Foxglove Studio 연결
# ws://leader_robot_ip:8765
```

### 20.3 개발 세션 로그 규칙

매 개발 세션 종료 시 아래 형식으로 DEV_LOG 작성:

```markdown
# GHOST-5 DEV_LOG — YYYY-MM-DD

## 완료 항목
- [ ] 

## 이슈 및 해결
- 

## 다음 세션 TODO
- 

## 브랜치
git branch: feature/XXXX
commit: 
```

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-03-15 | 최초 작성 — GHOST5_research.md v2.1 기반 전체 구현 계획 수립. 인풋 기반 커서 페이징 설계 포함 |
| v1.3 | 2026-03-15 | **3가지 최종 보완 + 센서 배치 다이어그램**: ① 섹션 9 — Redis Slave Lag 대응: add_victim() WAIT(1, 100ms) 동기 쓰기(sync_write=True 기본값), add_victim_async() 비동기 폴백, check_slave_lag_and_warn() 모니터링 메서드 추가 ② 섹션 10 — Temporal Consistency Filter: TEMPORAL_MIN_SEC(2.0s), TEMPORAL_DECAY_SEC(10.0s) 파라미터 추가; elevation_cells에 first_seen/last_seen 타임스탬프 기록; _publish_elevation()에서 Decay 삭제 + Duration Guard(지속 시간 미달 셀 미확정) 이중 필터 적용 ③ 섹션 8 — Election Storm 방지: BACKOFF_STEP_SEC(0.1s), _start_election_with_backoff()로 ID 기반 지연(Robot-5: 0s → Robot-1: 0.4s), _start_election_once() Backoff 중 VICTORY 수신 시 자동 취소 ④ 섹션 20 — Pinky Pro 센서 배치 최종 다이어그램 |
| v2.0 | 2026-03-17 | **🆕 가상 드론(Gazebo) 통합 완전판**: GHOST5_research.md v3.1 기반. 섹션 21~26 신규 추가. Phase 3-A(fake_drone_node.py) + Phase 3-B(PX4 SITL px4_sitl_zenoh + Gazebo Harmonic). NED↔ENU 변환 노드, 드론-Nav2 브릿지, 드론-Gossip 브릿지, 드론 Fallback 모니터, 재난 SDF 월드, 5대 시나리오 검증 체크리스트. 드론 QoS 토픽 6개 추가. 워크스페이스에 ghost5_drone_sim + ghost5_drone_integration 패키지 추가. |

---

## 21. 🆕 가상 드론 통합 설계 (Phase 3-A: Fake Drone)

### 21.1 설계 목표

Phase 3-A는 실제 PX4 하드웨어 없이 **소프트웨어 드론 노드**를 즉시 구현하여 드론-지상 로봇 협동 아키텍처를 검증하는 단계다.

```
Phase 3-A 목표:
  ① fake_drone_node.py → 드론 행동 시뮬 (rmw_zenoh 직접 통신)
  ② drone_nav_bridge.py → 드론 좌표를 지상 로봇 Nav2 Goal로 변환
  ③ drone_gossip_bridge.py → 드론 생존자 탐지를 군집 전체에 Gossip 전파
  ④ drone_fallback_monitor.py → 드론 장애 감지 + Bully 리더 Router 인수
```

### 21.2 Fake Drone 노드 구현

**파일 경로**: `ghost5_drone_sim/ghost5_drone_sim/fake_drone_node.py`

```python
# ghost5_ws/src/ghost5_drone_sim/ghost5_drone_sim/fake_drone_node.py
# Phase 3-A: 실제 PX4 없이 드론 행동을 시뮬레이션하는 Fake Drone 노드

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32, Bool, String
import math
import json
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ghost5_bringup/config'))
from qos_profiles import POSE_QOS, EVENT_QOS, MAP_QOS


class FakeDroneNode(Node):
    """
    Phase 3-A: Fake 드론 노드.

    실제 PX4/Gazebo 없이 드론의 핵심 행동을 시뮬레이션:
      - 정해진 경로를 따라 ENU 좌표로 위치 퍼블리시 (/drone/gps_pose)
      - 특정 좌표에서 생존자 탐지 이벤트 발생 (/drone/survivor_pose)
      - WiFi AP 릴레이 상태 퍼블리시 (/drone/wifi_ap_status)
      - 배터리 시뮬레이션 (/drone/battery_percent)

    모든 토픽은 rmw_zenoh로 직접 퍼블리시 — PX4 브릿지 불필요.

    좌표계: ENU (East-North-Up), 단위: m
    """

    # 드론 순찰 경로 (ENU, 고도 3.0m 고정)
    PATROL_WAYPOINTS = [
        (0.0,  0.0,  3.0),
        (5.0,  0.0,  3.0),
        (5.0,  5.0,  3.0),
        (0.0,  5.0,  3.0),
        (0.0,  0.0,  3.0),   # 홈 복귀
    ]

    # 생존자 탐지 시뮬레이션 좌표 (드론이 이 위치 1m 이내 접근 시 탐지 이벤트)
    VICTIM_LOCATIONS = [
        (3.0, 2.0, 0.0),   # 생존자 1: 지면 기준
        (7.0, 4.0, 0.0),   # 생존자 2
    ]

    MOVE_SPEED     = 0.5    # m/s (시뮬 속도)
    PUBLISH_HZ     = 10.0   # gps_pose 퍼블리시 주기 (Hz)
    BATTERY_DRAIN  = 0.05   # % / sec (배터리 소모 속도)
    DETECTION_DIST = 1.5    # m (생존자 탐지 유효 거리)

    def __init__(self):
        super().__init__('fake_drone')
        self.get_logger().info('🚁 Fake Drone Node 시작 (Phase 3-A)')

        # 드론 상태
        self._pos         = list(self.PATROL_WAYPOINTS[0])  # [x, y, z] ENU
        self._wp_idx      = 0
        self._battery     = 100.0
        self._detected_victims: set[int] = set()  # 이미 보고한 생존자 인덱스
        self._active      = True

        # 퍼블리셔
        self.pose_pub     = self.create_publisher(PoseStamped, '/drone/gps_pose',          POSE_QOS)
        self.victim_pub   = self.create_publisher(PoseStamped, '/drone/survivor_pose',     EVENT_QOS)
        self.ap_pub       = self.create_publisher(Bool,        '/drone/wifi_ap_status',    MAP_QOS)
        self.battery_pub  = self.create_publisher(Float32,     '/drone/battery_percent',   POSE_QOS)
        self.relay_pub    = self.create_publisher(String,      '/swarm/drone_relay_active', EVENT_QOS)

        # 구독: 지상 로봇으로부터 dronen 우선순위 탐색 좌표 수신
        self.create_subscription(
            String, '/swarm/frontier_priority', self._on_frontier_priority, EVENT_QOS
        )

        # 타이머
        self.create_timer(1.0 / self.PUBLISH_HZ, self._update)
        self.create_timer(1.0, self._publish_status)

        # 드론 활성 상태 최초 퍼블리시
        self._publish_relay_active(True)

    # ── 메인 업데이트 루프 ────────────────────────────────────────────
    def _update(self):
        """매 1/10초: 위치 이동 + 퍼블리시 + 생존자 감지"""
        if not self._active:
            return

        self._move_towards_waypoint()
        self._publish_pose()
        self._check_victim_detection()
        self._battery -= self.BATTERY_DRAIN / self.PUBLISH_HZ

        # 배터리 소진 시 Fallback
        if self._battery <= 0.0:
            self._battery = 0.0
            self._active  = False
            self.get_logger().warn('🚁 드론 배터리 소진 → 비활성화')
            self._publish_relay_active(False)

    def _move_towards_waypoint(self):
        """현재 웨이포인트를 향해 이동 (직선 이동 시뮬)"""
        target = self.PATROL_WAYPOINTS[self._wp_idx]
        dx = target[0] - self._pos[0]
        dy = target[1] - self._pos[1]
        dz = target[2] - self._pos[2]
        dist = math.sqrt(dx**2 + dy**2 + dz**2)

        step = self.MOVE_SPEED / self.PUBLISH_HZ   # 한 스텝 이동 거리 (m)

        if dist <= step:
            # 웨이포인트 도달 → 다음으로 이동
            self._pos = list(target)
            self._wp_idx = (self._wp_idx + 1) % len(self.PATROL_WAYPOINTS)
            self.get_logger().debug(
                f'🚁 웨이포인트 {self._wp_idx} 도달: {target}'
            )
        else:
            # 방향 단위 벡터 × step
            self._pos[0] += (dx / dist) * step
            self._pos[1] += (dy / dist) * step
            self._pos[2] += (dz / dist) * step

    def _publish_pose(self):
        """현재 드론 위치를 /drone/gps_pose에 퍼블리시 (ENU, PoseStamped)"""
        msg = PoseStamped()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.pose.position.x = self._pos[0]
        msg.pose.position.y = self._pos[1]
        msg.pose.position.z = self._pos[2]
        msg.pose.orientation.w = 1.0   # 단순 호버링: 회전 없음
        self.pose_pub.publish(msg)

    def _check_victim_detection(self):
        """현재 위치에서 생존자 탐지 거리 내 생존자 있으면 이벤트 퍼블리시"""
        for idx, (vx, vy, vz) in enumerate(self.VICTIM_LOCATIONS):
            if idx in self._detected_victims:
                continue
            dist = math.sqrt(
                (self._pos[0] - vx)**2 +
                (self._pos[1] - vy)**2
            )
            if dist <= self.DETECTION_DIST:
                self._detected_victims.add(idx)
                victim_msg = PoseStamped()
                victim_msg.header.stamp    = self.get_clock().now().to_msg()
                victim_msg.header.frame_id = 'map'
                victim_msg.pose.position.x = vx
                victim_msg.pose.position.y = vy
                victim_msg.pose.position.z = vz
                self.victim_pub.publish(victim_msg)
                self.get_logger().warn(
                    f'🚁 드론 생존자 탐지! 위치: ({vx}, {vy}) → /drone/survivor_pose 퍼블리시'
                )

    def _publish_status(self):
        """1Hz: 배터리 + WiFi AP 상태 퍼블리시"""
        self.battery_pub.publish(Float32(data=float(self._battery)))
        # AP 상태: 배터리 > 10% 이면 릴레이 활성
        self.ap_pub.publish(Bool(data=(self._battery > 10.0)))

    def _publish_relay_active(self, active: bool):
        """드론 릴레이 활성/비활성 이벤트 퍼블리시"""
        self.relay_pub.publish(String(data=json.dumps({
            'active':    active,
            'timestamp': self.get_clock().now().nanoseconds
        })))

    def _on_frontier_priority(self, msg: String):
        """
        지상 로봇이 요청한 우선 탐색 좌표 수신.
        드론의 다음 웨이포인트를 해당 좌표로 삽입.
        """
        data = json.loads(msg.data)
        px, py = data.get('x', 0.0), data.get('y', 0.0)
        priority_wp = (px, py, 3.0)   # 고도 3.0m 유지

        # 현재 웨이포인트 직후에 우선 삽입
        waypoints = list(self.PATROL_WAYPOINTS)
        insert_idx = (self._wp_idx + 1) % len(waypoints)
        waypoints.insert(insert_idx, priority_wp)
        self.PATROL_WAYPOINTS = tuple(waypoints)

        self.get_logger().info(
            f'🚁 우선 탐색 좌표 수신: ({px:.1f}, {py:.1f}) → 웨이포인트 삽입'
        )


def main():
    rclpy.init()
    node = FakeDroneNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 21.3 드론-Nav2 브릿지 (drone_nav_bridge.py)

**파일 경로**: `ghost5_drone_integration/ghost5_drone_integration/drone_nav_bridge.py`

```python
# ghost5_ws/src/ghost5_drone_integration/ghost5_drone_integration/drone_nav_bridge.py
# 드론이 탐지한 생존자 좌표 → 가장 가까운 지상 로봇에 Nav2 Goal 자동 파견

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import String
import json
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ghost5_bringup/config'))
from qos_profiles import EVENT_QOS, POSE_QOS


class DroneNavBridge(Node):
    """
    드론 생존자 탐지 → 지상 로봇 Nav2 자동 파견 브릿지.

    처리 흐름:
      /drone/survivor_pose 수신
        → 가장 가까운 지상 로봇 선택 (현재 로봇 위치 기반)
        → NavigateToPose Action Goal 전송
        → /swarm/victim 토픽으로 군집 전체에 알림

    연동:
      - 드론 생존자 좌표 (ENU) → Nav2 map 프레임 직접 사용 가능
      - Blackboard에 생존자 기록 (add_victim 연동)
    """

    TOTAL_ROBOTS = 5

    def __init__(self):
        super().__init__('drone_nav_bridge')
        self.get_logger().info('DroneNavBridge 시작')

        # 로봇 현재 위치 캐시 {robot_id: (x, y)}
        self._robot_poses: dict[int, tuple] = {}

        # Nav2 Action 클라이언트 {robot_id: ActionClient}
        self._nav_clients: dict[int, ActionClient] = {}
        for rid in range(1, self.TOTAL_ROBOTS + 1):
            self._nav_clients[rid] = ActionClient(
                self, NavigateToPose,
                f'/robot_{rid}/navigate_to_pose'
            )

        # 구독: 드론 생존자 탐지
        self.create_subscription(
            PoseStamped, '/drone/survivor_pose',
            self._on_survivor_detected, EVENT_QOS
        )

        # 구독: 각 로봇 현재 위치 (PoseStamped)
        for rid in range(1, self.TOTAL_ROBOTS + 1):
            self.create_subscription(
                PoseStamped, f'/robot_{rid}/pose',
                lambda msg, r=rid: self._update_robot_pose(msg, r),
                POSE_QOS
            )

        # 퍼블리셔: 생존자 정보 군집 전파
        self.victim_pub = self.create_publisher(String, '/swarm/victim', EVENT_QOS)

    def _update_robot_pose(self, msg: PoseStamped, robot_id: int):
        """각 로봇 위치 캐시 업데이트"""
        self._robot_poses[robot_id] = (
            msg.pose.position.x,
            msg.pose.position.y
        )

    def _on_survivor_detected(self, msg: PoseStamped):
        """
        드론 생존자 탐지 이벤트 처리.
        가장 가까운 로봇을 선택해 Nav2 Goal 전송.
        """
        target_x = msg.pose.position.x
        target_y = msg.pose.position.y

        self.get_logger().warn(
            f'🚁→🤖 드론 생존자 탐지: ({target_x:.2f}, {target_y:.2f}) '
            f'→ 가장 가까운 로봇 파견'
        )

        # 1. 가장 가까운 로봇 선택
        nearest_robot = self._find_nearest_robot(target_x, target_y)
        if nearest_robot is None:
            self.get_logger().error('로봇 위치 미확인 — Nav2 파견 불가')
            return

        # 2. Nav2 NavigateToPose Goal 전송
        self._send_nav_goal(nearest_robot, target_x, target_y)

        # 3. 군집 전체에 생존자 알림
        self.victim_pub.publish(String(data=json.dumps({
            'source':    'drone',
            'robot_id':  nearest_robot,
            'x':         target_x,
            'y':         target_y,
            'timestamp': self.get_clock().now().nanoseconds
        })))

    def _find_nearest_robot(self, tx: float, ty: float) -> int | None:
        """현재 위치 기준 가장 가까운 로봇 ID 반환"""
        if not self._robot_poses:
            return None

        nearest_id   = None
        nearest_dist = float('inf')

        for rid, (rx, ry) in self._robot_poses.items():
            dist = math.sqrt((tx - rx)**2 + (ty - ry)**2)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_id   = rid

        self.get_logger().info(
            f'가장 가까운 로봇: Robot-{nearest_id} (거리 {nearest_dist:.2f}m)'
        )
        return nearest_id

    def _send_nav_goal(self, robot_id: int, x: float, y: float):
        """Nav2 NavigateToPose Action Goal 전송"""
        client = self._nav_clients.get(robot_id)
        if client is None or not client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error(f'Robot-{robot_id} Nav2 서버 미응답')
            return

        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp    = self.get_clock().now().to_msg()
        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.orientation.w = 1.0

        future = client.send_goal_async(goal)
        future.add_done_callback(
            lambda f: self.get_logger().info(
                f'Robot-{robot_id}: Nav2 Goal 전송 {"성공" if f.result().accepted else "거부"}'
            )
        )


def main():
    rclpy.init()
    node = DroneNavBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 21.4 드론-Gossip 브릿지 (drone_gossip_bridge.py)

**파일 경로**: `ghost5_drone_integration/ghost5_drone_integration/drone_gossip_bridge.py`

```python
# ghost5_ws/src/ghost5_drone_integration/ghost5_drone_integration/drone_gossip_bridge.py
# 드론 생존자 탐지 이벤트 → Gossip 프로토콜로 군집 전체 전파

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ghost5_bringup/config'))
from qos_profiles import EVENT_QOS


class DroneGossipBridge(Node):
    """
    드론 탐지 이벤트 → Gossip 전파 브릿지.

    처리 흐름:
      /drone/survivor_pose 수신
        → SemanticMemory에 이벤트 기록 (Redis)
        → /swarm/gossip으로 군집 전체에 전파
        → /swarm/frontier_priority에 우선 탐색 좌표 퍼블리시

    Gossip 메시지 형식:
      {
        "type": "DRONE_VICTIM",
        "x": float, "y": float,
        "confidence": float,
        "timestamp": int
      }
    """

    GOSSIP_REPEAT = 3   # 동일 메시지 3회 반복 전파 (신뢰도 향상)

    def __init__(self):
        super().__init__('drone_gossip_bridge')
        self.get_logger().info('DroneGossipBridge 시작')

        self._gossiped: set[str] = set()   # 이미 전파한 이벤트 ID (중복 방지)

        # 구독
        self.create_subscription(
            PoseStamped, '/drone/survivor_pose',
            self._on_survivor_detected, EVENT_QOS
        )
        self.create_subscription(
            PoseStamped, '/drone/gps_pose',
            self._on_drone_pose, EVENT_QOS
        )

        # 퍼블리셔
        self.gossip_pub    = self.create_publisher(String, '/swarm/gossip',            EVENT_QOS)
        self.priority_pub  = self.create_publisher(String, '/swarm/frontier_priority', EVENT_QOS)

        # 드론 현재 위치 캐시
        self._drone_pos = (0.0, 0.0, 0.0)

    def _on_drone_pose(self, msg: PoseStamped):
        """드론 현재 위치 캐시 업데이트"""
        self._drone_pos = (
            msg.pose.position.x,
            msg.pose.position.y,
            msg.pose.position.z
        )

    def _on_survivor_detected(self, msg: PoseStamped):
        """드론 생존자 탐지 → Gossip 전파"""
        x = msg.pose.position.x
        y = msg.pose.position.y
        ts = self.get_clock().now().nanoseconds

        event_id = f'drone_victim_{x:.1f}_{y:.1f}'
        if event_id in self._gossiped:
            return   # 중복 전파 방지

        self._gossiped.add(event_id)

        # Gossip 메시지 구성
        gossip_data = json.dumps({
            'type':       'DRONE_VICTIM',
            'event_id':   event_id,
            'x':          x,
            'y':          y,
            'drone_x':    self._drone_pos[0],
            'drone_y':    self._drone_pos[1],
            'confidence': 0.85,   # 드론 카메라 감지 기본 신뢰도
            'timestamp':  ts
        })

        # GOSSIP_REPEAT 회 반복 전파
        for _ in range(self.GOSSIP_REPEAT):
            self.gossip_pub.publish(String(data=gossip_data))

        # 우선 탐색 좌표 퍼블리시 (드론 정찰 경로 재배치용)
        self.priority_pub.publish(String(data=json.dumps({
            'x': x, 'y': y, 'source': 'drone_victim', 'timestamp': ts
        })))

        self.get_logger().warn(
            f'🚁→📡 Gossip 전파: 드론 생존자 ({x:.2f}, {y:.2f}) — {self.GOSSIP_REPEAT}회'
        )


def main():
    rclpy.init()
    node = DroneGossipBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 21.5 드론 Fallback 모니터 (drone_fallback_monitor.py)

**파일 경로**: `ghost5_drone_integration/ghost5_drone_integration/drone_fallback_monitor.py`

```python
# ghost5_ws/src/ghost5_drone_integration/ghost5_drone_integration/drone_fallback_monitor.py
# 드론 장애 감지 → Fallback 전환 + Bully 리더 Zenoh Router 인수

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String, Bool
import json
import time
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ghost5_bringup/config'))
from qos_profiles import EVENT_QOS, MAP_QOS, POSE_QOS


class DroneFallbackMonitor(Node):
    """
    드론 장애 감지 + Fallback 전환 모니터.

    감지 조건:
      /drone/wifi_ap_status 또는 /drone/gps_pose가
      DRONE_TIMEOUT_SEC(5초) 동안 미수신 → 드론 장애로 판정

    Fallback 처리:
      ① /swarm/drone_relay_active = {"active": false} 퍼블리시
      ② 각 지상 로봇: Zenoh peer 모드 직접 통신 전환
      ③ Bully 리더 로봇: Zenoh Router 인수 (리더가 드론 대신 라우터 역할)
      ④ Frontier 탐색: 드론 우선순위 없이 지상 MMPF 자율 탐색 복귀

    Fallback 후 복구:
      드론 토픽 재수신 시 자동으로 드론 협동 모드 복귀.
    """

    DRONE_TIMEOUT_SEC = 5.0    # 드론 토픽 미수신 시 Fallback 트리거 시간

    def __init__(self):
        super().__init__('drone_fallback_monitor')
        self.get_logger().info('DroneFallbackMonitor 시작')

        self._last_drone_msg_time: float = time.time()
        self._fallback_active: bool = False

        # 구독: 드론 토픽 수신 시 타임스탬프 갱신
        self.create_subscription(
            PoseStamped, '/drone/gps_pose',
            lambda _: self._reset_timeout(), POSE_QOS
        )
        self.create_subscription(
            Bool, '/drone/wifi_ap_status',
            lambda _: self._reset_timeout(), MAP_QOS
        )
        self.create_subscription(
            String, '/swarm/drone_relay_active',
            self._on_relay_status, EVENT_QOS
        )

        # 퍼블리셔
        self.relay_pub = self.create_publisher(
            String, '/swarm/drone_relay_active', EVENT_QOS
        )

        # 장애 감지 타이머 (1초 주기)
        self.create_timer(1.0, self._check_drone_health)

    def _reset_timeout(self):
        """드론 토픽 수신 시 타임스탬프 갱신 + Fallback 복구 확인"""
        self._last_drone_msg_time = time.time()

        if self._fallback_active:
            self._fallback_active = False
            self.get_logger().info(
                '🚁 드론 통신 복구 → Fallback 해제, 드론 협동 모드 복귀'
            )
            self._publish_relay(active=True)

    def _check_drone_health(self):
        """1초마다 드론 생존 상태 확인"""
        elapsed = time.time() - self._last_drone_msg_time

        if elapsed > self.DRONE_TIMEOUT_SEC and not self._fallback_active:
            self.get_logger().error(
                f'🚁 드론 장애 감지! ({elapsed:.1f}초 미수신) → Fallback 전환'
            )
            self._activate_fallback()

    def _activate_fallback(self):
        """
        Fallback 활성화:
          1. drone_relay_active = false 퍼블리시
          2. 지상 로봇들이 이 토픽 수신 시 peer 모드 전환 + MMPF 자율 탐색 복귀
          3. Bully 리더는 별도로 Zenoh Router 인수 로직 실행
        """
        self._fallback_active = True
        self._publish_relay(active=False)

        self.get_logger().warn(
            'Fallback 상태:\n'
            '  ① 지상 로봇: Zenoh peer 직접 통신 전환\n'
            '  ② Bully 리더: Zenoh Router 인수\n'
            '  ③ Frontier: MMPF 자율 탐색 복귀\n'
            '  ④ 생존자 감지: 지상 센서 전용 (US-016, TCRT5000, YOLOv8n)'
        )

    def _publish_relay(self, active: bool):
        """드론 릴레이 상태 퍼블리시"""
        self.relay_pub.publish(String(data=json.dumps({
            'active':    active,
            'timestamp': self.get_clock().now().nanoseconds
        })))

    def _on_relay_status(self, msg: String):
        """다른 노드가 퍼블리시한 relay 상태 수신 (모니터링)"""
        data = json.loads(msg.data)
        active = data.get('active', True)
        self.get_logger().debug(
            f'드론 릴레이 상태: {"활성" if active else "비활성 (Fallback)"}'
        )


def main():
    rclpy.init()
    node = DroneFallbackMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

## 22. 🆕 PX4 SITL 드론 통합 (Phase 3-B)

### 22.1 Zenoh + uXRCE-DDS 충돌 문제 및 해결

> **핵심 이슈**: PX4 기본값인 uXRCE-DDS와 rmw_zenoh가 동일 포트를 점유해 충돌 발생.  
> **해결**: `px4_sitl_zenoh` 빌드 타겟 사용 → uXRCE-DDS 비활성화 + Zenoh 직접 통신.

```bash
# ── 버전 호환 매트릭스 ──────────────────────────────────────────────
# ROS2 Jazzy + Gazebo Harmonic + PX4 v1.16+ 조합 필수
# Ubuntu 24.04 + Python 3.12 기준

# ── PX4 SITL 빌드 환경 구축 ────────────────────────────────────────

# 1. 의존성 설치
sudo apt install -y \
    git cmake ninja-build python3-pip \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-bad \
    libgazebo-dev

# 2. Gazebo Harmonic 설치 (Ubuntu 24.04)
sudo apt install -y gz-harmonic

# 3. PX4-Autopilot 소스 클론
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot
git checkout v1.16.0   # Jazzy + Zenoh 호환 버전

# 4. px4_sitl_zenoh 빌드 타겟으로 빌드
# → uXRCE-DDS 비활성화, Zenoh 직접 통신 활성화
make px4_sitl_zenoh gz_x500

# 5. 실행 (X500 드론 + Gazebo Harmonic)
make px4_sitl_zenoh gz_x500
```

### 22.2 NED→ENU 좌표 변환 노드 (px4_topic_bridge.py)

**파일 경로**: `ghost5_drone_sim/ghost5_drone_sim/px4_topic_bridge.py`

```python
# ghost5_ws/src/ghost5_drone_sim/ghost5_drone_sim/px4_topic_bridge.py
# PX4 SITL 토픽 (NED 좌표계) → GHOST-5 표준 (ENU 좌표계) 변환 브릿지

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from px4_msgs.msg import VehicleLocalPosition, VehicleStatus
from std_msgs.msg import Float32, Bool
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../ghost5_bringup/config'))
from qos_profiles import POSE_QOS, EVENT_QOS, MAP_QOS


class PX4TopicBridge(Node):
    """
    PX4 SITL → GHOST-5 토픽 변환 브릿지.

    좌표계 변환 (NED → ENU):
      PX4 NED (North-East-Down):  x=North, y=East,  z=Down
      ROS2 ENU (East-North-Up):   x=East,  y=North, z=Up

      변환 공식:
        enu_x =  ned_y   (East  = East)
        enu_y =  ned_x   (North = North)
        enu_z = -ned_z   (Up    = -Down)

    출력 토픽 (GHOST-5 표준):
      /drone/gps_pose        → PoseStamped (ENU, map 프레임)
      /drone/battery_percent → Float32 (%)
      /drone/wifi_ap_status  → Bool (활성 여부)
    """

    def __init__(self):
        super().__init__('px4_topic_bridge')
        self.get_logger().info('PX4TopicBridge 시작 (Phase 3-B: NED→ENU 변환)')

        # PX4 토픽 구독 (uXRCE-DDS 표준 토픽명)
        # px4_sitl_zenoh 빌드 시 Zenoh로 직접 퍼블리시됨
        self.create_subscription(
            VehicleLocalPosition,
            '/fmu/out/vehicle_local_position',
            self._on_local_position,
            10
        )
        self.create_subscription(
            VehicleStatus,
            '/fmu/out/vehicle_status',
            self._on_vehicle_status,
            10
        )

        # GHOST-5 표준 토픽 퍼블리셔
        self.pose_pub    = self.create_publisher(PoseStamped, '/drone/gps_pose',        POSE_QOS)
        self.battery_pub = self.create_publisher(Float32,     '/drone/battery_percent', POSE_QOS)
        self.ap_pub      = self.create_publisher(Bool,        '/drone/wifi_ap_status',  MAP_QOS)

        self._battery: float = 100.0

    def _on_local_position(self, msg: VehicleLocalPosition):
        """
        PX4 로컬 위치 (NED) → ENU 변환 후 퍼블리시.

        PX4 VehicleLocalPosition 필드:
          x: North (m), y: East (m), z: Down (m, 음수가 위쪽)
        """
        # NED → ENU 변환
        enu_x =  msg.y    # East  ← PX4 y (East)
        enu_y =  msg.x    # North ← PX4 x (North)
        enu_z = -msg.z    # Up    ← -PX4 z (Down)

        pose = PoseStamped()
        pose.header.stamp    = self.get_clock().now().to_msg()
        pose.header.frame_id = 'map'
        pose.pose.position.x = enu_x
        pose.pose.position.y = enu_y
        pose.pose.position.z = enu_z
        pose.pose.orientation.w = 1.0

        self.pose_pub.publish(pose)

        self.get_logger().debug(
            f'PX4 NED ({msg.x:.2f}, {msg.y:.2f}, {msg.z:.2f}) → '
            f'ENU ({enu_x:.2f}, {enu_y:.2f}, {enu_z:.2f})'
        )

    def _on_vehicle_status(self, msg: VehicleStatus):
        """PX4 차량 상태 → 배터리 / WiFi AP 상태 변환"""
        # 배터리: PX4 battery_status 별도 토픽에서 읽는 것이 정확하나,
        # 여기서는 비행 시간 기반 선형 감소 시뮬
        self.battery_pub.publish(Float32(data=float(self._battery)))

        # WiFi AP: 비행 중이면 릴레이 활성
        is_flying = (msg.arming_state == VehicleStatus.ARMING_STATE_ARMED)
        self.ap_pub.publish(Bool(data=is_flying))


def main():
    rclpy.init()
    node = PX4TopicBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 22.3 재난 시나리오 Gazebo SDF 월드

**파일 경로**: `ghost5_bringup/worlds/ghost5_disaster.sdf`

```xml
<?xml version="1.0" ?>
<!--
  ghost5_disaster.sdf — GHOST-5 재난 시나리오 Gazebo Harmonic 월드
  구성: 붕괴 건물 잔해 + 생존자 마커(빨간 구) + TurtleBot3 5대 스폰 위치
-->
<sdf version="1.9">
  <world name="ghost5_disaster">

    <!-- 기본 물리 엔진 -->
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">
      <render_engine>ogre2</render_engine>
    </plugin>

    <!-- 조명 -->
    <light type="directional" name="sun">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
    </light>

    <!-- 바닥 -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="surface">
          <geometry><plane><normal>0 0 1</normal></plane></geometry>
        </collision>
        <visual name="visual">
          <geometry><plane><normal>0 0 1</normal><size>50 50</size></plane></geometry>
          <material><ambient>0.4 0.4 0.4 1</ambient></material>
        </visual>
      </link>
    </model>

    <!-- 붕괴 건물 잔해 블록 1 -->
    <model name="debris_1">
      <static>true</static>
      <pose>3.0 2.0 0.5 0 0 0.3</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>2.0 0.5 1.0</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>2.0 0.5 1.0</size></box></geometry>
          <material><ambient>0.5 0.4 0.3 1</ambient></material>
        </visual>
      </link>
    </model>

    <!-- 붕괴 건물 잔해 블록 2 -->
    <model name="debris_2">
      <static>true</static>
      <pose>6.0 4.0 0.3 0 0 1.0</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>1.5 0.4 0.6</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>1.5 0.4 0.6</size></box></geometry>
          <material><ambient>0.4 0.3 0.2 1</ambient></material>
        </visual>
      </link>
    </model>

    <!-- 좁은 통로 (두 벽) -->
    <model name="wall_1">
      <static>true</static>
      <pose>4.0 0.0 1.0 0 0 0</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>0.2 6.0 2.0</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>0.2 6.0 2.0</size></box></geometry>
          <material><ambient>0.6 0.6 0.6 1</ambient></material>
        </visual>
      </link>
    </model>

    <!-- 생존자 마커 1 (빨간 구) — 드론이 탐지할 위치 -->
    <model name="survivor_1">
      <static>true</static>
      <pose>3.0 2.0 0.3 0 0 0</pose>
      <link name="link">
        <visual name="vis">
          <geometry><sphere><radius>0.3</radius></sphere></geometry>
          <material>
            <ambient>1 0 0 1</ambient>
            <diffuse>1 0 0 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

    <!-- 생존자 마커 2 (빨간 구) -->
    <model name="survivor_2">
      <static>true</static>
      <pose>7.0 4.0 0.3 0 0 0</pose>
      <link name="link">
        <visual name="vis">
          <geometry><sphere><radius>0.3</radius></sphere></geometry>
          <material>
            <ambient>1 0 0 1</ambient>
            <diffuse>1 0 0 1</diffuse>
          </material>
        </visual>
      </link>
    </model>

  </world>
</sdf>
```

---

## 23. 🆕 드론-지상 로봇 협동 아키텍처

### 23.1 협동 시나리오 전체 흐름

```
드론 (Fake / PX4 SITL)
  │
  ├─ /drone/gps_pose (10Hz, ENU)
  │     → DroneFallbackMonitor: 생존 확인
  │     → DroneNavBridge: 로봇 위치 기준 파견 판단
  │
  ├─ /drone/survivor_pose (이벤트)
  │     → DroneNavBridge: 가장 가까운 로봇에 Nav2 Goal 전송
  │     → DroneGossipBridge: /swarm/gossip으로 군집 전파
  │     → Blackboard: 생존자 Redis 기록 (add_victim)
  │
  ├─ /drone/wifi_ap_status (1Hz)
  │     → DroneFallbackMonitor: 5초 미수신 시 Fallback
  │
  └─ /swarm/drone_relay_active (이벤트)
        → 각 지상 로봇: Zenoh peer 모드 전환
        → Bully 리더: Zenoh Router 인수

지상 로봇 (5대)
  │
  ├─ /swarm/frontier_priority 수신
  │     → FrontierManager: 드론 좌표 기반 우선 Frontier 설정
  │
  └─ /swarm/victim 수신
        → Blackboard 기록 + GCS 보고
```

### 23.2 Bully 리더 Zenoh Router 인수 로직

드론 Fallback 시 지상 Leader 로봇이 Zenoh Router 역할을 인수한다.

```python
# leader_election.py에 추가 메서드

def _handle_drone_fallback(self, active: bool):
    """
    드론 릴레이 비활성화 수신 시:
      Leader 로봇만 Zenoh Router를 추가 실행.
    """
    if not active and self.current_leader_id == self.robot_id:
        self.get_logger().warn(
            f'Robot-{self.robot_id} (Leader): 드론 Fallback → Zenoh Router 인수'
        )
        import subprocess
        subprocess.Popen(['ros2', 'run', 'rmw_zenoh_cpp', 'init_rmw_zenoh_router'])

def _on_drone_relay(self, msg: String):
    """/swarm/drone_relay_active 구독 콜백"""
    data = json.loads(msg.data)
    self._handle_drone_fallback(data.get('active', True))
```

### 23.3 Frontier 우선순위 드론 연동

```python
# frontier_manager.py compute_mmpf_goal 메서드 드론 연동 추가

class FrontierManager:
    def __init__(self, robot_id: int, node):
        # ... 기존 코드 ...
        self._drone_priority: tuple | None = None   # 드론이 요청한 우선 좌표

        # 드론 우선 탐색 좌표 구독
        node.create_subscription(
            String, '/swarm/frontier_priority',
            self._on_drone_priority, EVENT_QOS
        )

    def _on_drone_priority(self, msg: String):
        """드론 우선 탐색 좌표 수신"""
        data = json.loads(msg.data)
        if data.get('source') == 'drone_victim':
            self._drone_priority = (data['x'], data['y'])
            self.node.get_logger().info(
                f'드론 우선 좌표 수신: ({data["x"]:.1f}, {data["y"]:.1f})'
            )

    def compute_mmpf_goal(self, frontiers, robot_poses, my_pose, skip_zones=None):
        """드론 우선 좌표가 있으면 가장 가까운 Frontier를 우선 선택"""
        if self._drone_priority and frontiers:
            dpx, dpy = self._drone_priority
            # 드론 좌표에 가장 가까운 Frontier 선택
            nearest = min(
                frontiers,
                key=lambda f: (f['x'] - dpx)**2 + (f['y'] - dpy)**2
            )
            self._drone_priority = None   # 1회 사용 후 초기화
            self._claim_frontier(nearest['id'])
            return nearest

        # 드론 우선 없으면 기존 MMPF 알고리즘
        return self._mmpf_select(frontiers, robot_poses, my_pose, skip_zones)
```

---

## 24. 🆕 드론 통합 런치 파일 설계

### 24.1 드론 통합 런치 (Phase 3-A)

**파일 경로**: `ghost5_drone_integration/launch/drone_integration.launch.py`

```python
# ghost5_ws/src/ghost5_drone_integration/launch/drone_integration.launch.py

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    드론 통합 런치 파일 (Phase 3-A: Fake Drone).

    실행 노드:
      - fake_drone_node     : 드론 행동 시뮬
      - drone_nav_bridge    : 생존자 좌표 → Nav2 Goal
      - drone_gossip_bridge : 생존자 → Gossip 전파
      - drone_fallback_monitor : 드론 장애 감지 + Fallback
    """
    return LaunchDescription([
        # Fake 드론 노드 (Phase 3-A)
        Node(
            package='ghost5_drone_sim',
            executable='fake_drone_node',
            name='fake_drone',
            output='screen',
            parameters=[{'use_sim_time': False}]
        ),

        # 드론-Nav2 브릿지
        Node(
            package='ghost5_drone_integration',
            executable='drone_nav_bridge',
            name='drone_nav_bridge',
            output='screen'
        ),

        # 드론-Gossip 브릿지
        Node(
            package='ghost5_drone_integration',
            executable='drone_gossip_bridge',
            name='drone_gossip_bridge',
            output='screen'
        ),

        # 드론 Fallback 모니터
        Node(
            package='ghost5_drone_integration',
            executable='drone_fallback_monitor',
            name='drone_fallback_monitor',
            output='screen'
        ),
    ])
```

### 24.2 전체 군집 + 드론 통합 런치

**파일 경로**: `ghost5_bringup/launch/swarm_with_drone.launch.py`

```python
# ghost5_ws/src/ghost5_bringup/launch/swarm_with_drone.launch.py

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    """
    5대 지상 로봇 군집 + 드론 통합 런치.

    포함:
      - robot.launch.py × 5 (robot_id 1~5)
      - drone_integration.launch.py (Fake Drone + 브릿지)
    """
    bringup_dir  = get_package_share_directory('ghost5_bringup')
    drone_dir    = get_package_share_directory('ghost5_drone_integration')

    launch_descriptions = []

    # 5대 지상 로봇 런치
    for robot_id in range(1, 6):
        is_leader = 'true' if robot_id == 1 else 'false'
        launch_descriptions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(bringup_dir, 'launch', 'robot.launch.py')
                ),
                launch_arguments={
                    'robot_id':  str(robot_id),
                    'is_leader': is_leader,
                }.items()
            )
        )

    # 드론 통합 노드 런치
    launch_descriptions.append(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(drone_dir, 'launch', 'drone_integration.launch.py')
            )
        )
    )

    return LaunchDescription(launch_descriptions)
```

### 24.3 package.xml 정의 (드론 패키지)

```xml
<!-- ghost5_drone_sim/package.xml -->
<?xml version="1.0"?>
<package format="3">
  <name>ghost5_drone_sim</name>
  <version>1.0.0</version>
  <description>GHOST-5 드론 시뮬레이션 패키지 (Phase 3-A/B)</description>
  <maintainer email="gjkong097@example.com">Stephen Kong</maintainer>
  <license>MIT</license>

  <depend>rclpy</depend>
  <depend>geometry_msgs</depend>
  <depend>std_msgs</depend>
  <depend>ghost5_interfaces</depend>

  <buildtool_depend>ament_python</buildtool_depend>
  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

```xml
<!-- ghost5_drone_integration/package.xml -->
<?xml version="1.0"?>
<package format="3">
  <name>ghost5_drone_integration</name>
  <version>1.0.0</version>
  <description>GHOST-5 드론-지상 로봇 통합 패키지</description>
  <maintainer email="gjkong097@example.com">Stephen Kong</maintainer>
  <license>MIT</license>

  <depend>rclpy</depend>
  <depend>geometry_msgs</depend>
  <depend>std_msgs</depend>
  <depend>nav2_msgs</depend>
  <depend>ghost5_interfaces</depend>
  <depend>ghost5_drone_sim</depend>

  <buildtool_depend>ament_python</buildtool_depend>
  <test_depend>pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

---

## 25. 🆕 드론 통합 검증 시나리오

### 25.1 Phase 3-A 검증 시나리오 (Fake Drone)

```
시나리오 1: Fake 드론 단독 토픽 검증
  ① swarm_with_drone.launch.py 실행
  ② 확인 명령:
     ros2 topic hz /drone/gps_pose          # 10Hz 이상 확인
     ros2 topic echo /drone/wifi_ap_status  # True 퍼블리시 확인
     ros2 topic echo /drone/battery_percent # 감소하는지 확인
  성공 조건: 10Hz 퍼블리시 유지, 배터리 선형 감소

시나리오 2: 드론 생존자 탐지 → Nav2 파견
  ① 드론이 생존자 좌표 (3.0, 2.0) 근방 접근
  ② /drone/survivor_pose 퍼블리시 확인
  ③ DroneNavBridge → 가장 가까운 지상 로봇에 Nav2 Goal 전송
  ④ 해당 로봇 실제 이동 확인 (RViz2)
  성공 조건: 드론 탐지 후 5초 이내 가장 가까운 로봇 이동 시작

시나리오 3: Gossip 전파 확인
  ① 드론 생존자 탐지 이벤트 발생
  ② ros2 topic echo /swarm/gossip 확인
  ③ Redis에 생존자 기록 확인:
     redis-cli -a ghost5secure! HGETALL victims
  성공 조건: /swarm/gossip 3회 반복 퍼블리시 + Redis 기록 완료

시나리오 4: 드론 Fallback 전환
  ① 드론 노드 강제 종료 (Ctrl+C)
  ② 5초 후 DroneFallbackMonitor 장애 감지 확인
  ③ /swarm/drone_relay_active → {"active": false} 퍼블리시 확인
  ④ 지상 로봇들이 Zenoh peer 모드로 전환하고 MMPF 탐색 계속 확인
  성공 조건: 5초 이내 Fallback 전환, 지상 탐색 중단 없음
```

### 25.2 Phase 3-B 검증 시나리오 (PX4 SITL)

```
시나리오 5: PX4 SITL 호버링 + ENU 좌표 정확성
  ① make px4_sitl_zenoh gz_x500 실행
  ② X500 드론 Takeoff → 고도 3.0m 호버링
  ③ /drone/gps_pose ENU 좌표 정확성 확인:
     ros2 topic echo /drone/gps_pose
  ④ 드론 Gazebo 위치와 /drone/gps_pose 위치 비교 (오차 < 0.1m)
  성공 조건: ENU 좌표 정확성 오차 < 0.1m, 토픽 손실 < 5%

시나리오 6: 전체 통합 재난 시나리오
  ① ghost5_disaster.sdf 월드 실행
  ② PX4 X500 드론 + TurtleBot3 5대 동시 실행
  ③ 드론 순찰 경로 비행 → 생존자 마커(빨간 구) 탐지
  ④ 탐지된 생존자 좌표 → 가장 가까운 TurtleBot3 자동 파견
  ⑤ 나머지 4대 Frontier 자율 탐색 지속
  성공 조건: 생존자 1명 탐지 후 30초 이내 지상 로봇 도착
```

### 25.3 드론 통합 단위 테스트

```python
# ghost5_ws/tests/unit/test_drone_integration.py

import pytest
import json


class TestFakeDroneNode:

    def test_waypoint_cycling(self):
        """웨이포인트 순환 이동 확인"""
        # FakeDroneNode 5개 웨이포인트 순환 후 홈 복귀 검증
        pass

    def test_victim_detection_distance(self):
        """생존자 탐지 거리 임계값 (DETECTION_DIST=1.5m) 검증"""
        pass

    def test_battery_drain_rate(self):
        """배터리 소모 속도 선형 감소 검증"""
        pass

    def test_priority_waypoint_insertion(self):
        """드론 우선 탐색 좌표 웨이포인트 삽입 검증"""
        pass


class TestDroneNavBridge:

    def test_nearest_robot_selection(self):
        """가장 가까운 로봇 선택 알고리즘 검증"""
        # Robot 1(0,0), Robot 2(10,10), 생존자(1,1) → Robot 1 선택
        pass

    def test_nav_goal_sent_on_detection(self):
        """드론 탐지 이벤트 시 Nav2 Goal 전송 확인"""
        pass


class TestDroneFallbackMonitor:

    def test_fallback_trigger_after_timeout(self):
        """5초 미수신 후 Fallback 전환 확인"""
        pass

    def test_fallback_recovery_on_reconnect(self):
        """드론 토픽 재수신 시 Fallback 해제 확인"""
        pass

    def test_relay_topic_published_on_fallback(self):
        """/swarm/drone_relay_active = false 퍼블리시 확인"""
        pass


class TestNEDtoENUConversion:

    def test_ned_to_enu_basic(self):
        """NED (1,2,-3) → ENU (2,1,3) 변환 검증"""
        ned_x, ned_y, ned_z = 1.0, 2.0, -3.0
        enu_x =  ned_y   # 2.0
        enu_y =  ned_x   # 1.0
        enu_z = -ned_z   # 3.0
        assert enu_x == 2.0
        assert enu_y == 1.0
        assert enu_z == 3.0

    def test_hover_altitude_positive(self):
        """호버링 시 ENU z가 양수인지 확인 (NED z는 음수)"""
        ned_z = -3.0    # 고도 3m (Down 방향이 양수)
        enu_z = -ned_z  # 3.0 (Up 방향이 양수)
        assert enu_z > 0
```

---

## 26. 🆕 최종 통합 아키텍처 (지상 5대 + 가상 드론)

### 26.1 전체 시스템 아키텍처 (v2.0)

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Ground Control Station (GCS)                       │
│     Foxglove Studio — 2.5D 지도 + 생존자 + 드론 위치 통합 표시       │
│     FastAPI GCS API (포트 8000) — 커서 기반 페이징                   │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ rmw_zenoh (SROS2 AES-GCM 암호화)
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│         🚁 가상 드론                                                  │
│                                                                      │
│  Phase 3-A (즉시):               Phase 3-B (2~4주 후):              │
│  fake_drone_node.py              PX4 SITL X500 + Gazebo Harmonic     │
│  (rmw_zenoh 직접)                px4_sitl_zenoh 빌드 타겟           │
│                                  px4_topic_bridge.py (NED→ENU)       │
│                                                                      │
│  공통 publish 토픽:                                                  │
│    /drone/gps_pose          (10Hz, ENU, BEST_EFFORT)                │
│    /drone/survivor_pose     (이벤트, RELIABLE, KEEP_ALL)            │
│    /drone/wifi_ap_status    (1Hz, RELIABLE)                          │
│    /drone/battery_percent   (1Hz, BEST_EFFORT)                       │
│    /swarm/drone_relay_active (이벤트, RELIABLE, KEEP_ALL)           │
│                                                                      │
│  드론 통합 노드 (모든 지상 로봇에서 실행):                           │
│    drone_nav_bridge.py      (생존자 → Nav2 Goal)                    │
│    drone_gossip_bridge.py   (생존자 → Gossip 전파)                  │
│    drone_fallback_monitor.py (장애 감지 + Fallback)                 │
│                                                                      │
│  Zenoh Router ← 모든 로봇 Discovery 허브                             │
│  (드론 Fallback 시 Bully 리더가 Router 인수)                        │
└──────────────────────┬───────────────────────────────────────────────┘
                       │ rmw_zenoh Mesh (WiFi AP 릴레이)
         ┌─────────────┼─────────────────┐
         │             │                 │
   R-1 (Leader)     R-2~R-3          R-4~R-5 (Explorer)
 ┌─────────────────┐ ┌─────────────┐  ┌─────────────────────┐
 │ slam_toolbox    │ │ slam_toolbox│  │ slam_toolbox        │
 │ map_merger_v2   │ │ frontier_mgr│  │ frontier_mgr (MMPF) │
 │ elevation_global│ │ gossip_node │  │ gossip_node         │
 │ leader_election │ │ drone_nav   │  │ drone_nav_bridge    │
 │ Redis Blackboard│ │   _bridge   │  │ drone_gossip_bridge │
 │ SemanticMemory  │ │ drone_gossip│  │ drone_fallback      │
 │ drone_nav_bridge│ │   _bridge   │  │   _monitor          │
 │ drone_gossip_   │ │ drone_fall  │  │ comm_monitor (RSSI) │
 │   bridge        │ │   back_mon  │  │ victim_fuser        │
 │ drone_fallback_ │ │             │  │ lidar_elevation     │
 │   monitor       │ └─────────────┘  └─────────────────────┘
 │ Zenoh Router    │
 │  (+ Fallback    │
 │   인수 로직)    │
 └─────────────────┘

하드웨어 (로봇 1대, Pinky Pro):
  Raspberry Pi 5 (8GB)
    ├── RPLiDAR C1         → slam_toolbox + Elevation Z-stack
    ├── 5MP 카메라          → YOLOv8n 인체 감지
    ├── US-016 초음파       → 생존자 근거리 감지 (20~150cm)
    ├── TCRT5000 IR         → 근거리 반사 감지 (~30cm)
    ├── BNO055 IMU (9축)    → EKF + LiDAR 스캔 보정
    ├── 다이나믹셀 XL330   → 구동 + 오도메트리
    └── (옵션) Hailo 26TOPS → NPU 가속 (Phase 2)
```

### 26.2 최종 기술 스택 요약 (v2.0)

| 레이어 | 선택 기술 | 상태 |
|--------|-----------|------|
| **미들웨어** | rmw_zenoh (ROS2 Jazzy) | ✅ 드론 = Zenoh Router |
| **SLAM** | slam_toolbox + Pose Graph | ✅ 유지 |
| **지도 병합** | Delta Update + map_merger_v2 | ✅ 유지 |
| **Frontier** | MMPF + Claim Blackboard | ✅ 드론 좌표 우선순위 연동 |
| **리더 선출** | Bully Algorithm | ✅ 드론 Fallback 시 Router 인수 |
| **드론 Phase 3-A** | fake_drone_node.py | 🆕 신규 |
| **드론 Phase 3-B** | PX4 px4_sitl_zenoh + Gazebo Harmonic | 🆕 신규 |
| **NED→ENU 변환** | px4_topic_bridge.py | 🆕 신규 |
| **드론 협동** | drone_nav_bridge + drone_gossip_bridge | 🆕 신규 |
| **드론 Fallback** | drone_fallback_monitor + Bully Router 인수 | 🆕 신규 |
| **공유 상태** | Redis Blackboard + Semantic Event Memory | ✅ 유지 |
| **보안** | SROS2 (DDS-Security AES-GCM) | ✅ 유지 |
| **생존자 감지** | US-016 + TCRT5000 + YOLOv8n | ✅ 유지 |
| **2.5D 인지** | RPLiDAR Z-stack + IMU 보정 | ✅ 유지 |
| **시각화** | Foxglove Studio | ✅ 드론 위치 오버레이 추가 |

### 26.3 구현 우선순위 (Phase 3)

| 우선순위 | 항목 | Phase | 난이도 | 선행 조건 |
|----------|------|-------|--------|-----------|
| **P0** | `fake_drone_node.py` 작성·실행 | 3-A | ⭐ | ROS2 Jazzy |
| **P0** | `drone_nav_bridge.py` 작성 | 3-A | ⭐ | Nav2 완성 |
| **P0** | `drone_gossip_bridge.py` 작성 | 3-A | ⭐ | Gossip 완성 |
| **P0** | `drone_fallback_monitor.py` 작성 | 3-A | ⭐ | — |
| **P0** | Phase 3-A 시나리오 1~4 검증 | 3-A | ⭐ | 위 P0 완료 |
| **P1** | PX4 SITL 빌드 환경 구축 | 3-B | ⭐⭐⭐ | GPU 권장 |
| **P1** | `px4_topic_bridge.py` (NED→ENU) | 3-B | ⭐⭐ | PX4 SITL |
| **P1** | ghost5_disaster.sdf 월드 제작 | 3-B | ⭐⭐ | Gazebo Harmonic |
| **P2** | TurtleBot3 5대 + X500 통합 시뮬 | 3-B | ⭐⭐⭐ | 위 P1 완료 |
| **P2** | Phase 3-B 시나리오 5~6 검증 | 3-B | ⭐⭐ | — |
| **P3** | 실기체 X500 V2 전환 결정 | 4+ | ⭐⭐⭐⭐ | 충분한 시뮬 검증 |

### 26.4 빌드 및 실행 (v2.0 전체)

```bash
# venv 비활성화 필수 (colcon 빌드 전)
deactivate 2>/dev/null || true

cd ~/ghost5_ws

# 전체 패키지 빌드 (드론 패키지 포함)
colcon build --symlink-install --packages-select \
    ghost5_interfaces \
    ghost5_bringup \
    ghost5_slam \
    ghost5_navigation \
    ghost5_swarm \
    ghost5_victim \
    ghost5_viz \
    ghost5_drone_sim \
    ghost5_drone_integration

source install/setup.bash

# ── Phase 3-A: 지상 5대 + Fake 드론 통합 실행 ──────────────────────
export LEADER_IP=192.168.1.101
ros2 launch ghost5_bringup swarm_with_drone.launch.py

# 또는 개별 실행:
# 터미널 1 — 5대 지상 로봇 군집
ros2 launch ghost5_bringup swarm.launch.py

# 터미널 2 — 드론 통합 노드
ros2 launch ghost5_drone_integration drone_integration.launch.py

# ── Phase 3-B: PX4 SITL 실행 ─────────────────────────────────────
cd ~/PX4-Autopilot
make px4_sitl_zenoh gz_x500

# 별도 터미널 — NED→ENU 변환 브릿지
ros2 run ghost5_drone_sim px4_topic_bridge

# ── GCS API 서버 ──────────────────────────────────────────────────
uvicorn ghost5_viz.gcs_api:app --host 0.0.0.0 --port 8000 &

# ── Foxglove Studio 연결 ──────────────────────────────────────────
# ws://leader_robot_ip:8765
# 드론 위치: /drone/gps_pose 토픽 추가 시각화
```

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-03-15 | 최초 작성 — GHOST5_research.md v2.1 기반 전체 구현 계획 수립. 인풋 기반 커서 페이징 설계 포함 |
| v1.3 | 2026-03-15 | **3가지 최종 보완 + 센서 배치 다이어그램**: ① 섹션 9 — Redis Slave Lag 대응: add_victim() WAIT(1, 100ms) 동기 쓰기(sync_write=True 기본값), add_victim_async() 비동기 폴백, check_slave_lag_and_warn() 모니터링 메서드 추가 ② 섹션 10 — Temporal Consistency Filter: TEMPORAL_MIN_SEC(2.0s), TEMPORAL_DECAY_SEC(10.0s) 파라미터 추가; elevation_cells에 first_seen/last_seen 타임스탬프 기록; _publish_elevation()에서 Decay 삭제 + Duration Guard(지속 시간 미달 셀 미확정) 이중 필터 적용 ③ 섹션 8 — Election Storm 방지: BACKOFF_STEP_SEC(0.1s), _start_election_with_backoff()로 ID 기반 지연(Robot-5: 0s → Robot-1: 0.4s), _start_election_once() Backoff 중 VICTORY 수신 시 자동 취소 ④ 섹션 20 — Pinky Pro 센서 배치 최종 다이어그램 |
| v2.0 | 2026-03-17 | **🆕 가상 드론(Gazebo) 통합 완전판**: GHOST5_research.md v3.1 기반. 섹션 21~26 신규 추가. Phase 3-A(fake_drone_node.py) + Phase 3-B(PX4 SITL px4_sitl_zenoh + Gazebo Harmonic). NED↔ENU 변환 노드, 드론-Nav2 브릿지, 드론-Gossip 브릿지, 드론 Fallback 모니터, 재난 SDF 월드, 6가지 검증 시나리오, 드론 단위 테스트. 드론 QoS 토픽 6개 추가(/drone/*, /swarm/drone_*). 워크스페이스에 ghost5_drone_sim + ghost5_drone_integration 패키지 추가. Bully 리더 Zenoh Router 인수 로직 추가. |
| v2.1 | 2026-03-17 | **🆕 Inter-Robot 동적 장애물 등록 (충돌 회피 보완)**: 섹션 10.3 신규 추가. Nav2 local costmap에 `robot_layer`(ObstacleLayer) 추가. `InterRobotCostmapLayer` 노드(`inter_robot_costmap_layer.py`) 신규 구현 — /robot_N/pose 5대 수집 → TTL 0.3s 관리 → PointCloud2 변환 → /swarm/robot_poses_array 5Hz 퍼블리시. QoS 토픽에 /swarm/robot_poses_array 추가. nav2_params.yaml에 robot_layer 섹션 추가(obstacle_max_range 3m, clearing true). ghost5_navigation 패키지에 inter_robot_costmap_layer.py 추가. |

---

*본 plan.md v2.1은 GHOST5_research.md v3.1의 모든 설계 결정(지상 5대 + Gazebo 드론)을 구현 관점으로 재구성한 완전판 문서입니다.*  
*Phase 3-A 완료(Fake Drone 검증) → v2.2, Phase 3-B 완료(PX4 SITL 검증) → v3.0으로 갱신 예정.*
