---
title: "📋 Work Log — 2026-02-07 (Final)"
date: 2026-03-21
draft: true
tags: ["dev-tools", "pyqt6"]
categories: ["dev-tools"]
description: "- GUI 실시간 모니터링 시 10초 후 크래시 원인 조사 및 해결 - RF 모델 GUI 통합 (binary 모델 적용) - DB 저장 에러 수정"
---

# 📋 Work Log — 2026-02-07 (Final)

## 프로젝트: Home Safe Solution - 낙상 감지 시스템

---

## 🎯 오늘의 목표

- GUI 실시간 모니터링 시 10초 후 크래시 원인 조사 및 해결
- RF 모델 GUI 통합 (binary 모델 적용)
- DB 저장 에러 수정
- RF 탐지 성능 개선 (신규 데이터 학습 + 좌표 정규화)

---

## ✅ 완료 작업

### 1. GUI 크래시 원인 조사 (체계적 단계별 테스트)

카메라 + YOLO + RF + GUI 조합에서 10초 후 크래시 발생. 원본에서도 동일 증상.

**단계별 테스트 결과:**

| 테스트 | 구성 | 결과 |
|--------|------|------|
| 카메라 단독 | cv2.VideoCapture | ✅ 72초+ 정상 |
| 카메라 + YOLO | CLI, GUI 없음 | ✅ 20초+ (26fps) |
| 카메라 + YOLO + RF | CLI, GUI 없음 | ✅ 20초+ (26.5fps) |
| PyQt6 + YOLO (간단 GUI) | QTimer + QLabel | ✅ 1분+ 정상 |
| monitoring_page: YOLO만 | skeleton 없음 | ✅ 1분+ 정상 |
| monitoring_page: + skeleton | RF 없음 | ✅ 30초+ 정상 |
| monitoring_page: + RF 추론 | UI 업데이트 없음 | ❌ 10초 크래시 |
| monitoring_page: + RF (n_jobs=1) | 스레드 제한 | ✅ 안정 동작 |

**근본 원인:** `RandomForestClassifier`의 `n_jobs=16`이 QTimer 메인루프 안에서 매 프레임 16개 스레드를 생성 → 메모리 누수(RSS 949MB→1721MB, 10초만에 800MB 증가) → OOM Killer가 프로세스 강제 종료

**해결:** `self.rf_model.n_jobs = 1` 설정

---

### 2. 3class 모델 손상 발견 및 binary 모델 적용

| 경로 | 상태 | features | classes |
|------|------|----------|---------|
| `models_integrated/3class/` | ❌ 손상 | 50개, 이름 없음 | [1] (class 1개) |
| `models_integrated/binary/` | ✅ 정상 | 181개, 이름 있음 | [0, 1] |

**조치:** binary 모델로 경로 변경, binary(2class) → 3class 형식 변환하여 기존 UI 호환 유지

---

### 3. RF 모델 실제 적용 (규칙 기반 → predict_proba)

**변경 전:** `predict_fall()`이 RF 모델을 전혀 사용하지 않고, hip_height/aspect_ratio 기반 하드코딩 규칙

**변경 후:** RF `predict_proba` 실제 사용, 3프레임마다 추론 (부하 경감)

---

### 4. 181개 Feature 전체 추출

**변경 전:** 2개 feature만 추출 → 나머지 179개 = 0 → 확률 바 고정

**변경 후:** 181개 전체 추출

| 그룹 | 개수 |
|------|------|
| Keypoint 좌표 (17 joint × x, y, conf) | 51 |
| 가속도 센서 (센서 없음→0) | 4 |
| 파생 Feature (각도, 높이, bbox 등) | 13 |
| 속도/가속도 (17 joint × 6) | 102 |
| 시계열 통계 (5프레임 윈도우) | 11 |

---

### 5. DB 에러 수정 (pool exhausted + numpy.float32)

- `save_event_to_db()` 중복 호출 제거 → `save_fall_event()`로 통합
- 모든 값 `float()` 변환 (numpy.float32 → python float)
- 저장 간격: Normal 10초, Fall 3초로 조정

---

### 6. RF 탐지 성능 개선 — 신규 데이터 + 정규화 + 대규모 데이터 증강

#### 6-1. 신규 데이터 전처리

| 폴더 | 파일 수 | 라벨 |
|------|---------|------|
| normal | 1,629개 (.avi, NTU RGB+D) | 0 (Normal) |
| falling → normal 통합 | 204개 (.avi) | 0 (Normal) |
| fallen (최종) | 301개 (.mp4, 자체촬영+추가수집) | 1 (Fallen) |

