# 📋 Work Log — 2026-02-07

## 프로젝트: Home Safe Solution - 낙상 감지 시스템

---

## 🎯 오늘의 목표

- GUI 실시간 모니터링 시 10초 후 크래시 원인 조사 및 해결
- RF 모델 GUI 통합 (binary 모델 적용)
- DB 저장 에러 수정
- RF 탐지 성능 개선 (신규 데이터 학습)

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

**모델 상태 비교:**

| 경로 | 상태 | features | classes |
|------|------|----------|---------|
| `models_integrated/3class/` | ❌ 손상 | 50개, 이름 없음 | [1] (class 1개) |
| `models_integrated/binary/` | ✅ 정상 | 181개, 이름 있음 | [0, 1] |

**조치:** binary 모델로 경로 변경, binary(2class) → 3class 형식 변환하여 기존 UI 호환 유지

---

### 3. RF 모델 실제 적용 (규칙 기반 → predict_proba)

**변경 전:** `predict_fall()`이 RF 모델을 전혀 사용하지 않고, hip_height/aspect_ratio 기반 하드코딩 규칙으로 확률 반환

**변경 후:** RF `predict_proba` 실제 사용, 3프레임마다 추론 (부하 경감)

---

### 4. 181개 Feature 전체 추출

**변경 전:** `extract_simple_features()`가 2개 feature만 추출 (hip_height, aspect_ratio) → 나머지 179개 = 0 → 추론 결과 항상 동일 → 확률 바 고정

**변경 후:** 181개 feature 전체 추출

| 그룹 | Feature | 개수 |
|------|---------|------|
| Keypoint 좌표 | 17 joint × (x, y, conf) | 51 |
| 가속도 센서 | acc_x, y, z, mag (센서 없음→0) | 4 |
| 파생 Feature | 각도, 높이, bbox, tilt 등 | 13 |
| 속도/가속도 | 17 joint × (vx, vy, speed, ax, ay, accel) | 102 |
| 시계열 통계 | mean_5, std_5 등 (5프레임 윈도우) | 11 |

---

### 5. DB 에러 수정 (pool exhausted + numpy.float32)

**원인 1: 중복 DB 호출**
- `save_fall_event()`: Normal 5초, Fall 1초 간격
- `save_event_to_db()`: 30프레임(~1.5초)마다 → 매번 새 EventLog 인스턴스 생성

**원인 2: numpy.float32 타입**
- DB 드라이버가 numpy float 변환 불가

**해결:**
- `save_event_to_db()` 중복 호출 제거 → `save_fall_event()`로 통합
- 모든 값 `float()` 변환
- 저장 간격: Normal 10초, Fall 3초로 조정

---

### 6. RF 탐지 성능 개선 — 신규 데이터 학습

#### 6-1. 신규 데이터 전처리

동영상에서 YOLO keypoint 추출 → 181개 feature 계산 → CSV 저장

| 폴더 | 파일 수 | 형식 | 라벨 |
|------|---------|------|------|
| normal | 1629개 | .avi (NTU RGB+D) | 0 (Normal) |
| falling | 204개 → normal에 통합 | .avi (NTU RGB+D) | 0 (Normal) |
| fallen | 30개 | .mp4 (자체촬영) | 1 (Fallen) |

최종 데이터: Normal 116,854행, Fallen 2,870행 (불균형 비율 40.7:1)

전처리 도구: `preprocess_videos.py` → 약 20분 소요

#### 6-2. 데이터 누수(Data Leakage) 발견 및 해결

**v1 문제:** 프레임 단위 random split → 같은 동영상의 연속 프레임이 train/test에 섞임 → 모든 전략 100% 정확도 (가짜 성능)

**v2 해결:** 동영상 단위 train/test split (`GroupShuffleSplit` 개념) → 같은 영상의 프레임이 절대 train/test에 동시 존재하지 않음

