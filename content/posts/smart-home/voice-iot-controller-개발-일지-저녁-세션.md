---
title: "Voice IoT Controller — 개발 일지 (저녁 세션)"
date: 2026-03-21
draft: true
tags: ["smart-home", "esp32"]
categories: ["smart-home"]
description: "- 브라우저 WS 연결 후 정확히 1초 만에 끊김 → 3초 후 재연결 무한 반복 - `cam_verdict` Command Log 미기록 `ws_debug.log` 분석 결과:"
---

# Voice IoT Controller — 개발 일지 (저녁 세션)
## 작업일: 2026-02-24
## 세션: 저녁 (20:40 ~ 종료)
## 주제: WebSocket 끊김 해결 + PIR 알림 해제 LED 복원 + 방해금지 모드 추가

---

## 1. WebSocket 3초 주기 끊김 이슈 해결 ✅

### 증상
- 브라우저 WS 연결 후 정확히 1초 만에 끊김 → 3초 후 재연결 무한 반복
- `cam_verdict` Command Log 미기록

### 원인 파악
`ws_debug.log` 분석 결과:
```
[WS] broadcast 실패 (ws_client_0001): data is a dict-like object
```
- `websocket_hub.py broadcast(message: str)` — `send_text()`는 str만 허용
- `main.py`에서 `command_router.handle()` 반환값(dict)을 그대로 `ws_hub.broadcast(result)` 전달
- `camera_stream.py`의 `ws_broadcast_fn=ws_hub.broadcast`도 동일하게 dict 전달
- 예외 발생 → 모든 클라이언트 강제 해제 → 재연결 반복

### 해결 — `server/websocket_hub.py`

```python
# 수정 전
async def broadcast(self, message: str):
    ...
    await ws.send_text(message)   # dict 전달 시 예외

# 수정 후
async def broadcast(self, message: str | dict):
    if isinstance(message, dict):
        message = json.dumps(message, ensure_ascii=False)
    ...
    await ws.send_text(message)
```

**수정 파일:** `server/websocket_hub.py` — `broadcast()` 시그니처 및 dict 직렬화 처리 추가

---

## 2. PIR 침입 알림 해제 시 LED 미복원 버그 수정 ✅

### 증상
- PIR 감지 → LED 전체 점등 → CCTV/CAM 모달의 **확인·해제 버튼** 클릭 시 LED가 꺼지지 않고 계속 켜져 있음

### 원인
- `dismissAlert()` / `camAlertConfirm()` 함수가 모달만 닫고 서버에 LED 복원 명령을 전송하지 않음
- 서버의 `_led_snapshot` 복원 로직은 모드 전환 시에만 실행됨

### 해결

**`server/command_router.py` — `_execute_pir_dismiss()` 신규 추가**
```python
async def _execute_pir_dismiss(self, data: dict) -> str:
    """
    _led_snapshot 있으면 → 이전 LED 상태 복원
    스냅샷 없으면       → all_off (안전장치)
    복원 후 ws_device_update 브로드캐스트
    """
```

**`web/index.html` — 두 함수 모두 `sendCmd` 추가**
```javascript
// dismissAlert() — CCTV 모달 확인 버튼
sendCmd({ cmd: 'pir_dismiss', device_id: 'esp32_home' });

// camAlertConfirm() — CAM 알람 모달 확인 버튼
sendCmd({ cmd: 'pir_dismiss', device_id: 'esp32_home' });
```

| 팝업 | 버튼 | 처리 |
|---|---|---|
| CCTV 모달 (PIR 감지) | ✅ 확인 — 해제 | `dismissAlert()` → `pir_dismiss` |
| CAM 알람 모달 (얼굴 인식) | ✅ 확인 — 경고 해제 | `camAlertConfirm()` → `pir_dismiss` |

---

## 3. 보안 모드 방해금지(DnD) 추가 — 5번째 PIR 모드 ✅

### 요구사항
- 현관 PIR 및 카메라 얼굴 감지 외 모든 센서 알람 무시
- 기록은 계속 유지 (`[방해금지]` 태그로 구분)
- 총 5개 버튼: 외출 / 귀가 / 취침 / 기상 / **방해금지**

### 구현

**`web/index.html`**

| 항목 | 내용 |
|---|---|
| 버튼 그리드 | 4컬럼 → 5컬럼 |
| 버튼 | `🔕 방해금지` (보라색 `active-dnd` 스타일) |
| status dot | 보라색 `dnd` dot 추가 |
| `PIR_MODE_CONFIG` | `dnd_mode` 등록 |
| `handlePirAlert()` | 현관 PIR(away/sleep context) → 알람 유지, 나머지 → 로그만 |
| `handleCamAlert()` | `intruder` → 항상 허용, `delivery` → 무시+기록 |

**알람 동작표:**

| 이벤트 | 방해금지 시 | 기록 |
|---|---|---|
| 현관 PIR 침입 감지 | ✅ 알람 유지 | ✅ |
| 현관 CAM intruder | ✅ 알람 유지 | ✅ |
| 기타 PIR 감지 | 🔕 알람 무시 | ✅ `[방해금지]` |
| 택배(delivery) 감지 | 🔕 알람 무시 | ✅ `[방해금지]` |

**`server/command_router.py`**
```python
# pir_map에 dnd_mode 추가
"dnd_mode": ("dnd", "dnd")

# dnd 시 ESP32 명령 없이 서버 로그만 기록 후 즉시 반환
if pir_mode == "dnd":
    logger.info("[Router] 방해금지 모드 설정 — 현관 PIR/CAM 외 알람 무시 (기록 유지)")
    return ws_cmd_result("ok", msg)
```

---

## 4. 수정 파일 목록

| 파일 | 버전 | 주요 수정 |
|---|---|---|
| `server/websocket_hub.py` | - | `broadcast()` dict 직렬화 지원 |
| `server/command_router.py` | v2.5 | `pir_dismiss` 핸들러, `dnd_mode` 추가 |
| `web/index.html` | - | `dismissAlert` / `camAlertConfirm` LED 복원, 방해금지 버튼 및 필터 로직 |

---

## 5. 현재 상태 (2026-02-24 종료 기준)

```
✅ 얼굴 DB 등록 완료 (stephen 28장)
✅ KNOWN: stephen 정상 판정
✅ WebSocket 끊김 이슈 해결 (broadcast dict 직렬화)
✅ PIR 모드 LED 상태 복원 버그 수정 (pir_dismiss)
✅ CCTV 모달 확인 버튼 LED 복원 연동
✅ CAM 알람 모달 확인 버튼 LED 복원 연동
✅ 방해금지(DnD) 모드 추가 — 총 5개 PIR 버튼
✅ cam_verdict WS 브로드캐스트 정상 동작 확인
⬜ 침입 감지 E2E 테스트
⬜ InsightFace threshold 현장 튜닝 (현재 0.45)
⬜ cam_verdict Command Log 실출력 확인
```

---

## 6. 다음 세션 작업 예정

- 침입 감지 E2E 테스트 (외출 모드 → PIR 감지 → CAM 판정 → 알림 → 해제 전체 흐름)
- InsightFace cosine threshold 현장 튜닝 (현재 0.45, 오인식률 확인)
- cam_verdict Command Log 실출력 확인 (WS 안정화 이후)
