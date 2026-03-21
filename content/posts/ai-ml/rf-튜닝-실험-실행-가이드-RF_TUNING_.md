---
title: "RF 튜닝 실험 실행 가이드"
date: 2026-03-21
draft: true
tags: ["ai-ml"]
categories: ["ai-ml"]
description: "기존 Random Forest 모델(94.92% accuracy)의 실시간 낙상 탐지 성능을 개선하기 위한 실험 스크립트입니다. **핵심 원칙:** - ✅ 기존 모델 파일 변경 없음 (읽기 전용 로드)"
---

# RF 튜닝 실험 실행 가이드

## 📅 날짜: 2026-02-06

---

## 1. 개요

기존 Random Forest 모델(94.92% accuracy)의 실시간 낙상 탐지 성능을 개선하기 위한 실험 스크립트입니다.

**핵심 원칙:**
- ✅ 기존 모델 파일 변경 없음 (읽기 전용 로드)
- ✅ 모든 결과는 `experiments/rf_tuning_YYYYMMDD_HHMMSS/`에 별도 저장
- ✅ 동일 테스트셋으로 모든 전략을 공정 비교

---

## 2. 4가지 튜닝 전략

| 순서 | 전략 | 내용 | 기대 효과 |
|------|------|------|----------|
| 1 | Threshold 조정 | 판정 기준을 0.20~0.50으로 변경 | Recall ↑ (FN 감소) |
| 2 | Optuna HP 최적화 | 100회 탐색으로 최적 파라미터 발견 | 전체 성능 ↑ |
| 3 | Feature Selection | 상위 50/80/100/130개 feature 선별 | 효율 ↑, 과적합 ↓ |
| 4 | 조합 전략 | class_weight + Optuna + Threshold 조합 | 최적 균형 |

---

## 3. 실행 방법

### 3.1 사전 준비

```bash
# 필요 패키지 설치
pip install optuna --break-system-packages

# (이미 설치되어 있을 패키지)
# scikit-learn, pandas, numpy, matplotlib, seaborn
```

### 3.2 실행

```bash
cd /home/gjkong/dev_ws/yolo/myproj
python rf_tuning_experiment.py
```

### 3.3 경로 설정 (필요시)

스크립트 내 `ExperimentConfig` 클래스에서 경로를 확인/수정:

```python
@dataclass
class ExperimentConfig:
    project_root: str = "/home/gjkong/dev_ws/yolo/myproj"
    # RF 모델: {project_root}/models/binary/random_forest_model.pkl
    # 데이터: {project_root}/dataset/binary/train.csv, test.csv
```

---

## 4. 출력 구조

```
experiments/rf_tuning_YYYYMMDD_HHMMSS/
├── RF_TUNING_EXPERIMENT_REPORT.md    ← 종합 비교 리포트
├── threshold_analysis.png            ← Threshold별 메트릭 변화
├── strategy_comparison.png           ← 전략별 최적 결과 비교
├── confusion_matrices.png            ← 주요 모델 Confusion Matrix
├── roc_curves.png                    ← ROC 커브 비교
├── feature_importance_top30.png      ← Feature 중요도 상위 30
└── models/
    └── rf_optuna_best.pkl            ← Optuna 최적 모델 (별도 저장)
```

---

## 5. 설정 조정

`ExperimentConfig`에서 실험 파라미터를 변경할 수 있습니다:

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `threshold_range` | [0.20~0.50] | 테스트할 threshold 목록 |
| `optuna_n_trials` | 100 | Optuna 탐색 횟수 (↑ = 더 정밀, 더 느림) |
| `optuna_metric` | "recall" | 최적화 기준 (recall / f1 / accuracy) |
| `top_k_features` | [50, 80, 100, 130] | Feature Selection 테스트 개수 |
| `n_inference_repeats` | 50 | 추론 속도 측정 반복 횟수 |

---

## 6. 주의사항

- Optuna 100회 탐색에 약 5~15분 소요 (데이터 크기에 따라 다름)
- 기존 모델 (`models/binary/random_forest_model.pkl`)은 절대 수정되지 않음
- 실험 결과를 실제 배포에 적용하려면 별도 작업 필요
