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

---

## 📊 현재 시스템 상태

| 항목 | 상태 |
|------|------|
| GUI 안정성 | ✅ 2분+ 안정 동작 |
| RF 추론 | ✅ 실시간 (n_jobs=1) |
| 서기 감지 | ✅ Normal |
| 앉기 감지 | ✅ Normal |
| 쓰러짐 감지 | ✅ 매우 좋음 (F1=94.5%, Recall=94.3%) |
| Skeleton 표시 | ✅ 정상 |
| DB 저장 | ✅ 에러 없이 정상 |
| 대시보드 | ✅ DB 값 정상 노출 |

---

## 📌 다음 작업

1. ST-GCN 모델 실시간 통합 테스트
2. 이미지 370개 활용 검토 (시계열=0 문제 고려)
3. 추론 임계값 조정 검토 (50%→40% 등)
4. 모델 비교 리포트 자동화

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

### confidence 필터링
YOLO keypoint conf < 0.3인 점은 좌표가 부정확. 정규화/속도 계산에서 제외해야 feature 오염 방지.

### ⭐⭐ 데이터 양의 효과
데이터 추가가 모델 튜닝보다 압도적으로 효과적:

| 변경 | F1 변화 |
|------|---------|
| 30→60영상 (+100%) | 74% → 87% (**+13%p**) |
| 60→301영상 (+400%) | 87% → 94.5% (**+7.5%p**) |
| FN Rate | 36.3% → 5.7% (**−30.6%p**) |

모델 알고리즘이나 하이퍼파라미터 튜닝보다, **양질의 데이터 확보**가 성능 개선의 핵심.
