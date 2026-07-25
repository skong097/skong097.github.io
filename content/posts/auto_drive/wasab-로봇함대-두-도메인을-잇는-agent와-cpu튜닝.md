---
title: "로봇 함대를 한 화면에서 — 두 ROS 도메인을 잇는 agent를 만들고 CPU를 70% 깎기까지"
date: 2026-07-25
tags: ["auto-drive", "ros2", "multi-robot", "fleet", "ros-domain", "agent", "bridge", "nav2", "amcl", "cpu-tuning", "wasab", "pinky"]
categories: ["robotics"]
summary: "여러 대의 Pinky를 한 관제 콘솔에서 다루기 위해, 로봇마다 ROS 도메인을 격리하고 그 사이를 잇는 2-context agent를 만들었다. agent는 로봇 상태를 heartbeat로 올리고 콘솔 명령을 로봇으로 중계하며 재측위·도킹 세션을 관리한다. 그리고 이 agent의 CPU를 상시 TransformListener 제거로 약 70~75% 줄였다. 함대 구현 → agent 도메인 브리지 설계 → CPU 튜닝까지의 경험담."
draft: false
ShowToc: true
TocOpen: true
---

학교 환경에서 여러 대의 Pinky 로봇을 **한 관제 콘솔에서** 움직이려 했다.
순찰을 돌리고, 정밀 도킹으로 충전대에 붙이고, 위치가 틀어지면 재측위하고,
위급하면 전체를 세운다 — 이 모든 걸 한 화면에서.

그런데 로봇이 여러 대가 되는 순간 가장 먼저 부딪힌 건 알고리즘이 아니라 **통신**이었다.
같은 네트워크에 여러 로봇의 ROS 2 토픽이 그대로 흘러다니면, 로봇 A의 `/cmd_vel`이
로봇 B에게도 보이고 `/amcl_pose`·`/scan`이 서로 섞인다. 이 글은 그 문제를 도메인 격리로
끊고, 끊어진 두 세계를 다시 잇는 **agent**를 만들고, 그 agent를 튜닝한 기록이다.

세 부분으로 나눠 적는다 — (1) 함대 시스템을 어떻게 구성했는지, (2) 두 도메인을 잇는
agent를 어떻게 설계했는지, (3) 그 agent의 CPU를 어떻게 깎았는지.

---

## 1. 함대 시스템 — 도메인을 나누고, 콘솔로 모은다

WaSaB는 **2머신** 구조다. 콘솔 PC(노트북)가 통합 관제를 맡고, Pinky 로봇 함대(RPi5)가
자율주행을 맡는다. 핵심은 **도메인 분리**다.

- **콘솔 도메인 50** — 통합 관제 콘솔(PyQt6 GUI), 사용자 웹앱(FastAPI), 천정 오버헤드 CCTV.
- **로봇별 도메인 51 / 52 / 53 / 54** — 각 로봇이 자기 도메인 안에서 Nav2 자율주행,
  AMCL 측위, AprilTag 정밀 도킹, 순찰 코디네이터를 돌린다.

로봇마다 도메인을 다르게 주면 로봇 간 토픽이 물리적으로 섞이지 않는다. 대신
"그럼 콘솔은 로봇 상태를 어떻게 보고, 명령은 어떻게 내리나?"라는 문제가 남는데,
그걸 푸는 게 다음 장의 agent다.

{{< figure src="/images/diagrams/autodrive-wasab-fleet-arch.svg" alt="WaSaB 다중로봇 관제 시스템 구조. 콘솔 도메인 50에는 통합 관제 콘솔 GUI, 사용자 웹앱, 오버헤드 CCTV가 있고, 로봇 함대는 로봇별 도메인 51에서 54로 분리되어 각 로봇이 Nav2 자율주행, AMCL 측위, AprilTag 도킹, 순찰 코디네이터를 실행한다. 각 로봇에서 실행되는 wasab_robot_agent가 두 도메인을 잇는 브리지로, 로봇 상태를 heartbeat와 이벤트로 콘솔에 올리고 콘솔의 cmd_vel과 모드 명령을 로봇으로 내려보낸다." caption="agent만이 로봇 도메인과 콘솔 도메인 50을 동시에 붙잡는 유일한 프로세스다" >}}

