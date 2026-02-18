---
title: "LLM 기반 Guard Brain AI 에이전트 만들기 — Tool Use 패턴 입문"
date: 2026-02-18
categories: ["ai-agent"]
tags: ["ai-agent", "tool-use", "llm", "fastapi", "ollama", "python"]
description: "ChatGPT에게 질문하는 것과 AI Agent가 행동하는 것은 근본적으로 다르다. Tool Use 패턴으로 보안 에이전트를 직접 만들어보며 그 차이를 체감했다."
cover:
  image: images/covers/cover-ai-agent.png
  alt: Guard Brain AI Agent
ShowToc: true
ShowReadingTime: true
---

## AI Agent란 무엇인가?

LLM(대형 언어 모델)을 쓰다 보면 한계가 느껴지는 순간이 있다.
"이 센서 데이터 분석해줘"라고 하면 코드를 알려준다. 하지만 실제로 센서를 읽고, 판단하고, 로봇에게 명령을 내리고, 알림까지 보내는 건 직접 해야 한다.

**AI Agent는 이 과정을 스스로 한다.**

핵심 차이를 한 줄로 정리하면 이렇다.

```
LLM    : 질문 → 답변 (1회성, 수동적)
Agent  : 목표 → 계획 → 도구 호출 → 실행 → 피드백 루프 (자율적)
```

에이전트를 에이전트답게 만드는 핵심은 **Tool Use(도구 사용)** 패턴이다.
LLM이 상황을 보고 어떤 함수를 호출할지 스스로 결정하고, 그 결과를 보고 다음 행동을 결정한다.

---

## 프로젝트 구조

기존 프로젝트와 완전히 분리된 독립 환경으로 시작했다.

```
~/dev_ws/ai_agent/guard_brain_agent/
├── config.py      ← 설정값 (모델명, 포트)
├── tools.py       ← 도구 함수 5개 (Mock)
├── prompts.py     ← LLM 시스템 프롬프트
├── agent.py       ← 에이전트 코어 (판단 루프)
├── main.py        ← FastAPI 서버
└── requirements.txt
```

**스택**: Python + FastAPI + Ollama(EXAONE 3.5 7.8B) + Pydantic  
**포트**: 8100 (기존 프로젝트 충돌 방지)  
**원칙**: Mock 데이터만 사용, ROS2·실제 센서 연동 없음

---

## Step 1 — 도구 정의 (tools.py)

에이전트가 호출할 수 있는 함수들을 정의한다.
지금은 Mock 데이터지만, 나중에 실제 센서·ROS2로 교체하면 된다.

```python
def get_sensor_status(zone: str = "A") -> dict:
    """구역 센서 상태 조회"""
    return {
        "zone": zone,
        "motion": random.choice([True, False]),
        "temperature": round(random.uniform(18.0, 42.0), 1),
        "humidity": round(random.uniform(30.0, 80.0), 1),
    }

def move_robot(waypoint: str) -> dict:
    """로봇 이동 명령"""
    return {"waypoint": waypoint, "status": "accepted", "eta_seconds": ...}

def send_alert(level: str, message: str) -> dict:
    """알림 발송 (info / warning / critical)"""
    ...

def get_camera_feed(zone: str) -> dict:
    """카메라 피드 상태 조회"""
    ...

def log_event(event_type: str, data: dict) -> dict:
    """이벤트 로그 기록"""
    ...

# LLM이 이름으로 호출할 수 있도록 레지스트리로 관리
TOOLS = {
    "get_sensor_status": get_sensor_status,
    "move_robot": move_robot,
    "send_alert": send_alert,
    "get_camera_feed": get_camera_feed,
    "log_event": log_event,
}
```

---

## Step 2 — 프롬프트 설계 (prompts.py)

LLM에게 역할, 도구 목록, 응답 형식을 알려주는 시스템 프롬프트가 핵심이다.
**응답을 JSON으로 강제**하는 것이 파싱 안정성에 중요하다.

```python
SYSTEM_PROMPT = """당신은 건물 보안을 담당하는 AI 에이전트입니다.

사용 가능한 도구:
1. get_sensor_status(zone)     - 구역 센서 상태 조회
2. move_robot(waypoint)        - 로봇 이동 명령
3. send_alert(level, message)  - 알림 발송
4. log_event(event_type, data) - 이벤트 기록
5. get_camera_feed(zone)       - 카메라 상태 조회

응답 형식 (반드시 JSON만):
{
  "thought": "현재 상황 판단 및 다음 행동 이유",
  "action": "도구이름 또는 FINISH",
  "action_input": {"파라미터명": "값"},
  "final_answer": "FINISH일 때만 작성"
}

완료 조건:
- 상황 파악 + 알림 발송 완료 시 FINISH
- 상황 파악 + 로봇 이동 완료 시 FINISH
- 같은 도구 두 번 호출 금지
"""
```

---

## Step 3 — 에이전트 코어 (agent.py)

판단 루프의 핵심 흐름이다.

