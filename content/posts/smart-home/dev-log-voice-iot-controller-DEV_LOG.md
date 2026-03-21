---
title: "DEV_LOG — Voice IoT Controller"
date: 2026-03-21
draft: true
tags: ["smart-home", "esp32", "fastapi", "whisper"]
categories: ["smart-home"]
description: "Voice-Controlled IoT System 신규 프로젝트 착수. 아키텍처 설계부터 전체 모듈 구현, 웨이크 워드 통합, 버튼/웨이크 공존 트리거, UI 이중선 버그 수정, PyQt6 마이크 버튼 실제 연동까지"
---

# DEV_LOG — Voice IoT Controller

---

## 2026-02-20 | Phase 1~6 구현 + 웨이크 워드 + 버튼 트리거 + UI 버그 수정

### 작업 요약

Voice-Controlled IoT System 신규 프로젝트 착수.  
아키텍처 설계부터 전체 모듈 구현, 웨이크 워드 통합, 버튼/웨이크 공존 트리거,  
UI 이중선 버그 수정, PyQt6 마이크 버튼 실제 연동까지 완료.

---

### 1. 아키텍처 확정 (v2)

- 초기 PyQt6 단독 구성 → FastAPI 통합 서버 구조로 재설계
- FastAPI 단일 서버가 REST / WebSocket / TCP 동시 제공
- Web App (브라우저) + PyQt6 (데스크탑) 이중 클라이언트 구조 확정

```
[마이크] → [STTEngine] → ("헤이 IoT" 웨이크 워드 또는 버튼 트리거)
                ↓
         [Whisper 추론] → [LLMEngine (Ollama)]
                                  ↓
                          [FastAPI Server]
                         /       |        \
                WebSocket     REST API    TCP :9000
                    |                        |
             [Web Browser]             [ESP32 #1~N]
             [PyQt6 Dashboard]
```

---

### 2. 평면도 기반 디바이스 배치 확정

| 공간 | device_id | caps |
|------|-----------|------|
| 차고 | `esp32_garage` | LED, 서보(차고문) |
| 욕실 | `esp32_bathroom` | LED, DS18B20(온도) |
| 침실 | `esp32_bedroom` | LED, DHT22(온습도), 서보, 7세그먼트 |
| 현관 | `esp32_entrance` | LED, 서보(현관문) |

- 침실 ESP32가 가장 복잡한 유닛 (4종 caps)
- 7세그먼트(TM1637): CLK=GPIO22, DIO=GPIO23
- 서보 도어 프리셋: 열기=90도, 닫기=0도

---

### 3. 구현 파일 목록

#### server/

| 파일 | 버전 | 주요 변경 |
|------|------|----------|
| `main.py` | v0.3 | LLMEngine + STTEngine 의존성 주입, 콜백 팩토리, DISABLE_STT/LLM 플래그 |
| `tcp_server.py` | v1.0 | asyncio TCP 서버, 다중 ESP32 관리 |
| `websocket_hub.py` | v1.0 | WebSocket 연결 풀, 브로드캐스트 |
| `command_router.py` | v1.1 | `manual_trigger` WS 타입 추가, STTEngine.activate() 연동 |
| `api_routes.py` | v1.1 | `POST /stt/activate` 엔드포인트 추가 |
| `llm_engine.py` | v1.0 | Ollama LLM 연동, 자연어 → JSON 파싱 |
| `stt_engine.py` | v2.0 | 웨이크 워드 + VAD 상태머신, openwakeword + Whisper 폴백 |

#### web/ · gui/ · esp32/

| 파일 | 버전 | 주요 변경 |
|------|------|----------|
| `index.html` | v1.1 | 이중선 버그 수정, 모드 뱃지, REST+WS 이중 트리거, wake/stt WS 핸들러 |
| `dashboard.py` | v0.3 | outer/inner 패널 분리(이중선 수정), 마이크 버튼 실제 연동, 모드 뱃지 |
| `esp32_client.ino` | v1.0 | Arduino ESP32 TCP 클라이언트 |

---

### 4. 주요 기능 상세

#### STT 상태머신 (stt_engine.py v2.0)

```
IDLE → (웨이크 워드 or 버튼) → LISTENING → (발화 후 침묵 1초) → Whisper 추론 → IDLE
                                    └── 8초 타임아웃 → IDLE
```

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| `BLOCK_SIZE` | 1280 샘플 | 80ms @ 16kHz, OWW 권장 |
| `WAKE_THRESHOLD` | 0.5 | OWW 감지 신뢰도 임계값 |
| `WAKE_CONFIRM_CHUNKS` | 3회 | 연속 감지 오탐 방지 |
| `WAKE_LISTEN_SEC` | 8.0초 | 명령 대기 타임아웃 |
| `VAD_SILENCE_SEC` | 1.0초 | 발화 종료 판단 침묵 시간 |

폴백: openwakeword 미설치 시 Whisper tiny로 웨이크 워드 감지

#### 버튼 + 웨이크 워드 공존 트리거

