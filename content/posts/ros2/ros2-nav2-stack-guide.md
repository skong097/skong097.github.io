---
title: "ROS 2 자율주행 스택 총정리 — Nav2 · Planner/Controller · AMCL · TF"
date: 2026-08-06
slug: ros2-nav2-스택-총정리
tags: ["ros2", "nav2", "planner", "controller", "amcl", "tf2", "localization", "costmap", "dds", "qos", "navigation", "rep-105"]
categories: ["ros2"]
summary: "ROS 2 를 붙잡고 있으면 계층이 너무 많아서 지금 보고 있는 문제가 어느 층 문제인지부터 헷갈린다. DDS 부터 Nav2 까지의 전체 스택, Nav2 내부 서버 구성, Planner 와 Controller 를 굳이 나눠 놓은 이유, AMCL 이 map→base_link 대신 map→odom 을 발행하는 이유, 그리고 그 모든 것을 떠받치는 TF 의 개념과 기동 순서를 한 편으로 정리한다. 특정 로봇에 묶이지 않은 개념 레퍼런스다."
draft: false
ShowToc: true
TocOpen: true
---

ROS 2 로 자율주행을 다루다 보면 계층이 너무 많아서, **지금 보고 있는 증상이 어느 층의 문제인지**부터 헷갈린다. 로봇이 목표 앞에서 흔들릴 때 그게 컨트롤러 튜닝 문제인지, 측위가 흔들리는 건지, 아니면 TF 가 늦게 도착하는 건지 구분이 안 된다.

이 글은 그 지도를 그린다. 아래에서 위로 — TF, 측위, 코스트맵, Planner/Controller, BT Navigator 순으로 쌓아 올리고, 각 층이 무엇을 책임지는지와 왜 그렇게 잘려 있는지를 정리한다. 특정 로봇이나 프로젝트에 묶이지 않은 개념 레퍼런스로 썼다.

---

## 1. ROS 2 전체 스택

### 1-1. 계층

{{< figure src="/images/diagrams/ros2-stack-layers.svg" alt="ROS 2 계층 스택. 아래에서 위로 OS와 하드웨어, DDS, DDS 벤더를 추상화하는 RMW, 언어 공통 C 코어인 rcl, rclcpp와 rclpy 바인딩, 그리고 최상단의 Nav2·MoveIt2·ros2_control 응용 프레임워크가 쌓인다. QoS와 분산 discovery는 DDS 계층에서 올라오며 그 때문에 마스터 노드가 없다." >}}

핵심은 그림의 **아래 두 칸**이다. ROS 1 의 `roscore` 에 해당하는 마스터가 없다. DDS 의 분산 discovery 가 그 역할을 대신하므로 노드를 어떤 순서로 켜도 서로를 찾는다. 대신 그 대가로 QoS 라는 개념이 개발자에게 그대로 노출됐다.

| 계층 | 하는 일 | 대표 구현 |
|---|---|---|
| 응용 프레임워크 | 도메인 스택 | Nav2, MoveIt2, ros2_control, SLAM Toolbox |
| Client Library | 언어 바인딩 | `rclcpp`, `rclpy`, `rclrs` |
| rcl | 언어 공통 C 코어 | `rcl`, `rcl_action`, `rcl_lifecycle` |
| RMW | DDS 벤더 추상화 | `rmw_fastrtps_cpp`, `rmw_cyclonedds_cpp` |
| DDS | 실제 통신 미들웨어 | Fast DDS(기본), Cyclone DDS, Connext |
| OS / HW | 실행 환경 | Ubuntu, RTOS, MCU(micro-ROS) |

### 1-2. 통신 프리미티브 4종

| 종류 | 패턴 | 쓰는 곳 | 예 |
|---|---|---|---|
| Topic | pub/sub · 비동기 · N:N | 흘러가는 데이터 | `/scan`, `/odom`, `/cmd_vel` |
| Service | req/res · 동기 · 1:1 | 즉답이 필요한 질의 | `/clear_entirely_global_costmap` |
| Action | goal/feedback/result · 취소 가능 | 오래 걸리는 작업 | `/navigate_to_pose` |
| Parameter | (내부적으로 service) | 런타임 설정 | `max_vel_x` |