각 로봇의 자율주행 스택은 앞선 글들에서 다룬 것을 그대로 얹었다 — Nav2로 지도 기준
경로를 만들고([Nav2·costmap·AMCL 입문](../nav2-costmap-amcl-자율주행-위치추정-입문/)),
AMCL로 위치를 추정하고, 마지막 몇 cm는 AprilTag PID로 붙인다
([정밀 도킹 성공 기록](../nav2-apriltag-pid-정밀도킹-성공기록/)). 함대 관점에서 새로 더한 것은
그 위에 **순찰 코디네이터**(웨이포인트 순회 + 로봇 간 양보)를 올린 것이다.

아래는 순찰 한 사이클을 처음부터 끝까지 돌린 것이다. 웨이포인트를 따라 돌고,
출발지로 복귀한다.

{{< figure src="/images/auto_drive/wasab-patrol-fullcycle-2x.gif" alt="Pinky 로봇이 순찰 웨이포인트를 한 바퀴 순회하고 출발 지점으로 복귀하는 전체 순찰 사이클 데모, 2배속" caption="순찰 풀사이클 (2배속) — 웨이포인트 순회 후 복귀" >}}

같은 장면을 실제 속도로 보면 로봇이 각 지점에서 얼마나 신중하게 감·가속하는지 보인다.

{{< figure src="/images/auto_drive/wasab-patrol-fullcycle-1x.gif" alt="같은 순찰 풀사이클을 실제 속도로 재생한 데모, 1배속" caption="같은 순찰 사이클 (1배속, 실제 속도)" >}}

---

## 2. agent 구축 — 두 도메인을 잇는 2-Context 브리지

도메인을 나눈 대가로, 콘솔은 로봇의 토픽을 볼 수 없게 됐다. 이 간극을 메우는 게
`wasab_robot_agent`다. **로봇마다 하나씩** 실행되며, 두 개의 ROS 도메인을 동시에
붙잡는 **유일한** 프로세스다.

### 2.1 왜 하나의 노드로 두 도메인을 붙잡나

ROS 2에서 노드는 보통 하나의 도메인에 속한다. 하지만 agent는 로봇 도메인의
`/amcl_pose`·배터리를 읽으면서 동시에 콘솔 도메인 50에 `heartbeat`를 발행해야 한다.
그래서 하나의 프로세스 안에 **두 개의 `rclpy.Context`**를 띄우고, 각각 별도 executor
스레드에서 돌린다.

```python
# robot_ctx = 로봇 로컬 도메인(ROS_DOMAIN_ID 그대로)
self._robot_ctx = rclpy.Context()
rclpy.init(context=self._robot_ctx)
# console_ctx = 콘솔 도메인 50
self._console_ctx = rclpy.Context()
rclpy.init(context=self._console_ctx, domain_id=self.console_domain)

# 노드 이름에 로봇 id를 붙여 유일화 —
# 여러 로봇 agent가 공유 콘솔 도메인에 등록하므로 충돌 방지 필수
rn = Node(f"wasab_agent_robot_{self.id}", context=self._robot_ctx)
cn = Node(f"wasab_agent_console_{self.id}", context=self._console_ctx)
```

콘솔 도메인은 여러 로봇의 agent가 **공유**한다. 그래서 노드 이름에 로봇 id를 붙여
유일화하지 않으면 도메인 안에서 같은 이름이 충돌한다.

### 2.2 핵심 규칙 — 콜백은 큐에 넣기만, 발행은 타이머가

두 컨텍스트를 한 프로세스에서 돌릴 때 가장 위험한 건 **크로스-컨텍스트 발행**이다.
콘솔 executor 스레드에서 받은 명령을 그 자리에서 로봇 도메인 publisher로 쏘면,
publisher가 자기 것이 아닌 스레드에서 호출되어 경쟁 상태가 생긴다.

그래서 규칙을 하나로 못 박았다 — **console_ctx 콜백은 스레드 안전 큐에 넣기만 하고,
실제 로봇 도메인 발행은 robot_ctx의 타이머가 자기 스레드에서만 한다.**

{{< figure src="/images/diagrams/autodrive-wasab-agent-bridge.svg" alt="wasab_robot_agent의 2-context 브리지 내부 구조. 왼쪽 console_ctx는 콘솔 도메인 50에 붙어 콘솔의 cmd_vel과 cmd_mode를 구독해 스레드 안전 큐에 넣기만 하고, heartbeat를 2Hz로 발행하며 재측위·도킹 이벤트 큐를 비워 발행한다. 오른쪽 robot_ctx는 로봇 로컬 도메인에 붙어 amcl_pose와 battery를 구독하고, 20Hz drain 타이머가 큐를 비워 로컬 cmd_vel로 재발행하며 0.3초 watchdog으로 명령이 끊기면 정지시킨다. 핵심 규칙은 console_ctx 콜백은 큐에 넣기만 하고 실제 발행은 robot_ctx 타이머가 자기 컨텍스트 스레드에서만 수행한다는 것이다." caption="명령은 왼→오, 이벤트는 오→왼. 어느 쪽이든 실제 발행은 자기 컨텍스트 타이머에서만" >}}