```
[버튼 클릭]                        [헤이 IoT 발화]
  ├─ WS: {type:"manual_trigger"}      └─ OWW 자동 감지
  └─ REST: POST /stt/activate               ↓
                  ↓                  STTEngine LISTENING
         STTEngine.activate()
                  ↓
     WS broadcast: {type:"wake_detected"}
```

#### WS 메시지 타입 (서버 → 클라이언트)

| type | 발생 시점 | UI 반응 |
|------|----------|---------|
| `wake_detected` | 웨이크/버튼 트리거 | 뱃지 `LISTENING`, 마이크 초록 |
| `stt_result` | Whisper 인식 완료 | 텍스트 표시, 뱃지 `IDLE` 복귀 |
| `wake_timeout` | 8초 초과 | 뱃지 `IDLE` 복귀, warn 로그 |
| `cmd_result` | ESP32 명령 결과 | 결과 텍스트 표시 |
| `sensor_data` | ESP32 센서 수신 | 센서 값 + 차트 업데이트 |
| `device_list` | 디바이스 연결/해제 | ONLINE/OFFLINE 뱃지 |

#### API 엔드포인트 (v1.1)

```
GET  /              - Web App 서빙
GET  /devices       - ESP32 목록 + STT 상태
GET  /status        - 서버 상태 (stt_state 포함)
POST /command       - 수동 명령 전송
POST /voice         - STT 텍스트 → LLM → 명령 실행
POST /stt/activate  - 버튼 모드 트리거
GET  /ws            - WebSocket 연결
```

#### UI 이중선 버그 수정

원인: PyQt6/CSS에서 `border: 1px` + `border-top: 2px` 동시 지정 시 두 선 중첩됨

```
web/index.html  : border-top accent 선 + box-shadow 보완
dashboard.py    : QFrame#voiceOuter(cyan 2px 노출)
                    └── QFrame#voiceInner(border:none)
```

#### PyQt6 마이크 버튼 실제 연동

```
클릭 → RestPoller.activate_stt() → POST /stt/activate
  ├─ None        : 서버 미연결 안내
  ├─ ok/warn     : UI 즉시 LISTENING 선반영
  └─ fail        : 활성화 실패 로그
WS wake_detected 수신 시 정식 상태 동기화
```

---

### 5. 프로젝트 디렉터리 구조

```
voice_iot_controller/
├── server/
│   ├── __init__.py
│   ├── main.py             v0.3
│   ├── tcp_server.py       v1.0
│   ├── websocket_hub.py    v1.0
│   ├── command_router.py   v1.1
│   ├── api_routes.py       v1.1
│   ├── llm_engine.py       v1.0
│   └── stt_engine.py       v2.0
├── gui/
│   └── dashboard.py        v0.3
├── web/
│   └── index.html          v1.1
├── protocol/
│   ├── __init__.py
│   └── schema.py           v1.0
├── esp32/
│   └── esp32_client.ino    v1.0
├── config/
│   └── settings.yaml       v1.0
├── docs/
│   ├── voice_iot_plan_v2.md
│   └── DEV_LOG.md
└── requirements.txt
```

---

### 6. requirements.txt

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
websockets>=12.0
httpx>=0.27.0
faster-whisper>=1.0.0
sounddevice>=0.4.6
numpy>=1.24.0
ollama>=0.1.9
openwakeword>=0.6.0
PyQt6>=6.6.0
pyqtgraph>=0.13.0
pyyaml>=6.0.1
requests>=2.31.0
```

---

### 7. 실행 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# 웨이크 워드 모델 다운로드
python -c "from openwakeword.utils import download_models; download_models()"

# 풀 모드 실행 (STT + LLM)
cd ~/dev_ws/voice_iot_controller
uvicorn server.main:app --host 0.0.0.0 --port 8000

# 서버만 실행 (STT/LLM 비활성화)
DISABLE_STT=1 DISABLE_LLM=1 uvicorn server.main:app --host 0.0.0.0 --port 8000

# PyQt6 대시보드
python -m gui.dashboard

# Web App
http://localhost:8000
```

---

### 8. 다음 작업 (TODO)

- [ ] `server/__init__.py`, `protocol/__init__.py` 생성
- [ ] `device_id: "all"` 전체 명령 브로드캐스트 처리
- [ ] Phase 7: E2E 통합 테스트
- [ ] ESP32 4개 유닛 실제 업로드 및 연결 테스트
- [ ] 커스텀 "헤이 IoT" 웨이크 워드 모델 학습
- [ ] Web App 반응형 모바일 레이아웃 개선

---

*Voice IoT Controller · DEV_LOG · 2026-02-20*

---

## 2026-02-21 | 웨이크 워드 디버깅 + STT 파이프라인 개선 + UI 클리어 구현

### 작업 요약

STT 음성 인식 파이프라인 전반 디버깅 및 안정화.  
openwakeword 0.4.0 API 호환성 문제 해결, 웨이크 워드 모델 확정,  
STT 결과 자동 클리어, LLM 웨이크 워드 노이즈 필터 개선까지 완료.

---

### 1. STT 결과 전처리 개선 (`stt_engine.py`)

**문제:** Whisper가 웨이크 워드를 `"해, IOT, 해, IOT, 침실 불거죠."` 형태로 변환  
→ LLM이 명령을 이해 못하는 원인

