---
title: "자율주행 로봇은 길을 어떻게 보고, 자기 위치를 어떻게 알까 — Costmap과 AMCL 정리"
date: 2026-06-30
tags: ["auto-drive", "ros2", "nav2", "costmap", "amcl", "slam", "localization", "wasab", "pinky"]
categories: ["robotics"]
summary: "Nav2를 처음 다룰 때 계속 마주치는 global/local costmap과 AMCL. 이름은 어렵지만 역할은 직관적이다. '어느 길로 갈까'와 '나는 지금 어디 있나'라는 두 질문으로 두 개념을 정리한다."
draft: false
ShowToc: true
TocOpen: true
---

자율주행 로봇을 처음 다루다 보면 `global costmap`, `local costmap`, `AMCL` 같은 용어가 계속 나온다. 이름만 보면 어렵지만, 실제 역할은 꽤 직관적이다.

로봇이 목적지까지 가려면 두 가지를 계속 해결해야 한다.

1. **어느 길로 갈 것인가?**
2. **나는 지금 지도 위 어디에 있는가?**

이 글에서는 Nav2 기준으로 이 두 질문에 답하는 핵심 개념인 **costmap**과 **AMCL**을 정리한다. 실제로 이 개념들이 작은 실내 로봇에서 어떻게 맞물려 돌아가는지는 후속 글 [AMCL yaw 측위 오차 추적기](../amcl-yaw-측위오차-추적기-가설반박부터-환경개선까지/)에서 실측과 함께 다룬다.

아래는 이 개념들이 실제로 동작하는 현장 — WaSaB 다중 로봇 통합 관제 화면이다. 왼쪽이 `map` 좌표계 위의 실시간 위치맵, 오른쪽이 천정 카메라 뷰다.

{{< figure src="/images/auto_drive/wasab-control-gui.png" alt="WaSaB 통합 제어 및 모니터링 시스템 — 왼쪽 실시간 위치맵에 분리수거장·교무실·교실 등 구역과 로봇 위치가 표시되고, 오른쪽 천정뷰에 실제 로봇 두 대가 검출되어 좌표가 오버레이된다" caption="WaSaB 통합 관제 화면 — costmap·AMCL이 결국 만들어내는 것은 이 한 장의 '지도 위 로봇 위치'다" >}}

---

## 1. Costmap: 위험도를 숫자로 표현한 지도

먼저 costmap부터 보자.

**Costmap은 공간을 격자로 나누고, 각 칸에 "지나가기 위험한 정도"를 비용으로 표시한 지도**다.

즉, 로봇은 단순히 "여기는 장애물, 여기는 빈 공간"만 보는 것이 아니다. 벽이나 장애물에 얼마나 가까운지까지 고려해서, 더 안전한 길을 고르도록 만든다.

| 비용 | 의미 |
|---:|---|
| 낮은 값 | 지나가기 좋음 |
| 높은 값 | 장애물에 가까워 위험함 |
| 최대값 | 장애물 또는 통과 불가 |
| unknown | 아직 모르는 영역 |

예를 들어 벽 자체는 통과할 수 없으므로 가장 높은 비용이 된다. 벽 바로 옆도 위험하므로 높은 비용을 가진다. 반대로 복도 중앙처럼 장애물에서 떨어진 곳은 낮은 비용을 가진다.

그래서 로봇은 벽을 스치듯 지나가기보다, 가능하면 비용이 낮은 경로를 선택한다.

---

## 2. Global costmap: 목적지까지의 큰길을 찾는 지도

**Global costmap**은 목적지까지 가는 전체 경로를 계획할 때 쓰인다.

질문으로 표현하면 이렇다.

> "목표까지 어느 길로 갈까?"

Global costmap은 보통 전체 지도 또는 넓은 영역을 기준으로 한다. 저장된 map, 고정 장애물, 벽, inflation layer 등을 보고 목표 지점까지의 큰 경로를 만든다.

예를 들어 로봇이 복도 끝 방으로 가야 한다면, global costmap은 전체 지도를 보고 "이 복도를 따라가고, 저 지점에서 오른쪽으로 돌자" 같은 큰 계획을 세운다.

| 항목 | Global costmap |
|---|---|
| 역할 | 전체 경로 계획 |
| 주로 쓰는 쪽 | Global Planner |
| 범위 | 넓음, 보통 전체 map |
| 기준 좌표계 | 보통 `map` |
| 주로 보는 것 | 벽, 고정 장애물, 지도 구조 |

