# Home Safe Solution - Vision AI 프로젝트

> **출처**: Confluence 내부 문서 (2026-02-17 export)  
> **용도**: 블로그 포스트 작성 레퍼런스

---

## 1. 프로젝트 개요

- **프로젝트명**: Home Safe Solution
- **목적**: YOLO Pose 기반 키포인트 검출 + Random Forest 분류기를 활용한 실시간 낙상 감지 시스템
- **배경**: 1인 가구 시대, 평소 행동을 모니터링하다가 이상한 패턴의 움직임이 있으면 탐지 → 알림 발생 → 긴급 지원을 받을 수 있도록 하는 비전 AI 기반 홈 케어 도우미 시스템

---

## 2. 기술 스택

- **비전 AI**: YOLO11s-pose (Pose Estimation)
- **ML 모델**: Random Forest (181 features)
- **분류**: 3-Class (Normal, Falling, Fallen) 로 시작 → 최종 2-Class (Normal, Fallen) 조정
- **GUI**: PyQt6
- **DB**: MySQL (ORM)
- **인증**: bcrypt 해시

---

## 3. 데이터 소스

- **형식**: .mp4 영상 + 가속도계 CSV
- **정상 데이터**: 1,629개
- **낙상 데이터**: 303개
- **출처**:
  - University of Rzeszow Fall Detection Dataset
  - https://ieee-dataport.org/documents/tst-fall-detection-dataset-v2

---

## 4. 특징(Feature) 구성 — 총 181개

### 4-1. 정적 특징 (Static Features)

| 카테고리 | 특징 수 | 설명 |
|---|---|---|
| Raw Keypoints | 51 | 17 키포인트 × (x, y, confidence) |
| Joint Angles | 4 | 팔꿈치, 무릎 각도 |
| Body Metrics | 7 | 척추 1, 바운딩박스 3, 높이 3 |
| Orientation | 2 | 어깨 기울기, 평균 신뢰도 |
| Accelerometer | 4 | acc_x, acc_y, acc_z, acc_mag |

### 4-2. 동적 특징 (Dynamic Features)

| 카테고리 | 특징 수 | 설명 |
|---|---|---|
| Keypoint Velocity | 34 | 각 키포인트 속도 (vx, vy) |
| Keypoint Acceleration | 34 | 각 키포인트 가속도 (ax, ay) |
| Rolling Statistics | 20+ | 이동 평균, 표준편차 |

**Velocity 예시**:
- `nose_vx = 5.2` → 오른쪽으로 이동
- `nose_vy = -8.3` → 위로 이동 (y축 반전)
- `hip_vy = 50.5` → 빠르게 아래로 (낙상 징후!)

**Rolling Statistics 판단 기준**:
- `hip_height_std > 50` → 불안정한 움직임
- `hip_velocity_max > 100` → 급격한 낙하
- `aspect_ratio_change > 0.5` → 자세 급변

---

## 5. 데이터 파이프라인

### 5-1. 전처리 스크립트

| 스크립트 | 기능 | 입력 | 출력 |
|---|---|---|---|
| extract_skeleton.py | YOLO Pose 키포인트 추출 | MP4 + 가속도계 CSV | 스켈레톤 CSV |
| feature_engineering.py | 특징 추출 (180+ 특징) | 스켈레톤 CSV | 특징 CSV |
| auto_labeling.py | 자동 레이블링 | 특징 CSV | 레이블된 CSV |
| create_dataset.py | 데이터셋 분할 | 레이블된 데이터 | Train/Val/Test |
| train_random_forest.py | Random Forest 학습 | 데이터셋 CSV | 모델 (pkl) |
| realtime_fall_detection.py | 실시간 낙상 감지 | 웹캠 피드 | 예측 결과 |
| run_pipeline.py | 전체 파이프라인 오케스트레이터 | 원본 데이터 | 완성된 모델 |

### 5-2. 파이프라인 흐름

```
원본 비디오 (fall-*.mp4) + 가속도계 (fall-*-acc.csv)
                    ↓
         [YOLO Pose Detection]
                    ↓
        스켈레톤 데이터 (17 키포인트 × 3)
                    ↓
         [Feature Engineering]
                    ↓
        특징 데이터 (180+ 특징)
                    ↓
           [Auto Labeling]
        ├─ Binary: Normal(0) / Fall(1)
        └─ 3-Class: Normal(0) / Falling(1) / Fallen(2)
                    ↓
         [Dataset Creation]
        Train(80%) / Val(10%) / Test(10%)
                    ↓
          [Model Training]
        Random Forest (100 trees, depth=20)
                    ↓
         [Real-time Inference]
        웹캠 → YOLO → RF → 이벤트 로깅
```

