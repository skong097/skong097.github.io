---
title: "ROSForge — 통합 리서치 문서"
date: 2026-03-21
draft: true
tags: ["ros2", "slam", "gazebo"]
categories: ["ros2"]
description: "**프로젝트명**: ROSForge — ROS2 Unified Development & Monitoring Platform **작성일**: 2026-03-18 **버전**: v2.0"
---

# ROSForge — 통합 리서치 문서

**프로젝트명**: ROSForge — ROS2 Unified Development & Monitoring Platform  
**작성일**: 2026-03-18  
**버전**: v2.0  
**작성자**: gjkong  
**참조 교재**:
- `ros2_basic-main` — ROS2 기초 패키지
- `for_ROS2_study-main` — R2R 실전편 전체
- PinkLAB Edu — 터미널 bashrc 그리고 리눅스 익숙해지기 (2026-02-13)

---

## 목차

1. [프로젝트 배경 및 문제 정의](#1-프로젝트-배경-및-문제-정의)
2. [기존 도구 현황 조사](#2-기존-도구-현황-조사)
2-B. [ROS2 핵심 개념별 기술 조사 (모니터링 대상 전체)](#2-b-ros2-핵심-개념별-기술-조사)
3. [교재 커리큘럼 분석](#3-교재-커리큘럼-분석)
4. [전체 기능 요구사항](#4-전체-기능-요구사항)
5. [M00 — 초기 환경 설정](#5-m00--초기-환경-설정)
6. [M00 GUI 상세 설계 — 환경 설정 화면](#6-m00-gui-상세-설계--환경-설정-화면)
7. [제안 아키텍처](#7-제안-아키텍처)
8. [기술 스택](#8-기술-스택)
9. [프로젝트 디렉토리 구조](#9-프로젝트-디렉토리-구조)
10. [전체 마일스톤 계획](#10-전체-마일스톤-계획)
11. [리스크 및 고려사항](#11-리스크-및-고려사항)

---

## 1. 프로젝트 배경 및 문제 정의

### 1.1 현재 ROS2 개발 워크플로의 고통 지점

ROS2 기반 개발 시 개발자가 겪는 주요 불편 사항:

| 카테고리 | 현재 방식 | 문제점 |
|----------|-----------|--------|
| **환경 설정** | `.bashrc` 수동 편집, `source` 명령 반복 | 실수 잦음, 터미널마다 재소싱 필요 |
| **빌드** | `colcon build` + `source install/setup.bash` | 매 수정마다 터미널 반복, venv 충돌 |
| **실행** | `ros2 run`, `ros2 launch` 개별 실행 | 여러 터미널, 실행 순서 관리 어려움 |
| **모니터링** | `ros2 topic echo`, `rqt`, `rviz2` 별도 실행 | 도구 분산, 화면 복잡 |
| **파라미터** | `ros2 param set/get` CLI | 실시간 반영 어려움, 결과 즉시 확인 불가 |
| **인터페이스 확인** | `ros2 interface show` | 가독성 낮음 |
| **노드 그래프** | `rqt_graph` 별도 실행 | 실시간 토폴로지 변화 추적 어려움 |
| **로그** | 터미널 출력 | 레벨별 필터링/검색 불편 |
| **시각화** | rviz2, gazebo 별도 실행 | 별도 설정 필요, 레이아웃 저장 불편 |

### 1.2 목표

**단 하나의 통합 도구**에서 ROS2 개발의 전체 라이프사이클을 처리:

- `.bashrc` 환경 설정 GUI (플랫폼 선택 → alias 자동 생성 → 버튼 클릭으로 적용)
- 빌드 자동화 (watch mode 포함, venv 자동 비활성화)
- 노드/액션/서비스 실행 및 관리
- 실시간 토픽/파라미터 모니터링 및 수정
- 3D 시각화 (SLAM 맵, 포인트 클라우드, TF)
- 인터페이스(msg/srv/action) 브라우저
- 로그 통합 뷰어
- Gazebo / rviz2 연동

---

## 2. 기존 도구 현황 조사

### 2.1 시각화 도구 비교

| 도구 | 특징 | 강점 | 한계 |
|------|------|------|------|
| **RViz2** | ROS2 공식 3D 시각화 | URDF, TF, 포인트 클라우드 지원 | 독립 실행, 원격 불가, 고주파 성능 저하 |
| **Foxglove Studio** | Web + 데스크톱, 20+ 패널 | foxglove_bridge 고성능, bag 재생, 레이아웃 저장 | 빌드/실행 관리 없음, 파라미터 수정 제한, 클라우드 유료 |
| **Rerun** | 경량 네이티브, 고성능 렌더링 | 빠른 렌더링, Python/C++ SDK | bag 직접 열기 불가, 브릿지 별도 필요 |
| **rqt** | ROS2 공식 플러그인 GUI | rqt_graph/plot/console/param 통합 | UI 구식, 플러그인 간 통합 부족 |

### 2.2 브릿지/통신 레이어 비교

| 브릿지 | 프로토콜 | 성능 | 특징 |
|--------|----------|------|------|
| **foxglove_bridge** | Foxglove WebSocket | ⭐⭐⭐⭐⭐ | C++ 구현, 고성능, 파라미터/그래프 지원 |
| **rosbridge_suite** | JSON/WebSocket | ⭐⭐⭐ | Python 구현, 범용, 성능 한계 |
| **rclpy 직접** | DDS/rmw | ⭐⭐⭐⭐⭐ | 네이티브 성능, Python 직접 제어 |

### 2.3 기존 통합 IDE 시도

| 도구 | 상태 | 평가 |
|------|------|------|
| **Rovium IDE** | Beta (2025) | colcon 빌드/실행 지원, 디버그 미구현 |
| **CLion + ROS2** | 지원 | compile_commands.json 기반, 외부 도구 통합 |
| **VS Code + ros2-devcontainer** | 활성 | 컨테이너 기반, C++/Python 디버그 지원 |
| **PyCharm + ROS2** | 지원 | Python 노드 attach 디버그 가능 |

### 2.4 경쟁 분석 요약

| 기능 | ROSForge (제안) | Foxglove | rqt | RViz2 |
|------|:-:|:-:|:-:|:-:|
| 환경 설정 GUI (.bashrc) | ✅ | ❌ | ❌ | ❌ |
| 빌드 자동화 | ✅ | ❌ | ❌ | ❌ |
| 노드 실행 관리 | ✅ | ❌ | ❌ | ❌ |
| **노드 상세 인트로스펙션** | ✅ | 부분 | ✅ | ❌ |
| **QoS 프로파일 조회/시각화** | ✅ | ❌ | ❌ | ❌ |
| **토픽 주파수/대역폭 실시간** | ✅ | ✅ | ✅ | ❌ |
| 실시간 토픽 뷰어 | ✅ | ✅ | ✅ | ❌ |
| 파라미터 GUI 수정 | ✅ | 제한적 | ✅ | ❌ |
| **라이프사이클 노드 상태 제어** | ✅ | 부분 | ❌ | ❌ |
| **발행자/구독자 엔드포인트 정보** | ✅ | ❌ | ❌ | ❌ |
| 3D 시각화 | ✅ | ✅ | ❌ | ✅ |
| 실시간 플롯 | ✅ | ✅ | ✅ | ❌ |
| 로그 뷰어 | ✅ | ✅ | ✅ | ❌ |
| 인터페이스 브라우저 | ✅ | ❌ | ❌ | ❌ |
| Watch Mode 빌드 | ✅ | ❌ | ❌ | ❌ |
| bag 파일 재생 | ✅ | ✅ | ❌ | 제한적 |
| **통합 단일 도구** | ✅ | 시각화만 | 분산 | 3D만 |

**결론**: 빌드-실행-모니터링-시각화-파라미터 수정을 하나로 통합한 도구는 **현재 존재하지 않음**.

---

## 2-B. ROS2 핵심 개념별 기술 조사 (모니터링/수정/시각화 대상)

> ROSForge가 실시간 모니터링·수정·시각화해야 하는 모든 ROS2 요소를 빠짐없이 정의하고, 각각의 rclpy API와 구현 방법을 조사한다.

### 2-B.1 노드 (Node) 인트로스펙션

#### 조회 가능한 정보 전체 목록

`ros2 node info /<node_name>` 으로 얻을 수 있는 6가지 카테고리:

```
/node_name
  Subscribers:          # 이 노드가 구독하는 토픽 + 타입
  Publishers:           # 이 노드가 발행하는 토픽 + 타입
  Service Servers:      # 이 노드가 제공하는 서비스 + 타입
  Service Clients:      # 이 노드가 호출하는 서비스 + 타입
  Action Servers:       # 이 노드가 제공하는 액션 + 타입
  Action Clients:       # 이 노드가 호출하는 액션 + 타입
```

> ⚠️ **현재 research.md 누락**: 노드의 Service Clients, Action Clients 조회가 요구사항에 없음

#### rclpy API

```python
# 노드 목록
node.get_node_names_and_namespaces()
# → [('turtlesim', '/'), ('my_publisher', '/')]

# 특정 노드의 구독자 목록
node.get_subscriber_names_and_types_by_node(node_name, node_namespace)

# 특정 노드의 발행자 목록
node.get_publisher_names_and_types_by_node(node_name, node_namespace)

# 특정 노드의 서비스 서버 목록
node.get_service_names_and_types_by_node(node_name, node_namespace)

# 특정 노드의 서비스 클라이언트 목록 (rclpy 최신)
node.get_client_names_and_types_by_node(node_name, node_namespace)

# 특정 노드의 액션 서버 목록
from rclpy.action import get_action_server_names_and_types_by_node
get_action_server_names_and_types_by_node(node, node_name, node_namespace)

# 특정 노드의 액션 클라이언트 목록
from rclpy.action import get_action_client_names_and_types_by_node
get_action_client_names_and_types_by_node(node, node_name, node_namespace)
```

#### ROSForge Node Panel 요구사항

```
노드 카드 클릭 시 표시할 정보:
┌─────────────────────────────────────────┐
│  📦 /dist_turtle_action_server           │
│  패키지: my_first_package                │
│  PID: 12345  |  CPU: 2.1%  |  MEM: 45MB │
│                                         │
│  📤 Publishers (1)                       │
│    /turtle1/cmd_vel  geometry_msgs/Twist │
│                                         │
│  📥 Subscribers (1)                      │
│    /turtle1/pose     turtlesim/Pose      │
│                                         │
│  🔧 Service Servers (6)                  │
│    /dist_turtle_action_server/set_params │
│    /dist_turtle_action_server/get_params │
│    ... (파라미터 기본 서비스)             │
│                                         │
│  🎯 Action Servers (1)                   │
│    /dist_turtle  my_first_package_msgs/  │
│                  action/DistTurtle       │
│                                         │
│  [노드 종료]  [재시작]  [로그 보기]       │
└─────────────────────────────────────────┘
```

### 2-B.2 토픽 (Topic) 상세 모니터링

#### 조회 가능한 정보 전체 목록

```bash
# 기본 목록
ros2 topic list -t
# → /turtle1/cmd_vel  [geometry_msgs/msg/Twist]

# 상세 정보 (발행자/구독자 엔드포인트 + QoS)
ros2 topic info /turtle1/cmd_vel --verbose
# →  Type: geometry_msgs/msg/Twist
#    Publisher count: 1
#      Node name: teleop_turtle  /  Endpoint: PUBLISHER
#      QoS: Reliability=RELIABLE, Durability=VOLATILE, History=KEEP_LAST(7)
#    Subscription count: 2
#      Node name: turtlesim  /  Endpoint: SUBSCRIPTION
#      QoS: ...

# 발행 주파수
ros2 topic hz /turtle1/pose
# → average rate: 62.500  min: 0.016s  max: 0.016s

# 대역폭
ros2 topic bw /turtle1/pose
# → 1.51 KB/s  mean: 0.02KB  min: 0.02KB  max: 0.02KB

# 메시지 내용
ros2 topic echo /turtle1/pose
```

#### rclpy API

```python
# 전체 토픽 목록 + 타입
node.get_topic_names_and_types()

# 토픽별 발행자 엔드포인트 정보 (QoS 포함)
node.get_publishers_info_by_topic('/turtle1/cmd_vel')
# → [TopicEndpointInfo(
#      node_name='teleop_turtle',
#      node_namespace='/',
#      topic_type='geometry_msgs/msg/Twist',
#      endpoint_type=TopicEndpointTypeEnum.PUBLISHER,
#      qos_profile=QoSProfile(reliability=RELIABLE, ...)
#   )]

# 토픽별 구독자 엔드포인트 정보 (QoS 포함)
node.get_subscriptions_info_by_topic('/turtle1/cmd_vel')

# 발행자 수
node.count_publishers('/turtle1/cmd_vel')

# 구독자 수
node.count_subscribers('/turtle1/cmd_vel')
```

#### ROSForge Topic Panel 요구사항 (신규/보완)

```
토픽 목록 행 클릭 시 표시할 상세:
┌─────────────────────────────────────────────┐
│  📡 /turtle1/cmd_vel                         │
│  타입: geometry_msgs/msg/Twist               │
│  주파수: 2.0 Hz  |  대역폭: 0.08 KB/s        │
│                                             │
│  발행자 (1)                                  │
│    teleop_turtle [/]                         │
│    QoS: RELIABLE | VOLATILE | KEEP_LAST(10) │
│                                             │
│  구독자 (2)                                  │
│    turtlesim [/]                             │
│    QoS: RELIABLE | VOLATILE | KEEP_LAST(10) │
│    _ros2cli_xxx [/]                          │
│    QoS: BEST_EFFORT | VOLATILE | KEEP_LAST  │
│                                             │
│  ⚠️  QoS 호환성 경고: RELIABLE ↔ BEST_EFFORT │
│  [메시지 보기]  [플롯]  [발행]  [녹화]        │
└─────────────────────────────────────────────┘
```

> ⚠️ **현재 research.md 누락**:
> - 토픽 주파수(Hz) 실시간 표시
> - 토픽 대역폭(KB/s) 실시간 표시
> - 발행자/구독자 엔드포인트 상세 (노드명, QoS 프로파일)
> - QoS 호환성 불일치 경고

### 2-B.3 QoS (Quality of Service) 프로파일

#### QoS 7가지 정책

| 정책 | 옵션 | 설명 |
|------|------|------|
| **History** | KEEP_LAST(N) / KEEP_ALL | 메시지 큐 보관 방식 |
| **Depth** | 정수 (queue size) | History=KEEP_LAST일 때 큐 크기 |
| **Reliability** | RELIABLE / BEST_EFFORT | 재전송 보장 여부 |
| **Durability** | VOLATILE / TRANSIENT_LOCAL | 늦게 참여한 구독자에게 이전 메시지 제공 |
| **Deadline** | Duration | 최대 허용 발행 간격 |
| **Liveliness** | AUTOMATIC / MANUAL_BY_TOPIC | 발행자 생존 확인 방식 |
| **Liveliness Lease Duration** | Duration | Liveliness 타임아웃 |

#### ROSForge QoS Panel 요구사항 (신규)

```
QoS 호환성 매트릭스 표시:
발행자 RELIABLE + 구독자 BEST_EFFORT → ✅ 호환 (다운그레이드)
발행자 BEST_EFFORT + 구독자 RELIABLE → ❌ 비호환 (연결 안 됨)

발행자 VOLATILE + 구독자 TRANSIENT_LOCAL → ❌ 비호환
발행자 TRANSIENT_LOCAL + 구독자 VOLATILE → ✅ 호환
```

### 2-B.4 서비스 (Service) 상세 모니터링

#### 조회 가능한 정보

```bash
ros2 service list -t          # 서비스 목록 + 타입
ros2 service type /srv_name   # 서비스 타입
ros2 service find <type>      # 타입으로 서비스 검색
ros2 service call /srv_name <type> <args>  # 서비스 호출
```

#### rclpy API

```python
# 전체 서비스 목록 + 타입
node.get_service_names_and_types()

# 서비스 서버 존재 여부 확인
node.service_is_ready('/multi_spawn')

# 서비스 타입 동적 import
import importlib
module = importlib.import_module('my_first_package_msgs.srv')
SrvType = getattr(module, 'MultiSpawn')

# 서비스 호출
client = node.create_client(SrvType, '/multi_spawn')
req = SrvType.Request()
req.num = 5
future = client.call_async(req)
```

#### ROSForge Service Panel 요구사항 (보완)

```
서비스 호출 UI:
┌─────────────────────────────────────────┐
│  🔧 /multi_spawn                         │
│  타입: my_first_package_msgs/srv/MultiSpawn │
│                                         │
│  Request                                │
│  ─────────────────────────────────────  │
│  num (int64):  [ 5 ]                    │
│                                         │
│  [호출]   응답 시간: 12ms               │
│                                         │
│  Response                               │
│  ─────────────────────────────────────  │
│  x:     [1.23, 3.45, 5.67]              │
│  y:     [2.34, 4.56, 6.78]              │
│  theta: [0.00, 1.05, 2.09]              │
│                                         │
│  호출 히스토리:                           │
│  14:23:01  num=5  → 성공 (12ms)         │
│  14:22:45  num=3  → 성공 (8ms)          │
└─────────────────────────────────────────┘
```

> ⚠️ **현재 research.md 누락**: 서비스 호출 응답 시간, 호출 히스토리 로깅

### 2-B.5 액션 (Action) 상세 모니터링

#### 액션 내부 구조 (ROS2)

액션은 내부적으로 3개의 서비스 + 2개의 토픽으로 구성된다:

```
/dist_turtle/_action/send_goal         → 서비스 (Goal 전송)
/dist_turtle/_action/cancel_goal       → 서비스 (취소)
/dist_turtle/_action/get_result        → 서비스 (결과 조회)
/dist_turtle/_action/feedback          → 토픽 (Feedback 스트림)
/dist_turtle/_action/status            → 토픽 (Goal 상태 목록)
```

#### Goal 상태 머신

```
UNKNOWN → ACCEPTED → EXECUTING → SUCCEEDED
                   ↘ CANCELING → CANCELED
                   ↘ ABORTED
```

#### rclpy API

```python
from rclpy.action import ActionClient, ActionServer, get_action_names_and_types

# 액션 목록 전체
get_action_names_and_types(node)

# 액션 클라이언트
ac = ActionClient(node, DistTurtle, '/dist_turtle')
goal_handle = await ac.send_goal_async(goal_msg)

# Feedback 콜백
def feedback_cb(feedback):
    print(feedback.feedback.remained_dist)

# Result 대기
result = await goal_handle.get_result_async()

# Cancel
await goal_handle.cancel_goal_async()
```

#### ROSForge Action Panel 요구사항 (보완)

```
액션 실행 UI:
┌─────────────────────────────────────────┐
│  🎯 /dist_turtle                         │
│  타입: my_first_package_msgs/DistTurtle  │
│  서버 상태: ✅ 활성                       │
│                                         │
│  Goal 전송                               │
│  linear_x (float32):   [ 2.0 ]          │
│  angular_z (float32):  [ 1.5 ]          │
│  dist      (float32):  [ 3.0 ]          │
│  [전송]  [취소]                          │
│                                         │
│  실행 중 — Goal ID: abc-123              │
│  상태: EXECUTING ██████░░░░ 60%         │
│  Feedback: remained_dist = 1.23m        │
│                                         │
│  실시간 플롯:  remained_dist vs time    │
│  ████████████████░░░░                  │
│                                         │
│  Result                                 │
│  pos_x: 5.54  pos_y: 3.21              │
│  pos_theta: 1.57  result_dist: 3.00    │
│                                         │
│  Goal 히스토리:                          │
│  14:23:01  dist=3.0 → SUCCEEDED         │
│  14:21:30  dist=5.0 → CANCELED          │
└─────────────────────────────────────────┘
```

> ⚠️ **현재 research.md 누락**:
> - 액션 내부 상태 머신 시각화 (ACCEPTED→EXECUTING→SUCCEEDED)
> - Goal 히스토리 로깅
> - Feedback 실시간 플롯 (time-series)
> - 서버 활성/비활성 상태 표시

### 2-B.6 파라미터 (Parameter) 상세 모니터링

#### 파라미터 타입 전체

```python
ParameterType.PARAMETER_NOT_SET     = 0
ParameterType.PARAMETER_BOOL        = 1
ParameterType.PARAMETER_INTEGER     = 2
ParameterType.PARAMETER_DOUBLE      = 3
ParameterType.PARAMETER_STRING      = 4
ParameterType.PARAMETER_BYTE_ARRAY  = 5
ParameterType.PARAMETER_BOOL_ARRAY  = 6
ParameterType.PARAMETER_INTEGER_ARRAY = 7
ParameterType.PARAMETER_DOUBLE_ARRAY  = 8
ParameterType.PARAMETER_STRING_ARRAY  = 9
```

#### 파라미터 서비스 6개 (모든 노드 기본 제공)

```
/<node>/describe_parameters        → 파라미터 설명/타입/범위 조회
/<node>/get_parameter_types        → 파라미터 타입 조회
/<node>/get_parameters             → 파라미터 값 조회
/<node>/list_parameters            → 파라미터 목록 조회
/<node>/set_parameters             → 파라미터 개별 설정
/<node>/set_parameters_atomically  → 파라미터 원자적 일괄 설정
```

#### rclpy API

```python
from rcl_interfaces.srv import (
    DescribeParameters, GetParameterTypes, GetParameters,
    ListParameters, SetParameters, SetParametersAtomically
)
from rcl_interfaces.msg import ParameterEvent

# 파라미터 이벤트 구독 (모든 노드의 변경 감지)
sub = node.create_subscription(
    ParameterEvent, '/parameter_events', callback, 10)

# 파라미터 설명 조회 (범위, 설명, 추가 제약)
client = node.create_client(DescribeParameters, '/dist_turtle_action_server/describe_parameters')
```

#### ROSForge Parameter Panel 요구사항 (보완)

```
파라미터 편집 UI:
┌─────────────────────────────────────────────┐
│  🔩 /dist_turtle_action_server               │
│                                             │
│  파라미터 (4)           [YAML 저장] [로드]   │
│  ─────────────────────────────────────────  │
│  quatile_time      [DOUBLE]                 │
│    현재: 0.75   ─────●──────  [0.0 ~ 1.0]  │
│    설명: 목표 거리의 분위수 시점             │
│                                             │
│  almost_goal_time  [DOUBLE]                 │
│    현재: 0.95   ──────────●  [0.0 ~ 1.0]  │
│                                             │
│  angular_P  [DOUBLE]  현재: 1.0  [ 1.0  ]  │
│  angular_I  [DOUBLE]  현재: 0.0  [ 0.0  ]  │
│  angular_D  [DOUBLE]  현재: 0.0  [ 0.0  ]  │
│  ...                                        │
│                                             │
│  변경 히스토리:                              │
│  14:23:01  angular_P: 1.0 → 2.0  ✅ 적용   │
│  14:22:45  quatile_time: 0.75 → 0.8  ✅    │
│                                             │
│  ⚡ /parameter_events 실시간 감지 중         │
└─────────────────────────────────────────────┘
```

> ⚠️ **현재 research.md 누락**:
> - `describe_parameters`를 통한 파라미터 설명/범위 표시
> - `BYTE_ARRAY`, `BOOL_ARRAY`, `INTEGER_ARRAY`, `DOUBLE_ARRAY`, `STRING_ARRAY` 배열 타입 처리
> - `/parameter_events` 토픽 구독으로 전체 노드 파라미터 변경 실시간 감지
> - 파라미터 원자적 일괄 변경 (`set_parameters_atomically`)
> - 파라미터 변경 히스토리 로깅

### 2-B.7 라이프사이클 노드 (Lifecycle / Managed Node)

#### 상태 머신 (7개 상태, 7개 트랜지션)

```
상태:                     트랜지션:
UNCONFIGURED  ──configure──→  INACTIVE
INACTIVE      ──activate──→   ACTIVE
ACTIVE        ──deactivate──→ INACTIVE
INACTIVE      ──cleanup──→   UNCONFIGURED
ACTIVE/INACTIVE/UNCONFIGURED ──shutdown──→ FINALIZED
(에러 발생 시) ──→ ERROR_PROCESSING ──→ UNCONFIGURED or FINALIZED
```

#### 라이프사이클 관련 서비스/토픽

```
/<node>/get_state              → 현재 상태 조회
/<node>/change_state           → 상태 전환 요청
/<node>/get_available_states   → 가능한 상태 목록
/<node>/get_available_transitions → 가능한 트랜지션 목록
/<node>/transition_event       → 상태 전환 이벤트 토픽 (latched)
```

#### rclpy API

```python
from lifecycle_msgs.srv import GetState, ChangeState
from lifecycle_msgs.msg import Transition, State

# 현재 상태 조회
client = node.create_client(GetState, '/lifecycle_node/get_state')
response = await client.call_async(GetState.Request())
# response.current_state.id, response.current_state.label

# 상태 전환
change_client = node.create_client(ChangeState, '/lifecycle_node/change_state')
req = ChangeState.Request()
req.transition.id = Transition.TRANSITION_CONFIGURE  # 1
await change_client.call_async(req)
```

#### ROSForge Lifecycle Panel 요구사항 (신규 — 현재 research.md에 완전 누락)

```
라이프사이클 노드 UI:
┌──────────────────────────────────────────┐
│  🔄 /nav2_controller (LifecycleNode)      │
│                                          │
│  현재 상태: ██ ACTIVE (녹색)              │
│                                          │
│  상태 다이어그램:                          │
│  [UNCONFIGURED] ──→ [INACTIVE] ──→ [ACTIVE]│
│       ↑_____________↑__________↑         │
│                 (shutdown)                │
│                                          │
│  제어 버튼:                               │
│  [configure] [activate] [deactivate]     │
│  [cleanup]   [shutdown]                  │
│                                          │
│  트랜지션 이벤트 로그:                     │
│  14:23:01  INACTIVE → configure → ACTIVE │
│  14:21:30  UNCONFIGURED → configure → INACTIVE │
└──────────────────────────────────────────┘
```

### 2-B.8 TF (Transform) 트리

#### TF 관련 주요 토픽/API

```bash
ros2 topic echo /tf           # TF 프레임 변환 스트림
ros2 topic echo /tf_static    # 정적 TF (한 번만 발행)
ros2 run tf2_tools view_frames  # TF 트리 PDF 저장
ros2 run tf2_ros tf2_echo <parent> <child>  # 두 프레임 간 변환
```

```python
import tf2_ros

# TF 버퍼 + 리스너
tf_buffer = tf2_ros.Buffer()
listener = tf2_ros.TransformListener(tf_buffer, node)

# 특정 프레임 변환 조회
transform = tf_buffer.lookup_transform(
    'world', 'moving_frame',
    rclpy.time.Time()
)
# transform.transform.translation.x/y/z
# transform.transform.rotation.x/y/z/w

# 모든 프레임 목록
all_frames = tf_buffer.all_frames_as_string()
```

#### ROSForge TF Panel 요구사항 (보완)

```
TF 트리 시각화:
- D3.js force-directed 또는 tree 레이아웃
- 각 엣지에 변환 행렬(translation + rotation) 표시
- 오래된 TF (> 0.1s) 빨간색 경고
- /tf + /tf_static 모두 구독
- 프레임 클릭 시 해당 변환값 상세 표시
- 두 프레임 선택 → 상대 변환 계산 표시
```

> ⚠️ **현재 research.md 누락**: `/tf_static` 구독, 두 프레임 간 상대 변환 계산

### 2-B.9 로그 (Logging) 시스템

#### ROS2 로그 레벨 및 수집 방법

```python
# 로그 레벨 (5단계)
RCUTILS_LOG_SEVERITY_DEBUG    = 10
RCUTILS_LOG_SEVERITY_INFO     = 20
RCUTILS_LOG_SEVERITY_WARN     = 30
RCUTILS_LOG_SEVERITY_ERROR    = 40
RCUTILS_LOG_SEVERITY_FATAL    = 50

# /rosout 토픽 구독 (모든 노드의 로그 통합)
from rcl_interfaces.msg import Log
sub = node.create_subscription(Log, '/rosout', callback, 1000)

# Log 메시지 필드:
# - stamp (시간)
# - level (레벨)
# - name (노드명)
# - msg (메시지)
# - file (소스 파일)
# - function (함수명)
# - line (라인 번호)
```

#### 로거 레벨 동적 변경 (Jazzy 신기능)

```python
# enable_logger_service=True 로 노드 생성 시
# 외부에서 로그 레벨 변경 가능
# /<node>/get_logger_levels 서비스
# /<node>/set_logger_levels 서비스
```

#### ROSForge Log Panel 요구사항 (보완)

```
로그 뷰어 UI:
┌─────────────────────────────────────────────────────┐
│  📋 통합 로그                [필터] [저장] [지우기]   │
│  레벨: [ALL ▼]  노드: [ALL ▼]  키워드: [      ]     │
│                                                     │
│  14:23:01.123  [INFO]  /turtlesim          turtle1  │
│                        turtlesim_node.cpp:45        │
│  14:23:00.987  [WARN]  /dist_turtle_server          │
│                        Heading error: 0.15          │
│  14:22:59.001  [ERROR] /my_publisher                │
│                        Failed to connect            │
│                                                     │
│  [로그 레벨 변경]  /dist_turtle_server: [WARN → DEBUG]│
└─────────────────────────────────────────────────────┘
```

> ⚠️ **현재 research.md 누락**:
> - Log 메시지의 `file`, `function`, `line` 필드 표시 (디버깅에 필수)
> - 로거 레벨 동적 변경 UI (`set_logger_levels` 서비스)
> - 로그 파일 저장 (.log, .csv)

### 2-B.10 rosbag2 — 데이터 녹화 및 재생

#### rosbag2 핵심 기능

```bash
# 녹화 (모든 토픽)
ros2 bag record -a -o my_bag

# 특정 토픽만 녹화
ros2 bag record /turtle1/pose /turtle1/cmd_vel -o my_bag

# 정보 조회
ros2 bag info my_bag.mcap

# 재생
ros2 bag play my_bag.mcap

# 재생 속도 조절
ros2 bag play my_bag.mcap --rate 2.0

# 특정 토픽만 재생
ros2 bag play my_bag.mcap --topics /turtle1/pose
```

#### Python API (rosbags 라이브러리 — non-ROS)

```python
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

typestore = get_typestore(Stores.ROS2_HUMBLE)
with Reader('/path/to/bag') as reader:
    for connection, timestamp, rawdata in reader.messages():
        if connection.topic == '/turtle1/pose':
            msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
            print(msg.x, msg.y)
```

#### ROSForge Bag Panel 요구사항 (신규 — 현재 완전 누락)

```
bag 녹화/재생 UI:
┌─────────────────────────────────────────────┐
│  🎬 Bag Recorder/Player                      │
│                                             │
│  ── 녹화 ──────────────────────────────     │
│  토픽 선택: [✅ 전체]  [선택 토픽...]         │
│  저장 경로: [~/bags/session_20260318  ][찾기]│
│  형식: [MCAP ▼]                             │
│  [● 녹화 시작]  녹화 중: 00:01:23  45MB     │
│                                             │
│  ── 재생 ──────────────────────────────     │
│  파일: [~/bags/session_20260318.mcap  ][열기]│
│  속도: [1.0x ▼]   반복: [OFF]              │
│  타임라인:  ──────●───────────── 01:23/02:45 │
│  [◀◀ 처음][◀ 5s][▶ 재생][▶ 5s][▶▶ 끝]     │
│                                             │
│  포함 토픽 (3):                              │
│  ✅ /turtle1/pose      62Hz   1.2MB        │
│  ✅ /turtle1/cmd_vel    2Hz   0.1MB        │
│  ✅ /error             10Hz   0.3MB        │
└─────────────────────────────────────────────┘
```

### 2-B.11 노드 그래프 토폴로지

#### ros2cli API

```bash
ros2 node list                    # 노드 목록
ros2 node info /node_name         # 노드 상세 (pub/sub/svc/action)
ros2 topic list -t                # 토픽 + 타입
ros2 service list -t              # 서비스 + 타입

# rqt_graph 대체 데이터 수집 방법:
# 1. 모든 노드 순회하며 get_publisher_names_and_types_by_node()
# 2. 모든 토픽의 get_publishers_info_by_topic() 으로 연결 매핑
```

#### ROSForge Graph Panel 요구사항 (보완)

```
노드 그래프 UI:
- D3.js force-directed graph
- 노드: 원형 (실행 중=녹색, 라이프사이클 비활성=노란색, 오류=빨간색)
- 엣지: 토픽(실선), 서비스(점선), 액션(두꺼운선)
- 엣지 색상: 타입별 구분
- 노드 클릭: 상세 정보 사이드 패널
- 토픽 엣지 클릭: 토픽 메시지 뷰어 열기
- 숨김 노드 필터 (/_ros2cli_xxx 등 내부 노드)
- 실시간 자동 업데이트 (1초 주기)
```

> ⚠️ **현재 research.md 누락**: 노드 상태별 색상 구분, 라이프사이클 상태 연동, 토픽/서비스/액션 엣지 타입 구분

### 2-B.12 인터페이스 (Interface) 브라우저

#### ros2 interface 명령 전체

```bash
ros2 interface list              # 전체 인터페이스 목록
ros2 interface list --only-msgs  # msg만
ros2 interface list --only-srvs  # srv만
ros2 interface list --only-acts  # action만
ros2 interface show <type>       # 타입 정의 내용
ros2 interface packages          # 인터페이스 포함 패키지 목록
ros2 interface package <pkg>     # 특정 패키지의 인터페이스
```

#### ROSForge Interface Panel 요구사항 (보완)

```
인터페이스 브라우저 UI:
┌─────────────────────────────────────────────┐
│  📚 Interface Browser                [검색]  │
│  [msg] [srv] [action]               [패키지]│
│                                             │
│  my_first_package_msgs                      │
│  ├── msg/                                   │
│  │   └── CmdAndPoseVel.msg ──────────────→  │ float32 cmd_vel_linear
│  ├── srv/                                   │  float32 cmd_vel_angular
│  │   └── MultiSpawn.srv                     │  float32 pose_x
│  └── action/                               │  float32 pose_y
│      └── DistTurtle.action                 │  float32 linear_vel
│                                             │  float32 angular_vel
│  geometry_msgs                              │
│  ├── msg/                                   │
│  │   ├── Twist.msg                          │
│  │   ├── Pose.msg                           │
│  │   └── ...                                │
│                                             │
│  [토픽 발행에 사용]  [서비스 호출에 사용]     │
└─────────────────────────────────────────────┘
```

> ⚠️ **현재 research.md 누락**: 인터페이스 타입에서 바로 토픽 발행/서비스 호출 패널로 연결하는 기능

---

## 3. 교재 커리큘럼 분석

### 3.1 ros2_basic 패키지 구성

| 파일 | 기능 | 사용 ROS2 요소 |
|------|------|----------------|
| `my_first_node.py` | Hello World 기본 노드 | 단순 Python 실행 |
| `my_publisher.py` | Twist 메시지 발행 | Publisher, Timer, geometry_msgs/Twist |
| `my_subscriber.py` | Turtle Pose 구독 | Subscriber, turtlesim/Pose |
| `my_service_server.py` | MultiSpawn 서비스 서버 | Service Server/Client, custom srv |
| `turtle_cmd_and_pose.py` | 토픽 2개 구독 + 커스텀 메시지 발행 | 복수 Subscriber + Publisher, custom msg |
| `dist_turtle_action_server.py` | 거리 이동 액션 서버 + 파라미터 동적 수정 | ActionServer, MultiThreadedExecutor, declare_parameter |
| `my_multi_thread.py` | Publisher + Subscriber 동시 실행 | MultiThreadedExecutor |
| `turtlesim_and_teleop.launch.py` | turtlesim + publisher 동시 런치 | Launch, namespace |
| `dist_turtle_action.launch.py` | 배경색 파라미터 포함 런치 | Launch + parameters dict |
| `turtlesim.yaml` | 파라미터 파일 | ros__parameters YAML |
| `CmdAndPoseVel.msg` | 커스텀 메시지 타입 | float32 복합 메시지 |
| `MultiSpawn.srv` | 커스텀 서비스 타입 | int64 → float64[] |
| `DistTurtle.action` | 커스텀 액션 타입 | Goal/Result/Feedback 3단 |

### 3.2 for_ROS2_study 커리큘럼 구성

| 카테고리 | 파일/폴더 | 핵심 내용 |
|----------|-----------|-----------|
| **PID 제어 + State Machine** | `move_turtle.py` | PID 클래스, state 기반 Turtle 목표 이동, 파라미터 동적 수정 |
| **Behavior Tree** | `move_turtle_behavior_tree.py` | BTNode / SequenceNode, RotateToGoal → MoveToGoal → RotateToFinal |
| **웹 모니터링** | `web_publisher_node.py` + `ros_web_monitor/index.html` | JSON 집계 토픽 → rosbridge → HTML Canvas 시각화 |
| **TF Tutorials** | `my_tf_1.py`, `my_tf_2.py`, `child_frame.py` 외 | TransformBroadcaster, tf2_ros, 거리/방향 계산 |
| **Nav2 연동** | `nav2_send_goal_basic.py` | BasicNavigator, goToPose, feedback 모니터링 |
| **ROS_DOMAIN_ID** | `domain_test.py`, `domain_test_action.py` | 멀티 프로세스, domain_id 격리 테스트 |
| **Gazebo** | `building_robot.sdf` | Gazebo Harmonic SDF 월드 빌드 |
| **Ultrasonic 센서 (RPi)** | `ultrasonic_sensor/` 패키지 | GPIO → ROS2 토픽 발행, launch.xml, config yaml |
| **카메라 퍼블리셔** | `img_pub_1/` | cv_bridge, sensor_msgs/Image |
| **State Machine** | `move_turtle_state_machine.py` | python-statemachine 라이브러리 |
| **PyQt 모니터** | `qmonitor_*.py` | PyQt6 실시간 시각화 |
| **Bash 환경 설정** | `alias_settings_jazzy.sh` | ROS2 Jazzy alias 모음 |

### 3.3 교재 실습 UX 시나리오

#### 시나리오 A: 기초편 (ros2_basic)
```
1. [Env Panel]   플랫폼 선택 → .bashrc alias 적용 → 터미널 확인
2. [Build Panel] my_first_package_msgs 빌드 → 완료 확인
3. [Build Panel] my_first_package 빌드 → 완료 확인
4. [Run Panel]   turtlesim/turtlesim_node 실행
5. [Run Panel]   my_first_package/my_publisher 실행
6. [Topic Panel] /turtle1/cmd_vel 스트리밍 확인 + Twist 플롯
7. [Run Panel]   my_first_package/my_subscriber 실행
8. [Topic Panel] /turtle1/pose x,y,theta 실시간 플롯
9. [Service Panel] multi_spawn 서비스 호출 (num=5)
10. [Action Panel] dist_turtle 액션 Goal 전송 (linear_x=1.0, dist=3.0)
11. [Param Panel]  quatile_time 슬라이더 조정 → 즉시 반영
12. [Log Panel]    parameter_callback 로그 확인
```

#### 시나리오 B: 실전편 — PID 제어
```
1. [Env Panel]   ros2_study 프로파일 활성화
2. [Build Panel] controller_tutorials 빌드
3. [Run Panel]   turtlesim_node + move_turtle 실행
4. [Topic Panel] /goal_pose 토픽 발행 GUI → Pose 입력 (x=5.0, y=8.0, theta=1.57)
5. [Param Panel] angular_P/I/D 슬라이더 실시간 조정
6. [Plot Panel]  /error 토픽 실시간 플롯 확인
7. [2D Map]      Turtlesim x/y 위치 실시간 추적
```

#### 시나리오 C: TF 튜토리얼
```
1. [Build Panel] my_tf 빌드
2. [Run Panel]   my_tf_broadcaster 실행
3. [TF Panel]    world → moving_frame TF 트리 실시간 시각화
4. [Run Panel]   child_frame 실행 추가
5. [TF Panel]    다중 프레임 트리 확인
```

### 3.4 교재 특이사항 (구현 시 주의)

| 항목 | 상세 |
|------|------|
| `turtlesim` 필수 의존성 | 대부분 예제가 `/turtle1/pose`, `/turtle1/cmd_vel` 사용 — turtlesim 자동 감지/실행 권장 |
| namespace 충돌 | `turtlesim_and_teleop.launch.py`에서 `namespace="turtlesim"` — `/turtlesim/turtle1/cmd_vel` vs `/turtle1/cmd_vel` 구분 필요 |
| `ExcuteProcess` 오타 | `dist_turtle_action.launch.py`에 `ExcuteProcess` 오타 — 교재 버그, 파싱 시 무시 처리 필요 |
| rosbridge 포트 9090 | `ros_web_monitor/index.html`이 `ws://localhost:9090` 사용 — rosbridge 자동 시작 지원 필요 |
| ROS_DOMAIN_ID 멀티프로세스 | `domain_test.py`는 `multiprocessing.Process` 사용 — subprocess 관리와 별도 처리 |

---

## 4. 전체 기능 요구사항

### 4.1 Priority 1 — MVP (없으면 교재 실습 불가)

```
[환경 설정]
F-00   플랫폼 선택 GUI → .bashrc alias 자동 생성 → 버튼 클릭 → bashrc 적용 → 터미널 출력
F-00a  ROS_DOMAIN_ID 사용자 입력 + 실시간 수정
F-00b  환경 검증 체크리스트 (ros2 CLI, colcon, rclpy, turtlesim 설치 여부)

[빌드/환경]
F-01   colcon build GUI (패키지 선택, 빌드 로그 실시간)
F-02   source install/setup.bash 자동 적용
F-03   커스텀 메시지 패키지 의존성 순서 빌드

[실행]
F-04   ros2 run GUI (pkg/executable 선택 + args)
F-05   ros2 launch GUI (.py, .xml 모두)
F-06   여러 노드 동시 실행 + 개별 종료

[노드 인트로스펙션]
F-06a  실행 중인 노드 목록 실시간 표시 (이름, 네임스페이스, PID, CPU, MEM)
F-06b  노드 클릭 시 상세 정보 — Publishers / Subscribers / Service Servers /
       Service Clients / Action Servers / Action Clients 6가지 전부 표시
F-06c  노드 종료 / 강제 kill 기능

[토픽]
F-07   토픽 목록 + 타입 실시간 표시
F-07a  토픽별 발행 주파수(Hz) 실시간 표시
F-07b  토픽별 대역폭(KB/s) 실시간 표시
F-07c  토픽별 발행자/구독자 엔드포인트 상세 (노드명, QoS 프로파일)
F-07d  QoS 호환성 불일치 경고 표시
F-08   토픽 메시지 실시간 스트리밍 뷰어 (JSON 트리)
F-09   float64/float32 토픽 실시간 플롯 (pyqtgraph)
F-10   토픽 직접 발행 GUI (Publish Panel — 메시지 필드 자동 생성)

[파라미터]
F-11   노드별 파라미터 실시간 조회
F-11a  파라미터 설명/범위 표시 (describe_parameters 서비스 활용)
F-11b  /parameter_events 구독으로 전체 노드 파라미터 변경 실시간 감지
F-12   파라미터 GUI 수정 (슬라이더 + 입력창, 즉시 반영)
F-12a  배열 타입 파라미터 처리 (BOOL_ARRAY, INTEGER_ARRAY, DOUBLE_ARRAY, STRING_ARRAY)
F-12b  파라미터 변경 히스토리 로깅 (타임스탬프, 이전값→새값, 성공/실패)
F-13   PID 파라미터 전용 슬라이더 위젯

[서비스]
F-14   서비스 호출 GUI (Request 필드 자동 생성 → Response 표시)
F-14a  서비스 호출 응답 시간 측정 및 표시
F-14b  서비스 호출 히스토리 로깅

[액션]
F-15   액션 Goal 전송 + Feedback 실시간 + Result 표시
F-15a  액션 Goal 상태 머신 시각화 (ACCEPTED→EXECUTING→SUCCEEDED/CANCELED/ABORTED)
F-15b  Feedback 실시간 플롯 (time-series)
F-15c  액션 서버 활성/비활성 상태 표시
F-15d  Goal 히스토리 로깅

[인터페이스]
F-16   msg/srv/action 정의 브라우저 (패키지 트리 + 필드 상세)
F-16a  인터페이스 검색/필터 기능
F-16b  인터페이스 브라우저에서 바로 토픽 발행/서비스 호출로 연결

[로그]
F-17   통합 로그 뷰어 (노드별/레벨별 필터)
F-17a  로그 메시지의 file/function/line 소스 위치 표시
F-17b  로그 파일 저장 (.log, .csv)
F-17c  노드 로거 레벨 동적 변경 GUI (set_logger_levels)

[환경변수]
F-18   ROS_DOMAIN_ID 프로젝트별 설정
F-19   환경변수 편집 패널
```

### 4.2 Priority 2 — 실습 효율 대폭 향상

```
F-20   Turtlesim 2D 포즈 뷰어 (Canvas x/y/theta 실시간 + 경로 트레일)
F-21   TF Tree 실시간 시각화 (D3.js — /tf + /tf_static 통합)
F-21a  두 TF 프레임 선택 → 상대 변환 계산 표시
F-22   노드 그래프 토폴로지 (rqt_graph 대체)
F-22a  노드 상태별 색상 구분 (실행중/라이프사이클 상태/오류)
F-22b  엣지 타입 구분 (토픽=실선, 서비스=점선, 액션=두꺼운선)
F-23   상태머신 다이어그램 표시 (BT 상태 하이라이트)
F-24   YAML 파라미터 파일 로드/저장 GUI
F-25   터미널 내장 패널
F-26   액션 Cancel 기능

[라이프사이클 노드]
F-26a  라이프사이클 노드 감지 및 상태 표시
F-26b  라이프사이클 상태 전환 버튼 (configure/activate/deactivate/cleanup/shutdown)
F-26c  트랜지션 이벤트 로그 표시

[Bag 녹화/재생]
F-26d  ros2 bag 녹화 GUI (토픽 선택, 경로 지정, 형식 선택)
F-26e  bag 파일 재생 GUI (타임라인 슬라이더, 속도 조절, 반복)
F-26f  bag 파일 정보 표시 (포함 토픽, 시간범위, 파일 크기)
```

### 4.3 Priority 3 — 고급 기능 (이후 확장)

```
F-27   Gazebo 외부 실행 연동
F-28   RViz2 외부 실행 연동
F-29   sensor_msgs/Image 카메라 뷰어
F-30   MCAP bag 파일 재생 (rosbags 라이브러리)
F-31   다중 ROS_DOMAIN_ID 동시 관리
F-32   rosbridge WebSocket 임베딩 모니터 패널
F-33   토픽 통계 (topic_statistics) 시각화
F-34   QoS 프로파일 편집 및 노드 재시작 없이 적용
F-35   노드 리맵핑 (remapping) GUI
```

### 4.4 파라미터 타입 매핑 (교재 기반)

```python
declare_parameter('angular_P', 1.0)       # float → 슬라이더 + 소수점 입력창
declare_parameter('background_r', 255)    # int   → 0~255 슬라이더
declare_parameter('use_sim_time', False)  # bool  → ON/OFF 토글
declare_parameter('robot_name', 'turtle1')# str   → 텍스트 입력창
```

---

## 5. M00 — 초기 환경 설정

> **M00은 M01 이전에 반드시 완료되어야 하는 선행 마일스톤이다.**  
> 모든 빌드/실행/모니터링 기능이 이 환경 위에서 동작한다.

### 5.1 교재에서 확인된 환경 설정 구조

교재(PinkLAB Edu — bashrc 편)와 `alias_settings_jazzy.sh`를 분석하면 ROS2 개발 환경은 **3계층**으로 구성된다.

```
Layer 1 — ROS2 배포판 소싱
  └─ source /opt/ros/jazzy/setup.bash

Layer 2 — Python 가상환경 (선택적)
  └─ source ~/venv/jazzy/bin/activate

Layer 3 — 워크스페이스 소싱
  └─ source ~/<workspace>/install/local_setup.bash

+ 환경변수
  └─ export ROS_DOMAIN_ID=<ID>
  └─ export RMW_IMPLEMENTATION=<rmw>
  └─ export ROS_LOCALHOST_ONLY=<0|1>
```

#### 교재가 가르치는 .bashrc 설정 순서 (PDF 기준)

```
Step 1  source /opt/ros/jazzy/setup.bash 추가 → 터미널 자동 소싱  (PDF 1.4절)
Step 2  alias 3개 등록                                              (PDF 2절)
        - sb        = "source ~/.bashrc"        (재로드 단축키)
        - ros_domain = "export ROS_DOMAIN_ID=13"
        - jazzy     = "source + ros_domain 한번에"
Step 3  ws_setting() 함수 + 워크스페이스 alias 등록
        - ros2_study = ws_setting "ros2_study"
```

> ⚠️ **PDF 2.1절 주의**: alias에서 `=` 양쪽에 **띄어쓰기 없이** 붙여 써야 함.  
> `alias sb = "..."` → ❌ 오류 / `alias sb="..."` → ✅ 정상

#### 최종 .bashrc 완성 블록 (교재 완성형)

```bash
# ── ROSForge START ──────────────────────────────────────
# 이 블록은 ROSForge가 자동 관리합니다. 수동 편집 시 주의.
# Generated: 2026-03-18 | Profile: ros2_study

alias sb="source ~/.bashrc; echo \"bashrc is reloded\""

ID=13
alias ros_domain="export ROS_DOMAIN_ID=$ID; echo \"ROS_DOMAIN_ID is set to $ID !\""

alias active_venv_jazzy="source ~/venv/jazzy/bin/activate; echo \"Venv Jazzy is activated.\""

alias jazzy="active_venv_jazzy; source /opt/ros/jazzy/setup.bash; ros_domain; echo \"ROS2 Jazzy is activated!\""

ws_setting()
{
    jazzy
    source ~/$1/install/local_setup.bash
    echo "$1 workspace is activated."
}

get_status()
{
    if [ -z $ROS_DOMAIN_ID ]; then
        echo "ROS_DOMAIN_ID : 0"
    else
        echo "ROS_DOMAIN_ID : $ROS_DOMAIN_ID"
    fi

    if [ -z $ROS_LOCALHOST_ONLY ]; then
        echo "ROS_LOCALHOST_ONLY : 0"
    else
        echo "ROS_LOCALHOST_ONLY : $ROS_LOCALHOST_ONLY"
    fi
}

alias ros2_study="ws_setting \"ros2_study\""
# ── ROSForge END ────────────────────────────────────────
```

### 5.2 지원 플랫폼 정의

ROSForge는 사용자가 어떤 플랫폼에서 작업하는지 먼저 물어보고, 선택에 따라 alias 구성을 달리한다.

| 플랫폼 | 설명 | 기본 alias 구성 | 특이사항 |
|--------|------|-----------------|----------|
| **ROS2 Basic (PC)** | 교재 기초편 실습 | jazzy + ros_domain + ws_setting + ros2_study | venv 선택적 |
| **Raspberry Pi** | RPi 하드웨어 개발 | jazzy + ros_domain + ws_setting + GPIO alias | venv OFF 권장 |
| **GHOST-5 (Swarm)** | 스웜 로봇 개발 | jazzy + RMW_ZENOH + SROS2 + ghost5 ws | venv OFF 필수, Domain 42 |
| **Custom** | 직접 구성 | 사용자가 항목별로 선택 | 제한 없음 |

#### 플랫폼별 생성 alias 차이

```bash
# ── ROS2 Basic (PC) ──────────────────────────────────
alias jazzy="source /opt/ros/jazzy/setup.bash; ros_domain; echo \"ROS2 Jazzy is activated!\""
alias ros2_study="ws_setting \"ros2_study\""

# ── Raspberry Pi ─────────────────────────────────────
alias jazzy="source /opt/ros/jazzy/setup.bash; ros_domain; echo \"ROS2 Jazzy is activated!\""
alias rpi_ws="ws_setting \"rpi_ws\""
# GPIO alias 추가 없음 (RPi 전용 환경 확인용)

# ── GHOST-5 ──────────────────────────────────────────
alias ghost5="source /opt/ros/jazzy/setup.bash; \
              export RMW_IMPLEMENTATION=rmw_zenoh_cpp; \
              export ROS_DOMAIN_ID=42; \
              source ~/ghost5/ghost5_ws/install/local_setup.bash; \
              echo \"GHOST-5 env activated!\""
# venv 없음, SROS2 환경변수 추가
```

### 5.3 환경 설정 프로파일 (YAML)

```yaml
# ~/.rosforge/projects/ros2_study.yaml
profile_name: "ros2_study"
description: "ROS2 기초 교재 실습"
platform: "ros2_basic"
created_at: "2026-03-18"

ros2:
  distro: "jazzy"
  setup_path: "/opt/ros/jazzy/setup.bash"

python:
  use_venv: true
  venv_path: "~/venv/jazzy"

workspace:
  root: "~/ros2_study"
  name: "ros2_study"
  overlay_stack:
    - "/opt/ros/jazzy/setup.bash"
    - "~/ros2_study/install/local_setup.bash"

environment:
  ROS_DOMAIN_ID: 13
  ROS_LOCALHOST_ONLY: 0
  RMW_IMPLEMENTATION: "rmw_fastrtps_cpp"
  RCUTILS_COLORIZED_OUTPUT: "1"

build:
  default_args:
    - "--symlink-install"
  auto_venv_deactivate: true    # colcon build 시 venv 자동 비활성화

bashrc:
  auto_apply: true
  backup_before_write: true

launch_presets: []
```

```yaml
# ~/.rosforge/projects/ghost5.yaml
profile_name: "ghost5"
description: "GHOST-5 Swarm Robotics"
platform: "ghost5"

ros2:
  distro: "jazzy"
  setup_path: "/opt/ros/jazzy/setup.bash"

python:
  use_venv: false               # ghost5는 venv 사용 안 함

workspace:
  root: "~/ghost5/ghost5_ws"
  name: "ghost5"
  overlay_stack:
    - "/opt/ros/jazzy/setup.bash"
    - "~/ghost5/ghost5_ws/install/local_setup.bash"

environment:
  ROS_DOMAIN_ID: 42
  RMW_IMPLEMENTATION: "rmw_zenoh_cpp"
  ROS_SECURITY_ENABLE: "true"
  ROS_SECURITY_KEYSTORE: "~/ghost5_keystore"

build:
  auto_venv_deactivate: true
```

### 5.4 환경 검증 체크리스트

프로파일 로드 또는 [환경 검증] 버튼 클릭 시 자동 실행:

```
[Check 1] ROS2 배포판 소싱 확인
  → source /opt/ros/jazzy/setup.bash 가능 여부
  → which ros2 경로 확인

[Check 2] 워크스페이스 유효성
  → <ws_root>/src/ 디렉토리 존재
  → <ws_root>/install/ 존재 여부 (미빌드 시 경고)
  → src/ 내 package.xml 1개 이상

[Check 3] Python 환경
  → venv 경로 존재 여부
  → bash -c "source venv && python -c 'import rclpy'" 가능 여부

[Check 4] 환경변수 상태
  → 현재 ROS_DOMAIN_ID, RMW_IMPLEMENTATION 값 표시

[Check 5] 빌드 도구 확인
  → which colcon
  → cmake --version

[Check 6] 선택적 도구 확인
  → foxglove_bridge 설치 여부
  → rosbridge_suite 설치 여부
  → turtlesim 설치 여부
```

### 5.5 내부 구현 — EnvironmentManager

```python
import subprocess
import os
from pathlib import Path

class EnvironmentManager:
    """
    ROS2 sourced 환경을 Python dict로 생성.
    모든 빌드/실행 프로세스에 이 env를 주입한다.
    """

    def __init__(self, profile: dict):
        self.profile = profile
        self._cached_env: dict | None = None

    def build_ros2_env(self) -> dict:
        """source 명령들을 실행하여 최종 환경변수 dict 반환."""
        dump_cmd = self._build_source_chain() + "\nenv"
        result = subprocess.run(
            ["bash", "-c", dump_cmd],
            capture_output=True, text=True
        )
        env = {}
        for line in result.stdout.splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                env[k] = v
        self._cached_env = env
        return env

    def build_colcon_env(self) -> dict:
        """colcon build 전용: venv PATH 완전 제거."""
        env = self.build_ros2_env().copy()
        venv_path = self.profile["python"].get("venv_path", "")
        if venv_path:
            venv_bin = str(Path(venv_path).expanduser() / "bin")
            env["PATH"] = ":".join(
                p for p in env.get("PATH", "").split(":")
                if p != venv_bin
            )
            env.pop("VIRTUAL_ENV", None)
            env.pop("VIRTUAL_ENV_PROMPT", None)
        return env

    def _build_source_chain(self) -> str:
        lines = []
        for path in self.profile["workspace"]["overlay_stack"]:
            expanded = str(Path(path).expanduser())
            lines.append(f"[ -f '{expanded}' ] && source '{expanded}'")
        for k, v in self.profile.get("environment", {}).items():
            lines.append(f"export {k}={v}")
        return "\n".join(lines)

    def invalidate_cache(self):
        """빌드 완료 후 환경 재소싱을 위한 캐시 무효화."""
        self._cached_env = None
```

### 5.6 .bashrc 편집 로직

```python
class BashrcManager:
    BLOCK_START = "# ── ROSForge START ──────────────────────────────────────"
    BLOCK_END   = "# ── ROSForge END ────────────────────────────────────────"
    BASHRC_PATH = Path.home() / ".bashrc"

    def apply(self, profile: dict, domain_id: int) -> str:
        """
        .bashrc에 ROSForge 블록을 삽입 또는 갱신.
        반환값: 실제로 .bashrc에 기록된 블록 내용 (터미널 출력용)
        """
        block = self._generate_block(profile, domain_id)
        content = self.BASHRC_PATH.read_text()

        if self.BLOCK_START in content:
            # 기존 블록 교체
            start = content.index(self.BLOCK_START)
            end   = content.index(self.BLOCK_END) + len(self.BLOCK_END)
            new_content = content[:start] + block + content[end:]
        else:
            # 중복 source 감지 후 경고
            self._check_conflicts(content, profile)
            new_content = content.rstrip() + "\n\n" + block + "\n"

        # 백업 후 저장
        backup = self.BASHRC_PATH.with_suffix(".bak")
        backup.write_text(content)
        self.BASHRC_PATH.write_text(new_content)
        return block

    def _generate_block(self, profile: dict, domain_id: int) -> str:
        distro    = profile["ros2"]["distro"]
        ws_name   = profile["workspace"]["name"]
        ws_root   = profile["workspace"]["root"]
        use_venv  = profile["python"]["use_venv"]
        venv_path = profile["python"].get("venv_path", "")
        platform  = profile.get("platform", "ros2_basic")
        rmw       = profile["environment"].get("RMW_IMPLEMENTATION", "rmw_fastrtps_cpp")

        lines = [
            self.BLOCK_START,
            f"# 이 블록은 ROSForge가 자동 관리합니다. 수동 편집 시 주의.",
            f"# Generated: 2026-03-18 | Profile: {profile['profile_name']}",
            "",
            f'alias sb="source ~/.bashrc; echo \\"bashrc is reloded\\""',
            "",
            f"ID={domain_id}",
            f'alias ros_domain="export ROS_DOMAIN_ID=$ID; echo \\"ROS_DOMAIN_ID is set to $ID !\\""',
            "",
        ]

        if use_venv and venv_path:
            lines += [
                f'alias active_venv_{distro}="source {venv_path}/bin/activate; echo \\"Venv {distro} is activated.\\""',
                f'alias {distro}="active_venv_{distro}; source /opt/ros/{distro}/setup.bash; ros_domain; echo \\"{distro.upper()} Jazzy is activated!\\""',
            ]
        else:
            lines += [
                f'alias {distro}="source /opt/ros/{distro}/setup.bash; ros_domain; echo \\"ROS2 {distro.capitalize()} is activated!\\""',
            ]

        if platform == "ghost5":
            lines += [
                "",
                f'export RMW_IMPLEMENTATION={rmw}',
            ]

        lines += [
            "",
            "ws_setting()",
            "{",
            f"    {distro}",
            "    source ~/$1/install/local_setup.bash",
            '    echo "$1 workspace is activated."',
            "}",
            "",
            "get_status()",
            "{",
            '    if [ -z $ROS_DOMAIN_ID ]; then',
            '        echo "ROS_DOMAIN_ID : 0"',
            "    else",
            '        echo "ROS_DOMAIN_ID : $ROS_DOMAIN_ID"',
            "    fi",
            '    if [ -z $ROS_LOCALHOST_ONLY ]; then',
            '        echo "ROS_LOCALHOST_ONLY : 0"',
            "    else",
            '        echo "ROS_LOCALHOST_ONLY : $ROS_LOCALHOST_ONLY"',
            "    fi",
            "}",
            "",
            f'alias {ws_name}="ws_setting \\"{ws_name}\\""',
            self.BLOCK_END,
        ]
        return "\n".join(lines)

    def _check_conflicts(self, content: str, profile: dict):
        distro = profile["ros2"]["distro"]
        if f"source /opt/ros/{distro}/setup.bash" in content:
            raise ConflictError(
                f"~/.bashrc에 이미 'source /opt/ros/{distro}/setup.bash'가 존재합니다.\n"
                f"ROSForge 블록과 충돌할 수 있습니다. 기존 줄을 삭제하거나 주석 처리해주세요."
            )
```

---

## 6. M00 GUI 상세 설계 — 환경 설정 화면

> **핵심 목표**: 버튼 클릭만으로 `.bashrc`에 alias가 적용되고, 그 결과가 오른쪽 터미널 패널에 즉시 출력된다.

### 6.1 화면 전체 레이아웃

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ROSForge  │  Environment Setup  │  Profile: [ros2_study ▼]  │  DOMAIN: 13  │
├────────────────────────────────────────────┬────────────────────────────────┤
│                                            │  ● ● ●  Terminal               │
│  STEP 1  플랫폼 선택                        │  ─────────────────────────────│
│  ┌──────────┐ ┌──────────┐                 │                               │
│  │🖥️  ROS2  │ │🍓  RPi  │                 │  $ source ~/.bashrc            │
│  │  Basic   │ │         │                 │  ROSForge 블록을 적용합니다...  │
│  └──────────┘ └──────────┘                 │  ✅ alias sb 등록 완료         │
│  ┌──────────┐ ┌──────────┐                 │  ✅ alias ros_domain 등록 완료 │
│  │👻 GHOST5 │ │⚙️ Custom│                 │  ✅ alias jazzy 등록 완료      │
│  │  Swarm   │ │         │                 │  ✅ alias ros2_study 등록 완료  │
│  └──────────┘ └──────────┘                 │  ✅ .bashrc 저장 완료          │
│                                            │                               │
│  STEP 2  환경 설정                          │  bashrc is reloded            │
│  ┌──────────────────────────────────────┐  │  ROS_DOMAIN_ID is set to 13 ! │
│  │ ROS_DOMAIN_ID  [  13  ] (0~232)      │  │  ROS2 Jazzy is activated!     │
│  │ ROS2 배포판    [jazzy ▼]             │  │  ros2_study workspace is      │
│  │ venv 사용      [■ ON]  [~/venv/jazzy]│  │  activated.                   │
│  │ 워크스페이스   [~/ros2_study  ][찾기]│  │                               │
│  │ RMW            [rmw_fastrtps_cpp ▼] │  │  jt@ubuntu:~$  ▌              │
│  └──────────────────────────────────────┘  │                               │
│                                            │                               │
│  STEP 3  생성될 alias 미리보기              │                               │
│  ┌──────────────────────────────────────┐  │                               │
│  │ # ── ROSForge START ─────────────   │  │                               │
│  │ alias sb="source ~/.bashrc; ..."    │  │                               │
│  │ ID=13                               │  │                               │
│  │ alias ros_domain="export ROS_..."   │  │                               │
│  │ alias jazzy="source /opt/ros/..."   │  │                               │
│  │ ws_setting() { ... }                │  │                               │
│  │ alias ros2_study="ws_setting ..."   │  │                               │
│  │ # ── ROSForge END ───────────────   │  │                               │
│  └──────────────────────────────────────┘  │                               │
│                                            │                               │
│  STEP 4  적용                               │                               │
│  [✅ .bashrc에 적용]  [🔍 환경 검증]        │                               │
│  [💾 백업 생성]       [↩️ 복원]            │                               │
│                                            │                               │
│  ── 상태 점검 결과 ──────────────────────  │                               │
│  ✅ ros2 CLI 감지됨  ✅ colcon 감지됨       │                               │
│  ✅ rclpy import 성공                       │                               │
│  ⚠️ foxglove_bridge 미설치                  │                               │
│  ✅ turtlesim 감지됨                        │                               │
└────────────────────────────────────────────┴────────────────────────────────┘
```

### 6.2 STEP 1 — 플랫폼 선택 카드

플랫폼 선택 → 즉시 STEP 3 미리보기 갱신:

| 플랫폼 카드 | 아이콘 | 자동 설정 내용 |
|------------|--------|----------------|
| **ROS2 Basic** | 🖥️ | jazzy 소싱, venv ON/OFF 선택, ros_domain, ros2_study alias |
| **Raspberry Pi** | 🍓 | jazzy 소싱, venv OFF 기본, rpi_ws alias |
| **GHOST-5** | 👻 | jazzy + rmw_zenoh, venv OFF 강제, Domain 42, ghost5 alias |
| **Custom** | ⚙️ | 모든 항목 사용자 직접 입력 |

### 6.3 STEP 2 — 환경 설정 입력 필드

| 필드 | 위젯 종류 | 비고 |
|------|-----------|------|
| **ROS_DOMAIN_ID** | 숫자 입력창 (0~232) + 슬라이더 | 변경 시 미리보기 즉시 갱신 |
| **ROS2 배포판** | 드롭다운 (자동 감지) | jazzy, humble, rolling |
| **venv 사용** | ON/OFF 토글 | ON 시 경로 입력창 활성화 |
| **venv 경로** | 텍스트 + [찾기] 버튼 | venv 토글 OFF 시 비활성화 |
| **워크스페이스 경로** | 텍스트 + [찾기] 버튼 | 유효성 자동 검사 |
| **RMW** | 드롭다운 | GHOST-5 선택 시 rmw_zenoh 자동 설정 |
| **워크스페이스 alias 이름** | 텍스트 입력창 | 기본값: ros2_study |

> ⚠️ **ROS_DOMAIN_ID**는 이후 언제든지 Environment Panel에서 수정 가능. 변경 후 [.bashrc에 적용] 버튼 클릭 → 터미널에 결과 출력.

### 6.4 STEP 3 — alias 미리보기

실시간 코드 미리보기 패널. STEP 2 값이 바뀔 때마다 자동 갱신:

```
┌──────────────────────────────────────────────────────┐
│  생성될 .bashrc 블록 미리보기          [복사]          │
├──────────────────────────────────────────────────────┤
│  # ── ROSForge START ─────────────────────────────   │
│  # Generated: 2026-03-18 | Profile: ros2_study       │
│                                                      │
│  alias sb="source ~/.bashrc; echo \"bashrc is ..."   │
│                                                      │
│  ID=13                                               │
│  alias ros_domain="export ROS_DOMAIN_ID=$ID; ..."    │
│                                                      │
│  alias active_venv_jazzy="source ~/venv/jazzy/..."   │
│  alias jazzy="active_venv_jazzy; source /opt/..."    │
│                                                      │
│  ws_setting()                                        │
│  {                                                   │
│      jazzy                                           │
│      source ~/$1/install/local_setup.bash            │
│      echo "$1 workspace is activated."               │
│  }                                                   │
│                                                      │
│  get_status() { ... }                                │
│                                                      │
│  alias ros2_study="ws_setting \"ros2_study\""        │
│  # ── ROSForge END ───────────────────────────────   │
└──────────────────────────────────────────────────────┘
```

### 6.5 STEP 4 — 적용 버튼 동작

#### [✅ .bashrc에 적용] 버튼 클릭 시 실행 순서

```
1. .bashrc 백업 생성  (~/.bashrc.bak)
2. 기존 ROSForge 블록 감지
   - 있으면: 해당 블록 교체
   - 없으면: 기존 source 충돌 감지 → 경고 다이얼로그 → 확인 후 파일 끝에 추가
3. 블록 내용을 .bashrc에 기록
4. 터미널 패널에 적용 결과 출력:
   ✅ ~/.bashrc 백업 생성: ~/.bashrc.bak
   ✅ ROSForge 블록 적용 완료
   ─────────────────────────────
   [적용된 내용 요약 출력]
   ─────────────────────────────
5. 자동으로 source ~/.bashrc 실행 (ROSForge 내부 환경 갱신)
6. 터미널에 각 alias 등록 확인 메시지 출력
7. 상태 표시줄 업데이트: DOMAIN: 13 | jazzy ✅
```

#### 터미널 출력 예시

```
$ [ROSForge] .bashrc에 적용을 시작합니다...
  백업 생성: ~/.bashrc.bak ✅
  ROSForge 블록 작성 완료 ✅

$ source ~/.bashrc
bashrc is reloded
ROS_DOMAIN_ID is set to 13 !
ROS2 Jazzy is activated!
ros2_study workspace is activated.

$ alias | grep -E "sb|jazzy|ros_domain|ros2_study"
alias jazzy='active_venv_jazzy; source /opt/ros/jazzy/setup.bash; ...'
alias ros2_study='ws_setting "ros2_study"'
alias ros_domain='export ROS_DOMAIN_ID=13; ...'
alias sb='source ~/.bashrc; echo "bashrc is reloded"'

[ROSForge] ✅ 환경 설정이 완료되었습니다.
```

#### [🔍 환경 검증] 버튼 클릭 시

```
$ [ROSForge] 환경 검증을 시작합니다...
  ✅  ros2 CLI       : /opt/ros/jazzy/bin/ros2
  ✅  colcon         : /usr/bin/colcon
  ✅  rclpy          : import 성공
  ✅  turtlesim      : ros-jazzy-turtlesim 설치됨
  ⚠️  foxglove_bridge: 미설치 (sudo apt install ros-jazzy-foxglove-bridge)
  ✅  rosbridge_suite: ros-jazzy-rosbridge-suite 설치됨
```

### 6.6 ROS_DOMAIN_ID 이후 수정 시나리오

환경 설정 완료 후, 언제든지 수정 가능:

```
Environment Panel 상단 표시줄:
┌────────────────────────────────────────────────────────┐
│  DOMAIN ID:  [ 13 ]  →  [수정]  →  [ 42 ]  [적용]     │
│  변경 시 .bashrc 블록의 ID 값이 갱신되고 터미널 출력    │
└────────────────────────────────────────────────────────┘

터미널 출력:
$ [ROSForge] ROS_DOMAIN_ID를 42로 변경합니다...
  .bashrc 갱신 완료 ✅
$ source ~/.bashrc
  ROS_DOMAIN_ID is set to 42 !
```

---

## 7. 제안 아키텍처

### 7.1 전체 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    ROSForge Frontend (PyQt6)                 │
│                    홈 폴더: ~/ROSForge/                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Env &    │ │  Build & │ │ Topic /  │ │  3D / Plot   │   │
│  │ Bashrc   │ │  Launch  │ │  Param   │ │  Visualizer  │   │
│  │  Panel   │ │  Panel   │ │  Panel   │ │    Panel     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │Interface │ │  Log     │ │  TF Tree │ │  Terminal    │   │
│  │ Browser  │ │ Viewer   │ │  Panel   │ │    Panel     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ WebSocket / IPC
┌───────────────────────────┴─────────────────────────────────┐
│                   ROSForge Backend                           │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │EnvironmentM │  │  ROS2        │  │  foxglove_bridge  │   │
│  │BashrcManager│  │  Introspect  │  │  / rosbridge      │   │
│  │ColconManager│  │  Engine      │  │  WebSocket        │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │ DDS / rmw
┌───────────────────────────┴─────────────────────────────────┐
│                    ROS2 Runtime                              │
│          (Nodes / Topics / Services / Actions)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 기술 스택

### 8.1 프론트엔드

| 항목 | 기술 | 이유 |
|------|------|------|
| UI 프레임워크 | PyQt6 6.x | 기존 스택 활용, rclpy 동일 프로세스 가능 |
| 3D 렌더링 | Three.js (via QWebEngineView) | 웹 기술 활용, URDF/PointCloud 지원 |
| 실시간 플롯 | pyqtgraph (OpenGL 가속) | 10Hz 이상 실시간 최적화 |
| 노드 그래프 | D3.js force-directed (via WebEngine) | 인터랙티브 토폴로지 |
| TF 트리 | D3.js tree layout (via WebEngine) | 계층 구조 표현 |
| 스타일링 | Qt Style Sheets (Dark Theme) | 일관된 다크 테마 |
| 레이아웃 | QDockWidget 패널 시스템 | 자유 배치 가능 |

### 8.2 백엔드

| 항목 | 기술 |
|------|------|
| API 서버 | FastAPI + uvicorn (async) |
| ROS2 인터페이스 | rclpy (직접 노드 임베딩) |
| 실시간 통신 | WebSocket (FastAPI WebSocket) |
| 시각화 브릿지 | foxglove_bridge (C++, 고성능) |
| 프로세스 관리 | asyncio.subprocess + psutil |
| 파일 감시 | watchdog 4.x |
| 직렬화 | pydantic v2 |

### 8.3 ROS2 연동 — 모니터링 대상별 API 매핑

| 모니터링 대상 | rclpy API / 서비스 | 비고 |
|--------------|-------------------|------|
| **노드 목록** | `get_node_names_and_namespaces()` | 1초 폴링 |
| **노드 발행자** | `get_publisher_names_and_types_by_node()` | 노드 선택 시 |
| **노드 구독자** | `get_subscriber_names_and_types_by_node()` | 노드 선택 시 |
| **노드 서비스 서버** | `get_service_names_and_types_by_node()` | 노드 선택 시 |
| **노드 서비스 클라이언트** | `get_client_names_and_types_by_node()` | 노드 선택 시 |
| **노드 액션 서버** | `get_action_server_names_and_types_by_node()` | from rclpy.action |
| **노드 액션 클라이언트** | `get_action_client_names_and_types_by_node()` | from rclpy.action |
| **토픽 목록** | `get_topic_names_and_types()` | 1초 폴링 |
| **토픽 발행자 엔드포인트** | `get_publishers_info_by_topic()` | QoS 포함 |
| **토픽 구독자 엔드포인트** | `get_subscriptions_info_by_topic()` | QoS 포함 |
| **토픽 발행자 수** | `count_publishers()` | |
| **토픽 구독자 수** | `count_subscribers()` | |
| **토픽 메시지** | `create_subscription()` | 동적 타입 |
| **파라미터 목록** | `/<node>/list_parameters` 서비스 | |
| **파라미터 값** | `/<node>/get_parameters` 서비스 | |
| **파라미터 설명/범위** | `/<node>/describe_parameters` 서비스 | |
| **파라미터 수정** | `/<node>/set_parameters` 서비스 | |
| **파라미터 이벤트** | `/parameter_events` 토픽 구독 | 전체 노드 감지 |
| **서비스 목록** | `get_service_names_and_types()` | |
| **서비스 호출** | `create_client()` + `call_async()` | 동적 타입 |
| **액션 목록** | `get_action_names_and_types()` | from rclpy.action |
| **액션 호출** | `ActionClient` | Goal/Feedback/Result |
| **라이프사이클 상태** | `/<node>/get_state` 서비스 | lifecycle_msgs |
| **라이프사이클 전환** | `/<node>/change_state` 서비스 | lifecycle_msgs |
| **라이프사이클 이벤트** | `/<node>/transition_event` 토픽 | latched |
| **TF 프레임** | tf2_ros.Buffer + TransformListener | /tf + /tf_static |
| **로그** | `/rosout` 토픽 구독 | rcl_interfaces/Log |
| **로거 레벨 변경** | `/<node>/set_logger_levels` 서비스 | Jazzy 신기능 |
| **인터페이스 목록** | `ros2 interface list` subprocess | |
| **인터페이스 정의** | `ros2 interface show` subprocess | |

### 8.4 ROS2 연동

| 항목 | 기술 |
|------|------|
| ROS2 버전 | Jazzy Jalisco |
| 기본 미들웨어 | rmw_fastrtps_cpp |
| 스웜 미들웨어 | rmw_zenoh_cpp (GHOST-5) |
| 파라미터 서비스 | rcl_interfaces/srv/SetParameters, DescribeParameters |
| 라이프사이클 | lifecycle_msgs/srv/ChangeState, GetState |
| TF | tf2_ros (Buffer, TransformListener) |
| bag 녹화/재생 | rosbag2_py (Python API) |
| bag 파싱 (비ROS) | rosbags 라이브러리 |

### 8.5 데이터/저장소

| 항목 | 기술 |
|------|------|
| 설정 저장 | YAML (프로파일, 레이아웃) |
| 로그 저장 | SQLite + aiosqlite |
| 파라미터 히스토리 | SQLite (타임스탬프, 이전값, 새값) |
| 서비스/액션 히스토리 | SQLite (호출 시간, 응답 시간, 결과) |
| bag 파일 | MCAP (rosbags 라이브러리) |

### 8.6 Python 패키지 의존성

```
# requirements.txt
rclpy                     # ROS2 Python 클라이언트
PyQt6>=6.6.0
PyQt6-WebEngine>=6.6.0
pyqtgraph>=0.13.0         # 실시간 플롯 (OpenGL)
fastapi>=0.110.0          # REST API 서버
uvicorn[standard]>=0.27   # ASGI 서버
websockets>=12.0          # WebSocket 서버
pydantic>=2.0             # 데이터 모델/검증
watchdog>=4.0             # 파일 시스템 감시
psutil>=5.9               # 프로세스 모니터링 (CPU, MEM)
rosbags>=0.9              # bag 파일 파싱 (non-ROS)
PyYAML>=6.0               # 설정 파일
aiosqlite>=0.19           # 비동기 SQLite
tf-transformations>=1.0   # TF 변환 계산 유틸리티
```

### 8.7 ROS2 패키지 의존성

```xml
<!-- package.xml -->
<depend>rclpy</depend>
<depend>rcl_interfaces</depend>          <!-- ParameterEvent, Log -->
<depend>lifecycle_msgs</depend>          <!-- ChangeState, GetState -->
<depend>foxglove_bridge</depend>         <!-- 시각화 WebSocket -->
<depend>rosbridge_server</depend>        <!-- 웹 모니터 지원 -->
<depend>tf2_ros</depend>                 <!-- TF 트리 -->
<depend>tf2_msgs</depend>                <!-- TFMessage -->
<depend>sensor_msgs</depend>
<depend>nav_msgs</depend>
<depend>geometry_msgs</depend>
<depend>std_msgs</depend>
<depend>action_msgs</depend>             <!-- GoalStatus, GoalInfo -->
<depend>rosbag2_py</depend>              <!-- bag 녹화/재생 -->
```

---

## 9. 프로젝트 디렉토리 구조

> **홈 폴더**: `~/ROSForge/`

```
~/ROSForge/
├── rosforge/
│   ├── main.py                         # 진입점
│   ├── backend/
│   │   ├── environment_manager.py      # source 체인, env dict 생성
│   │   ├── bashrc_manager.py           # .bashrc 편집, 블록 삽입/갱신
│   │   ├── profile_manager.py          # 프로파일 YAML 저장/불러오기
│   │   ├── build_manager.py            # colcon 빌드 자동화
│   │   ├── launch_parser.py            # .launch.py / .launch.xml 파싱
│   │   ├── process_manager.py          # subprocess 노드 관리
│   │   ├── ros2_introspector.py        # 노드/토픽/서비스/액션 전체 인트로스펙션
│   │   ├── topic_manager.py            # 토픽 구독/발행, Hz/BW 측정
│   │   ├── param_manager.py            # 파라미터 CRUD + describe + events
│   │   ├── service_manager.py          # 서비스 클라이언트 + 히스토리
│   │   ├── action_manager.py           # 액션 클라이언트 + Goal 상태 추적
│   │   ├── lifecycle_manager.py        # 라이프사이클 노드 감지 + 상태 전환
│   │   ├── tf_manager.py               # tf2_ros Buffer + 프레임 관리
│   │   ├── log_manager.py              # /rosout 구독 + SQLite 저장 + 레벨 변경
│   │   ├── bag_manager.py              # rosbag2 녹화/재생 래퍼
│   │   └── qos_analyzer.py             # QoS 호환성 분석
│   ├── ui/
│   │   ├── main_window.py              # QMainWindow + QDockWidget
│   │   ├── panels/
│   │   │   ├── env_panel.py            # M00: 환경 설정 + .bashrc 관리
│   │   │   ├── build_panel.py          # M01: colcon 빌드
│   │   │   ├── run_panel.py            # M01: 노드/launch 실행
│   │   │   ├── node_panel.py           # 노드 목록 + 상세 인트로스펙션
│   │   │   ├── topic_panel.py          # M02: 토픽 목록+Hz+BW+엔드포인트+뷰어
│   │   │   ├── param_panel.py          # M03: 파라미터 편집 + 히스토리
│   │   │   ├── service_panel.py        # M04: 서비스 호출 + 히스토리
│   │   │   ├── action_panel.py         # M04: 액션 호출 + 상태머신 + 히스토리
│   │   │   ├── lifecycle_panel.py      # 라이프사이클 노드 제어
│   │   │   ├── interface_panel.py      # M05: 인터페이스 브라우저
│   │   │   ├── log_panel.py            # M05: 로그 뷰어 + 레벨 변경
│   │   │   ├── map2d_panel.py          # M06: Turtlesim 2D 뷰 + 트레일
│   │   │   ├── tf_panel.py             # M06: TF 트리 + 상대 변환
│   │   │   ├── graph_panel.py          # M07: 노드 그래프 (토픽/서비스/액션 엣지)
│   │   │   ├── bag_panel.py            # Bag 녹화/재생 UI
│   │   │   └── terminal_panel.py       # M07: 내장 터미널
│   │   └── widgets/
│   │       ├── platform_selector.py    # 플랫폼 선택 카드 위젯
│   │       ├── alias_preview.py        # alias 코드 미리보기
│   │       ├── domain_id_editor.py     # DOMAIN ID 입력 + 슬라이더
│   │       ├── pid_slider_widget.py    # PID 6개 슬라이더
│   │       ├── param_editor.py         # 파라미터 타입별 위젯 (배열 포함)
│   │       ├── topic_publisher.py      # 메시지 필드 자동 생성 폼
│   │       ├── realtime_plot.py        # pyqtgraph 래퍼
│   │       ├── qos_badge.py            # QoS 프로파일 배지 위젯
│   │       ├── history_table.py        # 히스토리 테이블 공통 위젯
│   │       └── lifecycle_state_widget.py # 라이프사이클 상태 다이어그램
│   ├── config/
│   │   ├── projects/                   # 프로파일 YAML — ~/.rosforge/projects/
│   │   └── layouts/                    # 패널 레이아웃 — ~/.rosforge/layouts/
│   └── assets/
│       └── dark_theme.qss
├── setup.py
├── requirements.txt
└── README.md
```

---

## 10. 전체 마일스톤 계획

### 마일스톤 순서 (선행 의존성 포함)

```
M00 환경 설정 (선행 필수 — 모든 마일스톤의 기반)
 ├─ M00-1:  EnvironmentManager (source 체인, env dict 생성)
 ├─ M00-2:  colcon 전용 env (venv 비활성화 로직)
 ├─ M00-3:  프로파일 YAML 스키마 + 저장/불러오기
 ├─ M00-4:  플랫폼 선택 카드 UI (4종: ROS2 Basic / RPi / GHOST-5 / Custom)
 ├─ M00-5:  환경 설정 입력 필드 UI (DOMAIN ID, 배포판, venv, ws 경로, RMW)
 ├─ M00-6:  alias 미리보기 패널 (실시간 코드 렌더링)
 ├─ M00-7:  [.bashrc에 적용] 버튼 + 터미널 결과 출력
 ├─ M00-8:  환경 검증 체크리스트 실행기
 ├─ M00-9:  상태 표시줄 (프로파일명, DOMAIN, venv, 소싱 상태)
 ├─ M00-10: 프로파일 전환 드롭다운
 ├─ M00-11: .bashrc 충돌 감지 + 경고 다이얼로그
 └─ M00-12: 빌드 후 자동 재소싱 트리거

M01 Build Panel (M00 완료 후)
 → colcon build GUI, 빌드 로그 실시간, 의존성 순서 자동 처리

M02 Topic Panel (M01 완료 후)
 → 토픽 목록, 메시지 뷰어, 실시간 플롯, Publish GUI

M03 Param Panel (M02 완료 후)
 → 파라미터 조회/수정, PID 슬라이더, YAML 로드

M04 Service & Action Panel (M03 완료 후)
 → 서비스 호출 GUI, 액션 Goal/Feedback/Result

M05 Log & Interface Browser (M04 완료 후)
 → 통합 로그 뷰어, msg/srv/action 브라우저

M06 2D Map & TF Panel (M05 완료 후)
 → Turtlesim 2D 포즈 뷰어, TF 트리 시각화

M07 Node Graph & Terminal (M06 완료 후)
 → rqt_graph 대체, 내장 터미널

M08 Launch 파일 파싱 GUI (M07 완료 후)
 → .launch.py / .launch.xml 파싱, 노드 미리보기, 파라미터 수정

M09 Nav2 & Gazebo 연동 (M08 완료 후)
 → Nav2 액션 연동, Gazebo 외부 실행 관리

M10 레이아웃 & 프리셋 (M09 완료 후)
 → 패널 레이아웃 저장/불러오기, 프로젝트 프리셋
```

### 마일스톤별 커버 범위

| 마일스톤 | 기능 코드 | 커버하는 교재 시나리오 |
|----------|-----------|----------------------|
| **M00** | F-00, F-00a, F-00b, F-18, F-19 | 환경 설정 전체 (bashrc 편) |
| **M01** | F-01, F-02, F-03, F-04, F-05, F-06 | ros2_basic 전체 실행 가능 |
| **M02** | F-07, F-08, F-09, F-10 | Publisher/Subscriber 예제 |
| **M03** | F-11, F-12, F-13, F-24 | dist_turtle, move_turtle PID 튜닝 |
| **M04** | F-14, F-15, F-26 | multi_spawn, dist_turtle 액션 |
| **M05** | F-16, F-17 | 전체 교재 디버깅 |
| **M06** | F-20, F-21 | TF 튜토리얼, turtlesim 경로 추적 |
| **M07** | F-22, F-25 | 복합 예제, domain test |
| **M08** | F-05 확장, F-24 | launch 파일 전체 |
| **M09** | F-27, F-28 | Nav2, Gazebo 튜토리얼 |
| **M10** | 레이아웃, F-30 | 전체 |

---

## 11. 리스크 및 고려사항

| 리스크 | 내용 | 대응 |
|--------|------|------|
| **rclpy 스레드 안전성** | GIL + executor 스레드 충돌 | MultiThreadedExecutor + asyncio 분리 |
| **colcon venv 충돌** | venv 활성화 시 colcon 오작동 | 빌드 시 자동 venv PATH 제거 |
| **.bashrc 기존 내용 충돌** | 기존 jazzy source 중복 | 충돌 감지 후 경고 + 사용자 선택 |
| **foxglove_bridge 의존성** | 별도 ROS2 노드로 실행 필요 | subprocess로 자동 시작/관리 |
| **고주파 토픽 성능** | WebSocket 병목 가능 | 메시지 샘플링 (max 10Hz) + 이진 인코딩 |
| **동적 메시지 타입** | 커스텀 msg 타입 런타임 import | `rosidl_runtime_py` + importlib 동적 로드 |
| **멀티 워크스페이스** | 여러 workspace overlay 관리 | 프로파일 파일에 overlay 스택 저장 |
| **커스텀 메시지 빌드 순서** | msgs 패키지 먼저 빌드 필요 | package.xml 의존성 분석 → 자동 정렬 |
| **ExcuteProcess 오타** | 교재 launch 파일 오타 | 파싱 시 `ExcuteProcess` → `ExecuteProcess` 자동 치환 |
| **QoS 불일치** | 발행자-구독자 QoS 호환성 문제 | `get_publishers_info_by_topic` 으로 비교 후 경고 |
| **라이프사이클 노드 감지** | 일반 노드와 구분 필요 | `get_state` 서비스 존재 여부로 감지 |
| **파라미터 배열 타입 UI** | DOUBLE_ARRAY 등 복잡한 타입 | 배열 편집 전용 다이얼로그 위젯 |
| **로거 레벨 서비스** | Jazzy에서 enable_logger_service=True 필요 | 노드 재실행 없이 불가 시 경고 표시 |
| **/rosout 과부하** | 노드 수 증가 시 로그 폭주 | 레벨 필터 + 버퍼 크기 제한 |

---

*작성: gjkong | 2026-03-18 | v2.0 — 모니터링 대상 전체 조사 완료*  
*참조: ros2_basic-main, for_ROS2_study-main, PinkLAB Edu bashrc 교재, ROS2 Jazzy 공식 문서*