#### 6-3. 해상도 차이 문제 발견 및 좌표 정규화 ⭐

**문제 발견:** v2 모델을 GUI에 적용한 결과, 서있기→Fallen, 쓰러짐→Normal로 **정반대 감지**

**근본 원인:** 학습 데이터 간 해상도 차이

| Feature | Normal (NTU RGB+D, 1080p) | Fallen (자체촬영, 저해상도) |
|---------|--------------------------|--------------------------|
| hip_height | **626** (높은 해상도 → 큰 값) | **160** (낮은 해상도 → 작은 값) |
| bbox_height | **505** | **98** |

모델이 **"좌표가 큰 것 = Normal, 작은 것 = Fallen"**으로 학습했기 때문에, 실제 웹캠(중간 해상도)에서 서있는 사람의 좌표값이 학습된 Fallen 범위에 해당하여 반전 동작 발생.

**해결: bbox 기준 좌표 정규화 (0~1)**

모든 keypoint 좌표를 사람의 bounding box 기준으로 0~1 범위로 정규화:

```python
norm_x = (x - bbox_x_min) / bbox_width   # 0~1
norm_y = (y - bbox_y_min) / bbox_height   # 0~1
```

정규화 후 해상도 차이가 제거됨:

| Feature | 정규화 전 (Normal/Fallen) | 정규화 후 (Normal/Fallen) |
|---------|-------------------------|-------------------------|
| hip_height | 626 / 160 (해상도 의존) | 0.526 / 0.553 (해상도 무관) |
| bbox_aspect_ratio | 절대 크기 영향 | 0.355 / 0.953 (순수 비율) |
| spine_angle | 변화 없음 | 5.5° / 27.3° (각도는 스케일 불변) |

**핵심 인사이트:**
- 정규화 후 Normal과 Fallen을 구분하는 진짜 feature가 드러남
  - `bbox_aspect_ratio`: 서있으면 세로가 길고(0.35), 쓰러지면 가로가 길어짐(0.95)
  - `spine_angle`: 서있으면 작고(5.5°), 쓰러지면 커짐(27.3°)
- 좌표 기반 feature(hip_height 등)은 정규화 후 구분력이 사라짐 → 모델이 자세 패턴에 집중

#### 6-4. 정규화 버그 수정 (v3 → v3b)

**v3 문제:** confidence가 낮은 keypoint(< 0.3)의 좌표가 0,0이라 bbox 밖에 위치 → 정규화 시 음수 발생 (`hip_height: -321, -3969`)

**v3b 수정:**
- conf < 0.3인 keypoint는 정규화 값 = 0으로 처리
- 모든 정규화 값을 `np.clip(0, 1)`로 클램핑
- 속도/가속도 계산 시 양쪽 keypoint 모두 conf > 0.3일 때만 계산
- 전처리 후 min/max 범위 자동 검증 출력

**v3b 정규화 범위 검증:**
```
hip_height:      min=0.363, max=0.747 ✅
head_height:     min=0.000, max=0.920 ✅
shoulder_height: min=0.000, max=0.997 ✅
nose_x:          min=0.000, max=1.000 ✅
```

#### 6-5. 학습 결과 (v3 전체 데이터, 정규화 적용)

| 전략 | Acc | F1 | Precision | Recall | AUC | FP% | FN% |
|------|-----|-----|-----------|--------|-----|-----|-----|
| Balanced (class_weight) | 99.0% | 73.9% | 79.5% | 69.1% | 99.2% | 0.4% | 30.9% |
| Undersample 5:1 | 98.9% | 75.4% | 71.7% | 79.6% | 99.5% | 0.7% | 20.4% |
| **Undersample 3:1 + Bal** | **98.7%** | **74.7%** | **63.4%** | **90.9%** | **99.5%** | **1.2%** | **9.1%** |
| Hybrid 5:1 + Bal | 98.8% | 74.4% | 67.0% | 83.7% | 99.4% | 0.9% | 16.3% |

