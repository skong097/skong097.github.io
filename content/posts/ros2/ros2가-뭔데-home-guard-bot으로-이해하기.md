---
title: "🤖 ROS2가 뭔데? — Home Guard Bot으로 이해하기"
date: 2026-03-21
draft: true
tags: ["ros2"]
categories: ["ros2"]
description: "사람도 마찬가지야. 눈으로 보고, 머리로 생각하고, 입으로 말하잖아. 이 세 가지를 한 명이 하지만, 각각은 독립된 기능이야. 눈이 없어도 말은 할 수 있고, 입이 없어도 생각은 할 수 있어. 로봇도 똑같아. Hom"
---

# 🤖 ROS2가 뭔데? — Home Guard Bot으로 이해하기

---

## 로봇은 혼자 다 못 한다

사람도 마찬가지야. 눈으로 보고, 머리로 생각하고, 입으로 말하잖아. 이 세 가지를 한 명이 하지만, 각각은 독립된 기능이야. 눈이 없어도 말은 할 수 있고, 입이 없어도 생각은 할 수 있어.

로봇도 똑같아. Home Guard Bot은 이런 일을 해야 해:

```
👁️ 카메라로 사람을 본다 (눈)
🧠 넘어졌는지 판단한다 (머리)
🔊 "위험합니다!" 말한다 (입)
```

이걸 하나의 거대한 프로그램에 다 넣으면 어떻게 될까?

```python
# ❌ 이렇게 하면 안 되는 이유
while True:
    frame = 카메라_촬영()          # 0.03초
    fall = AI가_판단(frame)        # 0.05초
    llm_report = LLM에게_물어봄() # 14초 ← 여기서 멈춤!
    음성_재생(llm_report)          # 3초
    # 총 17초 동안 카메라가 멈춤 😱
```

LLM이 14초 동안 생각하는 동안 카메라도 멈추고, 음성도 안 나와. 만약 그 14초 사이에 할머니가 넘어지면? 감지를 못 해.

**그래서 각 기능을 독립된 프로그램으로 분리해야 해.**

---

## ROS2란? — 로봇 부품들의 카카오톡

ROS2(Robot Operating System 2)는 이름과 달리 운영체제(OS)가 아니야. 로봇의 여러 프로그램들이 서로 대화할 수 있게 해주는 "메신저 시스템"이야.

카카오톡을 생각해봐:

```
카카오톡                           ROS2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
내가 메시지 보냄        →    노드가 메시지 발행(publish)
단톡방에 올림           →    토픽(topic)에 올림
단톡방 사람들이 읽음    →    다른 노드가 구독(subscribe)해서 읽음
```

**핵심 용어 3개만 기억하면 돼:**

| ROS2 용어 | 쉬운 비유 | Home Guard Bot 예시 |
|-----------|-----------|---------------------|
| **노드(Node)** | 단톡방의 각 사람 | guard_vision, guard_brain, guard_voice |
| **토픽(Topic)** | 단톡방 이름 | /guard/sensor_data, /guard/tts_command |
| **메시지(Message)** | 단톡방에 보내는 글 | `{"fall_detected": true, "zone": "거실"}` |

---

## Home Guard Bot의 구조 — 3명이 단톡방에서 협력



```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│  👁️ 눈       │  메시지  │  🧠 머리     │  메시지  │  🔊 입       │
│ guard_vision│ ──────→ │ guard_brain │ ──────→ │ guard_voice │
│             │        │             │        │             │
│ 카메라+YOLO │        │ 룰 판단+LLM │        │ Edge TTS    │
│ +낙상감지   │        │             │        │ +스피커     │
└─────────────┘        └─────────────┘        └─────────────┘
     [노드 1]              [노드 2]              [노드 3]
```

각 노드는 **독립된 프로그램**이야. 따로 실행되고, 따로 종료돼.

### 메시지 흐름을 자세히 보면:

