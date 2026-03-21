---
title: "Home Safe Solution - Random Forest 튜닝 실험 보고서"
date: 2026-03-21
draft: true
tags: ["ai-ml"]
categories: ["ai-ml"]
description: "기존 Random Forest 모델의 실시간 낙상 탐지 성능을 개선하기 위해 4가지 튜닝 전략을 실험하고, 동일 테스트셋으로 비교 평가합니다. | 전략 | 설명 | 목표 | |------|------|------|"
---

# Home Safe Solution - Random Forest 튜닝 실험 보고서
## 생성일: 2026-02-06 19:16

---

## 1. 실험 개요

### 1.1 목적
기존 Random Forest 모델의 실시간 낙상 탐지 성능을 개선하기 위해 4가지 튜닝 전략을 실험하고, 동일 테스트셋으로 비교 평가합니다.

### 1.2 실험 전략

| 전략 | 설명 | 목표 |
|------|------|------|
| 전략 1 | Threshold 조정 (0.20~0.50) | Recall ↑ (놓침 최소화) |
| 전략 2 | Optuna 하이퍼파라미터 최적화 (100회) | 전체 성능 ↑ |
| 전략 3 | Feature Selection (상위 [50, 80, 100, 130]) | 효율성 ↑, 과적합 ↓ |
| 전략 4 | 조합 전략 (class_weight + Optuna + Threshold) | 최적 균형 |

### 1.3 기존 모델 보호

- ✅ 기존 모델 파일 변경 없음 (읽기 전용 로드)
- ✅ 모든 실험 결과는 별도 디렉토리에 저장: `/home/gjkong/dev_ws/yolo/myproj/experiments/rf_tuning_20260206_191149`
- ✅ 새로 학습된 모델은 `models/` 하위에 별도 저장

---

## 2. Baseline (기존 모델)

| 항목 | 값 |
|------|-----|
| Accuracy | 0.9492 (94.92%) |
| Precision | 0.8776 |
| Recall | 0.9663 |
| F1-Score | 0.9198 |
| AUC | 0.9956 |
| Inference Time | 13.4578 ms |
| Threshold | 0.5 |

**Confusion Matrix (Baseline):**

|  | Pred: Normal | Pred: Fall |
|--|-------------|-----------|
| **Actual: Normal** | 194 (TN) | 12 (FP) |
| **Actual: Fall** | 3 (FN) | 86 (TP) |

---

## 3. 전략 1: Threshold 조정

기존 모델의 확률 출력에 다양한 threshold를 적용하여 Recall과 Precision의 트레이드오프를 분석합니다.

| Threshold | Accuracy | Precision | Recall | F1-Score | FP | FN |
|-----------|----------|-----------|--------|----------|-----|-----|
| 0.20 | 0.9288 | 0.8091 | 1.0000 | 0.8945 | 21 | 0 |
| 0.25 | 0.9356 | 0.8241 | 1.0000 | 0.9036 | 19 | 0 |
| 0.30 | 0.9390 | 0.8318 | 1.0000 | 0.9082 | 18 | 0 |
| 0.35 | 0.9458 | 0.8544 | 0.9888 | 0.9167 | 15 | 1 |
| 0.40 | 0.9492 | 0.8627 | 0.9888 | 0.9215 | 14 | 1 |
| 0.45 | 0.9458 | 0.8687 | 0.9663 | 0.9149 | 13 | 3 |
| 0.50 ⬅ default | 0.9492 | 0.8776 | 0.9663 | 0.9198 | 12 | 3 |

![Threshold Analysis](threshold_analysis.png)

**분석:** Recall 최대화 threshold = 0.20 (Recall=1.0000), F1 최대화 threshold = 0.40 (F1=0.9215)

---

## 4. 전략 2: Optuna 하이퍼파라미터 최적화

**탐색 횟수:** 100회
**최적화 기준:** recall
**Best CV recall:** 0.9762

**Best 파라미터:**

| 파라미터 | 값 |
|---------|-----|
| n_estimators | 343 |
| max_depth | 5 |
| min_samples_split | 19 |
| min_samples_leaf | 10 |
| max_features | log2 |
| class_weight | balanced_subsample |

**성능 결과:**

| 모델 | Accuracy | Precision | Recall | F1-Score | AUC |
|------|----------|-----------|--------|----------|------|
| RF Optuna (th=0.50) | 0.9220 | 0.8113 | 0.9663 | 0.8821 | 0.9923 |
| RF Optuna (th=0.80) | 0.9661 | 0.9647 | 0.9213 | 0.9425 | 0.9923 |

---

## 5. 전략 3: Feature Selection

Feature Importance 기반으로 상위 K개 feature만 선별하여 학습/평가합니다.

| 모델 | Features | Accuracy | Precision | Recall | F1-Score | Speed (ms) |
|------|----------|----------|-----------|--------|----------|------------|
| Baseline (전체) | 181 | 0.9492 | 0.8776 | 0.9663 | 0.9198 | 13.4578 |
| Top-50 | 50 | 0.9458 | 0.8763 | 0.9551 | 0.9140 | 13.4826 |
| Top-80 | 80 | 0.9559 | 0.9043 | 0.9551 | 0.9290 | 15.2426 |
| Top-100 | 100 | 0.9559 | 0.8958 | 0.9663 | 0.9297 | 13.5132 |
| Top-130 | 130 | 0.9627 | 0.9149 | 0.9663 | 0.9399 | 13.2654 |