---

## 3. Local costmap: 지금 눈앞의 장애물을 피하는 지도

**Local costmap**은 로봇 주변의 짧은 범위를 실시간으로 본다.

질문으로 표현하면 이렇다.

> "지금 당장 어떻게 움직여야 충돌하지 않을까?"

Global planner가 큰길을 정해주더라도, 실제 주행 중에는 변수가 많다. 사람이 지나가거나, 박스가 놓여 있거나, 지도에는 없던 장애물이 나타날 수 있다.

이때 local costmap은 LiDAR나 depth camera 같은 센서로 로봇 주변을 계속 갱신한다. 그리고 local controller는 이 정보를 이용해 속도 명령을 만든다.

예를 들어 global path는 복도 중앙으로 가라고 하지만, 복도 중간에 사람이 서 있다면 local costmap이 그 사람을 장애물로 반영하고, 로봇은 잠깐 옆으로 피해서 간다.

| 항목 | Local costmap |
|---|---|
| 역할 | 실시간 장애물 회피 |
| 주로 쓰는 쪽 | Local Controller |
| 범위 | 좁음, 로봇 주변 |
| 기준 좌표계 | 보통 `odom` |
| 주로 보는 것 | LiDAR scan, 근거리 동적 장애물 |

---

## 4. Global costmap과 local costmap의 차이

두 costmap의 차이는 한 문장으로 정리할 수 있다.

> Global costmap은 **목표까지의 큰길**을 찾고, local costmap은 **그 길을 따라가며 눈앞의 장애물**을 피한다.

표로 보면 더 명확하다.

| 항목 | Global costmap | Local costmap |
|---|---|---|
| 목적 | 전체 경로 계획 | 실시간 장애물 회피 |
| 사용하는 쪽 | Planner | Controller |
| 범위 | 넓음 | 좁음 |
| 기준 좌표계 | 보통 `map` | 보통 `odom` |
| 업데이트 성격 | 비교적 느려도 됨 | 빠르게 갱신 필요 |
| 핵심 질문 | 어느 길로 갈까? | 지금 어떻게 움직일까? |

실제 로봇에서는 둘 중 하나만으로는 부족하다. Global costmap만 있으면 큰길은 알지만 눈앞의 장애물을 피하기 어렵고, local costmap만 있으면 당장 충돌은 피할 수 있어도 목적지까지의 큰 경로를 알기 어렵다.

---

## 5. AMCL: 지도 위에서 "내 위치"를 찾는 알고리즘

이제 AMCL을 보자.

**AMCL**은 **Adaptive Monte Carlo Localization**의 약자다. 쉽게 말하면, 로봇이 이미 가지고 있는 지도 위에서 **자신의 현재 위치를 추정하는 알고리즘**이다.

로봇은 바퀴 odometry만으로도 "내가 어느 정도 움직였는지"를 알 수 있다. 하지만 바퀴는 미끄러질 수 있고, 바닥 상태나 회전 오차 때문에 위치가 조금씩 밀린다. 이 오차는 시간이 지날수록 누적된다.

AMCL은 이 문제를 줄이기 위해 LiDAR로 본 현재 주변 모양을 저장된 지도와 비교한다.

즉:

> "바퀴 기준으로는 여기쯤 왔을 것 같고, LiDAR로 보이는 벽 모양을 지도와 맞춰보니 실제 위치는 여기다."

이 역할을 AMCL이 한다.

---

## 6. AMCL이 사용하는 것

AMCL은 보통 다음 정보를 함께 사용한다.

| 입력 | 의미 |
|---|---|
| 저장된 map | SLAM으로 만든 지도 |
| LiDAR scan | 현재 로봇 주변에서 보이는 벽/장애물 |
| odometry | 로봇이 대략 얼마나 움직였는지 |
| initial pose | 처음 위치 추정값. RViz의 `2D Pose Estimate`로 지정하는 경우가 많음 |

AMCL은 이 정보를 바탕으로 지도 위에서 로봇의 위치를 계속 보정한다.

---

## 7. AMCL이 내보내는 것 — 프레임 책임 분담

Nav2에서 AMCL이 잘 동작하면 보통 두 가지를 볼 수 있다.

