---
title: "🔍 EyeCon — 심리 상태 분석기 프로젝트 계획서"
date: 2026-03-21
draft: true
tags: ["dev-tools", "pyqt6"]
categories: ["dev-tools"]
description: "> **프로젝트명:** EyeCon — 심리 상태 분석기 > **작성일:** 2026-02-14 (음성 분석 통합 업데이트) > **작성자:** stephen.kong"
---

# 🔍 EyeCon — 심리 상태 분석기 프로젝트 계획서

> **프로젝트명:** EyeCon — 심리 상태 분석기
> **작성일:** 2026-02-14 (음성 분석 통합 업데이트)
> **작성자:** stephen.kong
> **개발 루트:** `/home/gjkong/dev_ws/eyecon`
> **하드웨어:** NVIDIA RTX 4050 / 노트북 캠 / 마이크 / 스피커
> **분석 모달리티:** 영상(얼굴) + 음성(Voice) 멀티모달

---

## 1. 프로젝트 개요

### 1.1 목적

실시간 영상에서 얼굴 표정, 홍채 움직임, 눈 깜빡임 등 비언어적 단서를 분석하여 대상의 **감정 상태를 인식**하고, **거짓말 가능성을 추정**하는 대화형 AI 시스템을 구축한다.

### 1.2 핵심 기능

```
📷 실시간 얼굴 랜드마크 (478점) + 홍채 추적
🧠 감정 인식 (7개 감정 분류) + 미세 표정 변화 감지
👁️ 심리 지표 수치화 (시선, 깜빡임, 동공, 미세 근육)
🎤 음성 분석 (피치, 떨림, 응답 지연, 비유창성, 말 속도)
🤖 LLM 기반 심리 분석 대화 (Ollama + EXAONE)
🔊 한국어 음성 대화 (Edge TTS + STT)
📊 PyQt6 대시보드 (실시간 데이터 시각화)
```

---

## 2. 현재 코드 분석 (v2.6)

### 2.1 구현 완료된 기능

| 기능 | 구현 상태 | 비고 |
|------|----------|------|
| MediaPipe Face Mesh (468점) | ✅ | 홍채 포함 (refine_landmarks=True) |
| 홍채 좌표 추적 | ✅ | 좌(468)/우(473) 홍채 랜드마크 |
| Stress Score 계산 | ✅ | 홍채 30프레임 표준편차 기반 |
| PyQt6 GUI | ✅ | 카메라 영상 + 상태 표시 + 로그 |
| Edge TTS 음성 출력 | ✅ | ko-KR-SunHiNeural |
| STT 음성 입력 | ✅ | Google Speech Recognition |
| Ollama LLM 대화 | ✅ | EXAONE 3.5 프롬프트 질문 |

### 2.2 현재 코드의 한계점

| 문제 | 상세 |
|------|------|
| **단일 지표** | Stress Score가 홍채 움직임(std)만 반영. 표정, 깜빡임, 동공 크기 미반영 |
| **감정 분류 없음** | Happy/Sad/Angry 등 감정 분류가 없음. FER/DeepFace 미사용 |
| **미세 표정 미감지** | AU(Action Unit) 기반 미세 표정 분석 없음 |
| **깜빡임 미추적** | 눈 깜빡임 빈도 — 거짓말의 핵심 지표인데 빠져 있음 |
| **동공 크기 미측정** | 동공 확장은 가장 신뢰성 높은 거짓말 지표 중 하나 |
| **베이스라인 없음** | 정상 상태 기준치 없이 절대값으로 판단 |
| **프롬프트 단순** | LLM에게 stress_score만 전달, 다차원 분석 데이터 미포함 |
| **모듈화 부족** | main.py 단일 파일에 모든 로직 |

---

## 3. 핵심 기술 스택

