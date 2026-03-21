---
title: "ISSUE — 방해금지(dnd) 모드 미등록 인물 TTS 알람 미억제"
date: 2026-03-21
draft: true
tags: ["smart-home"]
categories: ["smart-home"]
description: "- **프로젝트:** iot-repo-1 Voice IoT Controller - **날짜:** 2026-03-07 - **상태:** 🔴 미해결"
---

# ISSUE — 방해금지(dnd) 모드 미등록 인물 TTS 알람 미억제

- **프로젝트:** iot-repo-1 Voice IoT Controller
- **날짜:** 2026-03-07
- **상태:** 🔴 미해결
- **관련 파일:** `server/camera_stream.py`, `server/command_router.py`, `web/index_dashboard.html`

---

## 증상

방해금지 모드 활성화 상태에서 미등록 인물 감지 시:
- TTS 음성 알람 발생 (억제 안 됨)
- 웹 대시보드 `🚨 현관 미등록 인물 감지` 알람 팝업 발생

---

## 원인 추적 과정

### 1단계 — 코드 수정 (`camera_stream.py` v2.1)
- `elif label == "intruder"` 블록에 `_is_dnd` 체크 추가
- `logger.debug("[CameraStream] 방해금지 모드 — 미등록 인물 알람 억제")` 추가
- **결과:** 코드 반영 확인 (`grep` 636번 줄) → 그러나 TTS 여전히 발생

### 2단계 — `_get_security_mode()` 콜백 확인
- `main.py` 468번: `_get_security_mode()` 정의 확인
- `main.py` 476번: `set_security_mode_fn()` 연동 확인
- 변환 로직: `"dnd_mode"` → `"dnd"` 정상
- **결과:** 콜백 연결은 정상

### 3단계 — `_current_pir_mode` 값 확인
- 서버 로그에서 `dnd`, `PIR`, `방해금지` 관련 로그 **전혀 없음**
- 방해금지 버튼 클릭해도 `command_router`에 `dnd_mode` 도달 안 함

### 4단계 — 브라우저 WebSocket Send 메시지 확인
- Chrome DevTools → Network → Socket → Messages → Send 필터
- 방해금지 버튼 클릭 시 전송 메시지:
  ```json
  {"type":"llm_cmd", "cmd":"dnd_mode"}
  ```
- **결과:** 브라우저는 정상적으로 전송 중

### 5단계 — `websocket_hub` → `command_router` 연결 확인
- `ws_hub._on_message = command_router.handle` (main.py 346번) 확인
- `llm_cmd` 수신 로그는 찍힘 (`[WS] ← ws_client_0007: type=llm_cmd`)
- `command_router` 로그는 **전혀 없음**
- `on_message 오류` 로그도 없음

### 6단계 — `execute()` 내부 진입 여부 미확인
- `llm_cmd` → `execute()` → `dnd_mode` 분기 코드는 정상
- 그러나 `execute()` 내부에서 **조용히 실패** 가능성 있음
- **디버그 로그 추가 필요** → 미완료 상태

---

## 현재 가설

`execute()` 진입은 되는데 내부에서 예외 없이 조용히 종료되거나,  
`llm_cmd` 수신 후 `command_router.handle()` 자체가 호출되지 않는 상황.

---

## 다음 액션

1. `server/command_router.py` 업로드
2. `execute()` 및 `handle()` 진입부에 디버그 로그 추가:
   ```python
   logger.debug(f"[Router] execute() 진입 — cmd={data.get('cmd')}")
   logger.debug(f"[Router] handle() 진입 — type={data.get('type')}")
   ```
3. 서버 재시작 후 방해금지 버튼 클릭 → 로그 확인
4. `_get_security_mode()` 반환값 직접 로깅 추가:
   ```python
   logger.debug(f"[CameraStream] security_mode={_get_security_mode()}")
   ```

---

## 참고

- `camera_stream.py` v1.9: `_suppress_intruder` 플래그로 `label → clear` 변환 로직 존재
- v2.1 추가 코드는 알람 브로드캐스트/TTS 단계에서 dnd 재체크
- 두 단계 모두 `_get_security_mode() == "dnd"` 조건 동일
- `command_router._current_pir_mode`가 `None`이면 `_get_security_mode()`는 `"off"` 반환
- **결론: `_current_pir_mode`가 `dnd_mode`로 세팅되지 않는 것이 근본 원인**
