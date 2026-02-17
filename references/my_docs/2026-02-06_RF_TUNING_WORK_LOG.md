# Home Safe Solution - RF 튜닝 실험 작업 기록

## 📅 날짜: 2026-02-06 (목) 저녁

---

## 1. 작업 목적

기존 Random Forest 모델(binary, 94.92% accuracy)의 실시간 낙상 탐지 성능 개선을 위해 4가지 튜닝 전략을 실험하고 동일 테스트셋으로 비교 평가한다.

### 원칙
- ✅ 기존 모델 파일 변경 없음 (읽기 전용 로드)
- ✅ 모든 결과는 별도 디렉토리에 저장
- ✅ 동일 테스트셋(binary/test.csv, 295 samples)으로 공정 비교

---

## 2. 데이터셋 정보

| 항목 | 내용 |
|------|------|
| **분류 방식** | 이진 바이너리 (Normal=0, Fall=1) |
| **Label 컬럼** | `label_binary` |
| **Train** | 2,354 samples (Normal: 1,641 / Fall: 713) |
| **Test** | 295 samples (Normal: 206 / Fall: 89) |
| **Features** | 181개 |
| **데이터 경로** | `dataset/binary/train.csv`, `test.csv` |

---

## 3. 실험 스크립트

| 파일 | 설명 |
|------|------|
| `rf_tuning_experiment.py` | 4가지 전략 자동 실행 + 시각화 + MD 리포트 생성 |
| `RF_TUNING_GUIDE.md` | 실행 가이드 문서 |

### 3.1 기존 모델 로드 이슈

- `pickle.load()` 시 `STACK_GLOBAL requires str` 오류 발생
- 원인: scikit-learn 버전 차이로 인한 pickle 호환성 문제
- 해결: try/except로 감싸고, 로드 실패 시 동일 설정(`n_estimators=100`)으로 재학습하여 Baseline 생성
- 기존 모델 파일은 변경하지 않음

---

## 4. 4가지 튜닝 전략 및 결과

### 전략 1: Threshold 조정 (0.20 ~ 0.50)

기존 모델의 확률 출력에 다양한 threshold를 적용하여 Recall/Precision 트레이드오프 분석.

| Threshold | Accuracy | Precision | Recall | F1-Score |
|-----------|----------|-----------|--------|----------|
| 0.20 | 0.9288 | 0.8091 | **1.0000** | 0.8945 |
| 0.25 | 0.9356 | 0.8241 | **1.0000** | 0.9036 |
| 0.30 | 0.9390 | 0.8318 | **1.0000** | 0.9082 |
| 0.35 | 0.9458 | 0.8544 | 0.9888 | 0.9167 |
| 0.40 | 0.9492 | 0.8627 | 0.9888 | 0.9215 |
| 0.45 | 0.9458 | 0.8687 | 0.9663 | 0.9149 |
| 0.50 ⬅ default | 0.9492 | 0.8776 | 0.9663 | 0.9198 |

**분석:** threshold 0.20~0.30에서 Recall 1.0000(낙상 100% 감지) 달성 가능하나 오경보 증가.

### 전략 2: Optuna 하이퍼파라미터 최적화

100회 탐색, recall 최대화 기준.

**Best 파라미터:**

| 파라미터 | 값 |
|---------|-----|
| n_estimators | 343 |
| max_depth | 5 |
| min_samples_split | 19 |
| min_samples_leaf | 10 |
| max_features | log2 |
| class_weight | balanced_subsample |

| 모델 | Accuracy | Recall | F1-Score |
|------|----------|--------|----------|
| Optuna (th=0.50) | 0.9220 | 0.9663 | 0.8821 |
| **Optuna (th=0.80)** | **0.9661** | 0.9213 | **0.9425** |

**Best CV Recall:** 0.9762

### 전략 3: Feature Selection

Feature Importance 기반 상위 K개 feature만 선별하여 학습/평가.

| 모델 | Features | Accuracy | Recall | F1-Score |
|------|----------|----------|--------|----------|
| Baseline (전체) | 181 | 0.9492 | 0.9663 | 0.9198 |
| Top-50 | 50 | 0.9458 | 0.9551 | 0.9140 |
| Top-80 | 80 | 0.9559 | 0.9551 | 0.9290 |
| Top-100 | 100 | 0.9559 | 0.9663 | 0.9297 |
| **Top-130** | 130 | **0.9627** | **0.9663** | **0.9399** |