```
┌─── Vision Layer ────────────────────────────────────────┐
│  MediaPipe Face Landmarker (478점 + 52 Blendshapes)     │
│  → 홍채 추적, AU 추출, 깜빡임 감지, 동공 측정           │
└─────────────────────────────────────────────────────────┘
         ↓
┌─── Voice Layer ─────────────────────────────────────────┐
│  librosa + webrtcvad (실시간 오디오 분석)                 │
│  → 피치(F0), Jitter/Shimmer, 응답 지연, 말 속도          │
│  → 비유창성("음..","어.."), 음량 변화, 음성 떨림          │
└─────────────────────────────────────────────────────────┘
         ↓
┌─── Analysis Layer (멀티모달 퓨전) ──────────────────────┐
│  영상 지표: 홍채 불안정 + 깜빡임 + 동공 + AU 비대칭      │
│  음성 지표: 피치 변화 + 응답 지연 + 비유창성 + 떨림      │
│  복합 스코어: 가중 합산 → 심리 상태 종합 점수             │
│  베이스라인 보정: 개인별 정상 상태 자동 학습              │
└─────────────────────────────────────────────────────────┘
         ↓
┌─── AI & Interface Layer ────────────────────────────────┐
│  Ollama EXAONE 3.5: 다차원 데이터 → 심리 분석 보고서     │
│  Edge TTS: 한국어 여성 음성 피드백                        │
│  Google STT: 사용자 음성 입력                             │
│  PyQt6: 실시간 대시보드 + 그래프                          │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 거짓말 탐지 — 과학적 근거 & 지표

### 4.1 핵심 생체 지표 (연구 기반)

**영상(얼굴) 지표:**

| 지표 | 스트레스/거짓 시 변화 | 신뢰도 | 측정 방법 |
|------|---------------------|--------|----------|
| **동공 확장** | 4~8% 증가 | 높음 | 홍채/동공 비율 계산 |
| **깜빡임 빈도** | 거짓 후 급증 (거짓 중 감소) | 중간 | EAR(Eye Aspect Ratio) 기반 |
| **시선 고정/회피** | 인지 부하로 시선 고정 증가 | 중간 | 홍채 움직임 분산 |
| **미세 표정** | 0.04~0.5초 내 얼굴 비대칭 | 높음 | AU 변화 속도 감지 |
| **입술 압축** | 무의식적 입술 누름 (AU24) | 중간 | 입술 랜드마크 거리 |
| **비대칭 표정** | 좌우 AU 강도 차이 | 중간 | 좌/우 반 비교 |

**음성(Voice) 지표:**

| 지표 | 스트레스/거짓 시 변화 | 신뢰도 | 측정 방법 |
|------|---------------------|--------|----------|
| **피치(F0) 상승** | 후두 근육 긴장 → 음높이 상승 | 높음 (70%) | librosa.yin() |
| **피치 변동성** | 분산 증가 | 중간 | F0 표준편차 |
| **응답 지연** | 답변까지 시간 증가 | 높음 | STT 타이밍 측정 |
| **비유창성** | "음..", "어..", 반복, 말 더듬 증가 | 높음 | STT 텍스트 패턴 |
| **말 속도 변화** | 인지 부하로 느려지거나 의도적 빨라짐 | 중간 | 음절/초 계산 |
| **Jitter/Shimmer** | 성대 미세 떨림 증가 | 중간 | librosa 파라미터 |
| **음량(RMS) 변화** | 스트레스 시 음량 범위 증가 | 중간 | librosa.feature.rms() |

### 4.2 중요한 한계 (정직한 고지)

연구에 따르면 단일 비언어적 단서로는 거짓말 탐지가 어렵다. 동공 확장이 가장 일관된 시각 지표이나 효과 크기(effect size)는 작다. 음성 스트레스 분석은 피치, 톤, 음성 스트레스 분석 모델에서 약 88% 정확도가 보고되었으나, 스트레스와 거짓의 구분이 어렵다는 한계가 있다. 그러나 영상+음성 멀티모달 결합 시 단일 모달 대비 정확도가 크게 향상된다.

따라서 이 시스템은 **"심리 상태 분석기"** — 감정과 스트레스 수준을 종합적으로 분석하는 도구로 포지셔닝한다.

---

## 5. 관련 논문 및 기술 참조

### 5.1 미세 표정 인식

| 논문/자료 | 핵심 내용 |
|----------|----------|
| "Advances in Facial Micro-Expression Detection" (Information, 2025) | 2018~2025 미세 표정 인식 종합 리뷰. Transformer, GNN, 멀티모달 전략 포함 |
| "FMeAR: FACS Driven Ensemble Model" (SN CompSci, 2024) | LBP+PCA+SVM 앙상블로 CASME II에서 95.9% 정확도 |
| "HTNet with LAPE" (Scientific Reports, 2025) | Vision Transformer + 엔트로피 어텐션 기반 미세 표정 인식 |
| "MEGANet: Micro-expression Gradient Attention" | MESTI(시공간 이미지) + Gradient Attention으로 미세 동작 특징 추출 |

### 5.2 거짓말 탐지

| 논문/자료 | 핵심 내용 |
|----------|----------|
| "Deception detection based on micro-expression" (Springer, 2025) | OpenFace AU + SOFTNet 미세 표정 + SVM으로 거짓말 탐지. 미세 표정이 가장 중요한 특징 |
| "The influence of micro-expressions on deception" (Multimedia Tools, 2023) | MediaPipe 478점 Face Mesh + CNN으로 FER-2013 기반 거짓말 탐지 |
| "Eye Movements as Indicators of Deception" (ACM ETRA, 2025) | XGBoost로 시선(고정, 사케이드, 깜빡임, 동공) 기반 74% 탐지 정확도 |
| "Facial expression-based lie detection survey" (AIP, 2025) | 2019~2023 미세 표정 기반 거짓말 탐지 종합 리뷰 |

### 5.3 시선 & 동공

| 논문/자료 | 핵심 내용 |
|----------|----------|
| "Can the Eyes Betray a Liar?" (Vision Science Academy, 2025) | 동공 확장 4~8%가 가장 신뢰할 수 있는 안구 지표. 시선 회피는 신뢰성 낮음 |
| "Countermeasures and Eye Tracking Deception" (UNO, 2012) | 깜빡임 빈도 + 동공 확장 + 시선 고정점 복합 분석 |
| Ekman (1969): "Nonverbal leakage and clues to deception" | 비언어적 누출 이론의 원전. 미세 표정이 진짜 감정을 드러냄 |

### 5.4 음성 분석 & 거짓말 탐지

| 논문/자료 | 핵심 내용 |
|----------|----------|
| "Voice analysis for detection of deception" (ResearchGate, 2016) | PRAAT으로 F0, Jitter, Shimmer, 포먼트 분석. 스트레스 시 F0 유의미 증가 확인 |
| "Vocal Analysis Software for Security Screening" (HSA) | 거짓 시 응답 지연 증가, 비유창성 증가, 피치 분산 증가, 음질 저하 |
| Paul Ekman: "How The Voice Can Betray Lies" | 70%에서 스트레스 시 피치 상승. 일시 정지, 말 실수가 핵심 단서 |
| "Deception Detection through Speech and Voice" (Resemble AI, 2025) | Jitter, Shimmer, HNR 기반 AI 모델 88% 정확도 보고 |

### 5.5 기술 도구

| 도구 | 활용 |
|------|------|
| MediaPipe Face Landmarker | 478 랜드마크 + 52 Blendshapes (AU 대체) |
| librosa | 오디오 특징 추출 (F0, RMS, Tempo, Spectral) |
| webrtcvad | 음성 구간 감지 (Voice Activity Detection) |
| CASME II / CAS(ME)³ / SMIC | 미세 표정 학습 데이터셋 |
| FER-2013 | 감정 인식 학습 데이터셋 (35,887장, 7감정) |
| OpenFace | AU 추출 참조 (MediaPipe Blendshapes로 대체 가능) |

---

## 6. 상세 작업 계획 (Phase Plan)

### Phase 1: 코드 모듈화 + MediaPipe 업그레이드 (2일)

> 목표: 단일 파일 → 모듈 구조, MediaPipe Face Landmarker (Blendshapes 지원) 전환

**코드 리팩토링:**
```
/home/gjkong/dev_ws/eyecon/
├── main.py                  # PyQt6 메인 윈도우
├── core/
│   ├── __init__.py
│   ├── vision.py            # MediaPipe Face Landmarker + 데이터 추출
│   ├── voice_analyzer.py    # 음성 특징 추출 (librosa 기반)
│   ├── analyzer.py          # 멀티모달 퓨전 분석 엔진
│   ├── baseline.py          # 개인 베이스라인 학습 (영상+음성)
│   └── llm_client.py        # Ollama EXAONE 연동
├── utils/
│   ├── __init__.py
│   ├── tts_engine.py        # Edge TTS 음성 출력
│   ├── stt_engine.py        # Google STT + WAV 저장
│   └── logger.py            # 데이터 로깅
├── config/
│   └── settings.py          # 설정값 관리
├── assets/                  # UI 리소스
└── requirements.txt
```

**MediaPipe 업그레이드:**
- 기존: `face_mesh.FaceMesh` (레거시, 468점)
- 변경: `FaceLandmarker` (최신, 478점 + **52 Blendshapes**)
- Blendshapes가 AU(Action Unit)를 대체하여 미세 표정 분석 가능

```python
# 52 Blendshapes 예시 (AU와 매핑 가능)
browDownLeft, browDownRight      # AU4 (미간 찌푸림)
browInnerUp                      # AU1 (내측 눈썹 올림)
eyeBlinkLeft, eyeBlinkRight      # AU45 (눈 깜빡임)
jawOpen                          # AU26/27 (입 벌림)
mouthSmileLeft, mouthSmileRight  # AU12 (웃음)
mouthPressLeft, mouthPressRight  # AU24 (입술 압축) ← 거짓말 지표!
```

### Phase 2: 다차원 생체 지표 추출 — 영상 + 음성 (4일)

> 목표: 영상 6개 + 음성 7개 = 13개 심리 지표를 실시간 추출

#### 2A. 영상 지표 (Vision)

**2A.1 눈 깜빡임 감지**
```python
# EAR (Eye Aspect Ratio) 알고리즘
# 또는 Blendshapes의 eyeBlinkLeft/Right 직접 사용
blink_count = 0
blink_rate_per_minute = 0  # 정상: 15-20회/분
```

**2A.2 동공 크기 측정**
```python
# 홍채 랜드마크(468~477)로 홍채 직경 계산
# 눈 전체 대비 홍채 비율 = 동공 확장 추정
iris_ratio = iris_diameter / eye_width
# 베이스라인 대비 변화율 추적
```

**2A.3 미세 표정 감지**
```python
# Blendshapes 급변 감지 (0.5초 미만)
# 예: mouthSmileLeft가 0.5초 내에 0.1→0.8→0.2 변화 = 억제된 웃음
micro_expression_detected = delta > threshold and duration < 0.5
```

**2A.4 표정 비대칭**
```python
# 좌/우 Blendshapes 차이
asymmetry = abs(mouthSmileLeft - mouthSmileRight)
# 진짜 감정은 대칭적, 가짜 감정은 비대칭적
```

**2A.5 시선 패턴**
```python
# 홍채 위치 → 시선 방향 (상/하/좌/우)
# 시선 고정 시간, 회피 빈도 계산
gaze_fixation_duration = 0
gaze_aversion_count = 0
```

**2A.6 입술 압축 (AU24)**
```python
# mouthPressLeft + mouthPressRight
lip_press_score = (mouthPressLeft + mouthPressRight) / 2
```

#### 2B. 음성 지표 (Voice)

현재 STT에서 마이크 녹음 후 텍스트만 추출하고 있다. 같은 오디오를
WAV로 저장하여 librosa로 분석하면 추가 하드웨어 없이 음성 지표 추출 가능.

**2B.1 오디오 녹음 파이프라인 수정**
```python
# stt_engine.py — STT 시 원본 오디오도 저장
import soundfile as sf

