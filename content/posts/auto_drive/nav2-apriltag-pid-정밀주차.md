---
title: "Nav2로 가까이 가고, AprilTag PID로 정확히 멈추기 — Pinky 정밀 주차"
date: 2026-07-02
tags: ["auto-drive", "ros2", "nav2", "apriltag", "pid", "docking", "precision-parking", "wasab", "pinky"]
categories: ["robotics"]
summary: "Nav2는 목표물 근처까지 데려다주는 데 강하지만, 충전기 앞 2cm 같은 마지막 정렬은 map 좌표가 아니라 목표물과의 상대 위치 문제다. Pinky의 정밀 주차를 'Nav2 접근 + AprilTag 저속 PID 정렬' 두 단계로 나눈 구조와 실기 검증 순서를 정리한다."
draft: false
ShowToc: true
TocOpen: true
---

로봇을 목적지까지 보내는 일은 Nav2가 잘한다. 지도 위에서 경로를 만들고, 장애물을 피하고, 목표 지점 근처까지 안정적으로 이동하는 데에는 Nav2가 적합하다. (Nav2가 지도 위 위치를 어떻게 잡는지는 앞선 글 [Costmap과 AMCL 정리](../nav2-costmap-amcl-자율주행-위치추정-입문/)에서 다뤘다.)

하지만 "정확히 충전기 앞에 서기", "작업 지점 앞에서 2cm 안쪽으로 맞추기", "벽면의 특정 표식과 정면으로 마주 보기" 같은 문제는 조금 다르다. 이때 필요한 기준은 지도상의 좌표라기보다, 실제 목표물과 로봇 사이의 상대 위치다.

그래서 Pinky의 정밀 주차는 두 단계로 나누기로 했다.

1. Nav2로 목표물 근처까지 이동한다.
2. AprilTag를 보고 마지막 위치와 방향을 저속 PID로 맞춘다.

이 글은 이 방식이 실제로 어떻게 동작하는지 정리한 설명이다.

## 왜 Nav2만으로 끝내지 않는가

Nav2는 `map` 좌표계에서 목표 pose를 받는다. 예를 들어 콘솔에서 `x=1.20`, `y=0.42`, `yaw=1.57` 같은 목표를 보내면, Nav2는 그 지점까지 경로를 계획하고 로봇을 이동시킨다.

이 방식은 복도 주행, 웨이포인트 이동, 넓은 영역에서의 위치 도달에는 충분히 좋다. 하지만 정밀 주차에서는 몇 가지 한계가 있다.

- AMCL/map 기준 pose에는 누적 오차와 흔들림이 있다.
- 실제 목표물의 위치가 지도와 완전히 일치한다고 보장하기 어렵다.
- 충전기나 작업 지점 앞에서는 최종 1-2cm 오차가 중요할 수 있다.
- 목표 yaw를 맞추는 것보다 "목표물과 정면으로 마주 보는 것"이 더 중요한 경우가 많다.

그래서 최종 정차 기준을 map pose가 아니라 AprilTag 상대 pose로 바꾼다. 목표물에 AprilTag를 붙이고, 로봇의 전방 카메라가 그 태그를 보면서 마지막 정렬을 수행한다.

## 전체 구조

전체 흐름은 아래와 같다.

{{< figure src="/images/diagrams/autodrive-precision-arch.svg" alt="Pinky 정밀 주차 전체 구조 — 콘솔이 /wasab/precise_goal로 정밀 목표를 보내면 wasab_robot_agent가 robot_id가 일치하는 로봇으로만 재발행하고, 로봇의 precision node가 NavigateToPose로 Nav2 접근 주행을 하고 AprilTag 검출·TF로 태그 상대 pose를 계산해 /cmd_vel로 저속 PID/servo 정렬을 수행한다" >}}

콘솔은 정밀 목표 명령을 하나 보낸다. 이 명령에는 "Nav2가 먼저 갈 위치"와 "어떤 AprilTag 앞에서 어떻게 멈출지"가 함께 들어 있다.

로봇 쪽 precision node는 먼저 Nav2를 실행한다. Nav2가 접근 위치까지 성공적으로 도착하면, 그 다음부터 AprilTag 기반 정렬을 시작한다.

## 정밀 목표 명령

정밀 주차 명령은 일반 waypoint보다 정보가 조금 더 많다.