| 출력 | 의미 |
|---|---|
| `/amcl_pose` | `map` 기준 로봇 위치 추정값 |
| `map → odom` TF | odom 좌표계를 map 좌표계에 맞추는 보정 transform |

ROS/Nav2에서는 프레임 구조가 보통 `map → odom → base_footprint`로 나뉘고, 각 구간의 책임이 다르다.

{{< figure src="/images/diagrams/autodrive-tf-tree.svg" alt="ROS TF 프레임 체인 — map에서 odom 구간은 AMCL이 지도 기준 누적 drift를 보정하고, odom에서 base_footprint 구간은 휠 오도메트리 또는 EKF가 짧은 시간의 움직임을 추정하며, 둘이 합쳐져 map에서 base_footprint, 즉 지도 위 로봇 위치가 만들어진다" >}}

즉, odometry는 짧은 시간 동안 부드럽게 움직임을 추정하고, AMCL은 지도 기준으로 누적 오차를 보정한다. 둘이 합쳐져서 최종적으로 `map → base_footprint`, 즉 지도 위 로봇 위치가 만들어진다.

---

## 8. Odometry와 AMCL은 경쟁 관계가 아니다

처음에는 odometry와 AMCL을 둘 중 하나만 쓰는 것으로 오해하기 쉽다. 하지만 실제로는 역할이 다르다.

| 항목 | Odometry | AMCL |
|---|---|---|
| 기준 | 바퀴/IMU로 얼마나 움직였는지 | 지도와 LiDAR 관측이 얼마나 맞는지 |
| 장점 | 짧은 시간에는 빠르고 부드러움 | 누적 drift를 map 기준으로 보정 |
| 약점 | 시간이 갈수록 drift 누적 | 지도 품질이나 초기 위치가 나쁘면 틀릴 수 있음 |
| 담당 TF | `odom → base_footprint` | `map → odom` |

그래서 좋은 자율주행 시스템은 보통 둘을 함께 쓴다.

1. Odometry/EKF가 짧은 시간의 움직임을 부드럽게 추정한다.
2. AMCL이 LiDAR와 map을 비교해 위치를 지도 기준으로 보정한다.
3. Planner와 controller가 costmap을 보고 경로와 속도 명령을 만든다.

> 💡 "지도 품질이 나쁘면 AMCL이 틀릴 수 있다"는 약점은 단순한 경고가 아니다. 후속 글에서 **맵이 180° 대칭이면 AMCL의 heading(yaw)이 흔들린다**는 것을 실측으로 보게 된다.

---

## 9. 전체 흐름으로 보면

Nav2 자율주행을 큰 흐름으로 보면 이렇게 정리할 수 있다.

{{< figure src="/images/diagrams/autodrive-nav2-flow.svg" alt="Nav2 자율주행 전체 흐름 — 저장된 map과 LiDAR와 odometry가 AMCL로 들어가 map 기준 로봇 위치를 만들고, 그 위치를 토대로 global costmap이 global planner로 전체 경로를, local costmap이 local controller로 실시간 속도 명령을 만든다" >}}

정리하면:

- **AMCL**은 로봇이 지도 위 어디에 있는지 추정한다.
- **Global costmap**은 목표까지의 큰길을 찾는 데 쓰인다.
- **Local costmap**은 눈앞의 장애물을 피하며 실제로 움직이는 데 쓰인다.

이 세 가지가 맞물려야 로봇은 "내가 어디 있는지 알고", "어디로 가야 하는지 알고", "지금 어떻게 움직여야 안전한지" 판단할 수 있다.

WaSaB/Pinky 같은 작은 실내 로봇에서도 구조는 같다. SLAM으로 만든 map 위에서 AMCL이 현재 위치를 잡고, global costmap이 웨이포인트까지의 경로를 만들고, local costmap이 LiDAR로 주변 장애물을 보면서 실제 주행을 조정한다.

---

## 한 줄 요약

> **AMCL은 로봇의 현재 위치를 지도 위에 맞춰주는 역할이고, costmap은 그 위치에서 어디로 가면 안전한지를 비용으로 표현한 지도다. Global costmap은 큰길, local costmap은 눈앞의 회피를 담당한다.**

개념이 잡혔다면, 이 개념들이 실제 1m×2m 소형 실내에서 어떻게 무너지고 어떻게 고쳐졌는지 — [AMCL yaw 측위 오차 추적기](../amcl-yaw-측위오차-추적기-가설반박부터-환경개선까지/)로 이어진다.