class STTWorker(QThread):
    result_signal = pyqtSignal(str)
    audio_signal = pyqtSignal(str)  # WAV 파일 경로 전달

    def run(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            # WAV 저장 (음성 분석용)
            wav_path = "last_response.wav"
            with open(wav_path, "wb") as f:
                f.write(audio.get_wav_data())
            self.audio_signal.emit(wav_path)
            # STT 텍스트 변환
            text = recognizer.recognize_google(audio, language='ko-KR')
            self.result_signal.emit(text)
```

**2B.2 피치(F0) 분석**
```python
import librosa
import numpy as np

def analyze_pitch(wav_path):
    y, sr = librosa.load(wav_path, sr=16000)
    # YIN 알고리즘으로 F0 추출
    f0 = librosa.yin(y, fmin=75, fmax=500, sr=sr)
    f0_valid = f0[f0 > 0]  # 무음 구간 제거
    return {
        'f0_mean': np.mean(f0_valid),      # 평균 피치
        'f0_std': np.std(f0_valid),        # 피치 변동성
        'f0_max': np.max(f0_valid),        # 최대 피치
        'f0_range': np.ptp(f0_valid),      # 피치 범위
    }
```

**2B.3 Jitter & Shimmer (성대 떨림)**
```python
def analyze_jitter_shimmer(f0):
    # Jitter: 연속 피치 주기 간 변동률
    periods = 1.0 / f0[f0 > 0]
    jitter = np.mean(np.abs(np.diff(periods))) / np.mean(periods) * 100

    # Shimmer: 진폭 변동률 (RMS 기반 근사)
    return {'jitter_pct': jitter}

def analyze_shimmer(wav_path):
    y, sr = librosa.load(wav_path, sr=16000)
    rms = librosa.feature.rms(y=y)[0]
    shimmer = np.mean(np.abs(np.diff(rms))) / np.mean(rms) * 100
    return {'shimmer_pct': shimmer}
```

**2B.4 응답 지연 (Response Latency)**
```python
def measure_response_latency(tts_end_time, stt_start_time):
    """AI 질문 끝 → 사용자 발화 시작 사이의 시간"""
    latency = stt_start_time - tts_end_time
    return {'response_latency_sec': latency}
    # 정상: 0.5~2초 / 스트레스: 3초 이상
```

**2B.5 말 속도 & 음량**
```python
def analyze_speech_rate(wav_path, text):
    y, sr = librosa.load(wav_path, sr=16000)
    duration = librosa.get_duration(y=y, sr=sr)
    syllable_count = len(text)  # 한국어: 글자수 ≈ 음절수
    return {
        'speech_rate': syllable_count / duration,  # 음절/초
        'duration_sec': duration,
    }

def analyze_volume(wav_path):
    y, sr = librosa.load(wav_path, sr=16000)
    rms = librosa.feature.rms(y=y)[0]
    return {
        'volume_mean': float(np.mean(rms)),
        'volume_std': float(np.std(rms)),
        'volume_range': float(np.ptp(rms)),
    }
```

**2B.6 비유창성 감지 (Disfluency)**
```python
import re

def detect_disfluency(text):
    """STT 텍스트에서 비유창성 패턴 감지"""
    fillers = re.findall(r'(음+|어+|아+|그+|저+)', text)
    repetitions = re.findall(r'(\b\w+\b)(?:\s+\1)+', text)
    return {
        'filler_count': len(fillers),       # "음..", "어.." 횟수
        'repetition_count': len(repetitions), # 반복 횟수
        'disfluency_total': len(fillers) + len(repetitions),
    }
```

**2B.7 통합 음성 분석기**
```python
# core/voice_analyzer.py

class VoiceAnalyzer:
    def __init__(self):
        self.baseline = {}  # 베이스라인 저장

    def analyze(self, wav_path, text, response_latency):
        pitch = analyze_pitch(wav_path)
        jitter = analyze_jitter_shimmer(pitch['f0_raw'])
        shimmer = analyze_shimmer(wav_path)
        volume = analyze_volume(wav_path)
        speech = analyze_speech_rate(wav_path, text)
        disfluency = detect_disfluency(text)

        return {
            **pitch, **jitter, **shimmer,
            **volume, **speech, **disfluency,
            'response_latency_sec': response_latency,
        }
```

### Phase 3: 감정 분류 + 복합 스코어 (2일)

> 목표: 7감정 분류 + 거짓말 가능성 복합 점수

**감정 분류:**
- Blendshapes 조합으로 7감정 매핑
- 또는 FER 모델 (CNN) 병렬 실행
- 감정: Happy, Sad, Angry, Surprise, Fear, Disgust, Neutral

**심리 상태 복합 스코어 (멀티모달):**
```python
# 영상 지표 (0~100)
vision_score = (
    w1 * iris_instability +      # 시선 불안정
    w2 * blink_rate_change +     # 깜빡임 변화
    w3 * pupil_dilation +        # 동공 확장
    w4 * micro_expression +      # 미세 표정
    w5 * asymmetry +             # 비대칭
    w6 * lip_press               # 입술 압축
) / vision_total_weight

# 음성 지표 (0~100)
voice_score = (
    w7 * pitch_change +          # 피치 변화
    w8 * response_latency +      # 응답 지연
    w9 * disfluency +            # 비유창성
    w10 * jitter_change +        # 성대 떨림
    w11 * speech_rate_change +   # 말 속도 변화
    w12 * volume_change          # 음량 변화
) / voice_total_weight

# 멀티모달 종합 (영상 60% + 음성 40%)
combined_score = vision_score * 0.6 + voice_score * 0.4

# 베이스라인 대비 변화율로 보정
adjusted_score = combined_score - personal_baseline
```

**베이스라인 시스템:**
- 대화 시작 후 최초 30초간 정상 상태 수집
- 개인별 평균/표준편차 저장
- 이후 분석은 베이스라인 대비 변화율로 판단

### Phase 4: LLM 프롬프트 고도화 + 대화 전략 (2일)

> 목표: 다차원 데이터를 LLM에 전달, 심리 분석 대화

**프롬프트 설계 (멀티모달):**
```python
prompt = f"""당신은 심리 분석 전문가 AI입니다.

[실시간 영상 분석 데이터]
- 감정 상태: {emotion} (확신도: {confidence}%)
- 시선 불안정: {iris_score}
- 깜빡임 변화: {blink_change}% (현재 {blink_rate}회/분)
- 동공 확장: {pupil_change}%
- 미세 표정 감지: {micro_exp_count}건
- 표정 비대칭: {asymmetry_score}
- 입술 압축: {lip_press_score}

[실시간 음성 분석 데이터]
- 피치(F0): 평균 {f0_mean}Hz (베이스라인 대비 {f0_delta}%)
- 피치 변동성: {f0_std} (베이스라인 대비 {f0_std_delta}%)
- 응답 지연: {response_latency}초
- 비유창성: {filler_count}회 (음.., 어..)
- 말 속도: {speech_rate} 음절/초 (베이스라인 대비 {rate_delta}%)
- 성대 떨림(Jitter): {jitter_pct}%
- 음량 변화: {volume_delta}%

[종합 점수]
- 영상 스코어: {vision_score}/100
- 음성 스코어: {voice_score}/100
- 멀티모달 종합: {combined_score}/100

[이전 대화]
Q: {prev_question}
A: {prev_answer}

위 데이터를 참고하여 한국어 경어체로 다음 질문을 하나만 하세요.
종합 점수가 높으면 해당 주제를 깊이 파고드는 질문을 하세요.
영상과 음성 데이터가 불일치하면 (예: 표정은 차분한데 목소리가 떨림)
그 불일치에 대해 부드럽게 탐색하는 질문을 하세요.
"""
```

**대화 전략:**
1. 워밍업 (베이스라인 수집): 가벼운 질문 3~4개
2. 탐색: 감정 변화가 큰 주제 발견
3. 심화: 거짓말 지수 높은 답변에 대해 구체적 질문
4. 요약: 전체 분석 보고서 생성

### Phase 5: PyQt6 대시보드 고도화 (2일)

> 목표: 실시간 그래프 + 다차원 지표 시각화

**대시보드 레이아웃 (멀티모달):**
```
┌──────────────────┬──────────────────────────┐
│                  │  감정: 😊 Happy (82%)     │
│   카메라 영상     │  종합 스코어: ████░ 72   │
│   (랜드마크 표시) │  ─── 영상 지표 ────────  │
│                  │  👁 시선 불안정: 높음      │
│                  │  👀 깜빡임: 28회/분 (↑)   │
│                  │  ⚫ 동공 확장: +6.2%      │
│                  │  ⚡ 미세 표정: 3건 감지    │
│                  │  ─── 음성 지표 ────────  │
│                  │  🎵 피치: 245Hz (↑12%)    │
│                  │  ⏱️ 응답 지연: 3.2초      │
│                  │  💬 비유창성: 4회          │
│                  │  📈 말 속도: 느림 (-18%)   │
├──────────────────┼──────────────────────────┤
│  실시간 그래프    │                          │
│  (시계열 차트)    │  대화 로그               │
│  - 종합 스코어   │  [AI] 질문...            │
│  - 피치 변화     │  [사용자] 답변...         │
│  - 깜빡임 빈도   │  [AI] 분석...            │
└──────────────────┴──────────────────────────┘
```

**시각화 라이브러리:** pyqtgraph (PyQt6 네이티브, 실시간 그래프 최적)

### Phase 6: 최적화 + 테스트 (2일)

> 목표: RTX 4050 최적화, 안정성 테스트

- ONNX Runtime GPU 가속 (MediaPipe → ONNX 변환)
- 멀티스레딩: Vision / Analysis / LLM / TTS 각각 별도 스레드
- 메모리 관리: 프레임 버퍼 크기 제한
- 시나리오 테스트: 정상 대화 / 의도적 거짓말 / 감정 변화

---

## 7. 일정 요약

| 주차 | Phase | 작업 | 일수 |
|------|-------|------|------|
| 1주차 | Phase 1 | 모듈화 + MediaPipe Landmarker 전환 | 2일 |
| 1~2주차 | Phase 2 | 영상 6개 + 음성 7개 지표 추출 (멀티모달) | 4일 |
| 2주차 | Phase 3 | 감정 분류 + 멀티모달 복합 스코어 | 2일 |
| 3주차 | Phase 4 | LLM 프롬프트 + 대화 전략 | 2일 |
| 3주차 | Phase 5 | PyQt6 대시보드 (멀티모달) | 2일 |
| 4주차 | Phase 6 | 최적화 + 테스트 | 2일 |

---

## 8. 설치 패키지

```bash
# 가상환경 생성
python -m venv ~/dev_ws/eyecon_venv
source ~/dev_ws/eyecon_venv/bin/activate

# 핵심 패키지
pip install mediapipe opencv-python numpy

# GUI
pip install PyQt6 pyqtgraph

# 음성 분석
pip install librosa soundfile webrtcvad

# AI/LLM
pip install requests  # Ollama API

# 음성
pip install edge-tts pygame SpeechRecognition

# 선택: 감정 인식 모델
pip install fer  # FER (CNN 기반 감정 분류)
# 또는
pip install deepface  # DeepFace (다양한 백엔드)

# GPU 가속 (선택)
pip install onnxruntime-gpu
```

---

## 9. 참고 데이터셋

| 데이터셋 | 용도 | 규모 |
|---------|------|------|
| FER-2013 | 감정 분류 학습 | 35,887장, 7감정 |
| CASME II | 미세 표정 학습 | 247 비디오 클립 |
| CAS(ME)³ | 미세 표정 + 매크로 | 대규모, AU 레이블 |
| SMIC | 미세 표정 (다중 카메라) | HS/VIS/NIS 녹화 |
| Real-Life Deception | 거짓말 탐지 | 121 비디오 (법정 증언) |
| MU3D | 거짓말 탐지 | 마이애미 대학 DB |

---

## 10. 향후 확장 가능성

- **자세 분석** 추가: MediaPipe Pose로 몸 움직임 (안절부절, 자기접촉)
- **멀티모달 딥러닝**: 영상+음성+텍스트 → End-to-End 학습 모델
- **학습 모델**: 수집 데이터로 개인 맞춤형 심리 분석 모델 학습
- **Home Guard Bot 연동**: 보안관이 방문자에게 질문 → 심리 상태 분석
- **리포트 생성**: 세션 종료 후 PDF 심리 분석 보고서 자동 생성
