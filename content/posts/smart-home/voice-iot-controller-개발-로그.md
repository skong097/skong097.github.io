---
title: "Voice IoT Controller 개발 로그"
date: 2026-03-21
draft: true
tags: ["smart-home"]
categories: ["smart-home"]
description: "**날짜:** 2026-02-22 **작업자:** Stephen Kong **세션:** TTS 통합 및 한국어 음성 출력 완성"
---

# Voice IoT Controller 개발 로그
**날짜:** 2026-02-22  
**작업자:** Stephen Kong  
**세션:** TTS 통합 및 한국어 음성 출력 완성

---

## 작업 목표
- `missing 'cmd' field` 버그 수정
- TTS 음성 출력 파이프라인 완성 (한국어)

---

## 버그 수정

### Bug #1 — `missing 'cmd' field` (자유 대화 미응답)
- **원인:** `command_router.py`의 `_handle_voice()`에서 LLM이 `{"cmd": null, "tts_response": "..."}` 반환 시 `execute()` → `validate_command()` 호출로 에러 발생
- **수정:** `cmd=None` 자유 대화 분기 처리 추가 (`execute()` 우회)
- **파일:** `command_router.py` v1.1 → **v1.2**

```python
# v1.2 추가 코드 (_handle_voice)
if data.get("cmd") is None:
    tts = data.get("tts_response", "")
    return json.dumps({
        "type": "cmd_result",
        "status": "conversation",
        "tts_response": tts,
    })
```

---

## TTS 파이프라인 구축

### Step 1 — 디버그 스크립트 작성
- `tests/test_tts_debug.py` 작성 (7단계 진단)
- **발견:** `models/kokoro-v0_19.onnx`, `models/voices.bin` 미설치
- **발견:** `config/settings.yaml` 경로 문제 (프로젝트 루트에서 실행 필요)

### Step 2 — Kokoro 모델 다운로드 및 테스트
```bash
cd models/
wget .../kokoro-v0_19.onnx   # 310.4 MB
wget .../voices.bin           # 5.5 MB
```
- **발견:** `Voice af_heart not found` → voices.bin 영어 전용 버전
- **조치:** `voice: af_heart` → `af_sarah` 변경

### Step 3 — Kokoro 언어 오류
- **에러:** `language "en" is not supported by the espeak backend`
- **조치:** `lang: en` → `en-us` 변경 (`settings.yaml` v0.9)
- **결과:** 음성 출력되나 한국어/영어 짬뽕 (영어 목소리로 한국어 텍스트 읽음)

### Step 4 — Kokoro 한국어 목소리 확인
```bash
python3 -c "
from kokoro_onnx import Kokoro
k = Kokoro('models/kokoro-v0_19.onnx', 'models/voices.bin')
for v in k.get_voices(): print(v)
"
```
- **결과:** 한국어 목소리(`kf_`, `km_`) 없음. 영어/일본어/중국어만 지원
- **결론:** Kokoro v0.19 한국어 미지원 → 대안 검토

### Step 5 — edge-tts 채택
- **선택 이유:** 무료, 한국어 고품질, `pip install edge-tts`로 즉시 사용
- **한국어 목소리:** `ko-KR-SunHiNeural` (여성), `ko-KR-InJoonNeural` (남성)
- **테스트 통과:** 한국어 자연스럽게 출력 확인 ✅

---

## 파일 수정 내역

| 파일 | 변경 전 | 변경 후 | 주요 변경 |
|------|---------|---------|----------|
| `command_router.py` | v1.1 | **v1.2** | cmd=None 자유 대화 분기 처리 |
| `tts_engine.py` | v1.0 | **v1.1** | edge-tts provider 추가 |
| `settings.yaml` | v0.9 | **v1.0** | TTS provider kokoro → edge |
| `main.py` | v0.5 | **v0.6** | TTSEngine edge_rate/edge_volume 파라미터 추가 |

---

## settings.yaml TTS 최종 설정

```yaml
tts:
  provider: "edge"
  edge:
    voice: "ko-KR-SunHiNeural"
    edge_rate: "+0%"
    edge_volume: "+0%"
```

---

## 전체 파이프라인 (현재 동작 상태)

```
마이크
  → Porcupine ("자비스야") 웨이크워드 감지
  → VAD + Whisper small (한국어 STT)
  → LLMEngine qwen2.5:7b
      ├─ IoT 명령 → TCP → ESP32
      └─ tts_response → edge-tts (ko-KR-SunHiNeural) → 스피커
```

---

## 시스템 현재 상태

| 컴포넌트 | 상태 | 비고 |
|----------|------|------|
| 웨이크워드 | ✅ | Porcupine "자비스야" |
| STT | ✅ | Whisper small, 한국어 |
| LLM | ✅ | qwen2.5:7b (Ollama) |
| IoT 명령 | ✅ | TCP → ESP32 |
| 자유 대화 | ✅ | cmd=null 분기 처리 |
| TTS | ✅ | edge-tts ko-KR-SunHiNeural |

---

## 잔여 이슈 (다음 작업)

| 이슈 | 우선순위 | 내용 |
|------|---------|------|
| VAD 배경음 | 🔴 높음 | IDLE energy 0.11~0.14 (thresh=0.06 초과) → 발화 종료 미감지, Silero VAD 교체 검토 |
| 큐 백로그 | 🟡 중간 | LLM 처리 중 qsize 100~196 까지 쌓임 |
| STT 오인식 | 🟡 중간 | "침실 전등켜줘" → "침실 전 등켜줘" 등 띄어쓰기 오류 |

---

## 개발 원칙 (재확인)
1. 작업 전 최신 파일 업로드 확인
2. 최신 파일 기준 수정 후 통합 버전 제공
3. 순차적 버전 진행 (건너뛰기 없음)
