---
title: "GHOST-5 프로젝트 포트폴리오"
date: 2026-03-21
draft: true
tags: ["ros2", "nav2", "slam", "zenoh"]
categories: ["ros2"]
description: "**GPS-denied Hazard Operation with Swarm Team — 5 Units** **2026년 3월** (진행 중) 설계 및 계획 수립: 2026-03-15"
---

# GHOST-5 프로젝트 포트폴리오

**GPS-denied Hazard Operation with Swarm Team — 5 Units**

---

## 1. 기간

**2026년 3월** (진행 중)  
설계 및 계획 수립: 2026-03-15  
Phase 1~3 구현 완료: 2026-03-18  
Phase 4~7 구현 예정

---

## 2. 프로젝트 배경

GPS 신호가 차단되는 재난 환경(붕괴 건물, 지하 공간, 화재 현장)에서는 단일 로봇으로 광범위한 탐색과 생존자 구조 임무를 수행하기 어렵다. 기존 단일 로봇 시스템은 다음과 같은 한계를 가진다.

- **커버리지 한계**: 1대의 로봇으로 넓은 공간을 신속하게 탐색하기 불가능
- **단일 장애점(SPOF)**: 로봇 1대 고장 시 전체 임무 중단
- **통신 단절 대응 부재**: WiFi 음영 구역 진입 시 원격 제어 불가
- **GPS 의존성**: 재난 현장에서는 GPS 신호 차단 또는 불안정

이러한 문제를 해결하기 위해 **Pinky Pro 5대**가 GPS 없이 자율적으로 협력하여 재난 현장을 탐색하고 생존자를 감지하는 군집 로봇 시스템 GHOST-5를 설계·구현한다.

---

## 3. 프로젝트 목표

GPS가 차단된 재난 환경에서 5대의 로봇이 다음을 자율적으로 수행한다.

1. **실시간 협력 지도 생성** — Multi-Robot SLAM으로 환경을 공동 매핑
2. **자율 분산 탐색** — MMPF 알고리즘 기반 중복 없는 커버리지 극대화
3. **생존자 위치 감지 및 보고** — 3종 센서 교차 검증으로 오탐 최소화
4. **내결함성 보장** — 1대 이상 다운 시에도 나머지 로봇이 임무 자동 지속
5. **드론 협동 탐색** — 가상 드론 + PX4 SITL 연동으로 수직 탐색 커버리지 추가

### 성능 목표 (벤치마크 합격 기준)

| 항목 | 목표값 |
|---|---|
| Pose 통신 지연 | < 50ms (P95) |
| 지도 Delta 전송 | < 500ms (1Hz) |
| Leader Election 수렴 | < 3초 |
| 생존자 알림 전파 | < 200ms |
| 탐색 커버리지 (10분) | > 80% |
| 내결함성 (1대 다운) | 임무 계속 |
| 중복 탐색 비율 | < 5% |
| CPU 부하 (기본) | < 75% |
| CPU 부하 (NPU 적용 시) | < 65% |

---

## 4. 성과 / 기여한 점

### Phase 1 — 기반 인프라 (M01~M04) ✅

- **rmw_zenoh 미들웨어 설정** (M01): 기존 DDS 대비 CPU 50% 절감, Discovery 트래픽 99% 감소하는 Zenoh 미들웨어 QoS 프로파일 설계·구현
- **커스텀 ROS2 인터페이스 정의** (M02): `RobotState`, `VictimInfo`, `SwarmCommand`, `DroneStatus` 등 프로젝트 전용 메시지/서비스/액션 타입 25종 구현
- **Redis Blackboard + Semantic Event Memory** (M03): 5대 로봇 공유 상태 관리, Leader 교체 시 컨텍스트 자동 승계 구조 설계
- **SROS2 보안 설정** (M04): AES-GCM 암호화 + X.509 인증 기반 로봇 간 통신 보안 아키텍처 구축

### Phase 2 — 단일 로봇 자율주행 (M05~M07) ✅