```json
{
  "robot_id": 31,
  "goal_id": "dock_a",
  "approach_pose": {"x": 1.20, "y": 0.42, "yaw": 1.57},
  "tag_id": 7,
  "tag_size": 0.06,
  "tag_goal": {"x": 0.25, "y": 0.0, "yaw": 0.0},
  "tolerance": {"x": 0.015, "y": 0.01, "yaw": 0.04},
  "timeout_s": 20.0
}
```

핵심 필드는 네 가지다.

`approach_pose`는 Nav2가 먼저 갈 map 좌표다. 이 위치는 최종 정차 위치가 아니라, AprilTag가 카메라에 보이기 시작하는 근처 위치다. 보통 태그 정면 약 30cm 전후를 목표로 잡는다.

`tag_id`는 최종 정렬에 사용할 AprilTag 번호다. 여러 태그가 보이더라도 이 ID만 기준으로 삼는다.

`tag_goal`은 로봇 기준에서 태그가 어디에 보여야 하는지를 의미한다. 예를 들어 `{"x": 0.25, "y": 0.0, "yaw": 0.0}`은 태그가 로봇 전방 25cm, 중앙, 정면에 보이는 상태를 목표로 한다는 뜻이다.

`tolerance`는 정차 성공으로 인정할 오차 범위다. 위 예시에서는 앞뒤 1.5cm, 좌우 1cm, yaw 0.04rad 이내를 목표로 한다.

## 여러 로봇 중 하나만 실행하는 방식

콘솔은 `/wasab/precise_goal`이라는 공통 토픽으로 명령을 보낸다. 다중 로봇 환경에서는 여러 agent가 이 명령을 볼 수 있다. 하지만 모든 로봇이 동시에 움직이면 안 된다.

그래서 `wasab_robot_agent`가 명령을 필터링한다.

```text
payload.robot_id == 내 robot_id
```

이 조건을 만족하는 agent만 자기 로봇 도메인으로 명령을 재발행한다. 나머지 로봇은 명령을 무시한다.

즉 콘솔은 한 번만 publish하고, 실제 실행은 선택된 로봇 하나만 한다.

## 로봇 쪽 상태머신

로봇 도메인의 precision node는 상태머신으로 동작한다.

{{< figure src="/images/diagrams/autodrive-precision-statemachine.svg" alt="precision node 상태머신 — IDLE에서 명령을 받으면 NAV_TO_APPROACH로 넘어가 approach_pose를 Nav2에 보내고, Nav2가 성공하면 SEARCH_TAG에서 tag_id를 찾고, 태그가 보이면 TAG_SERVO_ALIGN에서 precision node가 직접 /cmd_vel로 저속 정렬하며, tolerance 내에 settle되면 DONE이 된다. 어느 상태에서든 태그 상실·timeout·취소가 발생하면 FAILED로 가고 어떤 경우든 종료 시 /cmd_vel을 zero로 만든다" >}}

먼저 `IDLE` 상태에서 명령을 기다린다. 명령을 받으면 `NAV_TO_APPROACH`로 넘어가고, `approach_pose`를 Nav2 `NavigateToPose` goal로 보낸다.

Nav2가 성공하면 `SEARCH_TAG`로 넘어간다. 이때 목표 `tag_id`가 detector나 TF에서 보이는지 확인한다.

태그가 보이면 `TAG_SERVO_ALIGN` 상태가 된다. 여기서부터는 Nav2가 아니라 precision node가 직접 `/cmd_vel`을 publish하면서 저속 정렬을 한다.

정렬이 성공하면 `DONE`이 된다. 실패하거나 시간이 초과되면 `FAILED`가 된다. 어떤 경우든 종료 시에는 반드시 `/cmd_vel`에 zero를 publish해서 로봇을 멈춘다.

## Nav2의 역할은 "근처까지"

정밀 주차라고 해서 Nav2를 버리는 것은 아니다. 오히려 Nav2는 그대로 사용한다.

Nav2가 맡는 일은 다음과 같다.

- map 기준 경로 계획
- 장애물 회피
- 목표물 근처까지 안정적인 이동
- AprilTag가 카메라 시야에 들어오는 위치까지 접근

현재 기준은 SMAC Planner2D와 Regulated Pure Pursuit 조합이다. goal tolerance는 대략 `xy_goal_tolerance=0.05`, `yaw_goal_tolerance=0.1`에서 시작한다.

중요한 점은 Nav2의 목표가 "정밀 정차"가 아니라는 것이다. Nav2는 태그가 보이는 곳까지 데려다주는 역할을 한다. 마지막 몇 cm는 AprilTag가 담당한다.

