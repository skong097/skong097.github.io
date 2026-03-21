---
title: "DEV_LOG — 보안 조치 완료 + SmartGate trigger_welcome 구현 + WS 403 근본 해결"
date: 2026-03-21
draft: true
tags: ["robot-security", "hmac", "2fa"]
categories: ["robot-security"]
description: "- **프로젝트:** iot-repo-1 Voice IoT Controller - **작업자:** Stephen Kong - **날짜:** 2026-03-07"
---

# DEV_LOG — 보안 조치 완료 + SmartGate trigger_welcome 구현 + WS 403 근본 해결

- **프로젝트:** iot-repo-1 Voice IoT Controller
- **작업자:** Stephen Kong
- **날짜:** 2026-03-07
- **세션 목표:** 보안 조치 마무리 + SmartGate trigger_welcome() 전체 흐름 검증

---

## 완료 항목

### ✅ 1 — SmartGate `_entrance_light_on()` 버그 수정

- **파일:** `server/smartgate/manager.py`
- **문제:** `from protocol.schema import cmd_light` — 존재하지 않는 함수 호출 → ImportError
- **수정:**
  - `cmd_light` → `cmd_led` + `ROOM_LED_PIN.get("entrance", 0)` 으로 교체
  - HMAC 서명 (`esp32_secure.build_signed_packet`) 적용 (실패 시 평문 fallback)

---

### ✅ 2 — WebSocket 403 근본 원인 해결 (재발 방지)

- **파일:** `web/index_dashboard.html`, `server/api_routes.py`

#### 근본 원인
- `ws.onclose` → `setTimeout(connectWS, 3000)` 호출 시 `async connectWS`의 Promise를 무시
- `fetchToken()` 완료 전에 다음 재연결 시도가 큐에 쌓이는 **레이스 컨디션** 발생
- 여러 탭이 열려있으면 각각 독립적으로 재연결 루프를 돌며 토큰 없는 연결 시도

#### 수정 내용 — `index_dashboard.html`

| 항목 | 수정 내용 |
|------|----------|
| `_isConnecting` 플래그 추가 | 중복 연결 시도 원천 차단 |
| 재연결마다 `fetchToken()` 항상 실행 | 만료 토큰으로 연결 시도 방지 |
| `ws.onopen/onclose`에서 `_isConnecting = false` 해제 | 정상 흐름 보장 |

#### 수정 내용 — `api_routes.py`

| 항목 | 수정 내용 |
|------|----------|
| 토큰 없는 연결 즉시 거부 | `accept` 전에 `close(1008)` 처리 |
| 로그 레벨 분리 | 토큰 없음 → `DEBUG`, 위조/만료 → `WARNING` |

---

### ✅ 3 — `api_routes.py` 얼굴 등록 500 오류 수정

- **파일:** `server/api_routes.py`
- **문제:** `smartgate_register_face()` 내부에 `import cv2` 누락 → `NameError: name 'cv2' is not defined`
- **수정:** `import numpy as np` 바로 아래에 `import cv2` 추가

---

### ✅ 4 — `trigger_welcome()` 시뮬레이션 테스트 엔드포인트 추가

- **파일:** `server/main.py`
- **추가 엔드포인트:** `POST /debug/smartgate/welcome-test`
- **용도:** ESP32 보드 없이 `welcome_pending = True` 강제 세팅 후 PIR 트리거 테스트
- **TODO:** 실제 배포 전 제거

---

### ✅ 5 — SmartGate 전체 2FA 흐름 실물 검증 완료

**테스트 환경:** ESP32-CAM 연결, mediapipe 0.10.14 설치

**검증된 전체 흐름:**

```
SmartGate ARM
    → 얼굴 인식 (InsightFace buffalo_sc ArcFace) ✅
    → Liveness yaw 챌린지 (mediapipe 0.10.14) ✅
    → 제스처 인증 [1, 0, 3] ✅
    → 게이트 오픈 (서보 5초) ✅
    → welcome_pending = True
    → 현관 PIR 감지 (POST /pir-event) ✅
    → 💡 현관 조명 ON (TCP → ESP32, 보드 연결 시)
    → 🔊 TTS "Stephen님 어서오세요. 환영합니다." ✅
```

**보안 로직 검증:**
- 3단계(얼굴 + Liveness + 제스처) 모두 통과해야만 `welcome_pending = True`
- 120초 쿨다운 초과 시 자동 만료
- `_welcome_done = True`로 중복 실행 방지 (1회만)
- 일반 PIR 감지(인증 없음)는 로그만 기록, 환영 동작 없음

---

### ✅ 6 — mediapipe 설치 (Liveness 활성화)

```bash
pip install mediapipe==0.10.14 --break-system-packages
```

- 설치 전: `[WARNING] mediapipe 미설치 — Liveness 비활성화` → FACE_OK 즉시 진입
- 설치 후: yaw 챌린지 정상 동작 확인

---

## 보류 항목 (Todo)

| 항목 | 사유 |
|------|------|
| MEDIUM-5 — UDP MJPEG IP 필터링 | 사무실 환경 + ESP32-CAM 고정 IP 필요 |
| MEDIUM-4 — ESP32 OTA 서명 검증 | ESP-IDF 별도 설치 세션 필요 |
| LOW — pip-audit CVE 스캔 자동화 | 장기 |
| LOW — ESP32 JTAG 디버그 포트 비활성화 | 장기 |
| LOW — 보안 이벤트 감사 로그 별도 저장 | 장기 |
| `trigger_welcome()` 현관 조명 ON 물리 테스트 | ESP32 보드 TCP 연결 시 |
| `/debug/smartgate/welcome-test` 엔드포인트 제거 | 배포 전 |

---

## 수정된 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `server/smartgate/manager.py` | `_entrance_light_on()` cmd_light → cmd_led + HMAC 서명 |
| `web/index_dashboard.html` | `_isConnecting` 플래그, 재연결마다 `fetchToken()` 실행 |
| `server/api_routes.py` | WS 토큰 없는 연결 즉시 거부 + `import cv2` 누락 수정 |
| `server/main.py` | `/debug/smartgate/welcome-test` 디버그 엔드포인트 추가 |

---

## 참조

- 보안 가이드: `security_output/`
- IoT 보안 플랜: `IoT_Security_Plan.xlsx`
- ESP32 HMAC 검증: `docs/esp32_hmac_verify.cpp`
- SmartGate 설정: `config/settings.yaml` → `smartgate` 섹션
