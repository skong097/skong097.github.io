---
title: "\"자비스야\"가 들리기까지 — 웨이크워드 디버깅과 TTS 통합"
date: 2026-02-22
tags:
- voice-iot
- porcupine
- wake-word
- tts
- edge-tts
- vad
- debugging
- noisereduce
categories:
- smart-home
summary: "Porcupine 웨이크워드가 안 되던 원인 추적, VAD 에너지 임계값 튜닝, 그리고 edge-tts로 음성 답변을 달기까지의 기록"
---

---

## 버그수정 #1 — 웨이크 워드가 안 들린다

Voice IoT Controller의 첫 번째 난관은 웨이크 워드였다. 시스템 설정에는 `"헤이 코코"`라고 되어 있었지만, Porcupine 커스텀 모델은 `"자비스야"`로 학습되어 있었다. 웨이크 워드 불일치.

### 원인과 수정

문제는 단순했지만, 발견하기까지 시간이 걸렸다.

```yaml
# config/settings.yaml — 수정 전
wake_word:
  keyword: "헤이 코코"

# 수정 후
wake_word:
  keyword: "자비스야"
```

`.ppn` 모델 경로도 함께 맞추고, `stt_engine.py`에서 Porcupine 초기화 파라미터를 정리했다. 이후 "자비스야" 감지가 정상 작동.

### noisereduce 도입

웨이크 워드 감지율을 높이기 위해 `noisereduce` 라이브러리를 도입했다. 배경 소음이 있는 환경에서 Porcupine의 오감지/미감지를 줄여준다.

```python
# stt_engine.py v4.0
import noisereduce as nr

# 오디오 프레임 전처리
audio_clean = nr.reduce_noise(
    y=audio_frame,
    sr=16000,
    prop_decrease=0.85
)
```

`prop_decrease=0.85`는 배경음의 85%를 억제하면서도 음성 신호는 보존하는 균형점이다.

### 최종 버전

| 파일 | 버전 |
|------|------|
| `stt_engine.py` | v4.0 |
| `main.py` | v0.5 |
| `settings.yaml` | v0.5 |

핵심 파라미터: `frame=512 int16`, Whisper base → small, `noisereduce 0.85`, `mic=11`

---

## 버그수정 #2 — VAD 에너지 임계값 문제

웨이크 워드가 감지된 후, 사용자의 실제 발화를 캡처하는 VAD(Voice Activity Detection)에서 두 번째 문제가 발생했다.

### 증상

조용한 환경에서는 정상이지만, 에어컨이나 선풍기가 돌아가면 발화가 감지되지 않거나, 반대로 소음만으로 녹음이 시작되는 현상.

### 디버그 모드 구축

원인을 파악하기 위해 실시간 에너지 로그를 추가했다.

```python
# stt_engine.py v4.1-debug
if self.debug_mode:
    energy = np.sqrt(np.mean(audio_frame ** 2))
    logger.debug(f"VAD energy: {energy:.4f} | threshold: {self.vad_threshold}")
```

로그를 관찰한 결과, 배경 소음의 에너지가 0.02~0.04 수준이었고, 일반 발화는 0.08~0.15 범위였다.

### 임계값 튜닝

| 값 | 결과 |
|-----|------|
| 0.01 (기본) | 소음도 발화로 감지 |
| 0.15 | 발화도 미감지 ❌ |
| **0.06** | 적정 균형점 ✅ |

`vad_energy_threshold: 0.06`으로 고정하되, 환경 소음이 큰 경우의 한계를 인정하고 Silero VAD 교체를 향후 과제로 남겨두었다.

---

## TTS 음성 답변 통합

명령을 실행한 뒤 "침실 불을 켰습니다" 같은 음성 피드백이 있으면 사용자 경험이 크게 달라진다. TTS 엔진을 통합한 과정을 기록한다.

### TTS 엔진 선택

| 후보 | 장점 | 단점 | 결과 |
|------|------|------|------|
| Kokoro | 로컬, 빠름 | 한국어 품질 낮음 | ❌ |
| ElevenLabs | 고품질 | 클라우드, 유료 | ❌ |
| **edge-tts** | 무료, 고품질 한국어, 빠름 | 네트워크 필요 | ✅ |

`edge-tts`는 Microsoft Edge의 TTS 엔진을 활용하는 라이브러리로, 네트워크가 필요하지만 별도 API 키 없이 사용 가능하다. `ko-KR-SunHiNeural` 음성은 한국어 자연스러움이 뛰어나다.

### 구현

```python
# tts_engine.py v1.0
import edge_tts
import asyncio

class TTSEngine:
    def __init__(self, voice="ko-KR-SunHiNeural"):
        self.voice = voice

    async def speak(self, text: str):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save("/tmp/tts_output.mp3")
        # 재생 로직
```

### LLM 응답에 TTS 필드 추가

LLM이 JSON 명령을 생성할 때 `tts_response` 필드를 함께 생성하도록 시스템 프롬프트를 수정했다.

```json
{
  "cmd": "led",
  "device_id": "esp32_bedroom",
  "pin": 2,
  "state": "on",
  "tts_response": "침실 불을 켰습니다"
}
```

`main.py`에서 명령 실행 후 `tts_response`가 있으면 자동으로 음성 출력한다.

### 변경 파일

| 파일 | 변경 |
|------|------|
| `tts_engine.py` v1.0 | 신규 작성 |
| `llm_engine.py` v1.3 → v1.4 | tts_response 필드 추가 |
| `main.py` v0.4 → v0.5 | TTS 초기화 + speak 호출 |
| `settings.yaml` v0.7 → v0.8 | tts 블록 추가 |

---

## 교훈과 회고

### 웨이크 워드에서 배운 것

설정 파일과 실제 모델의 불일치는 찾기 어렵다. "동작하는데 왜 안 되지?"의 대부분은 이런 단순한 불일치에서 온다. 디버그 로그를 처음부터 넣어두는 습관이 중요하다.

### VAD에서 배운 것

에너지 기반 VAD는 구현이 간단하지만 환경 의존적이다. 고정 임계값은 특정 환경에서만 작동하며, 적응형 VAD(Silero 등)로의 전환이 필요하다. 다만 "완벽을 기다리지 말고 먼저 동작하게 만들어라"는 원칙에 따라, 0.06으로 우선 안정화하고 진행했다.

### TTS에서 배운 것

Kokoro(로컬)를 먼저 시도했지만 한국어 품질이 부족했다. edge-tts는 네트워크 의존이라는 타협이 있지만, 한국어 TTS 품질이 매우 좋다. 프로젝트의 핵심(STT + LLM + ESP32)은 로컬을 유지하되, TTS처럼 부가 기능은 실용적으로 선택하는 것도 나쁘지 않다.

---

## 현재 상태 — v1.7

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| v1.7 | 02-22 | UnifiedStateManager 통합, status 템플릿화 |
| v1.6 | 02-22 | TTS edge-tts 교체, 웨이크워드 버그수정 |
| v1.5 | 02-22 | status 자연어화, CMD Router 개선 |
| v1.3 | 02-21 | music 명령, HOUSE MAP 추가 |
| v1.2 | 02-21 | qwen2.5:7b, LLM 워밍업 |
| v1.1 | 02-21 | Whisper small, VAD 최적화 |

> 이 시리즈의 전체 프로젝트 소개는 [첫 번째 포스트](/posts/smart-home/voice-iot-controller-overview/)에서, STT/LLM 최적화 과정은 [두 번째 포스트](/posts/smart-home/voice-iot-stt-llm-optimization/)에서 확인할 수 있다.
