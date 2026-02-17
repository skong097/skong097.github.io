# Day 1 - ROS2 환경 세팅 & 기본 통신 테스트

## 날짜
> 2026-02-16 (월)

## 오늘 학습한 내용

### 1. 프로젝트 구조 생성
- `setup_mini_patrol.sh` 스크립트로 워크스페이스 일괄 생성
- **patrol_interfaces** (CMake 패키지): 커스텀 msg/srv/action 정의
- **mini_patrol** (Python 패키지): 노드 코드, config, launch 포함

### 2. 패키지 빌드 & 의존성 순서
- `patrol_interfaces` → `mini_patrol` 순서로 빌드 필수 (커스텀 인터페이스 의존)
- `colcon build --packages-select` 로 개별 패키지 빌드
- 빌드 후 반드시 `source install/setup.bash`

### 3. Pub/Sub 통신 테스트
- `status_pub` 노드: 로봇 상태(JSON)를 `/patrol/status` 토픽으로 발행
- `status_monitor` 노드: 상태 수신, 배터리 30% 이하 시 ALERT 출력
- 배터리 감소 시뮬레이션 → CHARGING 상태 전환 확인

### 4. CLI 명령어 실습
- 노드/토픽 조회 및 실시간 모니터링 명령어 실습

## 작성/수정한 코드
- `setup_mini_patrol.sh` — 프로젝트 구조 생성 스크립트
- `mini_patrol/robot_status_pub.py` — Publisher 노드 (동작 확인)
- `mini_patrol/status_monitor_sub.py` — Subscriber 노드 (동작 확인)

## 사용한 CLI 명령어
```bash
# 빌드
colcon build --packages-select patrol_interfaces
colcon build --packages-select mini_patrol
source install/setup.bash

# 빌드 캐시 정리 (Duplicate package 에러 해결)
rm -rf build/ install/ log/

# 노드 실행
ros2 run mini_patrol status_pub
ros2 run mini_patrol status_monitor

# 모니터링
ros2 node list
ros2 topic list -t
ros2 topic echo /patrol/status
ros2 topic hz /patrol/status
ros2 node info /robot_status_publisher
```

## 이슈 & 해결
| 이슈 | 원인 | 해결 |
|------|------|------|
| `Duplicate package names not supported` | install/ 폴더에 이전 빌드 캐시 잔존 | `rm -rf build/ install/ log/` 후 재빌드 |

## 내일 할 것
- Day 2: `battery_pub.py` 구현 (센서 분리 패턴)
- Day 3: Service 통신 — `patrol_commander.py` (Server) & `patrol_client.py` (Client) 구현
- 커스텀 인터페이스 `PatrolCommand.srv` 활용 테스트