- **slam_toolbox SLAM 설정** (M05): RPLiDAR C1 기반 5cm 해상도 실시간 2D 지도 생성, Loop Closure 설정, Raspberry Pi 5 성능 최적화
- **Nav2 + EKF + SlipAwareEKFTuner** (M06): 재난 환경 미끄러운 바닥 대응 슬립 감지 노드 설계. IMU–엔코더 속도 차 0.15m/s 초과 시 EKF 공분산 자동 전환(0.01→5.0)
- **[B4] InterRobotCostmapLayer** (M06): 이동 중 로봇 간 동적 충돌 방지를 위한 Nav2 Costmap 동적 장애물 등록 노드 설계. TTL 0.3s 자동 잔상 제거
- **2.5D Elevation Map + IMU 동적 보정** (M07): 단일 수평 LiDAR 스캔으로 높이 정보 추출하는 Z-stack 누적 방식 구현. BNO055 IMU pitch/roll 보정으로 Ghost Obstacle 제거. Bresenham Ray-casting으로 이동 물체 잔상 제거. **[B3]** Python dict에서 Numpy float32 배열로 교체 → 메모리 사용 ~128MB → ~9MB(상한 고정)로 대폭 절감

### Phase 3 — 군집 지능 (M08~M10) ✅

- **Bully Algorithm Leader Election** (M08): 5대 분산 환경에서 최고 ID 로봇이 3초 내 리더로 선출되는 알고리즘 설계. ID 기반 Backoff로 Election Storm 방지, Quorum(3대 합의)으로 Split-Brain 방지. **[B2]** 지수 백오프 + Jitter로 Redis HA 레이스 컨디션 방지 (총 최대 대기 ~19.5s)
- **MMPF Frontier 탐색** (M09): Multi-robot Multi-target Potential Field 알고리즘 설계. `U(f) = α × (info_gain/dist) - β × Σ(1/dist_to_robot)` 포텐셜 함수로 5대 중복 없는 분산 탐색. Redis SET NX 원자적 Claim, 3회 실패 구역 자동 스킵(5분 TTL). 드론 우선 좌표 연동 설계
- **Delta Map Merger** (M10): 5대 로컬 맵을 1Hz 주기로 글로벌 맵에 병합. Delta Update(변경 셀만 추출)로 전체 대비 10~20% 대역폭 사용 목표. Majority Vote 충돌 해소, 3-레이어(2D + Elevation + LowObstacle) 통합. **[B1]** TF Buffer 30s 확장으로 드론 좌표 지연 대응

---

## 5. 사용한 기술

### 로봇 플랫폼
| 구성 요소 | 사양 |
|---|---|
| 메인 컴퓨터 | Raspberry Pi 5 (8GB) |
| LiDAR | RPLiDAR C1 (최대 12m) |
| 카메라 | 5MP |
| 초음파 센서 | US-016 (2cm ~ 400cm) |
| IR 센서 | TCRT5000 (~30cm) |
| IMU | BNO055 (9축) |
| 구동 | 다이나믹셀 XL330 |
| NPU (선택) | Hailo AI HAT+ 26TOPS |

### 소프트웨어 스택

| 분류 | 기술 |
|---|---|
| **로봇 OS** | ROS2 Jazzy |
| **미들웨어** | rmw_zenoh (WiFi Mesh 최적화) |
| **SLAM** | slam_toolbox (async, Loop Closure) |
| **자율주행** | Nav2 (DWB Controller, NavFn Planner) |
| **상태 추정** | robot_localization EKF |
| **공유 상태** | Redis (HA Sentinel + Blackboard) |
| **보안** | SROS2 (AES-GCM, X.509) |
| **비전 AI** | YOLOv8n (인체 감지), InsightFace |
| **드론 시뮬** | PX4 SITL + Gazebo Harmonic |
| **시각화** | Foxglove Studio |
| **언어** | Python 3.12, YAML, JSON5 |
| **라이브러리** | NumPy, tf2_ros, action_msgs |

### 핵심 알고리즘

| 알고리즘 | 적용 모듈 | 역할 |
|---|---|---|
| Bully Algorithm | M08 | 분산 리더 선출 |
| MMPF (Multi-robot Multi-target Potential Field) | M09 | 중복 없는 분산 Frontier 탐색 |
| Bresenham Ray-casting | M07 | Ghost Obstacle 제거 |
| Delta Update | M10 | 대역폭 절감 지도 병합 |
| Exponential Backoff + Jitter | M08 [B2] | Redis 레이스 컨디션 방지 |
| Rolling Window (Numpy) | M07 [B3] | 메모리 상한 고정 |
| Communication Gradient Map | M12 | RSSI 기반 통신 단절 복귀 |
| Gossip Protocol | 전체 swarm | 분산 이벤트 전파 |

---