## AprilTag 상대 pose를 계산하는 방법

Nav2가 접근 위치에 도착하면, precision node는 목표 AprilTag를 찾는다.

AprilTag detector가 camera frame 기준 pose를 내보내면, TF를 이용해 이 pose를 `base_footprint` 기준으로 변환한다.

최종 제어에서 쓰는 값은 이것이다.

```text
base_footprint 기준 tag pose
```

예를 들어 현재 태그가 이렇게 보인다고 하자.

```text
tag_x   = 0.31 m
tag_y   = -0.03 m
tag_yaw = 0.10 rad
```

우리가 원하는 상태는 아래와 같다.

```text
goal_x   = 0.25 m
goal_y   = 0.00 m
goal_yaw = 0.00 rad
```

그러면 오차는 이렇게 계산된다.

```text
error_x   = 0.31 - 0.25 = +0.06 m
error_y   = -0.03 - 0.00 = -0.03 m
error_yaw = 0.10 - 0.00 = +0.10 rad
```

이 값의 의미는 직관적이다.

- `error_x`가 양수면 태그가 아직 목표보다 멀다. 로봇이 조금 더 전진해야 한다.
- `error_x`가 음수면 태그가 너무 가깝다. 로봇이 후진해야 한다.
- `error_y`가 0이 아니면 태그가 중앙에서 벗어났다.
- `error_yaw`가 0이 아니면 로봇이 태그와 정면으로 맞지 않는다.

단, 실제 detector의 frame 정의에 따라 yaw 부호가 기대와 반대일 수 있다. 그래서 실기에서는 반드시 "오차가 줄어드는 방향으로 움직이는지"부터 확인해야 한다. 방향이 반대라면 gain을 키우는 것이 아니라 adapter의 부호를 고쳐야 한다.

## PID라고 하지만 처음은 단순하게

처음부터 full PID를 넣지 않는다. 1차 구현은 P 제어에 가깝게 시작한다. 이유는 간단하다. frame 부호, 카메라 extrinsic, 태그 pose 안정성이 확인되기 전에는 복잡한 제어기를 넣어도 문제 원인을 분리하기 어렵다.

기본 제어식은 아래처럼 잡는다.

```text
vx = clamp(kx * error_x, -max_vx_back, max_vx)
wz = clamp(kyaw * error_yaw + ky * error_y, -max_wz, max_wz)
```

`vx`는 앞뒤 거리 오차를 줄인다. 태그가 목표보다 멀면 전진하고, 너무 가까우면 후진한다.

`wz`는 회전 속도다. yaw 오차와 좌우 오차를 함께 사용한다. Pinky는 differential drive라 옆으로 직접 이동할 수 없다. 따라서 `error_y`는 lateral 속도로 보내는 대신 회전에 섞어서 태그가 다시 중앙에 오도록 만든다.

초기 파라미터는 보수적으로 잡는다.

```yaml
precision_controller:
  ros__parameters:
    kx: 0.35
    ky: 0.8
    kyaw: 0.9
    max_vx: 0.03
    max_vx_back: 0.02
    max_wz: 0.3
    tol_x: 0.015
    tol_y: 0.01
    tol_yaw: 0.04
    tag_lost_timeout_s: 0.5
    settle_time_s: 0.4
```

실기 첫 테스트에서는 이보다 더 느리게 시작하는 것이 좋다.

```text
max_vx = 0.02 m/s
max_wz = 0.2 rad/s
tag_goal.x = 0.25 m
```

정밀 주차에서 중요한 것은 빠르게 붙는 것이 아니라, 오차가 줄어드는 방향이 맞는지 안전하게 확인하는 것이다.

## 언제 "정차 성공"으로 볼 것인가

오차가 tolerance 안에 한 번 들어왔다고 바로 성공 처리하지 않는다. AprilTag pose는 약간 흔들릴 수 있고, 로봇도 멈추기 직전 미세하게 움직인다.

그래서 조건이 일정 시간 유지되어야 한다.

예를 들어 아래 조건을 모두 만족해야 한다.

```text
abs(error_x)   <= 0.015 m
abs(error_y)   <= 0.010 m
abs(error_yaw) <= 0.040 rad
```

그리고 이 상태가 `settle_time_s`, 예를 들어 0.4초 동안 유지되면 `DONE`으로 판단한다.

완료 시에는 반드시 정지 명령을 낸다.

```text
/cmd_vel = zero
state = DONE
```

