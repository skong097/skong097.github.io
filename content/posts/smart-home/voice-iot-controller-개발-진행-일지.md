---
title: "Voice IoT Controller — 개발 진행 일지"
date: 2026-03-21
draft: true
tags: ["smart-home", "esp32", "whisper", "porcupine"]
categories: ["smart-home"]
description: "> 작성일: 2026-02-22 > 프로젝트 경로: `~/dev_ws/voice_iot_controller` | 파일 | 버전 | 경로 |"
---

# Voice IoT Controller — 개발 진행 일지

> 작성일: 2026-02-22  
> 프로젝트 경로: `~/dev_ws/voice_iot_controller`

---

## 📁 현재 파일 버전

| 파일 | 버전 | 경로 |
|------|------|------|
| main.py | v0.6+ | server/main.py |
| llm_engine.py | v1.6 | server/llm_engine.py |
| command_router.py | v1.5 | server/command_router.py |
| tcp_server.py | v2.0 | server/tcp_server.py |

---

## ✅ 완료 작업

### 1. Wake Word — Porcupine "자비스야"
- 기존 한국어 "헤이 코코" → 영어 호환 문제로 교체
- `자비스야_ko_linux_v4_0_0.ppn` 정상 동작 확인
- frame: 512 samples, mic_device: 11

### 2. STT — faster-whisper
- model: small, language: ko
- 평균 인식 시간 ~1.3s
- VAD 에너지 임계값: 0.06, 최대 발화: 5.0s
- noisereduce prop_decrease: 0.85

### 3. TTS — edge-tts 마이그레이션 (v1.1)
- Kokoro onnx → edge-tts 교체 (한국어 미지원 문제)
- 음성: ko-KR-SunHiNeural (여성)
- asyncio 논블로킹, Lock으로 중복 재생 방지

### 4. LLM — qwen2.5:7b (v1.6)
- Ollama 로컬 서버 연동
- 자연어 → JSON 명령 파싱
- `cmd=null` 자유 대화 분기 처리
- **status 명령 추가** (v1.6)
  - 상태 조회 키워드 패턴 7개 추가
  - "차고 문 닫혀있니?", "외출 전 전체 점검해줘" 등

### 5. CMD Router (v1.5)
- `validate_command()` 이전에 music/status 분기 처리
  - 기존 버그: status가 validate_command에서 unknown cmd로 실패
  - 수정: music/status → validate 이전에 먼저 분기
- `_handle_status()` 추가: 디바이스 상태 조회
- `_naturalize_status()` 추가: 기계적 요약 → LLM 자연어 구어체 변환
  - LLM 있을 때: "침실 전등은 켜져 있고 커튼은 닫혀 있어요."
  - LLM 없을 때: 키워드 치환 fallback

### 6. StateManager (tcp_server.py v2.0)
- 전체 디바이스 상태 스냅샷 싱글턴 관리
- 업데이트 시점:
  - ESP32 연결 시 → 초기값 등록 (LED off, servo 0)
  - 명령 전송 시 → 낙관적 선반영
  - ACK 수신 시 → 확정 반영
  - 센서 수신 시 → temp/humidity 반영
- `start_polling()`: 30초 주기 센서 자동 쿼리
- main.py lifespan에 polling 태스크 시작/종료 연동

### 7. IoT 디바이스 제어
- LED, Servo, DHT22, DS18B20, 7-Segment 제어
- device_id="all" 전체 브로드캐스트
- 거실 음악 재생 (ytPlayer WebSocket 제어)
  - play / pause / next / prev / volume

---

## 🔧 현재 시스템 구성

```
마이크 (16kHz·int16·mic:11)
  → Porcupine "자비스야"
  → VAD + noisereduce
  → Whisper STT (small·ko·~1.3s)
  → LLM Engine (qwen2.5:7b·Ollama)
  → CMD Router
    ├── led/servo/query/seg7 → TCP → ESP32
    ├── music               → WebSocket → 브라우저 ytPlayer
    ├── status              → StateManager → 즉시 응답
    └── cmd=null            → tts_response 자유 대화
  → TTS Engine (edge-tts·ko-KR-SunHiNeural)
  → 스피커 출력

ESP32 디바이스:
  - esp32_garage   (차고)  : LED, Servo
  - esp32_entrance (현관)  : LED, Servo
  - esp32_living   (거실)  : LED, 음악재생
  - esp32_bedroom  (침실)  : LED, Servo, DHT22, 7-Segment
  - esp32_bathroom (욕실)  : LED, DS18B20
```