Action 은 독립된 프리미티브처럼 보이지만 실제로는 **3 개의 service + 2 개의 topic** 합성물이다(goal / cancel / result service, feedback / status topic). 그래서 `ros2 topic list --include-hidden-topics` 를 하면 액션 하나에 여러 토픽이 딸려 나온다.

### 1-3. QoS — ROS 1 대비 가장 큰 함정

DDS 의 QoS 가 그대로 노출되어 있고, **pub 과 sub 의 QoS 가 호환되지 않으면 아예 연결이 성립하지 않는다.** "토픽은 `ros2 topic list` 에 보이는데 콜백이 한 번도 안 불린다"의 1 순위 원인이다.

| 정책 | 값 | 의미 |
|---|---|---|
| Reliability | `RELIABLE` / `BEST_EFFORT` | 재전송 여부. 고빈도 센서는 보통 best_effort |
| Durability | `VOLATILE` / `TRANSIENT_LOCAL` | 늦게 붙은 구독자에게 과거 메시지를 줄지 (= ROS 1 의 latched) |
| History | `KEEP_LAST(depth)` / `KEEP_ALL` | 큐 정책 |
| Deadline / Liveliness / Lifespan | — | 실시간성·헬스체크용 |

관례상 `/scan` 같은 센서 스트림은 `SensorDataQoS`(best_effort, depth 5), `/map` 과 `/tf_static` 은 `transient_local` 을 쓴다. 이 두 개를 기본 QoS 로 구독하면 조용히 아무것도 못 받는다.

### 1-4. 실행 모델

- **Node** — 콜백을 담는 단위. 프로세스와 1:1 이 아니다.
- **Executor** — 콜백을 꺼내 실행하는 루프. `SingleThreadedExecutor`(기본, 콜백 직렬화)와 `MultiThreadedExecutor` 가 있다.
- **Callback Group** — `MutuallyExclusive`(그룹 안에서 직렬) / `Reentrant`(병렬). **서비스 콜백 안에서 다른 서비스를 동기 호출하면 데드락**이고, 이때 Reentrant 그룹으로 분리하는 게 정석 처방이다.
- **Lifecycle Node** — `unconfigured → inactive → active → finalized` 상태머신을 갖는 관리형 노드. Nav2 의 서버들이 전부 이걸로 되어 있다.
- **Composition** — 여러 노드를 한 프로세스에 로드하면 intra-process 통신으로 직렬화 없이 포인터를 넘긴다. 카메라·포인트클라우드에서 체감 차이가 크다.

### 1-5. 빌드와 툴링

```bash
colcon build --symlink-install
source install/setup.bash

ros2 node list
ros2 topic echo /scan
ros2 param get /controller_server max_vel_x
ros2 interface show nav_msgs/msg/Path
ros2 launch nav2_bringup navigation_launch.py
ros2 bag record -a
```

진단용으로는 `rqt_graph`, `rviz2`, `ros2 doctor`, 그리고 뒤에서 다룰 `tf2_tools` 가 사실상 상시 도구다.

---

## 2. Nav2 내비게이션 스택

### 2-1. Nav2 는 하나의 노드가 아니다

Nav2 는 **여러 개의 lifecycle 노드(서버)** 와 그 안에 꽂히는 **플러그인**의 조합이다. 모놀리식 라이브러리가 아니라서, 문제가 생겼을 때 "어느 서버가 실패했는가"를 먼저 물어야 한다.

| 서버 | 역할 | 대표 플러그인 |
|---|---|---|
| **BT Navigator** | 최상위 오케스트레이터. 행동트리로 전체 흐름 제어 | `navigate_to_pose.xml`, `navigate_through_poses.xml` |
| **Planner Server** | 전역 경로 생성 | NavFn(A*/Dijkstra), Smac 2D · Hybrid-A* · State Lattice, Theta* |
| **Controller Server** | 경로 추종 + 지역 회피 | DWB, RPP(Regulated Pure Pursuit), MPPI, TEB, Graceful |
| **Smoother Server** | 경로 후처리 평활화 | Simple, Savitzky-Golay, Constrained |
| **Behavior Server** | 복구 행동 | Spin, BackUp, Wait, DriveOnHeading, AssistedTeleop |
| **Velocity Smoother** | `cmd_vel` 의 가속도·저크 제한 | — |
| **Collision Monitor** | 최종 안전망. 근접 시 감속·정지 | polygon / circle zone |
| **Waypoint Follower** | 다지점 순회 + 지점별 태스크 | WaitAtWaypoint, PhotoAtWaypoint |
| **Map Server** | 정적 지도 로드·저장 | — |
| **Lifecycle Manager** | 위 노드들의 configure/activate 순서와 감시 | — |

