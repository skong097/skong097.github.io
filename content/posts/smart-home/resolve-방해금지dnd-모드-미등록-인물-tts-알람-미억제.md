---
title: "RESOLVE — 방해금지(dnd) 모드 미등록 인물 TTS 알람 미억제"
date: 2026-03-21
draft: true
tags: ["smart-home", "esp32"]
categories: ["smart-home"]
description: "- **프로젝트:** iot-repo-1 Voice IoT Controller - **날짜:** 2026-03-07 - **상태:** ✅ 해결 완료"
---

# RESOLVE — 방해금지(dnd) 모드 미등록 인물 TTS 알람 미억제

- **프로젝트:** iot-repo-1 Voice IoT Controller
- **날짜:** 2026-03-07
- **상태:** ✅ 해결 완료
- **관련 파일:** `server/command_router.py`, `server/camera_stream.py`, `server/main.py`

---

## 증상 (요약)

방해금지 모드 활성화 상태에서 미등록 인물 감지 시:
- TTS 음성 알람 발생 (억제 안 됨)
- 웹 대시보드 `🚨 현관 미등록 인물 감지` 알람 팝업 발생

---

## 원인 분석

### 버그 #1 — `command_router.py` (_execute_pir_mode)
**파일:** `server/command_router.py` v2.4  
**위치:** `_execute_pir_mode()` 상단부 (~453번 줄)

ESP32 연결 확인(`get_device`)을 먼저 수행하고, 미연결 시 즉시 `return` 하는 구조로 인해
`self._current_pir_mode = cmd` 세팅 코드에 도달하지 못함.

```python
# 기존 코드 (버그)
pir_device = DEVICE_HOME2 if self._tcp.get_device(DEVICE_HOME2) else DEVICE_HOME
client = self._tcp.get_device(pir_device)
if not client:
    return ws_cmd_result("fail", "esp32_home2 미연결")  # ← 여기서 return

# 아래 코드 실행 안 됨
self._current_pir_mode = cmd   # ← 미실행
```

**결과:** `_current_pir_mode`가 항상 `None` → `_get_security_mode()` 가 항상 `"off"` 반환
→ `camera_stream.py`의 dnd 체크가 항상 False → 알람/TTS 억제 안 됨

---

### 버그 #2 — `camera_stream.py` (analysis_loop)
**파일:** `server/camera_stream.py` v2.1  
**위치:** `analysis_loop()` intruder 처리 블록 (539번, 625번 줄)

dnd 억제 로직이 두 곳으로 분산되어 있고 구조적 충돌 발생:

1. **539번 블록** — dnd 체크 → `_suppress_intruder = True` → `label = "clear"` 로 변환
2. **625번 블록** — `if label == "intruder"` 조건이므로 label이 이미 "clear"인 경우 진입 불가
   → cooldown 갱신 안 됨 → 30초 후 억제 없이 알람 재발생

또한 625번 블록에 dnd 체크 중복 코드가 존재했으나, 버그 #1로 인해 이 체크 자체가 무의미한 상태였음.

---

### 추가 수정 — `main.py` (보안모드 콜백 등록 순서)
**파일:** `server/main.py` v0.9  
**위치:** `lifespan()` 내 `analysis_loop` 시작 구간

기존 코드: `analysis_loop` 시작 → SmartGate 시작 → `set_security_mode_fn()` 등록  
→ `analysis_loop`가 콜백 없는 상태로 먼저 구동되는 순서 버그

수정: `set_security_mode_fn()` 등록을 `analysis_loop` 시작 **직전**으로 이동

---

## 수정 내역

### `server/command_router.py`

`_execute_pir_mode()` 내 `_current_pir_mode` 세팅 위치를 ESP32 연결 확인 **앞으로** 이동.
ESP32 미연결이어도 모드 상태는 반드시 저장되도록 수정.
dnd_mode + ESP32 미연결 시 반환값을 `fail` → `ok` 로 변경.

