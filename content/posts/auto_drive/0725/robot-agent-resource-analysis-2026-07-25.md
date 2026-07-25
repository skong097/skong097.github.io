# 로봇 모듈별 CPU 자원 및 Agent 역할 분석

## 1. 목적

이 문서는 로봇 `pinky@192.168.2.9`에서 실행 중인 주요 소프트웨어를
`bringup`, `AMCL`, `Nav2`, `agent`의 네 영역으로 나누어 CPU와 메모리 부하를
비교하고, agent가 담당하는 기능과 그에 따른 자원 사용 현황을 정리한다.

## 2. 측정 조건

| 항목 | 값 |
|---|---|
| 측정 일시 | 2026-07-25 12:08 KST |
| 호스트 | `raspi` (`aarch64`) |
| 커널 | Linux `6.8.0-1040-raspi` |
| CPU | 4 logical CPUs |
| 메모리 | 총 3,784 MiB |
| 측정 도구 | `pidstat -u -r`, `mpstat`, `free`, `/sys/class/thermal` |
| 표본 | 1초 간격 12회 |

CPU 표기는 Linux 프로세스 기준이다. 프로세스 CPU `100%`는 CPU 코어 하나를
완전히 사용하는 값이다. 따라서 4코어 장치에서 프로세스 CPU 합계 `400%`가
전체 CPU 용량에 해당한다.

측정 당시 로봇의 정확한 임무 단계나 이동 여부를 통제하지 않았으므로, 결과는
현재 운용 상태의 관측값이며 모듈 단독 벤치마크는 아니다.

## 3. 시스템 전체 상태

| 지표 | 측정값 | 판단 |
|---|---:|---|
| Load average | 8.86 / 7.04 / 6.16 | 4코어 수보다 높아 실행 대기 또는 비중단 대기 작업이 존재 |
| CPU user | 47.02% | 애플리케이션 연산 비중이 큼 |
| CPU system | 21.75% | 커널·통신·드라이버 처리 비중도 높음 |
| CPU idle | 31.03% | 평균적으로 약 69% 사용 중 |
| I/O wait | 0.02% | 저장장치 I/O가 주 병목은 아님 |
| 메모리 사용 | 1,300 MiB / 3,784 MiB | 즉각적인 메모리 부족 없음 |
| 메모리 available | 2,483 MiB | 여유 있음 |
| Swap 사용 | 0 MiB | 메모리 압박 징후 없음 |
| CPU 온도 | 81.3°C | 높음. 열 스로틀링 여부 추가 확인 필요 |

Load average가 CPU 코어 수보다 높지만 CPU idle이 약 31% 남아 있다. 동시에 여러
ROS 프로세스에서 `%wait`가 관측됐으므로, 단순 계산 포화뿐 아니라 스케줄링,
통신 대기, 커널 대기 상태가 load에 포함된 것으로 해석해야 한다.

## 4. 네 영역별 측정 결과

### 4.1 요약

| 영역 | 포함 프로세스 | 평균 프로세스 CPU | 4코어 전체 대비 | RSS | 전체 시스템에서의 역할 |
|---|---|---:|---:|---:|---|
| Bringup | `bringup` | 22.40% | 5.60% | 79.1 MiB | 모터 명령, 엔코더, odometry, TF |
| AMCL | `amcl` | 16.24% | 4.06% | 47.3 MiB | LiDAR·지도 기반 위치 추정 |
| Nav2 | 아래 8개 navigation process | 133.29% | 33.32% | 401.2 MiB | 계획, 제어, 행동 실행, 속도 평활화 |
| Agent | `wasab_robot_agent.agent_node` | 9.83% | 2.46% | 77.7 MiB | 로봇·관제 도메인 브리지와 임무 중계 |
| **합계** | 11개 프로세스 | **181.76%** | **45.44%** | **605.3 MiB** | 네 영역 총합 |

네 영역은 4코어 전체 용량의 약 45.4%를 사용했다. 같은 구간의 시스템 전체
사용률은 약 69.0%였으므로, 이 네 영역이 전체 CPU 사용량의 약 65.9%를
차지한 것으로 추정된다.

### 4.2 Nav2 세부 구성

| Nav2 프로세스 | 평균 CPU | RSS |
|---|---:|---:|
| `lifecycle_manager_navigation` | 24.23% | 42.3 MiB |
| `bt_navigator` | 19.98% | 70.2 MiB |
| `controller_server` | 19.65% | 54.6 MiB |
| `behavior_server` | 17.40% | 50.2 MiB |
| `planner_server` | 15.65% | 57.1 MiB |
| `smoother_server` | 14.40% | 46.2 MiB |
| `waypoint_follower` | 11.07% | 43.7 MiB |
| `velocity_smoother` | 10.91% | 36.9 MiB |
| **Nav2 합계** | **133.29%** | **401.2 MiB** |