**낙상 감지 시스템에서는 Recall이 가장 중요** (낙상을 놓치면 위험):
- **Undersample 3:1 + Bal**: Recall 90.9% (낙상 10건 중 9건 감지), 오탐지 1.2%

#### 6-6. 진행 중: v3b 전체 데이터 학습

정규화 버그 수정 후 전체 데이터로 재학습 진행 중 (~20분 소요)

---

## 📁 수정 파일 요약

### monitoring_page.py (원본 대비 변경점)

1. **모델 로드**: binary_v3 경로 + `n_jobs=1` + `verbose=0` + `feature_names_in_` 사용
2. **RF 추론 빈도**: 3프레임마다 1번
3. **extract_simple_features()**: 181개 전체 추출 (정규화 적용 시 GUI도 업데이트 필요)
4. **predict_fall()**: RF `predict_proba` + binary→3class 변환
5. **DB 저장**: 중복 제거 + `float()` 변환 + 간격 조정

### 신규 스크립트

| 파일 | 용도 |
|------|------|
| `preprocess_videos.py` | 동영상 → CSV 전처리 (v1, 절대좌표) |
| `train_rf_new.py` | RF 학습 v1 (프레임 split, 데이터 누수) |
| `train_rf_new_v2.py` | RF 학습 v2 (동영상 split) |
| `train_rf_v3_normalized.py` | 전처리+학습 v3 (정규화, 버그 있음) |
| `train_rf_v3b.py` | 전처리+학습 v3b (정규화 버그 수정) ⭐ |

---

## 📊 현재 시스템 상태

| 항목 | 상태 |
|------|------|
| GUI 안정성 | ✅ 2분+ 안정 동작 |
| RF 추론 | ✅ 실시간 동작 (n_jobs=1) |
| 확률 바 | ✅ 실시간 변동 |
| Skeleton 표시 | ✅ 정상 |
| DB 저장 | ✅ 에러 없이 정상 |
| 대시보드 | ✅ DB 값 정상 노출 |
| RF 모델 | ⏳ v3b 학습 진행 중 |

---

## 📌 다음 작업

1. **v3b 학습 결과 확인** 및 GUI 적용 테스트
2. **GUI extract_simple_features 정규화 적용** (v3 모델 사용 시 필수)
3. 실시간 서기/앉기/쓰러짐 테스트
4. ST-GCN 모델 실시간 통합 테스트

---

## 💡 교훈

### sklearn n_jobs와 Qt 메인루프 충돌
QTimer 안에서 멀티스레드 sklearn 추론 시 메모리 누수 발생. GUI 환경에서는 반드시 `n_jobs=1` 사용.

### 체계적 단계별 테스트
카메라→YOLO→RF→GUI를 하나씩 추가하며 범인을 좁혀가는 방법이 효과적. RSS 모니터링(`ps -o pid,rss`)으로 OOM 문제 진단.

### 데이터 누수(Data Leakage) 방지
동영상 기반 데이터에서 프레임 단위 random split은 데이터 누수를 유발. 반드시 **동영상(그룹) 단위 split** 사용.

### ⭐ 좌표 정규화의 중요성
서로 다른 해상도/카메라 환경의 데이터를 학습할 때, **절대 픽셀 좌표는 해상도에 의존**하여 모델이 자세 패턴이 아닌 해상도 패턴을 학습할 수 있음. bbox 기준 정규화(0~1)를 적용하면:
- 해상도에 무관한 feature 생성
- 모델이 실제 자세 패턴(aspect_ratio, spine_angle 등)에 집중
- 학습 환경과 다른 실제 환경에서도 일반화 성능 확보

### confidence 기반 필터링
YOLO keypoint의 confidence가 낮은 점은 정규화나 속도 계산에서 제외해야 함. 그렇지 않으면 bbox 밖의 좌표(0,0)가 큰 음수값으로 변환되어 feature 오염 발생.
