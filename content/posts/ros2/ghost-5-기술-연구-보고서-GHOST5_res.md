---
title: "GHOST-5 기술 연구 보고서"
date: 2026-03-21
draft: true
tags: ["ros2", "slam", "gazebo", "zenoh"]
categories: ["ros2"]
description: "> GPS-denied Hazard Operation with Swarm Team — 5 Units + Gazebo 드론 시뮬레이션 > 작성일: 2026-03-15 | **v3.1 — Gazebo 드론 심화 기술 조"
---

# GHOST-5 기술 연구 보고서

> GPS-denied Hazard Operation with Swarm Team — 5 Units + Gazebo 드론 시뮬레이션  
> 작성일: 2026-03-15 | **v3.1 — Gazebo 드론 심화 기술 조사 완료: 2026-03-16**  
> 연관 문서: GHOST-5_구축계획서.md, Ghost5_데이터공유방식.md, GHOST5_Phase3_UAV_Relay_Research.md  
> 참고 논문: MEM (Multi-Scale Embodied Memory for VLAs, Physical Intelligence 2025), DARPA SubT Field Robotics 2023

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-03-15 | 최초 작성 (미들웨어, SLAM, Frontier, Leader Election, 보안, 코드 구조) |
| v2.0 | 2026-03-15 | **리뷰 반영**: 2.5D Elevation Map 융합, Semantic Event Memory, Rendezvous 프로토콜, NPU 가속 설계 추가 |
| v2.1 | 2026-03-15 | **Pinky Pro 실제 스펙 반영**: RPLiDAR C1, 5MP 카메라, US-016, TCRT5000, XL330 모터. MLX90640/USB마이크 제거 |
| v3.0 | 2026-03-16 | **🆕 Gazebo 드론 시뮬레이션 통합**: 섹션 16~18 초기 추가. 5대 지상 로봇 + 가상 드론 협동 시나리오 |
| v3.1 | 2026-03-16 | **🆕 Gazebo 심화 기술 조사**: Zenoh+uXRCE-DDS 충돌 이슈 및 해결책(px4_sitl_zenoh), 버전 호환 매트릭스, 전체 설치 가이드, NED↔ENU 변환 노드, 재난 시나리오 SDF 월드, TurtleBot3 혼합 시뮬, 트러블슈팅 체크리스트 추가. 참고문헌 29편으로 확장 |

---

## 목차

