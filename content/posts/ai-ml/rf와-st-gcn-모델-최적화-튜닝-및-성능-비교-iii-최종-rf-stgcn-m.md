---
title: "RF와 ST-GCN 모델 최적화 튜닝 및 성능 비교 III (최종)"
date: 2026-03-21
draft: true
tags: ["ai-ml"]
categories: ["ai-ml"]
description: "> **출처**: Confluence 내부 문서 (2026-02-17 export) > **작성자**: 공국진 > **용도**: 블로그 포스트 작성 레퍼런스"
---

# RF와 ST-GCN 모델 최적화 튜닝 및 성능 비교 III (최종)

> **출처**: Confluence 내부 문서 (2026-02-17 export)  
> **작성자**: 공국진  
> **용도**: 블로그 포스트 작성 레퍼런스

---

## 1. 테스트 개요

- 이전 문서에서 Random Forest, ST-GCN (original), ST-GCN (fine_tuned) 3개 모델 성능 비교 결과, Random Forest가 가장 합리적 선택이라는 잠정 결론을 내렸었음
- 하지만 ST-GCN의 기술적 잠재력을 고려, 낙상 감지 문제는 **시계열(Time-series) 동작 데이터**이므로 ST-GCN같은 **시공간 그래프 신경망**이 더 많은 학습 데이터와 최적화를 거치면 다른 결과를 얻을 수 있을 것이라는 기대로 추가 테스트 진행

---

## 2. 최적화 대상

- ST-GCN(original)은 전반적으로 현저히 낮은 성능 → 사용 불가 판단
- 최적화 대상:
  - **Random Forest**
  - **ST-GCN (fine_tuned)**

---

## 3. 학습 데이터

| 경로 | 내용 |
|---|---|
| new_data/normal/ | 1,629개 .avi (NTU RGB+D) |
| new_data/fallen/ | 301개 .mp4 (추가수집) |
| new_data/features_normalized/normal_features.csv | 116,854행 (정규화) |
| new_data/features_normalized/fallen_features.csv | 25,510행 (정규화) |

---

## 4. RF 모델 성능 개선

### 4-1. 신규 데이터 대규모 증강

| 폴더 | 파일 수 | 라벨 |
|---|---|---|
| normal | 1,629개 (.avi, NTU RGB+D) | 0 (Normal) |
| falling → normal 통합 | 204개 (.avi) | 0 (Normal) |
| fallen (최종) | 301개 (.mp4, 추가수집) | 1 (Fallen) |

- **최종 데이터**: Normal 116,854프레임 (1,629영상), Fallen 25,510프레임 (301영상)
- **데이터 불균형 발생**: Normal vs Fallen = 약 4.6:1
- 이를 해소하기 위한 **4가지 전략** 적용 비교

### 4-2. 전략 비교

| 전략 | Acc | F1 | Prec | Recall | AUC | FP% | FN% |
|---|---|---|---|---|---|---|---|
| 1) Balanced | 97.8% | 94.0% | 95.9% | 92.1% | 99.7% | 0.9% | 7.9% |
| 2) Undersample 5:1 | 98.0% | 94.4% | 95.9% | 92.9% | 99.7% | 0.9% | 7.1% |
| **3) Undersample 3:1 + Bal** | **98.0%** | **94.5%** | **94.7%** | **94.3%** | **99.7%** | **1.2%** | **5.7%** |
| 4) Hybrid 5:1 + Bal | 97.9% | 94.3% | 95.5% | 93.0% | 99.7% | 1.0% | 7.0% |

**최적 모델**: Undersample 3:1 + Bal (Recall 94.3%, F1 94.5%)
- 본 과제 취지에 맞게 **Recall이 가장 높은** 전략 선택

### 4-3. 각 전략 설명

1. **Balanced**: sklearn `class_weight='balanced'` 사용. 데이터 그대로 두고, Fallen 오분류 패널티를 높임 (Normal 1개 = Fallen 4.6개)
2. **Undersample 5:1**: Normal 데이터를 버려서 비율을 5:1로 줄임 (Normal ~127,550개 사용)
3. **Undersample 3:1 + Bal (최적)**: Normal을 3:1 비율로 줄이고 (Normal ~76,530) + `class_weight='balanced'` 동시 적용. 데이터 비율 조정 + 패널티 가중치 조정 → **Recall 최고**
4. **Hybrid 5:1 + Bal**: Undersample + SMOTE(합성 오버샘플링) + Balanced 조합. 합성 데이터가 오히려 노이즈 → Recall 소폭 하락

