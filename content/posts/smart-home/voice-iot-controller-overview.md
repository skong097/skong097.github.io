---
title: "한국어 음성으로 스마트홈을 제어하다 — Voice IoT Controller 프로젝트"
date: 2026-02-22
tags:
- voice-iot
- esp32
- fastapi
- whisper
- ollama
- smart-home
- porcupine
categories:
- smart-home
summary: "\"자비스야, 침실 불 켜줘\" — 로컬 STT + LLM으로 ESP32 디바이스를 음성 제어하는 온프레미스 스마트홈 시스템 구축기"
---

---

## 왜 이 프로젝트를 시작했나

클라우드 기반 스마트홈 솔루션은 편리하지만, 네트워크 의존성과 프라이버시 문제가 항상 따라다닌다. "내 집 안의 모든 것을 내 서버에서, 내 음성으로 제어할 수 있다면?" 이라는 단순한 질문에서 **Voice IoT Controller** 프로젝트가 시작되었다.

목표는 명확했다 — **외부 클라우드 없이**, 한국어 음성 명령 하나로 집 안의 조명, 문, 커튼, 음악까지 제어하는 완전한 로컬 시스템을 만드는 것.

---

## 시스템 개요

Voice IoT Controller는 한국어 웨이크 워드 감지부터 ESP32 디바이스 제어까지 전 과정을 로컬에서 처리한다.

```
"자비스야" → 웨이크 워드 감지 (Porcupine)
     ↓
"침실 불 켜줘" → 음성 인식 (faster-whisper)
     ↓
{"cmd":"led","device_id":"esp32_bedroom","state":"on"} → LLM 파싱 (Ollama)
     ↓
TCP → ESP32 실행
```

단 4단계로, 사용자의 자연어 명령이 실제 하드웨어 동작으로 이어진다.

---

## 아키텍처

전체 시스템은 **FastAPI 단일 서버**를 중심으로 REST, WebSocket, TCP 세 가지 프로토콜을 동시에 처리하는 구조다.

```
┌──────────────────────────────────────────────────────┐
│                   INPUT PIPELINE                      │
│  🎙️ 마이크 → Whisper STT → Ollama LLM → JSON 명령   │
└─────────────────────┬────────────────────────────────┘
                      ↓
┌──────────────────────────────────────────────────────┐
│            CORE SERVER (FastAPI · Python)             │
│  REST :8000 │ WebSocket /ws │ TCP Server :9000       │
│  stt_engine · llm_engine · command_router            │
│  tcp_server · websocket_hub · tts_engine             │
└──────┬──────────────────────────────┬────────────────┘
       │ WebSocket                    │ TCP Socket
       ↓                              ↓
  Web Dashboard              ESP32 × 5대 (5개 방)
  (브라우저 실시간)           LED / 서보 / 센서 / 7세그먼트
```

핵심 설계 원칙은 **하나의 서버가 모든 것을 통합**하는 것이다. HTTP API, 브라우저 실시간 통신, ESP32 하드웨어 제어가 모두 하나의 FastAPI 앱 안에서 비동기로 동작한다.

---

## 기술 스택

| 분류 | 기술 | 역할 |
|------|------|------|
| STT | faster-whisper (small) | 로컬 한국어 음성 인식 |
| LLM | Ollama + qwen2.5:7b | 자연어 → JSON 명령 변환 |
| 웨이크 워드 | Porcupine "자비스야" | 오프라인 키워드 감지 |
| TTS | edge-tts (ko-KR-SunHiNeural) | 음성 답변 출력 |
| 노이즈 제거 | noisereduce | 배경음 억제 |
| 백엔드 | FastAPI + uvicorn | REST / WebSocket / TCP 통합 서버 |
| 상태 관리 | UnifiedStateManager | ESP32 + 음악 + 웹앱 상태 일원화 |
| 프론트엔드 | Vanilla JS + Canvas 2D | HOUSE MAP 대시보드 |
| 음악 | YouTube IFrame API | 거실 음악 음성 제어 |
| 하드웨어 | ESP32 (Arduino) | LED, 서보모터, TM1637, DHT22 |