`Planner Server` 와 `Controller Server` 는 각각 `nav2_core::GlobalPlanner`, `nav2_core::Controller` 인터페이스를 구현한 플러그인을 로드한다. 로봇 형태가 바뀌면 서버가 아니라 플러그인을 바꾼다.

### 2-2. 데이터 흐름

{{< figure src="/images/diagrams/ros2-nav2-dataflow.svg" alt="Nav2 데이터 흐름. BT Navigator가 goal을 받아 Planner Server를 부르면 Global Costmap을 근거로 경로가 나오고, 그 경로를 Controller Server가 Local Costmap을 보며 cmd_vel로 바꾼다. cmd_vel은 Velocity Smoother와 Collision Monitor를 거쳐 ros2_control로 간다. 바퀴가 돌면 휠 엔코더가 odom을 만들고, AMCL이 스캔과 지도를 비교해 map에서 odom TF를 발행한다." >}}

여기서 놓치기 쉬운 부분은 오른쪽 아래에서 왼쪽 위로 돌아오는 점선이다. **TF 가 없으면 코스트맵이 센서 데이터를 지도 위에 놓을 수 없다.** 그래서 TF 가 끊기면 Nav2 전체가 멈춘다 — 5장에서 다시 다룬다.

### 2-3. Costmap 2D

Planner 와 Controller 의 공통 입력이다. 두 벌이 따로 돈다.

{{< figure src="/images/diagrams/ros2-costmap-layers.svg" alt="Costmap 2D 레이어 구조. 왼쪽의 정적 지도, 라이다 스캔, 포인트클라우드, 필터 마스크가 static_layer, obstacle_layer, inflation_layer, costmap_filter로 들어가 순서대로 굽히고, 오른쪽에서 0부터 255 사이의 최종 cost 격자가 만들어진다." >}}

레이어를 아래부터 순서대로 쌓아 최종 cost 를 만든다.

```yaml
global_costmap:
  global_costmap:
    ros__parameters:
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        inflation_radius: 0.55
        cost_scaling_factor: 3.0
```

| 레이어 | 하는 일 |
|---|---|
| Static | `/map` 을 그대로 격자에 굽는다 |
| Obstacle / Voxel | LaserScan·PointCloud 로 마킹(marking), 레이캐스팅으로 지우기(clearing) |
| Inflation | 장애물 주변에 지수 감쇠 cost 를 부여 — 로봇 반경만큼 부풀려 **로봇을 점으로 취급**할 수 있게 한다 |
| Range | 초음파·적외선 |
| Denoise | 튀는 노이즈 셀 제거 |
| Costmap Filter | Keepout(진입금지), Speed Limit(구역별 속도제한) 마스크 |

cost 값의 관례는 `0` 자유, `1~252` 비용 있음, `253` inscribed(로봇 내접원 충돌), `254` lethal, `255` unknown 이다. Planner 와 Controller 는 이 숫자만 본다.

`inflation_radius` 는 튜닝 파라미터가 아니라 **로봇 크기를 코스트맵에 알려주는 선언**에 가깝다. 이걸 로봇 반경보다 작게 잡으면 경로가 벽에 붙고, 크게 잡으면 좁은 문을 통과 못 한다.

### 2-4. Behavior Tree — Nav2 의 조율 계층

BT Navigator 가 실행하는 XML 이 사실상 Nav2 의 제어 흐름이다. 기본 트리(`navigate_to_pose_w_replanning_and_recovery.xml`)의 뼈대만 추리면 이렇다.

```xml
<RecoveryNode number_of_retries="6">
  <PipelineSequence>
    <RateController hz="1.0">
      <ComputePathToPose goal="{goal}" path="{path}"/>
    </RateController>
    <FollowPath path="{path}"/>
  </PipelineSequence>

  <SequenceStar>
    <ClearEntireCostmap/>
    <Spin spin_dist="1.57"/>
    <BackUp backup_dist="0.15"/>
    <Wait wait_duration="5"/>
  </SequenceStar>
</RecoveryNode>
```