최종 데이터: Normal 116,854프레임 (1,629영상), Fallen 25,510프레임 (301영상)

#### 6-2. 데이터 누수(Data Leakage) 발견 및 해결

**v1:** 프레임 단위 random split → 같은 영상의 프레임이 train/test에 섞임 → 100% (가짜)

**v2:** 동영상 단위 split → 데이터 누수 제거

#### 6-3. 해상도 차이 문제 — 반전 감지 발생 ⭐

v2 모델 GUI 적용 결과: **서있기→Fallen, 쓰러짐→Normal** (정반대)

**원인:** NTU RGB+D(1080p)와 자체촬영(저해상도) 간 절대 좌표 차이

| Feature | Normal (NTU) | Fallen (자체촬영) |
|---------|-------------|-----------------|
| hip_height | **626** | **160** |
| bbox_height | **505** | **98** |

모델이 "좌표 큰 것 = Normal" 패턴 학습 → 실제 웹캠에서 반전

#### 6-4. 좌표 정규화 (v3) ⭐⭐

**해결:** bbox 기준 0~1 정규화

```python
norm_x = np.clip((x - bbox_x_min) / bbox_width, 0, 1)
norm_y = np.clip((y - bbox_y_min) / bbox_height, 0, 1)
```

정규화 후 해상도 차이가 제거되고 진짜 구분 feature가 드러남:

| Feature | Normal | Fallen | 구분 |
|---------|--------|--------|------|
| hip_height | 0.495 | 0.417 | 비슷 (해상도 무관) |
| bbox_aspect_ratio | 0.384 | **2.020** | ⭐ 핵심 구분 |
| spine_angle | 10.1° | **65.9°** | ⭐ 핵심 구분 |

#### 6-5. 정규화 버그 수정 (v3b)

**v3 문제:** conf < 0.3 keypoint 좌표(0,0)가 bbox 밖 → 정규화 시 큰 음수

**v3b 수정:**
- conf < 0.3 → 정규화 값 = 0
- `np.clip(0, 1)` 클램핑
- 속도/가속도: 양쪽 conf > 0.3일 때만 계산

#### 6-6. 성능 개선 추이 ⭐⭐⭐

| 단계 | Fallen 영상 | F1 | Recall | Precision | AUC | FN Rate |
|------|------------|-----|--------|-----------|-----|---------|
| v3 (30영상) | 30 | 74.0% | 63.7% | 88.4% | 99.1% | 36.3% |
| v3b (60영상) | 60 | 87.0% | 82.6% | 91.9% | 99.4% | 17.4% |
| **v3b (301영상)** | **301** | **94.5%** | **94.3%** | **94.7%** | **99.7%** | **5.7%** |

#### 6-7. 최종 전략 비교 (301영상, 정규화 v3b)

| 전략 | Acc | F1 | Prec | Recall | AUC | FP% | FN% |
|------|-----|-----|------|--------|-----|-----|-----|
| Balanced | 97.8% | 94.0% | 95.9% | 92.1% | 99.7% | 0.9% | 7.9% |
| Undersample 5:1 | 98.0% | 94.4% | 95.9% | 92.9% | 99.7% | 0.9% | 7.1% |
| **Undersample 3:1 + Bal** | **98.0%** | **94.5%** | **94.7%** | **94.3%** | **99.7%** | **1.2%** | **5.7%** |
| Hybrid 5:1 + Bal | 97.9% | 94.3% | 95.5% | 93.0% | 99.7% | 1.0% | 7.0% |

**최적 모델:** Undersample 3:1 + Bal (Recall 94.3%, F1 94.5%)

#### 6-8. 실제 GUI 테스트 결과

| 동작 | v2 (비정규화) | v3 (30영상) | v3b (60영상) | v3b (301영상) |
|------|-------------|------------|-------------|--------------|
| 서있기 | ❌ Fallen | ✅ Normal | ✅ Normal | ✅ Normal |
| 앉기 | ✅ Normal | ✅ Normal | ✅ Normal | ✅ Normal |
| 쓰러짐 | ❌ Normal | △ 50% 미만 | △ 65%+ | **✅ 매우 좋음** |

---

### 7. 모델 비교 스크립트 업데이트

`compare_models_report.py` 수정:

| 항목 | 기존 | 수정 |
|------|------|------|
| RF 모델 경로 | `models/binary/` | `models_integrated/binary_v3/` |
| 테스트 데이터 | `dataset/binary/test.csv` | `features_normalized/*.csv` (동영상 단위 split) |

3개 모델(RF, ST-GCN Original, ST-GCN Fine-tuned) 비교 리포트 정상 동작 확인

---

### 8. 성능 리포트 생성

`RF_v3b_Performance_Report.png` 생성:
- 주요 지표 카드 (Acc, F1, Prec, Rec, AUC, FN Rate)
- 4가지 전략 비교 바 차트
- FP vs FN 에러율 비교
- Confusion Matrix (최적 모델)
- 데이터 증가에 따른 성능 변화 추이 (30→60→301)
- FN Rate 감소 추이 (36.3% → 5.7%, −30.6%p)
- 전 단계 성능 요약 테이블

---

## 📁 파일 구조

### 모델 백업

| 경로 | 내용 |
|------|------|
| `models_integrated/binary_backup_20260207/` | 원본 binary 모델 백업 |
| `models_integrated/binary_v2/` | 비정규화 재학습 모델 |
| `models_integrated/binary_v3/random_forest_model.pkl` | **현재 적용 모델** (정규화, Under 3:1+Bal) |
| `models_integrated/binary_v3/random_forest_model_balanced_backup.pkl` | Balanced 모델 백업 (60영상) |

### 스크립트

| 파일 | 용도 |
|------|------|
| `preprocess_videos.py` | 동영상 → CSV 전처리 (v1, 절대좌표) |
| `train_rf_new.py` | RF 학습 v1 (프레임 split — 데이터 누수) |
| `train_rf_new_v2.py` | RF 학습 v2 (동영상 split) |
| `train_rf_v3_normalized.py` | 전처리+학습 v3 (정규화, 버그 있음) |
| `train_rf_v3b.py` | **전처리+학습 v3b (정규화 버그 수정)** ⭐ |
| `compare_models_report.py` | 3모델 비교 리포트 생성 (RF v3 경로 반영) |

### 데이터

| 경로 | 내용 |
|------|------|
| `new_data/normal/` | 1,629개 .avi (NTU RGB+D) |
| `new_data/fallen/` | 301개 .mp4 (자체촬영 + 추가수집) |
| `new_data/features_normalized/normal_features.csv` | 116,854행 (정규화) |
| `new_data/features_normalized/fallen_features.csv` | 25,510행 (정규화) |

### monitoring_page.py 변경점 (원본 대비)

1. 모델 경로: `binary_v3` + `n_jobs=1` + `verbose=0`
2. RF 추론: 3프레임마다, `predict_proba` 실제 사용
3. **extract_simple_features: bbox 기준 0~1 정규화 (v3b)** ⭐
4. predict_fall: binary→3class 변환
5. DB 저장: 중복 제거 + float() 변환 + 간격 조정
6. **Detection Accuracy 오버레이: Fallen 기준으로 변경** ⭐

---

### 9. Detection Accuracy 오버레이 — Fallen 기준으로 변경

**배경:** 영상 우측 상단 오버레이 박스의 Detection Accuracy가 Normal 기준(ground_truth='Normal')으로 측정되고 있었음. 낙상 감지 시스템이므로 **Fallen 감지 정확도**를 측정해야 함.

**변경 (monitoring_page.py, 2곳만 수정):**

| 줄 | 변경 전 | 변경 후 |
|-----|---------|---------|
| 404 | `set_ground_truth('Normal')` | `set_ground_truth('Fallen')` |
| 1678-1680 | `Detection Acc:` (폰트 0.5) | `FN Detection Acc:` (폰트 0.45) |

**목적:** 5분간 Fallen 감지 평균 정확도를 측정하여, 일정 기간 지속 시 다른 액션(알림 등)을 트리거하는 용도로 활용 예정.

---

### 10. 대시보드 페이지 — 탐지율 라벨 수정

**변경 (dashboard_page.py, 3곳):**

`정상 탐지율` → `낙상 탐지율` 텍스트 변경

---

## 📁 파일 구조

### 모델 백업

| 경로 | 내용 |
|------|------|
| `models_integrated/binary_backup_20260207/` | 원본 binary 모델 백업 |
| `models_integrated/binary_v2/` | 비정규화 재학습 모델 |
| `models_integrated/binary_v3/random_forest_model.pkl` | **현재 적용 모델** (정규화, Under 3:1+Bal) |
| `models_integrated/binary_v3/random_forest_model_balanced_backup.pkl` | Balanced 모델 백업 (60영상) |