## 6. 결과 / 기대 효과

### 구현 완료 현황 (2026-03-18 기준)

| Phase | 모듈 수 | 코드 구현 | 로직 검증 | 하드웨어 검증 |
|---|---|---|---|---|
| Phase 1 (기반 인프라) | 4 | ✅ 완료 | ✅ 완료 | ⬜ 하드웨어 대기 |
| Phase 2 (단일 자율주행) | 3 | ✅ 완료 | ✅ 완료 | ⬜ 하드웨어 대기 |
| Phase 3 (군집 지능) | 3 | ✅ 완료 | ✅ 완료 | ⬜ 하드웨어 대기 |
| Phase 4 (생존자 감지) | 2 | ⬜ 예정 | ⬜ 예정 | ⬜ 예정 |
| Phase 5 (GCS + 시각화) | 2 | ⬜ 예정 | ⬜ 예정 | ⬜ 예정 |
| Phase 6 (드론 통합) | 3 | ⬜ 예정 | ⬜ 예정 | ⬜ 예정 |
| Phase 7 (최종 검증) | 3 | ⬜ 예정 | ⬜ 예정 | ⬜ 예정 |

### 기대 효과

**운영 측면**
- GPS 불가 환경에서 5대 로봇이 자율적으로 재난 현장 탐색 및 생존자 위치 보고
- 로봇 1대 고장 시에도 나머지 4대가 임무 자동 지속 (내결함성 확보)
- 단일 로봇 대비 탐색 시간 약 5배 단축 (병렬 분산 탐색)

**기술 측면**
- rmw_zenoh 도입으로 기존 DDS 대비 통신 CPU 부하 50% 절감
- Numpy Rolling Window로 Elevation Map 메모리 상한 ~9MB 고정 (기존 dict 방식 대비 최대 14배 절감)
- Delta Update 지도 병합으로 전체 대비 10~20% 대역폭 사용
- MMPF + Claim Blackboard로 중복 탐색 비율 < 5% 달성 목표
- Hailo NPU 적용 시 YOLOv8n CPU 부하 ~25% → ~3% 절감

**보안 측면**
- SROS2 기반 AES-GCM 암호화 + X.509 인증으로 로봇 간 통신 보안 확보
- 재난 현장 무선 통신 환경에서의 보안 강화

---

## 7. 팀 구성 / 맡은 책임

### 팀 구성

| 역할 | 인원 | 담당 영역 |
|---|---|---|
| **로봇 SW 엔지니어** | 1명 (본인) | 전체 소프트웨어 설계 및 구현 |

### 본인이 맡은 책임 (Solo Developer)

**설계**
- 전체 시스템 아키텍처 설계 (7개 Phase, 20개 모듈)
- 알고리즘 선택 및 파라미터 설계 (MMPF, Bully, Delta Update 등)
- 4가지 보완 사항 독립 도출 ([B1]~[B4])
- ROS2 패키지 구조 및 의존성 설계

**구현 (M01~M10 완료)**
- `ghost5_bringup` — 런치파일, YAML 설정, QoS 프로파일
- `ghost5_slam` — slam_toolbox 래퍼, Elevation Map, Delta Map Merger
- `ghost5_navigation` — Nav2 설정, SlipAwareEKF, InterRobotCostmapLayer, Frontier 탐색
- `ghost5_swarm` — Bully Leader Election, ElectionGuard

**품질 보증**
- 모듈별 단위 테스트 스크립트 작성 (10종, 총 37개 검증 항목)
- 하드웨어 없이 실행 가능한 로직 검증 체계 구축
- 트러블슈팅 및 빌드 에러 해결 (colcon build 오류 3건 해결)

**문서화**
- 세션별 작업 로그 작성 (Phase 2, Phase 3 세션 로그)
- 모듈별 작업 로그 7종 작성
- 코딩 스타일 가이드 v1.2 유지

---

## 8. 문제 해결

구현 과정에서 발생한 주요 문제와 해결 과정을 기록한다.

### 문제 1 — ament_python 패키지 빌드 오류: resource 마커 파일 누락

**발생 모듈**: M05 (ghost5_bringup, ghost5_slam)

**오류 메시지**
```
error: can't copy '.../build/ghost5_bringup/resource/ghost5_bringup':
doesn't exist or not a regular file
```