```python
# 수정 후
pir_mode, context = pir_map[cmd]

# ── 모드 상태 세팅: ESP32 연결 여부와 무관하게 항상 먼저 저장 ──
self._current_pir_mode = cmd
self._save_pir_mode(cmd)

pir_device = DEVICE_HOME2 if self._tcp.get_device(DEVICE_HOME2) else DEVICE_HOME
client = self._tcp.get_device(pir_device)
if not client:
    logger.warning(f"[Router] esp32_home2 미연결 — 모드={cmd} 상태는 저장됨")
    if pir_mode == "dnd":
        return ws_cmd_result("ok", "방해금지 모드 설정 완료 (ESP32 미연결 — 알람 억제 적용)")
    return ws_cmd_result("fail", "esp32_home2 미연결")
```

---

### `server/camera_stream.py`

dnd 억제 로직을 **539번 suppress 블록으로 통합**하고, 625번 알람 블록의 중복 체크 제거.
dnd 억제 시 cooldown 갱신을 suppress 블록 내에서 함께 처리.

```python
# 수정 후 (suppress 블록 내 dnd 처리)
if _suppress_intruder:
    if _suppress_reason == "dnd":
        if now - cooldown["intruder"] > COOLDOWN_SEC["intruder"]:
            cooldown["intruder"] = now
            logger.debug("[CameraStream] 방해금지 모드 — intruder 쿨다운 갱신 + 알람/TTS 억제")
    label = "clear"
    verdict["label"] = "clear"
    with _verdict_lock:
        _last_verdict["label"] = "clear"

# 625번 알람 블록 — 중복 dnd 체크 제거, 단순화
if label == "intruder":
    if now - cooldown["intruder"] > COOLDOWN_SEC["intruder"]:
        cooldown["intruder"] = now
        await ws_broadcast_fn({...})
        if tts_fn:
            await tts_fn("현관에 미등록 인물이 감지되었습니다. 확인해 주세요.")
```

---

### `server/main.py`

1. `command_router`, `camera_stream` 모듈에 대해 DEBUG 레벨 로깅 활성화 (진단용)
2. `set_security_mode_fn()` 등록을 `analysis_loop` 시작 직전으로 이동
3. `_get_security_mode()` 내부에 DEBUG 로그 추가

```python
# 디버그 로깅 (원인 확인 후 제거 가능)
logging.getLogger("server.command_router").setLevel(logging.DEBUG)
logging.getLogger("server.camera_stream").setLevel(logging.DEBUG)

# 콜백 등록 순서 수정 — analysis_loop 시작 직전
cam_mod.set_security_mode_fn(_get_security_mode)
logger.info("[CAM] 보안모드 콜백 연동 완료 (command_router → camera_stream)")

analysis_task = asyncio.create_task(
    cam_mod.analysis_loop(...)
)
```

---

## 검증 결과

```
# 방해금지 활성화 후 로그 확인
20:44:31 [DEBUG] [Router] _current_pir_mode 설정 완료: dnd_mode
20:44:31 [WARNING] [Router] esp32_home2 미연결 — 모드=dnd_mode 상태는 저장됨
20:44:32 [DEBUG] [CameraStream] 보안모드 'dnd' → intruder 억제  ✅
20:44:33 [DEBUG] [CameraStream] 보안모드 'dnd' → intruder 억제  ✅
20:44:34 [DEBUG] [CameraStream] 보안모드 'dnd' → intruder 억제  ✅
20:44:35 [DEBUG] [CameraStream] 보안모드 'dnd' → intruder 억제  ✅
```

- 방해금지 모드 활성화 후 TTS 알람 미발생 ✅
- 웹 대시보드 🚨 팝업 미발생 ✅
- 방해금지 해제(기상 모드) 후 알람 정상 복구 ✅

---

## 후속 조치

- `main.py` DEBUG 로깅 2줄은 충분한 검증 후 제거 가능
- ESP32 연결 후 dnd_mode + ESP32 연결 상태에서 재검증 권장