---

## 지원 디바이스 — 5개 방

| Device ID | 위치 | 기능 |
|-----------|------|------|
| `esp32_garage` | 차고 | LED, 서보(차고문) |
| `esp32_entrance` | 현관 | LED, 서보(현관문) |
| `esp32_living` | 거실 | LED, YouTube 음악 |
| `esp32_bedroom` | 침실 | LED, 서보(커튼) |
| `esp32_bathroom` | 욕실 | LED, TM1637 7세그먼트 |

---

## 음성 명령 예시

```
"자비스야"                → 웨이크 워드 활성화
"침실 불 켜줘"            → 침실 LED ON
"차고문 열어줘"           → 차고 서보 90도
"거실 음악 틀어줘"        → YouTube 음악 재생
"볼륨 크게"               → 볼륨 80%
"전체 불 꺼줘"            → 전체 디바이스 LED OFF
"외출 전 전체 점검해줘"   → 전등 + 문 + 음악 전체 상태 응답
```

자연어 명령이 LLM을 통해 정확한 JSON 구조체로 변환되므로, "불 켜줘", "조명 ON", "라이트 온"처럼 다양한 표현을 모두 이해한다.

---

## 부팅 시퀀스

서버 시작부터 ESP32 연결까지의 흐름이 체계적으로 설계되어 있다.

```
uvicorn 실행
  → settings.yaml 로드
  → 인스턴스 생성 (TCPServer, WebSocketHub, LLMEngine, STTEngine)
  → 상호 의존성 연결
  → TCP :9000 LISTEN (ESP32 대기)
  → LLM Ollama 연결 확인
  → STT 마이크 스트림 + 웨이크 워드 대기
  → 서버 Ready
```

ESP32는 전원이 켜지면 자동으로 WiFi 연결 → TCP 서버 접속 → `register` 메시지 전송 → 명령 수신 대기 순서로 동작한다. 연결이 끊기면 자동 재연결을 시도하므로, 네트워크 불안정에도 견고하다.

---

## 성능

| 항목 | 수치 |
|------|------|
| Whisper STT (small) | ~1,300ms |
| LLM 파싱 (워밍업 후) | ~600ms |
| 전체 파이프라인 (음성→동작) | ~1,900ms |
| 상태 조회 응답 | 즉시 (템플릿) |

테스트 환경은 Intel CPU 16코어, RAM 14GB. 음성 명령 후 약 2초 내에 실제 디바이스가 반응하는 수준이다.

---

## 프로젝트 구조

```
voice_iot_controller/
├── server/
│   ├── main.py              # FastAPI + uvicorn 진입점
│   ├── stt_engine.py        # faster-whisper STT 엔진
│   ├── llm_engine.py        # Ollama LLM 파싱 엔진
│   ├── command_router.py    # 명령 라우터
│   ├── tcp_server.py        # ESP32 TCP 통신 + UnifiedState
│   ├── tts_engine.py        # edge-tts TTS 엔진
│   ├── websocket_hub.py     # 브라우저 WS 허브
│   └── api_routes.py        # REST API 라우트
├── config/
│   └── settings.yaml        # 시스템 설정
├── web/
│   └── index.html           # HOUSE MAP 대시보드
└── esp32/
    └── esp32_client.ino     # Arduino ESP32 TCP 클라이언트
```

---

## 다음 단계

현재 v1.7까지 개발이 진행되었고, 앞으로의 계획은 다음과 같다.

- **Silero VAD** 도입으로 발화 감지 정확도 향상
- **PyQt6 데스크탑 대시보드** 고급 모니터링
- **센서 데이터 시계열 저장** 및 트렌드 분석
- **다중 사용자 음성 구분** 탐색

> 다음 포스트에서는 STT/LLM 성능 최적화 과정과, 버그수정 및 TTS 음성 답변 통합에 대해 다룬다.