Nav2가 네 영역 중 가장 큰 자원을 사용했다. 특히 일반적으로 관리 부하가
작아야 할 `lifecycle_manager_navigation`이 Nav2 프로세스 중 가장 높은 CPU를
보였으므로, 반복적인 lifecycle 상태 조회, DDS discovery/통신, 과도한 logging
또는 executor wake-up 여부를 추가로 확인할 가치가 있다.

## 5. Agent의 역할

`wasab_robot_agent.agent_node`는 로봇 내부 기능을 직접 계산하는 주행 알고리즘이
아니라, 서로 다른 ROS 2 domain을 연결하고 로봇 상태와 명령을 중계하는
운영 제어 게이트웨이다.

### 5.1 두 ROS domain 연결

- 로봇 domain에서 `amcl_pose`, 배터리, 태그 관측, 도킹 상태를 수신한다.
- 콘솔 domain에 heartbeat, 태그 상태, 재측위 및 도킹 이벤트를 발행한다.
- 콘솔 명령을 큐에 넣고 로봇 domain의 executor에서 다시 발행한다.
- 서로 다른 `rclpy.Context`와 executor thread를 사용해 domain을 분리한다.

### 5.2 상태 수집과 heartbeat

- `/amcl_pose`에서 현재 위치와 yaw를 저장한다.
- `/battery/voltage`를 상태에 반영한다.
- 실행 모드와 태그 관측 결과를 관리한다.
- 2 Hz로 `/robots/heartbeat`를 발행해 관제 화면에 로봇 상태를 제공한다.

### 5.3 원격 주행 명령 중계와 watchdog

- 콘솔의 `/robot_<id>/cmd_vel`을 로봇 로컬 `/cmd_vel`로 중계한다.
- 20 Hz drain timer가 domain 간 명령 큐를 처리한다.
- 수동 명령이 0.3초 동안 들어오지 않으면 zero velocity를 발행하는 watchdog을
  적용한다.

### 5.4 재측위와 도킹 세션 관리

- 재측위 detector process를 시작하고 제한 시간 이후 종료한다.
- `/initialpose` 적용을 감시하고 재측위 이벤트를 콘솔에 전달한다.
- 태그 기반 도킹 process와 timeout을 관리한다.
- 도킹 상태와 성공·실패 이벤트를 관제 domain으로 전달한다.

### 5.5 자원 사용과 역할의 관계

Agent의 평균 CPU는 단일 코어 기준 9.83%, 4코어 전체 대비 2.46%였다. 네 영역
중 CPU가 가장 작지만 RSS는 약 77.7 MiB로 AMCL보다 컸다.

메모리 사용이 상대적으로 큰 이유는 다음 구조와 관련이 있다.

- 로봇 domain과 콘솔 domain을 위한 두 개의 ROS 2 context
- 두 executor thread와 다수 publisher/subscriber
- domain 간 전달 queue
- 재측위·도킹 process와 session 상태 관리

CPU 사용은 다음 주기 작업의 영향을 받는다.

- 20 Hz command queue drain과 watchdog
- 2 Hz heartbeat 생성과 발행
- DDS 통신 및 직렬화
- AMCL, battery, tag, docking callback

현재 9.83% CPU는 Nav2 합계 133.29%보다 현저히 작으므로 agent가 로봇 전체
CPU 부하의 주된 원인은 아니다. 다만 단순 heartbeat relay만 담당하는
프로세스로 보기에는 약 10%의 단일 코어 부하가 지속되므로, 기능별 최적화가
필요할 때는 20 Hz drain timer의 빈 wake-up과 두 DDS context의 통신 부하를
우선 확인하는 것이 합리적이다.

## 6. 성분별 CPU 기여도

네 영역 합산 CPU 181.76%를 기준으로 한 내부 구성 비율은 다음과 같다.

| 영역 | 네 영역 CPU 합계 내 비중 |
|---|---:|
| Nav2 | 73.3% |
| Bringup | 12.3% |
| AMCL | 8.9% |
| Agent | 5.4% |

Agent는 네 영역 합산 CPU의 약 5.4%를 차지한다. 따라서 로봇의 CPU 부하를
줄이는 목적이라면 우선순위는 Nav2, bringup, AMCL, agent 순이다.