---

## 🚧 미완료 / 다음 작업

### 🔴 High Priority

#### 1. UnifiedStateManager — 종합 상태 관리 통합
**현재 문제:**
- ESP32 상태 → StateManager (TCP) ✅
- 음악 재생 상태 → 브라우저 JS (ytPlayer) ❌ 서버 모름
- 웹앱 연결 상태 → 별도 관리 ❌

**목표 구조:**
```
UnifiedStateManager
  ├── ESP32 디바이스 상태 (TCP ACK/센서)
  ├── 음악 재생 상태 (playing, title, volume)
  └── 웹앱 상태 (연결 클라이언트 수 등)
```

**필요 작업:**
- `tcp_server.py`: StateManager → UnifiedStateManager 확장
  - `living_room` 음악 상태 필드 추가
- `command_router.py`: `WS_TYPE_MUSIC_STATE` 수신 핸들러 추가
- **프론트 JS**: ytPlayer 이벤트 시 WS로 상태 보고
  ```js
  // play/pause/track 변경 시
  ws.send(JSON.stringify({
    type: "music_state",
    action: "play",        // play|pause|stop
    title: "곡명",
    volume: 70
  }))
  ```
- **파일 확인 필요**: `static/js/` 내 프론트 JS 파일명 확인
  ```bash
  find ~/dev_ws/voice_iot_controller -name "*.js" | grep -v node_modules
  ```

#### 2. VAD 배경음 개선
- 현재: 에너지 임계값 0.06, IDLE 구간 에너지 0.11~0.14로 노이즈 오감지
- 목표: Silero VAD 교체로 정확도 향상
- 관련 파일: `server/stt_engine.py`

### 🟡 Medium Priority

#### 3. 음악 플레이어 첫 재생 문제
- 증상: 첫 음성 명령 시 ytPlayer 미초기화로 재생 불가
- 원인: 브라우저 autoplay 정책 + ytPlayer 초기화 타이밍
- 해결 방향: 프론트에서 pending 큐 → ytPlayer 준비 후 실행

#### 4. STT 띄어쓰기 오류
- "침실 전 등 켜줘" → "침실 전등 켜줘" 로 인식 개선 필요
- 후처리 normalization 또는 LLM 프롬프트 보완

#### 5. WebSocket 큐 백로그 최적화
- 명령 연속 입력 시 큐 쌓임 현상
- 처리 중 새 명령 수신 시 이전 명령 취소 로직 검토

### 🟢 Low Priority

#### 6. ESP32 ACK 기반 상태 동기화
- 현재: 명령 전송 후 낙관적 선반영 (ACK 전)
- 개선: ACK 수신 확인 후 확정 반영 + 실패 시 rollback

#### 7. 개발 로그 자동화
- 현재: 수동으로 dev_log md 파일 작성
- 목표: 하루 마지막 커밋 시 자동 md 생성 스크립트

---

## 📝 settings.yaml 주요 설정

```yaml
# 상태 폴링 (선택, 기본 30초)
state_polling:
  interval: 30

# TTS
tts:
  provider: edge
  voice: ko-KR-SunHiNeural
  edge_rate: "+0%"
  edge_volume: "+0%"

# STT
stt:
  model: small
  language: ko
  vad_threshold: 0.06
  max_speech_duration: 5.0

# Ollama
ollama:
  host: http://localhost:11434
  model: qwen2.5:7b
  timeout: 30
  temperature: 0.1
```

---

## 🗂️ 관련 파일 목록

```
voice_iot_controller/
├── server/
│   ├── main.py              v0.6+
│   ├── llm_engine.py        v1.6
│   ├── command_router.py    v1.5
│   ├── tcp_server.py        v2.0
│   ├── stt_engine.py
│   └── tts_engine.py        v1.1
├── protocol/
│   └── schema.py
├── config/
│   └── settings.yaml
└── static/
    └── js/
        └── (프론트 JS — 파일명 확인 필요)
```