**원인 분석**  
ROS2 ament_python 패키지는 `resource/패키지명` 이라는 빈 마커 파일이 반드시 존재해야 패키지 등록이 완료된다. `setup.py`의 `data_files`에 해당 경로를 선언했지만 실제 파일이 없으면 colcon이 복사 실패로 빌드를 중단한다.

**해결**
```bash
mkdir -p ~/ghost5/ghost5_ws/src/ghost5_bringup/resource
touch ~/ghost5/ghost5_ws/src/ghost5_bringup/resource/ghost5_bringup
```
이후 모든 신규 패키지 생성 시 resource 마커 파일 생성을 표준 절차로 정착시켰다.

**교훈**  
ROS2 ament_python 패키지 생성 체크리스트에 `resource/패키지명` 마커 파일 생성을 필수 항목으로 추가했다.

---

### 문제 2 — colcon build 오류: glob('config/*')가 `__pycache__` 포함

**발생 모듈**: M05 (ghost5_bringup)

**오류 메시지**
```
error: can't copy '.../build/ghost5_bringup/config/__pycache__':
doesn't exist or not a regular file
```

**원인 분석**  
`setup.py`의 `data_files`에서 `glob('config/*')`를 사용했는데, `config/` 디렉토리에 `qos_profiles.py` 등 Python 파일이 있어 `__pycache__/` 디렉토리가 자동 생성됐다. `glob('*')`는 파일·디렉토리를 구분하지 않으므로 `__pycache__` 디렉토리도 포함해 버렸다.

**해결**  
확장자를 명시적으로 지정하는 방식으로 변경했다.
```python
# 변경 전 (문제)
glob('config/*')

# 변경 후 (해결)
glob('config/*.yaml') + glob('config/*.json5') + glob('config/*.py')
```

**교훈**  
ament_python의 `data_files`에서 `glob`을 사용할 때는 반드시 확장자를 명시해야 한다. 와일드카드 `*`는 하위 디렉토리까지 포함해 예상치 못한 빌드 오류를 유발할 수 있다.

---

### 문제 3 — colcon build 오류: 디렉토리명 오타 (`resouce` → `resource`)

**발생 모듈**: M06 (ghost5_navigation)

**오류 메시지**
```
error: can't copy '.../build/ghost5_navigation/resource/ghost5_navigation':
doesn't exist or not a regular file
```

**원인 분석**  
`resource` 디렉토리를 생성할 때 `resouce`로 오타가 발생했다. 디렉토리는 존재하지만 colcon이 찾는 경로(`resource/ghost5_navigation`)와 달라 빌드 실패.

**해결**
```bash
# 올바른 경로로 재생성
mkdir -p ~/ghost5/ghost5_ws/src/ghost5_navigation/resource
touch ~/ghost5/ghost5_ws/src/ghost5_navigation/resource/ghost5_navigation
```

**교훈**  
패키지 생성 직후 `ls src/패키지명/` 으로 디렉토리 구조를 즉시 확인하는 습관이 필요하다.

---

### 문제 4 — M05 검증 스크립트 FAIL: Zenoh 라우터 미실행 환경

**발생 모듈**: M05 (slam 검증 스크립트)

**오류 내용**
```
[WARN] Unable to connect to a Zenoh router.
[FAIL] M05 완료 조건 미달 (0/3)
```

**원인 분석**  
`test_slam_m05.py`가 실제 ROS2 노드를 생성해 `/robot_1/map` 토픽을 구독하는데, Zenoh 라우터(`rmw_zenohd`)가 실행되지 않은 상태라 통신이 불가능했다. LiDAR 하드웨어도 없으므로 slam_toolbox 자체가 실행되지 않아 `/map` 토픽 수신이 원천 불가.

**해결 방향**  
하드웨어 없는 환경에서의 검증 범위를 명확히 구분했다.
- **로직 단위 테스트**: ROS2 없이 Python 로직만 검증 (M06~M10 방식으로 표준화)
- **통합 테스트**: 하드웨어 도착 후 실제 환경에서 검증

이후 M06부터는 ROS2 의존 없이 클래스 상수·알고리즘 로직만 검증하는 방식으로 테스트 전략을 개선했다.

**교훈**  
하드웨어 없는 개발 초기 단계에서는 단위 테스트를 ROS2 의존성 없이 설계해야 CI 파이프라인과 빠른 피드백 루프를 유지할 수 있다.

---

### 문제 5 — SROS2 M04 미해결 이슈: `failed to validate namespace`