여기서 다음 장의 핵심이 이미 드러난다. `ComputePathToPose`(Planner)는 `RateController hz="1.0"` 로 감싸여 **1 Hz** 로만 다시 불리고, `FollowPath`(Controller)는 그 사이에 **계속** 돈다.

---

## 3. Planner 와 Controller

### 3-1. 각각 무엇인가

{{< figure src="/images/diagrams/ros2-planner-controller-split.svg" alt="Planner Server와 Controller Server의 여섯 축 비교. Planner는 어느 길로 갈지를 지도 전체를 보고 1Hz로 탐색해 Path를 내고, Controller는 지금 어떤 속도로 갈지를 주변 몇 미터만 보고 20~50Hz로 최적화해 Twist를 낸다." >}}

**Planner (Global Planner)**

- 질문: "여기서 목표까지 **어떤 길로** 가야 하나?"
- 입력: global costmap, 현재 pose, goal pose
- 출력: `nav_msgs/Path` — 좌표들의 나열
- 주기: goal 수신 시 1 회, 또는 1 Hz 정도의 재계획
- 알고리즘: 격자·그래프 **탐색** — Dijkstra, A*, Hybrid-A*, State Lattice
- 관심사: 완결성(경로가 존재하면 반드시 찾는다), 최적성, 전역 데드엔드 회피

**Controller (Local Planner)**

- 질문: "이 경로를 **지금 이 순간 어떤 속도로** 따라가야 하나?"
- 입력: local costmap, 현재 pose·속도, Planner 가 준 경로
- 출력: `geometry_msgs/Twist` — 선속도·각속도 한 쌍
- 주기: 20~50 Hz
- 알고리즘: 궤적 샘플링·**최적화** — DWA, Pure Pursuit, MPC(MPPI)
- 관심사: 운동학·동역학 제약, 갑자기 나타난 장애물 회피, 부드러움

### 3-2. 왜 분리했는가

여섯 가지 이유가 있고 서로 독립적이다.

**① 계산 비용과 요구 주기가 정반대다 — 가장 결정적**

100 m × 100 m 격자에서 A* 탐색은 수십~수백 ms 가 걸린다. 이걸 50 Hz(20 ms 주기)로 돌릴 수 없다. 반대로 제어 명령은 20 ms 안에 나와야 갑자기 나타난 장애물 앞에서 멈출 수 있다. **하나의 알고리즘이 두 요구를 동시에 만족할 수 없어서**, 느리지만 넓게 보는 층과 빠르지만 좁게 보는 층으로 쪼갠 것이다.

**② 상태 공간의 차원이 다르다**

Planner 는 `(x, y)` 또는 `(x, y, θ)` — 기하학이다. Controller 는 여기에 `(v, ω, a)` 까지 포함한 동적 상태 — 물리다. 동역학까지 포함해서 전역 탐색을 하면 차원의 저주로 폭발한다.

**③ 정보의 신선도와 범위가 다르다**

전역 지도는 며칠 전에 만든 정적 정보이고, 로컬 코스트맵은 방금 들어온 센서다. 오래된 정보로 즉각 회피를 결정하면 안 되고, 최신 센서만으로 전역 경로를 짜면 벽 뒤 상황을 몰라서 막다른 길에 갇힌다. **두 종류의 정보를 각자 맞는 층에서 쓰게 하는 것**이다.

**④ 실패 모드와 복구 전략이 다르다**

- Planner 실패 = "경로 자체가 없다" → 코스트맵 클리어, 목표 완화
- Controller 실패 = "경로는 있는데 못 따라간다" → 재계획 요청, 제자리 회전, 후진

BT 가 이 둘을 다른 방식으로 처리할 수 있는 건 애초에 분리되어 있기 때문이다.

**⑤ 플러그인 조합의 자유도**

| 로봇 | Planner | Controller |
|---|---|---|
| 차동구동 실내 | NavFn 또는 Smac 2D | RPP 또는 MPPI |
| 애커만(차량형) | Smac Hybrid-A* | RPP + 회전반경 제약 |
| 옴니휠 | Smac 2D | MPPI (Omni) |

**⑥ 이론적 배경**

