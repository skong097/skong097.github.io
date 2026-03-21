---
title: "GHOST-5 Phase 3 세션 작업 로그 (M08 + M09 + M10)"
date: 2026-03-21
draft: true
tags: ["ros2"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **Phase**: 3 — 군집 지능 **작업 모듈**: M08, M09, M10"
---

# GHOST-5 Phase 3 세션 작업 로그 (M08 + M09 + M10)

**날짜**: 2026-03-18  
**Phase**: 3 — 군집 지능  
**작업 모듈**: M08, M09, M10  
**작업자**: Stephen Kong (`gjkong`)  
**이전 완료**: Phase 1 (M01~M04), Phase 2 (M05~M07) 전체 완료

---

## 세션 요약

| 모듈 | 내용 | 빌드 | 로직 검증 | 하드웨어 검증 |
|---|---|---|---|---|
| M08 | Bully Leader Election | ⬜ 빌드 대기 | ✅ 5/5 | ⬜ 하드웨어 대기 |
| M09 | MMPF Frontier 탐색 | ✅ | ✅ 5/5 | ⬜ 하드웨어 대기 |
| M10 | Delta Map Merger | ✅ | ✅ 4/4 | ⬜ 하드웨어 대기 |

---

## M08 — Bully Algorithm Leader Election

### 개요
5대 중 생존 로봇 중 최고 ID가 3초 내 리더로 선출.  
v1.2 Split-Brain 방지 쿼럼, v1.3 Election Storm 방지 Backoff,  
[B2] 지수 백오프 Write Lock으로 Redis HA 레이스 컨디션 방지.

### 생성 파일

| 파일 경로 | 설명 |
|---|---|
| `ghost5_swarm/ghost5_swarm/leader_election.py` | Bully + Quorum(v1.2) + Backoff(v1.3) |
| `ghost5_swarm/ghost5_swarm/election_guard.py` | [B2] 지수 백오프 + Jitter Write Lock |
| `ghost5_swarm/ghost5_swarm/__init__.py` | 패키지 초기화 |
| `ghost5_swarm/setup.py` | ghost5_swarm 패키지 설치 설정 |
| `ghost5_swarm/package.xml` | ghost5_swarm 패키지 의존성 정의 |
| `tests/unit/test_leader_election_m08.py` | M08 완료 조건 검증 스크립트 |

### 핵심 설계
```
Bully Algorithm:
  Leader Heartbeat 3초 미수신 → 사망 투표 + 선거 발동
  자신보다 높은 ID에 ELECTION 전송 → 3초 내 응답 없으면 쿼럼 확인 → VICTORY

[v1.3] Election Storm 방지 Backoff:
  delay = (MAX_ROBOT_ID - my_id) × 0.1s
  Robot-5: 0.0s → Robot-4: 0.1s → Robot-3: 0.2s → Robot-1: 0.4s

[v1.2] Split-Brain 방지 쿼럼:
  VICTORY 전 최소 3대 /swarm/leader_dead 투표 확인
  쿼럼 미달 → 5s 대기 후 재시도 (최대 3회)

[B2] ElectionGuard 지수 백오프:
  delay = min(0.5 × 2^attempt, 8.0) × random(0.5, 1.0)
  총 최대 대기 ~19.5s (리더 교체 윈도우 커버)
  WRITE_LOCK_KEY: 'swarm:election:write_lock' (TTL 10s)
```

### 빌드 방법
```bash
# resource 마커 생성 (필수)
mkdir -p ~/ghost5/ghost5_ws/src/ghost5_swarm/resource
touch ~/ghost5/ghost5_ws/src/ghost5_swarm/resource/ghost5_swarm

cd ~/ghost5/ghost5_ws
colcon build --packages-select ghost5_swarm --symlink-install
```

### 로직 검증 결과
```
python3 tests/unit/test_leader_election_m08.py
→ [PASS] 5/5 ALL PASS
  ✅ [조건 1] LeaderElection 상수 검증 (timeout=3.0s, quorum=3, backoff=0.1s/ID)
  ✅ [조건 3] Election Storm Backoff (Robot-5=0.0s, Robot-1=0.4s)
  ✅ [조건 4] Split-Brain 쿼럼 로직 (QUORUM_SIZE=3, MAX_RETRY=3)
  ✅ [B2] ElectionGuard 지수 백오프 (base=0.5s, max=8.0s, TTL=10s)
  ✅ [B2] election_safe_write 데코레이터 존재 확인
```

### 완료 조건 현황

| 완료 조건 | 상태 |
|---|---|
| 5대 시뮬 → Robot-5 Leader 선출 | ⬜ 하드웨어 대기 |
| Robot-5 종료 → Robot-4 3초 내 선출 | ⬜ 하드웨어 대기 |
| Election Storm 없음 확인 | ⬜ 하드웨어 대기 |
| 쿼럼 미달 승격 차단 확인 | ⬜ 하드웨어 대기 |
| [B2] 지수 백오프 로그 확인 | ⬜ 하드웨어 대기 |
| [B2] WriteBlockedError 발생/복구 | ⬜ 하드웨어 대기 |

---

## M09 — MMPF Frontier 탐색

### 개요
5대가 중복 없이 분산 탐색, 3회 실패 구역 자동 스킵.  
FrontierDetector (OccupancyGrid → Frontier 추출 + 클러스터링) +  
FrontierManager (MMPF 포텐셜 함수 + Redis 원자적 Claim Blackboard).

### 생성 파일

| 파일 경로 | 설명 |
|---|---|
| `ghost5_navigation/ghost5_navigation/frontier_detector.py` | OccupancyGrid → Frontier 추출 + 0.5m 클러스터링 |
| `ghost5_navigation/ghost5_navigation/frontier_manager.py` | MMPF + Redis Claim + skip_zones + 드론 우선 탐색 |
| `tests/unit/test_frontier_m09.py` | M09 완료 조건 검증 스크립트 |

### 핵심 설계
```
MMPF 포텐셜 함수:
  U(f) = α × (info_gain / dist) - β × Σ(1 / dist_to_robot)
  α = 1.0, β = 0.5

Claim 흐름:
  드론 우선 좌표(/swarm/frontier_priority) 있으면 최인접 Frontier 우선 선택
  skip_zones(3회 실패) 제외
  MMPF 점수 최고 Frontier 선택
  Redis SET NX 원자적 Claim (30초 TTL)
  /swarm/frontier_claims 브로드캐스트

skip_zones:
  탐색 실패 3회 이상 → skip_zone 등록 (5분 TTL)
  TTL 만료 후 자동 해제

Frontier 클러스터링:
  0.5m 반경 내 인접 Frontier 병합 → 중복 목표 방지
  클러스터 info_gain = 멤버 합산
```

### 빌드 결과
```
colcon build --packages-select ghost5_navigation --symlink-install
→ ghost5_navigation Finished ✅
```

### 로직 검증 결과
```
python3 tests/unit/test_frontier_m09.py
→ [PASS] 5/5 ALL PASS
  ✅ [조건 1] FrontierDetector 로직 (Free+Unknown → Frontier 추출)
  ✅ [조건 1] Frontier 클러스터링 (4개 → 2개 클러스터)
  ✅ [조건 1] MMPF 포텐셜 함수 (α=1.0, β=0.5, score_A=4.00 > score_B=2.00)
  ✅ [조건 2] skip_zones 로직 (MAX_FAIL=3, TTL=5분)
  ✅ [조건 1] Claim 중복 방지 (5대 동시 시도 → 1대만 성공)
```

### 완료 조건 현황

| 완료 조건 | 상태 |
|---|---|
| 5대 동시 실행 시 동일 Frontier Claim 없음 | ⬜ 하드웨어 대기 |
| 3회 실패 zone → skip_zones 등록 | ⬜ 하드웨어 대기 |
| 표준 맵 10분 내 80% 이상 커버리지 | ⬜ 하드웨어 대기 |

---

## M10 — Multi-Robot SLAM + Delta Map Merger

### 개요
5대 로컬 맵을 글로벌 맵으로 통합, Delta Update로 대역폭 10~20% 사용.  
3-레이어 병합 (2D OccupancyGrid + Elevation + LowObstacle) +  
PoseGraphPublisher (TF fallback용 pose 공유).

### 생성 파일

| 파일 경로 | 설명 |
|---|---|
| `ghost5_slam/ghost5_slam/map_merger_node.py` | 3-레이어 Delta 병합 노드 |
| `ghost5_slam/ghost5_slam/pose_graph_publisher.py` | 로봇 pose 수집 → /map_merge/pose_graph |
| `ghost5_slam/setup.py` | pose_graph_publisher entry_point 추가 |
| `tests/unit/test_map_merger_m10.py` | M10 완료 조건 검증 스크립트 |

### 핵심 설계
```
Delta Update:
  prev_maps[robot_id] vs 현재 맵 numpy 비교
  변경 셀 수 / 전체 셀 수 = Delta 비율 로그
  Delta > 20% 시 warn 출력
  변경 있을 때만 robot_maps 갱신 (불필요한 병합 방지)

Layer 1 (2D) 병합 원칙:
  TF lookup → 로컬 → 글로벌 좌표 변환
  동일 셀 복수 로봇 데이터 → Majority Vote
    occupied(>0) 다수 → 100
    free(0) 다수 → 0
    동수 → free 우선 (안전 우선)

Layer 2+3 (Elevation + LowObstacle):
  최대 비용(max) 우선 채택

[B1] TF Buffer 30s 확장:
  tf2_ros.Buffer(cache_time=Duration(seconds=30))
  드론 좌표 지연 최대 3초 후에도 TF 조회 성공
```

### 빌드 결과
```
colcon build --packages-select ghost5_slam --symlink-install
→ ghost5_slam Finished ✅
```

### 로직 검증 결과
```
python3 tests/unit/test_map_merger_m10.py
→ [PASS] 4/4 ALL PASS
  ✅ [조건 3] Delta 비율 계산 (10%/0%/100% 정확)
  ✅ [조건 2] cells_to_grid 변환 (2×2 grid free/occupied/unknown 정확)
  ✅ [조건 2] Majority Vote (2/3 occupied→occupied, 동수→free)
  ✅ PoseGraphPublisher 상수 (PUBLISH_HZ=1.0Hz)
```

### 완료 조건 현황

| 완료 조건 | 상태 |
|---|---|
| /map_merge/global_map 토픽 퍼블리시 | ⬜ 하드웨어 대기 |
| 2대 로봇 지도 글로벌 맵 통합 확인 | ⬜ 하드웨어 대기 |
| Delta Update 비율 < 20% 로그 | ⬜ 하드웨어 대기 |

---

## 전체 프로젝트 진행 현황 (2026-03-18 기준)

| Phase | 모듈 | 내용 | 코드 구현 | 빌드 | 로직 검증 | 하드웨어 검증 |
|---|---|---|---|---|---|---|
| Phase 1 | M01 | rmw_zenoh + QoS | ✅ | ✅ | ✅ | ⬜ |
| Phase 1 | M02 | 커스텀 메시지/서비스/액션 | ✅ | ✅ | ✅ | ⬜ |
| Phase 1 | M03 | Redis Blackboard + Semantic Memory | ✅ | ✅ | ✅ | ⬜ |
| Phase 1 | M04 | SROS2 보안 설정 | ✅ | ✅ | ✅ | ⬜ |
| Phase 2 | M05 | slam_toolbox 단일 로봇 SLAM | ✅ | ✅ | ✅ | ⬜ |
| Phase 2 | M06 | Nav2 + EKF + Inter-Robot Costmap | ✅ | ✅ | ✅ 2/2 | ⬜ |
| Phase 2 | M07 | 2.5D Elevation Map + IMU 보정 | ✅ | ✅ | ✅ 4/4 | ⬜ |
| Phase 3 | M08 | Bully Leader Election | ✅ | ⬜ | ✅ 5/5 | ⬜ |
| Phase 3 | M09 | MMPF Frontier 탐색 | ✅ | ✅ | ✅ 5/5 | ⬜ |
| Phase 3 | M10 | Delta Map Merger | ✅ | ✅ | ✅ 4/4 | ⬜ |
| Phase 4 | M11 | 3-센서 생존자 감지 | ⬜ | ⬜ | ⬜ | ⬜ |
| Phase 4 | M12 | Rendezvous + RSSI Gradient | ⬜ | ⬜ | ⬜ | ⬜ |
| Phase 5 | M13 | FastAPI GCS API | ⬜ | ⬜ | ⬜ | ⬜ |
| Phase 5 | M14 | Foxglove 시각화 | ⬜ | ⬜ | ⬜ | ⬜ |
| Phase 6 | M15 | Fake Drone 노드 | ⬜ | ⬜ | ⬜ | ⬜ |
| Phase 6 | M16 | 드론-Nav2 브릿지 | ⬜ | ⬜ | ⬜ | ⬜ |
| Phase 6 | M17 | 드론 Fallback 모니터 | ⬜ | ⬜ | ⬜ | ⬜ |
| Phase 7 | M18 | PX4 SITL + NED→ENU | ⬜ | ⬜ | ⬜ | ⬜ |
| Phase 7 | M19 | Hailo NPU YOLOv8n (선택) | ⬜ | ⬜ | ⬜ | ⬜ |
| Phase 7 | M20 | 5대 군집 통합 벤치마크 | ⬜ | ⬜ | ⬜ | ⬜ |

---

## 패키지별 빌드 상태

| 패키지 | 포함 모듈 | 빌드 상태 |
|---|---|---|
| `ghost5_bringup` | M05, M06 설정파일 | ✅ |
| `ghost5_slam` | M05, M07, M10 | ✅ |
| `ghost5_navigation` | M06, M09 | ✅ |
| `ghost5_swarm` | M08 | ⬜ 빌드 필요 |

### M08 빌드 명령 (미완료)
```bash
mkdir -p ~/ghost5/ghost5_ws/src/ghost5_swarm/resource
touch ~/ghost5/ghost5_ws/src/ghost5_swarm/resource/ghost5_swarm

cd ~/ghost5/ghost5_ws
colcon build --packages-select ghost5_swarm --symlink-install
```

---

## 다음 세션 작업 예정

**Phase 4 — 생존자 감지 (M11~M12)**  
M11, M12는 병렬 구현 가능.

- **M11**: 3-센서 생존자 감지 (US-016 + TCRT5000 + YOLOv8n)
  → `ghost5_victim/ghost5_victim/proximity_detector.py`
  → `ghost5_victim/ghost5_victim/vision_detector.py`
  → `ghost5_victim/ghost5_victim/victim_fuser.py`
  → `ghost5_victim/ghost5_victim/triangulation.py`

- **M12**: Rendezvous 프로토콜 + RSSI Gradient Map
  → `ghost5_swarm/ghost5_swarm/comm_monitor.py`

---

## 공통 주의사항

- `colcon build` 및 `ros2` CLI는 **venv 비활성화 상태**에서 실행
- SROS2 keystore 경로: `~/ghost5_keystore`
- Redis 비밀번호: `ghost5secure!`
- `map_merger_node`는 **Leader 로봇**에서만 실행 (M08 Leader Election 연동)
- `pose_graph_publisher`는 **전체 로봇**에서 실행
- TF 미준비 시 origin offset fallback 적용 (하드웨어 없는 환경 안전 처리)
- `UserWarning: Unbuilt egg for pytest-repeat` 은 무해한 경고 — 무시