**발생 모듈**: M04 (SROS2 보안 설정)

**오류 내용**
```
ros2 security generate_artifacts 실행 시
failed to validate namespace
```

**원인 분석**  
`ros2 security generate_artifacts` 명령어에서 keystore enclave 경로 구조가 올바르지 않아 네임스페이스 검증 실패. `/ghost5/robot_N/노드명` 형식의 경로가 keystore 내부에 정확히 매핑되지 않은 것으로 추정.

**현재 상태**  
Phase 1 완료 처리 후 하드웨어 통합 테스트 시점에 재검증 예정. 현재는 `ROS_SECURITY_ENABLE=false`로 개발 진행 중.

**교훈**  
SROS2는 개발 초기보다 하드웨어 통합 직전 단계에서 적용하는 것이 효율적이다. 보안 설정을 너무 이른 시점에 강제하면 개발 속도가 크게 저하된다.

---

## 9. 회고

### 잘 된 점

**하드웨어 독립적 테스트 전략 수립**  
로봇 하드웨어가 없는 상태에서 10개 모듈을 구현하면서, M06부터는 ROS2 의존 없이 Python 로직만으로 검증하는 방식을 정착시켰다. 결과적으로 모든 단위 테스트(37개 항목)가 하드웨어 없이 통과됐고, 실제 로봇 도착 시 통합 검증만 수행하면 되는 체계를 만들었다.

**보완 사항의 선제적 도출 ([B1]~[B4])**  
초기 설계 단계에서 발생 가능한 문제를 미리 분석하고 4가지 보완 사항을 설계에 반영했다.
- [B1] PX4-ROS2 시각 드리프트 → TF Buffer 30s 확장 + ROS2 시계 강제 대체
- [B2] Redis HA 레이스 컨디션 → 지수 백오프 + Jitter
- [B3] Elevation Map 메모리 증가 → Numpy 배열 + Rolling Window
- [B4] 이동 중 로봇 간 충돌 → InterRobotCostmapLayer

이 과정에서 단순 기능 구현을 넘어 운영 환경에서 발생할 수 있는 엣지 케이스를 사전에 차단하는 방어적 설계 능력을 키웠다.

**세션 로그 기반 지식 연속성 유지**  
매 세션마다 작업 로그를 작성해 다음 세션에서 컨텍스트를 빠르게 복구할 수 있었다. 특히 `colcon build` 오류 해결 과정을 기록해 이후 신규 패키지 생성 시 동일 오류를 반복하지 않았다.

---

### 아쉬운 점

**M04 SROS2 미완 상태로 Phase 진행**  
`failed to validate namespace` 오류를 해결하지 못한 채 Phase 2~3을 진행했다. 보안 레이어가 비활성화된 상태로 개발하다 보면 하드웨어 통합 시점에 SROS2를 뒤늦게 적용할 때 예상치 못한 문제가 발생할 수 있다. 다음 세션에서 M04 이슈를 먼저 재검토하는 것이 바람직하다.

**M08 ghost5_swarm 빌드 미완료**  
M09, M10은 빌드까지 완료됐지만 M08(`ghost5_swarm`)은 로직 검증만 통과하고 빌드를 진행하지 못했다. Phase 4 진입 전 `ghost5_swarm` 빌드를 완료해야 한다.

**pose_graph_publisher.py 계획 문서에 구현 코드 없음**  
`GHOST5_plan_v2.md`에 `pose_graph_publisher.py`가 파일명으로만 언급되고 구현 코드가 없었다. 설계 의도를 추론해 직접 구현했지만, 계획 문서와 구현 간의 gap이 발생했다. 향후 계획 문서 작성 시 모든 파일에 최소한의 인터페이스 스펙을 포함해야 한다.

---

### 다음에 개선할 점

1. **Phase 4 진입 전 M08 빌드 + M04 SROS2 재검토** 필수 수행
2. **단위 테스트 자동화**: 현재 수동 실행 중인 테스트 스크립트를 `pytest tests/unit/` 한 번으로 전체 실행 가능하도록 `conftest.py` 구성
3. **계획 문서 정합성 유지**: 신규 파일 추가 시 계획 문서(`GHOST5_plan_v2.md`)에도 최소 인터페이스 스펙 동기화

---

*이 문서는 진행 중인 프로젝트의 포트폴리오 초안으로, Phase 4~7 완료 후 성과 항목이 업데이트될 예정입니다.*
