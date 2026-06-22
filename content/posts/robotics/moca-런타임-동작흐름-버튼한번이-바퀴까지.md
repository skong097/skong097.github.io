---
title: "MOCA 카페 로봇 시스템 아키텍처 (2) — 버튼 한 번이 바퀴까지 닿는 런타임 동작 흐름"
date: 2026-06-21
draft: false
tags: ["robotics", "ros2", "rclpy", "fastapi", "websocket", "system-design"]
categories: ["robotics"]
summary: "MOCA의 정적 구조 위에서 실제 명령이 어떻게 흐르는지 정리한다. 다섯 모드가 공유하는 런타임 골격 세 가지, 서빙 모드가 브라우저 클릭에서 모터까지 닿는 전체 경로, 그리고 FastAPI 웹 서버와 ROS2 rclpy 노드를 한 프로세스에서 공존시킨 방법까지."
cover:
  alt: "MOCA 런타임 동작 흐름"
  hidden: true
ShowToc: true
TocOpen: true
---

> MOCA 시스템 2부작 중 2편(런타임편)이다. [1편(설계편)](/posts/robotics/moca-시스템-아키텍처-웹운영화면부터-ros2-로봇까지/)에서 정적 구조(3계층·FSM·cmd_vel 파이프라인)를 다뤘고, 이번 편은 그 위에서 명령이 실제로 흐르는 동작을 다룬다.

## 배경

1편에서 본 구조는 "무엇이 어디에 있는가"였다. 이번 편의 질문은 "버튼을 누르면 그게 어떻게 바퀴까지 가는가"이다. 다섯 모드(idle·serving·patrol·guiding·engaging)는 겉보기엔 하는 일이 다르지만, 실행 골격은 모두 같은 패턴을 공유한다. 그 패턴을 먼저 보면 개별 모드 시퀀스가 전부 같은 모양으로 보인다.

## 1. 모든 모드가 공유하는 런타임 골격 세 가지

**① 하향(명령) — ROS2 서비스 호출 + 모드 프로세스 생성**

브라우저가 보낸 모드 요청은 다음 순서로 흐른다. 명령은 "받았다/거절됐다"는 확인이 필요하므로 **요청-응답형 서비스**를 쓴다.

1. 브라우저가 WebSocket으로 모드 요청(`set_mode`, 파라미터)을 보낸다.
2. OperationServer가 우선순위·배터리·안전을 검증(게이팅)한다.
3. 통과하면 ROS2 서비스(`SetMode`)로 mode_manager에 전달한다.
4. mode_manager가 기존 모드 프로세스를 종료하고 새 모드의 launch를 서브프로세스로 띄운다 → 디스패처 실행.
5. 응답(`success`)이 브라우저로 돌아온다.

**② 상향(상태) — ROS2 토픽 → WebSocket 브로드캐스트**

모드 상태는 1초에 한 번(1Hz) 토픽으로 방송된다. OperationServer가 이를 구독해 받은 뒤, 연결된 모든 브라우저에 WebSocket으로 푸시한다. 상태는 계속 흐르는 방송이므로 **pub-sub 토픽**이 맞다. (`mode_manager` → `/mode/state` 1Hz → OperationServer 구독 → WebSocket 브로드캐스트 → 화면 갱신)

**③ 완료 감지 — completion_watcher**

작업이 끝나면 mode_manager가 아니라 OperationServer가 처리한다. 디스패처가 "끝났다(done)"는 상태만 방송하면, OperationServer의 completion_watcher가 그걸 보고 대기 모드 전환을 호출한다. 1편에서 말한 코어/정책 분리가 런타임에서 이렇게 나타난다.

> 명령은 서비스(확인 필요), 상태는 토픽(지속 방송), 완료는 OperationServer가 관찰 후 판정 — 이 세 가지가 모든 모드의 뼈대다.

## 2. 서빙 모드 — 브라우저 클릭이 모터까지

가장 긴 경로인 서빙으로 전체 체인을 따라가 보자. 단일 클릭 하나가 **여섯 개의 프로토콜 경계**를 통과한다.

{{< figure src="/images/diagrams/moca-serving-chain.svg" alt="서빙 모드 전체 체인 — 브라우저 버튼 클릭이 WebSocket으로 OperationServer에, ROS2 서비스 SetMode로 mode_manager에, 서브프로세스 launch로 serving_dispatcher에, ROS2 액션으로 Nav2에, ROS2 토픽으로 cmd_vel 파이프라인에 전달되고, 최종적으로 Modbus RTU로 모터와 바퀴를 구동한다" >}}

도착 후에는 정해진 시간 대기 → 홈 복귀 → 디스패처가 "서빙 종료" 상태 방송 → OperationServer가 대기 모드로 전환하는 식으로 닫힌다. 명령이 내려갈 때는 서비스→액션→토픽→Modbus로, 상태가 올라올 때는 토픽→WebSocket으로 — **경계마다 의미(확인/실행/주행/속도/구동)가 다르다는 점**이 이 흐름의 핵심이다.