전통적 Sense-Plan-Act(느리지만 똑똑함)와 반응형 아키텍처(빠르지만 근시안)의 절충인 **hierarchical deliberative/reactive** 구조다. 로보틱스에서 수십 년에 걸쳐 수렴한 패턴이고, Nav2 만의 발명이 아니다.

### 3-3. 분리의 대가

분리는 공짜가 아니다. **불일치(mismatch)** 를 만든다. Planner 가 "제자리에서 90도 회전한 뒤 직진"하는 격자 경로를 냈는데, 애커만 로봇은 그렇게 움직이지 못한다. 이 틈을 메우는 장치가 셋 있다.

- **Kinematically feasible planner** — Smac Hybrid-A* 는 애초에 로봇의 최소 회전반경을 지키는 경로만 만든다.
- **Smoother Server** — 계단식 격자 경로를 곡선으로 다듬는다.
- **MPPI** — 경로를 "반드시 밟아야 할 점"이 아니라 **비용함수의 참조**로 써서, 못 따라가는 구간을 부드럽게 흡수한다.

로봇이 경로를 따라가다 지그재그를 그린다면, 컨트롤러 게인부터 만지기 전에 **Planner 가 낸 경로가 애초에 이 로봇이 따라갈 수 있는 모양인지**를 먼저 보는 게 순서다.

---

## 4. AMCL — Adaptive Monte Carlo Localization

### 4-1. 무엇인가

**이미 있는 지도 위에서 로봇이 어디 있는지 추정**하는 파티클 필터다. 지도를 만들지는 않는다 — 그건 SLAM 의 일이다.

- **Monte Carlo Localization** — 로봇의 가능한 pose 후보를 수천 개의 **파티클**로 뿌리고, 센서와 맞는 것만 살아남게 한다.
- **Adaptive** — **KLD-sampling**. 파티클이 한 곳에 모이면(확신 ↑) 개수를 줄이고, 퍼지면(불확실 ↑) 늘린다. CPU 를 아끼는 핵심 기법이다.

| 방향 | 항목 |
|---|---|
| 입력 | `/scan`(LaserScan), `/map`(OccupancyGrid), `odom→base_link` TF, `/initialpose` |
| 출력 | **`map→odom` TF**, `/amcl_pose`(PoseWithCovarianceStamped), `/particle_cloud` |

### 4-2. 왜 `map→base_link` 가 아니라 `map→odom` 인가

{{< figure src="/images/diagrams/ros2-amcl-cycle.svg" alt="AMCL의 두 가지 핵심. 위는 TF 소유권으로, map에서 odom은 AMCL이 drift 보정으로, odom에서 base_link는 휠 오도메트리가 연속적으로 발행한다. 부모는 하나뿐이라 AMCL은 map에서 base_link를 직접 발행할 수 없다. 아래는 파티클 필터 한 사이클로 Predict, Update, Resample이 반복된다." >}}

이게 AMCL 이해의 핵심이다.

TF 트리에서 **한 프레임의 부모는 정확히 하나**다. `odom→base_link` 는 이미 휠 오도메트리가 발행하고 있다 — 고주파, 연속적, 대신 누적 drift 가 있다. 여기에 AMCL 이 `map→base_link` 를 발행해 버리면 `base_link` 의 부모가 둘이 되어 트리가 깨진다.

그래서 AMCL 은 **"오도메트리가 그동안 얼마나 틀렸는지"라는 보정량**만 `map→odom` 으로 발행한다.

결과적으로 `map→base_link` 는 두 변환의 합성으로 자동 계산된다. 오도메트리의 **연속성**(제어에 필요)과 전역 위치의 **정확성**(내비게이션에 필요)을 동시에 얻는 설계다.

### 4-3. 동작 사이클

1. **Predict (Motion Update)** — 오도메트리 변화량만큼 모든 파티클을 이동시키고, `alpha1~alpha5` 노이즈를 섞어 퍼뜨린다.
   - `alpha1` 회전→회전, `alpha2` 이동→회전, `alpha3` 이동→이동, `alpha4` 회전→이동
2. **Update (Measurement Update)** — 각 파티클 위치에서 "이 스캔이 나올 확률"을 계산해 가중치를 준다.
   - `likelihood_field` — 지도의 장애물까지 거리장을 미리 계산해 둔다. 빠르고, **기본 권장**
   - `beam` — 광선별 물리 모델(hit/short/max/rand). 정확하지만 느리고 지역 최소값에 취약