```
guard_vision                guard_brain               guard_voice
━━━━━━━━━━━━                ━━━━━━━━━━━               ━━━━━━━━━━━
카메라 촬영                         │                        │
    ↓                              │                        │
YOLO가 사람 감지                    │                        │
    ↓                              │                        │
RF/ST-GCN이 낙상 판단               │                        │
    ↓                              │                        │
메시지 발행 ──────────────→ 메시지 수신                      │
/guard/sensor_data          {"fall_detected":true}          │
                                   ↓                        │
                            ⚡ 룰 엔진 즉시 판단              │
                            (0.01초)                        │
                                   ↓                        │
                            메시지 발행 ──────────→ 메시지 수신
                            /guard/tts_command       "위험! 낙상 감지!"
                                   │                        ↓
                                   │               Edge TTS 음성 합성
                                   │                        ↓
                            (동시에 LLM 비동기)        🔊 스피커 재생
                            14초 후 상세 보고서 발행
                            /guard/report
```

**핵심:** guard_brain이 LLM에게 14초 동안 물어보는 동안에도, guard_vision은 계속 카메라를 보고 있어! 각자 독립적으로 돌아가니까.

---

## 토픽 — 단톡방 목록

Home Guard Bot의 단톡방(토픽)은 이렇게 있어:

```
📋 /guard/sensor_data    — 센서+비전 데이터 (vision → brain)
📋 /guard/report         — 상황 보고서 (brain → 누구든)
📋 /guard/tts_command    — "이거 말해" 명령 (brain → voice)
📋 /guard/fall_detection — 낙상 상세 정보 (vision → 누구든)
```

토픽의 장점은 **보내는 쪽은 누가 읽는지 몰라도 돼**. guard_vision은 그냥 "/guard/sensor_data" 단톡방에 메시지를 올리기만 해. 누가 읽든 상관없어. 나중에 새로운 노드(예: guard_dashboard)를 추가해도 vision 코드를 수정할 필요가 없어.

```
                    /guard/sensor_data
guard_vision ──→  ┌──────────────────────┐
                  │  단톡방               │ ←── guard_brain (구독 중)
                  │                      │ ←── guard_dashboard (나중에 추가해도 OK)
                  │                      │ ←── guard_logger (나중에 추가해도 OK)
                  └──────────────────────┘
```

---


### ROS2 없이 직접 만든다면:

```python
# 프로그램 A에서 프로그램 B로 데이터를 보내려면...
import socket
server = socket.socket(...)    # 소켓 서버 만들고
server.bind(('localhost', 9090))  # 포트 열고
server.listen()                # 연결 대기하고
conn, addr = server.accept()   # 연결 받고
data = conn.recv(1024)         # 데이터 받고
# ... 직렬화, 에러 처리, 재연결 로직 등등 😵
```

### ROS2를 쓰면:

```python
# 보내는 쪽 (guard_vision)
self.publisher = self.create_publisher(String, '/guard/sensor_data', 10)
msg = String()
msg.data = '{"fall_detected": true}'
self.publisher.publish(msg)  # 끝! 한 줄로 발행

# 받는 쪽 (guard_brain)
self.subscription = self.create_subscription(
    String, '/guard/sensor_data', self.on_sensor_data, 10)
# 메시지가 오면 on_sensor_data 함수가 자동 호출됨
```

ROS2가 알아서 해주는 것들: 프로그램 간 연결, 메시지 전달, 직렬화/역직렬화, 에러 처리, 다중 구독자 관리.

---

## 왜 이렇게 나눴을까? — 실제 장점

### 1. 하나가 죽어도 나머지는 살아있다

```
guard_voice가 에러로 죽음
    → guard_vision은 계속 카메라 감시 ✅
    → guard_brain은 계속 판단 ✅
    → guard_voice만 다시 실행하면 됨 ✅
```

### 2. 개발할 때 각자 따로 테스트

```bash
# vision만 테스트 (brain, voice 없어도 됨)
hg-vision-stgcn

# 다른 터미널에서 메시지 확인
ros2 topic echo /guard/sensor_data
```

### 3. 부품 교체가 쉽다

```
RF 모델 → ST-GCN 모델로 교체?
    → guard_vision만 수정
    → guard_brain, guard_voice는 그대로

Edge TTS → Piper TTS로 교체?
    → guard_voice만 수정
    → guard_vision, guard_brain은 그대로
```

토픽(단톡방)의 메시지 형식만 같으면, 안쪽을 어떻게 바꾸든 상관없어.

### 4. 컴퓨터 여러 대에 분산 가능

