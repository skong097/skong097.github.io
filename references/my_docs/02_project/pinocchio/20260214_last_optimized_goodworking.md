# 피노키오 프로젝트 — 작업 기록 (2026-02-14)

> **날짜:** 2026-02-14
> **작업 범위:** Phase 2 ~ Phase 5 + 최적화 튜닝
> **버전:** v3.1 → v3.5
> **상태:** ✅ 완료

---

## 1. 버전 이력

| 버전 | 내용 |
|------|------|
| v2.6 | 원본 단일 파일 (EyeCon) |
| v3.0 | 7개 모듈 분리 + FaceLandmarker 전환 |
| v3.1 | Phase 1: 4분할 대시보드 + 그래프 + 대화 루프 |
| v3.2 | Phase 2: 영상 6개 + 음성 7개 지표 + 마이크 설정 + 썬글라스 오버레이 |
| v3.3 | Phase 3: 7감정 분류 + 멀티모달 복합 스코어 + 베이스라인 시스템 |
| v3.4 | Phase 4: LLM 다차원 프롬프트 + 대화 전략 4단계 |
| v3.5 | Phase 5: 레이더 차트 + 마이크 자동 검색 + 최적화 튜닝 |

---

## 2. Phase 2 — 영상+음성 지표 (v3.2)

### 2.1 Phase 2A — 영상 지표 고도화 (`core/vision.py`)

| 지표 | 구현 내용 |
|------|----------|
| 미세 표정 | Blendshapes 급변 감지 (0.5초 내 delta>0.3), 유형 라벨링 |
| 동공 확장률 | 최초 10초 자동 베이스라인 → 변화율(%) 실시간 비교 |
| 시선 패턴 | 방향 고정 시간(초) + 최근 60초 회피 횟수 추적 |
| 비대칭 종합 | 6개 좌/우 AU 쌍 평균 차이 |
| 입술 압축 | FaceData에 lip_press_score 직접 포함 |

FaceData 추가 필드: `pupil_dilation_pct`, `gaze_fixation_sec`, `gaze_aversion_count`, `micro_expression_count`, `micro_expression_label`, `asymmetry_score`, `lip_press_score`

### 2.2 Phase 2B — 음성 파이프라인

데이터 흐름:
```
TTS 종료 → _tts_end_time 기록 → 0.5초 후 STT 시작
→ timing_signal → audio_signal(WAV) → result_signal(텍스트)
→ VoiceAnalyzer.analyze(WAV + 텍스트 + 응답지연)
→ _latest_voice_data → 지표 패널 표시
```

음성 지표 7개: 피치(F0), Jitter, Shimmer, 응답 지연, 말 속도, 음량, 비유창성

### 2.3 내장 마이크 설정

문제: PipeWire가 DMIC(card 3)를 점유, 배경 소음으로 에너지 임계값 자동 상승

해결:
```python
STT = {
    "microphone_index": 11,       # PipeWire 장치 (자동 검색으로 대체)
    "energy_threshold": 15000,    # 수동 고정
    "dynamic_energy": False,
    "pause_threshold": 1.5,
    "phrase_time_limit": 15,
}
```

### 2.4 LLM 응답 속도 최적화

시스템 프롬프트를 `system` 파라미터로 분리, `num_predict: 80`, `temperature: 0.7`

### 2.5 썬글라스 오버레이 (`core/vision.py`)

노란색 반투명 사다리꼴 렌즈, 양쪽 홍채 사이 거리 기반 고정 비율, 브릿지/템플/반사광 포함

---

## 3. Phase 3 — 감정 분류 + 멀티모달 퓨전 (v3.3)

### 3.1 7감정 분류 (`core/analyzer.py`)

Blendshapes 규칙 엔진:

| 감정 | 주요 AU |
|------|---------|
| Happy 😊 | mouthSmile (60%) + cheekSquint (40%) |
| Sad 😢 | mouthFrown (50%) + browInnerUp (50%) |
| Angry 😠 | browDown (40%) + mouthPress (30%) + jawForward (30%) |
| Surprise 😲 | eyeWide (30%) + browInnerUp (20%) + browOuterUp (20%) + jawOpen (30%) |
| Fear 😰 | browInnerUp (30%) + eyeWide (30%) + mouthPress (20%) + lipPress (20%) |
| Disgust 😖 | noseSneer (50%) + mouthShrugUpper (30%) + mouthFrown (20%) |
| Neutral 😐 | 0.5 - max(다른 감정) |

### 3.2 멀티모달 복합 스코어

영상 6개 지표(가중치 합) × 60% + 음성 6개 지표(가중치 합) × 40% = 종합 0~100

### 3.3 이상 감지 플래그

시선 회피 빈번, 깜빡임 급증, 미세 표정 다발, 입술 압축 강함, 응답 지연 과다, 비유창성 과다

### 3.4 베이스라인 시스템 (`core/baseline.py`)

대화 시작 시 30초간 자동 수집, 완료 후 콜백으로 Analyzer에 전달

---

## 4. Phase 4 — LLM 프롬프트 고도화 (v3.4)

### 4.1 다차원 프롬프트 (`core/llm_client.py`)

기존 `[스트레스: 25] 사용자: '...'` → 감정/지표/이상 플래그/이전 대화 포함:
```
[explore] 관찰:불안 😰,시선회피,억제된 웃음,응답지연 스트레스:45
이전답변:오~ 그렇군요! 그때 기분이 어땠어요?
사용자:직장에서 스트레스 받아요
```

프롬프트 ~300자 → ~80자로 압축 (토큰 1/3 감소)

### 4.2 대화 전략 4단계

| 단계 | 턴 | 목표 |
|------|-----|------|
| warmup | 0~2 | 가벼운 일상 질문, 분석 결과 언급 안 함 |
| explore | 3~6 | 감정/경험 자연스럽게 탐색 |
| deepen | 7~12 | 핵심 주제 깊이 탐색, 이상 패턴 참고 |
| summary | 13+ | 대화 정리, 긍정 메시지 |

### 4.3 대화 히스토리

최근 1턴(이전 AI 답변 40자) 포함, conversation_history 전체 관리

---

## 5. Phase 5 — 레이더 차트 (v3.5)

### 5.1 레이더 차트 (`utils/radar_chart.py`)

QPainter 기반 커스텀 위젯:
- 13개 꼭짓점: 영상 6개(시안) + 음성 6개(그린) + 종합(레드)
- 거미줄 4단계 (25/50/75/100)
- 값에 따른 꼭짓점 색상 (초록 < 40 < 주황 < 70 < 빨강)
- 반투명 데이터 영역 채우기
- 15프레임마다 갱신 (부하 최소화)

### 5.2 레이아웃 변경

좌하단 그래프 패널을 좌우 분할:
```
┌──────────────────────────────────┐
│ 시계열 그래프 (60%) │ 레이더 (40%) │
└──────────────────────────────────┘
```

---

## 6. 최적화 튜닝

### 6.1 파이프라인 시간 비교

| 구간 | 최적화 전 | 최적화 후 |
|------|-----------|-----------|
| STT 대기 | ~1.5초 | ~1.0초 |
| 음성 분석 | 1.18초 (순차) | 1.18초 (병렬, 비대기) |
| LLM 추론 | ~2.5초 | ~0.93초 |
| TTS 합성 | ~0.1초 | ~0.1초 |
| **총 체감 지연** | **~3.5초** | **~1.5초 (57% 단축)** |

### 6.2 핵심 최적화 항목