### 4-4. 좌표 정규화 (v3)

bbox 기준 0~1 정규화:

```python
norm_x = np.clip((x - bbox_x_min) / bbox_width, 0, 1)
norm_y = np.clip((y - bbox_y_min) / bbox_height, 0, 1)
```

정규화 후 해상도 차이 제거, 진짜 구분 feature가 드러남:

| Feature | Normal | Fallen | 구분 |
|---|---|---|---|
| hip_height | 0.495 | 0.417 | 비슷 (해상도 무관) |
| bbox_aspect_ratio | 0.384 | 2.020 | **핵심 구분** |
| spine_angle | 10.1° | 65.9° | **핵심 구분** |

- 해상도가 1080p든 480p든, bbox 안에서의 상대적 위치만 남기므로 해상도 의존 문제 해결
- 매 프레임 YOLO 추론 시 실시간으로 bbox를 얻어서 그 자리에서 정규화

### 4-5. 성능 개선 추이

| 단계 | Fallen 영상 | F1 | Recall | Precision | AUC | FN Rate |
|---|---|---|---|---|---|---|
| v3 (30영상) | 30 | 74.0% | 63.7% | 88.4% | 99.1% | 36.3% |
| v3b (60영상) | 60 | 87.0% | 82.6% | 91.9% | 99.4% | 17.4% |
| v3b (301영상) | 301 | **94.5%** | **94.3%** | **94.7%** | **99.7%** | **5.7%** |

### 4-6. 실시간 영상 추론 (GUI) 테스트 결과

| 동작 | v2 (비정규화) | v3 (30영상) | v3b (60영상) | v3b (301영상) |
|---|---|---|---|---|
| 서있기 | Very Bad | Good | Good | Good |
| 앉기 | Bad | Good | Good | Good |
| 쓰러짐 | Bad | △ 50% 미만 | △ 65%+ | **Very Good** |

---

## 5. ST-GCN 모델 성능 개선

### 5-1. 대규모 데이터 증강/변환

- **기존**: 174샘플 (Normal 137, Fall 37) → 84.21%
- **변경**: RF와 동일한 추가 데이터 모두 활용하여 재학습

**데이터 변환 파이프라인** (`prepare_stgcn_data.py`):
- RF 동영상 (normal 1,629 + fallen 301)에서 YOLO Pose로 keypoint 추출
- 60프레임 시퀀스, stride 30 (50% overlap)
- 기존 ST-GCN과 동일 정규화 (hip center 기준, max distance → -1~1)
- 동영상 단위 split (seed=42, 20%)

| 항목 | 기존 (binary) | 신규 (binary_v2) | 증가 |
|---|---|---|---|
| Train | 174 샘플 | 2,040 샘플 | 11.7배 |
| Test | 38 샘플 | 534 샘플 | 14배 |
| Normal (Train) | 137 | 1,423 | |
| Fallen (Train) | 37 | 617 | |

데이터 누수 검증: 중복 시퀀스 1개, 중복 동영상 0개

### 5-2. PYSKL Pre-trained + Fine-tuning 설정

| 항목 | 설정 |
|---|---|
| Pre-trained | PYSKL ST-GCN NTU60 HRNet (56,000+ 동영상) |
| 구조 | Fine-tuned (data_bn + layers + 3-partition) |
| 차등 LR | FC=1e-3, Backbone=1e-4 |
| Class weight | Normal=1.0, Fallen=2.31 |
| Early stopping | 15 epochs |

### 5-3. Fine-tuning 설정 상세 설명

1. **Pre-trained (Transfer Learning)**: NTU RGB+D 60 데이터셋 — 60가지 동작을 56,000+ 동영상으로 촬영. 이 사전 학습된 지식 위에 "낙상인지 아닌지"만 추가 학습. HRNet은 COCO 17 keypoint 사용 → YOLO Pose의 17 keypoint와 호환

2. **구조 Fine-tuned**:
   - `data_bn` (Batch Normalization): 17 관절 × 3채널(x, y, conf) = 51개 값을 안정적 범위로 조정
   - `layers`: 9개 GCN+TCN 블록. GCN은 관절 간 공간적 관계(어깨↔팔꿈치), TCN은 시간적 변화(60프레임 동안 자세 변화)를 학습
   - `3-partition`: 골격 그래프 인접 행렬을 self-loop / inward / outward로 분리. "팔이 몸쪽으로 오는 움직임"과 "바깥으로 가는 움직임"을 구분하여 학습