1. [연구 배경 및 목적](#1-연구-배경-및-목적)
2. [미들웨어 기술 분석 — 핵심 선택](#2-미들웨어-기술-분석--핵심-선택)
3. [Multi-Robot SLAM 알고리즘 선택](#3-multi-robot-slam-알고리즘-선택)
4. [Frontier 탐색 알고리즘 선택](#4-frontier-탐색-알고리즘-선택)
5. [리더 선출 알고리즘 선택](#5-리더-선출-알고리즘-선택)
6. [데이터 공유 전략 최적 설계](#6-데이터-공유-전략-최적-설계)
7. [보안 설계 (SROS2 기반)](#7-보안-설계-sros2-기반)
8. [코드 구조 설계](#8-코드-구조-설계)
9. [검증 전략 및 성능 지표](#9-검증-전략-및-성능-지표)
10. [MEM 논문에서 얻은 아키텍처 인사이트](#10-mem-논문에서-얻은-아키텍처-인사이트)
11. [🆕 보완 설계 — 2.5D Elevation Map 융합](#11-보완-설계--25d-elevation-map-융합)
12. [🆕 보완 설계 — Semantic Event Memory](#12-보완-설계--semantic-event-memory)
13. [🆕 보완 설계 — Rendezvous 프로토콜 (통신 단절 대응)](#13-보완-설계--rendezvous-프로토콜-통신-단절-대응)
14. [🆕 보완 설계 — Hailo NPU 하드웨어 가속](#14-보완-설계--hailo-npu-하드웨어-가속)
15. [최종 기술 스택 요약 (v2.0)](#15-최종-기술-스택-요약-v20)
16. [🆕 v3.1 — Gazebo 드론 시뮬레이션 심화 기술 조사](#16-v31--gazebo-드론-시뮬레이션-심화-기술-조사)
17. [🆕 v3.1 — 드론 시뮬 통합 설계: 토픽·아키텍처·코드](#17-v31--드론-시뮬-통합-설계-토픽아키텍처코드)
18. [🆕 v3.1 — 최종 통합 아키텍처 (지상 5대 + Gazebo 드론)](#18-v31--최종-통합-아키텍처-지상-5대--gazebo-드론)

---

## 1. 연구 배경 및 목적

GHOST-5는 GPS가 차단된 재난 환경(붕괴 건물, 지하 공간, 화재 현장)에서 5대의 자율 군집 로봇이 협력 지도를 실시간 생성하고 생존자를 탐색하는 시스템이다. 단일 로봇의 한계(배터리, 통신 단절, 시야 제한)를 군집 협력으로 극복하는 것이 핵심 목표이다.

이 보고서는 다음 세 가지 핵심 질문에 답한다:

1. **5대 로봇이 ROS2로 빠르고 정확하게 통신하기 위한 최상의 미들웨어는 무엇인가?**
2. **불안정한 재난 환경 네트워크에서 최적의 알고리즘 조합은 무엇인가?**
3. **각 알고리즘 선택이 최상인 이유와 검증 방법은 무엇인가?**

---

## 2. 미들웨어 기술 분석 — 핵심 선택

### 2.1 후보 비교 분석

ROS2 Jazzy 기준으로 사용 가능한 RMW(ROS Middleware)는 세 가지다.

| 항목 | FastDDS | CycloneDDS | **Zenoh (rmw_zenoh)** |
|------|---------|-----------|----------------------|
| 네트워크 방식 | UDP Multicast | UDP Multicast | TCP/UDP 혼합 + Gossip |
| WiFi 무선 환경 성능 | 보통 | 보통 | **우수** |
| 4G/불안정 네트워크 | 취약 | 취약 | **강함** |
| CPU 사용량 (Raspberry Pi) | 높음 | 중간 | **절반 수준** |
| Discovery 오버헤드 | 높음 | 중간 | **97~99.9% 절감** |
| 대형 메시지 (지도) | 불안정 | 불안정 | **안정** |
| Jazzy 공식 지원 | ✅ | ✅ | ✅ (2025년 정식 포함) |
| 메쉬 네트워크 지원 | ❌ | ❌ | ✅ |

**2025년 주요 연구 결과 (Journal of Intelligent & Robotic Systems):**
> Zenoh는 동적 메쉬 토폴로지 환경에서 CycloneDDS/FastDDS 대비 지연(delay) 감소, 도달 가능성(reachability) 향상, CPU 사용량 절반 수준을 보여줬다. 행성 탐사 시나리오(극한 환경 멀티 로봇)에서 Zenoh가 최적 RMW로 선정됐다.

**Multi-Robot Graph SLAM 저자 권고 (GitHub, 2025):**
> "실제 로봇에서 mrg_slam을 사용할 경우 ROS2 Jazzy + rmw_zenoh를 강력히 권장한다. Humble + DDS 조합은 두 로버 통신에서 반복적으로 실패했지만, Jazzy + rmw_zenoh는 안정적이었다."

### 2.2 채택 결론: **rmw_zenoh (Zenoh RMW)**

재난 환경의 특성인 불안정한 WiFi Mesh, 동적 토폴로지 변화, Raspberry Pi 5의 제한된 리소스를 고려할 때 Zenoh가 압도적으로 적합하다. CycloneDDS는 유선 Ethernet에서 더 좋지만 GHOST-5의 환경은 무선이 전제다.

### 2.3 Zenoh 적용 설정

```bash
# 설치 (ROS2 Jazzy)
sudo apt install ros-jazzy-rmw-zenoh-cpp

# 모든 로봇에 환경변수 설정
export RMW_IMPLEMENTATION=rmw_zenoh_cpp

# Zenoh 라우터 실행 (Leader 로봇에서)
ros2 run rmw_zenoh_cpp init_rmw_zenoh_router
```

```xml
<!-- zenoh_config.json5 — 각 Explorer 로봇 설정 -->
{
  "mode": "peer",
  "connect": {
    "endpoints": ["tcp/robot1_ip:7447"]  // Leader Zenoh Router에 연결
  },
  "scouting": {
    "gossip": {
      "enabled": true,
      "multihop": true  // Mesh 네트워크 멀티홉 활성화
    }
  }
}
```

### 2.4 QoS 정책 설계 (통신 우선순위별)

```python
# ghost5_ws/ghost5_bringup/config/qos_profiles.py

from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
import rclpy.qos as qos

# 🔴 HIGH: 로봇 위치, 상태 (10Hz, 손실 허용, 최신 값만)
POSE_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,   # UDP: 빠름, 손실 허용
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
    depth=1  # 최신 1개만 유지
)

# 🟡 MEDIUM: 지도 delta, Frontier 정보 (1Hz, 손실 불허)
MAP_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,      # TCP: 보장, 약간 느림
    durability=DurabilityPolicy.TRANSIENT_LOCAL, # 늦게 참여한 로봇도 수신
    history=HistoryPolicy.KEEP_LAST,
    depth=5
)

# 🟢 LOW: 생존자 감지, Leader Election (이벤트, 반드시 전달)
EVENT_QOS = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_ALL  # 모든 이벤트 보존
)
```

---

## 3. Multi-Robot SLAM 알고리즘 선택

### 3.1 후보 비교

| 방식 | 설명 | 장점 | 단점 | GHOST-5 적합성 |
|------|------|------|------|----------------|
| 중앙화 (GCS에서 병합) | 모든 로봇이 스캔 데이터를 GCS로 전송 | 구현 단순 | GCS 다운 시 전체 마비, 대역폭 폭발 | ❌ 재난 환경 부적합 |
| Pose Graph 공유 (분산) | 각 로봇이 로컬 SLAM 후 Pose Graph만 공유 | 낮은 대역폭 | 초기 상대 위치 추정 필요 | ✅ |
| Submap 공유 (SMMR-Explore) | 변경된 Submap만 공유 | 균형잡힌 효율 | 구현 복잡도 중간 | ✅ |
| 전체 지도 주기적 전송 | 완전한 OccupancyGrid를 주기적 전송 | 단순 | 대역폭 폭발 (수 MB/cycle) | ❌ |

### 3.2 채택 결론: **분산 Pose Graph SLAM + Delta Map Update**

**근거:**
- 2025년 RAL 발표 Multi-SLAM + LPFE 논문에서 "Pose Graph 기반 글로벌 최적화 지도가 대역폭 효율적"임이 검증됐다.
- 각 로봇은 `slam_toolbox`로 로컬 SLAM을 독립 실행하고, Pose Graph 노드/엣지만 공유한다.
- 지도 데이터는 변경된 셀만 Delta Update로 전송 (전체 대비 10~20% 용량).

### 3.3 slam_toolbox 멀티 로봇 설정

```yaml
# ghost5_ws/ghost5_slam/config/slam_toolbox_params.yaml
slam_toolbox:
  ros__parameters:
    # 로봇별 네임스페이스로 분리
    odom_frame: robot_N/odom
    base_frame: robot_N/base_link
    map_frame: map  # 공통 글로벌 프레임

    # 성능 최적화 (Raspberry Pi 5 기준)
    resolution: 0.05           # 5cm 해상도
    max_laser_range: 12.0      # RPLiDAR C1 최대 범위
    minimum_travel_distance: 0.2
    minimum_travel_heading: 0.3

    # Loop Closure 설정
    loop_search_maximum_distance: 3.0
    do_loop_closing: true
    loop_match_minimum_chain_size: 3

    # 멀티 로봇 모드: 각자 독립 맵 생성
    mode: mapping
```

### 3.4 지도 병합 전략

```python
# ghost5_ws/ghost5_slam/ghost5_slam/map_merger_node.py

import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
import numpy as np

class MapMergerNode(Node):
    """
    Leader 로봇에서 실행되는 지도 병합 노드.
    각 로봇의 로컬 맵 delta를 수집하여 글로벌 맵 생성.
    """

    def __init__(self):
        super().__init__('map_merger')
        self.robot_maps = {}         # {robot_id: OccupancyGrid}
        self.prev_maps = {}          # delta 계산용 이전 맵
        self.global_map = None

        # 각 로봇의 로컬 맵 구독 (5대)
        for i in range(1, 6):
            self.create_subscription(
                OccupancyGrid,
                f'/robot_{i}/map',
                lambda msg, rid=i: self.map_callback(msg, rid),
                qos_profile=MAP_QOS
            )

        # 글로벌 맵 퍼블리셔
        self.global_map_pub = self.create_publisher(
            OccupancyGrid, '/map_merge/global_map', MAP_QOS
        )

        # 1Hz 병합 타이머
        self.create_timer(1.0, self.merge_and_publish)

    def map_callback(self, msg: OccupancyGrid, robot_id: int):
        """Delta 업데이트: 변경된 셀만 저장"""
        if robot_id in self.prev_maps:
            prev = np.array(self.prev_maps[robot_id].data)
            curr = np.array(msg.data)
            # 변경된 인덱스만 추출
            changed_indices = np.where(prev != curr)[0]
            if len(changed_indices) > 0:
                self.robot_maps[robot_id] = msg
                self.get_logger().debug(
                    f'Robot {robot_id}: {len(changed_indices)} cells updated '
                    f'({len(changed_indices)/len(curr)*100:.1f}%)'
                )
        else:
            self.robot_maps[robot_id] = msg

        self.prev_maps[robot_id] = msg

    def merge_and_publish(self):
        """모든 로봇 맵을 하나의 글로벌 맵으로 병합"""
        if len(self.robot_maps) < 2:
            return

        # 최대 범위로 글로벌 맵 초기화
        merged = self._initialize_global_map()

        # 각 로봇 맵을 글로벌 좌표로 변환 후 병합
        for robot_id, local_map in self.robot_maps.items():
            self._overlay_map(merged, local_map, robot_id)

        self.global_map_pub.publish(merged)

    def _overlay_map(self, global_map, local_map, robot_id):
        """로컬 맵을 글로벌 맵에 오버레이 (Known > Unknown 우선)"""
        # TF를 통해 로봇 위치 기반 좌표 변환 적용
        # 점유 셀이 있는 경우 글로벌 맵 업데이트
        pass  # 실제 구현 시 tf2_ros 사용
```

---

## 4. Frontier 탐색 알고리즘 선택

### 4.1 후보 비교

| 알고리즘 | 방식 | 효율 | 중복 탐색 방지 | GHOST-5 적합성 |
|----------|------|------|----------------|----------------|
| 단순 최근접 Frontier | 각 로봇이 독립적으로 가장 가까운 Frontier 선택 | 낮음 | ❌ 매우 빈번 | ❌ |
| 중앙 집중 할당 (GCS) | GCS가 모든 Frontier를 할당 | 높음 | ✅ | ❌ GCS 의존 |
| **분산 Claim 기반 (Blackboard)** | Redis/토픽으로 Frontier를 "예약"하고 할당 | 높음 | ✅ | ✅ |
| MMPF (Multi-robot Multi-target Potential Field) | 포텐셜 필드로 로봇 간 반발 + Frontier 인력 | 매우 높음 | ✅ 자동 분산 | ✅ **채택** |
| LPFE (Lightweight Predictive Frontier Exploration) | 예측 기반 Frontier 우선순위 | 높음 | ✅ | ✅ 병행 활용 |

### 4.2 채택 결론: **MMPF + Claim Blackboard 하이브리드**

**근거:**
- MMPF(Tsinghua SMMR-Explore, ICRA 2021)는 단순 최근접 대비 탐색 효율 1.03~1.62배 향상, 이동 비용 3~40% 절감을 실증했다.
- 2025년 RAL LPFE 논문은 Frontier 클러스터링으로 연산 오버헤드를 크게 낮췄다.
- 재난 환경에서는 "Goal이 앞뒤로 흔들리는 현상(back-and-forth)"이 매우 위험하므로 MMPF의 안정성이 필수적이다.

### 4.3 구현 코드

```python
# ghost5_ws/ghost5_navigation/ghost5_navigation/frontier_manager.py

import numpy as np
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import json

class FrontierManager:
    """
    MMPF 기반 분산 Frontier 할당 관리자.
    각 로봇이 독립적으로 실행하며 Blackboard를 통해 중복 방지.
    """

    def __init__(self, robot_id: int, node):
        self.robot_id = robot_id
        self.node = node
        self.claimed_frontiers = {}  # {frontier_id: robot_id}

        # Blackboard 구독 (다른 로봇의 claim 모니터링)
        self.node.create_subscription(
            String, '/swarm/frontier_claims',
            self.claim_callback, EVENT_QOS
        )
        self.claim_pub = self.node.create_publisher(
            String, '/swarm/frontier_claims', EVENT_QOS
        )

    def compute_mmpf_goal(
        self,
        frontiers: list,
        robot_poses: dict,      # {robot_id: (x, y)}
        my_pose: tuple
    ) -> tuple:
        """
        MMPF 알고리즘: 각 Frontier의 포텐셜 점수 계산
        U(f) = α·attraction(f) - β·robot_repulsion(f) - γ·claimed_penalty(f)
        """
        if not frontiers:
            return None

        best_frontier = None
        best_score = -np.inf

        for frontier in frontiers:
            # 이미 다른 로봇이 claim한 Frontier 제외
            if frontier['id'] in self.claimed_frontiers:
                continue

            fx, fy = frontier['x'], frontier['y']

            # 1. 인력: Frontier까지의 정보 이득 / 거리
            dist_to_frontier = np.sqrt(
                (fx - my_pose[0])**2 + (fy - my_pose[1])**2
            )
            info_gain = frontier.get('info_gain', 1.0)
            attraction = info_gain / (dist_to_frontier + 0.01)

            # 2. 반발력: 다른 로봇과의 거리 (가까울수록 같은 곳 탐색 방지)
            repulsion = 0.0
            for other_id, other_pose in robot_poses.items():
                if other_id == self.robot_id:
                    continue
                dist_to_robot = np.sqrt(
                    (fx - other_pose[0])**2 + (fy - other_pose[1])**2
                )
                repulsion += 1.0 / (dist_to_robot + 0.01)

            # 3. 최종 점수
            alpha, beta = 1.0, 0.5
            score = alpha * attraction - beta * repulsion

            if score > best_score:
                best_score = score
                best_frontier = frontier

        if best_frontier:
            self._claim_frontier(best_frontier['id'])

        return best_frontier

    def _claim_frontier(self, frontier_id: str):
        """Frontier claim을 Blackboard에 브로드캐스트"""
        claim_msg = json.dumps({
            'frontier_id': frontier_id,
            'robot_id': self.robot_id,
            'timestamp': self.node.get_clock().now().to_msg().sec
        })
        self.claim_pub.publish(String(data=claim_msg))
        self.claimed_frontiers[frontier_id] = self.robot_id

    def claim_callback(self, msg):
        """다른 로봇의 claim 수신 및 동기화"""
        data = json.loads(msg.data)
        fid = data['frontier_id']
        rid = data['robot_id']
        # 내 claim이 아닌 경우 등록
        if rid != self.robot_id:
            self.claimed_frontiers[fid] = rid

        # Claim 만료 처리 (30초 후 자동 해제)
        # timer로 구현 예정
```

---

## 5. 리더 선출 알고리즘 선택

### 5.1 후보 비교

| 알고리즘 | 방식 | 수렴 시간 | 복잡도 | 5대 소규모 적합성 |
|----------|------|-----------|--------|-------------------|
| Bully Algorithm | 가장 높은 ID의 생존 로봇이 Leader | O(n²) 메시지 | 낮음 | ✅ **채택** |
| Raft Consensus | 다수결 투표 기반 | O(n log n) | 높음 | 과설계 |
| Ring Election | 링 구조로 ID 전달 | O(n) | 중간 | 링 구성 불안정 |
| Token Ring | 토큰 순환 | O(n) | 낮음 | 토큰 분실 리스크 |

### 5.2 채택 결론: **Bully Algorithm + 타임아웃 기반 Heartbeat**

**근거:**
- 5대 소규모 시스템에서 Raft의 복잡성은 과설계다. Bully는 구현 단순 + 빠른 수렴.
- 재난 환경에서 빠른 Leader 전환이 생사를 가를 수 있다. Bully는 통신 단절 감지 즉시 발동된다.
- GHOST-5 데이터공유방식.md에서도 Bully를 채택하고 있으며, 카프카의 KRaft와 철학적으로 동일하다.

### 5.3 구현 코드

```python
# ghost5_ws/ghost5_swarm/ghost5_swarm/leader_election.py

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import time

class LeaderElection(Node):
    """
    Bully Algorithm 기반 분산 리더 선출.
    - Heartbeat 주기: 1초
    - Timeout: 3초 무응답 시 Leader 다운으로 판단
    """

    HEARTBEAT_INTERVAL = 1.0   # seconds
    LEADER_TIMEOUT = 3.0       # seconds

    def __init__(self, robot_id: int):
        super().__init__(f'leader_election_robot_{robot_id}')
        self.robot_id = robot_id
        self.current_leader_id = None
        self.last_heartbeat_time = {}  # {robot_id: timestamp}
        self.is_election_running = False

        # 토픽 설정
        self.election_pub = self.create_publisher(
            String, '/swarm/election', EVENT_QOS
        )
        self.heartbeat_pub = self.create_publisher(
            String, '/swarm/heartbeat', POSE_QOS
        )
        self.create_subscription(
            String, '/swarm/election',
            self.election_callback, EVENT_QOS
        )
        self.create_subscription(
            String, '/swarm/heartbeat',
            self.heartbeat_callback, POSE_QOS
        )

        # 타이머
        self.create_timer(self.HEARTBEAT_INTERVAL, self.send_heartbeat)
        self.create_timer(self.LEADER_TIMEOUT, self.check_leader_alive)

    def send_heartbeat(self):
        """Leader인 경우 Heartbeat 전송"""
        if self.current_leader_id == self.robot_id:
            msg = json.dumps({
                'type': 'HEARTBEAT',
                'from': self.robot_id,
                'timestamp': time.time()
            })
            self.heartbeat_pub.publish(String(data=msg))

    def heartbeat_callback(self, msg):
        """Heartbeat 수신 처리"""
        data = json.loads(msg.data)
        self.last_heartbeat_time[data['from']] = data['timestamp']

    def check_leader_alive(self):
        """Leader Timeout 감지 → 선거 발동"""
        if self.current_leader_id is None:
            self._start_election()
            return

        if self.current_leader_id == self.robot_id:
            return  # 나 자신이 Leader면 불필요

        last_hb = self.last_heartbeat_time.get(self.current_leader_id, 0)
        if time.time() - last_hb > self.LEADER_TIMEOUT:
            self.get_logger().warn(
                f'Leader Robot {self.current_leader_id} TIMEOUT! Starting election.'
            )
            self._start_election()

    def _start_election(self):
        """Bully Election 시작: 자신보다 높은 ID에게 ELECTION 메시지 전송"""
        if self.is_election_running:
            return
        self.is_election_running = True

        self.get_logger().info(f'Robot {self.robot_id}: Election started')
        msg = json.dumps({
            'type': 'ELECTION',
            'from': self.robot_id,
        })
        self.election_pub.publish(String(data=msg))

    def election_callback(self, msg):
        """선거 메시지 처리"""
        data = json.loads(msg.data)
        msg_type = data['type']
        from_id = data['from']

        if msg_type == 'ELECTION':
            if from_id < self.robot_id:
                # 나보다 낮은 ID의 선거 → 내가 응답하고 선거 참여
                response = json.dumps({
                    'type': 'ALIVE',
                    'from': self.robot_id
                })
                self.election_pub.publish(String(data=response))
                self._start_election()

        elif msg_type == 'ALIVE':
            # 더 높은 ID가 살아있음 → 내 선거 포기
            if from_id > self.robot_id:
                self.is_election_running = False

        elif msg_type == 'COORDINATOR':
            # 새 리더 공표
            self.current_leader_id = from_id
            self.is_election_running = False
            self.get_logger().info(
                f'New Leader: Robot {from_id}'
            )
            if from_id == self.robot_id:
                self._on_become_leader()

    def _on_become_leader(self):
        """Leader가 됐을 때 처리"""
        coordinator_msg = json.dumps({
            'type': 'COORDINATOR',
            'from': self.robot_id
        })
        self.election_pub.publish(String(data=coordinator_msg))

        # Leader 역할 수행: Redis Blackboard 초기화, Frontier 재분배 등
        self.get_logger().info(f'Robot {self.robot_id}: I am the new Leader!')
```

---

## 6. 데이터 공유 전략 최적 설계

### 6.1 채택 아키텍처 (기존 계획서 기반 최적화)

```
계층: Hierarchical (Leader + 4 Explorer)
평상시: rmw_zenoh Publish-Subscribe (ROS2 DDS 대체)
지도: Delta Update (변경 셀만 전송, 1Hz)
장애 대비: Zenoh Gossip (자동 내장)
글로벌 상태: Redis Blackboard (Leader의 Raspberry Pi에서 실행)
```

### 6.2 Redis Blackboard 스키마

```python
# ghost5_ws/ghost5_swarm/ghost5_swarm/blackboard.py

import redis
import json
from dataclasses import dataclass, asdict

@dataclass
class RobotState:
    pose: dict          # {'x': 1.2, 'y': 3.4, 'theta': 0.5}
    status: str         # 'EXPLORING' | 'VICTIM_FOUND' | 'RETURNING' | 'DOWN'
    battery: float      # 0.0 ~ 100.0
    timestamp: float

@dataclass
class VictimDetection:
    x: float
    y: float
    confidence: float
    detected_by: int    # robot_id
    timestamp: float

class GhostBlackboard:
    """
    GHOST-5 공유 상태 저장소 (Leader 로봇의 Redis 인스턴스)
    """
    # 키 만료 시간 (초)
    POSE_TTL = 5        # 위치: 5초 (HIGH 데이터)
    FRONTIER_TTL = 60   # Frontier claim: 60초 (자동 해제)
    VICTIM_TTL = 0      # 생존자: 영구 보존

    def __init__(self, leader_ip: str = 'localhost'):
        self.r = redis.Redis(host=leader_ip, port=6379, decode_responses=True)

    # ── 로봇 상태 ──────────────────────────────────
    def update_robot_state(self, robot_id: int, state: RobotState):
        key = f'robot:{robot_id}:state'
        self.r.setex(key, self.POSE_TTL, json.dumps(asdict(state)))

    def get_all_robot_states(self) -> dict:
        states = {}
        for i in range(1, 6):
            data = self.r.get(f'robot:{i}:state')
            if data:
                states[i] = json.loads(data)
        return states

    def get_alive_robots(self) -> list:
        """TTL 만료되지 않은 로봇 = 생존 로봇"""
        alive = []
        for i in range(1, 6):
            if self.r.exists(f'robot:{i}:state'):
                alive.append(i)
        return alive

    # ── Frontier Claim ────────────────────────────
    def claim_frontier(self, frontier_id: str, robot_id: int) -> bool:
        """원자적 Claim (이미 claim된 경우 False 반환)"""
        key = f'frontier:claim:{frontier_id}'
        return bool(self.r.set(
            key, robot_id,
            nx=True,              # Not Exists: 없을 때만 set
            ex=self.FRONTIER_TTL  # 자동 만료
        ))

    def release_frontier(self, frontier_id: str):
        self.r.delete(f'frontier:claim:{frontier_id}')

    # ── 생존자 감지 ───────────────────────────────
    def add_victim(self, victim: VictimDetection):
        victim_id = f'victim:{int(victim.timestamp)}'
        self.r.hset('victims', victim_id, json.dumps(asdict(victim)))
        self.get_logger.info(f'⚠️ Victim detected at ({victim.x:.2f}, {victim.y:.2f})')

    def get_all_victims(self) -> list:
        victims_raw = self.r.hgetall('victims')
        return [json.loads(v) for v in victims_raw.values()]
```

---

## 7. 보안 설계 (SROS2 기반)

### 7.1 위협 모델

재난 현장에서의 보안 위협:

| 위협 | 설명 | 대응 |
|------|------|------|
| 도청 | 생존자 위치 정보 유출 | DDS 트래픽 AES-GCM 암호화 |
| 스푸핑 | 가짜 로봇이 군집에 참여 | X.509 인증서 기반 인증 |
| 권한 탈취 | Leader 명령 위조 | DDS Access Control + 권한 파일 |
| Replay 공격 | 이전 메시지 재전송 | 타임스탬프 + Nonce |

### 7.2 SROS2 설정

```bash
# 1. Keystore 초기화 (GCS에서 1회 실행)
ros2 security create_keystore ~/ghost5_keystore

# 2. 각 로봇의 Node별 인증서 생성
for i in 1 2 3 4 5; do
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/slam_node
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/nav_node
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/swarm_node
    ros2 security create_key ~/ghost5_keystore /ghost5/robot_${i}/victim_detector
done
ros2 security create_key ~/ghost5_keystore /ghost5/gcs/monitor_node

# 3. 권한 정책 파일 생성
ros2 security generate_artifacts -k ~/ghost5_keystore -p ghost5_policy.xml
```

```xml
<!-- ghost5_policy.xml — 최소 권한 원칙 적용 -->
<policy>
  <!-- Explorer 로봇: 자신의 데이터 퍼블리시만 허용 -->
  <enclave path="/ghost5/robot_2/swarm_node">
    <profiles>
      <profile node="swarm_coordinator" ns="/robot_2">
        <topics publish="ALLOW" subscribe="ALLOW">
          <topic>swarm/frontier_claims</topic>
          <topic>swarm/election</topic>
          <topic>swarm/heartbeat</topic>
        </topics>
        <topics publish="DENY" subscribe="DENY">
          <topic>**</topic>  <!-- 그 외 모두 차단 -->
        </topics>
      </profile>
    </profiles>
  </enclave>
</policy>
```

```bash
# 4. 로봇 실행 시 보안 환경변수 설정
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
export ROS_SECURITY_KEYSTORE=~/ghost5_keystore
```

### 7.3 알려진 SROS2 취약점 및 대응

2022년 CCS 논문("On the (In)Security of Secure ROS2")에서 SROS2의 4가지 취약점이 발견됐다. 이를 GHOST-5에서 명시적으로 대응한다:

| 취약점 | 설명 | 대응책 |
|--------|------|--------|
| V1: 인증서 만료 후 미갱신 | 정책 변경 시 구 인증서가 유효 | 정책 변경 시 전체 keystore 재생성 스크립트 실행 |
| V2: 동시 참여자 정책 충돌 | 정책 업데이트 중 레이스 컨디션 | 배포 전 모든 로봇 노드 중단 → 배포 → 재시작 |
| V3: 기본 설정 취약성 | 일부 기본값이 보안 미적용 | `rtps_protection_kind: ENCRYPT` 강제 설정 |
| V4: 도메인 격리 우회 | 도메인 ID 충돌 | `ROS_DOMAIN_ID=42` 고정 + 네트워크 레벨 분리 |

---

## 8. 코드 구조 설계

```
ghost5_ws/
├── src/
│   ├── ghost5_interfaces/          # 커스텀 메시지 정의
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
│   ├── ghost5_bringup/             # 런치 파일 및 파라미터
│   │   ├── launch/
│   │   │   ├── robot.launch.py          # 단일 로봇 런치
│   │   │   ├── swarm.launch.py          # 전체 군집 런치
│   │   │   └── simulation.launch.py    # Gazebo 시뮬레이션
│   │   └── config/
│   │       ├── qos_profiles.py
│   │       ├── slam_toolbox_params.yaml
│   │       ├── nav2_params.yaml
│   │       └── zenoh_config.json5
│   │
│   ├── ghost5_slam/                # SLAM + 지도 병합
│   │   └── ghost5_slam/
│   │       ├── map_merger_node.py       # 글로벌 지도 병합 (Leader)
│   │       ├── pose_graph_publisher.py  # Pose Graph 공유
│   │       └── loop_closure_detector.py # 다중 로봇 Loop Closure
│   │
│   ├── ghost5_navigation/          # Nav2 + Frontier 탐색
│   │   └── ghost5_navigation/
│   │       ├── frontier_detector.py     # OccupancyGrid → Frontier 추출
│   │       ├── frontier_manager.py      # MMPF 기반 Frontier 할당
│   │       └── nav_goal_publisher.py    # Nav2 Goal 전송
│   │
│   ├── ghost5_swarm/               # 군집 지능
│   │   └── ghost5_swarm/
│   │       ├── leader_election.py       # Bully Algorithm
│   │       ├── blackboard.py            # Redis 공유 상태
│   │       ├── swarm_coordinator.py     # 군집 조율 노드
│   │       └── fault_handler.py         # 로봇 다운 시 임무 재배치
│   │
│   ├── ghost5_victim/              # 생존자 감지
│   │   └── ghost5_victim/
│   │       ├── proximity_detector.py    # US-016 초음파 + TCRT5000 IR 감지
│   │       ├── vision_detector.py       # 5MP 카메라 기반 인체 감지 (YOLOv8n)
│   │       ├── victim_fuser.py          # 초음파 + IR + 비전 교차 검증
│   │       └── triangulation.py         # 3대 이상 동시 감지 시 삼각측량
│   │
│   └── ghost5_viz/                 # 시각화 및 GCS
│       └── ghost5_viz/
│           ├── foxglove_publisher.py    # Foxglove 통합 지도
│           └── victim_marker.py        # 생존자 위치 마커
│
├── tests/
│   ├── test_leader_election.py          # 유닛 테스트
│   ├── test_frontier_mmpf.py
│   ├── test_map_merger.py
│   └── integration/
│       ├── test_swarm_communication.py  # 통신 통합 테스트
│       └── test_fault_tolerance.py      # 내결함성 테스트
│
└── scripts/
    ├── setup_sros2.sh                   # 보안 초기화 스크립트
    ├── deploy_to_robots.sh              # SSH 기반 배포
    └── benchmark/
        ├── measure_latency.py           # 통신 지연 측정
        └── measure_coverage.py          # 탐색 커버리지 측정
```

### 8.1 핵심 커스텀 메시지 정의

```
# ghost5_interfaces/msg/RobotState.msg
int32 robot_id
geometry_msgs/Pose2D pose
string status          # EXPLORING | VICTIM_FOUND | RETURNING | DOWN | CHARGING
float32 battery_percent
float32 coverage_percent
builtin_interfaces/Time timestamp

# ghost5_interfaces/msg/VictimDetection.msg
int32 detected_by_robot
geometry_msgs/Point location
float32 thermal_confidence
float32 audio_confidence
float32 combined_confidence
builtin_interfaces/Time timestamp

# ghost5_interfaces/msg/SwarmStatus.msg
int32 leader_id
int32[] alive_robots
int32[] victim_count
float32 global_coverage_percent
string mission_phase  # EXPLORING | VICTIM_RESCUE | RETURNING
```

---

## 9. 검증 전략 및 성능 지표

### 9.1 유닛 테스트

```python
# tests/test_leader_election.py

import pytest
import asyncio
from ghost5_swarm.leader_election import LeaderElection

class TestBullyElection:

    def test_highest_id_becomes_leader(self):
        """5대 중 가장 높은 ID가 Leader가 되는지 검증"""
        # Robot 1~5 시뮬레이션
        robots = [LeaderElection(i) for i in range(1, 6)]
        # 선거 시뮬레이션 후 Robot 5가 Leader인지 확인
        assert robots[-1].current_leader_id == 5

    def test_leader_recovery_on_timeout(self):
        """Leader 다운 시 다음 높은 ID가 Leader가 되는지 검증"""
        # Robot 5 다운 시뮬레이션 → Robot 4가 Leader 되어야 함
        pass

    def test_election_convergence_time(self):
        """선거 수렴 시간 < 3초 검증"""
        import time
        start = time.time()
        # 선거 실행
        elapsed = time.time() - start
        assert elapsed < 3.0

class TestMPPFrontier:

    def test_no_duplicate_claims(self):
        """5대 로봇이 동일 Frontier를 claim하지 않는지 검증"""
        pass

    def test_full_coverage(self):
        """표준 맵에서 5대가 100% 커버리지 달성하는지 검증"""
        pass
```

### 9.2 성능 벤치마크 지표

```python
# scripts/benchmark/measure_latency.py
"""
GHOST-5 통신 성능 측정 스크립트
목표:
  - Pose 통신 지연: < 50ms (10Hz 기준)
  - 지도 Delta 전송: < 500ms (1Hz 기준)
  - Leader Election 수렴: < 3초
  - 생존자 알림 전파: < 200ms
"""

import rclpy
from rclpy.node import Node
import time
import statistics

class LatencyBenchmark(Node):
    def __init__(self):
        super().__init__('latency_benchmark')
        self.latencies = []
        self.send_timestamps = {}

        self.pub = self.create_publisher(
            String, '/benchmark/ping', POSE_QOS
        )
        self.create_subscription(
            String, '/benchmark/pong',
            self.pong_callback, POSE_QOS
        )
        self.create_timer(0.1, self.send_ping)

    def send_ping(self):
        ts = time.time()
        msg_id = str(ts)
        self.send_timestamps[msg_id] = ts
        self.pub.publish(String(data=msg_id))

    def pong_callback(self, msg):
        now = time.time()
        if msg.data in self.send_timestamps:
            latency_ms = (now - self.send_timestamps[msg.data]) * 1000
            self.latencies.append(latency_ms)
            if len(self.latencies) % 100 == 0:
                self.get_logger().info(
                    f'Latency — Mean: {statistics.mean(self.latencies):.2f}ms, '
                    f'P95: {sorted(self.latencies)[int(len(self.latencies)*0.95)]:.2f}ms, '
                    f'Max: {max(self.latencies):.2f}ms'
                )
```

### 9.3 성능 목표 (합격 기준)

| 항목 | 목표값 | 측정 방법 |
|------|--------|-----------|
| Pose 통신 지연 | < 50ms (P95) | LatencyBenchmark 노드 |
| 지도 Delta 전송 시간 | < 500ms | map_merger 로그 분석 |
| Leader Election 수렴 | < 3초 | 전원 차단 후 재선거 타이밍 |
| 생존자 알림 전파 | < 200ms | victim_detector → GCS 타임스탬프 |
| 탐색 커버리지 (10분) | > 80% | OccupancyGrid 커버리지 계산 |
| 내결함성 (1대 다운) | 임무 계속 유지 | 강제 종료 후 나머지 4대 동작 확인 |
| 중복 탐색 비율 | < 5% | 각 로봇 경로 오버랩 면적 계산 |

### 9.4 시뮬레이션 → 실제 검증 단계

```
Phase 1: Gazebo 시뮬레이션
  ├── B.A.T.M.A.N. Mesh 네트워크 에뮬레이션 (tc qdisc로 손실 주입)
  ├── 5개 TurtleBot3 모델 동시 실행
  └── 성능 지표 자동 수집 (rosbag2)

Phase 2: 실제 하드웨어 단일 로봇
  ├── Raspberry Pi 5 + RPLiDAR C1 + US-016 초음파 + TCRT5000 IR 연동
  ├── rmw_zenoh 통신 안정성 확인
  └── slam_toolbox 실내 SLAM 정확도 확인

Phase 3: 2대 로봇 멀티 통신
  ├── Zenoh Gossip 기반 지도 공유 검증
  ├── Leader Election 수렴 테스트
  └── 지도 병합 정확도 측정 (Ground Truth 대비 RMSE)

Phase 4: 5대 군집 통합
  ├── 실내 재난 시나리오 모의 환경 구성
  ├── 전체 벤치마크 지표 측정
  └── 로봇 1대 강제 종료 내결함성 테스트
```

---

## 10. MEM 논문에서 얻은 아키텍처 인사이트

Physical Intelligence의 MEM 논문(2025)은 로봇 메모리 아키텍처에서 중요한 통찰을 제공한다. 이를 GHOST-5에 적용하면:

### 10.1 핵심 인사이트: 다중 시간 스케일 메모리

MEM은 로봇 정책이 **단기(비디오 기반)와 장기(언어 기반) 메모리**를 결합해야 함을 입증했다. GHOST-5는 이를 데이터 공유에 직접 적용한다:

| MEM 개념 | GHOST-5 대응 |
|----------|-------------|
| Short-Term Video Memory (초 단위) | `POSE_QOS` 10Hz 실시간 로봇 위치 공유 |
| Long-Term Language Memory (분 단위) | Redis Blackboard의 탐색 히스토리, 생존자 위치 |
| Memory Compression (요약) | Delta Map Update (변경분만 전송) |
| Distribution Shift 방지 | Frontier Claim 만료(TTL 60초) 자동 해제 |

### 10.2 Compression의 중요성

MEM에서 "실패한 시도를 메모리에 기록하지 않아 학습-추론 분포 차이를 최소화"한다는 원칙처럼, GHOST-5도 **불필요한 상태 정보를 적극적으로 만료**시킨다:

```python
# 탐색이 완료된 구역의 Frontier claim 자동 만료
FRONTIER_TTL = 60  # 60초 후 자동 해제

# 오래된 로봇 위치는 5초 후 자동 만료 (다운된 로봇 자동 감지)
POSE_TTL = 5
```

### 10.3 계층적 정책 구조

MEM의 High-Level/Low-Level 정책 분리는 GHOST-5의 Leader/Explorer 구조와 정확히 대응한다:

```
MEM:
  πHL (고수준) → 언어 메모리 관리, 서브태스크 지시
  πLL (저수준) → 실제 조작 동작

GHOST-5:
  Leader (고수준) → 글로벌 맵 관리, Frontier 재분배, GCS 보고
  Explorer (저수준) → 로컬 SLAM, 탐색 실행, 생존자 감지
```

---

## 11. 🆕 보완 설계 — 2.5D Elevation Map 융합 (LiDAR 기반)

### 11.1 문제 정의: 2D SLAM의 재난 환경 한계

현재 설계는 RPLiDAR의 **수평 단일 스캔면**만 사용하는 slam_toolbox 기반이다. 재난 환경에서는 다음 문제가 발생한다:

| 문제 | 원인 | 결과 |
|------|------|------|
| **잔해 오인식** | 지면 돌출물을 2D 레이저가 벽으로 오인 | 통과 가능 경로를 막힌 것으로 판단 |
| **단차(step) 미감지** | 수평 단면만 스캔 → Z축 정보 없음 | 로봇 転倒 위험 |
| **낮은 잔해 무시** | 스캔 높이보다 낮은 잔해는 free space로 처리 | 바퀴 걸림 |
| **좁은 공간 오판** | 천장 붕괴 공간을 통과 가능으로 오판 | 로봇 끼임 |

**해결책**: RPLiDAR를 **고정 수평 장착 + 추가 틸트 장착(또는 수직 스윕)** 구성으로 바꾸거나, 5MP 카메라 depth 정보를 보조로 활용하는 대신, **LiDAR 자체의 다중 높이 스캔 데이터를 활용**한다.

GHOST-5 하드웨어 기준으로 가장 현실적인 방법은:
- **RPLiDAR를 수평 + 소폭 틸트(~15도 하방)** 로 추가 장착하여 전방 지면 스캔
- 두 스캔면의 Z축 차이로 장애물 높이를 추정하여 Elevation Layer 생성

> 📌 **단일 RPLiDAR인 경우**: 로봇 이동 중 LiDAR 높이 변화를 이용한 **수직 스캔 누적(Z-stack)** 방식으로도 구현 가능하다 (아래 11.4절 참조).

### 11.2 하드웨어 구성 옵션

```
옵션 A — RPLiDAR 2대 (권장)
  RPLiDAR #1 (수평, 지상 15cm): 기존 slam_toolbox SLAM 전용
  RPLiDAR #2 (15° 하방 틸트, 지상 25cm): 전방 지면 장애물 높이 감지
  → 두 스캔면의 차이로 장애물 높이 추정

옵션 B — RPLiDAR 1대 + 5MP 카메라 (현 하드웨어 그대로)
  RPLiDAR (수평): SLAM 전용
  5MP 카메라: 근거리 장애물 높이 추정 (RGB → 색상/텍스처 기반)
  → 카메라로 잔해 높이 분류 (NPU 활용)

옵션 C — RPLiDAR 1대, Z-stack 누적 (소프트웨어만)
  이동 중 LiDAR 포인트를 3D 누적
  → 정적 잔해 높이 점진적 파악
  → 가장 저렴하지만 초기 탐색 전까지 정보 부재
```

**GHOST-5 채택: 옵션 B** — 추가 하드웨어 비용 없이 현재 5MP 카메라를 활용하되, **LiDAR 스캔과 카메라 이미지의 기하학적 융합**으로 접근한다. LiDAR가 감지한 장애물 포인트에 카메라 픽셀을 대응시켜 높이를 추정하므로, 별도 깊이 추정 모델 없이도 동작한다.

### 11.3 LiDAR-Camera 기하학적 융합 파이프라인

```
RPLiDAR (수평 스캔)           5MP 카메라 (전방)
        ↓                           ↓
  2D LaserScan             Image (BGR)
        ↓                           ↓
  scan_to_3d_node       ─────── lidar_camera_fusion_node
  (z=0으로 고정 투영)     TF 기반 3D→2D 투영, 픽셀 대응
        ↓
  장애물 포인트 (x, y, 0)  + 카메라 픽셀 색상/밝기
        ↓
  장애물 높이 추정
   - 수직 엣지(vertical edge): 높은 잔해
   - 수평 텍스처(flat texture): 낮은 잔해
        ↓
  ElevationGrid (OccupancyGrid)
        ↓
  Nav2 Costmap elevation_layer 플러그인
```

### 11.4 단일 RPLiDAR Z-stack 누적 방식 (소프트웨어 전용)

LiDAR가 1대뿐이고 카메라 융합도 원치 않는 경우, 로봇 이동 중 LiDAR 포인트를 3D로 누적해 Elevation 정보를 점진적으로 구축한다.

```python
# ghost5_ws/ghost5_slam/ghost5_slam/lidar_elevation_node.py

import rclpy
from rclpy.node import Node
import numpy as np
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid
import tf2_ros

class LidarElevationNode(Node):
    """
    RPLiDAR 단일 수평 스캔 + 로봇 이동 궤적을 이용한 Z-stack 누적.

    원리:
      - RPLiDAR는 설치 높이(예: 지상 15cm)에서 수평 스캔
      - 로봇이 이동하면서 동일 (x,y) 위치에서 여러 번 스캔
      - LiDAR 빔이 장애물 '상단'을 스치면 그 높이를 추정 가능
      - 단, 이 방식은 탐색 초기에는 Elevation 정보가 부족하므로
        이동 누적과 함께 점진적으로 개선됨

    장착 전제:
      - RPLiDAR 장착 높이: 지상 15cm (LIDAR_MOUNT_HEIGHT)
      - 스캔면은 수평 (tilt = 0°)
    """

    LIDAR_MOUNT_HEIGHT = 0.15   # RPLiDAR 장착 높이 (m)
    GRID_RESOLUTION    = 0.05   # 5cm 격자 해상도
    MAX_RANGE          = 12.0   # RPLiDAR C1 최대 유효 거리 (m)

    # 높이 추정 기준 (LiDAR 빔이 닿은 높이 = 장애물이 최소 이 높이)
    # LiDAR 빔이 수평이므로, 장착 높이 이상의 장애물만 감지됨
    # 즉, 15cm 이하의 잔해는 LiDAR를 통과해 감지 불가 → Pi Camera 보완 필요

    def __init__(self, robot_id: int):
        super().__init__(f'lidar_elevation_robot_{robot_id}')
        self.robot_id = robot_id
        self.elevation_cells = {}     # {(gx, gy): {'min_height': float, 'hit_count': int}}
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.create_subscription(
            LaserScan,
            f'/robot_{robot_id}/scan',
            self.scan_callback,
            10
        )
        self.elev_pub = self.create_publisher(
            OccupancyGrid,
            f'/robot_{robot_id}/elevation_layer',
            MAP_QOS
        )
        # 2Hz로 Elevation 레이어 퍼블리시
        self.create_timer(0.5, self.publish_elevation)

    def scan_callback(self, msg: LaserScan):
        """
        LiDAR 스캔 → 월드 좌표 변환 → Elevation 셀 업데이트.
        RPLiDAR 수평 스캔 빔이 장애물에 닿은 위치 = 최소 LIDAR_MOUNT_HEIGHT 높이 보장.
        """
        try:
            tf = self.tf_buffer.lookup_transform(
                'map',
                f'robot_{self.robot_id}/laser',
                rclpy.time.Time()
            )
        except Exception:
            return

        robot_x = tf.transform.translation.x
        robot_y = tf.transform.translation.y
        yaw = self._quat_to_yaw(tf.transform.rotation)

        angle = msg.angle_min
        for r in msg.ranges:
            if not (msg.range_min < r < min(msg.range_max, self.MAX_RANGE)):
                angle += msg.angle_increment
                continue

            # 월드 좌표 변환
            wx = robot_x + r * np.cos(yaw + angle)
            wy = robot_y + r * np.sin(yaw + angle)

            gx = int(wx / self.GRID_RESOLUTION)
            gy = int(wy / self.GRID_RESOLUTION)
            key = (gx, gy)

            # LiDAR 빔이 닿은 = 최소 LIDAR_MOUNT_HEIGHT 이상의 장애물 존재
            if key not in self.elevation_cells:
                self.elevation_cells[key] = {
                    'min_height': self.LIDAR_MOUNT_HEIGHT,
                    'hit_count': 1
                }
            else:
                self.elevation_cells[key]['hit_count'] += 1

            angle += msg.angle_increment

    def publish_elevation(self):
        """누적된 Elevation 셀을 OccupancyGrid로 변환해 퍼블리시"""
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
        grid.header.stamp = self.get_clock().now().to_msg()
        grid.info.resolution = self.GRID_RESOLUTION
        grid.info.width  = width
        grid.info.height = height
        grid.info.origin.position.x = min_x * self.GRID_RESOLUTION
        grid.info.origin.position.y = min_y * self.GRID_RESOLUTION
        grid.data = [-1] * (width * height)

        for (gx, gy), info in self.elevation_cells.items():
            idx = (gy - min_y) * width + (gx - min_x)
            h = info['min_height']

            # RPLiDAR 장착 높이(15cm) 기준 비용 할당
            # - 장착 높이보다 낮은 장애물: LiDAR가 감지 못함 (→ Pi Camera 보완)
            # - 장착 높이(15cm) 수준: 로봇이 통과 가능하지만 주의 필요
            # - 로봇 높이(22cm) 이상: 통과 불가
            if h < 0.10:
                cost = 10     # 낮은 잔해 (통과 가능)
            elif h < 0.22:
                cost = 60     # 주의 필요 (로봇 높이에 근접)
            else:
                cost = 100    # 통과 불가

            grid.data[idx] = cost

        self.elev_pub.publish(grid)

    def _quat_to_yaw(self, q) -> float:
        """쿼터니언 → yaw 각도 변환"""
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return np.arctan2(siny, cosy)
```

### 11.5 5MP 카메라 보완 — LiDAR 사각지대(15cm 이하) 감지

RPLiDAR 수평 스캔은 장착 높이(15cm) 이하의 잔해를 감지하지 못한다. 5MP 카메라로 이 사각지대를 보완한다. **LiDAR가 이미 감지한 장애물 위치에 카메라 픽셀을 투영**해 낮은 잔해의 존재 여부를 확인한다.

```python
# ghost5_ws/ghost5_slam/ghost5_slam/camera_low_obstacle_node.py

import rclpy
from rclpy.node import Node
import numpy as np
import cv2
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, LaserScan
from nav_msgs.msg import OccupancyGrid
from message_filters import ApproximateTimeSynchronizer, Subscriber

class CameraLowObstacleNode(Node):
    """
    5MP 카메라로 LiDAR 사각지대(15cm 이하 잔해) 감지.

    방법:
      - LiDAR free space(장애물 없음) 판정 구역을 카메라로 재확인
      - 해당 픽셀의 밝기/색상/텍스처 변화로 낮은 잔해 존재 판단
      - Hailo NPU 불필요: 경량 OpenCV 처리로 충분
    """

    # 낮은 잔해 판단 기준 (경험적 임계값, 현장 조정 필요)
    TEXTURE_VAR_THRESH = 800.0   # 텍스처 분산 임계값 (잔해 = 높은 분산)
    EDGE_DENSITY_THRESH = 0.15   # 엣지 밀도 임계값

    def __init__(self, robot_id: int):
        super().__init__(f'camera_low_obs_robot_{robot_id}')
        self.robot_id = robot_id
        self.bridge = CvBridge()

        # LiDAR + 카메라 시간 동기화 구독
        scan_sub = Subscriber(self, LaserScan, f'/robot_{robot_id}/scan')
        img_sub  = Subscriber(self, Image, f'/robot_{robot_id}/camera/image_raw')
        self.sync = ApproximateTimeSynchronizer(
            [scan_sub, img_sub], queue_size=5, slop=0.1
        )
        self.sync.registerCallback(self.sync_callback)

        self.low_obs_pub = self.create_publisher(
            OccupancyGrid,
            f'/robot_{robot_id}/low_obstacle_layer',
            MAP_QOS
        )

    def sync_callback(self, scan_msg: LaserScan, img_msg: Image):
        """LiDAR + 카메라 동기 처리 → 낮은 잔해 레이어 생성"""
        img = self.bridge.imgmsg_to_cv2(img_msg, 'bgr8')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 이미지 하단 1/3만 처리 (지면 영역)
        h, w = gray.shape
        ground_region = gray[2*h//3:, :]

        # Canny 엣지 + 텍스처 분산으로 잔해 판단
        edges = cv2.Canny(ground_region, 50, 150)
        edge_density = np.mean(edges > 0)

        # 블록별 텍스처 분산 계산 (32x32 블록)
        low_obstacle_mask = self._compute_texture_mask(ground_region)

        # 결과를 OccupancyGrid로 변환 (LiDAR free space 범위 내)
        grid = self._mask_to_grid(low_obstacle_mask, scan_msg)
        self.low_obs_pub.publish(grid)

    def _compute_texture_mask(self, region: np.ndarray) -> np.ndarray:
        """
        32x32 블록별 분산 계산 → 잔해 마스크 생성.
        높은 분산 = 잔해 존재 가능성
        """
        h, w = region.shape
        mask = np.zeros((h // 32, w // 32), dtype=np.uint8)

        for i in range(0, h - 32, 32):
            for j in range(0, w - 32, 32):
                block = region[i:i+32, j:j+32].astype(np.float32)
                variance = np.var(block)
                if variance > self.TEXTURE_VAR_THRESH:
                    mask[i//32, j//32] = 60  # 주의 비용

        return mask

    def _mask_to_grid(self, mask: np.ndarray,
                      scan: LaserScan) -> OccupancyGrid:
        """텍스처 마스크 → OccupancyGrid 변환 (간략 구현)"""
        grid = OccupancyGrid()
        grid.header.frame_id = f'robot_{self.robot_id}/base_link'
        grid.header.stamp = self.get_clock().now().to_msg()
        grid.info.resolution = 0.05
        grid.info.width  = mask.shape[1]
        grid.info.height = mask.shape[0]
        grid.data = mask.flatten().tolist()
        return grid
```

### 11.6 map_merger_node.py — 3개 레이어 통합

```python
# ghost5_slam/map_merger_node.py — 레이어 통합 부분

class MapMergerNode(Node):
    """
    3개 레이어를 통합한 글로벌 맵 생성:
      Layer 1: 2D OccupancyGrid (slam_toolbox, LiDAR 수평 스캔)
      Layer 2: Elevation Layer  (lidar_elevation_node, Z-stack)
      Layer 3: LowObstacle Layer (camera_low_obstacle_node, 15cm 이하)
    """

    def __init__(self):
        super().__init__('map_merger_v2')
        self.robot_maps      = {}   # {robot_id: OccupancyGrid}
        self.robot_elevations = {}  # {robot_id: OccupancyGrid}
        self.robot_low_obs   = {}   # {robot_id: OccupancyGrid}

        for i in range(1, 6):
            self.create_subscription(
                OccupancyGrid, f'/robot_{i}/map',
                lambda m, r=i: self.map_callback(m, r), MAP_QOS
            )
            self.create_subscription(
                OccupancyGrid, f'/robot_{i}/elevation_layer',
                lambda m, r=i: self._store(self.robot_elevations, m, r), MAP_QOS
            )
            self.create_subscription(
                OccupancyGrid, f'/robot_{i}/low_obstacle_layer',
                lambda m, r=i: self._store(self.robot_low_obs, m, r), MAP_QOS
            )

        self.global_map_pub  = self.create_publisher(
            OccupancyGrid, '/map_merge/global_map', MAP_QOS
        )
        self.global_elev_pub = self.create_publisher(
            OccupancyGrid, '/map_merge/elevation_global', MAP_QOS
        )
        self.create_timer(1.0, self.merge_and_publish)

    def _store(self, store: dict, msg: OccupancyGrid, robot_id: int):
        store[robot_id] = msg

    def merge_and_publish(self):
        """레이어 1+2+3을 최대 비용으로 통합"""
        # 1. 2D 맵 병합 (기존 로직)
        self._merge_2d_maps()

        # 2. Elevation + LowObstacle 병합 후 퍼블리시
        merged = {}
        for store in [self.robot_elevations, self.robot_low_obs]:
            for robot_id, grid in store.items():
                for idx, cost in enumerate(grid.data):
                    if cost <= 0:
                        continue
                    # 로컬 → 글로벌 좌표 변환 (TF 기반)
                    key = self._local_idx_to_world_key(idx, grid, robot_id)
                    if key and (key not in merged or merged[key] < cost):
                        merged[key] = cost  # 최대 비용 우선

        if merged:
            self.global_elev_pub.publish(
                self._cells_to_grid(merged, frame='map')
            )

    def _local_idx_to_world_key(self, idx: int, grid: OccupancyGrid,
                                 robot_id: int):
        """로컬 그리드 인덱스 → 월드 격자 키 변환 (TF 사용)"""
        try:
            tf = self.tf_buffer.lookup_transform(
                'map', f'robot_{robot_id}/base_link', rclpy.time.Time()
            )
        except Exception:
            return None

        lx = (idx % grid.info.width) * grid.info.resolution \
             + grid.info.origin.position.x
        ly = (idx // grid.info.width) * grid.info.resolution \
             + grid.info.origin.position.y

        wx = lx + tf.transform.translation.x
        wy = ly + tf.transform.translation.y
        return (int(wx / 0.05), int(wy / 0.05))
```

### 11.7 Nav2 Costmap 설정

```yaml
# ghost5_bringup/config/nav2_params.yaml

local_costmap:
  local_costmap:
    ros__parameters:
      # 3개 레이어 통합
      plugins: ["obstacle_layer", "elevation_layer", "low_obs_layer", "inflation_layer"]

      obstacle_layer:   # LiDAR 수평 스캔 (기존)
        plugin: "nav2_costmap_2d::ObstacleLayer"
        observation_sources: scan
        scan.topic: /robot_N/scan

      elevation_layer:  # LiDAR Z-stack Elevation (신규)
        plugin: "nav2_costmap_2d::StaticLayer"
        map_topic: /robot_N/elevation_layer
        map_subscribe_transient_local: true
        combination_method: 1  # 최대값 취합

      low_obs_layer:    # 카메라 15cm 이하 잔해 (신규)
        plugin: "nav2_costmap_2d::StaticLayer"
        map_topic: /robot_N/low_obstacle_layer
        combination_method: 1

      inflation_layer:
        inflation_radius: 0.25   # 잔해 주변 25cm 팽창
        cost_scaling_factor: 3.0

global_costmap:
  global_costmap:
    ros__parameters:
      plugins: ["static_layer", "elevation_layer", "inflation_layer"]
      elevation_layer:
        plugin: "nav2_costmap_2d::StaticLayer"
        map_topic: /map_merge/elevation_global
        combination_method: 1
```

### 11.8 높이 감지 한계 및 대응 전략 요약

```
LiDAR 수평 스캔 (장착 높이 15cm)
  ✅ 감지 가능: 15cm 이상 장애물 (벽, 큰 잔해, 문)
  ❌ 감지 불가: 15cm 미만 저고도 잔해

5MP 카메라 (텍스처 분석)
  ✅ 보완: 5~15cm 저고도 잔해 (높은 텍스처 분산으로 판단)
  ❌ 한계: 텍스처 없는 평평한 잔해, 조명 불량 환경

LiDAR Z-stack 누적
  ✅ 보완: 이동 궤적이 쌓이면서 점진적 높이 맵 개선
  ❌ 한계: 탐색 초기 / 처음 방문 구역에서 정보 부재

결론: 3개 레이어 합산 → 단일 방법 대비 사각지대 대폭 축소
```

---

## 12. 🆕 보완 설계 — Semantic Event Memory

### 12.1 문제 정의: 단순 상태 저장소의 한계

기존 `GhostBlackboard`는 **현재 상태(State)**만 저장한다:
- 로봇 위치, 배터리, 탐색 상태

그러나 Leader 교체 시 다음 정보가 소실된다:
- "로봇 3호가 B구역 입구에서 통신 단절됨"
- "C방은 문이 잠겨 진입 실패 2회"
- "D구역 북쪽에서 인체 감지(YOLOv8n) 반응 있었으나 확인 실패"

이는 MEM 논문에서 강조한 **장기 언어 메모리(Long-Term Language Memory)**의 부재와 정확히 같은 문제다.

### 12.2 Semantic Event Memory 설계

MEM의 언어 메모리 압축 원칙을 적용한다:
- 성공한 이벤트만 기록 (실패는 "시도됨"으로 요약, 상세 제거)
- 불필요해진 이벤트는 자동 압축/삭제
- Leader 교체 시 전체 Event Log 즉시 승계

```python
# ghost5_ws/ghost5_swarm/ghost5_swarm/semantic_memory.py

import redis
import json
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional

class EventType(Enum):
    # 탐색 이벤트
    ZONE_ENTERED     = "zone_entered"
    ZONE_COMPLETED   = "zone_completed"
    ZONE_BLOCKED     = "zone_blocked"       # 진입 불가
    # 통신 이벤트
    COMM_LOST        = "comm_lost"          # 통신 단절
    COMM_RESTORED    = "comm_restored"
    ROBOT_ISOLATED   = "robot_isolated"     # 완전 고립
    # 생존자 이벤트
    VICTIM_SUSPECTED = "victim_suspected"   # 의심 감지
    VICTIM_CONFIRMED = "victim_confirmed"   # 확인됨
    VICTIM_RESCUED   = "victim_rescued"
    # 장애물 이벤트
    DOOR_LOCKED      = "door_locked"        # 잠긴 문
    DEBRIS_BLOCKING  = "debris_blocking"    # 잔해 차단
    PASSABLE_FOUND   = "passable_found"     # 통로 발견

@dataclass
class SemanticEvent:
    event_id: str
    event_type: str          # EventType 값
    robot_id: int
    location: dict           # {'x': float, 'y': float}
    zone_id: Optional[str]   # 해당 구역 ID
    description: str         # 자연어 요약 (Leader 승계 시 사용)
    attempt_count: int        # 실패 횟수 (압축 기준)
    timestamp: float
    resolved: bool            # True = 이미 처리됨 (압축 대상)

class SemanticMemory:
    """
    GHOST-5 의미론적 이벤트 메모리.
    MEM 논문의 언어 메모리 압축 원칙을 적용:
    - 실패한 시도는 요약만 보존
    - Leader 교체 시 전체 컨텍스트 즉시 승계
    """

    # 이벤트 보존 정책
    RESOLVED_EVENT_TTL = 300   # 처리된 이벤트: 5분 후 만료
    ACTIVE_EVENT_TTL   = 0     # 미처리 이벤트: 영구 보존
    MAX_ATTEMPT_BEFORE_SKIP = 3  # 3회 실패 후 해당 구역 우선순위 하락

    def __init__(self, leader_ip: str = 'localhost'):
        self.r = redis.Redis(host=leader_ip, port=6379, decode_responses=True)

    # ── 이벤트 기록 ──────────────────────────────────
    def record_event(self, event: SemanticEvent):
        """
        새 이벤트를 메모리에 기록.
        MEM의 '성공한 서브태스크만 메모리에 통합' 원칙 적용.
        """
        key = f'event:{event.event_id}'

        # 실패 이벤트: attempt_count만 증가 (상세 내용은 최소화)
        existing = self.r.get(key)
        if existing:
            data = json.loads(existing)
            data['attempt_count'] += 1
            data['description'] = self._compress_description(
                data['description'], data['attempt_count']
            )
            self.r.set(key, json.dumps(data))
        else:
            self.r.set(key, json.dumps(asdict(event)))

        # 이벤트 목록에 추가 (타임스탬프 기반 정렬)
        self.r.zadd('events:timeline', {event.event_id: event.timestamp})

        self.get_logger().info(
            f'[SemanticMemory] {event.event_type}: {event.description}'
        )

    def _compress_description(self, desc: str, attempts: int) -> str:
        """
        MEM의 압축 원칙: 실패 횟수가 늘수록 설명을 간략화.
        예: "로봇 3이 C구역 문을 3회 시도했으나 진입 실패"
        """
        if attempts >= self.MAX_ATTEMPT_BEFORE_SKIP:
            return f"{desc.split(':')[0]}: {attempts}회 시도 실패 — 스킵 권고"
        return desc

    def record_zone_blocked(self, robot_id: int, zone_id: str,
                            location: dict, reason: str):
        """구역 진입 불가 이벤트 기록"""
        event_id = f'blocked:{zone_id}'
        existing_raw = self.r.get(f'event:{event_id}')
        attempts = 1
        if existing_raw:
            attempts = json.loads(existing_raw).get('attempt_count', 0) + 1

        event = SemanticEvent(
            event_id=event_id,
            event_type=EventType.ZONE_BLOCKED.value,
            robot_id=robot_id,
            location=location,
            zone_id=zone_id,
            description=f'Robot {robot_id}: {zone_id} 진입 불가 — {reason}',
            attempt_count=attempts,
            timestamp=time.time(),
            resolved=False
        )
        self.record_event(event)

    def record_comm_lost(self, robot_id: int, last_known_location: dict):
        """통신 단절 이벤트 기록"""
        event = SemanticEvent(
            event_id=f'comm_lost:robot_{robot_id}',
            event_type=EventType.COMM_LOST.value,
            robot_id=robot_id,
            location=last_known_location,
            zone_id=None,
            description=(
                f'Robot {robot_id}: ({last_known_location["x"]:.1f}, '
                f'{last_known_location["y"]:.1f}) 에서 통신 단절'
            ),
            attempt_count=1,
            timestamp=time.time(),
            resolved=False
        )
        self.record_event(event)

    # ── Leader 승계 지원 ───────────────────────────────
    def get_context_summary(self) -> str:
        """
        현재 모든 미처리 이벤트를 자연어 요약으로 반환.
        새 Leader가 즉시 상황을 파악할 수 있도록 한다.
        MEM의 Language Memory mt → mt+1 업데이트 개념과 동일.
        """
        event_ids = self.r.zrange('events:timeline', 0, -1)
        active_events = []

        for eid in event_ids:
            raw = self.r.get(f'event:{eid}')
            if raw:
                ev = json.loads(raw)
                if not ev.get('resolved', False):
                    active_events.append(ev['description'])

        if not active_events:
            return "현재 미처리 이벤트 없음. 정상 탐색 진행 중."

        summary = "현재 상황 요약:\n"
        for i, desc in enumerate(active_events, 1):
            summary += f"  {i}. {desc}\n"

        return summary

    def get_skip_zones(self) -> list:
        """
        3회 이상 실패한 구역 목록 반환.
        Frontier 탐색에서 이 구역의 우선순위를 낮춘다.
        """
        skip_zones = []
        event_ids = self.r.zrange('events:timeline', 0, -1)
        for eid in event_ids:
            raw = self.r.get(f'event:{eid}')
            if raw:
                ev = json.loads(raw)
                if (ev.get('event_type') == EventType.ZONE_BLOCKED.value and
                        ev.get('attempt_count', 0) >= self.MAX_ATTEMPT_BEFORE_SKIP):
                    skip_zones.append(ev.get('zone_id'))
        return skip_zones

    def mark_resolved(self, event_id: str):
        """이벤트 처리 완료 → TTL 설정 (5분 후 자동 만료)"""
        key = f'event:{event_id}'
        raw = self.r.get(key)
        if raw:
            data = json.loads(raw)
            data['resolved'] = True
            self.r.setex(key, self.RESOLVED_EVENT_TTL, json.dumps(data))
```

### 12.3 Leader 교체 시 컨텍스트 승계 흐름

```
기존 Leader (Robot 5) 다운
        ↓
새 Leader 선출 (Robot 4, Bully Algorithm)
        ↓
Robot 4의 LeaderElection._on_become_leader() 호출
        ↓
semantic_memory.get_context_summary() 호출
        ↓
"현재 상황 요약:
  1. Robot 3: (2.1, -1.5) 에서 통신 단절
  2. Robot 2: C구역 문 2회 시도 실패
  3. Robot 1: D구역 북쪽 인체 감지 의심 반응 (미확인)"
        ↓
Robot 4가 위 컨텍스트 기반으로 임무 재분배
(Robot 3 마지막 위치로 Rendezvous 로봇 파견 등)
```

---

## 13. 🆕 보완 설계 — Rendezvous 프로토콜 (통신 단절 대응)

### 13.1 문제 정의: 완전 고립 로봇의 공백

기존 설계는 Zenoh Gossip으로 통신 단절에 대응하지만, **완전 고립(모든 이웃과 통신 불가)** 상황에 대한 명시적 프로토콜이 부재하다.

완전 고립 시 발생하는 문제:
- 고립 로봇이 계속 Frontier를 탐색하면 중복 탐색 발생
- 군집이 고립 로봇의 상태를 모르므로 임무 공백 발생
- 고립 로봇이 생존자를 발견해도 보고 불가

### 13.2 Communication-Aware Navigation (통신 인식 내비게이션)

**신호 강도 기반 내비게이션**을 `swarm_coordinator.py`에 추가한다:

```python
# ghost5_ws/ghost5_swarm/ghost5_swarm/comm_monitor.py

import subprocess
import re
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
import json

class CommMonitor(Node):
    """
    WiFi 신호 강도를 모니터링하고 통신 단절 임박 시 자동 복귀 트리거.
    Communication-Aware Navigation의 핵심 노드.
    """

    # 신호 강도 임계값 (dBm)
    WARN_RSSI  = -70   # 경고: 통신 불안정 시작
    CRIT_RSSI  = -80   # 위험: 즉시 복귀 또는 랑데부 지점으로 이동
    LOST_RSSI  = -90   # 단절: 통신 완전 차단으로 간주

    # 랑데부 전략
    RENDEZVOUS_WAIT_SEC = 30   # 복귀 후 대기 시간 (재연결 시도)
    LAST_KNOWN_BUFFER   = 5    # 마지막 통신 위치 저장 개수

    def __init__(self, robot_id: int, interface: str = 'wlan0'):
        super().__init__(f'comm_monitor_robot_{robot_id}')
        self.robot_id = robot_id
        self.interface = interface
        self.last_good_positions = []  # 통신 양호했던 위치 이력
        self.current_rssi = 0
        self.rendezvous_mode = False

        # RSSI 퍼블리셔
        self.rssi_pub = self.create_publisher(Float32, f'/robot_{robot_id}/rssi', POSE_QOS)
        self.comm_event_pub = self.create_publisher(String, '/swarm/comm_events', EVENT_QOS)

        # 0.5Hz로 신호 강도 측정
        self.create_timer(2.0, self.measure_and_act)

    def measure_and_act(self):
        """신호 강도 측정 → 임계값 기반 행동 결정"""
        rssi = self._get_wifi_rssi()
        self.current_rssi = rssi
        self.rssi_pub.publish(Float32(data=float(rssi)))

        if rssi >= self.WARN_RSSI:
            # 정상: 현재 위치를 "좋은 위치"로 기록
            self._record_good_position()
            if self.rendezvous_mode:
                self._exit_rendezvous_mode()

        elif rssi >= self.CRIT_RSSI:
            # 경고: Nav2에 현재 속도 50% 감속 요청
            self.get_logger().warn(
                f'Robot {self.robot_id}: RSSI 경고 {rssi}dBm — 속도 감속'
            )
            self._request_speed_reduction(0.5)

        elif rssi >= self.LOST_RSSI:
            # 위험: 즉시 랑데부 모드 진입
            self.get_logger().error(
                f'Robot {self.robot_id}: RSSI 위험 {rssi}dBm — 랑데부 모드 진입'
            )
            self._enter_rendezvous_mode()

        else:
            # 단절: 완전 고립 프로토콜
            self.get_logger().error(
                f'Robot {self.robot_id}: 통신 완전 단절 — 자율 복귀 시작'
            )
            self._autonomous_return()

    def _enter_rendezvous_mode(self):
        """
        통신 임박 단절 시 랑데부 모드:
        1. 마지막으로 신호가 양호했던 위치로 복귀
        2. 도착 후 30초 대기 (재연결 시도)
        3. 재연결 실패 시 자율 복귀 시작
        """
        if self.rendezvous_mode:
            return
        self.rendezvous_mode = True

        # SemanticMemory에 이벤트 기록
        event = json.dumps({
            'type': 'COMM_DEGRADED',
            'robot_id': self.robot_id,
            'rssi': self.current_rssi,
            'timestamp': self.get_clock().now().nanoseconds
        })
        self.comm_event_pub.publish(String(data=event))

        # 마지막 통신 양호 위치로 Nav2 목표 설정
        if self.last_good_positions:
            last_good = self.last_good_positions[-1]
            self._navigate_to(last_good['x'], last_good['y'])
            self.get_logger().info(
                f'랑데부 지점으로 이동: ({last_good["x"]:.2f}, {last_good["y"]:.2f})'
            )

    def _autonomous_return(self):
        """
        완전 고립 시 자율 복귀:
        1. 최초 출발 지점(home position)으로 복귀
        2. 복귀 중 생존자 발견 시 위치를 저장 후 계속 복귀
        3. 복귀 후 재연결 → 저장된 생존자 위치 보고
        """
        self.get_logger().warn(
            f'Robot {self.robot_id}: 자율 복귀 시작 — home position으로 이동'
        )
        # Nav2 home position 복귀 Action 호출
        self._navigate_home()

    def _record_good_position(self):
        """신호 양호 위치 이력 저장 (최대 5개)"""
        # 실제 구현: TF에서 현재 위치 획득
        # 여기서는 예시로 처리
        if len(self.last_good_positions) >= self.LAST_KNOWN_BUFFER:
            self.last_good_positions.pop(0)
        # self.last_good_positions.append({'x': current_x, 'y': current_y})

    def _get_wifi_rssi(self) -> int:
        """iwconfig 명령어로 WiFi 신호 강도 측정"""
        try:
            result = subprocess.run(
                ['iwconfig', self.interface],
                capture_output=True, text=True
            )
            match = re.search(r'Signal level=(-\d+) dBm', result.stdout)
            if match:
                return int(match.group(1))
        except Exception as e:
            self.get_logger().error(f'RSSI 측정 실패: {e}')
        return -100  # 측정 실패 시 최저값 반환

    def _request_speed_reduction(self, factor: float):
        """Nav2에 속도 감소 파라미터 동적 재설정 요청"""
        # rclpy parameter service를 통해 max_vel_x 조정
        pass

    def _navigate_to(self, x: float, y: float):
        """Nav2 NavigateToPose Action 클라이언트 호출"""
        pass

    def _navigate_home(self):
        """저장된 home position으로 Nav2 복귀 요청"""
        pass

    def _exit_rendezvous_mode(self):
        """통신 복구 → 정상 탐색 모드 복귀"""
        self.rendezvous_mode = False
        self.get_logger().info(f'Robot {self.robot_id}: 통신 복구 — 탐색 재개')
        event = json.dumps({
            'type': 'COMM_RESTORED',
            'robot_id': self.robot_id,
            'timestamp': self.get_clock().now().nanoseconds
        })
        self.comm_event_pub.publish(String(data=event))
```

### 13.3 Rendezvous 프로토콜 상태 다이어그램

```
정상 탐색
(RSSI ≥ -70dBm)
      │
      │ RSSI 하락 (-70 ~ -80)
      ▼
속도 감속 + 경고
(50% 속도, 통신 모니터링 강화)
      │
      │ RSSI 위험 (-80 ~ -90)
      ▼
랑데부 모드 진입
(마지막 양호 지점으로 복귀 → 30초 대기)
      │                    │
      │ 재연결 성공         │ 재연결 실패 (-90 이하)
      ▼                    ▼
탐색 재개             자율 복귀 모드
                     (home position 복귀)
                           │
                           │ 복귀 중 생존자 발견
                           ▼
                      좌표 로컬 저장
                      (복귀 후 재연결 시 보고)
                           │
                           │ home 도착 + 재연결
                           ▼
                      저장 데이터 일괄 업로드
                      + 재충전 후 재출동
```

### 13.4 swarm_coordinator.py 통합

```python
# ghost5_swarm/swarm_coordinator.py 에 추가

def handle_comm_event(self, msg):
    """통신 이벤트 처리 (Leader 측)"""
    data = json.loads(msg.data)
    robot_id = data['robot_id']

    if data['type'] == 'COMM_DEGRADED':
        # 해당 로봇의 Frontier claim 30초 후 자동 해제 준비
        self.get_logger().warn(
            f'Robot {robot_id} 통신 불안정 — Frontier claim 임시 동결'
        )
        # SemanticMemory에 이벤트 기록
        last_pose = self.blackboard.get_robot_state(robot_id)
        if last_pose:
            self.semantic_memory.record_comm_lost(
                robot_id, last_pose.get('pose', {})
            )

    elif data['type'] == 'COMM_RESTORED':
        # 복구된 로봇에 새 Frontier 할당
        self.get_logger().info(
            f'Robot {robot_id} 통신 복구 — 새 임무 할당'
        )
        self._reassign_frontiers_to_robot(robot_id)
```

---

## 14. 🆕 보완 설계 — Hailo NPU 하드웨어 가속

### 14.1 문제 정의: CPU 부하 병목 분석

Raspberry Pi 5 (ARM Cortex-A76, 4코어 2.4GHz)의 CPU 부하 예상:

| 작업 | 예상 CPU 사용률 | 비고 |
|------|----------------|------|
| slam_toolbox SLAM | 30~40% | 루프 클로저 시 스파이크 |
| Nav2 경로 계획 | 10~15% | |
| Zenoh 통신 | 5~8% | DDS 대비 절반 |
| LiDAR Z-stack 누적 | 5~8% | 경량 포인트 누적 연산 |
| **YOLOv8n 인체 감지 (카메라)** | **20~30%** | 5MP 실시간 추론 |
| **카메라 텍스처 분석 (Elevation)** | **8~12%** | OpenCV 경량 처리 |
| US-016 / TCRT5000 처리 | 2~3% | 경량 센서 폴링 |
| **합계** | **~88%** | **CPU 과부하 위험 ⚠️** |

**결론: YOLOv8n 인체 감지를 NPU로 오프로딩하면 안정적 동작 가능.**

### 14.2 Hailo AI HAT+ 선택

Raspberry Pi AI HAT+는 Hailo NPU를 탑재해 클라우드 서버 없이 로컬에서 하드웨어 가속 AI 추론을 수행할 수 있으며, 에지 AI 방식으로 성능 향상, 지연 감소, 데이터 보안을 동시에 달성한다.

AI HAT+의 Hailo-8L 칩은 13 TOPS의 신경망 추론 가속 성능을 제공하며, M.2 HAT+를 통해 Raspberry Pi 5의 PCIe 2.0 인터페이스에 연결된다.

| 모델 | TOPS | 용도 | 비용 |
|------|------|------|------|
| AI HAT+ 13TOPS (Hailo-8L) | 13 TOPS | 단일 모델 실시간 추론 | ~$70 |
| **AI HAT+ 26TOPS (Hailo-8)** | **26 TOPS** | **다중 모델 동시 추론** | **~$100** ← **채택** |
| AI HAT+ 2 40TOPS (Hailo-10H) | 40 TOPS | LLM + VLM 포함 | ~$150 |

**26 TOPS Hailo-8 채택 이유**: YOLOv8n 인체 감지 + 카메라 기반 Elevation 분석 등 다중 비전 모델을 동시 실행하려면 13 TOPS로는 부족하다.

### 14.3 NPU 오프로딩 아키텍처

```
Raspberry Pi 5 CPU                    Hailo-8 NPU (26 TOPS)
─────────────────────                 ──────────────────────
slam_toolbox (30%)                    YOLOv8n 인체 감지 (5MP 카메라)
Nav2 경로 계획 (10%)      PCIe Gen3   YOLOv8n 인체 감지
Zenoh 통신 (5%)          ─────────▶  YOLOv8n-pose (인체 포즈)
swarm_coordinator (5%)               YOLOv8n (선택적 비전)
Redis Blackboard (3%)
────────────────────
합계: ~53% (안정적)
```

### 14.4 Hailo 설치 및 ROS2 연동

```bash
# 1. Hailo 드라이버 및 런타임 설치
sudo apt update
sudo apt install hailo-all  # hailort, tappas, Python API 포함

# PCIe Gen 3 활성화 (AI Kit 전용, AI HAT+는 자동)
sudo raspi-config nonint do_pcie_gen 3

# 재부팅 후 검증
hailortcli fw-control identify
# 출력: Board Name: Hailo-8, Firmware Version: 4.17.0...

# 2. ROS2 환경에서 Hailo Python API 사용
pip install hailort --break-system-packages
```

### 14.5 NPU 기반 victim_detector 노드 (강화 버전)

```python
# ghost5_ws/ghost5_victim/ghost5_victim/thermal_detector_npu.py

import numpy as np
from hailo_platform import VDevice, HailoStreamInterface, ConfigureParams
from hailo_platform import InputVStreamParams, OutputVStreamParams, FormatType

class VisionDetectorNPU:
    """
    Hailo NPU 가속 인체 감지 (5MP 카메라 + YOLOv8n).
    5MP 카메라 이미지 → YOLOv8n → 인체 BBox + 신뢰도 출력.
    NPU 오프로딩으로 CPU 부하 ~25% → ~3% 절감.
    """

    # 생존자 체온 범위 (°C)
    HUMAN_TEMP_MIN = 35.0
    HUMAN_TEMP_MAX = 39.5

    def __init__(self, hef_path: str = '/opt/ghost5/models/yolov8n_person.hef'):
        """
        hef_path: Hailo Dataflow Compiler로 변환된 모델 파일
        원본 모델: YOLOv8n (COCO person class 파인튜닝)
        """
        self.target = VDevice()
        self.network_group = self._load_model(hef_path)
        self.input_vstreams_params  = InputVStreamParams.make(
            self.network_group, format_type=FormatType.FLOAT32
        )
        self.output_vstreams_params = OutputVStreamParams.make(
            self.network_group, format_type=FormatType.FLOAT32
        )

    def _load_model(self, hef_path: str):
        from hailo_platform import Hef
        hef = Hef(hef_path)
        configure_params = ConfigureParams.create_from_hef(
            hef, interface=HailoStreamInterface.PCIe
        )
        network_groups = self.target.configure(hef, configure_params)
        return network_groups[0]

    def detect(self, thermal_frame: np.ndarray) -> dict:
        """
        5MP 카메라 이미지에서 YOLOv8n으로 생존자(사람) 감지.

        Args:
            thermal_frame: shape (24, 32), dtype float32 (온도값 °C)

        Returns:
            {'detected': bool, 'confidence': float, 'bbox': tuple, 'temp': float}
        """
        # 1. 온도 기반 관심 영역 마스킹
        human_mask = (thermal_frame >= self.HUMAN_TEMP_MIN) & \
                     (thermal_frame <= self.HUMAN_TEMP_MAX)

        if not human_mask.any():
            return {'detected': False, 'confidence': 0.0}

        # 2. 업스케일 (32x24 → 128x96) for NPU 입력
        import cv2
        upscaled = cv2.resize(
            thermal_frame.astype(np.float32),
            (128, 96),
            interpolation=cv2.INTER_CUBIC
        )

        # 3. 정규화 (0~1 범위)
        normalized = (upscaled - 20.0) / (50.0 - 20.0)  # 20~50°C 범위
        input_data = normalized[np.newaxis, :, :, np.newaxis]  # NHWC

        # 4. NPU 추론 (동기 호출)
        with self.network_group.activate():
            output = self._run_inference(input_data)

        # 5. 결과 파싱
        confidence = float(output['confidence'])
        detected = confidence > 0.65

        if detected:
            max_temp = float(thermal_frame[human_mask].max())
            return {
                'detected': True,
                'confidence': confidence,
                'bbox': self._extract_bbox(output),
                'temp': max_temp
            }
        return {'detected': False, 'confidence': confidence}

    def _run_inference(self, input_data: np.ndarray) -> dict:
        """Hailo NPU 추론 실행"""
        from hailo_platform import InferVStreams
        with InferVStreams(
            self.network_group,
            self.input_vstreams_params,
            self.output_vstreams_params
        ) as infer_pipeline:
            input_dict = {
                self.network_group.get_input_vstream_infos()[0].name: input_data
            }
            with infer_pipeline as pipeline:
                pipeline.send(input_dict)
                output = pipeline.recv()
        return output

    def _extract_bbox(self, output: dict) -> tuple:
        """출력 텐서에서 바운딩 박스 추출"""
        # 모델별 출력 파싱 로직
        return (0, 0, 32, 24)  # 예시
```

### 14.6 US-016 초음파 + TCRT5000 IR 생존자 감지 노드

Pinky Pro에 탑재된 US-016 초음파 센서와 TCRT5000 IR 센서를 활용한 근거리 생존자 감지 노드다. US-016 초음파와 TCRT5000 IR, 5MP 카메라 세 가지 센서를 교차 검증한다.

```python
# ghost5_victim/proximity_detector.py

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Range
from std_msgs.msg import Float32
import numpy as np

class ProximityDetectorNode(Node):
    """
    US-016 초음파 + TCRT5000 IR 기반 생존자 감지.

    US-016 초음파 (GPIO Trigger/Echo):
      - 측정 범위: 2cm ~ 400cm
      - 비정상적 접근/패턴 → 생존자 존재 추정

    TCRT5000 IR (반사형 적외선):
      - 근거리(~30cm) 물체 반사 강도 측정
      - 사람 피부/옷 반사율 기준 임계값 적용
    """

    # US-016 파라미터
    US_MIN_RANGE_M   = 0.02   # 최소 측정 거리 (2cm)
    US_MAX_RANGE_M   = 4.00   # 최대 측정 거리 (400cm)
    US_HUMAN_MIN_M   = 0.20   # 사람 감지 최소 거리 (20cm)
    US_HUMAN_MAX_M   = 1.50   # 사람 감지 최대 거리 (150cm)

    # TCRT5000 IR 파라미터 (ADC 0~1023 기준, 현장 캘리브레이션 필요)
    IR_HUMAN_MIN     = 300    # 사람 반사 최솟값 (경험적)
    IR_HUMAN_MAX     = 700    # 사람 반사 최댓값

    # 감지 신뢰도 임계값
    CONFIDENCE_THRESH = 0.60

    def __init__(self, robot_id: int):
        super().__init__(f'proximity_detector_robot_{robot_id}')
        self.robot_id = robot_id
        self.us_readings  = []   # 최근 10회 초음파 측정값
        self.ir_readings  = []   # 최근 10회 IR 측정값

        # 초음파 토픽 구독 (GPIO 드라이버 노드에서 퍼블리시)
        self.create_subscription(
            Range,
            f'/robot_{robot_id}/ultrasonic',
            self.us_callback,
            10
        )
        # IR 토픽 구독 (ADC 드라이버 노드에서 퍼블리시)
        self.create_subscription(
            Float32,
            f'/robot_{robot_id}/ir_sensor',
            self.ir_callback,
            10
        )

        self.victim_pub = self.create_publisher(
            String, f'/robot_{robot_id}/victim_proximity', EVENT_QOS
        )

    def us_callback(self, msg: Range):
        """초음파 측정값 수신 및 생존자 패턴 감지"""
        d = msg.range
        self.us_readings.append(d)
        if len(self.us_readings) > 10:
            self.us_readings.pop(0)

        if len(self.us_readings) >= 5:
            self._analyze_pattern()

    def ir_callback(self, msg: Float32):
        """IR 반사 강도 수신"""
        self.ir_readings.append(msg.data)
        if len(self.ir_readings) > 10:
            self.ir_readings.pop(0)

    def _analyze_pattern(self):
        """
        초음파 + IR 교차 분석으로 생존자 신뢰도 계산.

        생존자 판단 기준:
          1. 초음파: 20~150cm 범위 내 물체가 안정적으로 감지
          2. IR: 반사 강도가 사람 범위(300~700) 내
          3. 두 조건이 동시에 만족 → 높은 신뢰도
        """
        us_arr = np.array(self.us_readings)
        ir_arr = np.array(self.ir_readings)

        # 초음파 신뢰도: 사람 범위 내 안정적 거리
        us_in_range = (us_arr >= self.US_HUMAN_MIN_M) & (us_arr <= self.US_HUMAN_MAX_M)
        us_confidence = float(us_in_range.mean())  # 0~1

        # IR 신뢰도: 사람 반사 범위 내
        if len(ir_arr) > 0:
            ir_in_range = (ir_arr >= self.IR_HUMAN_MIN) & (ir_arr <= self.IR_HUMAN_MAX)
            ir_confidence = float(ir_in_range.mean())
        else:
            ir_confidence = 0.0

        # 교차 검증 신뢰도 (가중 평균)
        combined = 0.6 * us_confidence + 0.4 * ir_confidence

        if combined >= self.CONFIDENCE_THRESH:
            import json
            detection = json.dumps({
                'robot_id': self.robot_id,
                'us_confidence': us_confidence,
                'ir_confidence': ir_confidence,
                'combined_confidence': combined,
                'us_distance_m': float(np.median(us_arr)),
                'timestamp': self.get_clock().now().nanoseconds
            })
            self.victim_pub.publish(String(data=detection))
            self.get_logger().warn(
                f'⚠️ Robot {self.robot_id}: 생존자 감지 가능 '
                f'(신뢰도 {combined:.2f}, 거리 {np.median(us_arr):.2f}m)'
            )
```

### 14.7 CPU 부하 개선 예상

| 작업 | 기존 (CPU만) | NPU 오프로딩 후 | 절감 |
|------|------------|----------------|------|
| YOLOv8n 인체 감지 | 20~30% | 2~3% | **-27%** |
| 카메라 텍스처 분석 | 8~12% | 8~12% (CPU 유지) | — |
| **CPU 합계** | **~88%** | **~60%** | **+28% 여유** |

> YOLOv8n NPU 오프로딩만으로 CPU가 안정권(65% 이하)으로 진입한다.

---

## 15. 최종 기술 스택 요약 (v2.0)

### 15.1 확정된 기술 선택 (리뷰 반영 최종본)

| 레이어 | 선택 기술 | 선택 이유 | v2.0 보완 |
|--------|-----------|-----------|-----------|
| **미들웨어** | rmw_zenoh (ROS2 Jazzy) | WiFi 메쉬 최적화, CPU 절반, Discovery 99% 절감 | — |
| **SLAM** | slam_toolbox + Pose Graph 공유 | 대역폭 효율, ROS2 Jazzy 공식 지원 | 🆕 2.5D Elevation Layer 추가 |
| **지도 병합** | Delta Update + map_merge | 전체 대비 10~20% 대역폭 사용 | 🆕 Elevation 글로벌 병합 |
| **Frontier 탐색** | MMPF + Claim Blackboard | 중복 탐색 방지, 목표 안정성 | 🆕 skip_zones 연동 |
| **리더 선출** | Bully Algorithm | 5대 소규모 최적, 빠른 수렴 | — |
| **공유 상태** | Redis Blackboard (Leader) | 원자적 Claim, 자동 TTL 만료 | 🆕 Semantic Event Memory |
| **통신 단절 대응** | Zenoh Gossip | 메쉬 자동 우회 | 🆕 Rendezvous 프로토콜 + RSSI 모니터링 |
| **보안** | SROS2 (DDS-Security) | AES-GCM 암호화, X.509 인증 | — |
| **생존자 감지** | US-016 초음파 + TCRT5000 IR + 5MP 카메라(YOLOv8n) 교차 검증 | Pinky Pro 탑재 센서 활용, 오탐 최소화 | 🆕 YOLOv8n Hailo NPU 오프로딩 |
| **하드웨어 가속** | Raspberry Pi AI HAT+ 26TOPS | YOLOv8n 인체감지 실시간 추론 | 🆕 신규 추가 |
| **2.5D 인지** | RPLiDAR C1 Z-stack + 5MP 카메라 텍스처 | LiDAR 기반, 추가 하드웨어 불필요 | 🆕 신규 추가 |
| **시각화** | Foxglove Studio | 실시간 멀티 로봇 모니터링 | — |

### 15.2 최종 아키텍처 다이어그램 (v2.0, 드론 미적용)

```
┌──────────────────────────────────────────────────────────────┐
│                   Ground Control Station (GCS)               │
│        Foxglove Studio — 통합 2.5D 지도 + 생존자 위치 표시   │
└──────────────────────┬───────────────────────────────────────┘
                       │ rmw_zenoh + SROS2 (TCP, AES-GCM 암호화)
          ┌────────────┼────────────────┐
          │            │                │
  Robot-1 (Leader)    R2            R3~R5 (Explorer)
  ┌──────────────────┐  ┌─────────────────────────────┐
  │ slam_toolbox     │  │ slam_toolbox                 │
  │ map_merger_v2    │  │ depth_to_elevation_node      │
  │ elevation_global │  │   (RPLiDAR C1 Z-stack)      │
  │ leader_election  │  │ frontier_manager (MMPF)       │
  │ Redis Blackboard │  │ comm_monitor (RSSI)           │
  │  ├─ RobotState   │  │ thermal_detector (Hailo NPU)  │
  │  ├─ FrontierClaim│  │ audio_detector (Hailo NPU)    │
  │  └─ SemanticMem  │  │ leader_election               │
  └──────────────────┘  └─────────────────────────────┘

하드웨어 스택 (로봇 1대):
  Raspberry Pi 5 (8GB)
    ├── RPLiDAR C1         → 2D SLAM (slam_toolbox)
    ├── 5MP 카메라           → YOLOv8n 인체 감지 + Elevation 텍스처 분석
    ├── US-016 초음파           → 생존자 거리 감지 (2~400cm)
    ├── TCRT5000 IR             → 근거리 반사 감지 (~30cm)
    ├── BNO055 IMU (9축)        → EKF 오도메트리 보정
    ├── 다이나믹셀 XL330        → 구동 + 오도메트리
    └── Hailo AI HAT+ 26TOPS   → NPU 가속 (옵션, Phase 2)
         └── yolov8n_person.hef   (인체 감지)

통신 채널 (rmw_zenoh QoS):
  🔴 /robot_N/pose             → BEST_EFFORT  10Hz  TTL 5s
  🟡 /robot_N/map_delta        → RELIABLE     1Hz   TTL 60s
  🟡 /robot_N/elevation_layer  → RELIABLE     2Hz   (Hailo 추론 주기)
  🟢 /swarm/elevation_global   → RELIABLE     0.5Hz (병합 후 GCS)
  🟢 /swarm/election           → RELIABLE     이벤트  KEEP_ALL
  🟢 /swarm/comm_events        → RELIABLE     이벤트  (RSSI 경고)
  🟢 /swarm/victim             → RELIABLE     이벤트  KEEP_ALL
  🟢 /robot_N/rssi             → BEST_EFFORT  0.5Hz
```

### 15.3 단계별 보완 구현 우선순위

| 우선순위 | 보완 항목 | 구현 Phase | 난이도 |
|----------|-----------|-----------|--------|
| P1 (즉시) | Semantic Event Memory | Phase 1 | 낮음 — Redis 확장 |
| P1 (즉시) | RSSI 모니터링 + 기본 Rendezvous | Phase 2 | 낮음 — iwconfig |
| P2 (중요) | 2.5D Elevation Map (RPLiDAR C1 Z-stack + 5MP 카메라) | Phase 2 | 낮음 — 소프트웨어만 |
| P2 (중요) | Hailo NPU YOLOv8n 인체 감지 오프로딩 | Phase 2 | 중간 — HEF 변환 필요 |

---

## 참고 문헌

1. Ahmed et al., "Efficient Multi-robot Active SLAM," *Journal of Intelligent & Robotic Systems*, 2025. https://doi.org/10.1007/s10846-025-02275-8
2. Fina et al., "Multi-Robot Collaborative SLAM with Distributed LPFE," *IEEE Robotics and Automation Letters*, 2025.
3. Deng et al., "On the (In)Security of Secure ROS2," *ACM CCS*, 2022.
4. Zhang et al., "Comparison of Middlewares for Distributed ROS2," *JIRS*, 2024.
5. Petitpied et al., "Performance Comparison of ROS2 Middlewares for Multi-robot Mesh Networks," *JIRS*, 2025.
6. Park et al., "Optimization formula for DDS communication in ROS 2," *IEEE INFOCOM*, 2025.
7. Serov et al., "Multi-Robot Graph SLAM Using LIDAR," *ICARA*, 2024.
8. Torne et al., "MEM: Multi-Scale Embodied Memory for VLAs," Physical Intelligence, 2025.
9. Kim et al., "A 2.5D Map-Based Mobile Robot Localization via Cooperation of Aerial and Ground Robots," *PMC*, 2018.
10. Raspberry Pi Documentation, "AI HATs," 2025. https://www.raspberrypi.com/documentation/accessories/ai-hat-plus.html
11. Hailo AI, "Hailo-RPi5-Examples," GitHub, 2025. https://github.com/hailo-ai/hailo-rpi5-examples
12. ROS2 Official Documentation, "Working with Zenoh," Jazzy. https://docs.ros.org/en/jazzy
13. Aguirre et al., "SROS2: Usable Cyber Security Tools for ROS 2," *IEEE IROS*, 2022.

---

*본 연구 보고서 v2.1은 설계 리뷰 결과를 완전히 반영한 문서입니다 (드론 미적용 구성). v3.0에서 Gazebo 드론 시뮬레이션이 통합됩니다.*

---

## 16. 🆕 v3.1 — Gazebo 드론 시뮬레이션 심화 기술 조사

### 16.1 배경 및 동기

드론 실기체 운용에는 비행 경험, 실외 규제(항공안전법), 짧은 배터리(~15분), 추락/파손 위험 등 높은 진입장벽이 있다. GHOST-5의 핵심 가치는 지상 로봇 스웜 자체에 있으므로, **드론은 Gazebo 시뮬레이션으로 대체**하여 Phase 3에서 협동 로직을 먼저 완전히 검증한 뒤 실기체 도입 여부를 판단한다.

핵심 전제: **ROS2 토픽 인터페이스는 실기체와 시뮬레이션이 동일**하므로, 시뮬에서 검증된 코드는 최소한의 변경으로 실기체에 이식 가능하다.

---

### 16.2 ⚠️ 핵심 기술 이슈: Zenoh + uXRCE-DDS 공존 불가

이 이슈는 GHOST-5 Gazebo 통합 설계에서 **가장 중요한 기술적 제약**이다. 반드시 이해하고 대응 전략을 수립해야 한다.

#### 문제 원인

PX4 uXRCE-DDS 에이전트는 DDS 레이어에 직접 publish하는 구조다. 반면 GHOST-5는 `rmw_zenoh_cpp`를 사용한다. 이 두 미들웨어는 **동일 프로세스에서 동시 사용이 불가능**하다.

> PX4 GitHub Issue #25494 (2025): "uXRCE-DDS agent publishes directly via DDS and not through the RMW layer, so it's not possible to use rmw_zenoh as the middleware."

#### 해결 방법 3가지

**방법 1 — `px4_sitl_zenoh` 빌드 타겟 사용 (권장) ✅**

PX4 공식 문서에 따르면 `px4_sitl_zenoh`라는 Zenoh 전용 SITL 빌드 타겟이 존재하며, ROS2 Jazzy와 완전 호환된다.

```bash
# Zenoh 내장 PX4 SITL 빌드 (uXRCE-DDS 불필요)
cd ~/PX4-Autopilot
make px4_sitl_zenoh gz_x500

# 별도 브릿지 에이전트 불필요 — PX4가 직접 Zenoh로 토픽 publish
# ROS2 Jazzy에서 바로 구독 가능
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
ros2 topic list  # /fmu/out/* 토픽 확인
```

> PX4 공식 문서: "The PX4 ROS 2 Interface Library works out of the box with Zenoh as a transport backend."
> ROS2 Jazzy 호환 시 `CONFIG_ZENOH_KEY_TYPE_HASH=y` (기본값) 유지.

**방법 2 — 브릿지 노드로 미들웨어 분리**

PX4는 uXRCE-DDS(FastDDS)로 실행하고, 별도 브릿지 노드가 DDS 토픽을 Zenoh 토픽으로 변환한다.

```
PX4 SITL ──uXRCE-DDS──► FastDDS 토픽(/fmu/out/*)
                              │
                    [bridge_node.py]
                         (FastDDS 구독 → Zenoh publish)
                              │
                         Zenoh 토픽(/drone/*)
                              │
                    GHOST-5 로봇 5대 (rmw_zenoh)
```

```python
# ghost5_ws/ghost5_drone_sim/px4_zenoh_bridge.py
# FastDDS(RMW_IMPLEMENTATION=rmw_fastrtps_cpp)로 PX4 토픽 구독
# → Zenoh(rmw_zenoh_cpp) 토픽으로 변환 publish

# 이 방법은 두 프로세스를 분리하여 각각 다른 RMW로 실행
# Process 1: RMW_IMPLEMENTATION=rmw_fastrtps_cpp → PX4 구독
# Process 2: RMW_IMPLEMENTATION=rmw_zenoh_cpp    → GHOST-5 publish
```

**방법 3 — Fake Drone Node (미들웨어 문제 완전 회피)**

Zenoh 위에서 직접 드론 역할 토픽을 publish하는 경량 노드로, 미들웨어 충돌 없이 즉시 사용 가능하다. Phase 3-A에서 권장.

---

### 16.3 버전 호환성 매트릭스

GHOST-5 개발 환경(Ubuntu 24.04, ROS2 Jazzy)에서 PX4 + Gazebo를 구성할 때의 공식 지원 조합:

| Ubuntu | ROS2 | Gazebo | PX4 버전 | 상태 |
|--------|------|--------|----------|------|
| **24.04** | **Jazzy** | **Harmonic** | **main/v1.16+** | ✅ **공식 지원** |
| 22.04 | Humble | Harmonic | v1.14~v1.15 | ✅ 안정 |
| 22.04 | Humble | Fortress | v1.13 | ⚠️ 구버전 |
| 24.04 | Jazzy | Harmonic | v1.14 이하 | ❌ 미지원 |

> Ubuntu 24.04 + ROS2 Jazzy + Gazebo Harmonic + PX4 main 브랜치가 GHOST-5 환경과 정합.

> ⚠️ PX4 v1.16.0-alpha + Ubuntu 24.04 조합에서 센서 누락 경고(Accel, Barometer, EKF2 등)가 보고됨 (GitHub Issue #24159). 이는 Gazebo 플러그인 연동 문제로, **PX4 main 브랜치 최신 커밋 사용**으로 대부분 해결된다.

---

### 16.4 PX4 SITL + Gazebo Harmonic + ROS2 Jazzy 전체 설치 가이드

#### Step 1: 의존성 및 PX4 빌드

```bash
# Ubuntu 24.04 기준
sudo apt update && sudo apt upgrade -y

# PX4 클론 및 의존성 설치 (~10분)
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot
bash ./Tools/setup/ubuntu.sh   # Gazebo Harmonic, Python deps 포함

# Zenoh 내장 SITL 빌드 (첫 빌드 ~20분)
make px4_sitl_zenoh gz_x500
# 성공 시: Gazebo 창 열리고 X500 드론 스폰됨
```

#### Step 2: ROS2 Jazzy 워크스페이스 구성

```bash
# px4_msgs 패키지 클론 (PX4 토픽 메시지 정의)
mkdir -p ~/ghost5_drone_ws/src
cd ~/ghost5_drone_ws/src
git clone https://github.com/PX4/px4_msgs.git

# GHOST-5 드론 통합 패키지 추가
# (ghost5_drone_integration 패키지 — 섹션 17에서 작성)
git clone https://github.com/YOUR_REPO/ghost5_drone_integration.git

# 빌드
cd ~/ghost5_drone_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install

source install/setup.bash
```

#### Step 3: Gazebo Harmonic + ROS2 브릿지

```bash
# ros_gz_bridge 설치 (Gazebo ↔ ROS2 토픽 브릿지)
sudo apt install ros-jazzy-ros-gz

# GZ_SIM 환경변수 설정 (PX4 모델 경로)
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$HOME/PX4-Autopilot/Tools/simulation/gz/models
export GZ_SIM_SYSTEM_PLUGIN_PATH=$GZ_SIM_SYSTEM_PLUGIN_PATH:$HOME/PX4-Autopilot/build/px4_sitl_default/src/modules/simulation/gz_bridge
```

#### Step 4: 전체 실행 순서 (터미널 5개)

```bash
# [Terminal 1] Gazebo + PX4 SITL (Zenoh 내장)
cd ~/PX4-Autopilot
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
make px4_sitl_zenoh gz_x500

# [Terminal 2] Zenoh Router (드론 PC — GHOST-5 스웜 허브)
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
ros2 run rmw_zenoh_cpp init_rmw_zenoh_router

# [Terminal 3] PX4 → GHOST-5 토픽 변환 노드
source ~/ghost5_drone_ws/install/setup.bash
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
ros2 run ghost5_drone_integration px4_topic_bridge

# [Terminal 4] QGroundControl (선택 — 드론 상태 모니터링)
./QGroundControl.AppImage

# [Terminal 5] Foxglove Bridge (통합 시각화)
ros2 launch foxglove_bridge foxglove_bridge_launch.xml
```

---

### 16.5 NED ↔ ENU 좌표계 변환 (필수)

PX4는 **NED(North-East-Down)** 프레임을 사용하고, ROS2 Nav2는 **ENU(East-North-Up) + map 프레임**을 사용한다. 이 변환은 반드시 처리해야 한다.

```
PX4 NED:  X=North, Y=East,  Z=Down  (오른손 좌표계, Z 아래)
ROS2 ENU: X=East,  Y=North, Z=Up    (오른손 좌표계, Z 위)

변환 공식:
  x_enu =  y_ned
  y_enu =  x_ned
  z_enu = -z_ned
```

```python
# ghost5_ws/ghost5_drone_integration/px4_topic_bridge.py

import rclpy
from rclpy.node import Node
from px4_msgs.msg import VehicleLocalPosition, BatteryStatus
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32, String
import json


class PX4TopicBridge(Node):
    """
    PX4 SITL uORB 토픽 → GHOST-5 /drone/* 토픽 변환.

    좌표 변환: NED(PX4) → ENU(ROS2 map 프레임)
      x_enu =  y_ned
      y_enu =  x_ned
      z_enu = -z_ned

    구독 토픽 (PX4):
      /fmu/out/vehicle_local_position → NED 위치
      /fmu/out/battery_status         → 배터리 %

    발행 토픽 (GHOST-5):
      /drone/gps_pose       → ENU PoseStamped
      /drone/battery_percent → Float32 (0~100)
      /drone/wifi_ap_status  → JSON String
    """

    def __init__(self):
        super().__init__('px4_topic_bridge')

        # PX4 토픽 구독
        self.pos_sub = self.create_subscription(
            VehicleLocalPosition,
            '/fmu/out/vehicle_local_position',
            self.position_callback,
            10
        )
        self.bat_sub = self.create_subscription(
            BatteryStatus,
            '/fmu/out/battery_status',
            self.battery_callback,
            10
        )

        # GHOST-5 토픽 발행
        self.pose_pub = self.create_publisher(
            PoseStamped, '/drone/gps_pose', 10)
        self.battery_pub = self.create_publisher(
            Float32, '/drone/battery_percent', 10)
        self.ap_pub = self.create_publisher(
            String, '/drone/wifi_ap_status', 10)

        # AP 상태 주기 발행 (1Hz)
        self.create_timer(1.0, self.publish_ap_status)
        self.drone_altitude = 0.0

        self.get_logger().info('PX4TopicBridge 시작 — NED→ENU 변환 활성')

    def position_callback(self, msg: VehicleLocalPosition):
        """NED → ENU 좌표 변환 후 /drone/gps_pose publish"""
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = 'map'

        # NED → ENU 변환
        pose.pose.position.x =  msg.y   # East  = NED-Y
        pose.pose.position.y =  msg.x   # North = NED-X
        pose.pose.position.z = -msg.z   # Up    = -NED-Z

        self.drone_altitude = pose.pose.position.z
        self.pose_pub.publish(pose)

    def battery_callback(self, msg: BatteryStatus):
        """배터리 잔량 publish"""
        pct = msg.remaining * 100.0  # 0.0~1.0 → 0~100%
        self.battery_pub.publish(Float32(data=pct))

    def publish_ap_status(self):
        """WiFi AP 상태 publish (드론 시뮬 = 항상 ACTIVE)"""
        status = json.dumps({
            'status': 'ACTIVE',
            'ssid': 'GHOST5_RELAY_SITL',
            'altitude_m': round(self.drone_altitude, 1),
            'source': 'px4_sitl'
        })
        self.ap_pub.publish(String(data=status))


def main():
    rclpy.init()
    node = PX4TopicBridge()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

### 16.6 GHOST-5 재난 시나리오 Gazebo 월드 설계

Pinky Pro 5대 + X500 드론이 동작하는 재난 현장 시뮬레이션 월드를 구성한다.

```xml
<!-- ghost5_disaster_world.sdf -->
<!-- ~/PX4-Autopilot/Tools/simulation/gz/worlds/ 에 배치 -->
<?xml version="1.0" ?>
<sdf version="1.9">
  <world name="ghost5_disaster">

    <!-- 물리 엔진 -->
    <physics name="1ms" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>

    <!-- 조명 -->
    <light type="directional" name="sun">
      <pose>0 0 100 0 0 0</pose>
      <diffuse>1 1 1 1</diffuse>
    </light>

    <!-- 지면 -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry><plane><normal>0 0 1</normal><size>200 200</size></plane></geometry>
        </collision>
        <visual name="visual">
          <geometry><plane><normal>0 0 1</normal><size>200 200</size></plane></geometry>
          <material><ambient>0.4 0.4 0.4 1</ambient></material>
        </visual>
      </link>
    </model>

    <!-- 재난 현장: 붕괴 건물 잔해 (박스로 표현) -->
    <model name="debris_1">
      <static>true</static>
      <pose>5 3 0.5 0 0 0.3</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>3 2 1</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>3 2 1</size></box></geometry>
          <material><ambient>0.5 0.4 0.3 1</ambient></material>
        </visual>
      </link>
    </model>

    <model name="debris_2">
      <static>true</static>
      <pose>-4 6 0.75 0 0 -0.2</pose>
      <link name="link">
        <collision name="col"><geometry><box><size>4 1.5 1.5</size></box></geometry></collision>
        <visual name="vis">
          <geometry><box><size>4 1.5 1.5</size></box></geometry>
          <material><ambient>0.4 0.35 0.3 1</ambient></material>
        </visual>
      </link>
    </model>

    <!-- 생존자 마커 (빨간 구) -->
    <model name="survivor_1">
      <static>true</static>
      <pose>8 -2 0.3 0 0 0</pose>
      <link name="link">
        <visual name="vis">
          <geometry><sphere><radius>0.3</radius></sphere></geometry>
          <material><ambient>1 0 0 1</ambient></material>
        </visual>
      </link>
    </model>

    <!-- X500 드론 스폰 위치 (기본) -->
    <!-- PX4 SITL이 자동으로 스폰 — 위치는 PX4_GZ_MODEL_POSE로 지정 -->

  </world>
</sdf>
```

```bash
# 커스텀 월드로 PX4 SITL 실행
export PX4_GZ_MODEL_POSE="0,0,0.5,0,0,0"   # 드론 초기 위치
make px4_sitl_zenoh gz_x500 \
  PX4_SITL_WORLD=$(pwd)/Tools/simulation/gz/worlds/ghost5_disaster.sdf
```

---

### 16.7 Gazebo에서 Pinky Pro 대역 로봇(TurtleBot3) 스폰

실제 Pinky Pro URDF/SDF 모델이 준비되기 전까지 **TurtleBot3 Waffle**을 대역으로 사용한다. ROS2 Nav2, slam_toolbox와 완전 호환된다.

```bash
# TurtleBot3 Waffle 5대 + X500 드론 동시 실행
# [Terminal 1] Gazebo 월드만 먼저 실행
gz sim ghost5_disaster.sdf

# [Terminal 2] PX4 SITL Standalone (기존 Gazebo에 드론 스폰)
export PX4_GZ_STANDALONE=1
export PX4_GZ_MODEL_NAME=x500
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
make px4_sitl_zenoh gz_x500

# [Terminal 3~7] TurtleBot3 5대 스폰
for i in 1 2 3 4 5; do
  ros2 launch turtlebot3_gazebo spawn_turtlebot3.launch.py \
    x_pose:=$((i*2-6)) y_pose:=-3 \
    robot_name:=robot_$i \
    namespace:=robot_$i &
done

# [Terminal 8~12] 각 로봇 Nav2 + slam_toolbox 실행
for i in 1 2 3 4 5; do
  ros2 launch ghost5_bringup robot_bringup.launch.py \
    robot_id:=$i use_sim_time:=true &
done
```

---

### 16.8 주요 트러블슈팅 체크리스트

실제 설치 및 실행 시 자주 발생하는 문제와 해결법:

| 증상 | 원인 | 해결 |
|------|------|------|
| `make px4_sitl gz_x500` 빌드 실패 | 의존성 누락 | `bash Tools/setup/ubuntu.sh` 재실행 |
| Gazebo 창이 안 뜸 | GPU 드라이버 미설치 | `sudo apt install nvidia-driver-535` |
| `Preflight Fail: Accel Sensor 0 missing` | PX4 구버전 + Gazebo 플러그인 불일치 | PX4 main 브랜치 최신 커밋으로 업데이트 |
| `/fmu/out/*` 토픽 안 보임 | Zenoh RMW 미설정 | `export RMW_IMPLEMENTATION=rmw_zenoh_cpp` 확인 |
| Zenoh + uXRCE-DDS 충돌 | 미들웨어 공존 불가 | `px4_sitl_zenoh` 타겟 사용 또는 브릿지 노드 분리 |
| `ROS_DOMAIN_ID` 충돌 | FastDDS 기본값 충돌 | `unset ROS_DOMAIN_ID` (Zenoh 사용 시 불필요) |
| 드론 위치 좌표 이상 | NED/ENU 변환 미적용 | `px4_topic_bridge.py` 변환 로직 확인 |
| TurtleBot3 스폰 후 충돌 | 초기 위치 겹침 | `x_pose` 간격 2m 이상 확보 |
| Gazebo 느림 | CPU 렌더링 | `--headless` 모드 실행 또는 GPU 사용 |
| `use_sim_time` 불일치 | 실시간/시뮬 시간 혼재 | 모든 노드 `use_sim_time:=true` 통일 |

```bash
# 헤드리스 모드 (GUI 없이 빠른 시뮬)
HEADLESS=1 make px4_sitl_zenoh gz_x500
```

---

## 17. 🆕 v3.1 — 드론 시뮬 통합 설계: 토픽·아키텍처·코드

### 17.1 드론 시뮬 추가 토픽 설계 (확정)

기존 GHOST-5 Zenoh 토픽 구조에 드론 시뮬 토픽 6개를 추가한다.

```
기존 지상 로봇 토픽 (유지):
  🔴 /robot_N/pose             BEST_EFFORT  10Hz   TTL 5s
  🟡 /robot_N/map_delta        RELIABLE     1Hz    TTL 60s
  🟡 /robot_N/elevation_layer  RELIABLE     2Hz
  🟢 /swarm/elevation_global   RELIABLE     0.5Hz
  🟢 /swarm/election           RELIABLE     이벤트  KEEP_ALL
  🟢 /swarm/victim             RELIABLE     이벤트  KEEP_ALL
  🟢 /swarm/gossip             RELIABLE     이벤트

신규 드론 시뮬 토픽 (v3.1 추가):
  🔵 /drone/gps_pose           BEST_EFFORT  10Hz   드론 위치 (ENU, map 프레임)
  🔵 /drone/wifi_ap_status     RELIABLE     1Hz    AP 연결 상태 JSON
  🔵 /drone/survivor_pose      RELIABLE     이벤트  생존자 좌표 (ENU)
  🔵 /drone/battery_percent    BEST_EFFORT  1Hz    배터리 잔량 0~100
  🔵 /drone/map_overview       RELIABLE     0.5Hz  드론 시야 OccupancyGrid
  🔵 /swarm/drone_relay_active RELIABLE     이벤트  릴레이 활성/비활성
  🔵 /swarm/frontier_priority  RELIABLE     이벤트  Frontier 갱신 우선순위
```

### 17.2 Phase별 드론 노드 전략

| Phase | 드론 노드 | 미들웨어 | 비고 |
|-------|-----------|----------|------|
| **3-A (즉시)** | `fake_drone_node.py` | rmw_zenoh (직접) | 설치 0, 즉시 시작 |
| **3-B (2~4주)** | `px4_sitl_zenoh` + `px4_topic_bridge.py` | rmw_zenoh (PX4 내장) | 비행 물리 포함 |
| **4 (선택)** | 실기체 X500 V2 | rmw_zenoh (동일) | 코드 변경 최소 |

### 17.3 Fake Drone Node (Phase 3-A)

```python
# ghost5_ws/ghost5_drone_sim/ghost5_drone_sim/fake_drone_node.py

import rclpy, json
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String, Float32
from nav_msgs.msg import OccupancyGrid
import math


class FakeDroneNode(Node):
    """
    Phase 3-A: 물리 시뮬레이터 없이 드론 역할 수행.
    Zenoh RMW 위에서 직접 동작 — 미들웨어 충돌 없음.

    사용법:
      ros2 run ghost5_drone_sim fake_drone_node \\
        --ros-args -p drone_x:=0.0 -p drone_y:=0.0 \\
                   -p hover_alt:=30.0
    """

    def __init__(self):
        super().__init__('fake_drone')

        self.declare_parameter('drone_x', 0.0)
        self.declare_parameter('drone_y', 0.0)
        self.declare_parameter('hover_alt', 30.0)

        self.pose_pub     = self.create_publisher(PoseStamped, '/drone/gps_pose', 10)
        self.ap_pub       = self.create_publisher(String,      '/drone/wifi_ap_status', 10)
        self.survivor_pub = self.create_publisher(PoseStamped, '/drone/survivor_pose', 10)
        self.battery_pub  = self.create_publisher(Float32,     '/drone/battery_percent', 10)
        self.relay_pub    = self.create_publisher(String,      '/swarm/drone_relay_active', 10)

        self.create_timer(0.1,  self.publish_pose)      # 10Hz
        self.create_timer(1.0,  self.publish_ap_status) # 1Hz

        # 릴레이 활성 알림
        self.relay_pub.publish(String(data='{"active": true, "source": "fake_drone"}'))
        self.get_logger().info('🚁 FakeDroneNode 시작 (Phase 3-A)')

    def publish_pose(self):
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.pose.position.x = self.get_parameter('drone_x').value
        msg.pose.position.y = self.get_parameter('drone_y').value
        msg.pose.position.z = self.get_parameter('hover_alt').value
        self.pose_pub.publish(msg)
        self.battery_pub.publish(Float32(data=100.0))

    def publish_ap_status(self):
        status = json.dumps({
            'status': 'ACTIVE', 'ssid': 'GHOST5_RELAY',
            'connected_robots': 5, 'source': 'fake',
            'altitude_m': self.get_parameter('hover_alt').value
        })
        self.ap_pub.publish(String(data=status))

    def trigger_survivor(self, x: float, y: float):
        """CLI 또는 테스트에서 직접 호출하여 생존자 위치 발행"""
        msg = PoseStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.pose.position.x = x
        msg.pose.position.y = y
        self.survivor_pub.publish(msg)
        self.get_logger().warn(f'🔥 생존자 발행: ({x:.1f}, {y:.1f})')
```

### 17.4 지상 로봇 — 드론 좌표 → Nav2 연동

```python
# ghost5_ws/ghost5_drone_integration/drone_nav_bridge.py

import rclpy, json
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from std_msgs.msg import String


class DroneNavBridgeNode(Node):
    """
    /drone/survivor_pose 수신 → Nav2 Goal 전달.
    드론 AP 활성 상태(wifi_ap_status) 확인 후에만 이동.
    Fake Drone / PX4 SITL 양쪽과 동일하게 동작.
    """

    def __init__(self, robot_id: int):
        super().__init__(f'drone_nav_bridge_{robot_id}')
        self.robot_id  = robot_id
        self.ap_active = False

        self.create_subscription(
            PoseStamped, '/drone/survivor_pose',
            self.survivor_callback, 10)
        self.create_subscription(
            String, '/drone/wifi_ap_status',
            self.ap_callback, 10)

        self.nav_client = ActionClient(
            self, NavigateToPose, f'/robot_{robot_id}/navigate_to_pose')

    def ap_callback(self, msg: String):
        try:
            self.ap_active = json.loads(msg.data).get('status') == 'ACTIVE'
        except json.JSONDecodeError:
            pass

    def survivor_callback(self, msg: PoseStamped):
        if not self.ap_active:
            self.get_logger().warn(f'[Robot {self.robot_id}] AP 비활성 — 무시')
            return
        self.get_logger().info(
            f'[Robot {self.robot_id}] 생존자 수신: '
            f'({msg.pose.position.x:.2f}, {msg.pose.position.y:.2f})')
        self._navigate_to(msg)

    def _navigate_to(self, pose: PoseStamped):
        if not self.nav_client.wait_for_server(timeout_sec=3.0):
            self.get_logger().error('Nav2 서버 응답 없음')
            return
        goal = NavigateToPose.Goal()
        goal.pose = pose
        self.nav_client.send_goal_async(goal)
```

### 17.5 Gossip Protocol — 드론 생존자 스웜 전파

```python
# ghost5_ws/ghost5_gossip/drone_gossip_bridge.py

import rclpy, json, time
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String


class DroneGossipBridgeNode(Node):
    """
    드론 /drone/survivor_pose 수신 →
    Gossip Protocol로 GHOST-5 전체 로봇에 전파 (TTL=3홉).
    리더 로봇이 Frontier 우선순위 갱신.
    """

    GOSSIP_TTL    = 3
    GOSSIP_PERIOD = 2.0

    def __init__(self, robot_id: int):
        super().__init__(f'drone_gossip_bridge_{robot_id}')
        self.robot_id     = robot_id
        self.known_victims: dict = {}

        self.create_subscription(
            PoseStamped, '/drone/survivor_pose',
            self.drone_survivor_cb, 10)
        self.create_subscription(
            String, '/swarm/gossip',
            self.gossip_recv_cb, 10)

        self.gossip_pub   = self.create_publisher(String, '/swarm/gossip', 10)
        self.priority_pub = self.create_publisher(
            PoseStamped, '/swarm/frontier_priority', 10)

        self.create_timer(self.GOSSIP_PERIOD, self.propagate_gossip)

    def drone_survivor_cb(self, msg: PoseStamped):
        vid = f"drone_{int(time.time())}"
        self.known_victims[vid] = {
            'x': msg.pose.position.x, 'y': msg.pose.position.y,
            'ttl': self.GOSSIP_TTL, 'source': 'drone',
            'timestamp': time.time()
        }
        self._publish_gossip(vid)
        self.priority_pub.publish(msg)
        self.get_logger().info(
            f'🚁 드론 생존자 Gossip 발원 TTL={self.GOSSIP_TTL}')

    def gossip_recv_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            vid  = data.get('victim_id')
            ttl  = data.get('ttl', 0)
            if vid and vid not in self.known_victims and ttl > 0:
                self.known_victims[vid] = {**data, 'ttl': ttl - 1}
                self._publish_gossip(vid)
        except json.JSONDecodeError:
            pass

    def propagate_gossip(self):
        for vid in list(self.known_victims):
            if self.known_victims[vid]['ttl'] > 0:
                self._publish_gossip(vid)
                self.known_victims[vid]['ttl'] -= 1
            else:
                del self.known_victims[vid]

    def _publish_gossip(self, victim_id: str):
        info = self.known_victims.get(victim_id)
        if not info:
            return
        payload = json.dumps({
            'victim_id': victim_id, 'x': info['x'], 'y': info['y'],
            'ttl': info['ttl'], 'source': info.get('source', f'robot_{self.robot_id}'),
            'robot_id': self.robot_id
        })
        self.gossip_pub.publish(String(data=payload))
```

### 17.6 Zenoh 네트워크 구성 (드론 = Zenoh Router)

```bash
# ── 드론 PC (Fake or PX4 SITL 실행 머신) ──────────────────
export RMW_IMPLEMENTATION=rmw_zenoh_cpp

# Zenoh Router 실행 (모든 로봇의 Discovery 허브)
ros2 run rmw_zenoh_cpp init_rmw_zenoh_router

# ── 각 GHOST-5 지상 로봇 (5대) ────────────────────────────
# Zenoh 설정 파일 — 드론 PC IP를 Router로 지정
cat > /etc/zenoh_ghost5.json5 << 'EOF'
{
  "mode": "peer",
  "connect": {
    "endpoints": ["tcp/DRONE_PC_IP:7447"]
  },
  "scouting": {
    "gossip": { "enabled": true, "multihop": true }
  }
}
EOF

export RMW_IMPLEMENTATION=rmw_zenoh_cpp
export ZENOH_CONFIG_FILE=/etc/zenoh_ghost5.json5
ros2 launch ghost5_bringup robot_bringup.launch.py robot_id:=N use_sim_time:=true
```

### 17.7 통합 검증 시나리오

```
시나리오 1: 기본 통신 릴레이 검증 (Phase 3-A, Fake)
  ① fake_drone_node 실행 → Zenoh Router 활성
  ② 로봇 5대 연결 확인: ros2 node list
  ③ /drone/wifi_ap_status → 5대 수신 확인
  ④ /robot_1/pose → robot_2~5에서 수신 확인
  성공 조건: 토픽 지연 < 100ms

시나리오 2: 생존자 탐지 전파 (Phase 3-A, Fake)
  ① CLI로 생존자 좌표 발행:
     ros2 topic pub --once /drone/survivor_pose \
       geometry_msgs/msg/PoseStamped \
       "{header: {frame_id: 'map'}, pose: {position: {x: 5.0, y: 3.0}}}"
  ② Gossip 전파 확인: ros2 topic echo /swarm/gossip
  ③ 가장 가까운 로봇 Nav2 이동 시작 확인
  성공 조건: 감지→이동 시작 < 2초

시나리오 3: Bully + 드론 Fallback (Phase 3-A)
  ① 드론 노드 강제 종료 (Ctrl+C)
  ② /swarm/drone_relay_active = FALSE 수신 확인
  ③ 리더 로봇이 Zenoh Router 역할 인수 확인
  ④ 지상 로봇 간 직접 통신 유지 확인
  성공 조건: 30초 이내 복구

시나리오 4: PX4 SITL 호버링 + 좌표 공유 (Phase 3-B)
  ① make px4_sitl_zenoh gz_x500 실행
  ② 드론 Takeoff → 고도 30m 호버링
  ③ /drone/gps_pose ENU 좌표 정확성 확인
  ④ 드론 이동 시 로봇들 Zenoh 연결 유지
  성공 조건: 드론 이동 중 토픽 손실 < 5%

시나리오 5: 전체 통합 재난 시나리오 (Phase 3-B)
  ① Gazebo ghost5_disaster.sdf 월드 실행
  ② PX4 X500 드론 + TurtleBot3 5대 동시 실행
  ③ 드론이 생존자 마커(빨간 구) 탐지 → 좌표 publish
  ④ 가장 가까운 로봇 자동 파견
  ⑤ Frontier 탐색으로 나머지 4대 자율 탐색
  성공 조건: 생존자 1명 탐지 시 전체 시스템 정상 반응
```

---

## 18. 🆕 v3.1 — 최종 통합 아키텍처 (지상 5대 + Gazebo 드론)

### 18.1 전체 시스템 아키텍처 (v3.1)

```
┌──────────────────────────────────────────────────────────────────────┐
│                   Ground Control Station (GCS)                       │
│     Foxglove Studio — 2.5D 지도 + 생존자 + 드론 위치 통합 표시       │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ rmw_zenoh (SROS2 AES-GCM)
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│         🚁 가상 드론 [Phase 3-A: Fake / Phase 3-B: PX4 SITL]        │
│                                                                      │
│  Phase 3-A (즉시):          Phase 3-B (2~4주 후):                    │
│  fake_drone_node.py         PX4 SITL X500 + Gazebo Harmonic         │
│  (rmw_zenoh 직접)           px4_sitl_zenoh 빌드 타겟                 │
│                             px4_topic_bridge.py (NED→ENU)           │
│                                                                      │
│  공통 publish 토픽:                                                  │
│    /drone/gps_pose        (10Hz, ENU)                               │
│    /drone/survivor_pose   (이벤트)                                   │
│    /drone/wifi_ap_status  (1Hz)                                      │
│    /drone/battery_percent (1Hz)                                      │
│    /swarm/drone_relay_active (이벤트)                                │
│                                                                      │
│  Zenoh Router ← 모든 로봇 Discovery 허브                             │
└──────────────────────┬───────────────────────────────────────────────┘
                       │ rmw_zenoh Mesh (WiFi AP 릴레이)
         ┌─────────────┼──────────────┐
         │             │              │
   R-1 (Leader)      R-2          R-3~R-5 (Explorer)
 ┌───────────────┐ ┌──────────┐  ┌──────────────────┐
 │ slam_toolbox  │ │slam_tbox │  │ slam_toolbox     │
 │ map_merger    │ │frontier  │  │ frontier_mgr     │
 │ Redis BB      │ │gossip    │  │ gossip_node      │
 │ leader_elect  │ │drone_nav │  │ drone_nav_bridge │
 │ drone_gossip  │ │ _bridge  │  │ drone_gossip     │
 │ Zenoh Router  │ │          │  │   _bridge        │
 │ (Fallback)    │ └──────────┘  └──────────────────┘
 └───────────────┘

하드웨어 (로봇 1대, Pinky Pro):
  Raspberry Pi 5 (8GB) 또는 Gazebo TurtleBot3 대역
    ├── RPLiDAR C1         → slam_toolbox
    ├── 5MP 카메라          → YOLOv8n 인체 감지
    ├── US-016 초음파       → 생존자 근거리 감지
    ├── TCRT5000 IR         → 반사 강도 감지
    ├── BNO055 IMU          → EKF 오도메트리
    ├── 다이나믹셀 XL330    → 구동
    └── (옵션) Hailo 26TOPS → NPU 가속

통신 채널 (rmw_zenoh QoS, v3.1):
  🔴 /robot_N/pose             BEST_EFFORT  10Hz
  🟡 /robot_N/map_delta        RELIABLE     1Hz
  🟡 /robot_N/elevation_layer  RELIABLE     2Hz
  🟢 /swarm/elevation_global   RELIABLE     0.5Hz
  🟢 /swarm/election           RELIABLE     이벤트  KEEP_ALL
  🟢 /swarm/victim             RELIABLE     이벤트  KEEP_ALL
  🟢 /swarm/gossip             RELIABLE     이벤트
  🔵 /drone/gps_pose           BEST_EFFORT  10Hz   (신규)
  🔵 /drone/survivor_pose      RELIABLE     이벤트  (신규)
  🔵 /drone/wifi_ap_status     RELIABLE     1Hz    (신규)
  🔵 /drone/battery_percent    BEST_EFFORT  1Hz    (신규)
  🔵 /swarm/drone_relay_active RELIABLE     이벤트  (신규)
  🔵 /swarm/frontier_priority  RELIABLE     이벤트  (신규)
```

### 18.2 드론 장애 시 Fallback 설계

```
드론 장애 감지:
  /drone/wifi_ap_status 5초 이상 미수신
    → /swarm/drone_relay_active = {"active": false} publish
          → 각 로봇: Zenoh peer 모드 직접 통신 전환
                → Bully Algorithm 리더가 Zenoh Router 인수
                      → GHOST-5 v2.1 독립 동작 모드 복귀

Fallback 후 상태:
  생존자 감지: 지상 센서 전용 (US-016, TCRT5000, YOLOv8n)
  Frontier 탐색: 드론 우선순위 없이 자율 탐색
  통신: 리더 로봇 경유 Zenoh Mesh
```

### 18.3 패키지 구조

```
ghost5_ws/
  src/
    ghost5_drone_sim/              # 드론 시뮬레이션 패키지
      ghost5_drone_sim/
        fake_drone_node.py         # Phase 3-A: Fake 드론
        px4_topic_bridge.py        # Phase 3-B: PX4→GHOST5 변환
      package.xml
      setup.py

    ghost5_drone_integration/      # 드론-로봇 통합 패키지
      ghost5_drone_integration/
        drone_nav_bridge.py        # 드론 좌표 → Nav2 Goal
        drone_gossip_bridge.py     # 드론 생존자 → Gossip 전파
        drone_fallback_monitor.py  # 드론 장애 감지 + Fallback
      launch/
        drone_integration.launch.py
      package.xml
      setup.py

    ghost5_bringup/                # 기존 로봇 런치 (수정)
      launch/
        robot_bringup.launch.py    # drone_integration 노드 추가
```

### 18.4 v3.1 구현 우선순위

| 우선순위 | 항목 | Phase | 난이도 | 선행 조건 |
|----------|------|-------|--------|-----------|
| **P0** | `fake_drone_node.py` 작성·실행 | 3-A | ⭐ | ROS2 Jazzy |
| **P0** | `drone_nav_bridge.py` 작성 | 3-A | ⭐ | Nav2 완성 |
| **P0** | `drone_gossip_bridge.py` 작성 | 3-A | ⭐ | Gossip 완성 |
| **P0** | 시나리오 1~3 검증 | 3-A | ⭐ | |
| **P1** | PX4 SITL 빌드 환경 구축 | 3-B | ⭐⭐⭐ | GPU 권장 |
| **P1** | `px4_topic_bridge.py` (NED→ENU) | 3-B | ⭐⭐ | PX4 SITL |
| **P1** | ghost5_disaster.sdf 월드 제작 | 3-B | ⭐⭐ | Gazebo |
| **P2** | TurtleBot3 5대 + X500 통합 시뮬 | 3-B | ⭐⭐⭐ | |
| **P2** | 시나리오 4~5 검증 | 3-B | ⭐⭐ | |
| **P3** | 실기체 X500 V2 전환 결정 | 4+ | ⭐⭐⭐⭐ | 충분한 시뮬 검증 |

### 18.5 최종 기술 스택 요약 (v3.1)

| 레이어 | 선택 기술 | v3.1 상태 |
|--------|-----------|-----------|
| **미들웨어** | rmw_zenoh (ROS2 Jazzy) | 드론 = Zenoh Router |
| **SLAM** | slam_toolbox + Pose Graph | 유지 |
| **지도 병합** | Delta Update + map_merge | 드론 OccupancyGrid 병합 |
| **Frontier** | MMPF + Claim Blackboard | 드론 좌표로 우선순위 갱신 |
| **리더 선출** | Bully Algorithm | 드론 장애 시 Router 인수 |
| **드론 Phase 3-A** | fake_drone_node.py | 🔵 신규 |
| **드론 Phase 3-B** | PX4 px4_sitl_zenoh + Gazebo Harmonic | 🔵 신규 |
| **NED→ENU 변환** | px4_topic_bridge.py | 🔵 신규 |
| **드론 협동** | drone_nav_bridge + drone_gossip_bridge | 🔵 신규 |
| **드론 Fallback** | Bully 리더 Router 인수 | 🔵 신규 |
| **공유 상태** | Redis Blackboard | 유지 |
| **보안** | SROS2 (DDS-Security) | 유지 |
| **생존자 감지** | US-016 + TCRT5000 + YOLOv8n | 유지 |
| **시각화** | Foxglove Studio | 드론 위치 오버레이 추가 |

---

## 참고 문헌 (v3.1 전체)

**지상 로봇 (v1.0~v2.1)**

1. Ahmed et al., "Efficient Multi-robot Active SLAM," *JIRS*, 2025. https://doi.org/10.1007/s10846-025-02275-8
2. Fina et al., "Multi-Robot Collaborative SLAM with Distributed LPFE," *IEEE RAL*, 2025.
3. Deng et al., "On the (In)Security of Secure ROS2," *ACM CCS*, 2022.
4. Zhang et al., "Comparison of Middlewares for Distributed ROS2," *JIRS*, 2024.
5. Petitpied et al., "Performance Comparison of ROS2 Middlewares for Multi-robot Mesh Networks," *JIRS*, 2025.
6. Park et al., "Optimization formula for DDS communication in ROS 2," *IEEE INFOCOM*, 2025.
7. Serov et al., "Multi-Robot Graph SLAM Using LIDAR," *ICARA*, 2024.
8. Torne et al., "MEM: Multi-Scale Embodied Memory for VLAs," *Physical Intelligence*, 2025.
9. Kim et al., "A 2.5D Map-Based Mobile Robot Localization via Cooperation of Aerial and Ground Robots," *PMC*, 2018.
10. Raspberry Pi Documentation, "AI HATs," 2025.
11. Hailo AI, "Hailo-RPi5-Examples," GitHub, 2025.
12. ROS2 Official Documentation, "Working with Zenoh," Jazzy.
13. Aguirre et al., "SROS2: Usable Cyber Security Tools for ROS 2," *IEEE IROS*, 2022.

**Gazebo 드론 시뮬레이션 (v3.1 신규)**

14. PX4 공식 문서, "Zenoh (PX4 ROS 2 rmw_zenoh)," https://docs.px4.io/main/en/middleware/zenoh
15. PX4 공식 문서, "uXRCE-DDS (PX4-ROS 2/DDS Bridge)," https://docs.px4.io/main/en/middleware/uxrce_dds
16. PX4 공식 문서, "ROS 2 User Guide," https://docs.px4.io/main/en/ros2/user_guide
17. PX4 공식 문서, "Multi-Vehicle Simulation with ROS 2," https://docs.px4.io/main/en/ros2/multi_vehicle
18. PX4 GitHub Issue #25494, "uXRCE-DDS Zenoh RMW compatibility," 2025. https://github.com/PX4/PX4-Autopilot/issues/25494
19. PX4 GitHub Issue #24159, "PX4 v1.16 + Ubuntu 24.04 + ROS2 Jazzy + Gazebo Harmonic error," 2024.
20. Presley, T., "On Quadcopter Offboard Simulations: A ROS2 Example," Medium, 2024.
21. Petrlík et al., "UAVs Beneath the Surface: Cooperative Autonomy for Subterranean Search and Rescue in DARPA SubT," *Field Robotics*, vol. 3, 2023. arXiv:2206.08185
22. "Cooperative Localization for GNSS-Denied Subterranean Navigation: A UAV–UGV Team Approach," *NAVIGATION*, 2024.
23. Tebbe et al., "A Modular and Scalable System Architecture for Heterogeneous UAV Swarms Using ROS 2 and PX4-Autopilot," arXiv:2510.27327, 2025.
24. "SkySim: A ROS2-based Simulation Environment for Drone Swarms," arXiv:2602.01226, 2026.
25. Castillo-Sánchez et al., "Swarm Robot Communications in ROS 2: An Experimental Study," *IEEE Access*, 2024.
26. Chatziparaschis et al., "Aerial and Ground Robot Collaboration for Autonomous Mapping in SAR," *Drones*, 4(4), 79, 2020.
27. "Multi-UAV networks for disaster monitoring," *Drone Systems and Applications*, 2024.
28. "Physical simulation of Marsupial UAV-UGV Systems Connected by a Hanging Tether," arXiv:2412.12776, 2024.
29. Open Robotics, "ROS 2 Jazzy Jalisco Released," May 2024. https://www.openrobotics.org/blog/2024/5/ros-jazzy-jalisco-released

---

*본 연구 보고서 v3.1은 Gazebo 드론 시뮬레이션 심화 조사 결과를 완전히 반영한 최종 문서입니다.*
*Phase 3-A 완료(Fake Drone 검증) → v3.2, Phase 3-B 완료(PX4 SITL 검증) → v4.0으로 갱신 예정.*