3. **Resample** — 가중치에 비례해 재추출. 개수는 KLD 가 정한다. 매 스텝이 아니라 `resample_interval` 마다.

**트리거가 중요하다.** `update_min_d`(예 0.25 m) 또는 `update_min_a`(예 0.2 rad) 이상 움직여야 사이클이 돈다. 가만히 서 있으면 갱신하지 않는다 — 정지 상태에서 파티클이 인위적으로 수렴해 버리는 걸 막기 위해서다.

### 4-4. 주요 파라미터

```yaml
amcl:
  ros__parameters:
    min_particles: 500
    max_particles: 2000

    update_min_d: 0.25            # 이만큼 움직여야 필터 갱신
    update_min_a: 0.2
    resample_interval: 1

    laser_model_type: "likelihood_field"
    laser_likelihood_max_dist: 2.0
    laser_max_range: 12.0
    max_beams: 60                 # 스캔을 전부 쓰지 않고 다운샘플링

    z_hit: 0.5                    # 측정모델 혼합비 (z_hit + z_rand ≈ 1)
    z_rand: 0.5
    sigma_hit: 0.2

    robot_model_type: "nav2_amcl::DifferentialMotionModel"
    alpha1: 0.2
    alpha2: 0.2
    alpha3: 0.2
    alpha4: 0.2

    transform_tolerance: 1.0      # TF 를 미래로 얼마나 연장 발행할지
    set_initial_pose: true
    tf_broadcast: true            # false 면 map→odom 을 발행하지 않는다
```

`tf_broadcast: false` 는 다른 소스(예: 외부 측위 시스템)가 `map→odom` 을 소유할 때 쓴다. AMCL 을 추정치 계산용으로만 남기는 설정이다.

### 4-5. 서비스

```bash
# 전역 재초기화 — 파티클을 지도 전체에 다시 뿌린다
ros2 service call /reinitialize_global_localization std_srvs/srv/Empty

# 정지 상태에서 한 번 강제 갱신
ros2 service call /request_nomotion_update std_srvs/srv/Empty
```

### 4-6. 한계

- **Kidnapped robot** — 로봇을 들어서 옮기면 파티클이 이미 수렴해 있어 스스로 복구하지 못한다. 위 서비스로 수동 재초기화가 필요하다.
- **특징 없는 환경** — 긴 복도, 넓은 홀. 어디서 봐도 스캔이 비슷해서 진행 방향의 위치를 잡지 못한다.
- **지도와 현실의 불일치** — 가구 재배치, 사람 밀집. 가중치 계산이 엉망이 된다.
- **동적 장애물** — AMCL 자체에는 특별한 처리가 없다.

대안과 보완:

- `slam_toolbox` 의 localization 모드 — 스캔매칭 기반이고 지도를 갱신할 수 있다.
- `robot_localization` 의 EKF/UKF — AMCL 을 **대체하는 게 아니라**, IMU·휠·GPS 를 융합해 **더 좋은 `odom` 을 만들어 주는 하위 층**이다. 층위가 다르다.

---

## 5. TF (tf2)

### 5-1. 무엇을 해결하는가

로봇에는 좌표계가 수십 개 있다 — 지도, 로봇 본체, 라이다, 카메라, 각 관절. "라이다가 본 점을 지도 좌표로 바꾸기"를 매번 손으로 곱하면 감당이 안 된다. 게다가 **관절이 움직이면 변환도 시간에 따라 변하고**, 센서마다 타임스탬프가 다르다.

tf2 는 이걸 **분산 발행 + 시간 버퍼 + 자동 보간**으로 푼다.

### 5-2. 개념

{{< figure src="/images/diagrams/ros2-tf-bringup.svg" alt="TF 프레임 체인과 기동 순서. 위는 REP-105 체인으로 map에서 odom은 AMCL이나 SLAM이, odom에서 base_link는 베이스 드라이버가, base_link에서 센서 프레임은 URDF와 robot_state_publisher가 tf_static으로 발행한다. 아래는 다섯 단계 기동 순서와 각 단계의 검증 명령." >}}

**① 트리 구조** — 각 프레임의 부모는 정확히 하나. 사이클 없음. 하지만 각 엣지는 서로 다른 노드가 발행할 수 있고, tf2 가 전역으로 조립한다.

