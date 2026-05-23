# Home Safe Solution - 모델 성능 비교 분석 보고서
## 생성일: 2026-02-08 15:53

---

## 1. 분석 개요

- **비교 모델:** 2개
- **추론 반복 횟수:** 50회 (속도 측정)
- **평가 방식:** 각 모델의 고유 테스트 파이프라인 사용

### 모델별 테스트 데이터

| 모델 | 테스트 데이터 | 샘플 수 | 추론 방식 |
|------|-------------|---------|----------|
| 🌲 Random Forest | features_normalized (video-split, 385 videos, 28611 frames) | 28611 | 프레임 단위 → 다수결 |
| 🚀 ST-GCN (Fine-tuned) | binary_v2/test_data.npy (60-frame sequences, 1930 videos) | 534 | 60프레임 시퀀스 |

> ⚠ **참고:** 각 모델은 자체 테스트 파이프라인으로 평가되었습니다. RF는 feature 기반, ST-GCN은 시퀀스 기반으로 동일 데이터라도 입력 형태가 다릅니다.

## 2. 종합 성능 비교

| 항목 | 🌲 Random Forest | 🚀 ST-GCN (Fine-tuned) |
|------|------|------|
| **Accuracy** | **97.99%** | **99.63%** |
| **Precision** | 0.9466 | 0.9940 |
| **Recall** | 0.9430 | 0.9940 |
| **F1-Score** | 0.9448 | 0.9940 |
| **AUC** | 0.9971 | 0.9998 |
| **Inference Time** | 0.01 ms | 0.34 ms |
| **Model Size** | 43.96 MB | 29.77 MB |
| **Parameters** | 200 trees, 181 features | 2.59M |
| **Test Samples** | 28611 | 534 |

## 3. 상세 Classification Report

### 🌲 Random Forest

```
              precision    recall  f1-score   support

      Normal       0.99      0.99      0.99     23403
        Fall       0.95      0.94      0.94      5208

    accuracy                           0.98     28611
   macro avg       0.97      0.97      0.97     28611
weighted avg       0.98      0.98      0.98     28611

```

### 🚀 ST-GCN (Fine-tuned)

```
              precision    recall  f1-score   support

      Normal       1.00      1.00      1.00       366
        Fall       0.99      0.99      0.99       168

    accuracy                           1.00       534
   macro avg       1.00      1.00      1.00       534
weighted avg       1.00      1.00      1.00       534

```

## 4. Confusion Matrix

### 🌲 Random Forest (n=28611)

|  | Pred: Normal | Pred: Fall |
|--|-------------|-----------|
| **Actual: Normal** | 23126 (TN) | 277 (FP) |
| **Actual: Fall** | 297 (FN) | 4911 (TP) |

### 🚀 ST-GCN (Fine-tuned) (n=534)

|  | Pred: Normal | Pred: Fall |
|--|-------------|-----------|
| **Actual: Normal** | 365 (TN) | 1 (FP) |
| **Actual: Fall** | 1 (FN) | 167 (TP) |

## 5. 시각화

![종합 대시보드](dashboard_comparison.png)

![Confusion Matrix](confusion_matrices.png)

![Precision & Recall](precision_recall.png)

![ROC Curve](roc_curves.png)

![Inference Time](inference_time.png)

![Model Size](model_size.png)

## 6. 분석 결론

- **최고 정확도:** 🚀 ST-GCN (Fine-tuned) (99.63%)
- **최고 F1-Score:** 🚀 ST-GCN (Fine-tuned) (0.9940)
- **최고 Recall (낙상 감지율):** 🚀 ST-GCN (Fine-tuned) (0.9940)
- **최고 속도:** 🌲 Random Forest (0.01 ms)

### 권장 사용 시나리오

| 시나리오 | 권장 모델 | 이유 |
|---------|----------|------|
| 실시간 빠른 응답 | 🌲 Random Forest | 최소 지연시간 (0.01 ms) |
| 최고 정확도 우선 | 🚀 ST-GCN (Fine-tuned) | 최고 정확도 (99.63%) |
| 낙상 놓침 최소화 | 🚀 ST-GCN (Fine-tuned) | 최고 Recall (0.9940) |
| 균형 잡힌 선택 | 🚀 ST-GCN (Fine-tuned) | 최고 F1-Score (0.9940) |

### 참고 사항

- RF와 ST-GCN은 입력 형태가 다르므로 (feature vs sequence) 직접 비교 시 해석에 주의가 필요합니다.
- 실제 운영 환경에서는 YOLO 포즈 추정 → 특징 추출/시퀀스 구성 시간도 고려해야 합니다.
- 낙상 감지 시스템에서는 Recall (낙상을 놓치지 않는 것)이 Precision보다 중요할 수 있습니다.

## 7. 모델 경로

- 🌲 Random Forest: `/home/gjkong/dev_ws/yolo/myproj/models_integrated/binary_v3/random_forest_model.pkl`
- 🚀 ST-GCN (Fine-tuned): `/home/gjkong/dev_ws/st_gcn/checkpoints_v2/best_model.pth`

---

**생성 도구:** `compare_models.py`
**생성일:** 2026-02-08 15:53
**저장 경로:** `/home/gjkong/dev_ws/yolo/myproj/scripts/admin/Model_Compare_Report/20260208_155302`