3. **차등 LR**:
   - FC = 1e-3: 마지막 분류층. 60개 → 2개 클래스로 교체 → 처음부터 새로 학습 (빠르게)
   - Backbone = 1e-4: 9개 GCN+TCN 블록. 기존 지식 파괴 방지하면서 미세 조정 (천천히)
   - FC는 Backbone보다 **10배 빠르게** 학습

4. **Class weight**: Normal 1,423 vs Fallen 617 불균형(2.31:1). Fallen에 2.31배 가중치 → 소수 클래스 학습 강화

5. **Early stopping**: 15 epoch 동안 개선 없으면 중단. 실제 Best epoch 6, 중단 epoch 21 (6+15=21)

### 5-4. 학습 결과

| 지표 | 기존 (174샘플) | v2 (2,040샘플) |
|---|---|---|
| Accuracy | 91.89% | **99.63%** |
| F1 | — | 99.40% |
| Precision | — | 99.40% |
| Recall | — | 99.40% |
| AUC | — | 99.98% |

**Confusion Matrix** (Test 534 시퀀스):
```
TN=365  FP=1
FN=1    TP=167
```

Best Epoch 6, Early stopping at 21 (45초 완료)

---

## 6. 종합 성능 비교

| 항목 | Random Forest | ST-GCN (Fine-tuned) |
|---|---|---|
| **Accuracy** | 97.99% | **99.63%** |
| **Precision** | 0.9466 | **0.9940** |
| **Recall** | 0.9430 | **0.9940** |
| **F1-Score** | 0.9448 | **0.9940** |
| **AUC** | 0.9971 | **0.9998** |
| **Inference Time** | **0.01 ms** | 0.34 ms |
| **Model Size** | 43.96 MB | **29.77 MB** |
| Parameters | 200 trees, 181 features | 2.59M |
| Test Samples | 28,611 | 534 |

---

## 7. 상세 Classification Report

### Random Forest

```
              precision    recall  f1-score   support

      Normal       0.99      0.99      0.99     23403
        Fall       0.95      0.94      0.94      5208

    accuracy                           0.98     28611
   macro avg       0.97      0.97      0.97     28611
weighted avg       0.98      0.98      0.98     28611
```

### ST-GCN (Fine-tuned)

```
              precision    recall  f1-score   support

      Normal       1.00      1.00      1.00       366
        Fall       0.99      0.99      0.99       168

    accuracy                           1.00       534
   macro avg       1.00      1.00      1.00       534
weighted avg       1.00      1.00      1.00       534
```

---

## 8. Confusion Matrix

### Random Forest (n=28,611)

|  | Pred: Normal | Pred: Fall |
|---|---|---|
| Actual: Normal | 23,126 (TN) | 277 (FP) |
| Actual: Fall | 297 (FN) | 4,911 (TP) |

### ST-GCN Fine-tuned (n=534)

|  | Pred: Normal | Pred: Fall |
|---|---|---|
| Actual: Normal | 365 (TN) | 1 (FP) |
| Actual: Fall | 1 (FN) | 167 (TP) |

---

## 9. 분석 결론

- **최고 정확도**: ST-GCN (Fine-tuned) — 99.63%
- **최고 F1-Score**: ST-GCN (Fine-tuned) — 0.9940
- **최고 Recall (낙상 감지율)**: ST-GCN (Fine-tuned) — 0.9940
- **최고 속도**: Random Forest — 0.01 ms

예상대로 학습 데이터를 더 보강한 결과, **ST-GCN(Fine-tuned) 모델이 RF 모델보다 전반적인 성능 수치가 높게** 나옴.
실시간 영상 추론 성능도 이와 유사하게 개선될지 테스트 필요.

---

## 10. 권장 사용 시나리오

| 시나리오 | 권장 모델 | 이유 |
|---|---|---|
| 실시간 빠른 응답 | **Random Forest** | 최소 지연시간 (0.01 ms) |
| 최고 정확도 우선 | **ST-GCN (Fine-tuned)** | 최고 정확도 (99.63%) |
| 낙상 놓침 최소화 | **ST-GCN (Fine-tuned)** | 최고 Recall (0.9940) |
| 균형 잡힌 선택 | **ST-GCN (Fine-tuned)** | 최고 F1-Score (0.9940) |