### 스크립트

| 파일 | 용도 |
|------|------|
| `preprocess_videos.py` | 동영상 → CSV 전처리 (v1, 절대좌표) |
| `train_rf_new.py` | RF 학습 v1 (프레임 split — 데이터 누수) |
| `train_rf_new_v2.py` | RF 학습 v2 (동영상 split) |
| `train_rf_v3_normalized.py` | 전처리+학습 v3 (정규화, 버그 있음) |
| `train_rf_v3b.py` | **전처리+학습 v3b (정규화 버그 수정)** ⭐ |
| `compare_models_report.py` | 3모델 비교 리포트 생성 (RF v3 경로 반영) |

### 데이터

| 경로 | 내용 |
|------|------|
| `new_data/normal/` | 1,629개 .avi (NTU RGB+D) |
| `new_data/fallen/` | 301개 .mp4 (자체촬영 + 추가수집) |
| `new_data/features_normalized/normal_features.csv` | 116,854행 (정규화) |
| `new_data/features_normalized/fallen_features.csv` | 25,510행 (정규화) |

### 성능 리포트

| 파일 | 내용 |
|------|------|
| `RF_v3b_Performance_Report.png` | RF v3b 성능 대시보드 (전략 비교, 데이터 증가 추이 등) |

---

### 11. ST-GCN 대규모 데이터 변환 ⭐

**배경:** 기존 ST-GCN은 174샘플(Normal 137, Fall 37)로 학습 → 84.21%. RF와 동일 데이터로 재학습하여 공정 비교 필요.

**데이터 변환 파이프라인 (`prepare_stgcn_data.py`):**

1. RF 동영상(normal 1,629 + fallen 301)에서 YOLO Pose로 keypoint 추출
2. 60프레임 시퀀스, stride 30 (50% overlap)
3. 기존 ST-GCN과 동일 정규화 (hip center 기준, max distance → -1~1)
4. 동영상 단위 split (seed=42, 20%)

**결과:**

| 항목 | 기존 (binary) | 신규 (binary_v2) | 증가 |
|------|-------------|-----------------|------|
| Train | 174 샘플 | **2,040 샘플** | 11.7배 |
| Test | 38 샘플 | **534 샘플** | 14배 |
| Normal (Train) | 137 | 1,423 | |
| Fallen (Train) | 37 | 617 | |

**데이터 누수 검증:** 중복 시퀀스 1개, 중복 동영상 0개 ✅

---

### 12. ST-GCN PYSKL Pre-trained + Fine-tuning ⭐⭐

**학습 설정:**

| 항목 | 설정 |
|------|------|
| Pre-trained | PYSKL ST-GCN NTU60 HRNet (56,000+ 동영상) |
| 구조 | Fine-tuned (data_bn + layers + 3-partition) |
| 차등 LR | FC=1e-3, Backbone=1e-4 |
| Class weight | Normal=1.0, Fallen=2.31 |
| Early stopping | 15 epochs |

**학습 결과:**

| 지표 | 기존 (174샘플) | **v2 (2,040샘플)** |
|------|-------------|------------------|
| Accuracy | 91.89% | **99.63%** |
| F1 | — | **99.40%** |
| Precision | — | **99.40%** |
| Recall | — | **99.40%** |
| AUC | — | **99.98%** |

**Confusion Matrix (Test 534 시퀀스):**
```
TN=365  FP=1
FN=1    TP=167
```

Best Epoch 6, Early stopping at 21 (45초 완료)

---

### 13. 모델 비교 리포트 업데이트

**변경:** 3개 모델 → 2개 모델 비교 (RF + ST-GCN Fine-tuned v2)

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 비교 대상 | RF, ST-GCN Original, Fine-tuned | **RF, ST-GCN Fine-tuned v2** |
| ST-GCN 모델 경로 | `checkpoints_finetuned/` | `checkpoints_v2/` |
| ST-GCN 테스트 데이터 | `data/binary/` (38샘플) | `data/binary_v2/` (534샘플) |

**최종 비교 결과:**

| 지표 | 🌲 RF | 🚀 ST-GCN v2 |
|------|-------|-------------|
| **Accuracy** | 97.99% | **99.63%** |
| **F1** | 94.48% | **99.40%** |
| **AUC** | 99.71% | **99.98%** |
| **추론 속도** | **0.01ms** ⚡ | 0.34ms |
| **모델 크기** | 43.96MB | **29.77MB** |
| **테스트 단위** | 28,611 프레임 | 534 시퀀스 |

