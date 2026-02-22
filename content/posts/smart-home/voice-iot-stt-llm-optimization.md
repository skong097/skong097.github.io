---
title: "Voice IoT의 두뇌를 깎다 — STT/LLM 성능 최적화 여정"
date: 2026-02-22
tags:
- voice-iot
- whisper
- ollama
- faster-whisper
- openai
- stt
- llm
- optimization
categories:
- smart-home
summary: "faster-whisper CPU 튜닝, Ollama 모델 업그레이드, OpenAI 전환 시도와 원복까지 — Voice IoT Controller의 음성 파이프라인 최적화 기록"
---

---

## 문제 인식 — 3~7초는 너무 느리다

Voice IoT Controller의 초기 파이프라인은 이런 구조였다.

```
웨이크워드 → Whisper (2~4s) → LLM (1~3s) → ESP32
총 소요: 3~7초
```

"불 켜줘" 한마디에 7초를 기다리는 건 사용자 경험으로서 실패다. 특히 IoT 명령은 대부분 짧은 단문이므로, 무거운 추론이 불필요하다. 이 글에서는 STT와 LLM 각각을 어떻게 최적화했는지, 그리고 OpenAI API 전환을 시도했다가 원복한 과정까지 기록한다.

---

## Phase 1 — faster-whisper CPU 최적화

### 발견한 병목

`faster-whisper`는 이미 CTranslate2 기반이라 추론 자체는 빠르지만, 기본 설정이 문제였다.

- `cpu_threads` 미설정 → 기본값 1 (싱글 스레드)
- `beam_size=5` → IoT 단문에 불필요하게 높은 탐색 범위
- `num_workers=1` → 병렬 처리 미활용

### 적용한 최적화

```yaml
# settings.yaml
stt:
  model_size: small        # base → small 업그레이드
  beam_size: 1             # 5 → 1 (greedy decoding)
  cpu_threads: 3           # 1 → 3
  num_workers: 2           # 1 → 2
  language: ko
```

`beam_size=1`은 품질 저하가 우려될 수 있지만, "침실 불 켜줘" 같은 짧은 명령어에서는 greedy decoding으로 충분하다. 오히려 불필요한 탐색을 제거함으로써 속도가 크게 향상되었다.

### 모델 업그레이드: base → small

시스템 리소스를 확인해보니 RAM 14GB, CPU 16코어로 여유가 있었다. `base` 모델에서 `small`로 올리면 인식 정확도가 눈에 띄게 좋아지면서도, 로드 시간만 2초 → 5초로 늘어나고 추론 속도는 거의 동일했다.

**결과:** Whisper STT 약 2~4초 → **~1,300ms**

---

## Phase 2 — LLM 모델 업그레이드

### EXAONE 3.5 → qwen2.5:7b

초기에 사용하던 EXAONE 3.5 모델을 Ollama의 `qwen2.5:7b`로 교체했다. 이유는 다음과 같다.

- 한국어 IoT 명령 파싱에서 JSON 구조 준수율이 더 높았다
- 응답 시간이 안정적이었다 (분산이 적음)
- 7B 파라미터로 14GB RAM에서 충분히 구동 가능

### LLM 워밍업 추가

Ollama는 모델을 처음 호출할 때 로딩 시간이 발생한다. 이를 해결하기 위해 서버 시작 시 더미 요청으로 워밍업을 추가했다.

```python
# llm_engine.py — 서버 시작 시 워밍업
async def warmup(self):
    await self.parse("테스트")  # 모델 로드 트리거
```

**결과:** LLM 파싱 약 1~3초 → 워밍업 후 **~600ms**

---

## Phase 3 — OpenAI API 전환 시도

속도를 더 줄이기 위해 OpenAI API를 시도했다.

### 전환 과정

1. `llm_engine.py`에 OpenAI 클라이언트 추가
2. `gpt-4o-mini` 모델로 연결 → 성공
3. STT도 OpenAI Whisper API로 전환 시도 → **크레딧 소진으로 실패**

### 원복 결정

OpenAI API는 확실히 빠르고 정확했지만, 이 프로젝트의 핵심 철학은 **완전 로컬 실행**이다. 외부 API 의존은 네트워크 장애 시 시스템 전체가 멈추는 단일 장애점(SPOF)이 된다. 크레딧 소진이라는 현실적 문제도 있었고, 결국 Ollama로 원복했다.

교훈: 로컬 LLM의 성능이 충분하다면, 굳이 클라우드에 의존할 필요가 없다.

---

## Phase 4 — 한국어 오인식 교정

Whisper의 한국어 인식은 전반적으로 좋지만, 특정 단어에서 반복적인 오류가 발생했다.

```python
# stt_engine.py
_KO_CORRECTIONS = {
    "체실": "침실",
    "거실불": "거실 불",
    "서보모타": "서보모터",
    "차고문여": "차고문 열어",
}
```

패턴이 반복되는 오인식은 사전 기반 교정으로 빠르게 잡았다. 완벽하진 않지만, IoT 도메인 특화 사전으로 실사용 정확도를 체감 가능한 수준으로 끌어올렸다.

---

## Phase 5 — STT/LLM 업그레이드 종합

최종적으로 `stt_engine.py v4.2`, `llm_engine.py v1.2`에서 안정화되었다.

| 단계 | 내용 | 결과 |
|------|------|------|
| faster-whisper CPU 최적화 | beam_size=1, cpu_threads=3 | ✅ |
| Whisper base → small | 정확도 향상 | ✅ |
| qwen2.5:7b 업그레이드 | JSON 준수율 향상 | ✅ |
| LLM 워밍업 | 초기 지연 제거 | ✅ |
| OpenAI 전환 시도 | 크레딧 소진 | ❌ → Ollama 원복 |
| 한국어 오인식 교정 | _KO_CORRECTIONS | ✅ |
| _normalize_types | float→int 자동 변환 | ✅ |

---

## 최종 성능 비교

| 항목 | 최적화 전 | 최적화 후 | 개선율 |
|------|----------|----------|--------|
| Whisper STT | 2~4초 | ~1,300ms | **~60%** |
| LLM 파싱 | 1~3초 | ~600ms | **~70%** |
| 전체 파이프라인 | 3~7초 | **~1,900ms** | **~70%** |

음성 명령 후 2초 이내에 실제 디바이스가 반응하는 수준까지 도달했다. IoT 제어라는 맥락에서 이 정도면 "말하면 바로 되는" 느낌에 근접한다.

---

## 배운 것들

- **beam_size=1**은 짧은 명령어 도메인에서 품질 손실 없이 속도를 크게 향상시킨다
- **LLM 워밍업**은 사소하지만 사용자 경험에 큰 차이를 만든다
- 로컬 LLM은 특정 도메인에서 충분히 실용적이다 — 범용 대화가 아니라 JSON 파싱이라면 7B도 훌륭하다
- 클라우드 의존을 줄이는 것은 기술적 선택이자 설계 철학이다

> 다음 포스트에서는 웨이크 워드 버그수정 과정과 TTS 음성 답변 통합에 대해 다룬다.
