# ROS2 미니 로봇 관제 시스템 (Mini Robot Patrol System)

## 프로젝트 개요

ROS2의 핵심 개념을 단계별로 학습하기 위한 실습 프로젝트입니다.
가상 순찰 로봇의 상태를 모니터링하고 제어하는 시스템을 구축하면서,
ROS2 어드민/CLI 명령어와 Python 코드 작성을 균형 있게 익힙니다.

**ROS2 버전:** Humble / Jazzy (권장)
**언어:** Python (rclpy)
**학습 기간:** 약 5~7일 (하루 2~3시간 기준)

---

## 학습 로드맵 & 단계별 구성

### Day 1: ROS2 환경 세팅 & CLI 기초

**목표:** ROS2 설치 확인, 워크스페이스 생성, 기본 CLI 명령어 숙달

#### CLI 어드민 학습
```bash
# 환경 확인
ros2 doctor
ros2 wtf

# 워크스페이스 생성
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws
colcon build
source install/setup.bash

# 패키지 생성
cd src
ros2 pkg create mini_patrol --build-type ament_python --dependencies rclpy std_msgs sensor_msgs geometry_msgs

# 빌드 & 소싱
cd ~/ros2_ws
colcon build --packages-select mini_patrol
source install/setup.bash
```

#### CLI 탐색 명령어 (필수 암기)
```bash
# 노드 관련
ros2 node list
ros2 node info /node_name

# 토픽 관련
ros2 topic list
ros2 topic list -t              # 타입 포함
ros2 topic info /topic_name
ros2 topic echo /topic_name     # 실시간 데이터 확인
ros2 topic hz /topic_name       # 발행 주기 확인
ros2 topic pub /topic_name std_msgs/msg/String "data: 'hello'"

# 서비스 관련
ros2 service list
ros2 service type /service_name
ros2 service call /service_name std_srvs/srv/SetBool "data: true"

# 파라미터 관련
ros2 param list
ros2 param get /node_name param_name
ros2 param set /node_name param_name value
ros2 param dump /node_name

# 인터페이스 확인
ros2 interface show std_msgs/msg/String
ros2 interface list
```

#### 실습 과제
- [ ] turtlesim 실행 후 위 CLI 명령어 전부 실습
- [ ] `ros2 topic pub`으로 터틀 움직여보기
- [ ] `ros2 param list`로 turtlesim 파라미터 확인 & 변경

---

### Day 2: Publisher & Subscriber (토픽 통신)

**목표:** 로봇 상태 데이터를 발행하고 수신하는 노드 작성

#### 파일 구조
```
mini_patrol/
├── mini_patrol/
│   ├── __init__.py
│   ├── robot_status_pub.py      # 로봇 상태 Publisher
│   ├── status_monitor_sub.py    # 상태 모니터 Subscriber
│   └── battery_pub.py           # 배터리 상태 Publisher
├── package.xml
├── setup.py
├── setup.cfg
└── resource/
    └── mini_patrol
```

#### robot_status_pub.py (핵심 코드)
```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import json
import random
import time

class RobotStatusPublisher(Node):
    def __init__(self):
        super().__init__('robot_status_publisher')
        
        # Publisher 생성: 토픽명, 메시지타입, QoS
        self.status_pub = self.create_publisher(String, '/patrol/status', 10)
        self.vel_pub = self.create_publisher(Twist, '/patrol/cmd_vel', 10)
        
        # Timer: 1초마다 상태 발행
        self.timer = self.create_timer(1.0, self.publish_status)
        
        self.patrol_state = 'IDLE'  # IDLE, PATROLLING, CHARGING, ALERT
        self.battery = 100.0
        self.position = {'x': 0.0, 'y': 0.0}
        
        self.get_logger().info('Robot Status Publisher 시작!')
    
    def publish_status(self):
        # 배터리 감소 시뮬레이션
        if self.patrol_state == 'PATROLLING':
            self.battery = max(0, self.battery - random.uniform(0.1, 0.5))
            self.position['x'] += random.uniform(-0.5, 0.5)
            self.position['y'] += random.uniform(-0.5, 0.5)
        
        if self.battery < 20:
            self.patrol_state = 'CHARGING'
        
        # JSON으로 상태 패키징
        status = {
            'timestamp': time.time(),
            'state': self.patrol_state,
            'battery': round(self.battery, 1),
            'position': self.position,
            'alert': self.battery < 30
        }
        
        msg = String()
        msg.data = json.dumps(status)
        self.status_pub.publish(msg)
        
        self.get_logger().info(
            f'[{self.patrol_state}] Battery: {self.battery:.1f}% '
            f'Pos: ({self.position["x"]:.1f}, {self.position["y"]:.1f})'
        )

def main(args=None):
    rclpy.init(args=args)
    node = RobotStatusPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

#### status_monitor_sub.py
```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json

