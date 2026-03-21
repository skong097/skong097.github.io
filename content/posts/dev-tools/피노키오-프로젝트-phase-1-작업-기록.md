---
title: "피노키오 프로젝트 — Phase 1 작업 기록"
date: 2026-03-21
draft: true
tags: ["dev-tools", "pyqt6"]
categories: ["dev-tools"]
description: "> **날짜:** 2026-02-14 > **Phase:** 1 — 코드 모듈화 + MediaPipe 업그레이드 > **상태:** ✅ 완료 (v3.1)"
---

# 피노키오 프로젝트 — Phase 1 작업 기록

> **날짜:** 2026-02-14
> **Phase:** 1 — 코드 모듈화 + MediaPipe 업그레이드
> **상태:** ✅ 완료 (v3.1)

---

## 1. 작업 요약

v2.6 단일 파일(`main.py` 170줄)을 **7개 모듈**로 분리하고,
MediaPipe를 레거시 `FaceMesh`(468점)에서 **FaceLandmarker**(478점 + 52 Blendshapes)로 업그레이드.
4분할 대시보드 UI 구축 및 실시간 그래프, 대화 안정성 확보까지 완료.

## 2. 버전 이력

| 버전 | 내용 |
|------|------|
| v2.6 | 원본 단일 파일 (EyeCon) |
| v3.0 | 7개 모듈 분리 + FaceLandmarker 전환 |
| v3.1 | 4분할 대시보드 + 그래프 + 크래시 수정 + 대화 개선 |

## 3. 변경 전/후

| 항목 | v2.6 (Before) | v3.1 (After) |
|------|--------------|--------------|
| 구조 | `main.py` 단일 파일 | 7개 모듈 분리 |
| MediaPipe | `FaceMesh` (468점) | `FaceLandmarker` (478점 + 52 Blendshapes) |
| 설정 관리 | 하드코딩 | `config/settings.py` 중앙 관리 |
| 깜빡임 감지 | 없음 | EAR 기반 구현 + 빈도 표시 |
| 동공 측정 | 없음 | 홍채/눈 비율 계산 |
| 시선 추적 | 없음 | 홍채 위치 기반 방향 추정 |
| 표정 비대칭 | 없음 | Blendshapes 좌/우 차이 실시간 표시 |
| 입술 압축 | 없음 | AU24 (mouthPress) 실시간 표시 |
| 음성 분석 | 없음 | `VoiceAnalyzer` 스켈레톤 (Phase 2 활성화) |
| 데이터 로깅 | 없음 | `SessionLogger` JSON 기록 |
| UI 레이아웃 | 단일 컬럼 | **4분할 대시보드** (카메라/지표/그래프/대화) |
| 실시간 그래프 | 없음 | **pyqtgraph 시계열 차트** (스트레스+깜빡임) |
| 스레드 안전성 | 직접 호출 (크래시 위험) | **pyqtSignal 기반** (안전) |
| LLM 말투 | 기계적 존댓말 | **친근한 경어체** (피노키오 캐릭터) |
| STT 시간 | timeout=5초, limit=5초 | **timeout=20초, limit=60초** |
| 프로젝트명 | EyeCon | 피노키오 (Pinocchio) |

## 4. 디렉토리 구조

```
~/dev_ws/eyecon/
├── main.py                  # PyQt6 메인 윈도우 (PinocchioApp) — 4분할 대시보드
├── requirements.txt
├── core/
│   ├── __init__.py
│   ├── vision.py            # VisionEngine — FaceLandmarker + 478점 + Blendshapes
│   ├── voice_analyzer.py    # VoiceAnalyzer — librosa 음성 분석 (Phase 2)
│   ├── analyzer.py          # Analyzer — 멀티모달 퓨전 (Phase 3)
│   ├── baseline.py          # BaselineCollector — 개인 베이스라인 학습
│   └── llm_client.py        # LLMClient — Ollama EXAONE + 친근한 프롬프트
├── utils/
│   ├── __init__.py
│   ├── tts_engine.py        # TTSEngine — Edge TTS 음성 출력
│   ├── stt_engine.py        # STTWorker — Google STT + WAV 저장
│   └── logger.py            # SessionLogger — JSON 데이터 로깅
├── config/
│   ├── __init__.py
│   └── settings.py          # 모든 설정값 중앙 관리
├── assets/
│   └── face_landmarker_v2_with_blendshapes.task
├── logs/                    # 세션 로그 (자동 생성)
└── temp/                    # TTS/STT 임시 파일 (자동 생성)
```

## 5. 해결한 이슈

### 5.1 앱 크래시 (Segmentation Fault)
- **원인:** TTS/LLM 스레드에서 Qt 위젯에 직접 접근
- **해결:** `pyqtSignal` 도입 → 백그라운드 → 메인 스레드 안전 전달
  - `_tts_done_signal` → `_on_tts_complete_safe`
  - `_llm_response_signal` → `_on_llm_response_safe`

### 5.2 LLM 기계적 말투
- **원인:** 프롬프트가 단순 지시형
- **해결:** 피노키오 캐릭터 설정 + 말투 예시 포함 프롬프트
  - 친근한 경어체 (`~요`, `~죠`, `~네요`), 공감 우선

### 5.3 사용자 발화 끊김
- **원인:** `phrase_time_limit` 너무 짧음
- **해결:** timeout 20초, phrase_time_limit 60초로 확대

### 5.4 실시간 그래프 미표시
- **원인:** `_update_graph()`가 `face_data.detected` 블록 안에 있었음
- **해결:** 얼굴 감지 여부 무관하게 항상 업데이트
  - 5프레임 간격 (부하 절감), X축 자동 스크롤 (최근 60초)

## 6. 4분할 대시보드 레이아웃

```
┌──────────────────┬──────────────────────────┐
│ 📷 실시간 영상    │ 😐 감정: Neutral          │
│  (랜드마크 표시)  │  종합 스코어: ████░ 72    │
│                  │ ─── 영상 지표 ──────     │
│                  │ 👁 시선 / 👀 깜빡임       │
│                  │ ⚫ 동공 / ↔️ 비대칭        │
│                  │ ⚡ 미세 표정 / 👄 입술 압축 │
│                  │ ─── 음성 지표 ──────     │
│                  │ 🎵 피치 / ⏱️ 응답 지연     │
│                  │ 💬 비유창성 / 📈 말 속도   │
├──────────────────┼──────────────────────────┤
│ 📊 실시간 그래프   │ 💬 대화 로그             │
│  스트레스 (빨강)  │ [피노키오] 안녕하세요~    │
│  깜빡임 (파랑)    │ [사용자] 답변...         │
│  X축 자동 스크롤  │ [피노키오] 공감+질문     │
└──────────────────┴──────────────────────────┘
```

## 7. 다음 단계 (Phase 2)

- [ ] Phase 2A: 영상 6개 지표 고도화
  - 깜빡임/동공 베이스라인 대비 변화율
  - Blendshapes 급변 감지 → 미세 표정
  - 시선 고정/회피 시간 분석
- [ ] Phase 2B: 음성 7개 지표 활성화
  - STTWorker `audio_signal` → VoiceAnalyzer 파이프라인
  - 피치, Jitter/Shimmer, 응답 지연, 비유창성, 말 속도, 음량
  - 지표 패널 실시간 연동
- [ ] 베이스라인 수집 (30초) 자동 시작

---

> **Phase 1 완료: v2.6 → v3.1. 기존 기능 100% 보존 + 4분할 대시보드 + 실시간 그래프 + 안정성 확보.**