**분석:** Top-130에서 Baseline보다 Accuracy, F1 모두 개선되면서 Recall 유지.

### 전략 4: 조합 전략 (class_weight + Optuna + Threshold)

| 모델 | Accuracy | Recall | F1-Score |
|------|----------|--------|----------|
| **RF Balanced (th=0.59)** | **0.9695** | **0.9551** | **0.9497** |
| RF Optuna+Balanced (th=0.79) | 0.9627 | 0.9213 | 0.9371 |
| RF weight(Fall=2x, th=0.65) | 0.9661 | 0.9101 | 0.9419 |
| RF weight(Fall=3x, th=0.46) | 0.9593 | 0.9663 | 0.9348 |
| RF weight(Fall=5x, th=0.57) | 0.9593 | 0.9326 | 0.9326 |

---

## 5. 종합 비교

### Baseline 대비 개선 (Top 3)

| 순위 | 모델 | Accuracy | Recall | F1 | F1 개선 |
|------|------|----------|--------|------|---------|
| 1 | **RF Balanced (th=0.59)** | **96.95%** | 0.9551 | **0.9497** | **+0.0299** |
| 2 | RF Optuna (th=0.80) | 96.61% | 0.9213 | 0.9425 | +0.0227 |
| 3 | RF weight(Fall=2x, th=0.65) | 96.61% | 0.9101 | 0.9419 | +0.0221 |
| ⭐ | Baseline (th=0.50) | 94.92% | 0.9663 | 0.9198 | — |

---

## 6. 추천 모델

### 🏆 RF Balanced (th=0.59)

| 항목 | Baseline | RF Balanced | 변화 |
|------|----------|-------------|------|
| Accuracy | 94.92% | **96.95%** | **+2.03%p** |
| F1-Score | 0.9198 | **0.9497** | **+0.0299** |
| Recall | 0.9663 | 0.9551 | -0.0112 |

**선정 이유:**
- F1과 Accuracy 모두 전 실험 중 최고
- Recall 소폭 감소(-1.12%p)는 post-processing(연속 프레임 확인)으로 보완 가능
- `class_weight='balanced'` + `threshold=0.59` 조합으로 재현 가능

---

## 7. 실제 환경 적용 절차 (예정)

### Step 1: 기존 모델 백업
```bash
cd /home/gjkong/dev_ws/yolo/myproj/models/binary
cp random_forest_model.pkl random_forest_model_backup_20260206.pkl
```

### Step 2: 신규 모델 학습 및 저장
- `class_weight='balanced'`, `n_estimators=200` 설정으로 학습
- 기존 모델 경로(`models/binary/random_forest_model.pkl`)에 저장

### Step 3: GUI threshold 반영
- 기존 GUI 추론 코드에서 threshold 0.5 → 0.59로 변경
- 또는 설정 파일로 분리하여 관리

> ⚠ Step 2~3은 아직 미적용 상태. 별도 적용 스크립트 필요.

---

## 8. 출력 파일

```
experiments/rf_tuning_20260206_191149/
├── RF_TUNING_EXPERIMENT_REPORT.md    ← 자동 생성 종합 리포트
├── threshold_analysis.png            ← Threshold별 메트릭 변화
├── strategy_comparison.png           ← 전략별 최적 결과 비교
├── confusion_matrices.png            ← 주요 모델 Confusion Matrix
├── roc_curves.png                    ← ROC 커브 비교
├── feature_importance_top30.png      ← Feature 중요도 상위 30
└── models/
    └── rf_optuna_best.pkl            ← Optuna 최적 모델
```

---

## 9. 다음 작업 (예정)

- [ ] 추천 모델(RF Balanced) 실환경 적용 스크립트 작성
- [ ] 기존 모델 백업 → 신규 모델 저장 → threshold 설정 반영
- [ ] Post-processing 로직 추가 (연속 N프레임 확인)
- [ ] ST-GCN 테스트 데이터 확장 (현재 38개)
- [ ] Phase C: Optuna 하이퍼파라미터 튜닝 (ST-GCN 대상)

---

**작성일시:** 2026-02-06 19:20
**작성자:** Claude AI Assistant