class StatusMonitor(Node):
    def __init__(self):
        super().__init__('status_monitor')
        
        self.subscription = self.create_subscription(
            String,
            '/patrol/status',
            self.status_callback,
            10
        )
        self.alert_count = 0
        self.get_logger().info('Status Monitor 시작!')
    
    def status_callback(self, msg):
        status = json.loads(msg.data)
        
        if status['alert']:
            self.alert_count += 1
            self.get_logger().warn(
                f'⚠️ ALERT #{self.alert_count}: 배터리 부족 ({status["battery"]}%)'
            )
        else:
            self.get_logger().info(
                f'✅ 상태 정상 | {status["state"]} | Battery: {status["battery"]}%'
            )

def main(args=None):
    rclpy.init(args=args)
    node = StatusMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

#### setup.py entry_points 설정
```python
entry_points={
    'console_scripts': [
        'status_pub = mini_patrol.robot_status_pub:main',
        'status_monitor = mini_patrol.status_monitor_sub:main',
        'battery_pub = mini_patrol.battery_pub:main',
    ],
},
```

#### CLI 실습
```bash
# 빌드 후 각각 다른 터미널에서 실행
ros2 run mini_patrol status_pub
ros2 run mini_patrol status_monitor

# 별도 터미널에서 모니터링
ros2 topic echo /patrol/status
ros2 topic hz /patrol/status
ros2 topic info /patrol/status -v
ros2 node info /robot_status_publisher
```

---

### Day 3: Service (서비스 통신) & Custom Interface

**목표:** 서비스 요청/응답으로 로봇 제어, 커스텀 메시지/서비스 정의

#### 커스텀 인터페이스 패키지 생성
```bash
cd ~/ros2_ws/src
ros2 pkg create patrol_interfaces --build-type ament_cmake
```

#### srv/PatrolCommand.srv
```
# Request
string command          # START, STOP, RETURN_HOME, REPORT
string[] waypoints      # 순찰 웨이포인트 (선택)
---
# Response
bool success
string message
float64 battery_level
```

#### msg/RobotStatus.msg (커스텀 메시지)
```
# 커스텀 로봇 상태 메시지
builtin_interfaces/Time stamp
string robot_id
string state              # IDLE, PATROLLING, CHARGING, ALERT
float64 battery
float64 pos_x
float64 pos_y
float64 heading
bool alert
string alert_message
```

#### patrol_commander.py (Service Server)
```python
import rclpy
from rclpy.node import Node
from patrol_interfaces.srv import PatrolCommand

class PatrolCommander(Node):
    def __init__(self):
        super().__init__('patrol_commander')
        
        self.srv = self.create_service(
            PatrolCommand,
            '/patrol/command',
            self.command_callback
        )
        self.current_state = 'IDLE'
        self.battery = 100.0
        self.get_logger().info('Patrol Commander 서비스 시작!')
    
    def command_callback(self, request, response):
        cmd = request.command.upper()
        self.get_logger().info(f'명령 수신: {cmd}')
        
        if cmd == 'START':
            if self.battery < 20:
                response.success = False
                response.message = '배터리 부족! 충전 필요'
            else:
                self.current_state = 'PATROLLING'
                response.success = True
                response.message = f'순찰 시작! 웨이포인트: {request.waypoints}'
        
        elif cmd == 'STOP':
            self.current_state = 'IDLE'
            response.success = True
            response.message = '순찰 중지'
        
        elif cmd == 'REPORT':
            response.success = True
            response.message = f'현재 상태: {self.current_state}'
        
        else:
            response.success = False
            response.message = f'알 수 없는 명령: {cmd}'
        
        response.battery_level = self.battery
        return response

def main(args=None):
    rclpy.init(args=args)
    node = PatrolCommander()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

#### CLI로 서비스 호출
```bash
# 서비스 확인
ros2 service list
ros2 service type /patrol/command
ros2 interface show patrol_interfaces/srv/PatrolCommand