---

## 📁 파일 구조

### RF 모델

| 경로 | 내용 |
|------|------|
| `models_integrated/binary_backup_20260207/` | 원본 binary 모델 백업 |
| `models_integrated/binary_v2/` | 비정규화 재학습 모델 |
| `models_integrated/binary_v3/random_forest_model.pkl` | **현재 적용 RF 모델** (정규화, Under 3:1+Bal) |

### ST-GCN 모델

| 경로 | 내용 |
|------|------|
| `st_gcn/checkpoints/best_model_binary.pth` | Original (174샘플, 84.21%) |
| `st_gcn/checkpoints_finetuned/best_model_finetuned.pth` | Fine-tuned v1 (174샘플, 91.89%) |
| `st_gcn/checkpoints_v2/best_model.pth` | **Fine-tuned v2 (2,040샘플, 99.63%)** ⭐ |

### 스크립트

| 파일 | 용도 |
|------|------|
| `train_rf_v3b.py` | RF 전처리+학습 v3b (정규화 버그 수정) ⭐ |
| `st_gcn/scripts/prepare_stgcn_data.py` | 동영상 → ST-GCN npy 변환 (YOLO keypoint) |
| `st_gcn/scripts/02_finetune_stgcn_v2.py` | PYSKL Pre-trained Fine-tuning |
| `compare_models_report.py` | **2모델 비교 리포트 (RF + ST-GCN v2)** |

### GUI 파일 (수정)

| 파일 | 변경 내용 |
|------|----------|
| `gui/model_selection_dialog.py` | Original 제거, v2 경로/정확도 반영 |
| `gui/stgcn_inference_finetuned.py` | 모델 경로 v2, hip center 정규화 추가 |
| `gui/monitoring_page.py` | ST-GCN 경로 v2, 확률 바 softmax, accuracy_tracker Fallen, Normal DB 저장 |

### 데이터

| 경로 | 내용 |
|------|------|
| `new_data/normal/` | 1,629개 .avi (NTU RGB+D) — RF, ST-GCN 공용 |
| `new_data/fallen/` | 301개 .mp4 (자체촬영 + 추가수집) — RF, ST-GCN 공용 |
| `new_data/features_normalized/` | RF용 정규화 feature CSV |
| `st_gcn/data/binary_v2/` | ST-GCN용 npy (2,040 train + 534 test) |

---

### 14. GUI 모델 선택 다이얼로그 업데이트

**변경 (`model_selection_dialog.py`):**

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| 모델 목록 | RF, Original, Fine-tuned (3개) | **RF, Fine-tuned v2 (2개)** |
| RF 정확도 | 93.19% | **94.50%** |
| ST-GCN 이름 | Fine-tuned | **Fine-tuned v2** |
| ST-GCN 정확도 | 91.89% | **99.63%** |
| ST-GCN 경로 | `checkpoints_finetuned/` | `checkpoints_v2/` |

---

### 15. ST-GCN 추론 모듈 수정

**문제 1:** `stgcn_inference_finetuned.py` 모델 경로가 이전 버전
- `checkpoints_finetuned/best_model_finetuned.pth` → `checkpoints_v2/best_model.pth`

**문제 2:** `monitoring_page.py`의 `init_stgcn_model()`에서 하드코딩된 이전 경로
- `checkpoints/best_model_binary.pth` → `checkpoints_v2/best_model.pth`

**문제 3:** `set_frame_size` 메서드 미존재 에러 → 주석 처리

---

### 16. ST-GCN 실시간 추론 정규화 수정 ⭐

**핵심 문제:** 학습 시 hip center 정규화(-1~1)를 적용했으나, 실시간 추론 시 YOLO 원본 픽셀 좌표를 그대로 사용 → 항상 Fall 100%로 예측

**수정 (`stgcn_inference_finetuned.py` preprocess):**
```python
# Hip center 정규화 (학습과 동일)
hip_center = (sequence[:2, :, 11] + sequence[:2, :, 12]) / 2
sequence[:2, :, :] -= hip_center[:, :, np.newaxis]
max_dist = np.abs(sequence[:2, :, :]).max()
if max_dist > 0:
    sequence[:2, :, :] /= max_dist
```

**교훈:** 학습↔추론 시 전처리(정규화)는 반드시 동일해야 함. 정규화 불일치는 모델 성능 완전 붕괴의 원인.

---

