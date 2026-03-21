---
title: "GHOST-5 Phase 3 참고자료"
date: 2026-03-21
draft: true
tags: ["ros2"]
categories: ["ros2"]
description: "> 작성일: 2026-03-16 > 프로젝트: GHOST-5 (다중 로봇 재난 탐색 시스템) > 목적: Phase 3 드론 레이어 통합 설계 참고용"
---

# GHOST-5 Phase 3 참고자료
# UAV → 지상 로봇 통신/GPS 릴레이 연구 조사

> 작성일: 2026-03-16  
> 프로젝트: GHOST-5 (다중 로봇 재난 탐색 시스템)  
> 목적: Phase 3 드론 레이어 통합 설계 참고용  
> 관련 하드웨어: Holybro X500 V2 + Pixhawk 6C + Raspberry Pi 4B

---

## 목차

1. [시나리오 개요](#1-시나리오-개요)
2. [드론의 역할 분류](#2-드론의-역할-분류)
3. [핵심 논문 및 연구 사례](#3-핵심-논문-및-연구-사례)
4. [통신 기술 비교](#4-통신-기술-비교)
5. [추천 시스템 아키텍처](#5-추천-시스템-아키텍처)
6. [ROS2 구현 코드 스니펫](#6-ros2-구현-코드-스니펫)
7. [추천 오픈소스 프로젝트](#7-추천-오픈소스-프로젝트)
8. [하드웨어 부품 목록](#8-하드웨어-부품-목록)
9. [Phase 3 통합 로드맵](#9-phase-3-통합-로드맵)
10. [핵심 기술 용어 정리](#10-핵심-기술-용어-정리)

---

## 1. 시나리오 개요

### 목표
GHOST-5의 5대 Raspberry Pi 지상 로봇이 재난 현장(건물 잔해, GPS 음영 구역)에서 활동할 때,  
상공에서 호버링 중인 드론이 **통신 중계 + 위치 정보 제공** 역할을 수행하는 이종(Heterogeneous) 다중 로봇 시스템 구현.

### 핵심 문제
```
재난 현장의 주요 도전:
  ├── GPS 음영 (건물 잔해, 지하, 도심 협곡)
  ├── 통신 인프라 붕괴 (기지국, WiFi AP 없음)
  ├── 지상 로봇 간 직접 통신 거리 한계
  └── 넓은 탐색 면적 대비 느린 지상 탐색 속도
```

### 연구계 공식 명칭
- **UAV-UGV Cooperative Localization** (UAV-UGV 협동 측위)
- **UAV as Communication Relay** (통신 릴레이로서의 UAV)
- **UAV as Localization Anchor** (측위 앵커로서의 UAV)
- **Heterogeneous Multi-Robot System** (이종 다중 로봇 시스템)

---

## 2. 드론의 역할 분류

### 역할 A: 통신 릴레이 (Communication Relay)
```
드론 [WiFi/LoRa 중계기]
  ├── GHOST-5 Robot 1 ─── 드론 ─── GHOST-5 Robot 4
  ├── GHOST-5 Robot 2 ─── 드론 ─── GHOST-5 Robot 5
  └── GHOST-5 Robot 3 ─── 드론 ─── 원격 지휘소
```
- 지상 로봇 간 직접 통신 불가 시 드론이 메시지 중계
- Gossip Protocol 메시지 중계에 직접 활용 가능
- LoRa: 최대 15km 범위, 저전력
- WiFi 802.11s Mesh: 높은 대역폭, 실시간 데이터 전송

### 역할 B: GPS 대체 측위 앵커 (Localization Anchor)
```
드론 [UWB 앵커, 고도 30~50m]
  │
  ├── UWB 신호 → Robot 1 (UWB 태그) → 거리 측정 → EKF 퓨전 → 절대위치
  ├── UWB 신호 → Robot 2 (UWB 태그) → 거리 측정 → EKF 퓨전 → 절대위치
  ├── UWB 신호 → Robot 3 (UWB 태그) → 거리 측정 → EKF 퓨전 → 절대위치
  ├── UWB 신호 → Robot 4 (UWB 태그) → 거리 측정 → EKF 퓨전 → 절대위치
  └── UWB 신호 → Robot 5 (UWB 태그) → 거리 측정 → EKF 퓨전 → 절대위치
```
- UWB(Ultra-Wideband) 정확도: ~10cm ~ 30cm
- 드론 GPS 절대 좌표를 기준점으로 삼변측량(trilateration)
- AMCL 대체 또는 보완 측위로 활용

### 역할 C: 정찰 + 좌표 전달 (Scout + Coordinate Provider)
```
드론 [열화상 + GPS]
  └── MLX90640 열화상 → 생존자 감지
        └── 생존자 GPS 좌표 publish (/drone/survivor_pose)
              └── GHOST-5 로봇 5대 구독
                    └── Frontier Exploration 우선순위 갱신
                          └── Gossip Protocol로 전파
```
- GHOST-5 기존 열화상(MLX90640) 활용
- Nav2 목표 좌표로 직접 변환 가능

---

## 3. 핵심 논문 및 연구 사례

### 논문 1 — DARPA SubT 재난 탐색 (Field Robotics, 2023)

| 항목 | 내용 |
|---|---|
| **제목** | UAVs Beneath the Surface: Cooperative Autonomy for Subterranean Search and Rescue in DARPA SubT |
| **저자** | Petrlík et al. (Czech Technical University, CTU-CRAS-NORLAB 팀) |
| **게재** | Field Robotics, vol. 3, pp. 1–68, 2023 |
| **arXiv** | arXiv:2206.08185 |
| **URL** | https://arxiv.org/abs/2206.08185 |

**핵심 내용:**
- UAV와 바퀴·다리·궤도형 UGV가 결합된 이종 로봇 팀이 DARPA SubT에서 협동 탐색 수행
- 드론은 지상 로봇 접근 불가 공간 탐색 + **분산 데이터 공유(data muling)** 담당
- GNSS 차단 환경에서 **UAV가 UWB 측위 앵커를 특정 위치에 배치**하여 다른 로봇에 외부 측위 제공
- DARPA SubT Virtual Track 2위, 실물 경쟁에서도 검증된 robust 시스템
- UGV의 "빵부스러기(breadcrumb)" 통신 노드 배치 전략과 결합

**GHOST-5 적용 포인트:**
```
- 드론이 재난 현장 상공에서 UWB 앵커 역할
- 건물 잔해로 GPS 수신 불가한 지점의 로봇에 위치 제공
- Bully Algorithm 리더 선출 후 리더 로봇이 드론과 우선 통신
```

---

### 논문 2 — UAV-UGV 협동 측위 (NAVIGATION Journal, 2024)

| 항목 | 내용 |
|---|---|
| **제목** | Cooperative Localization for GNSS-Denied Subterranean Navigation: A UAV–UGV Team Approach |
| **게재** | NAVIGATION: Journal of the Institute of Navigation, 2024 |
| **DOI** | 10.33012/navi.677 |
| **URL** | https://navi.ion.org/content/71/4/navi.677 |

**핵심 내용:**
- UAV에 **UWB 라디오** 탑재 → UGV와 직접 거리 측정
- **ROS single core**를 UGV 컴퓨터에서 실행, UAV와 UGV 모두 동일한 ROS 네트워크에서 토픽 공유
- UAV에서 UGV로 제어 명령 전달 및 상대 측위 지원
- 센서 퓨전 구성: **UWB + LiDAR 고도계 + IMU** → 3D 위치 오차 **1m 미만** 달성
- UGV 플랫폼: Clearpath Robotics Husky, FAST-LIO SLAM

**기술 스택:**
```yaml
드론:
  - UWB 라디오 (DW1000 계열)
  - LiDAR-Lite 단빔 고도계
  - Intel RealSense T265 (VIO, 속도 센서 역할)
UGV:
  - 3D SLAM (FAST-LIO)
  - UWB 태그
  - 3D LiDAR (드론 감지용)
통신:
  - WiFi (ROS 토픽 공유)
  - UWB (거리 측정)
```

**GHOST-5 적용 포인트:**
```
- ROS2 DDS로 드론-로봇 동일 토픽 공간 구성 가능
- Raspberry Pi 4B에서 UWB 거리 측정 + EKF 퓨전 실행 검토
- AMCL 초기화 실패 시 UWB 기반 위치를 초기 포즈로 활용
```

---

### 논문 3 — UWB 기반 이종 로봇 측위 (arXiv, 2025)

| 항목 | 내용 |
|---|---|
| **제목** | Radio-based Multi-Robot Odometry and Relative Localization |
| **게재** | arXiv, 2025 (September) |
| **URL** | https://arxiv.org/html/2509.26558 |
| **GitHub** | https://github.com/robotics-upo/mr-radio-localization (**오픈소스**) |

**핵심 내용:**
- UAV-UGV 이종 로봇 시스템에서 **다중 UWB 트랜시버** 활용 실시간 상대 측위
- **Nonlinear Least Squares(NLS) 최적화**로 UAV-UGV 간 상대 변환 실시간 계산
- Pose Graph Optimization으로 레이더 오도메트리 + UWB 거리 측정 통합 퓨전
- **Gazebo Harmonic + PX4 SITL** 호환 UWB 시뮬레이터 플러그인 포함
- 실제 UAV-UGV 실험으로 검증 완료

**GHOST-5 적용 포인트:**
```
- 오픈소스 코드 직접 활용 가능
- Gazebo에서 GHOST-5 + 드론 UWB 시뮬레이션 가능
- PX4 SITL과 ROS2 Jazzy 연동 참고
```

---

### 논문 4 — LoRa + ROS 통합 통신 (Computer Communications, 2024)

| 항목 | 내용 |
|---|---|
| **제목** | Mission-critical UAV swarm coordination and cooperative positioning using an integrated ROS-LoRa-based communications architecture |
| **게재** | Computer Communications, Volume 225, 2024, pp. 27-43 |
| **DOI** | 10.1016/j.comcom.2024.02494 |
| **URL** | https://www.sciencedirect.com/science/article/abs/pii/S0140366424002494 |

**핵심 내용:**
- 재난 관리/수색구조 시나리오에서 **LoRa-ROS 통합 시스템** 개발
- GPS 불가 환경에서 **협동 측위(CRPS, Cooperative Relative Positioning System)** 실현
- LoRa 메시 네트워킹(BALORA 커스텀 PCB)으로 UAV 간 센서 정보 분산 공유
- IMU 퓨전으로 GPS 대체 측위, GPS+IMU 기준과 동등한 정확도 달성

**LoRa 적합 데이터:**
```yaml
전송 가능 (저대역폭):
  - GPS 좌표 (위도/경도/고도)
  - 로봇 상태 메시지 (배터리, 속도, 모드)
  - Gossip Protocol 제어 메시지
  - Bully Algorithm 선출 메시지
  - 긴급 명령 (all_stop, return_home)

전송 부적합 (고대역폭 필요):
  - 열화상 이미지 (MLX90640)
  - LiDAR 포인트 클라우드
  - 카메라 영상
```

---

### 논문 5 — GPS 차단 환경 공중-지상 협동 (Drones MDPI, 2025)

| 항목 | 내용 |
|---|---|
| **제목** | UAV Autonomous Navigation System Based on Air–Ground Collaboration in GPS-Denied Environments |
| **게재** | Drones 2025, 9(6), 442 |
| **DOI** | 10.3390/drones9060442 |
| **URL** | https://www.mdpi.com/2504-446X/9/6/442 |

**핵심 내용:**
- 다수의 UAV가 시각 감지 + UWB 기술을 통합한 **모바일 앵커 삼변측량(Mobile Anchor Trilateration)** 개발
- 실시간 3D 환경 모델 구축 + 정밀 측위 정보로 근지면 UAV 탐색 지원
- 공중 감시 UAV(정찰)와 근지면 UAV(탐색) 간 역할 분리 아키텍처

**삼변측량 원리 (GHOST-5 적용):**
```
드론 위치(알고 있음): P_drone = (x_d, y_d, z_d) [GPS]
UWB 거리 측정:       d_1, d_2, d_3, d_4, d_5 [각 로봇까지]

각 로봇 위치 추정:
  (x_r - x_d)² + (y_r - y_d)² + (z_r - z_d)² = d_i²
  → 드론 1대: 구 표면 (위치 후보)
  → 드론 3대: 교점 = 정확한 위치

※ 고도를 알면 드론 1대로도 2D 측위 가능
```

---

### 논문 6 — UAV-UGV 산업 협동 (Sensors MDPI, 2025)

| 항목 | 내용 |
|---|---|
| **제목** | Multi-Domain Robot Swarm for Industrial Mapping and Asset Monitoring |
| **게재** | Sensors 2025, 25(20), 6295 |
| **DOI** | 10.3390/s25206295 |
| **URL** | https://www.mdpi.com/1424-8220/25/20/6295 |

**핵심 내용:**
- UGV(LiDAR SLAM) + UAV(이미지 수집) 결합 이종 다중 로봇 시스템
- 실내 GPS 불가 환경에서도 정확한 측위와 착륙 정밀도 달성
- **탄력적 통신 프레임워크**: UAV가 UGV 위에 착륙하여 배터리 충전 후 재출발
- 84% 계기 감지 정확도, 87.5% 수치 판독 정확도
- Leader-Follower 접근법으로 통신 부하 최소화

**GHOST-5 적용 포인트:**
```
- 드론이 GHOST-5 리더 로봇 위에 착륙 → 배터리 교환/충전 프로토콜
- UAV-UGV 착륙 시 UWB + ArUco 마커 결합 정밀 착륙
```

---

### 논문 7 — 드론이 드론 안내 (IEEE ICRA, 2024)

| 항목 | 내용 |
|---|---|
| **제목** | Drones Guiding Drones: Cooperative Navigation of a Less-Equipped Micro Aerial Vehicle in Cluttered Environments |
| **게재** | IEEE ICRA 2024 |
| **arXiv** | arXiv:2312.09786 |
| **URL** | https://arxiv.org/html/2312.09786v2 |

**핵심 내용:**
- 성능이 좋은 1차 UAV(3D LiDAR)가 성능 낮은 2차 UAV(카메라만)를 안내
- 1차 UAV가 3D 점유 지도 구축 + 두 UAV 충돌 회피 경로 동시 계획
- GNSS 차단 환경에서 LiDAR 기반 상대 측위로 안내
- **이 개념을 UAV → UGV(지상 로봇)로 확장하면 GHOST-5 시나리오와 정확히 일치**

---

### 논문 8 — 재난 UAV 통신 네트워크 리뷰 (DSA Journal, 2024)

| 항목 | 내용 |
|---|---|
| **제목** | Multi-UAV networks for disaster monitoring: challenges and opportunities from a network perspective |
| **게재** | Drone Systems and Applications (DSA), 2024 |
| **URL** | https://cdnsciencepub.com/doi/10.1139/dsa-2023-0079 |

**핵심 내용 (리뷰 논문, 광범위 참고용):**
- 재난 시나리오에서 UAV는 **필수적인 통신 릴레이**로, 인프라가 붕괴된 지역에 임시 네트워크 구축
- LoRa 기반 레이어(장거리·저페이로드) + IEEE 802.11s 레이어(중거리·고페이로드) 혼합이 최신 트렌드
- 대규모 재난일수록 멀티 UAV 스웜 + 지상 시스템 + 위성 연동 복합 아키텍처 필요
- 배포 전략, 데이터 처리, 라우팅, 보안이 주요 연구 과제

---

### 논문 9 — UAV-UGV Magnetic 기반 측위 (arXiv, 2025)

| 항목 | 내용 |
|---|---|
| **제목** | Fly, Track, Land: Infrastructure-less Magnetic Localization for Heterogeneous UAV–UGV Teaming |
| **게재** | arXiv, 2025 (March) |
| **URL** | https://arxiv.org/html/2603.08926 |

**핵심 내용:**
- 자기 유도(MI) 기반 + UWB + GNSS 다층 측위 아키텍처
- 장거리: UWB/GNSS → 단거리 최종 도킹: 자기 센서
- 드론이 UGV 위에 정밀 착륙 시 100% 성공률, cm 수준 정확도
- 인프라 불필요한 완전 독립형 시스템

---

### 논문 10 — LoRa + ROS UAV 통신 구현 (IEEE, 2023)

| 항목 | 내용 |
|---|---|
| **제목** | Implementing Mission-Critical UAV Swarm Coordination Through the Integration of LoRa and ROS Frameworks |
| **게재** | IEEE Conference (DCOSS-IoT), 2023 |
| **URL** | https://ieeexplore.ieee.org/document/10286934/ |

**핵심 내용:**
- LoRa-ROS 통합 무선 통신 시스템 구현 및 실험 검증
- UAV-to-GCS (지상 통제소) 통신에서 LoRa 프로토콜 적합성 확인
- 재난/원격지 환경에서 전통 WiFi/셀룰러 불가 시 대안으로 검증

---

## 4. 통신 기술 비교

### 4.1 기술별 상세 비교

| 기술 | 범위 | 대역폭 | 지연 | 전력 | GPS 데이터 전송 | ROS2 연동 | GHOST-5 적합성 |
|---|---|---|---|---|---|---|---|
| **UWB** | ~100m | 낮음 | 매우 낮음 | 중간 | ✅ 측위 직접 제공 | ✅ | ⭐⭐⭐⭐⭐ |
| **LoRa** | ~15km | 매우 낮음 | 낮음 | 매우 낮음 | ✅ 좌표만 | ✅ | ⭐⭐⭐⭐ |
| **WiFi 802.11s Mesh** | ~300m | 높음 | 낮음 | 높음 | ✅ 풍부한 데이터 | ✅ (DDS) | ⭐⭐⭐ |
| **LoRa + WiFi 혼합** | 장거리+고속 | 혼합 | 혼합 | 중간 | ✅ 최적 | ✅ | ⭐⭐⭐⭐⭐ |
| **ZigBee** | ~100m | 낮음 | 낮음 | 낮음 | ✅ 제한적 | △ | ⭐⭐ |

### 4.2 GHOST-5 재난 시나리오 추천 조합

```
1순위: UWB (측위) + WiFi Mesh (데이터 전송)
  - UWB: 각 로봇 절대 위치 제공 (정확도 우수)
  - WiFi: 열화상 데이터, 맵 공유, ROS2 토픽

2순위: UWB (측위) + LoRa (제어 명령)
  - WiFi 불가 시 LoRa로 긴급 명령 전달
  - Gossip Protocol 메시지는 LoRa로 충분

3순위 (장거리 백업): LoRa 단독
  - 드론이 2km 이상 원거리 이동 시
  - 최소한의 상태/좌표만 전달
```

---

## 5. 추천 시스템 아키텍처

### 5.1 전체 시스템 구성

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                [원격 지휘소]
                     │ LoRa (장거리)
━━━━━━━━━━━━━━━━━━━━━│━━━━━━━━━━━━━━━━━━━━━━━━━
              [드론: X500 V2]
              고도 30~50m 호버링
              ├── Pixhawk 6C (PX4 v1.15)
              ├── Raspberry Pi 4B (ROS2 Jazzy)
              ├── MLX90640 열화상 카메라
              ├── UWB 모듈 ×3 (앵커)
              └── LoRa 모듈 (SX1276)
                     │
          ┌──────────┼──────────┐
          │ UWB      │ WiFi     │ LoRa
━━━━━━━━━━│━━━━━━━━━━│━━━━━━━━━━│━━━━━━━━━━━━
    [GHOST-5 Robot 1~5]
    각 로봇:
    ├── Raspberry Pi 4B
    ├── LiDAR (SLAM/Nav2)
    ├── MLX90640
    ├── UWB 태그 (DWM1001)
    └── WiFi / LoRa 모듈
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5.2 ROS2 토픽 구조

```
드론 발행 토픽:
  /drone/gps_pose              (geometry_msgs/PoseStamped)   - 드론 GPS 절대 위치
  /drone/survivor_pose         (geometry_msgs/PoseStamped)   - 감지된 생존자 위치
  /drone/thermal_image         (sensor_msgs/Image)           - 열화상 이미지
  /drone/uwb_anchor_pose       (geometry_msgs/PoseStamped)   - UWB 앵커 위치
  /drone/battery_status        (sensor_msgs/BatteryState)    - 드론 배터리
  /drone/status                (std_msgs/String)             - 드론 상태

로봇 → 드론 발행 토픽:
  /robot_{id}/uwb_range        (std_msgs/Float64)            - UWB 거리 측정값
  /robot_{id}/status           (std_msgs/String)             - 로봇 상태
  /robot_{id}/need_help        (std_msgs/Bool)               - 지원 요청
  /swarm/gossip                (std_msgs/String)             - Gossip 메시지
  /swarm/leader_id             (std_msgs/Int32)              - 현재 리더 ID
```

### 5.3 측위 퓨전 파이프라인

```
[드론 GPS]     → 드론 절대 위치 (x_d, y_d, z_d)
[UWB 거리]     → 드론-로봇 간 거리 d_i
[로봇 IMU]     → 단기 오도메트리
[로봇 LiDAR]   → SLAM 상대 위치

EKF 퓨전:
  State: [x, y, z, vx, vy, vz]
  Prediction: IMU 오도메트리
  Update: UWB 거리 측정 + 드론 GPS 기준점
  Output: 보정된 절대 위치 → AMCL 초기 포즈 또는 대체
```

---

## 6. ROS2 구현 코드 스니펫

### 6.1 드론 정찰 노드 (생존자 좌표 publish)

```python
#!/usr/bin/env python3
"""
GHOST-5 Drone Scout Node
드론이 열화상으로 생존자 감지 후 GHOST-5 로봇에 좌표 전달
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
import numpy as np


class DroneScoutNode(Node):
    def __init__(self):
        super().__init__('drone_scout')

        # 열화상 구독 (MLX90640)
        self.thermal_sub = self.create_subscription(
            Image,
            '/thermal/image_raw',
            self.thermal_callback,
            10
        )

        # 드론 자신의 위치 구독 (PX4 GPS)
        self.odom_sub = self.create_subscription(
            Odometry,
            '/drone/odometry',
            self.odom_callback,
            10
        )

        # GHOST-5 로봇들에게 생존자 위치 전달
        self.survivor_pub = self.create_publisher(
            PoseStamped,
            '/drone/survivor_pose',
            10
        )

        self.current_pose = None
        self.TEMP_THRESHOLD = 36.5  # 체온 임계값 (섭씨)

    def odom_callback(self, msg: Odometry):
        self.current_pose = msg.pose.pose

    def detect_human_signature(self, thermal_array: np.ndarray) -> bool:
        """열화상에서 사람 체온 감지"""
        max_temp = np.max(thermal_array)
        return max_temp >= self.TEMP_THRESHOLD

    def get_survivor_gps_from_thermal(self, thermal_array: np.ndarray) -> tuple:
        """열화상에서 최고온도 픽셀의 실제 GPS 좌표 계산 (간략화)"""
        # TODO: 카메라 내부 파라미터 + 드론 고도로 정밀 계산
        hotspot = np.unravel_index(np.argmax(thermal_array), thermal_array.shape)
        return hotspot  # (row, col) → 실제 구현 시 GPS 변환 필요

    def thermal_callback(self, msg: Image):
        if self.current_pose is None:
            return

        # Image → numpy (32x24 MLX90640)
        thermal_data = np.frombuffer(msg.data, dtype=np.float32).reshape(24, 32)

        if self.detect_human_signature(thermal_data):
            survivor_pose = PoseStamped()
            survivor_pose.header.stamp = self.get_clock().now().to_msg()
            survivor_pose.header.frame_id = 'map'
            survivor_pose.pose = self.current_pose  # 드론 위치 기준 (정밀화 필요)

            self.survivor_pub.publish(survivor_pose)
            self.get_logger().info(
                f'🔥 생존자 감지! 위치: ({self.current_pose.position.x:.2f}, '
                f'{self.current_pose.position.y:.2f})'
            )


def main():
    rclpy.init()
    node = DroneScoutNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 6.2 지상 로봇 — 드론 좌표 구독 + Nav2 연동

```python
#!/usr/bin/env python3
"""
GHOST-5 Robot — 드론 생존자 좌표 구독 후 Nav2로 이동
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose


class RobotMissionNode(Node):
    def __init__(self, robot_id: int):
        super().__init__(f'robot_{robot_id}_mission')
        self.robot_id = robot_id

        # 드론 생존자 위치 구독
        self.survivor_sub = self.create_subscription(
            PoseStamped,
            '/drone/survivor_pose',
            self.survivor_callback,
            10
        )

        # Nav2 Action Client
        self.nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        # Gossip Protocol용 발행 (다른 로봇에게 전파)
        # 실제 구현 시 gossip_publisher 추가

    def survivor_callback(self, msg: PoseStamped):
        self.get_logger().info(
            f'[Robot {self.robot_id}] 드론으로부터 생존자 위치 수신: '
            f'({msg.pose.position.x:.2f}, {msg.pose.position.y:.2f})'
        )
        self.navigate_to_survivor(msg)

    def navigate_to_survivor(self, pose: PoseStamped):
        if not self.nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn('Nav2 서버 연결 실패')
            return

        goal = NavigateToPose.Goal()
        goal.pose = pose

        self.get_logger().info(f'[Robot {self.robot_id}] 생존자 위치로 이동 시작')
        self.nav_client.send_goal_async(
            goal,
            feedback_callback=self.nav_feedback_callback
        )

    def nav_feedback_callback(self, feedback_msg):
        remaining = feedback_msg.feedback.distance_remaining
        self.get_logger().info(f'남은 거리: {remaining:.2f}m')


def main():
    rclpy.init()
    node = RobotMissionNode(robot_id=1)
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 6.3 UWB 기반 로봇 측위 노드 (EKF 퓨전)

```python
#!/usr/bin/env python3
"""
UWB 거리 측정 → EKF 퓨전 → 보정 위치 publish
드론의 UWB 앵커와 로봇의 UWB 태그 거리를 활용
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
import numpy as np


class UWBLocalizationNode(Node):
    def __init__(self, robot_id: int):
        super().__init__(f'uwb_localization_{robot_id}')
        self.robot_id = robot_id

        # 드론 앵커 위치 구독
        self.anchor_sub = self.create_subscription(
            PoseStamped,
            '/drone/uwb_anchor_pose',
            self.anchor_callback,
            10
        )

        # UWB 거리 측정값 구독 (DWM1001 드라이버)
        self.range_sub = self.create_subscription(
            Float64,
            f'/robot_{robot_id}/uwb_range',
            self.range_callback,
            10
        )

        # 보정 위치 발행
        self.pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            f'/robot_{robot_id}/uwb_corrected_pose',
            10
        )

        # AMCL 초기 포즈 설정 (UWB로 초기화)
        self.initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            '/initialpose',
            10
        )

        self.anchor_pose = None
        self.last_range = None
        self.initialized = False

    def anchor_callback(self, msg: PoseStamped):
        self.anchor_pose = msg.pose

    def range_callback(self, msg: Float64):
        self.last_range = msg.data

        if self.anchor_pose is not None and self.last_range is not None:
            self.update_position()

    def update_position(self):
        """
        단일 앵커 + 고도 정보로 2D 위치 추정
        실제 구현 시 다중 앵커 삼변측량 또는 EKF 사용 권장
        """
        # 간략화된 예시 (실제는 EKF 또는 NLS 최적화)
        d = self.last_range
        ax, ay, az = (
            self.anchor_pose.position.x,
            self.anchor_pose.position.y,
            self.anchor_pose.position.z
        )
        # 로봇 고도 ≈ 0 가정
        d_2d = np.sqrt(max(d**2 - az**2, 0))

        corrected = PoseWithCovarianceStamped()
        corrected.header.stamp = self.get_clock().now().to_msg()
        corrected.header.frame_id = 'map'
        corrected.pose.pose.position.x = ax  # 실제는 방향 벡터 필요
        corrected.pose.pose.position.y = ay
        # 공분산: UWB 정확도 ~0.1m
        corrected.pose.covariance[0] = 0.1  # x 분산
        corrected.pose.covariance[7] = 0.1  # y 분산

        self.pose_pub.publish(corrected)

        # AMCL 미초기화 시 초기 포즈로 설정
        if not self.initialized:
            self.initial_pose_pub.publish(corrected)
            self.initialized = True
            self.get_logger().info('UWB로 AMCL 초기 포즈 설정 완료')
```

### 6.4 LoRa 통신 브릿지 (ROS2 ↔ LoRa)

```python
#!/usr/bin/env python3
"""
LoRa ↔ ROS2 브릿지
드론의 LoRa 모듈로 Gossip Protocol 메시지 중계
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import json
import threading


class LoRaBridgeNode(Node):
    """
    LoRa 모듈 (SX1276, UART 연결) ↔ ROS2 토픽 브릿지
    드론 또는 지상 로봇에서 실행
    """

    def __init__(self):
        super().__init__('lora_bridge')

        # LoRa UART 설정
        self.declare_parameter('lora_port', '/dev/ttyUSB0')
        self.declare_parameter('lora_baudrate', 9600)
        port = self.get_parameter('lora_port').value
        baud = self.get_parameter('lora_baudrate').value

        try:
            self.lora_serial = serial.Serial(port, baud, timeout=1.0)
            self.get_logger().info(f'LoRa 연결: {port}@{baud}')
        except serial.SerialException as e:
            self.get_logger().error(f'LoRa 연결 실패: {e}')
            self.lora_serial = None

        # ROS2 Gossip 메시지 구독 → LoRa 송신
        self.gossip_sub = self.create_subscription(
            String, '/swarm/gossip',
            self.gossip_to_lora, 10
        )

        # LoRa 수신 → ROS2 Gossip 발행
        self.gossip_pub = self.create_publisher(
            String, '/swarm/gossip_received', 10
        )

        # GPS 좌표 구독 → LoRa 송신 (주기적)
        self.gps_sub = self.create_subscription(
            String, '/drone/gps_string',
            self.gps_to_lora, 10
        )

        # LoRa 수신 스레드
        if self.lora_serial:
            self.receive_thread = threading.Thread(
                target=self.lora_receive_loop, daemon=True
            )
            self.receive_thread.start()

    def gossip_to_lora(self, msg: String):
        """ROS2 Gossip → LoRa 송신"""
        if not self.lora_serial:
            return
        payload = json.dumps({'type': 'gossip', 'data': msg.data})
        self.lora_serial.write((payload + '\n').encode())

    def gps_to_lora(self, msg: String):
        """GPS 좌표 → LoRa 송신"""
        if not self.lora_serial:
            return
        payload = json.dumps({'type': 'gps', 'data': msg.data})
        self.lora_serial.write((payload + '\n').encode())

    def lora_receive_loop(self):
        """LoRa 수신 루프 (별도 스레드)"""
        while rclpy.ok():
            try:
                if self.lora_serial.in_waiting:
                    raw = self.lora_serial.readline().decode().strip()
                    data = json.loads(raw)

                    if data.get('type') == 'gossip':
                        msg = String()
                        msg.data = data['data']
                        self.gossip_pub.publish(msg)

            except (json.JSONDecodeError, serial.SerialException):
                pass
```

---

## 7. 추천 오픈소스 프로젝트

| 프로젝트 | GitHub URL | 특징 | GHOST-5 활용 |
|---|---|---|---|
| **mr-radio-localization** | https://github.com/robotics-upo/mr-radio-localization | UWB UAV-UGV 측위, Gazebo SITL | UWB 측위 직접 참고 |
| **CrazySwarm2** | https://github.com/IMRCLab/crazyswarm2 | ROS2 다중 드론 스웜 | 군집 비행 알고리즘 |
| **Aerostack2** | https://github.com/aerostack2/aerostack2 | ROS2 드론 미션 프레임워크 | 드론 미션 계획 |
| **PX4-ROS2 Interface** | https://github.com/PX4/px4_ros_com | PX4 ↔ ROS2 공식 브릿지 | 드론 제어 |
| **DARPA SubT 데이터셋** | https://subtchallenge.world/resources | 실제 재난 rosbag | 알고리즘 검증 |
| **px4_sim_ros2** | https://github.com/ParsaKhaledi/px4_sim_ros2 | PX4+Gazebo+ROS2 시뮬 환경 | 시뮬레이션 |
| **simtofly-guide** | https://github.com/simtofly/simtofly-guide | SITL → 실기체 튜토리얼 | 단계별 학습 |

---

## 8. 하드웨어 부품 목록

### 8.1 드론 본체 (Holybro X500 V2 기준)

| 부품 | 모델 | 가격 (참고) | 역할 |
|---|---|---|---|
| 프레임 키트 | Holybro X500 V2 ARF | ~$250 | 본체 |
| 비행 컨트롤러 | Pixhawk 6C | ~$200 | PX4 실행 |
| GPS | M8N | ~$50 | 드론 절대 위치 |
| 컴패니언 컴퓨터 | Raspberry Pi 4B (4GB) | ~$80 | ROS2 Jazzy |
| 배터리 | 4S 5000mAh LiPo | ~$50 | 전원 |
| RC 조종기 | RadioMaster TX16S | ~$150 | 수동 제어 |
| SiK 텔레메트리 | 915MHz | ~$50 | QGroundControl |
| **합계** | | **~$830** | |

### 8.2 통신/측위 모듈 (추가)

| 부품 | 모델 | 가격 | 역할 |
|---|---|---|---|
| **UWB 앵커 (드론)** | DWM1001 ×3 | ~$30/개 = $90 | 드론에서 측위 신호 송출 |
| **UWB 태그 (로봇)** | DWM1001 ×5 | ~$30/개 = $150 | 각 로봇에 부착 |
| **LoRa 모듈 (드론)** | Ra-02 SX1276 | ~$10 | 장거리 통신 |
| **LoRa 모듈 (로봇)** | Ra-02 SX1276 ×5 | ~$10/개 = $50 | 각 로봇 |
| **WiFi 라우터 (드론)** | 소형 AP 모듈 | ~$30 | ROS2 DDS 연결 |
| **열화상 (드론)** | MLX90640 | ~$50 | 생존자 감지 |
| **합계** | | **~$380** | |

### 8.3 UWB 모듈 연결 (DWM1001 ↔ Raspberry Pi)

```
DWM1001 ─── SPI/UART ─── Raspberry Pi 4B
  VCC  → 3.3V
  GND  → GND
  MOSI → GPIO10 (SPI0_MOSI)
  MISO → GPIO9  (SPI0_MISO)
  SCK  → GPIO11 (SPI0_SCLK)
  CS   → GPIO8  (SPI0_CE0)

ROS2 드라이버: ros2_uwb_driver (커뮤니티)
토픽: /uwb/range [std_msgs/Float64]
```

---

## 9. Phase 3 통합 로드맵

### 9.1 단계별 구현 계획

```
Phase 2 (현재): 지상 로봇 SLAM/Nav2/Frontier 탐색
  └── 완료 후 Phase 3 진입

Phase 3-A (2주): Gazebo SITL 시뮬레이션
  ├── PX4 + ROS2 Jazzy 연동 환경 구축
  ├── X500 V2 Gazebo 모델 추가
  ├── UWB 시뮬레이터 플러그인 설치 (mr-radio-localization)
  ├── 드론-GHOST-5 동일 ROS2 네트워크 구성
  └── /drone/survivor_pose → Nav2 연동 테스트

Phase 3-B (2주): 소형 드론 프로토타입
  ├── Crazyflie 2.1 + CrazySwarm2로 실내 테스트
  ├── UWB 측위 정확도 검증 (DWM1001)
  ├── LoRa 통신 범위/지연 측정
  └── GHOST-5 로봇 1대 ↔ 드론 위치 공유 검증

Phase 3-C (4주): X500 V2 실기체 통합
  ├── 하드웨어 조립 및 PX4 캘리브레이션
  ├── Offboard 모드 ROS2 제어 구현
  ├── UWB 앵커 → 로봇 5대 동시 측위 테스트
  ├── 열화상 생존자 감지 → Nav2 목표 전달
  └── Gossip Protocol LoRa 중계 통합 테스트

Phase 3-D (2주): 통합 재난 시나리오 테스트
  ├── GPS 음영 구역 시뮬레이션
  ├── Bully Algorithm 리더 선출 + 드론 우선 통신
  ├── 전체 시스템 내구성 테스트
  └── 성능 측정 (측위 정확도, 통신 지연, 커버리지)
```

### 9.2 우선순위 구현 순서

```
1️⃣ Gazebo에서 PX4 + ROS2 시뮬레이션 환경 구축
     → px4_sim_ros2 참고

2️⃣ /drone/survivor_pose 토픽 → Nav2 Goal 연동
     → 6.2 코드 스니펫 참고

3️⃣ UWB 시뮬레이터로 측위 알고리즘 검증
     → mr-radio-localization 참고

4️⃣ LoRa 모듈 ROS2 브릿지 구현
     → 6.4 코드 스니펫 참고

5️⃣ 실기체 비행 (반드시 SITL 충분히 후)
```

### 9.3 주요 성능 목표

| 항목 | 목표값 | 측정 방법 |
|---|---|---|
| UWB 측위 정확도 | < 0.3m (2D) | Motion Capture 또는 RTK GPS 기준 |
| LoRa 통신 지연 | < 500ms | 메시지 왕복 시간 측정 |
| 드론 비행 시간 | > 15분 | 배터리 완충 기준 |
| 생존자 감지 범위 | > 20m | 열화상 + 드론 고도 |
| 시스템 전체 지연 | < 2초 (감지→로봇 이동) | 시나리오 시뮬레이션 |

---

## 10. 핵심 기술 용어 정리

| 용어 | 설명 |
|---|---|
| **UWB (Ultra-Wideband)** | 초광대역 무선 통신. 매우 짧은 펄스로 정밀 거리 측정 (~10cm). GPS 대체 실내 측위에 사용 |
| **LoRa (Long Range)** | 저전력 장거리 무선 통신. 최대 15km. 저대역폭. 재난 현장 명령 전달에 적합 |
| **DWM1001** | Decawave의 UWB 모듈. $30 내외. SPI/UART 인터페이스. ROS2 드라이버 존재 |
| **Trilateration (삼변측량)** | 3개 이상의 앵커까지 거리로 위치 추정. GPS 원리와 동일 |
| **EKF (Extended Kalman Filter)** | 비선형 시스템의 상태 추정 필터. IMU + UWB 퓨전에 사용 |
| **Data Muling** | 로봇이 이동하며 데이터를 수집·전달하는 방식. DARPA SubT에서 사용 |
| **GNSS-Denied** | GPS/GNSS 신호가 없거나 불안정한 환경 (실내, 지하, 건물 잔해) |
| **PX4 SITL** | Software-In-The-Loop. 실제 드론 없이 소프트웨어로 비행 시뮬레이션 |
| **Offboard Mode** | PX4 외부(ROS2)에서 비행 명령을 내리는 모드. 자율 비행에 사용 |
| **uXRCE-DDS** | PX4와 ROS2를 직접 연결하는 미들웨어. MAVROS 대체 |
| **Heterogeneous Multi-Robot** | 서로 다른 종류(UAV+UGV)의 로봇이 협동하는 시스템 |
| **Mobile Anchor Trilateration** | 드론이 이동하며 여러 위치에서 측위 신호를 보내 지상 로봇 위치 추정 |

---

## 참고문헌 목록

```
[1] Petrlík et al., "UAVs Beneath the Surface: Cooperative Autonomy for 
    Subterranean Search and Rescue in DARPA SubT," Field Robotics, vol. 3, 
    pp. 1–68, 2023. arXiv:2206.08185

[2] "Cooperative Localization for GNSS-Denied Subterranean Navigation: 
    A UAV–UGV Team Approach," NAVIGATION Journal, 2024. DOI:10.33012/navi.677

[3] "Radio-based Multi-Robot Odometry and Relative Localization," 
    arXiv:2509.26558, 2025. GitHub: robotics-upo/mr-radio-localization

[4] "Mission-critical UAV swarm coordination and cooperative positioning 
    using an integrated ROS-LoRa-based communications architecture,"
    Computer Communications, vol. 225, pp. 27–43, 2024.

[5] Zhao et al., "UAV Autonomous Navigation System Based on Air–Ground 
    Collaboration in GPS-Denied Environments," Drones, 9(6), 442, 2025.
    DOI:10.3390/drones9060442

[6] "Multi-Domain Robot Swarm for Industrial Mapping and Asset Monitoring,"
    Sensors, 25(20), 6295, 2025. DOI:10.3390/s25206295

[7] "Drones Guiding Drones: Cooperative Navigation of a Less-Equipped 
    Micro Aerial Vehicle in Cluttered Environments," IEEE ICRA 2024.
    arXiv:2312.09786

[8] "Multi-UAV networks for disaster monitoring: challenges and opportunities 
    from a network perspective," Drone Systems and Applications, 2024.

[9] "Fly, Track, Land: Infrastructure-less Magnetic Localization for 
    Heterogeneous UAV–UGV Teaming," arXiv:2603.08926, 2025.

[10] "Implementing Mission-Critical UAV Swarm Coordination Through the 
     Integration of LoRa and ROS Frameworks," IEEE DCOSS-IoT, 2023.

[11] Wang Shule et al., "UWB-Based Localization for Multi-UAV Systems and 
     Collaborative Heterogeneous Multi-Robot Systems," 
     Procedia Computer Science 175, pp. 357–364, 2020.

[12] "A Comprehensive Review of UAV-UGV Collaboration: Advancements and 
     Challenges," J. Sens. Actuator Netw., 13(6), 81, 2024.
     DOI:10.3390/jsan13060081
```

---

*문서 끝 | GHOST-5 Phase 3 UAV 통합 참고자료*  
*다음 업데이트: Phase 3-A 시뮬레이션 완료 후*
