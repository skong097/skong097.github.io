---
title: "Home Safe Solution - Work Log"
date: 2026-03-21
draft: true
tags: ["ai-ml"]
categories: ["ai-ml"]
description: "기존 RF 모델(binary, 94.92%)의 실시간 낙상 탐지 성능 개선을 위해 4가지 전략 실험. | 항목 | 내용 | |------|------|"
---

# Home Safe Solution - Work Log

## 📅 날짜: 2026-02-06 (목)

---

## 1. 오전~오후: RF 튜닝 실험 ✅ 완료

### 1.1 목적
기존 RF 모델(binary, 94.92%)의 실시간 낙상 탐지 성능 개선을 위해 4가지 전략 실험.

### 1.2 데이터셋

| 항목 | 내용 |
|------|------|
| 분류 | Binary (Normal=0, Fall=1) |
| Train | 2,354 samples (Normal 1,641 / Fall 713) |
| Test | 295 samples (Normal 206 / Fall 89) |
| Features | 181개 |
| 경로 | `dataset/binary/train.csv`, `test.csv` |

### 1.3 4가지 전략 결과 요약

| 전략 | 최적 모델 | Accuracy | Recall | F1 |
|------|----------|----------|--------|------|
| 1. Threshold 조정 | th=0.30 | 93.90% | **1.0000** | 0.9082 |
| 2. Optuna 최적화 | th=0.80 | 96.61% | 0.9213 | 0.9425 |
| 3. Feature Selection | Top-130 | 96.27% | 0.9663 | 0.9399 |
| 4. 조합 전략 | **RF Balanced (th=0.59)** | **96.95%** | 0.9551 | **0.9497** |

### 1.4 추천 모델: RF Balanced (th=0.59)

| 항목 | Baseline | RF Balanced | 변화 |
|------|----------|-------------|------|
| Accuracy | 94.92% | **96.95%** | **+2.03%p** |
| F1-Score | 0.9198 | **0.9497** | **+0.0299** |
| Recall | 0.9663 | 0.9551 | -0.0112 |

설정: `class_weight='balanced'`, `n_estimators=200`, `threshold=0.59`

### 1.5 실험 산출물
```
experiments/rf_tuning_20260206_191149/
├── RF_TUNING_EXPERIMENT_REPORT.md
├── threshold_analysis.png
├── strategy_comparison.png
├── confusion_matrices.png
├── roc_curves.png
├── feature_importance_top30.png
└── models/
    └── rf_optuna_best.pkl
```

---

## 2. 저녁: RF Balanced 배포 시도 ⚠️ 실패 → 원복

### 2.1 작성한 배포 스크립트

**apply_rf_balanced.py** — 5단계 자동화 스크립트
1. 기존 모델 백업 → `models_integrated/binary/backups/`
2. RF Balanced 학습 (`class_weight='balanced'`, `n_estimators=200`)
3. 기존 경로에 저장 → `models_integrated/binary/random_forest_model.pkl`
4. 설정 파일 생성 → `models_integrated/binary/rf_config.json` (threshold=0.59)
5. 성능 검증

### 2.2 monitoring_page.py 수정 시도 및 문제

**수정하려던 내용:**

| # | 수정 대상 | 변경 내용 |
|---|----------|----------|
| 1 | RF 모델 경로 | `models_integrated/3class` → `models_integrated/binary` |
| 2 | class_names | 3class(Normal/Falling/Fallen) → binary(Normal/Fall) |
| 3 | predict_fall() | 규칙 기반 임시 로직 → RF `predict_proba` + threshold |
| 4 | update_fall_info() | binary/3class 호환 |
| 5 | save_fall_event() | binary/3class 호환 |
| 6 | draw_prediction() | `class_colors[i]` KeyError 방지 |

**발생한 문제들:**

| 순서 | 에러 | 원인 |
|------|------|------|
| 1차 | `IndentationError` (L1109) | docstring 앞 공백 2칸 여분 |
| 2차 | GUI 정상 로드, Start 시 PerformanceWarning 폭주 | `df[col] = 0` 루프가 181개 컬럼을 하나씩 추가 |
| 3차 | GUI 로드 안됨 (크래시) | 수정 누적으로 코드 꼬임 |

### 2.3 원복 완료 ✅

- monitoring_page.py를 **수정 전 원본으로 완전 복원**
- GUI 정상 동작 확인
- 원본 + 폴더 전체 백업 완료

---

## 3. 교훈 (Lessons Learned)

### 코드 수정 시 주의사항
1. **원본 백업 필수** — 수정 전 원본을 별도 보관
2. **한 곳씩 수정 → 테스트** — 여러 곳 동시 수정 금지
3. **predict_fall()의 구조적 문제** — 현재 규칙 기반 임시 로직으로 RF 모델을 실제 사용하지 않음
4. **feature 정렬 방식** — `for col in ... df[col] = 0` 루프 대신 dict comprehension 사용 필요
5. **binary/3class 호환** — class_names, class_colors, proba 길이 등 모든 참조 지점 동시 수정 필요

### 발견된 monitoring_page.py 현황
- **predict_fall()**: RF 모델 미사용 (hip_height/aspect_ratio 규칙 기반 임시 코드)
- **RF 모델 경로**: `models_integrated/3class/` (3class 모델 사용 중)
- **class_names**: 3class 기준 (`{0:'Normal', 1:'Falling', 2:'Fallen'}`)
- YOLO 모델: `yolo11s-pose.pt` ✅ 정상

---

## 4. 현재 상태 (2026-02-06 마감 기준)

| 항목 | 상태 |
|------|------|
| RF 튜닝 실험 | ✅ 완료 (RF Balanced 선정) |
| apply_rf_balanced.py | ✅ 작성 완료 (미실행) |
| monitoring_page.py 수정 | ❌ 원복 (수정 전 원본 상태) |
| rf_config.json | ❌ 미생성 |
| GUI 동작 | ✅ 정상 (원본 상태) |

### 파일 위치
```
프로젝트: /home/gjkong/dev_ws/yolo/myproj
├── models_integrated/binary/          ← RF 모델 (현재 3class 기준 동작)
├── models_integrated/3class/          ← 3class RF 모델
├── dataset/binary/                    ← 데이터셋
├── experiments/rf_tuning_20260206_*/  ← 실험 결과
├── gui/monitoring_page.py             ← 원본 복원 상태
└── scripts/admin/
    └── apply_rf_balanced.py           ← 배포 스크립트 (미실행)
```

---

## 5. 다음 작업 (TODO)

### 최우선: monitoring_page.py에 RF Balanced 적용 (단계적)
```
Step 1: predict_fall()만 수정 → 테스트
Step 2: 모델 경로 변경 → 테스트  
Step 3: class_names binary 전환 → 테스트
Step 4: update_fall_info, draw_prediction 호환 → 테스트
Step 5: rf_config.json threshold 로드 → 테스트
```

### 후속
- [ ] Post-processing 로직 (연속 N프레임 확인)
- [ ] ST-GCN 테스트 데이터 확장
- [ ] Phase C: Optuna (ST-GCN 대상)

---

**작성일시:** 2026-02-06 23:30
**작성자:** Claude AI Assistant
