# ST-GCN 낙상 감지 시스템 개발 프로젝트 보고서

**프로젝트 기간**: 2026-02-03  
**작성자**: Stephen Kong  
**목적**: Random Forest 대비 ST-GCN의 성능 향상 가능성 검증

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [Phase 1: 3-Class ST-GCN 구현](#phase-1-3-class-st-gcn-구현)
3. [Phase 2: 데이터 증강 시도](#phase-2-데이터-증강-시도)
4. [Phase 3: Binary Classification 재설계](#phase-3-binary-classification-재설계)
5. [최종 결과 및 결론](#최종-결과-및-결론)
6. [교훈 및 향후 계획](#교훈-및-향후-계획)

---

## 프로젝트 개요

### 배경

**Home Safe Solution**은 Random Forest 기반 낙상 감지 시스템으로 **93.19%의 정확도**를 달성했습니다.

```
Random Forest 성능 (현재 운영 중):
- 전체 정확도: 93.19%
- Normal:  98.5%
- Falling: 76.6%
- Fallen:  92.1%

데이터:
- 70개 비디오 (10,420 프레임)
- 181개 특징 (정적 68 + 동적 113)
```

### 목표

**ST-GCN (Spatial Temporal Graph Convolutional Network)**을 도입하여:
1. Falling(낙상 중) 감지율 향상 (76.6% → 85%+)
2. End-to-end 학습으로 특징 자동 추출
3. 시간적 패턴 학습 강화

### 프로젝트 구조

```
/home/gjkong/dev_ws/st_gcn/
├── data/
│   ├── processed/       # 3-Class 데이터
│   ├── augmented/       # 증강 데이터 (강함)
│   ├── augmented_moderate/ # 증강 데이터 (중간)
│   └── binary/          # Binary 데이터
├── skeleton_integrated/
│   ├── fall/            # 낙상 skeleton (30개)
│   └── normal/          # 정상 skeleton (40개)
├── models/
│   ├── graph.py         # COCO 17 skeleton graph
│   └── st_gcn.py        # ST-GCN 모델 (2.5M params)
├── scripts/
│   ├── 01_prepare_data.py
│   ├── 02_split_data.py
│   ├── 03_train.py
│   ├── 04_evaluate.py
│   ├── 06_augment_data.py
│   ├── 07_train_augmented.py
│   ├── 08_augment_moderate.py
│   ├── 09_train_moderate.py
│   ├── 10_reorganize_data.py
│   ├── 11_create_binary_dataset.py
│   ├── 12_train_binary.py
│   └── 13_evaluate_binary.py
└── checkpoints/
    ├── best_model.pth
    ├── best_model_augmented.pth
    ├── best_model_moderate.pth
    └── best_model_binary.pth
```

---

## Phase 1: 3-Class ST-GCN 구현

### 1.1 데이터 준비

**원본 데이터 분석:**
```
70개 비디오:
- 평균 길이: 148.9 프레임 (7.4초 @ 20 FPS)
- 총 프레임: 10,420

클래스 분포:
- Normal:  5,906 (56.7%)
- Falling: 1,708 (16.4%)
- Fallen:  2,806 (26.9%)
```

**시퀀스 생성:**
```python
시퀀스 길이: 60 프레임 (3초)
Stride: 30 프레임 (1.5초)

결과:
- 70개 비디오 → 249개 시퀀스
- Shape: (249, 3, 60, 17, 1)
  * 3: 채널 (x, y, confidence)
  * 60: 시간 프레임
  * 17: COCO keypoints
  * 1: 1명
```

**데이터 분할:**
```
Train: 174 시퀀스 (70%)
  - Normal:  104 (59.8%)
  - Falling:  27 (15.5%)
  - Fallen:   43 (24.7%)

Val: 37 시퀀스 (15%)
  - Normal:  22
  - Falling:  6
  - Fallen:   9

Test: 38 시퀀스 (15%)
  - Normal:  23
  - Falling:  5
  - Fallen:  10
```

### 1.2 ST-GCN 모델 구현

**아키텍처:**
```python
ST-GCN 구조:
- 입력: (N, 3, 60, 17, 1)
- 9개 ST-GCN 레이어
  * Layer 1-3: 64 채널
  * Layer 4-6: 128 채널
  * Layer 7-9: 256 채널
- Global Average Pooling
- FC Layer: 256 → 3 (Normal/Falling/Fallen)

파라미터 수: 2,586,563개
```

**학습 설정:**
```python
Optimizer: Adam
  - Learning rate: 0.001
  - Weight decay: 0.0001

Loss: CrossEntropyLoss
  - Class weights: [1.0, 2.5, 1.0]  # Falling 강조

Scheduler: ReduceLROnPlateau
  - Patience: 10
  - Factor: 0.5

Early Stopping: Patience 20
Batch size: 16
```

### 1.3 학습 결과 (원본 데이터)

**학습 과정:**
```
총 24 epochs (Early stopping)
Best epoch: 3
Best Val Acc: 81.08%
```

**Validation Set 성능 (Epoch 3):**
```
전체 정확도: 81.08%

클래스별:
- Normal:  90.91% ✅
- Falling: 33.33% ❌ (매우 낮음!)
- Fallen:  66.67%
```

**Test Set 성능:**
```
전체 정확도: 84.21%

클래스별:
- Normal:  95.65% (22/23)
- Falling: 40.00% (2/5) ❌
- Fallen:  80.00% (8/10)

Confusion Matrix:
              Predicted
           Normal  Falling  Fallen
Normal        22        0       1
Falling        3        2       0
Fallen         2        0       8
```

**Random Forest와 비교:**

| Metric  | Random Forest | ST-GCN | Diff    |
|---------|---------------|--------|---------|
| Overall | 93.19%        | 84.21% | -8.98%  |
| Normal  | 98.5%         | 95.65% | -2.85%  |
| Falling | 76.6%         | 40.00% | -36.6% ❌ |
| Fallen  | 92.1%         | 80.00% | -12.1%  |

**Phase 1 결론:**
- ❌ ST-GCN이 Random Forest보다 낮은 성능
- ❌ 특히 Falling 감지율 급격히 하락 (76.6% → 40%)
- ⚠️ 원인: 데이터 부족 (249 시퀀스, Falling 27개)

---

## Phase 2: 데이터 증강 시도

데이터 부족 문제를 해결하기 위해 데이터 증강을 시도했습니다.

### 2.1 증강 전략 (강한 증강)

**증강 기법:**
```python
1. 시간 축 증강:
   - Time warp (0.7x, 0.8x, 0.9x, 1.1x, 1.2x, 1.3x)

2. 공간 축 증강:
   - Spatial flip (좌우 반전)
   - Scale (0.9x, 1.1x)

3. 노이즈:
   - Gaussian noise (σ=0.01)

4. 복합 증강:
   - Time warp + Noise
   - Flip + Noise
   - Scale + Time warp
```

**증강 비율:**
```
Normal:  104 → 312 (3배)
Falling:  27 → 270 (10배) ⭐
Fallen:   43 → 129 (3배)

총: 174 → 711 (4.1배)
```

### 2.2 증강 데이터 학습 결과

**학습 과정:**
```
총 23 epochs (Early stopping)
Best epoch: 2
Best Val Acc: 64.86%
```

**Validation Set 성능:**
```
전체 정확도: 64.86% ❌ (-16.22%!)

클래스별:
- Normal:  27-68% (불안정)
- Falling: 83-100%
- Fallen:  22-55% (불안정)
```

**문제점:**
- ❌ 심각한 과적합 발생
- ❌ Val 성능이 원본보다 오히려 하락 (81.08% → 64.86%)
- ❌ 학습 불안정 (에폭마다 성능 급변)

### 2.3 증강 전략 수정 (중간 강도)

**수정된 증강 비율:**
```
Normal:  104 → 208 (2배)
Falling:  27 → 135 (5배) ⭐ (10배 → 5배로 감소)
Fallen:   43 → 86 (2배)

총: 174 → 429 (2.5배)
```

**증강 기법 단순화:**
```python
1. Spatial flip (좌우 반전)
2. Gaussian noise (약하게, σ=0.005)
3. Scale (약하게, 0.95x, 1.05x)
4. Flip + Noise 조합

시간 축 워핑 제거 (부자연스러움)
```

### 2.4 중간 강도 증강 학습 결과

**학습 과정:**
```
총 48 epochs (Early stopping)
Best epoch: 27
Best Val Acc: 75.68%
```

**Validation Set 성능:**
```
전체 정확도: 75.68% ❌ (여전히 원본 81.08%보다 낮음)

클래스별:
- Normal:  100.00%
- Falling:  33.33% ❌
- Fallen:   44.44%
```

**Phase 2 결론:**
- ❌ 증강이 오히려 성능 저하
  * 원본: 81.08%
  * 강한 증강: 64.86%
  * 중간 증강: 75.68%
- ❌ 증강 데이터의 품질 문제
  * 시간 워핑이 부자연스러운 패턴 생성
  * 모델이 증강 패턴만 학습 (과적합)
- ⚠️ 근본 원인: 데이터 절대량 부족 (증강으로 해결 불가)

---

## Phase 3: Binary Classification 재설계

3-Class 문제의 어려움을 인식하고 **Binary Classification**으로 문제를 단순화했습니다.

### 3.1 데이터 재정의

**핵심 통찰:**
```
기존 데이터 분석 결과:
- 70개 비디오 모두 낙상 시나리오
- "Normal" 시퀀스 = 낙상 직전 상태 (진짜 정상 X)
- 순수 정상 활동 데이터 0개!

문제점:
→ 모델이 "안전한 정상"을 학습하지 못함
→ "낙상 직전"과 "실제 낙상"의 구분 어려움
```

**데이터 재분류:**
```
비디오 레벨 분류:
- Fall (낙상):   fall-01 ~ fall-30 (30개)
- Normal (정상): fall-31 ~ fall-70 (40개)

파일 구조:
/home/gjkong/dev_ws/st_gcn/
├── skeleton_integrated/
│   ├── fall/    (30개 비디오, 2,870 프레임)
│   └── normal/  (40개 비디오, 7,550 프레임)
```

### 3.2 Binary 데이터셋 생성

**시퀀스 추출:**
```
설정:
- 시퀀스 길이: 60 프레임
- Stride: 30 프레임

결과:
총 249 시퀀스
- Normal: 196 (78.7%)
- Fall:    53 (21.3%)

분할:
- Train: 174 (Normal 137, Fall 37)
- Val:    37 (Normal 29, Fall 8)
- Test:   38 (Normal 30, Fall 8)

클래스 불균형: 약 4:1 (Normal:Fall)
```

### 3.3 Binary ST-GCN 모델

**모델 수정:**
```python
ST-GCN 구조:
- num_class: 2 (Normal vs Fall)
- 나머지 동일 (2.5M params)

Loss:
- CrossEntropyLoss
- Class weights: [1.0, 3.5]  # Fall에 3.5배 가중치

Batch size: 16
기타 설정 동일
```

### 3.4 Binary 학습 결과

**학습 과정:**
```
총 33 epochs (Early stopping)
Best epoch: 12
Best Val Acc: 91.89% ✅ (큰 개선!)
```

**Validation Set 성능:**
```
전체 정확도: 91.89% ✅

클래스별:
- Normal: 89.66%
- Fall:   100.00% ✅ (완벽!)

Fall 검출:
- Precision: 72.73%
- Recall:    100.00% ✅
- F1 Score:  84.21%

특징:
✅ 모든 낙상을 감지 (False Negative = 0)
⚠️ 일부 정상을 낙상으로 오판 (False Positive 존재)
```

### 3.5 Test Set 최종 평가

**Test Set 성능:**
```
전체 정확도: 63.16% ❌ (Val 대비 -28.73%!)

클래스별:
- Normal: 60.00% (18/30) - 12개를 Fall로 오판
- Fall:   75.00% (6/8)   - 2개를 Normal로 오판

Confusion Matrix:
              Predicted
           Normal  Fall
Normal        18     12
Fall           2      6

Fall 검출:
- Precision: 33.33% ❌
- Recall:    75.00%
- F1 Score:  46.15%
```

**문제점 분석:**
```
1. 심각한 Overfitting
   - Val: 91.89% vs Test: 63.16%
   - 약 30% 차이!

2. 데이터 양 절대 부족
   - Test Fall 8개 (너무 적음)
   - 2개만 틀려도 75%

3. Val/Test 분포 차이
   - Val에서는 잘 맞췄지만 Test에서 실패
   - 일반화 능력 부족
```

**Phase 3 결론:**
- ✅ Binary로 단순화하여 Val 성능 향상 (81.08% → 91.89%)
- ❌ Test 성능은 오히려 하락 (84.21% → 63.16%)
- ❌ 근본 원인: 데이터 절대량 부족 (249 시퀀스)
  * ST-GCN 권장: 500-1000 시퀀스
  * 현재: 249 시퀀스 (약 1/2 ~ 1/4)

---

## 최종 결과 및 결론

### 전체 실험 결과 비교

| Model | Dataset | Val Acc | Test Acc | Normal | Fall/Falling | Fallen |
|-------|---------|---------|----------|--------|--------------|--------|
| **Random Forest** | 70 videos | - | **93.19%** | 98.5% | 76.6% | 92.1% |
| ST-GCN (3-Class) | 249 seq | 81.08% | 84.21% | 95.65% | 40.00% | 80.00% |
| ST-GCN (강한 증강) | 711 seq | 64.86% | - | 27-68% | 83-100% | 22-55% |
| ST-GCN (중간 증강) | 429 seq | 75.68% | - | 100% | 33.33% | 44.44% |
| ST-GCN (Binary) | 249 seq | 91.89% | **63.16%** | 60.00% | 75.00% | - |

### 핵심 발견사항

**1. 데이터 양이 가장 중요**
```
ST-GCN 요구사항:
- 권장: 500-1000 시퀀스 (200-400 비디오)
- 현재: 249 시퀀스 (70 비디오)
- 부족: 약 50-75%

결과:
→ 데이터 부족으로 인한 과적합
→ Val과 Test 성능 차이 큼
→ 일반화 능력 부족
```

**2. 데이터 증강의 한계**
```
증강은 "새로운 정보"를 추가하지 못함:
- Flip, Noise, Scale: 단순 변형
- 실제 낙상의 다양성 표현 불가
- 모델이 증강 패턴을 외워버림

결과:
→ 증강이 오히려 성능 저하
→ 부자연스러운 패턴 생성
→ 근본 해결책 아님
```

**3. Random Forest의 강점**
```
적은 데이터에 강함:
- 181개 특징 직접 설계 (도메인 지식 활용)
- Decision Tree 앙상블 (Overfitting 방지)
- 데이터 효율적

결과:
→ 70개 비디오로 93.19% 달성
→ 안정적이고 일관된 성능
→ Train/Val/Test 성능 일관성
```

**4. ST-GCN의 요구사항**
```
Deep Learning 특성:
- End-to-end 학습 (특징 자동 추출)
- 많은 데이터 필요 (파라미터 2.5M개)
- 시간적 패턴 학습 (복잡한 구조)

결과:
→ 데이터가 충분할 때만 효과적
→ 현재 데이터로는 부족
→ 과적합 발생
```

### 최종 결론

**✅ Random Forest 계속 사용 (권장)**

```python
선택 이유:
1. 성능: 93.19% (가장 높음, 안정적)
2. 신뢰성: Train/Val/Test 일관성
3. 효율성: 빠른 추론 (<10ms)
4. 실용성: 현재 GUI와 완벽 통합
5. 유지보수: 간단한 구조

현재 시스템:
- 위치: /home/gjkong/dev_ws/yolo/myproj
- 상태: 정상 운영 중
- 변경: 없음 (무중단 유지)
```

**📦 ST-GCN 프로젝트 보관**

```python
위치: /home/gjkong/dev_ws/st_gcn
상태: 완전한 구현 (Binary까지)
용도: 
  - 향후 데이터 200개+ 확보 시 재학습
  - 연구 참고 자료
  - 다른 프로젝트 적용
  
보관 파일:
  - 모델: models/st_gcn.py, models/graph.py
  - 스크립트: scripts/*.py (13개)
  - 체크포인트: checkpoints/*.pth (4개)
  - 데이터: data/*, skeleton_integrated/*
```

---

## 교훈 및 향후 계획

### 주요 교훈

**1. 문제 선택의 중요성**
```
✅ Random Forest: 적은 데이터에 적합
   - 특징 직접 설계
   - 도메인 지식 활용
   - Overfitting 방지

❌ ST-GCN: 많은 데이터 필요
   - End-to-end 학습
   - 특징 자동 추출
   - 데이터 부족 시 실패
```

**2. 데이터 품질 > 데이터 증강**
```
증강의 한계:
- 단순 변형만 가능
- 새로운 패턴 생성 불가
- 부자연스러운 데이터 생성

해결책:
→ 실제 데이터 수집 (200-400 비디오)
→ 다양한 시나리오 촬영
→ 순수 정상 활동 추가
```

**3. Val/Test 분할의 중요성**
```
문제:
- Val: 91.89%
- Test: 63.16%
- 차이: 28.73%!

원인:
- 데이터 양 부족
- Val/Test 분포 차이
- 과적합

교훈:
→ 충분한 데이터 확보
→ Stratified 분할
→ Cross-validation
```

**4. 실용성 우선**
```
ST-GCN vs Random Forest:
- ST-GCN: 최신 기술, 논문 발표
- Random Forest: 검증된 기술, 안정적

선택:
→ 실용성 > 최신성
→ 안정성 > 복잡성
→ 현재 문제에 최적화
```

### 향후 개선 방안

**단기 (1-3개월): Random Forest 최적화**
```
1. 하이퍼파라미터 튜닝
   - Grid search
   - Random search
   - Bayesian optimization

2. 특징 추가
   - 관절 가속도 (jerk)
   - 무게 중심 이동
   - 각속도

3. 앙상블 개선
   - XGBoost, LightGBM 테스트
   - Stacking
   - Voting

목표: 93.19% → 95%+
```

**중기 (3-6개월): 데이터 확보**
```
1. 순수 정상 활동 비디오 100개
   - 일상 이동 (50개)
   - 가사 활동 (30개)
   - 휴식 활동 (20개)

2. 다양한 낙상 시나리오 50개
   - 느린 낙상 (20개)
   - 빠른 낙상 (15개)
   - 다양한 방향 (15개)

3. 경계 케이스 30개
   - 빠르게 앉기
   - 바닥 활동
   - 불안정한 자세

목표: 70 → 250 비디오
```

**장기 (6-12개월): ST-GCN 재도전**
```
전제 조건:
- 데이터 250개 이상 확보
- 시퀀스 800-1000개
- Falling 300개 이상

개선 사항:
1. 모델 경량화
   - 파라미터 감소 (2.5M → 1M)
   - Depth 조정

2. 학습 전략
   - Transfer learning
   - Pre-training
   - Multi-task learning

3. 정규화 강화
   - Dropout
   - Batch normalization
   - Label smoothing

목표: 90-93% (Random Forest 수준)
```

### 데이터 수집 가이드

**Priority 1: 순수 정상 활동 (100개)** ⭐⭐⭐⭐⭐
```
시나리오:
1. 일상 이동 (50개)
   - 걷기, 앉기, 서기
   - 다양한 속도

2. 가사 활동 (30개)
   - 요리, 청소, 정리

3. 활동적 동작 (10개)
   - 물건 줍기, 운동

4. 휴식 활동 (10개)
   - TV, 책, 침대

촬영 가이드:
- 길이: 15-30초
- 낙상 없음!
- 다양한 각도/조명
```

**Priority 2: 다양한 낙상 (50개)** ⭐⭐⭐
```
시나리오:
1. 느린 낙상 (20개)
   - Falling 구간 3-6초

2. 빠른 낙상 (15개)
   - 다양한 각도

3. 경계 케이스 (15개)
   - 빠른 앉기
   - 바닥 활동

촬영 가이드:
- Normal: 5-10초
- Falling: 3-6초 (현재 1.5초 → 2-4배!)
- Fallen: 5-10초
```

---

## 부록

### A. 프로젝트 파일 목록

```
/home/gjkong/dev_ws/st_gcn/
├── models/
│   ├── graph.py (123 lines)
│   └── st_gcn.py (285 lines)
├── scripts/
│   ├── 01_prepare_data.py (270 lines)
│   ├── 02_split_data.py (150 lines)
│   ├── 03_train.py (320 lines)
│   ├── 04_evaluate.py (240 lines)
│   ├── 06_augment_data.py (450 lines)
│   ├── 07_train_augmented.py (320 lines)
│   ├── 08_augment_moderate.py (380 lines)
│   ├── 09_train_moderate.py (320 lines)
│   ├── 10_reorganize_data.py (180 lines)
│   ├── 11_create_binary_dataset.py (280 lines)
│   ├── 12_train_binary.py (340 lines)
│   └── 13_evaluate_binary.py (260 lines)
└── checkpoints/
    ├── best_model.pth (10.4 MB)
    ├── best_model_augmented.pth (10.4 MB)
    ├── best_model_moderate.pth (10.4 MB)
    ├── best_model_binary.pth (10.4 MB)
    ├── history.json
    ├── history_augmented.json
    ├── history_moderate.json
    └── history_binary.json

총 라인 수: ~3,900 lines
```

### B. 실험 타임라인

```
2026-02-03:

09:00-12:00: Phase 1 - 3-Class ST-GCN 구현
  - 데이터 준비
  - 모델 구현
  - 학습 (24 epochs)
  - 평가 (Test 84.21%)

13:00-15:00: Phase 2 - 데이터 증강 (강함)
  - 증강 스크립트 작성
  - 증강 실행 (711 시퀀스)
  - 학습 (23 epochs)
  - 결과: Val 64.86% (실패)

15:00-17:00: Phase 2 - 데이터 증강 (중간)
  - 증강 전략 수정
  - 증강 실행 (429 시퀀스)
  - 학습 (48 epochs)
  - 결과: Val 75.68% (여전히 낮음)

18:00-21:00: Phase 3 - Binary Classification
  - 데이터 재정의
  - Binary 데이터셋 생성
  - Binary 모델 학습 (33 epochs)
  - 결과: Val 91.89% (성공!)
  - Test 평가: 63.16% (실패)

21:00-22:00: 결과 분석 및 문서화
  - 전체 실험 정리
  - 최종 결론 도출
  - 보고서 작성

총 소요 시간: 약 13시간
```

### C. 참고 문헌

1. **ST-GCN 원본 논문**
   - Yan, S., Xiong, Y., & Lin, D. (2018). Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition. AAAI.

2. **Random Forest**
   - Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5-32.

3. **YOLO Pose**
   - Ultralytics YOLO Documentation: https://docs.ultralytics.com/

4. **데이터 증강**
   - Shorten, C., & Khoshgoftaar, T. M. (2019). A survey on Image Data Augmentation for Deep Learning. Journal of Big Data, 6(1), 60.

---

## 마무리

이 프로젝트를 통해 **ST-GCN**은 충분한 데이터가 있을 때 강력하지만, 현재와 같이 데이터가 부족한 상황에서는 **Random Forest**가 더 실용적임을 확인했습니다.

**핵심 메시지:**
- ✅ 문제에 맞는 적절한 알고리즘 선택의 중요성
- ✅ 데이터 품질과 양의 중요성
- ✅ 실용성과 안정성 우선
- ✅ 실험 기록과 문서화의 가치

**감사합니다!** 🙏

---

*작성일: 2026-02-03*  
*작성자: Stephen Kong*  
*프로젝트: Home Safe Solution*