```python
def run(self, situation: str) -> dict:
    history = []

    for i in range(self.max_iterations):
        # 1. LLM에게 상황 + 이전 이력 전달
        user_prompt = build_user_prompt(situation, history)
        response = ollama.chat(model=self.model, messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_prompt}
        ])

        # 2. 응답 파싱
        parsed = self._parse_response(response["message"]["content"])
        action = parsed.get("action", "FINISH")

        # 3. LLM 스스로 FINISH
        if action == "FINISH":
            return {"status": "done", "finish_by": "llm", ...}

        # 4. 도구 호출
        result = self._call_tool(action, parsed.get("action_input", {}))
        history.append({...})

        # 5. 강제 종료 조건 체크
        if self._should_finish(history):
            return {"status": "done", "finish_by": "auto", ...}
```

**핵심 설계 포인트**: 프롬프트만으로 종료를 제어하면 불안정하다.
`_should_finish()` 같은 **코드 레벨 강제 종료 조건**을 반드시 함께 둬야 한다.

```python
def _should_finish(self, history: list) -> bool:
    called = [h["action"] for h in history]

    # alert + 최소 2개 도구 사용
    if "send_alert" in called and len(called) >= 2:
        return True

    # 로봇 이동 + 상황 확인 완료
    if "move_robot" in called and (
        "get_sensor_status" in called or "get_camera_feed" in called
    ):
        return True

    # 중복 호출 감지
    if len(called) != len(set(called)):
        return True

    return False
```

---

## Step 4 — FastAPI 서버 (main.py)

```python
app = FastAPI(title="Guard Brain Agent", version="1.0.0")
agent = GuardBrainAgent()

@app.post("/agent/run")
def run_agent(req: SituationRequest):
    return agent.run(req.situation)
```

```bash
python main.py
# → http://0.0.0.0:8100
```

---

## 실행 결과

```bash
curl -X POST http://localhost:8100/agent/run \
  -H "Content-Type: application/json" \
  -d '{"situation": "Zone A에서 모션 감지됨. 상황을 파악하고 적절히 대응하라."}'
```

```
🤖 Guard Brain Agent 시작
📋 상황: Zone A에서 모션 감지됨. 상황을 파악하고 적절히 대응하라.

[Iteration 1/5]
  💭 Thought : Zone A 상황 파악을 위해 카메라 피드를 먼저 확인한다.
  ⚡ Action  : get_camera_feed
  📊 Result  : {"status": "motion_detected", "persons_detected": 2}

[Iteration 2/5]
  💭 Thought : 사람 2명 확인. 센서로 추가 확인한다.
  ⚡ Action  : get_sensor_status
  📊 Result  : {"motion": true, "temperature": 33.2}

[Iteration 3/5]
  💭 Thought : 모션 및 인원 확인 완료. 로봇을 현장으로 이동시킨다.
  ⚡ Action  : move_robot
  📊 Result  : {"status": "accepted", "eta_seconds": 6}

✅ 최종 판단 (자동): 현장 조치 및 상황 확인 완료
   조치 내역: ['get_camera_feed', 'get_sensor_status', 'move_robot']
```

**3번의 판단만으로 완료.** LLM이 스스로 도구를 골라 순서대로 호출하고, 각 결과를 보고 다음 행동을 결정했다.

---

## 튜닝 과정에서 배운 것

처음에는 `max_iterations_reached`가 계속 떴다.
원인을 분석하며 세 가지 인사이트를 얻었다.

**1. 프롬프트만으로 종료 제어는 불안정하다**  
LLM은 "추가 확인이 필요하다"는 판단을 계속 하려는 경향이 있다.
코드 레벨에서 강제 종료 조건을 반드시 병행해야 한다.

**2. LLM은 없는 도구를 스스로 요청한다**  
Iteration 4에서 `wait`이라는 존재하지 않는 도구를 호출했다.
로봇 이동 후 도착을 기다리는 행동이 자연스럽다고 판단한 것이다.
이는 에러가 아니라 **다음에 추가할 도구의 힌트**다.

**3. 이력(history) 포맷이 판단 품질을 결정한다**  
단순히 행동 목록만 주는 것보다, 행동과 결과를 함께 주면 LLM의 판단이 훨씬 정확해진다.

---

## 다음 단계

Phase 1 Tool Use 에이전트가 완성됐다.
다음은 **Phase 2 — ReAct 루프**다.

현재 구조는 "도구 호출 → 결과 확인 → 다음 도구"의 선형 흐름이다.
ReAct는 여기에 **"결과를 보고 계획을 수정"** 하는 능력을 추가한다.

```
현재 (Tool Use):  상황 → 도구1 → 도구2 → 도구3 → 완료
다음 (ReAct):     상황 → 도구1 → 재판단 → 도구2 → 재판단 → 완료
                              ↑ 결과에 따라 계획 변경 가능
```

`wait` 도구를 추가하고, 로봇 도착 후 재확인하는 흐름을 구현할 예정이다.

---

## 마치며

오늘 만든 것은 아주 작은 에이전트지만, 핵심 원리는 동일하다.
**목표를 주면, 스스로 판단하고, 도구를 고르고, 행동한다.**

앞으로 이 에이전트가 Kevin Patrol Fleet의 순찰 판단, EyeCon의 감정 분석 트리거, 멀티로봇 협업 오케스트레이션으로 확장되는 것을 목표로 하고 있다.

---

*전체 코드는 [GitHub](https://github.com/skong097)에 공개 예정입니다.*