| 항목 | 내용 |
|------|------|
| 프롬프트 압축 | ~300자 → ~80자 (토큰 1/3) |
| 시스템 프롬프트 분리 | prompt 반복 → system 파라미터 1회 전송 |
| num_predict 제한 | 무제한 → 80토큰 |
| 음성 분석 병렬화 | threading.Thread로 LLM과 동시 실행 |
| 프레임 루프 경량화 | analyzer에 voice_data 매프레임 전달 제거 |
| 음성 지표 UI 분리 | 매프레임 리셋 → 분석 완료 시만 갱신 |
| 레이더 차트 주기 | 5프레임 → 15프레임마다 |
| 마이크 자동 검색 | pipewire > pulse > default 우선순위 |

### 6.3 마이크 자동 검색 (`utils/stt_engine.py`)

`find_microphone_index()` — PipeWire 재시작으로 장치 번호 변동 시 자동 대응:
```
우선순위: pipewire → pulse → default → settings 고정값
```

---

## 7. 수정 파일 목록

| 파일 | Phase | 변경 내용 |
|------|-------|----------|
| `core/vision.py` | 2 | 미세표정/동공확장률/시선패턴/비대칭 + 썬글라스 오버레이 |
| `core/voice_analyzer.py` | 2 | librosa 음성 분석 (F0, Jitter, Shimmer, 말속도, 음량, 비유창성) |
| `core/analyzer.py` | 3 | 7감정 분류 + 멀티모달 복합 스코어 + 이상 감지 (전면 재작성) |
| `core/baseline.py` | 3 | Phase 2A 지표 포함 + 자동 완료 콜백 (전면 재작성) |
| `core/llm_client.py` | 4 | 다차원 프롬프트 + 대화 전략 + 프롬프트 압축 (전면 재작성) |
| `utils/stt_engine.py` | 2+5 | 마이크 설정 + 에너지 고정 + 자동 검색 |
| `utils/radar_chart.py` | 5 | QPainter 레이더 차트 위젯 (신규) |
| `config/settings.py` | 2~4 | STT/LLM/SCORE_WEIGHTS 설정 |
| `main.py` | 2~5 | 전체 연동 (음성 병렬화, Analyzer, Baseline, 감정 표시, 레이더) |
| `check_mic.py` | 2 | 마이크 진단 도구 (신규) |
| `README.md` | — | GitHub 프로젝트 문서 (신규) |

---

## 8. 현재 프로젝트 구조

```
eyecon/
├── main.py                      # 메인 윈도우 (PyQt6 4분할 + 레이더)
├── config/
│   ├── __init__.py
│   └── settings.py              # 설정값 중앙 관리
├── core/
│   ├── __init__.py
│   ├── vision.py                # MediaPipe 영상 분석 엔진
│   ├── voice_analyzer.py        # librosa 음성 분석
│   ├── analyzer.py              # 멀티모달 퓨전 + 7감정 분류
│   ├── baseline.py              # 베이스라인 수집기
│   └── llm_client.py            # Ollama EXAONE 클라이언트
├── utils/
│   ├── __init__.py
│   ├── tts_engine.py            # Edge TTS
│   ├── stt_engine.py            # Google STT + 마이크 자동 검색
│   ├── logger.py                # 세션 로그
│   └── radar_chart.py           # 레이더 차트 위젯
├── assets/
│   └── face_landmarker_v2_with_blendshapes.task
├── logs/                        # 세션별 JSON 로그
├── temp/                        # WAV/MP3 임시 파일
├── check_mic.py                 # 마이크 진단 도구
├── requirements.txt
└── README.md
```

---

## 9. 다음 단계

- [ ] Phase 6: 성능 최적화 (ONNX Runtime GPU 가속)
- [ ] LLM 스트리밍 (stream: true → 첫 토큰 즉시 TTS)
- [ ] 세션 요약 리포트 자동 생성
- [ ] 감정 시계열 그래프
- [ ] 대화 전략 UI 표시

---

> **v3.5 완료: 13개 심리 지표 실시간 추출 + 7감정 분류 + 멀티모달 복합 스코어 + 4단계 대화 전략 + 레이더 차트 + 최적화 튜닝 (체감 지연 57% 단축)**