---

## 6. 데이터 구성

### 6-1. 원본 데이터

**정상 데이터 (40개)**:
```
경로: /home/gjkong/dev_ws/yolo/myproj/data_norm
파일명: adl-01-cam0.mp4 ~ adl-40-cam0.mp4
가속도: accel_norm/adl-01-acc.csv ~ adl-40-acc.csv
내용: 일상 생활 활동 (ADL) - 서 있기, 앉기, 걷기, 눕기, 계단 오르기, 물건 줍기 등
```

**낙상 데이터 (30개)**:
```
경로: /home/gjkong/dev_ws/yolo/myproj/data_fall
파일명: fall-01-cam0.mp4 ~ fall-30-cam0.mp4
가속도: accel_fall/fall-01-acc.csv ~ fall-30-acc.csv
내용: 앞으로 넘어지기, 뒤로 넘어지기, 옆으로 넘어지기, 기절 등
```

### 6-2. 통합 데이터 (70개)

```
data_integrated/
├── fall-01-cam0.mp4 ~ fall-30-cam0.mp4  (낙상)
└── fall-31-cam0.mp4 ~ fall-70-cam0.mp4  (정상)

accel_integrated/
├── fall-01-acc.csv ~ fall-30-acc.csv    (낙상)
└── fall-31-acc.csv ~ fall-70-acc.csv    (정상)

labeled_integrated/ (70개)
  └─ Normal:  5,906 프레임
  └─ Falling: 1,708 프레임
  └─ Fallen:  2,806 프레임
```

---

## 7. 레이블링 기준

### 7-1. Binary Classification

```python
if acc_mag > 2.5g:
    label = "Fall"
else:
    label = "Normal"
```

### 7-2. 3-Class Classification

```python
if acc_mag > 2.5g:
    label = "Falling"       # 낙상 시작
    if hip_height < threshold * 0.6:
        label = "Fallen"    # 완전히 쓰러짐
else:
    label = "Normal"
```

---

## 8. 모델 학습

### 8-1. Random Forest 설정

```python
RandomForestClassifier(
    n_estimators=100,        # 트리 개수
    max_depth=20,            # 최대 깊이
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight='balanced', # 클래스 불균형 처리
    random_state=42,
    n_jobs=-1                # 병렬 처리
)
```

### 8-2. 모델 디렉토리

```
models_integrated/
├── binary/
│   ├── random_forest_model.pkl
│   ├── feature_columns.txt
│   └── visualizations/
│       ├── confusion_matrix.png
│       ├── feature_importance.png
│       └── roc_curve.png
└── 3class/
    ├── random_forest_model.pkl
    ├── feature_columns.txt
    └── visualizations/
        ├── confusion_matrix.png
        └── feature_importance.png
```

### 8-3. 학습 과정

1. Train 세트로 학습
2. Validation 세트로 하이퍼파라미터 검증
3. Test 세트로 최종 성능 평가

---

## 9. 모델 성능

### 9-1. 3-Class Model (최종) — Test Set

```
Accuracy:  93.19%
Precision: 93.14%
Recall:    93.19%
F1-Score:  93.03%
```

### 9-2. 성능 평가

| 지표 | 값 | 의미 | 평가 |
|---|---|---|---|
| Accuracy | 93.19% | 전체 예측 중 정확한 비율 | 🟢 매우 우수 |
| Precision | 93.14% | 낙상으로 예측한 것 중 실제 낙상 비율 | 🟢 오탐률 낮음 |
| Recall | 93.19% | 실제 낙상 중 감지한 비율 | 🟢 놓치는 경우 적음 |
| F1-Score | 93.03% | Precision과 Recall의 조화평균 | 🟢 균형 잡힘 |

### 9-3. 벤치마크 비교

- 연구 논문: 80~85% (보통)
- 상용 제품: 85~90% (우수)
- **본 모델: 93.19% (매우 우수)**

### 9-4. Confusion Matrix 분석

- 대각선 (정확한 예측): 582 + 131 + 258 = 971
- 비대각선 (오분류): 71개
- 가장 중요한 피처: `acc_mag_mean`

### 9-5. class_weight 조정 후 개선 결과

**전체 성능 비교:**