**② REP-105 프레임 관례**

| 프레임 | 성질 |
|---|---|
| `map` | 전역 고정. **drift 없음, 대신 불연속 점프 가능**(AMCL 보정 순간) |
| `odom` | **연속적**, 매끄러움. **대신 시간에 따라 drift 누적** |
| `base_link` | 로봇 본체 기준점 |
| `base_footprint` | 지면 투영점 (선택) |

`map` 과 `odom` 을 나눈 이유가 여기 다 들어 있다. 제어는 연속성이 필요하고(위치가 점프하면 제어기가 발작한다), 내비게이션은 전역 정확성이 필요하다. 둘을 다른 프레임으로 분리해서 각자 필요한 걸 쓰게 한다.

**③ REP-103 단위·축 관례** — SI 단위, 오른손 좌표계, **x = 전방, y = 좌측, z = 상방**. 각도는 라디안.

**④ 두 종류의 변환**

| | 토픽 | QoS | 용도 |
|---|---|---|---|
| 동적 | `/tf` | volatile · 고주파 | 관절, 오도메트리, 측위 |
| 정적 | `/tf_static` | **transient_local (latched)** | 볼트로 고정된 센서 위치 |

정적 TF 는 한 번만 발행되고, 늦게 켜진 노드도 `transient_local` 덕분에 받는다. 반대로 구독 측 QoS 를 잘못 맞추면 못 받는다.

**⑤ 시간 보간과 extrapolation** — `lookupTransform` 에 시각을 넘기면 버퍼의 앞뒤 샘플을 보간한다. 버퍼 범위를 벗어나면 `ExtrapolationException`. `TimePointZero` 를 넘기면 "가장 최신"을 뜻한다.

### 5-3. 코드

발행 (동적):

```cpp
tf2_ros::TransformBroadcaster br(this);

geometry_msgs::msg::TransformStamped t;
t.header.stamp    = now();
t.header.frame_id = "odom";       // 부모
t.child_frame_id  = "base_link";  // 자식
t.transform.translation.x = x;
t.transform.rotation = tf2::toMsg(q);
br.sendTransform(t);
```

조회:

```cpp
tf2_ros::Buffer buffer(get_clock());
tf2_ros::TransformListener listener(buffer);

// (target, source, time, timeout)
auto tf = buffer.lookupTransform("map", "base_link",
                                 tf2::TimePointZero, 100ms);

geometry_msgs::msg::PointStamped out;
buffer.transform(in_point, out, "map", 100ms);
```

`lookupTransform("map", "base_link", ...)` 는 **"base_link 좌표를 map 좌표로 바꾸는 변환"**이다. 인자 순서가 `(target, source)` 라는 게 계속 헷갈리는 지점이니 주석으로 박아 두는 편이 낫다.

**URDF 기반 자동 발행** — `robot_state_publisher` 가 URDF 를 읽고 `/joint_states` 를 구독해 링크 간 TF 를 전부 자동 발행한다. 고정 조인트는 `/tf_static` 으로, 회전·직동 조인트는 `/tf` 로 나간다. 센서 마운트 위치를 손으로 broadcast 하지 말고 URDF 에 넣는 게 맞다.

### 5-4. 기동 절차

순서대로, **각 단계를 검증하면서** 올린다. 뒤 단계의 문제는 대개 앞 단계의 문제다.

**1단계 — URDF 와 static TF**

```bash
ros2 launch <robot>_description rsp.launch.py   # robot_state_publisher
ros2 run tf2_tools view_frames                  # frames.pdf 생성
```

검증: `base_link → laser_link` 같은 센서 프레임이 전부 보이고, **하나로 연결된 트리**여야 한다. 조각이 여러 개면 URDF 조인트 누락이다.

**2단계 — 베이스 드라이버 (`odom→base_link`)**

```bash
ros2 launch <robot>_bringup base.launch.py
ros2 run tf2_ros tf2_echo odom base_link
```

검증: 로봇을 손으로 밀거나 teleop 으로 움직였을 때 값이 따라 변하고, **방향이 REP-103 과 맞아야** 한다(전진하면 x 증가). 여기서 부호가 뒤집혀 있으면 이후 전부 망가진다.

