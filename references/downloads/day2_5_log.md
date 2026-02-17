# Day 2~5 - ROS2 미니 순찰 시스템 통합 학습 일지

## 날짜
> 2026-02-16 (월)

## Day 2: Publisher & Subscriber (토픽 통신)
### 학습 내용
- `robot_status_pub.py`: JSON 기반 로봇 상태 발행 (배터리, 위치, 상태)
- `status_monitor_sub.py`: 상태 수신 및 배터리 ALERT 모니터링
- Timer 기반 주기적 발행, 콜백 기반 수신 패턴

### 사용한 CLI
```bash
ros2 run mini_patrol status_pub
ros2 run mini_patrol status_monitor
ros2 topic echo /patrol/status
ros2 topic hz /patrol/status
ros2 topic info /patrol/status -v
ros2 node info /robot_status_publisher
```

---

## Day 3: Service (서비스 통신)
### 학습 내용
- `patrol_commander.py` (Service Server): START/STOP/RETURN_HOME/REPORT 명령 처리
- `patrol_client.py` (Service Client): 인터랙티브 CLI로 서비스 호출
- 서버가 `/patrol/status` 토픽도 구독하여 실시간 배터리 정보를 서비스 응답에 반영
- Request/Response 동기 패턴, `call_async` + `spin_until_future_complete` 패턴

### 사용한 CLI
```bash
ros2 service list
ros2 service type /patrol/command
ros2 interface show patrol_interfaces/srv/PatrolCommand
ros2 service call /patrol/command patrol_interfaces/srv/PatrolCommand \
  "{command: 'START', waypoints: ['A', 'B', 'C']}"
ros2 service call /patrol/command patrol_interfaces/srv/PatrolCommand \
  "{command: 'REPORT', waypoints: []}"
```

---

## Day 4: Parameter & Launch File
### 학습 내용
- `patrol_params.yaml`: 로봇 설정 외부 파일 관리
- `patrol_system.launch.py`: 3개 노드 일괄 실행 (status_pub, status_monitor, patrol_commander)
- 런타임 파라미터 변경 (노드 재시작 없이)
- Launch 인수 오버라이드 (`robot_id:=patrol_02`)

### 사용한 CLI
```bash
ros2 launch mini_patrol patrol_system.launch.py
ros2 launch mini_patrol patrol_system.launch.py robot_id:=patrol_02 patrol_speed:=2.0
ros2 param list
ros2 param get /robot_status_publisher robot_id
ros2 param set /robot_status_publisher patrol_speed 3.0
ros2 param dump /robot_status_publisher
```

---

## Day 5: Action (액션 통신)
### 학습 내용
- `patrol_action_server.py`: 순찰 미션 실행, 실시간 피드백, 취소 처리
- `patrol_action_client.py`: 미션 전송, 프로그레스 바 피드백 수신, Ctrl+C 취소
- Goal 수락/거부 판단 (배터리 체크, 중복 미션 체크)
- `goal_handle.succeed()` → `return result` 공식 패턴

### 사용한 CLI
```bash
ros2 action list
ros2 action info /patrol/mission
ros2 interface show patrol_interfaces/action/PatrolMission
ros2 action send_goal /patrol/mission patrol_interfaces/action/PatrolMission \
  "{waypoints: ['X', 'Y', 'Z'], speed: 1.5}" --feedback
ros2 run mini_patrol patrol_action_client \
  --ros-args -p waypoints_str:="lobby hallway server_room exit" -p speed:=1.5
```

### 테스트 결과
```
Goal accepted with ID: a989698ac4c240b49ed752cbc0f4dc27
Feedback: 25% lobby → 50% hallway → 75% server_room → 100% exit
Result: success=True, distance=46.1m, elapsed=4.0초
visited: ['lobby', 'hallway', 'server_room', 'exit']
```

---

## 이슈 & 해결
| 이슈 | 원인 | 해결 |
|------|------|------|
| `RuntimeError: no running event loop` | `async def` + `asyncio.sleep()`이 ROS2 executor에서 이벤트 루프 없이 실행 | 일반 `def` + `time.sleep()`으로 변경 |
| Action Result 항상 빈 값 반환 | `MultiThreadedExecutor` + `ReentrantCallbackGroup` 조합에서 result 전달 타이밍 이슈 | `rclpy.spin()` (SingleThread) + 기본 callback group으로 변경, 공식 패턴 준수 |
| 미션 거부 (`이미 미션 수행 중`) | 이전 미션 에러로 `is_executing=True` 잔존 | Action Server 재시작으로 초기화 |

## ROS2 핵심 개념 학습 현황
- [x] Node, Workspace, Package (Day 1)
- [x] Topic - Publisher/Subscriber (Day 2)
- [x] Service - Server/Client (Day 3)
- [x] Custom Interface - msg/srv/action (Day 3)
- [x] Parameter + YAML Config (Day 4)
- [x] Launch File (Day 4)
- [x] Action - Server/Client/Feedback/Cancel (Day 5)
- [ ] QoS, Lifecycle, rqt, rosbag2 (Day 6)
- [ ] 통합 시스템 + 문서화 (Day 7)

## 내일 할 것
- Day 6: QoS 프로파일 적용, rqt_graph로 노드 관계 시각화, rosbag2 녹화/재생
- Day 7: 전체 통합 Launch, 최종 정리
