# Nav2 Costmap / AMCL 개념 정리 — 2026-06-30

## 1. Costmap이란?

자율주행에서 **costmap**은 로봇 주변 또는 지도 위 공간을 격자로 나누고, 각 칸에
“지나가기 위험한 정도”를 비용값으로 표현한 지도다.

즉, 단순히 장애물이 있다/없다만 보는 것이 아니라, 장애물과 얼마나 가까운지에 따라
로봇이 선호하거나 피해야 할 정도를 숫자로 만든다.

| 비용 | 의미 |
|---:|---|
| 낮은 값 | 지나가기 좋음 |
| 높은 값 | 장애물에 가까워 위험함 |
| 최대값 | 장애물 또는 통과 불가 영역 |
| unknown | 모르는 영역. 설정에 따라 통과 가능/불가가 달라짐 |

예를 들어 벽 자체는 최고 비용이고, 벽 바로 옆은 높은 비용이며, 벽에서 충분히 떨어진
복도 중앙은 낮은 비용이 된다. 그래서 planner/controller는 벽을 스치듯 지나가기보다
비용이 낮은 안전한 경로를 선호한다.

## 2. Global costmap

**Global costmap**은 목표 지점까지 갈 전체 경로를 계획할 때 쓰는 costmap이다.

- 주 사용처: Global Planner
- 역할: 현재 위치에서 목표까지 큰 경로를 찾음
- 범위: 보통 전체 map 또는 넓은 영역
- 좌표계: 보통 `map`
- 주요 입력:
  - SLAM으로 만든 static map
  - 고정 장애물 정보
  - inflation layer

질문으로 표현하면:

> “목표까지 어느 길로 갈까?”

예를 들어 로봇이 복도 끝 방으로 가야 할 때, global costmap은 건물 지도 전체를 보고
복도를 따라가고, 어느 지점에서 회전할지 같은 큰 경로를 잡는다.

## 3. Local costmap

**Local costmap**은 로봇 바로 주변의 실시간 장애물 회피와 짧은 움직임 제어에 쓰는
costmap이다.

- 주 사용처: Local Controller
- 역할: global path를 따라가면서 지금 당장 충돌하지 않게 움직임
- 범위: 로봇 주변의 작은 창
- 좌표계: 보통 `odom`
- 주요 입력:
  - LiDAR `/scan`
  - depth camera 등 근거리 센서
  - inflation layer

질문으로 표현하면:

> “지금 당장 어떻게 움직여야 충돌하지 않을까?”

예를 들어 global path는 복도 중앙으로 가라고 해도, 복도에 사람이 서 있으면 local
costmap이 그 장애물을 반영하고 controller가 회피 속도 명령을 만든다.

## 4. Global costmap과 local costmap 차이

| 항목 | Global costmap | Local costmap |
|---|---|---|
| 목적 | 전체 경로 계획 | 실시간 장애물 회피 |
| 사용하는 쪽 | Planner | Controller |
| 범위 | 넓음, 보통 전체 map | 좁음, 로봇 주변 |
| 기준 좌표계 | 보통 `map` | 보통 `odom` |
| 업데이트 성격 | 비교적 느려도 됨 | 빠르게 갱신 필요 |
| 주요 장애물 | 벽, 고정 구조물, 지도 장애물 | 근거리 동적 장애물 |
| 핵심 질문 | 어느 길로 갈까? | 지금 어떻게 움직일까? |

요약하면, global costmap은 **목표까지의 큰길을 찾는 지도**이고, local costmap은
**그 길을 따라가면서 눈앞의 장애물을 피하는 지도**다.

WaSaB/Pinky 기준으로는 global costmap이 SLAM map/AMCL 기준의 `map` 위에서
웨이포인트까지 경로를 만들고, local costmap은 LiDAR로 로봇 주변 장애물을 보면서
실제 주행 명령을 안전하게 조정한다.

## 5. AMCL이란?

**AMCL**은 **Adaptive Monte Carlo Localization**의 약자다. 로봇이 이미 가지고 있는
지도 위에서 현재 자신이 어디에 있는지를 추정하는 위치추정 알고리즘이다.

쉽게 말하면:

> AMCL = 저장된 지도 + LiDAR 관측 + odometry를 이용해 로봇의 현재 위치를 `map`
> 좌표계에서 계속 맞춰주는 기능

바퀴 odometry만 쓰면 시간이 갈수록 위치가 밀린다. 바퀴가 미끄러지거나 wheel radius,
wheel separation, 회전량이 조금만 틀려도 오차가 누적된다. AMCL은 LiDAR로 현재 보이는
벽/장애물 모양을 기존 map과 비교해서 로봇의 실제 위치를 보정한다.

## 6. AMCL이 사용하는 입력

- 저장된 map: SLAM으로 만든 지도
- LiDAR scan: 현재 로봇 주변에서 보이는 벽/장애물
- odometry: 로봇이 대략 얼마나 움직였는지
- initial pose: 초기 위치 추정값. 보통 RViz의 `2D Pose Estimate`로 지정

## 7. AMCL이 내보내는 출력

- `/amcl_pose`: `map` 기준 로봇 위치 추정값
- `map -> odom` TF: odom 좌표계를 map 좌표계에 맞추는 보정 transform

ROS/Nav2에서는 보통 프레임 책임이 아래처럼 나뉜다.

```text
map -> odom -> base_footprint
```

- `odom -> base_footprint`: wheel odometry 또는 EKF가 담당
- `map -> odom`: AMCL이 담당
- 결과적으로 `map -> base_footprint`가 지도상 로봇 위치가 됨

## 8. Odometry와 AMCL의 차이

| 항목 | Odometry | AMCL |
|---|---|---|
| 기준 | 바퀴/IMU로 얼마나 움직였는지 | 지도와 LiDAR 관측이 얼마나 맞는지 |
| 강점 | 짧은 시간에는 부드럽고 빠름 | 누적 drift를 map 기준으로 보정 |
| 약점 | 시간이 갈수록 drift 누적 | 초기 위치나 map 품질이 나쁘면 틀릴 수 있음 |
| 담당 프레임 | `odom -> base_footprint` | `map -> odom` |

비유하면 odometry는 “바퀴 기준으로 이만큼 움직였을 것 같다”이고, AMCL은 “지금 LiDAR로
보이는 벽 모양을 지도와 맞춰보니 실제로는 여기다”라고 교정하는 역할이다.

WaSaB/Pinky 기준으로는 AMCL이 안정적으로 잡혀야 Nav2가 웨이포인트를 `map` 좌표계에서
정확히 찾아가고, GUI도 `/amcl_pose` 또는 `map -> base_footprint` TF를 구독해서 로봇
위치를 표시할 수 있다.
