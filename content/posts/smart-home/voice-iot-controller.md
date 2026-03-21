---
title: "🎙️ Voice IoT Controller"
date: 2026-03-21
draft: true
tags: ["smart-home", "esp32", "fastapi", "whisper", "porcupine"]
categories: ["smart-home"]
description: "> 한국어 음성 명령으로 ESP32 스마트홈 디바이스를 제어하는 로컬 IoT 시스템 [![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](ht"
---

# 🎙️ Voice IoT Controller

> 한국어 음성 명령으로 ESP32 스마트홈 디바이스를 제어하는 로컬 IoT 시스템

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Ollama](https://img.shields.io/badge/Ollama-qwen2.5%3A7b-black)](https://ollama.ai/)
[![ESP32](https://img.shields.io/badge/ESP32-Arduino-red)](https://www.espressif.com/)

---

## 📌 개요

**Voice IoT Controller**는 로컬 환경에서 동작하는 한국어 음성 인식 기반 스마트홈 제어 시스템입니다.  
외부 클라우드 없이 온프레미스 STT + LLM으로 자연어 명령을 JSON으로 변환하고, TCP/WebSocket을 통해 ESP32에 전달합니다.

```
"자비스야" → Porcupine 웨이크 워드 감지
    ↓
"침실 불 켜줘" → Whisper STT + noisereduce
    ↓
{"cmd":"led","room":"bedroom","state":"on"} → Ollama LLM (qwen2.5:7b)
    ↓
TCP → ESP32 실행 → TTS 응답 → WebSocket 브로드캐스트
```

---

## ✨ 주요 기능

- **🎙️ 로컬 STT** — faster-whisper (small 모델, 한국어 특화)
- **🧠 로컬 LLM** — Ollama qwen2.5:7b, 자연어 → JSON 명령 변환
- **🔊 웨이크 워드** — Porcupine "자비스야" (오프라인, frame=512 int16)
- **📡 ESP32 TCP 제어** — LED, 서보모터, TM1637 7세그먼트, PIR 센서
- **🌐 WebSocket 대시보드** — 실시간 디바이스 상태 모니터링
- **🗺️ HOUSE MAP** — 2D 평면도 기반 LED/상태 시각화 (Canvas)
- **🎵 거실 음악 제어** — YouTube IFrame + 음성 명령 연동
- **📊 통합 상태 관리** — UnifiedStateManager (ESP32 + 음악 + 웹앱 상태 일원화)
- **🔒 보안 모드** — PIR(HC-SR501) 기반 외출/귀가/취침/기상 4종 모드
- **🌡️ 욕실 온도 제어** — 희망온도 음성 설정 + TM1637 7세그먼트 표시
- **🔇 노이즈 리덕션** — noisereduce 0.85 배경음 억제

---

## 🏠 지원 디바이스

| Device ID | 위치 | 기능 |
|-----------|------|------|
| `esp32_garage` | 차고 | LED, 서보(차고문) |
| `esp32_entrance` | 현관 | LED, 서보(현관문) |
| `esp32_living` | 거실 | LED, YouTube 음악 |
| `esp32_bedroom` | 침실 | LED, 서보(커튼) |
| `esp32_home` | 욕실 (통합) | LED, TM1637 7세그먼트, PIR 센서 |

> v2.0부터 욕실·보안은 `esp32_home` 단일 디바이스로 통합 관리

---

## 🗂️ 프로젝트 구조

```
voice_iot_controller/
├── server/
│   ├── main.py              # FastAPI + uvicorn 진입점        v0.7
│   ├── stt_engine.py        # faster-whisper STT 엔진         v4.0
│   ├── llm_engine.py        # Ollama LLM 파싱 엔진            v2.0
│   ├── command_router.py    # 명령 라우터                     v2.4
│   ├── tcp_server.py        # ESP32 TCP 통신 + PIR 이벤트     v3.1
│   ├── tts_engine.py        # edge-tts TTS 엔진               v1.1
│   ├── websocket_hub.py     # 브라우저 WS 허브
│   └── api_routes.py        # REST API 라우트
├── protocol/
│   └── schema.py            # 명령 스키마 / 유효성 검사
├── config/
│   └── settings.yaml        # 시스템 설정
├── web/
│   └── index.html           # 대시보드 UI
├── esp32/
│   └── esp32_client_final.ino  # ESP32 펌웨어 (PIR 통합)
├── docs/                    # 개발 문서 및 가이드
├── run_server.sh            # 서버 실행 스크립트
└── requirements.txt
```

---

## ⚙️ 설치 및 실행

### 1. 사전 요구사항

```bash
# Python 3.12+
python3 --version

# Ollama 설치 및 모델 다운로드
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5:7b

# Porcupine 웨이크 워드 키 발급
# https://console.picovoice.ai/ 에서 무료 API 키 발급
```

### 2. 가상환경 및 패키지 설치

```bash
git clone https://github.com/YOUR_USERNAME/voice_iot_controller.git
cd voice_iot_controller

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### 3. 설정

```yaml
# config/settings.yaml 주요 설정
stt:
  model_size: small          # tiny / base / small / medium
  language: ko
  vad_threshold: 0.06
  max_speech_duration: 5.0

ollama:
  model: qwen2.5:7b
  host: http://localhost:11434
  timeout: 30
  temperature: 0.1

wake_word:
  keyword: "자비스야"          # Porcupine 커스텀 키워드
  access_key: "YOUR_KEY"     # Picovoice 콘솔에서 발급
  frame_length: 512          # int16 프레임

tts:
  provider: edge
  voice: ko-KR-SunHiNeural

audio:
  device_index: 11           # 마이크 디바이스 인덱스
  noise_reduce: 0.85

state_polling:
  interval: 30               # 센서 자동 폴링 주기 (초)
```

### 4. 실행

```bash
./run_server.sh
# 또는
source venv/bin/activate
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

브라우저에서 `http://localhost:8000` 접속

---

## 🎮 음성 명령 예시

### 기본 제어

| 명령 | 동작 |
|------|------|
| `"자비스야"` | 웨이크 워드 → 명령 대기 |
| `"침실 불 켜줘"` | 침실 LED ON |
| `"차고문 열어줘"` | 차고 서보 90도 |
| `"전체 다 꺼줘"` | 전체 LED + 음악 동시 OFF |
| `"전체 다 켜줘"` | 전체 LED + 음악 동시 ON |

### 음악 제어

| 명령 | 동작 |
|------|------|
| `"거실 음악 틀어줘"` | YouTube 음악 재생 |
| `"다음 곡"` | 다음 트랙 |
| `"볼륨 크게"` | 볼륨 80% |
| `"음악 꺼줘"` | 음악 정지 |

### 상태 조회

| 명령 | 동작 |
|------|------|
| `"집 전체 상태 알려줘"` | 전체 디바이스 상태 조회 |
| `"차고문 닫혀있니?"` | 차고 서보 상태 조회 |
| `"외출 전 전체 점검해줘"` | 전등 + 문 + 음악 전체 점검 |

### 🔒 보안 모드 (PIR)

| 명령 | 동작 |
|------|------|
| `"외출해"` / `"나갈게"` | 외출 모드 (PIR 방범 ON + 전체 조명 OFF) |
| `"귀가했어"` / `"집에 왔어"` | 귀가 모드 (PIR 재실 감지 ON) |
| `"잘게"` / `"취침할게"` | 취침 모드 (PIR 거실 방범 ON) |
| `"일어났어"` / `"기상"` | 기상 모드 (PIR 재실 감지 ON) |

> 방범 모드 중 침입 감지 시 → 전체 조명 ON + 웹앱 경고 알림 + CCTV 모달 팝업

### 🌡️ 욕실 온도

| 명령 | 동작 |
|------|------|
| `"욕실 25도로 설정해줘"` | 희망온도 설정 + 7세그먼트 표시 |
| `"욕실 온도 몇 도야?"` | 설정 온도 TTS 응답 (센서 없음 안내) |

---

## 📡 API

### WebSocket

```
ws://HOST:8000/ws
```

| 메시지 타입 | 방향 | 설명 |
|------------|------|------|
| `manual_cmd` | 클라이언트→서버 | 수동 명령 전송 |
| `voice_text` | 클라이언트→서버 | 브라우저 STT 결과 |
| `manual_trigger` | 클라이언트→서버 | 버튼으로 STT 활성화 |
| `music_state` | 클라이언트→서버 | ytPlayer 상태 보고 |
| `cmd_result` | 서버→클라이언트 | 명령 실행 결과 |
| `device_update` | 서버→클라이언트 | 디바이스 상태 업데이트 |
| `sensor_data` | 서버→클라이언트 | 센서 데이터 |
| `music_control` | 서버→클라이언트 | 음악 제어 |
| `wake_detected` | 서버→클라이언트 | 웨이크 워드 감지 |
| `stt_result` | 서버→클라이언트 | STT 결과 텍스트 |
| `pir_alert` | 서버→클라이언트 | PIR 침입/재실 경고 |
| `bathroom_temp_set` | 서버→클라이언트 | 욕실 희망온도 설정 동기화 |
| `query_bathroom_temp` | 서버→클라이언트 | 욕실 온도 조회 요청 |

### REST

```
POST /api/command       # 명령 직접 전송
GET  /api/devices       # 디바이스 목록
GET  /api/status        # 서버 상태
POST /pir-event         # PIR 이벤트 수신 (HTTP, 현재 TCP 대체)
```

---

## 🔒 보안 모드 상세

### 하드웨어 연결 (HC-SR501)

```
HC-SR501    ESP32
VCC    →    VIN (5V)
OUT    →    GPIO 27
GND    →    GND
```

### PIR 동작 모드

| 모드 | PIR 상태 | 동작 |
|------|----------|------|
| `guard` (외출/취침) | 방범 감시 | 움직임 감지 → 전체 조명 ON + 웹앱 경고 (30초 쿨다운) |
| `presence` (귀가/기상) | 재실 감지 | 4시간 이상 정적 → 웹앱 경고 (1회) |
| `off` | 비활성 | PIR 감지 무시 |

### 침입 감지 흐름

```
ESP32 PIR HIGH (GPIO 27)
  → allLightsOn() + sendPirEvent()
  → TCPServer._on_pir_event()
  → WS 브로드캐스트 pir_alert
  → 웹앱 PIR 카드 "⚠ 감지됨!" 점멸
  → CCTV 모달 자동 팝업
  → 로그 패널 빨간 텍스트 기록
```

---

## 📊 성능

| 항목 | 수치 |
|------|------|
| Whisper STT (small) | ~1,300ms |
| LLM 파싱 (워밍업 후) | ~600ms |
| 전체 파이프라인 | ~1,900ms |
| status 응답 (템플릿) | ~즉시 |
| 웨이크 워드 오감지 | 매우 낮음 (Porcupine) |

> 테스트 환경: Intel CPU 16코어, RAM 14GB

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| STT | faster-whisper (CTranslate2) small 모델 |
| LLM | Ollama + qwen2.5:7b |
| 웨이크 워드 | Porcupine (Picovoice) "자비스야" |
| TTS | edge-tts (ko-KR-SunHiNeural) |
| 노이즈 제거 | noisereduce 0.85 |
| 백엔드 | FastAPI + uvicorn + uvloop |
| 통신 | WebSocket, TCP Socket |
| 상태 관리 | UnifiedStateManager (ESP32 + 음악 + 웹앱) |
| 프론트엔드 | Vanilla JS + Canvas 2D |
| 음악 | YouTube IFrame API |
| 마이크로컨트롤러 | ESP32 (Arduino) + TM1637 + HC-SR501 PIR |

---

## 📝 개발 로그

| 버전 | 날짜 | 주요 변경사항 |
|------|------|--------------|
| v2.0 | 2026-02-22 | PIR 보안 모드 4종, 욕실 온도 음성 제어, 7세그먼트 웹앱 동기화 |
| v1.9 | 2026-02-22 | all_off/all_on (전등+음악 동시 제어), LLM SYSTEM_PROMPT 개선 |
| v1.8 | 2026-02-22 | Porcupine "자비스야" 웨이크 워드 버그 수정 (frame=512, mic=11) |
| v1.7 | 2026-02-22 | UnifiedStateManager 통합, status 응답 템플릿화, music_state WS 보고 |
| v1.6 | 2026-02-22 | TTS Kokoro → edge-tts 교체 |
| v1.5 | 2026-02-22 | status 명령 자연어화, CMD Router 분기 개선 |
| v1.3 | 2026-02-21 | music 명령 지원, HOUSE MAP 2D 평면도 추가 |
| v1.2 | 2026-02-21 | qwen2.5:7b 업그레이드, LLM 워밍업 추가 |
| v1.1 | 2026-02-21 | Whisper base → small, VAD 최적화 |
| v1.0 | 2026-02-xx | 최초 릴리스 |

---

## ⏳ PENDING

- [ ] `server/camera_stream.py` — USB 웹캠 MJPEG 스트리밍
- [ ] `main.py` camera_stream 라우터 등록
- [ ] Telegram / Slack / 카카오톡 침입 알림 연동
- [ ] 외출 시뮬레이션 모드 (ESP32 랜덤 스케줄러)
- [ ] Home Safe Solution (낙상 감지) 연동

---

## 🔧 알려진 이슈

- VAD energy 기반 발화 감지는 배경음이 높은 환경에서 한계 존재 → Silero VAD 교체 검토 중
- YouTube 자동재생 차단 정책 → 브라우저에서 한 번 이상 수동 재생 후 음성 제어 가능
- WebSocket 큐 백로그 → 명령 연속 입력 시 큐 쌓임, 이전 명령 취소 로직 검토 중
- 욕실 온도 센서 미설치 → 현재 희망온도 설정/조회만 지원, 실측 온도 조회 불가

---

## 📄 라이선스

MIT License

---

*Solo Developer: Stephen Kong | 2026*