```
PC 1 (GPU 있음): guard_vision (YOLO + AI)
PC 2 (스피커 달림): guard_voice (TTS)
라즈베리파이: guard_brain (센서 수집)

→ ROS2가 네트워크로 토픽을 자동 연결해줌
```

---

## ROS2 부분

`brain_node.py`를 예로 보면:

```python
import rclpy                         # ← ROS2 라이브러리
from rclpy.node import Node          # ← 노드 기본 클래스
from std_msgs.msg import String      # ← 메시지 타입

class BrainNode(Node):               # ← Node를 상속 = "나는 ROS2 노드야"
    def __init__(self):
        super().__init__("guard_brain")  # ← 노드 이름 등록

        # 구독: 이 단톡방의 메시지를 받겠다
        self.sensor_sub = self.create_subscription(
            String,                    # 메시지 타입
            "/guard/sensor_data",      # 토픽(단톡방) 이름
            self.on_sensor_data,       # 메시지 오면 이 함수 실행
            10                         # 큐 크기
        )

        # 발행: 이 단톡방에 메시지를 보내겠다
        self.report_pub = self.create_publisher(String, "/guard/report", 10)
        self.tts_pub = self.create_publisher(String, "/guard/tts_command", 10)

    def on_sensor_data(self, msg):
        # 센서 데이터가 오면 자동으로 호출됨!
        sensor = json.loads(msg.data)

        # 룰 판단
        result = rule_engine(sensor)

        # 결과를 다른 단톡방에 발행
        tts_msg = String()
        tts_msg.data = "위험! 낙상 감지!"
        self.tts_pub.publish(tts_msg)    # ← guard_voice가 이걸 받아서 말함

def main():
    rclpy.init()                    # ← ROS2 시스템 시작
    node = BrainNode()              # ← 노드 생성
    rclpy.spin(node)                # ← "메시지 계속 기다려!" (무한 대기)
    rclpy.shutdown()                # ← ROS2 시스템 종료
```

```
ROS2가 해주는 것:
  ✅ 노드 등록/관리
  ✅ 토픽 연결 (발행자↔구독자 자동 매칭)
  ✅ 메시지 전달 (직렬화, 네트워크 등)
  ✅ spin() — 메시지가 올 때까지 대기
  ✅ 파라미터 관리 (model_type, camera_id 등)
  ✅ 로깅 (self.get_logger().info(...))

관리자가 하는 것:
  🔧 YOLO로 사람 감지 (AI)
  🔧 RF/ST-GCN으로 낙상 판단 (AI)
  🔧 Ollama로 LLM 보고서 생성 (AI)
  🔧 Edge TTS로 음성 합성 (TTS)
  🔧 룰 엔진으로 즉시 판단 (로직)
```

즉, ROS2는 "통신과 관리"를 담당하고, 관리자는 "실제 기능"에 집중하는 거야.

---

## 정리: ROS2 = 로봇의 신경계

사람으로 비유하면:

```
사람의 몸              Home Guard Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
눈                 →   guard_vision (YOLO + 낙상 AI)
뇌                 →   guard_brain (룰 엔진 + LLM)
입                 →   guard_voice (Edge TTS + 스피커)
신경(눈→뇌→입)     →   ROS2 (토픽으로 연결)
```

눈이 뭔가 봤으면 신경을 통해 뇌에 전달하고, 뇌가 판단하면 신경을 통해 입에 전달해서 말하는 거야. **ROS2는 이 "신경" 역할**을 해.

눈, 뇌, 입은 각각 독립적으로 존재하지만, 신경(ROS2)이 연결해줘서 하나의 몸(로봇)처럼 동작하는 거야.

---

## 부록: 자주 쓰는 ROS2 명령어

```bash
# 현재 실행 중인 노드 확인
ros2 node list

# 현재 존재하는 토픽 확인
ros2 topic list

# 특정 토픽 메시지 실시간 확인 (디버깅)
ros2 topic echo /guard/sensor_data

# 토픽에 직접 메시지 보내기 (테스트)
ros2 topic pub --once /guard/tts_command std_msgs/String "data: '테스트 음성'"

# 노드 간 연결 그래프 시각화
ros2 run rqt_graph rqt_graph
```