**해결:** `_clean_text()` 정규식 패턴 보강
```python
wake_patterns = [
    r"(헤[이]?\s*[,.]?\s*아?이?오?티[,.]?\s*)+",
    r"(해[이]?\s*[,.]?\s*[Ii][Oo][Tt][,.]?\s*)+",
    r"([Hh]ey\s*[,.]?\s*[Ii][Oo][Tt][,.]?\s*)+",
    r"(헤이\s*[Ii][Oo][Tt][,.]?\s*)+",
]
# "해, IOT, 해, IOT, 침실 불거죠." → "침실 불거죠."
```

---

### 2. 음성 인식창 자동 클리어 (웹앱 + 대시보드 동일 적용)

**문제:** STT 결과가 화면에 계속 남아 다음 명령 구분 불가

**해결:** QTimer / setTimeout 으로 자동 클리어

| 이벤트 | 동작 |
|--------|------|
| `stt_result` 수신 | 🔄 처리 중 표시 (파란색) → 3초 후 클리어 |
| `cmd_result` 수신 | ✅/❌ 결과 표시 → 4초 후 클리어 |
| 클리어 후 | 힌트 문구 복원 `"Hey Jarvis라고 말하세요"` |

**수정 파일:** `dashboard.py`, `index.html`

---

### 3. `cmd_result` 중복 핸들러 제거 (`dashboard.py`)

840번 줄 구버전 핸들러와 870번 줄 신버전 핸들러 중복 발생  
→ 구버전 제거, 신버전(아이콘 + 클리어 타이머) 단일 유지

---

### 4. ESP32 업로드 가이드 작성

`docs/ESP32_UPLOAD_GUIDE.md` 신규 작성
- 4개 유닛(차고/욕실/침실/현관) 핀맵 배선도
- Arduino IDE 설정 + 라이브러리 설치
- 시리얼 로그 정상 예시
- 업로드 체크리스트 + 트러블슈팅

**핀 충돌 검증 결과:** 전체 안전 ✅

---

### 5. openwakeword 0.4.0 API 호환성 문제 해결 (`stt_engine.py`)

**문제 추적 과정:**

| 단계 | 증상 | 원인 |
|------|------|------|
| 1차 | OWW 감지 안 됨 | `Model()` 로드 시 `prediction_buffer` 키 `[]` 반환 |
| 2차 | 초기화 실패 | `wakeword_models` 파라미터 없음 (0.4.0 API 변경) |
| 3차 | 키 비어있음 | 첫 `predict()` 호출 전에는 키가 채워지지 않음 |

**최종 해결:**
```python
# 0.4.0 정확한 API: wakeword_model_paths
oww = Model(wakeword_model_paths=[model_path])

# 더미 추론으로 prediction_buffer 키 초기화
dummy = np.zeros(1280, dtype=np.int16)
oww.predict(dummy)
keys = list(oww.prediction_buffer.keys())  # → ['hey_jarvis_v0.1']

# 실제 키로 wake_word 자동 갱신
self.wake_word = keys[0]
```

---

### 6. 웨이크 워드 모델 확정 — `hey_jarvis_v0.1`

**문제:** 한국어 "헤이 코코" 발음이 모든 영어 모델에서 스코어 0.0001 미만

**모델별 테스트 결과 ("헤이 코코" 발음):**

| 모델 | 최고 스코어 |
|------|------------|
| hey_jarvis_v0.1 | 0.0005 ← 최고 |
| alexa_v0.1 | 0.0002 |
| hey_mycroft_v0.1 | 0.0001 |
| hey_marvin_v0.1 | 0.0000 |

**결론:** 한국어 웨이크 워드는 영어 모델로 감지 불가  
→ **"Hey Jarvis"** 영어 웨이크 워드로 확정 (임시)  
→ 향후 커스텀 한국어 모델 학습 예정

---

### 7. 수정 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `server/stt_engine.py` | OWW 0.4.0 API 수정, 웨이크 워드 패턴 보강, hey_jarvis 확정 |
| `server/main.py` | 배너 문구 헤이코코→Hey Jarvis |
| `config/settings.yaml` | wake_word: hey_jarvis |
| `gui/dashboard.py` | 자동 클리어, cmd_result 중복 제거, 힌트 문구 |
| `static/index.html` | 자동 클리어, cmd_result 아이콘, 힌트 문구 |
| `docs/ESP32_UPLOAD_GUIDE.md` | 신규 작성 |
| `docs/RUN_AND_TEST.md` | 신규 작성 |

---

### 8. 다음 작업 (TODO)

- [ ] `server/__init__.py`, `gui/__init__.py` 생성 + 패키지 정리
- [ ] DEV_LOG.md 지속 업데이트
- [ ] 커스텀 한국어 웨이크 워드 ("헤이 코코") 모델 학습
- [ ] ESP32 4개 유닛 실제 업로드 및 연결 테스트
- [ ] Web App 반응형 모바일 레이아웃 개선
- [ ] 반응 속도 최적화 (Whisper tiny 모델 검토)

---

*Voice IoT Controller · DEV_LOG · 2026-02-21*