### 17. ST-GCN UI 연동 수정

**수정 사항:**

| 문제 | 원인 | 수정 |
|------|------|------|
| FN Detection Acc 항상 0% | `record_prediction('Falling')` vs GT='Fallen' | → `'Fallen'`으로 변경 |
| 확률 바 미표시 | `update_stgcn_fall_info`에 바 업데이트 없음 | softmax(normal_prob, fall_prob) 직접 반영 |
| Normal시 DB 미저장 | else 블록에 DB 저장 없음 | `save_event_to_db('Normal', confidence)` 추가 |
| predict 반환값 | `(label, confidence)` 2개 | → `(label, confidence, normal_prob, fall_prob)` 4개 |

---

## 📊 현재 시스템 상태

| 항목 | 상태 |
|------|------|
| GUI 안정성 | ✅ 안정 동작 |
| RF 추론 | ✅ 실시간 (n_jobs=1, F1=94.5%) |
| ST-GCN v2 추론 | ✅ 실시간 GPU (Acc=99.63%) |
| 모델 선택 다이얼로그 | ✅ RF / ST-GCN v2 선택 |
| 서기 감지 | ✅ Normal (RF, ST-GCN 모두) |
| 앉기 감지 | ✅ Normal (RF, ST-GCN 모두) |
| 쓰러짐 감지 | ✅ Fall (RF, ST-GCN 모두) |
| 확률 바 표시 | ✅ softmax 확률 정상 반영 |
| FN Detection Acc | ✅ Fallen 기준 정상 동작 |
| DB 저장 | ✅ Normal/Fall 모두 정상 기록 |
| 대시보드 | ✅ 낙상 탐지율 표시 |
| 모델 비교 리포트 | ✅ RF vs ST-GCN v2 (2모델) |

---

## 📌 다음 작업

1. 추론 임계값 조정 검토 (50%→40% 등)
2. FN Detection Acc 기반 알림 트리거 구현
3. 장시간 안정성 테스트 (메모리 누수 확인)
4. ST-GCN + RF 앙상블 검토

---

## 💡 교훈

### sklearn n_jobs와 Qt 메인루프 충돌
QTimer 안에서 멀티스레드 sklearn 추론 시 메모리 누수. GUI 환경에서는 반드시 `n_jobs=1`.

### 체계적 단계별 테스트
구성 요소를 하나씩 추가하며 범인 좁히기. RSS 모니터링(`ps -o pid,rss`)으로 OOM 진단.

### 데이터 누수(Data Leakage) 방지
동영상 기반 데이터에서 프레임 단위 split은 누수 유발. 반드시 **동영상(그룹) 단위 split**.

### ⭐ 좌표 정규화의 중요성
서로 다른 해상도/카메라의 데이터를 혼합 학습할 때 **절대 좌표는 해상도 패턴을 학습**. bbox 기준 0~1 정규화로 해결:
- 해상도 무관 feature 생성
- 모델이 실제 자세 패턴(aspect_ratio, spine_angle)에 집중
- 학습↔실제 환경 간 일반화 성능 확보

### ⭐⭐ 학습↔추론 정규화 일치
학습 데이터에 hip center 정규화를 적용했으면, 추론 시에도 **반드시 동일한 정규화**를 적용해야 함. 불일치 시 모델이 완전히 다른 분포의 입력을 받아 예측이 무의미해짐. (100% Fall 오탐의 원인이었음)

### confidence 필터링
YOLO keypoint conf < 0.3인 점은 좌표가 부정확. 정규화/속도 계산에서 제외해야 feature 오염 방지.

### ⭐⭐ 데이터 양의 효과 — RF
데이터 추가가 모델 튜닝보다 압도적으로 효과적:

| 변경 | F1 변화 |
|------|---------|
| 30→60영상 (+100%) | 74% → 87% (**+13%p**) |
| 60→301영상 (+400%) | 87% → 94.5% (**+7.5%p**) |
| FN Rate | 36.3% → 5.7% (**−30.6%p**) |

### ⭐⭐ 데이터 양의 효과 — ST-GCN

| 변경 | Accuracy |
|------|----------|
| 174샘플 (Original) | 84.21% |
| 174샘플 (Fine-tuned v1) | 91.89% |
| **2,040샘플 (Fine-tuned v2)** | **99.63%** (+15.4%p) |

두 모델 모두 **동일 데이터 확대** 시 극적으로 성능 향상. 양질의 데이터 확보가 성능 개선의 핵심.