| Metric | Baseline | Improved | Difference | Change |
|---|---|---|---|---|
| Accuracy | 0.9319 | 0.9386 | +0.0067 | +0.72% |
| Precision | 0.9314 | 0.9380 | +0.0066 | +0.71% |
| Recall | 0.9319 | 0.9386 | +0.0067 | +0.72% |
| F1 | 0.9303 | 0.9371 | +0.0068 | +0.73% |

**클래스별 정확도 비교:**

| Class | Baseline | Improved | Difference | Change |
|---|---|---|---|---|
| Normal | 0.9848 | 0.9865 | +0.0017 | +0.17% |
| Falling | 0.7661 | 0.7778 | +0.0117 | +1.53% |
| Fallen | 0.9214 | 0.9357 | +0.0143 | +1.55% |

---

## 10. 핵심 감지 임계값 및 원리

### 10-1. 감지 임계값

```python
confidence_threshold = 0.3      # 키포인트 신뢰도
fall_acc_threshold = 2.5        # 가속도 (g)
fallen_height_threshold = 0.6   # 정상 높이의 60%
model_confidence = 0.7          # 모델 예측 신뢰도
```

### 10-2. 2.5g의 물리적 의미

- **1.0g**: 가만히 서 있거나 앉아 있을 때의 평상시 중력 상태
- **2.5g**: 자신의 몸무게보다 2.5배 강한 힘이 가속도 센서에 순간적으로 가해졌음을 의미
- **일상 움직임**: 걷기, 앉기 → 1.5g를 넘지 않음
- **실제 낙상**: 바닥과 충돌 순간 → 2.0g ~ 3.0g 이상의 급격한 가속도 변화

### 10-3. 높이 변화 60% 임계값의 근거

- **인체 측정학적 통계** 기반
- 서 있는 자세: 무게 중심은 지면에서 전체 키의 약 55~58% 높이에 위치
- 낙상 상태: 바닥에 완전히 쓰러졌을 때 무게 중심 높이가 급격히 낮아짐
- 60% 이하 = '단순히 숙이는 동작'과 '실제 바닥에 쓰러진 상태'를 구분하는 물리적 경계선

### 10-4. YOLO Pose 키포인트 기반 계산 방식

- **기준값**: 프레임 내 사용자의 평상시 서 있는 키 (Bounding Box Height 또는 눈~발목 거리)
- **비교값**: 실시간 특정 키포인트(nose 또는 mid_shoulder)의 지면 대비 높이
- **판독**: `현재 높이 < (평상시 키 × 0.6)` → 'Fallen' 상태 진입

### 10-5. 종합 판독 메커니즘 (Sensor Fusion)

정확도/신뢰도 향상을 위한 복합 수치 판독:

- **A — 가속도(2.5g)**: "강한 충격이 발생했는가?" (사건 발생 시점 포착)
- **B — 높이 변화(60%)**: "충격 후 신체가 바닥에 낮게 깔려 있는가?" (상태 지속 확인)
- **최종 확정**: A, B 두 조건 모두 충족 시 → `event_logs` 테이블에 낙상 이벤트 기록

---

## 11. 실시간 탐지 (추론) 요구사항

| # | 요구사항 | 상태 |
|---|---|---|
| 1 | 앉기 감지 로직 강화 | 미적용 (불필요) |
| 2 | 실시간 영상 화면 + 추론 결과 표시 | ✅ 완료 |
| 3 | 현재 상태 값 (normal, falling, fallen) 실시간 로깅 | ✅ 완료 |
| 4 | 종합 위험 상태 (정상 vs 비정상) 노출 + DB 저장 | 🔄 진행중 |
| 5 | 사전 정의 이벤트 로그 로깅 | ✅ 완료 |
| 6 | 영상 필터 조정 | ✅ 완료 |
| 7 | 이상 상태 시점 전후 스냅샷 영상 저장/검색/조회 | 🔄 진행중 |
| 8 | 긴급 호출 버튼 | ✅ 완료 |
| 9 | 종합 통계 Dashboard | ✅ 완료 |
| 10 | DB 로그/영상/이벤트 조회 | ✅ 완료 |
| 11 | 사용자 관리 | 🔄 진행중 |
| 12 | 쓰러짐(상태:2) 감지 후 로직 | 🔴 필수 |

### 12번 상세 — 쓰러짐 감지 후 로직