명령 경로는 이렇게 흐른다.

- 콘솔이 `/robot_<id>/cmd_vel`을 보낸다 → console_ctx 콜백이 `_to_robot` 큐에 **넣기만** 한다.
- robot_ctx의 **20Hz drain 타이머**가 큐를 비워 로봇 로컬 `/cmd_vel`로 재발행한다.
- 명령이 **0.3초** 동안 끊기면 watchdog이 zero velocity를 발행해 로봇을 세운다.

```python
ROBOT_DRAIN_HZ = 20.0     # 큐 drain + watchdog (명령 응답성)
CMD_VEL_TIMEOUT_S = 0.3   # 이 시간 명령 없으면 정지
HEARTBEAT_HZ = 2.0        # 콘솔로 로봇 상태 보고
```

반대 방향(로봇 → 콘솔)도 같은 원리다. robot_ctx가 재측위·도킹 이벤트를 큐에 넣으면,
console_ctx의 heartbeat tick이 그 큐를 비워 콘솔 도메인으로 발행한다. `_pose`·배터리·
모드 같은 상태값은 `_lock`으로 보호되는 스냅샷에 담아, 발행하는 쪽은 **읽기만** 한다.

### 2.3 heartbeat와 QoS — 잃어도 되는 것, 잃으면 안 되는 것

agent는 **2Hz**로 `/robots/heartbeat`를 발행해 콘솔 화면에 로봇 상태를 계속 갱신한다.
heartbeat는 주기적으로 다시 오므로 한두 개 놓쳐도 무방하다 → **BEST_EFFORT**.
반면 재측위·도킹 성공 같은 **원샷 이벤트**는 한 번 놓치면 콘솔이 상태를 영영 모른다
→ **RELIABLE**. QoS를 이벤트 성격에 맞춰 갈랐다.

```python
def _hb_qos():                     # heartbeat: 주기적 → 잃어도 됨
    q = QoSProfile(depth=10)
    q.reliability = QoSReliabilityPolicy.BEST_EFFORT
    return q

def _reloc_event_qos():            # 원샷 이벤트 → 드롭 방지
    q = QoSProfile(depth=10)
    q.reliability = QoSReliabilityPolicy.RELIABLE
    return q
```

### 2.4 세션 관리 — 재측위와 도킹

agent는 단순 relay를 넘어 **세션**을 관리한다. 콘솔이 "재측위 시작"을 누르면 agent가
detector 서브프로세스를 띄우고, `/initialpose`가 AMCL에 반영되는 걸 감지하면
detector를 **즉시 종료**한다(CPU 회수). 태그가 안 잡히면 백스톱 타임아웃으로 자동 종료한다.

```python
DETECTOR_TIMEOUT_S = 30.0     # 재측위 detector 자동종료 백스톱
DETECTOR_STOP_GRACE_S = 1.5   # 성공 후 kill 유예 — /initialpose가 AMCL에 flush될 시간
DOCK_STANDOFF_M = 0.5         # 태그 정면 접근 거리
DOCK_TIMEOUT_S = 90.0         # dock 전체 백스톱(Nav2 접근 + 서보 여유)
```

재측위가 성공하는 순간 — 흩어져 있던 파티클 구름이 한 점으로 수렴한다.

{{< figure src="/images/auto_drive/wasab-relocalize-success-2x.gif" alt="재측위 명령 후 AMCL 파티클 구름이 한 지점으로 수렴하며 로봇 위치가 잡히는 재측위 성공 순간, 2배속" caption="재측위 성공 — initialpose 반영과 동시에 detector 종료" >}}

여러 로봇을 차례로 재측위하는 것도 콘솔에서 그대로 된다.

{{< figure src="/images/auto_drive/wasab-relocalize-multi-2x.gif" alt="콘솔에서 여러 로봇을 연속으로 재측위해 각 로봇의 위치를 차례로 다시 잡는 복수 재측위 데모, 2배속" caption="복수 재측위 — 함대 각 로봇을 콘솔에서 순차 재측위" >}}

도킹도 마찬가지로 agent가 세션을 연다 — Nav2로 접근점까지 데려가고, AprilTag PID가
마지막 정렬을 하며, 성공·실패 이벤트를 콘솔로 올린다. 아래는 순찰을 마친 로봇이
홈(충전대)으로 복귀해 도킹하는 장면이다.