# 서비스 호출
ros2 service call /patrol/command patrol_interfaces/srv/PatrolCommand \
  "{command: 'START', waypoints: ['A', 'B', 'C']}"

ros2 service call /patrol/command patrol_interfaces/srv/PatrolCommand \
  "{command: 'REPORT', waypoints: []}"
```

---

### Day 4: Parameter & Launch File

**목표:** 파라미터로 노드 설정 관리, Launch 파일로 시스템 일괄 실행

#### 파라미터 적용 노드
```python
class ConfigurablePatrol(Node):
    def __init__(self):
        super().__init__('configurable_patrol')
        
        # 파라미터 선언 (기본값 포함)
        self.declare_parameter('patrol_speed', 1.0)
        self.declare_parameter('battery_threshold', 20.0)
        self.declare_parameter('publish_rate', 1.0)
        self.declare_parameter('robot_id', 'patrol_bot_01')
        self.declare_parameter('waypoints', ['A', 'B', 'C', 'D'])
        
        # 파라미터 읽기
        speed = self.get_parameter('patrol_speed').value
        threshold = self.get_parameter('battery_threshold').value
        robot_id = self.get_parameter('robot_id').value
        
        self.get_logger().info(
            f'설정 로드: ID={robot_id}, Speed={speed}, Threshold={threshold}'
        )
        
        # 파라미터 변경 콜백
        self.add_on_set_parameters_callback(self.param_callback)
    
    def param_callback(self, params):
        for param in params:
            self.get_logger().info(f'파라미터 변경: {param.name} = {param.value}')
        return SetParametersResult(successful=True)
```

#### launch/patrol_system.launch.py
```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    return LaunchDescription([
        # Launch 인수 선언
        DeclareLaunchArgument('robot_id', default_value='patrol_01'),
        DeclareLaunchArgument('patrol_speed', default_value='1.5'),
        
        LogInfo(msg=['순찰 시스템 시작!']),
        
        # 상태 Publisher 노드
        Node(
            package='mini_patrol',
            executable='status_pub',
            name='robot_status_publisher',
            parameters=[{
                'robot_id': LaunchConfiguration('robot_id'),
                'patrol_speed': LaunchConfiguration('patrol_speed'),
                'publish_rate': 2.0,
            }],
            output='screen'
        ),
        
        # 상태 Monitor 노드
        Node(
            package='mini_patrol',
            executable='status_monitor',
            name='status_monitor',
            output='screen'
        ),
        
        # Patrol Commander 서비스
        Node(
            package='mini_patrol',
            executable='patrol_commander',
            name='patrol_commander',
            output='screen'
        ),
    ])
```

#### CLI 실습
```bash
# Launch 실행
ros2 launch mini_patrol patrol_system.launch.py
ros2 launch mini_patrol patrol_system.launch.py robot_id:=patrol_02 patrol_speed:=2.0

