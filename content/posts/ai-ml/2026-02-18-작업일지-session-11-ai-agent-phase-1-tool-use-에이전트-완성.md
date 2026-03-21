---
title: "2026-02-18 작업일지 (Session 11: AI Agent Phase 1 — Tool Use 에이전트 완성)"
date: 2026-03-21
draft: true
tags: ["ai-ml", "llm", "exaone"]
categories: ["ai-ml"]
description: "**작성일**: 2026-02-18 **세션**: Session 10 이후 추가 작업 기존 프로젝트와 완전 독립된 환경에서"
---

# 2026-02-18 작업일지 (Session 11: AI Agent Phase 1 — Tool Use 에이전트 완성)

**작성일**: 2026-02-18  
**세션**: Session 10 이후 추가 작업

---

## 작업 개요

기존 프로젝트와 완전 독립된 환경에서  
**Guard Brain Tool-Use Agent v1** 개발 및 동작 검증 완료.

---

## 1. 환경 구축 ✅

```
~/dev_ws/ai_agent/guard_brain_agent/
├── venv/            ← 독립 가상환경 (ai_agent_venv)
├── config.py
├── tools.py
├── prompts.py
├── agent.py
├── main.py
├── requirements.txt
└── logs/
```

**설치 패키지**: fastapi, uvicorn, ollama, pydantic, python-dotenv  
**사용 모델**: exaone3.5:7.8b (Ollama 로컬)  
**서버 포트**: 8100 (기존 프로젝트 충돌 방지)

---

## 2. 구현 내용

### tools.py — Mock 도구 5개
| 도구 | 기능 |
|------|------|
| `get_sensor_status(zone)` | 구역 센서 상태 조회 (motion, temp, humidity) |
| `move_robot(waypoint)` | 로봇 이동 명령 |
| `send_alert(level, message)` | 알림 발송 (info/warning/critical) |
| `log_event(event_type, data)` | 이벤트 로그 기록 |
| `get_camera_feed(zone)` | 카메라 상태 조회 |

### agent.py — Tool Use 루프
- LLM이 상황을 보고 도구 선택 → 호출 → 결과 관찰 → 재판단
- `_should_finish()` 강제 종료 조건 3가지:
  1. `send_alert` 완료 + 최소 2개 도구 사용
  2. `move_robot` + 센서/카메라 확인 완료
  3. 같은 도구 중복 호출 감지
- `finish_by`: llm(LLM 스스로) / auto(강제 종료) 구분

### prompts.py — 시스템 프롬프트
- JSON 응답 형식 강제
- 완료 조건 명시
- 도구 중복 호출 금지 규칙

---

## 3. 테스트 결과

**입력 상황**: `"Zone A에서 모션 감지됨. 상황을 파악하고 적절히 대응하라."`

**최종 성공 실행 (3 iterations):**
```
Iteration 1: get_camera_feed   → 사람 2명 감지
Iteration 2: get_sensor_status → 모션 true, 온도 33.2도
Iteration 3: move_robot        → 로봇 이동 명령
→ status: done / finish_by: auto
```

**튜닝 과정:**
| 시도 | 문제 | 해결 |
|------|------|------|
| 1차 | max_iterations_reached | 프롬프트에 종료 조건 추가 |
| 2차 | max_iterations_reached | 히스토리 포맷 개선 |
| 3차 | "wait" 없는 도구 호출, 중복 호출 | agent.py에 강제 종료 조건 추가 |
| 4차 | **✅ 3 iterations에 done** | 완성 |

---

## 4. 발견된 인사이트

- LLM은 **없는 도구(`wait`)를 스스로 요청** → 향후 추가할 도구 힌트
- 프롬프트만으로 종료 제어는 불안정 → **코드 레벨 강제 종료 조건 필수**
- Mock 데이터의 랜덤성으로 매 실행마다 다른 판단 흐름 → 에이전트 유연성 확인

---

## 5. Phase 1 완성 기준 달성

- [x] 독립 환경 구축 (기존 프로젝트 영향 없음)
- [x] Tool Use 패턴 구현
- [x] LLM 자율 도구 선택
- [x] FastAPI 서버로 REST API 제공
- [x] 3 iterations 안에 완료

---

## 다음 세션 (Phase 2 후보)

1. **`log_event` 활용** — 에이전트 판단 이력을 파일로 저장
2. **시나리오 다양화** — 화재, 침입, 센서 오류 등 상황별 테스트
3. **ReAct 루프** — `wait` 도구 추가 + 로봇 도착 후 재확인 흐름
4. **블로그 포스트 초안** — 오늘 만든 것 정리해서 첫 ai-agent 포스팅