다른 모드는 디스패처 내부만 다르다.

- **patrol**: 점유 감지 노드를 먼저 띄우고, 스케줄러가 "스캔 → 다음 테이블 이동"을 반복한다. 도착마다 점유 결과를 토픽으로 올려 화면 테이블 색을 갱신한다.
- **guiding**: 사람 감지 노드가 15Hz로 손님을 추적한다. 손님이 1.5m 이상 멀어지면 정지해 기다리고, 오래 놓치면 대기 모드로 복귀한다.
- **engaging**: 유일하게 행동 트리(Behavior Tree, 10Hz)로 동작한다. 감지 → 접근 → 아이스브레이크 → 미니게임 → 권유 단계를 거치며, 손님 감정 신호가 전이 가드가 된다.

## 3. FastAPI 웹 서버와 ROS2 rclpy를 한 프로세스에서 공존시키기

런타임에서 가장 까다로웠던 통합 지점이다. OperationServer는 **하나의 파이썬 프로세스 안에서 FastAPI(웹)와 rclpy(ROS2 노드)를 동시에 돌린다.** 그래서 둘 사이는 네트워크가 아니라 같은 프로세스 안의 객체 호출로 이어진다.

문제는 두 런타임이 각자 자기 루프를 잡으려 한다는 것이다. rclpy는 보통 `spin()`으로 블로킹하며 자체 executor를 돌리고, FastAPI는 asyncio 이벤트 루프가 돌아야 한다. 한 프로세스에서 둘 다 메인 루프를 차지하려 하니 충돌한다.

해결은 **FastAPI/uvicorn을 별도 스레드에서 돌리는 것**이다. 메인 스레드는 rclpy executor(`MultiThreadedExecutor.spin()`)가 토픽 구독과 서비스 응답을 처리하고, 백그라운드 데몬 스레드에서 uvicorn의 asyncio 루프가 WebSocket·REST를 처리한다.

{{< figure src="/images/diagrams/moca-runtime-opserver-bridge.svg" alt="OperationServer는 단일 프로세스에서 rclpy 노드(메인 스레드 executor spin)와 FastAPI/uvicorn(별도 데몬 스레드 asyncio 루프)을 함께 돌린다. 브라우저는 WebSocket/REST로 FastAPI와 통신하고, rclpy 노드는 call_async(SetMode)로 mode_manager에 명령하며 /mode/state 토픽을 구독한다. mode_manager는 launch로 디스패처·Nav2·cmd_vel·바퀴 체인을 실행한다" >}}

- **웹 → 로봇**: 핸들러가 같은 프로세스 안에서 오케스트레이터를 호출하고, 오케스트레이터가 rclpy 서비스 클라이언트의 `call_async`로 mode_manager에 명령한다. REST 라우터는 동기 함수라 FastAPI 스레드풀에서 안전하게 응답을 대기하지만, WebSocket 핸들러(`async def`) 경로는 `_await_future`가 `time.sleep` 폴링으로 응답을 기다려 최대 `SetMode` 타임아웃(2초) 동안 asyncio 루프를 점유한다 — 이 타임아웃이 점유 상한 역할을 한다.
- **로봇 → 웹**: rclpy 구독 콜백(ROS 스레드)이 받은 상태를, asyncio 루프 쪽으로 스레드 경계를 안전하게 넘겨 WebSocket으로 브로드캐스트한다. 공유 상태는 락으로 보호한다.

이 과정에서 "ROS spin과 asyncio 루프 충돌", "긴 타이머 콜백이 executor를 독점하는 문제"를 실제로 겪고 해결했다. 두 비동기 세계(ROS executor / asyncio)를 잇는 다리를 스레드 경계에서 어떻게 안전하게 놓느냐가 관건이었다.

## 배운 점

- **다섯 모드의 공통 골격을 먼저 세우니 개별 모드 구현이 단순해졌다.** "하향 서비스 + 상향 토픽 + 완료 감지"라는 틀을 공유하자, 새 모드는 디스패처 로직만 끼우면 됐다.
- **서로 다른 두 비동기 런타임을 한 프로세스에 합칠 때는 누가 메인 루프를 갖는지 먼저 정해야 한다.** asyncio(uvicorn)를 별도 데몬 스레드로 내리고 rclpy executor를 메인에 둔 뒤, 스레드 경계만 안전하게 처리하니 충돌이 사라졌다.
- 동기/비동기 통신을 **목적에 맞게 구분**한 게 통합을 깔끔하게 만들었다. 확인이 필요한 명령은 서비스, 흐르는 상태는 토픽, 장시간 주행은 피드백·취소가 되는 액션으로 나눴다.