![Feature Importance](feature_importance_top30.png)

---

## 6. 전략 4: 조합 전략

class_weight, Optuna 파라미터, Threshold를 조합하여 최적 모델을 탐색합니다.

| 모델 | Accuracy | Precision | Recall | F1-Score | AUC |
|------|----------|-----------|--------|----------|------|
| RF Balanced (th=0.59) | 0.9695 | 0.9444 | 0.9551 | 0.9497 | 0.9953 |
| RF Optuna+Balanced (th=0.79) | 0.9627 | 0.9535 | 0.9213 | 0.9371 | 0.9918 |
| RF weight(Fall=2x, th=0.65) | 0.9661 | 0.9759 | 0.9101 | 0.9419 | 0.9951 |
| RF weight(Fall=3x, th=0.46) | 0.9593 | 0.9053 | 0.9663 | 0.9348 | 0.9945 |
| RF weight(Fall=5x, th=0.57) | 0.9593 | 0.9326 | 0.9326 | 0.9326 | 0.9942 |

---

## 7. 종합 비교 (Top 10)

| 순위 | 모델 | Accuracy | Precision | Recall | F1-Score | AUC | Speed (ms) |
|------|------|----------|-----------|--------|----------|------|------------|
| 1 | RF Balanced (th=0.59)  | 0.9695 | 0.9444 | 0.9551 | 0.9497 | 0.9953 | 24.9453 |
| 2 | RF Optuna (th=0.80)  | 0.9661 | 0.9647 | 0.9213 | 0.9425 | 0.9923 | 36.8503 |
| 3 | RF weight(Fall=2x, th=0.65)  | 0.9661 | 0.9759 | 0.9101 | 0.9419 | 0.9951 | 25.5903 |
| 4 | RF Top-130 Features  | 0.9627 | 0.9149 | 0.9663 | 0.9399 | 0.9942 | 13.2654 |
| 5 | RF Optuna+Balanced (th=0.79)  | 0.9627 | 0.9535 | 0.9213 | 0.9371 | 0.9918 | 37.0750 |
| 6 | RF weight(Fall=3x, th=0.46)  | 0.9593 | 0.9053 | 0.9663 | 0.9348 | 0.9945 | 25.0090 |
| 7 | RF weight(Fall=5x, th=0.57)  | 0.9593 | 0.9326 | 0.9326 | 0.9326 | 0.9942 | 24.7639 |
| 8 | RF Top-100 Features  | 0.9559 | 0.8958 | 0.9663 | 0.9297 | 0.9945 | 13.5132 |
| 9 | RF Top-80 Features  | 0.9559 | 0.9043 | 0.9551 | 0.9290 | 0.9950 | 15.2426 |
| 10 | RF (threshold=0.40)  | 0.9492 | 0.8627 | 0.9888 | 0.9215 | 0.9956 | 13.2371 |

![Strategy Comparison](strategy_comparison.png)

![ROC Curves](roc_curves.png)

![Confusion Matrices](confusion_matrices.png)

---

## 8. 결론 및 권장사항

### 8.1 최고 성능 모델

| 기준 | 모델 | 값 |
|------|------|----|
| 최고 Accuracy | RF Balanced (th=0.59) | 0.9695 |
| 최고 Recall (낙상 감지율) | RF (threshold=0.20) | 1.0000 |
| 최고 F1-Score (균형) | RF Balanced (th=0.59) | 0.9497 |

### 8.2 Baseline 대비 개선

- **Recall 개선:** +0.0337 (+3.37%p) — Baseline RF (th=0.50) → RF (threshold=0.20)
- **F1 개선:** +0.0299 (+2.99%p) — Baseline RF (th=0.50) → RF Balanced (th=0.59)

### 8.3 권장 시나리오

| 시나리오 | 권장 모델 | 이유 |
|---------|----------|------|
| 낙상 놓침 최소화 | RF (threshold=0.20) | Recall 1.0000 |
| 균형 잡힌 성능 | RF Balanced (th=0.59) | F1 0.9497 |
| 최고 정확도 | RF Balanced (th=0.59) | Accuracy 0.9695 |

### 8.4 참고 사항

- 낙상 감지 시스템에서는 FN(놓침)이 FP(오경보)보다 치명적이므로 Recall 우선이 권장됩니다.
- Threshold를 낮추면 Recall이 높아지지만 Precision이 낮아져 오경보가 증가합니다.
- 실제 배포 시에는 Post-processing(연속 N프레임 확인) 로직을 추가하여 오경보를 줄일 수 있습니다.
- 기존 모델 파일은 변경되지 않았으므로 언제든 원래 설정으로 복원 가능합니다.

---

## 9. 파일 경로

- **기존 모델:** `/home/gjkong/dev_ws/yolo/myproj/models/binary/random_forest_model.pkl`
- **실험 결과:** `/home/gjkong/dev_ws/yolo/myproj/experiments/rf_tuning_20260206_191149`
- **본 보고서:** `/home/gjkong/dev_ws/yolo/myproj/experiments/rf_tuning_20260206_191149/RF_TUNING_EXPERIMENT_REPORT.md`

---

**생성 도구:** `rf_tuning_experiment.py`
**생성일:** 2026-02-06 19:16
**저장 경로:** `/home/gjkong/dev_ws/yolo/myproj/experiments/rf_tuning_20260206_191149`