## 7. 최근 2주 CPU 튜닝 이력과 효과

분석 기간은 **2026-07-11~2026-07-25**다. 작업일지에 전후 조건과 수치가
남아 있는 실험만 효과 판정에 사용했다. 서로 다른 시점의 load average와
프로세스 CPU는 직접 합산하지 않았으며, 같은 실험 안의 변경 전후 값만 비교했다.

### 7.1 수치 요약

| 영역 | 튜닝 작업 | 변경 전 | 변경 후 | 정량 효과 | 판정 |
|---|---|---:|---:|---:|---|
| Agent | 상시 `TransformListener`와 5 Hz pose timer 제거, `/amcl_pose` 구독으로 전환 | robot_ctx 약 30% | 7.5~9% | **-21~-22.5%p, 약 70~75% 감소** | **채택·유지** |
| Agent | 원인 격리: bringup 정지로 agent의 `/tf` 입력 제거 | 30% | 10% | -20%p, 66.7% 감소 | 원인 확인 실험 |
| Bringup 주변 | 중복 `joint_state_publisher` 제거 | base load 2.6 | 2.0 | **-0.6, 23.1% 감소** | **채택·유지** |
| Bringup/AMCL 입력 | LiDAR 요청 주기 10→8 Hz | 실제 `/scan` 10.00 Hz | 실제 `/scan` 10.00 Hz | 실제 입력 변화 0 Hz, CPU 효과 없음 | 기각·원복 |
| Nav2 | 정상 composition 적용 | idle load 약 9, peak 23.0 | idle 5~7.6, peak 9.7 | idle **15.6~44.4% 감소**, peak **57.8% 감소** | 효과 큼, 운영 설정은 미채택 |
| Nav2 | composition에서 bond timeout 4→10초 | heartbeat 누락 후 teardown | 오판 0건, Nav 76초·약 1 m 이동 | CPU 절감이 아닌 장애 내성 개선 | 실험 성공, 현재 미채택 |
| Nav2 | controller 20→10 Hz | Nav2 합계 120.63% | 123.90% | **+3.27%p, 2.7% 증가** | 효과 없음·원복 |
| Nav2 | local costmap update 10→5 Hz | Nav2 합계 120.63% | 122.11% | **+1.48%p, 1.2% 증가** | 효과 없음·원복 |
| AMCL | `max_beams=60`, particles 1000~2500 유지 | 동일 | 동일 | 단독 A/B 측정 없음 | 성공 기준 유지 |

`base load`는 `/proc/loadavg`의 1분 load이며 프로세스 CPU 백분율이 아니다.
따라서 JSP 제거 효과를 Agent 또는 Bringup 프로세스 CPU 감소량으로 환산하지
않았다.

### 7.2 영역별 해석

#### Bringup

직접적인 `bringup` 알고리즘 튜닝보다 중복 publisher 제거가 효과가 있었다.
`joint_state_publisher`는 실제 엔코더 기반 `/joint_states`와 기능이 겹쳤고,
제거 뒤 base load가 2.6에서 2.0으로 23.1% 낮아졌다. 이 변경은 유지됐다.
반면 LiDAR에 8 Hz를 요청해도 실제 `/scan`은 10.00 Hz로 그대로여서 bringup과
AMCL 입력량이 줄지 않았고, 해당 실험은 원복됐다.

#### AMCL

최근 2주 동안 AMCL만을 대상으로 한 유효한 전후 CPU 비교는 없다. 현재 성공
기준인 `max_beams=60`, particles 1000~2500을 유지했다. 7월 25일 실측 AMCL
CPU는 16.24%지만, 이를 다른 날짜의 수치와 비교해 튜닝 효과로 주장할 수는
없다. 향후에는 beams와 particles를 한 번에 하나씩 바꾸고 재측위 정확도와
CPU를 동시에 측정해야 한다.

#### Nav2

가장 큰 절감은 composition이었다. 정상적으로 component container를 구성한
실험에서 idle load가 약 9에서 5~7.6으로, peak가 23.0에서 9.7로 낮아졌다.
다만 당시 4초 bond heartbeat 오판과 이후 경로·충돌 문제 때문에 현재 성공
기준은 non-composition이다. 즉 **수치상 가장 효과적이지만 운영 검증이 끝나지
않아 미채택인 설계 후보**다.