- **상태 2 탐지 후 30초 지속 유지**: 1차 SMS 발송 + DB 이벤트/발송 처리 로그 저장
- **+1분 지속 유지**: 해당 시점 영상 저장 + SMS 저장 로그 발송 + DB 저장
- **+30초 지속 유지**: 긴급 호출 버튼 클릭 → 조치 내역 DB 저장

---

## 12. GUI 모듈 구성

| 파일 | 기능 |
|---|---|
| main.py | 애플리케이션 진입점 |
| login_window.py | 로그인 (bcrypt 해시) |
| main_window.py | 메인 윈도우 + 사이드바 |
| monitoring_page.py | 실시간 웹캠 모니터링 |
| dashboard_page.py | 통계 대시보드 |
| event_management_page.py | 이벤트 관리 (CRUD) |
| events_page.py | 이벤트 로그 뷰어 |
| users_page.py | 사용자 관리 (관리자) |
| database_models.py | MySQL ORM |
| fall_detector.py | 낙상 감지 유틸리티 |
| one_euro_filter.py | 키포인트 스무딩 필터 |

---

## 13. 데이터베이스 (MySQL)

### 13-1. 접속 설정

```python
config = {
    'host': 'localhost',
    'database': 'home_safe',
    'user': 'homesafe',
    'password': '*******'
}
```

### 13-2. 스키마

| 테이블 | 설명 |
|---|---|
| users | 사용자 계정 (bcrypt 해시) |
| event_types | 이벤트 유형 (Fall, Fire, Flooding 등) |
| event_logs | 이벤트 기록 (신뢰도, 높이, 각도 등) |
| auto_report_logs | 119/112 자동 신고 로그 |
| system_settings | 시스템 설정 (key-value) |
| login_history | 로그인 이력 |

---

## 14. YOLO 키포인트 (COCO 17-point)

```python
keypoint_names = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
]
```

**분류 클래스:**
```python
# Binary
{0: 'Normal', 1: 'Fall'}

# 3-Class
{0: 'Normal', 1: 'Falling', 2: 'Fallen'}
```

---

## 15. 디렉토리 구조

```
myproj/
├── accel/              # 가속도계 센서 데이터 (CSV)
├── data/               # 원본 비디오 파일 (MP4)
├── dataset/            # 학습/검증/테스트 데이터셋
│   ├── 3class/         # 3클래스 분류용 (Normal/Falling/Fallen)
│   └── binary/         # 이진 분류용 (Normal/Fall)
├── features/           # 추출된 특징 데이터 (CSV)
├── gui/                # PyQt6 GUI 애플리케이션
├── labeled/            # 레이블링된 데이터
│   └── visualizations/ # 레이블링 시각화
├── models/             # 학습된 모델 파일
│   ├── 3class/         # 3클래스 Random Forest 모델
│   └── binary/         # 이진 분류 Random Forest 모델
├── scripts/            # 데이터 처리 및 학습 스크립트
│   ├── admin/          # 관리자용 스크립트
└── skeleton/           # YOLO Pose 키포인트 데이터 (CSV)
```

---

## 16. 후속 진행 필요

### 16-1. 모델 최적화 개선

1. **추가 데이터 수집**: 직접 촬영 + 기존 비디오에서 Falling 구간 추출
2. **Auto Labeling 조정**: `falling_duration = 30 ~ 45`
3. **Data Augmentation**: Noise 추가, 시간 축 변환, 속도 변화 → Falling 샘플 2~3배 증가
4. **class_weight 조정**:
   ```python
   class_weight={0: 1.0, 1: 2.0, 2: 1.0}  # Falling에 2배 가중치
   ```
5. **2단계 분류 전략**:
   - 1단계: Binary Classification (Normal vs Fall) → 93%+ 정확도, 빠른 판단
   - 2단계: Fall인 경우만 3-Class (Falling vs Fallen) → 세밀한 구분
6. **윈도우 사이즈 조정**: `window_size = 5` (0.25초) → `window_size = 10` (0.5초)
   - 더 긴 시간 고려 → Falling 패턴 인식 개선 (단, 지연 시간 증가 trade-off)
7. **Feature Selection**: `feature_importance.png` 확인 → 상위 50개 피처 선택 후 재학습

### 16-2. 기타 후속 작업

- 이벤트 로그 연동
- 1,2차 알림 및 영상 저장
- 사용자 관리
- **ST-GCN (Spatio-Temporal Graph Convolutional Networks) 모델 비교**
- **LSTM 모델 기반 추론 로직 적용 후 RF와 비교**
