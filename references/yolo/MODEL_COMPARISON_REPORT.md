# Home Safe Solution - 모델 성능 비교 분석 보고서
## 생성일: 2026-02-05 19:43

---

## 1. 분석 개요

- **비교 모델:** 3개
- **추론 반복 횟수:** 50회 (속도 측정)
- **평가 방식:** 각 모델의 고유 테스트 파이프라인 사용

### 모델별 테스트 데이터

| 모델 | 테스트 데이터 | 샘플 수 | 추론 방식 |
|------|-------------|---------|----------|
| 🌲 Random Forest | binary/test.csv (295 samples) | 295 | 프레임 단위 → 다수결 |
| 📊 ST-GCN (Original) | binary/test_data.npy (60-frame sequences) | 38 | 60프레임 시퀀스 |
| 🚀 ST-GCN (Fine-tuned) | binary/test_data.npy (60-frame sequences) | 38 | 60프레임 시퀀스 |

> ⚠ **참고:** 각 모델은 자체 테스트 파이프라인으로 평가되었습니다. RF는 feature 기반, ST-GCN은 시퀀스 기반으로 동일 데이터라도 입력 형태가 다릅니다.

## 2. 종합 성능 비교

| 항목 | 🌲 Random Forest | 📊 ST-GCN (Original) | 🚀 ST-GCN (Fine-tuned) |
|------|------|------|------|
| **Accuracy** | **94.92%** | **21.05%** | **86.84%** |
| **Precision** | 0.8854 | 0.2105 | 0.7143 |
| **Recall** | 0.9551 | 1.0000 | 0.6250 |
| **F1-Score** | 0.9189 | 0.3478 | 0.6667 |
| **AUC** | 0.9951 | 0.6208 | 0.9000 |
| **Inference Time** | 0.08 ms | 0.26 ms | 0.24 ms |
| **Model Size** | 1.25 MB | 29.74 MB | 9.97 MB |
| **Parameters** | 100 trees, 181 features | 2.59M | 2.59M |
| **Test Samples** | 295 | 38 | 38 |

## 3. 상세 Classification Report

### 🌲 Random Forest

```
              precision    recall  f1-score   support

      Normal       0.98      0.95      0.96       206
        Fall       0.89      0.96      0.92        89

    accuracy                           0.95       295
   macro avg       0.93      0.95      0.94       295
weighted avg       0.95      0.95      0.95       295

```

### 📊 ST-GCN (Original)

```
              precision    recall  f1-score   support

      Normal       0.00      0.00      0.00        30
        Fall       0.21      1.00      0.35         8

    accuracy                           0.21        38
   macro avg       0.11      0.50      0.17        38
weighted avg       0.04      0.21      0.07        38

```

### 🚀 ST-GCN (Fine-tuned)

```
              precision    recall  f1-score   support

      Normal       0.90      0.93      0.92        30
        Fall       0.71      0.62      0.67         8

    accuracy                           0.87        38
   macro avg       0.81      0.78      0.79        38
weighted avg       0.86      0.87      0.87        38

```

## 4. Confusion Matrix

### 🌲 Random Forest (n=295)

|  | Pred: Normal | Pred: Fall |
|--|-------------|-----------|
| **Actual: Normal** | 195 (TN) | 11 (FP) |
| **Actual: Fall** | 4 (FN) | 85 (TP) |

### 📊 ST-GCN (Original) (n=38)

|  | Pred: Normal | Pred: Fall |
|--|-------------|-----------|
| **Actual: Normal** | 0 (TN) | 30 (FP) |
| **Actual: Fall** | 0 (FN) | 8 (TP) |

### 🚀 ST-GCN (Fine-tuned) (n=38)

|  | Pred: Normal | Pred: Fall |
|--|-------------|-----------|
| **Actual: Normal** | 28 (TN) | 2 (FP) |
| **Actual: Fall** | 3 (FN) | 5 (TP) |

## 5. 시각화

![종합 대시보드](dashboard_comparison.png)

![Confusion Matrix](confusion_matrices.png)

![ROC Curve](roc_curves.png)

![Inference Time](inference_time.png)

![Model Size](model_size.png)

## 6. 분석 결론

- **최고 정확도:** 🌲 Random Forest (94.92%)
- **최고 F1-Score:** 🌲 Random Forest (0.9189)
- **최고 Recall (낙상 감지율):** 📊 ST-GCN (Original) (1.0000)
- **최고 속도:** 🌲 Random Forest (0.08 ms)

### 권장 사용 시나리오

| 시나리오 | 권장 모델 | 이유 |
|---------|----------|------|
| 실시간 빠른 응답 | 🌲 Random Forest | 최소 지연시간 (0.08 ms) |
| 최고 정확도 우선 | 🌲 Random Forest | 최고 정확도 (94.92%) |
| 낙상 놓침 최소화 | 📊 ST-GCN (Original) | 최고 Recall (1.0000) |
| 균형 잡힌 선택 | 🌲 Random Forest | 최고 F1-Score (0.9189) |

### 참고 사항

- RF와 ST-GCN은 입력 형태가 다르므로 (feature vs sequence) 직접 비교 시 해석에 주의가 필요합니다.
- 실제 운영 환경에서는 YOLO 포즈 추정 → 특징 추출/시퀀스 구성 시간도 고려해야 합니다.
- 낙상 감지 시스템에서는 Recall (낙상을 놓치지 않는 것)이 Precision보다 중요할 수 있습니다.

## 7. 모델 경로

- 🌲 Random Forest: `/home/gjkong/dev_ws/yolo/myproj/models/binary/random_forest_model.pkl`
- 📊 ST-GCN (Original): `/home/gjkong/dev_ws/st_gcn/checkpoints/best_model_binary.pth`
- 🚀 ST-GCN (Fine-tuned): `/home/gjkong/dev_ws/st_gcn/checkpoints_finetuned/best_model_finetuned.pth`

---

**생성 도구:** `compare_models.py`
**생성일:** 2026-02-05 19:43
**저장 경로:** `/home/gjkong/dev_ws/yolo/myproj/scripts/admin/Model_Compare_Report/20260205_194318`