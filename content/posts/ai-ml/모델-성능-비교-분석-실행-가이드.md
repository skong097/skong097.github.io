---
title: "모델 성능 비교 분석 실행 가이드"
date: 2026-03-21
draft: true
tags: ["ai-ml"]
categories: ["ai-ml"]
description: "각 모델의 **고유 테스트 파이프라인**을 존중하여 공정하게 비교합니다. | 모델 | 입력 형태 | 추론 방식 | 테스트 데이터 | |------|----------|----------|-------------|"
---

# 모델 성능 비교 분석 실행 가이드

## 설계 원칙

각 모델의 **고유 테스트 파이프라인**을 존중하여 공정하게 비교합니다.

| 모델 | 입력 형태 | 추론 방식 | 테스트 데이터 |
|------|----------|----------|-------------|
| 🌲 Random Forest | feature 벡터 | 프레임 단위 → 다수결 | RF 전용 test set (우선) / val_data fallback |
| 📊 ST-GCN Original | (N,3,60,17,1) | 60프레임 시퀀스 배치 | val_data.npy |
| 🚀 ST-GCN Fine-tuned | (N,3,60,17,1) | 60프레임 시퀀스 배치 | val_data.npy |

---

## 실행 방법

```bash
cd /home/gjkong/dev_ws/st_gcn/
python compare_models.py
```

---

## RF 테스트 데이터 탐색 순서

RF 파이프라인은 아래 경로를 순서대로 탐색합니다:

1. `models/binary/test_features.npy` + `test_labels.npy`
2. `models/binary/test_features.csv` + `test_labels.csv`
3. `models/binary/X_test.npy` + `y_test.npy`
4. `yolo/myproj/data/test_features.npy` + `test_labels.npy`
5. (fallback) ST-GCN `val_data.npy` → 프레임별 특징 추출 후 다수결

**RF 전용 테스트 데이터가 있다면** 위 경로 중 하나에 저장해 주세요.  
없으면 자동으로 fallback 모드로 동작합니다.

---

## 출력 결과 (일시 폴더)

```
~/dev_ws/yolo/myproj/scripts/admin/Model_Compare_Report/
└── 20260205_153042/
    ├── MODEL_COMPARISON_REPORT.md   # 종합 보고서
    ├── dashboard_comparison.png     # 종합 대시보드
    ├── confusion_matrices.png       # Confusion Matrix
    ├── roc_curves.png               # ROC Curve / AUC
    ├── inference_time.png           # 추론 속도 비교
    └── model_size.png               # 모델 크기/파라미터
```

실행할 때마다 새 타임스탬프 폴더가 생성되어 이전 결과가 보존됩니다.

---

## 필요 패키지

```bash
pip install numpy torch scikit-learn matplotlib joblib
```

---

## 커스터마이징

### 추론 속도 반복 횟수
```python
INFERENCE_REPEAT = 50  # 기본값
```

### 새 모델 추가
`ModelPipeline`을 상속받아 4개 메서드를 구현하면 됩니다:

```python
class NewModelPipeline(ModelPipeline):
    def load_model(self): ...
    def load_test_data(self): ...  # → (X, y_true)
    def predict(self, X): ...      # → (y_pred, y_prob)
    def measure_speed(self, X): ...
```

`main()` 함수의 `pipelines` 리스트에 추가하면 자동으로 비교에 포함됩니다.

---

**작성일:** 2026-02-05