**3단계 — 센서 드라이버**

```bash
ros2 topic echo /scan --field header.frame_id
```

검증: `frame_id` 가 URDF 의 링크 이름과 정확히 일치해야 한다. 오타, 그리고 앞에 붙은 `/`(ROS 2 에서는 붙이지 않는다)를 주의한다.

**4단계 — Localization (`map→odom`)**

```bash
ros2 launch nav2_bringup localization_launch.py map:=my_map.yaml
ros2 run tf2_ros tf2_echo map odom
```

검증: RViz 의 2D Pose Estimate 로 초기 위치를 준 뒤 로봇을 움직이면 `/particle_cloud` 가 수렴해야 한다.

**5단계 — Nav2**

```bash
ros2 launch nav2_bringup navigation_launch.py
```

검증: `map → odom → base_link → laser_link` 가 끊김 없이 연결된 상태. RViz 의 TF 디스플레이로 확인한다.

**상시 진단 도구**

```bash
ros2 run tf2_tools view_frames                 # 전체 트리 PDF + 발행 주기·발행 노드
ros2 run tf2_ros tf2_echo <parent> <child>     # 실시간 값
ros2 run tf2_ros tf2_monitor <parent> <child>  # 지연·주기 통계
ros2 topic hz /tf
```

### 5-5. 흔한 실패 다섯 가지

| 증상 | 원인 | 처방 |
|---|---|---|
| `Lookup would require extrapolation into the future` | 노드 간 시간 불일치, 또는 stamp 가 너무 오래됨 | 시뮬이면 **모든 노드에** `use_sim_time:=true`. 실기는 chrony/NTP 동기화 |
| `"X" passed to lookupTransform does not exist` | frame_id 오타, URDF 미로드, 앞에 붙은 `/` | `view_frames` 로 실제 이름 확인 |
| TF 가 튀거나 진동 | **두 노드가 같은 자식 프레임을 발행** (예: 오도메트리와 EKF 가 둘 다 `odom→base_link`) | 하나만 남긴다. `view_frames` 출력에 발행 노드가 표시된다 |
| static TF 를 못 받음 | QoS durability 미스매치 | 구독 측을 `transient_local` 로 |
| 목표 근처에서 로봇이 흔들림 | `transform_tolerance` 부족, TF 주기가 낮음 | 주기를 올린다(오도메트리는 최소 30~50 Hz 권장) |

---

## 6. 하나로 꿰기

{{< figure src="/images/diagrams/ros2-stack-overview.svg" alt="이 글 전체를 하나로 꿴 지도. 왼쪽 세로 기둥은 노드·토픽·액션·QoS·lifecycle을 제공하는 ROS 2 코어이고, 오른쪽은 아래에서 위로 TF, AMCL 측위, 코스트맵, Planner와 Controller, BT Navigator가 쌓인다." >}}

- **TF** 가 모든 것의 기반이다. `odom→base_link` 는 드라이버가(연속·drift), `map→odom` 은 AMCL 이(보정·점프 가능) 발행한다.
- 그 위에서 **Costmap** 이 TF 로 센서를 지도 좌표에 투영해 비용 격자를 만든다.
- 그 격자를 **Planner** 는 느리게·넓게 보고 "어느 길"을, **Controller** 는 빠르게·좁게 보고 "어떤 속도"를 낸다.
- **BT Navigator** 가 둘을 조율하고, 실패하면 복구 행동을 부른다.
- 이 전부가 **ROS 2 코어**(노드·토픽·액션·QoS·lifecycle) 위에서 돈다.

실무적으로 가장 쓸모 있는 결론은 **디버깅 순서도 이 그림과 같다**는 것이다. 증상은 위층에서 보이지만 원인은 대개 아래층에 있다. 로봇이 목표 앞에서 떠는 걸 보고 컨트롤러 게인부터 만지기 전에, 순서대로 아래를 확인하는 게 빠르다.

1. TF 트리가 하나로 연결되어 있고 주기가 충분한가
2. `map→odom` 이 안정적인가 (`/particle_cloud` 가 수렴해 있는가)
3. 코스트맵의 `inflation_radius` 와 로봇 크기가 맞는가
4. Planner 가 낸 경로를 이 로봇이 따라갈 수 있는 모양인가
5. 그 다음이 Controller 튜닝이다