{{< figure src="/images/auto_drive/wasab-home-docking-2x.gif" alt="순찰을 마친 Pinky 로봇이 홈 충전대로 복귀해 AprilTag를 보며 정밀 도킹하는 데모, 2배속" caption="홈 복귀 도킹 (2배속) — Nav2 접근 후 AprilTag PID 정렬" >}}

{{< figure src="/images/auto_drive/wasab-home-docking-1x.gif" alt="같은 홈 복귀 도킹을 실제 속도로 재생한 데모, 1배속" caption="같은 홈 복귀 도킹 (1배속, 실제 속도)" >}}

---

## 3. 튜닝 경험담 — agent의 CPU를 70% 깎다

시스템이 돌아가기 시작하자 다음 질문은 "이게 RPi5 위에서 감당 가능한가"였다.
로봇 `pinky`에서 `bringup`·`AMCL`·`Nav2`·`agent` 네 영역의 CPU·메모리를 측정했다.

### 3.1 측정 조건

| 항목 | 값 |
|---|---|
| 호스트 | `raspi` (`aarch64`), 4 logical CPUs |
| 커널 | Linux `6.8.0-1040-raspi` |
| 메모리 | 총 3,784 MiB |
| 도구 | `pidstat -u -r`, `mpstat`, `free` |
| 표본 | 1초 간격 12회 |

프로세스 CPU `100%`는 코어 하나를 완전히 쓰는 값이다. 4코어이므로 합계 `400%`가
전체 용량이다. 임무 단계를 통제하지 않은 관측값이라 모듈 단독 벤치마크는 아니다.

### 3.2 네 영역 CPU

| 영역 | 평균 프로세스 CPU | 4코어 대비 | RSS | 역할 |
|---|---:|---:|---:|---|
| Bringup | 22.40% | 5.60% | 79.1 MiB | 모터·엔코더·odometry·TF |
| AMCL | 16.24% | 4.06% | 47.3 MiB | LiDAR·지도 측위 |
| **Nav2** (8개 프로세스) | **133.29%** | **33.32%** | 401.2 MiB | 계획·제어·행동·평활화 |
| **Agent** | **9.83%** | **2.46%** | 77.7 MiB | 도메인 브리지·임무 중계 |
| 합계 | 181.76% | 45.44% | 605.3 MiB | — |

한눈에 드러난 건 **Nav2가 압도적**이라는 것이다(네 영역 CPU의 73.3%). agent는 5.4%로
가장 작다. 그런데 이 9.83%조차 처음부터 이랬던 건 아니다.

### 3.3 keeper — 상시 TransformListener 제거 (`/tf` → `/amcl_pose`)

튜닝 전 agent의 robot_ctx는 약 **30%** CPU를 먹었다. 프로파일을 떠 보니 그 CPU의
약 **85%가 좌표 계산이 아니라**, 35~55Hz로 쏟아지는 `/tf`가 Python executor의
wait-set을 **끊임없이 깨우는 비용**이었다. agent는 pose 한 개가 필요했을 뿐인데,
상시 `TransformListener`를 두고 매 `/tf`마다 깨어나고 있었다.

원인을 확인하려고 bringup을 잠깐 세워 `/tf` 입력을 끊자 agent CPU가 30% → 10%로
떨어졌다 — `/tf` wake-up이 진범이라는 직접 증거였다.

그래서 pose 소스를 상시 `TransformListener` 대신 **`/amcl_pose` 구독**으로 바꿨다.
필요한 저빈도 pose만 받고, 재측위 반영은 `/initialpose`로 감지한다.

| 지표 | 변경 전 | 변경 후 |
|---|---:|---:|
| robot_ctx CPU | 약 30% | 7.5 ~ 9% |
| 정량 효과 | — | **-21~-22.5%p, 약 70~75% 감소** |

바꾼 뒤 agent를 켠 상태로 도킹 8→7→9번을 완주했다. 7월 25일 실측 9.83%도 이 범위와
일치한다. 최근 2주 튜닝 중 가장 명확한 **keeper**다.

### 3.4 정직하게 기각한 실험들

효과가 있을 것 같았지만 실측이 아니라고 답한 실험도 기록한다. **측정 없이 채택하지
않는다**는 원칙을 지켰다.