실패했을 때도 마찬가지다. 태그를 잃었거나 timeout이 나거나 goal이 취소되면, 먼저 `/cmd_vel`을 zero로 만들어야 한다.

## Nav2와 PID가 동시에 cmd_vel을 내면 안 된다

이 구조에서 중요한 안전 조건이 하나 있다. Nav2와 precision node가 동시에 `/cmd_vel`을 publish하면 안 된다.

그래서 정밀 정렬은 Nav2 goal이 성공한 뒤에만 시작한다.

```text
Nav2 NavigateToPose 성공
  -> SEARCH_TAG
  -> TAG_SERVO_ALIGN
```

Nav2가 아직 경로를 따라가고 있는 동안에는 precision node가 `/cmd_vel`을 직접 publish하지 않는다.

나중에 더 견고한 구조가 필요하면 `cmd_vel mux`를 넣을 수 있다. 하지만 1차 구현은 단순하게 "Nav2 완료 후 servo 시작" 규칙으로 충분하다.

## AprilTag를 어떻게 붙일 것인가

태그의 물리 조건도 중요하다. 제어가 아무리 좋아도 detector pose가 흔들리면 정밀 정차가 흔들린다.

현재 기준은 다음과 같다.

- Family: `tag36h11`
- 태그 패턴 크기: 6cm x 6cm
- detector `tag_size`: `0.06`
- 검은 패턴 바깥 흰 여백: 최소 2-3cm
- 권장 전체 라벨 크기: 약 10cm x 10cm
- 부착 높이: 카메라 렌즈 높이 또는 ±3cm 이내
- 부착면: 수직 벽면, 평평하고 무광에 가까운 표면
- 투명 테이프나 반사 코팅이 패턴 위를 덮지 않게 할 것

거리별로는 이렇게 확인한다.

- 15cm: 너무 가까워 태그가 잘리거나 초점이 흐릴 수 있다.
- 20-25cm: 최종 정차 후보 거리다.
- 30cm: servo 시작 후보 거리다.
- 50cm: 외곽 검출 확인용이다. 6cm 태그가 흔들리면 8cm 태그를 백업으로 비교한다.

## 실기 검증 순서

검증은 한 번에 end-to-end로 하지 않는다. 단계별로 분리해서 본다.

먼저 Nav2 접근만 검증한다. 태그 앞 약 30cm까지 안정적으로 가는지, 태그가 카메라 시야에 들어오는지, 최종 yaw가 얼마나 틀어지는지 기록한다.

그 다음 정지 상태에서 tag detection을 본다. 20cm, 25cm, 30cm, 50cm 거리에서 tag pose가 얼마나 안정적인지 확인한다. 이때 `base_footprint` 기준 `x`, `y`, `yaw` 부호도 같이 확인한다.

그 다음은 servo 단독 테스트다. 로봇을 손으로 태그 근처에 놓고, PID/servo만 켜서 오차가 줄어드는지 본다. 이 단계에서는 속도를 낮게 제한한다.

```text
max_vx = 0.02
max_wz = 0.2
tag_goal.x = 0.25
```

마지막으로 전체 흐름을 검증한다.

```text
precise_goal 발행
  -> Nav2 approach 성공
  -> tag 검색 성공
  -> servo 정렬 시작
  -> tolerance 내 settle
  -> DONE
```

각 단계에서 반드시 확인할 것은 정지 동작이다. `DONE` 후에도 `/cmd_vel`이 zero여야 하고, `FAILED` 후에도 zero여야 한다.

## 핵심은 역할 분리

이 방식의 핵심은 Nav2와 AprilTag PID의 역할을 분리하는 것이다.

{{< figure src="/images/diagrams/autodrive-precision-roles.svg" alt="Nav2와 AprilTag PID의 역할 분리 — Nav2는 지도 기준으로 목표물 근처까지 안전하게 이동하고, AprilTag PID는 목표물 기준 상대 pose로 마지막 cm 단위 정렬을 담당한다. 결국 Nav2로 가까이 가고 AprilTag로 정확히 멈추는 구조다" >}}

Nav2는 넓은 공간에서의 이동 문제를 풀고, AprilTag PID는 목표물 앞에서의 정밀 정차 문제를 푼다. 두 문제를 억지로 하나의 controller에 넣기보다, 각자 잘하는 구간을 나누는 쪽이 단순하고 디버깅하기 쉽다.

그래서 Pinky의 정밀 주차는 "Nav2로 가까이 가고, AprilTag로 정확히 멈추는" 구조가 된다.