# 런타임 파라미터 조작
ros2 param list
ros2 param get /robot_status_publisher robot_id
ros2 param set /robot_status_publisher patrol_speed 3.0
ros2 param dump /robot_status_publisher
ros2 param load /robot_status_publisher ./params.yaml
```

---

### Day 5: Action (액션 통신)

**목표:** 장시간 작업(순찰 미션)에 액션 통신 적용, 피드백 & 취소 구현

#### action/PatrolMission.action
```
# Goal
string[] waypoints
float64 speed
---
# Result
bool success
float64 total_distance
float64 elapsed_time
string[] visited_waypoints
---
# Feedback
string current_waypoint
int32 waypoints_remaining
float64 battery_level
float64 progress_percent
```

#### patrol_action_server.py (핵심 구조)
```python
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from patrol_interfaces.action import PatrolMission
import time

class PatrolActionServer(Node):
    def __init__(self):
        super().__init__('patrol_action_server')
        self._action_server = ActionServer(
            self,
            PatrolMission,
            '/patrol/mission',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback
        )
        self.get_logger().info('Patrol Action Server 시작!')
    
    def goal_callback(self, goal_request):
        self.get_logger().info(f'미션 요청: {goal_request.waypoints}')
        return GoalResponse.ACCEPT
    
    def cancel_callback(self, goal_handle):
        self.get_logger().info('미션 취소 요청!')
        return CancelResponse.ACCEPT
    
    async def execute_callback(self, goal_handle):
        self.get_logger().info('미션 실행 중...')
        feedback_msg = PatrolMission.Feedback()
        waypoints = goal_handle.request.waypoints
        visited = []
        
        for i, wp in enumerate(waypoints):
            # 취소 확인
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result = PatrolMission.Result()
                result.success = False
                result.visited_waypoints = visited
                return result
            
            # 웨이포인트 이동 시뮬레이션
            feedback_msg.current_waypoint = wp
            feedback_msg.waypoints_remaining = len(waypoints) - i - 1
            feedback_msg.progress_percent = (i + 1) / len(waypoints) * 100
            feedback_msg.battery_level = 100.0 - (i * 5.0)
            goal_handle.publish_feedback(feedback_msg)
            
            self.get_logger().info(f'📍 웨이포인트 {wp} 도착 ({feedback_msg.progress_percent:.0f}%)')
            visited.append(wp)
            
            # 이동 시간 시뮬레이션
            await rclpy.get_default_context().executor.create_task(
                lambda: time.sleep(2.0)
            )
        
        goal_handle.succeed()
        result = PatrolMission.Result()
        result.success = True
        result.visited_waypoints = visited
        result.total_distance = len(visited) * 10.0
        return result

def main(args=None):
    rclpy.init(args=args)
    node = PatrolActionServer()
    rclpy.spin(node)
    rclpy.shutdown()
```

#### CLI로 액션 테스트
```bash
# 액션 확인
ros2 action list
ros2 action info /patrol/mission
ros2 interface show patrol_interfaces/action/PatrolMission

# 액션 Goal 전송
ros2 action send_goal /patrol/mission patrol_interfaces/action/PatrolMission \
  "{waypoints: ['A', 'B', 'C', 'D'], speed: 1.0}" --feedback
```

---

### Day 6: QoS & Lifecycle & 디버깅

**목표:** QoS 정책, Lifecycle Node, rqt 도구 활용

#### QoS 프로파일 설정
```python
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy

# 센서 데이터용 (최신 값만, 유실 허용)
sensor_qos = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
    history=HistoryPolicy.KEEP_LAST,
    depth=5
)

# 명령 데이터용 (반드시 전달)
command_qos = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_LAST,
    depth=10
)
```

#### 디버깅 & 모니터링 CLI
```bash
# rqt 도구들
rqt_graph                        # 노드/토픽 관계 시각화
rqt_console                      # 로그 실시간 확인
rqt_topic                        # 토픽 모니터링
ros2 run rqt_reconfigure rqt_reconfigure  # 파라미터 GUI 변경

# 로깅 레벨 변경
ros2 service call /robot_status_publisher/set_logger_level \
  rcl_interfaces/srv/SetLoggerLevel \
  "{logger_name: 'robot_status_publisher', level: 10}"

# 녹화 & 재생 (rosbag2)
ros2 bag record -o patrol_log /patrol/status /patrol/cmd_vel
ros2 bag info patrol_log
ros2 bag play patrol_log