| 영역 | 튜닝 | 변경 전 → 후 | 판정 |
|---|---|---|---|
| Nav2 | controller 20→10 Hz | 120.63% → 123.90% (**+3.27%p**) | 효과 없음·원복 |
| Nav2 | local costmap 10→5 Hz | 120.63% → 122.11% (**+1.48%p**) | 효과 없음·원복 |
| Bringup/AMCL | LiDAR 요청 10→8 Hz | 실제 `/scan` 10.00 Hz 그대로 | 입력 변화 0·원복 |
| Bringup | 중복 `joint_state_publisher` 제거 | base load 2.6 → 2.0 (**-23.1%**) | **채택·유지** |
| Nav2 | 정상 composition | idle 9→5~7.6, peak 23.0→9.7 | 효과 크나 **미채택** |

controller와 costmap 주기를 절반으로 낮춘 통제 실험에서 Nav2 CPU는 오히려 **늘었다**.
측정 노이즈 범위라 해도 절감 근거가 없고 제어·장애물 반응 여유만 깎으므로 모두 원복했다.
LiDAR에 8Hz를 요청해도 실제 `/scan`은 10.00Hz 그대로여서 입력량이 줄지 않았다.

가장 아이러니한 건 **Nav2 composition**이다. 수치상 가장 효과적(idle load 9→5~7.6,
peak 23→9.7)이었지만, 당시 4초 bond heartbeat 오판과 이후 경로·충돌 문제 때문에
운영 검증이 끝나지 않았다. **수치는 최고인데 미채택**인 설계 후보로 남겼다.

### 3.5 남은 경고 — 온도와 lifecycle manager

두 가지를 후속 과제로 적어 둔다.

1. **온도 81.3°C** — 지속 운용 시 스로틀링 여부를 `vcgencmd get_throttled`로 확인해야 한다.
2. **lifecycle_manager_navigation이 24.23%** — 관리 프로세스가 개별 주행 노드보다 CPU가
   높다. 반복 lifecycle 조회·DDS discovery·과도한 logging 중 무엇인지 별도 측정이 필요하다.

---

## 4. 함대 안전 — 긴급정지는 일부러 agent를 우회한다

마지막으로 안전. 콘솔에서 **전체 로봇 긴급정지**를 누르면 함대가 멈춰야 한다.
여기서 중요한 설계 판단은 **긴급정지 경로를 agent에 태우지 않았다**는 것이다.

agent는 heartbeat·명령 중계·세션 관리로 항상 바쁘고, 두 도메인·큐·타이머를 거친다.
정지 명령이 이 경로를 타면 지연·병목·단일 실패점에 노출된다. 그래서 긴급정지는
로봇 base에 직접 붙는 **독립 relay(systemd 상시 서비스)**로 분리해, agent가 죽어 있어도
동작하게 했다. 안전 경로는 최대한 짧고 독립적이어야 한다.

{{< figure src="/images/auto_drive/wasab-estop-all-stop-2x.gif" alt="콘솔에서 전체 긴급정지를 실행하자 함대의 모든 로봇이 즉시 정지하는 데모, 2배속" caption="전체 긴급정지 — agent를 우회하는 독립 정지 경로로 함대 일괄 정지" >}}

---

## 5. 정리

- **도메인 분리 + agent 브리지** — 로봇마다 ROS 도메인을 격리해 토픽 혼선을 끊고,
  두 도메인을 동시에 붙잡는 agent 하나로 관제를 다시 통합했다.
- **2-context의 안전 규칙** — 콜백은 큐에 넣기만, 발행은 자기 컨텍스트 타이머에서만.
  QoS는 이벤트 성격(주기적 vs 원샷)에 맞춰 BEST_EFFORT / RELIABLE로 갈랐다.
- **튜닝은 프로파일부터** — agent CPU의 진범은 좌표 계산이 아니라 고빈도 `/tf`의
  executor wake-up이었다. `/amcl_pose`로 바꿔 약 70~75%를 줄였다.
- **측정 없이 채택하지 않는다** — 좋아 보였던 주기 하향은 실측이 효과 없음이라 답했고,
  효과가 컸던 composition조차 운영 검증 전이라 미채택으로 남겼다.
- **안전 경로는 짧고 독립적으로** — 긴급정지는 일부러 agent를 우회시켰다.

측위·도킹의 기반이 궁금하다면 이 함대가 딛고 선 앞선 기록들을 함께 보면 좋다 —
[Nav2·costmap·AMCL 입문](../nav2-costmap-amcl-자율주행-위치추정-입문/),
[AMCL yaw 측위오차 추적기](../amcl-yaw-측위오차-추적기-가설반박부터-환경개선까지/),
[AprilTag PID 정밀 도킹 성공 기록](../nav2-apriltag-pid-정밀도킹-성공기록/).