반대로 controller와 local costmap 주기를 절반으로 낮춘 통제 실험에서는 Nav2
합계 CPU가 각각 3.27%p, 1.48%p 증가했다. 측정 노이즈 범위라 하더라도 절감
근거가 없고 제어·장애물 반응 여유만 줄이므로 모두 원복했다. 현재는 controller
20 Hz, local costmap update/publish 10/2 Hz, global costmap 1/1 Hz를 유지한다.

#### Agent

최근 2주 동안 가장 명확한 keeper다. 프로파일에서 기존 Agent CPU의 약 85%가
TF 좌표 계산이 아니라 35~55 Hz `/tf`가 Python executor wait-set을 계속 깨우는
비용임을 확인했다. pose 소스를 `/amcl_pose`로 바꾼 뒤 robot_ctx CPU가 약
30%에서 7.5~9%로 70~75% 감소했고, agent ON 상태에서 도킹 8→7→9를 완주했다.
7월 25일 현재 12초 평균 9.83%는 튜닝 후 관측 범위와 대체로 일치한다.

### 7.3 최종 채택 상태

| 구분 | 현재 값/상태 | 이유 |
|---|---|---|
| Bringup | 중복 JSP 없음, LiDAR DenseBoost 실제 10 Hz | JSP 제거만 효과 확인 |
| AMCL | beams 60, particles 1000~2500 | 기능 성공 기준, 직접 절감 실험 없음 |
| Nav2 | non-composition, controller 20 Hz, local 10/2 Hz, global 1/1 Hz | 주기 하향 효과 없음 |
| Agent | `/amcl_pose` + `/initialpose`, 상시 TransformListener 없음 | CPU 약 70~75% 감소 |

## 8. 주요 판단

1. **주요 CPU 소비 영역은 Nav2다.** 8개 프로세스 합계가 단일 코어 기준
   133.29%, 4코어 전체의 약 33.3%다.
2. **Agent는 핵심 운영 기능에 비해 CPU 비중이 낮다.** 4코어 전체의 약
   2.46%를 사용하며, 네 영역 합계의 약 5.4%다.
3. **메모리는 현재 병목이 아니다.** available memory가 약 2.4 GiB이고 swap
   사용이 없다.
4. **온도는 주의가 필요하다.** 81.3°C는 지속 운용 시 성능 변동이나
   스로틀링을 점검해야 하는 수준이다.
5. **lifecycle manager 부하는 비정상 후보다.** Nav2 관리 프로세스가 개별
   주행 노드보다 높은 CPU를 사용한 원인을 별도로 측정할 필요가 있다.

## 9. 권장 후속 측정

이번 결과는 현재 상태의 단일 12초 구간 측정이다. 최적화 결정을 내리기 전에
다음 조건을 각각 60초 이상 측정하는 것을 권장한다.

1. 로봇 완전 정지·임무 없음
2. AMCL만 활성화
3. Nav2 goal 수행 중
4. agent만 활성화한 상태
5. 순찰·재측위·도킹 각각 수행 중

각 조건에서 CPU, context switch, DDS traffic, 온도 및 clock throttling을 함께
기록하면 agent의 순수 비용과 주행 스택의 비용을 더 정확히 분리할 수 있다.

Raspberry Pi 환경에서는 다음 값도 함께 확인하는 것이 좋다.

```bash
vcgencmd measure_temp
vcgencmd get_throttled
pidstat -u -r -w -p <PID 목록> 1 60
mpstat -P ALL 1 60
```

## 10. 측정 범위의 한계

- Bringup 영역은 핵심 `bringup` process만 포함했다. LiDAR, battery publisher,
  joint/robot state publisher는 별도 주변 process로 제외했다.
- AMCL 영역은 `amcl` process만 포함했다. `map_server`와 localization lifecycle
  manager는 제외했다.
- Nav2 영역은 navigation lifecycle manager와 7개 navigation server를
  포함했다.
- 측정 중 로봇 임무 상태를 고정하지 않았기 때문에 다른 시점의 수치와 직접
  비교할 때는 동일 조건을 맞춰야 한다.
- RSS 합계는 shared library page를 중복 계산할 수 있으므로 물리 메모리의
  순증가량으로 해석하면 안 된다.


## 11. 근거 기록

- `docs/cpu-tuning-nav2-docking-2026-07-13.md`
- `docs/worklog-2026-07-14-agent-cpu-root-cause.md`
- `docs/worklog-2026-07-14-agent-cpu-fix-and-docking-success.md`
- `docs/worklog-2026-07-15-87-docking-success-settings-and-cpu.md`
- `docs/worklog-2026-07-20-systemd-stack-and-cpu-tuning.md`