# 컴포넌트 & 노드 확인
ros2 component list
ros2 lifecycle list
ros2 lifecycle get /lifecycle_node
```

---

### Day 7: 통합 & 정리

**목표:** 전체 시스템 통합 Launch, YAML 설정, 문서화

#### config/patrol_params.yaml
```yaml
/**:
  ros__parameters:
    robot_id: "patrol_01"
    patrol_speed: 1.5
    battery_threshold: 20.0
    publish_rate: 2.0
    waypoints: ["lobby", "hallway_a", "server_room", "hallway_b"]
    alert_email: "admin@company.com"
```

#### 최종 Launch 파일 (config 포함)
```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    config = os.path.join(
        get_package_share_directory('mini_patrol'),
        'config',
        'patrol_params.yaml'
    )
    
    return LaunchDescription([
        Node(
            package='mini_patrol',
            executable='status_pub',
            name='robot_status_publisher',
            parameters=[config],
            output='screen'
        ),
        Node(
            package='mini_patrol',
            executable='status_monitor',
            name='status_monitor',
            parameters=[config],
            output='screen'
        ),
        Node(
            package='mini_patrol',
            executable='patrol_commander',
            name='patrol_commander',
            parameters=[config],
            output='screen'
        ),
    ])
```

#### 최종 패키지 구조
```
ros2_ws/src/
├── mini_patrol/
│   ├── mini_patrol/
│   │   ├── __init__.py
│   │   ├── robot_status_pub.py
│   │   ├── status_monitor_sub.py
│   │   ├── battery_pub.py
│   │   ├── patrol_commander.py        # Service Server
│   │   ├── patrol_client.py           # Service Client
│   │   ├── patrol_action_server.py    # Action Server
│   │   └── patrol_action_client.py    # Action Client
│   ├── config/
│   │   └── patrol_params.yaml
│   ├── launch/
│   │   ├── patrol_system.launch.py
│   │   └── patrol_full.launch.py
│   ├── package.xml
│   ├── setup.py
│   └── setup.cfg
│
└── patrol_interfaces/
    ├── msg/
    │   └── RobotStatus.msg
    ├── srv/
    │   └── PatrolCommand.srv
    ├── action/
    │   └── PatrolMission.action
    ├── package.xml
    └── CMakeLists.txt
```

---

## ROS2 핵심 개념 체크리스트

| 개념 | Day | CLI 명령어 | Python 코드 |
|------|-----|-----------|-------------|
| Workspace & Package | 1 | colcon build, ros2 pkg | setup.py |
| Node | 1-2 | ros2 node list/info | rclpy.node.Node |
| Topic (Pub/Sub) | 2 | ros2 topic echo/pub/hz | create_publisher/subscription |
| Service (Req/Res) | 3 | ros2 service call | create_service/create_client |
| Custom Interface | 3 | ros2 interface show | .msg / .srv / .action |
| Parameter | 4 | ros2 param get/set/dump | declare_parameter |
| Launch File | 4 | ros2 launch | LaunchDescription |
| Action (Goal/Feedback) | 5 | ros2 action send_goal | ActionServer/ActionClient |
| QoS | 6 | - | QoSProfile |
| Lifecycle | 6 | ros2 lifecycle | LifecycleNode |
| rosbag2 | 6 | ros2 bag record/play | - |
| YAML Config | 7 | - | parameters=[config] |

---

## 매일 마무리 루틴

하루 학습이 끝나면 아래 형식으로 `.md` 파일을 작성합니다:

```markdown
# Day N - [주제]
## 오늘 학습한 내용
## 작성한 코드 목록
## 사용한 CLI 명령어
## 이슈 & 해결
## 내일 할 것
```

---

## 참고 자료

- ROS2 공식 튜토리얼: https://docs.ros.org/en/jazzy/Tutorials.html
- rclpy API: https://docs.ros2.org/latest/api/rclpy/
- ROS2 CLI cheatsheet: `ros2 --help`, `ros2 topic --help` 등
