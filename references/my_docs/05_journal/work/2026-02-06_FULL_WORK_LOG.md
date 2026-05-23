# Home Safe Solution - 작업 기록

## 📅 날짜: 2026-02-06 (목)

---

## 1. 학습 파이프라인 구현 완료 (오전)

### 1.1 Pipeline 패키지 생성 (`/home/gjkong/dev_ws/yolo/myproj/pipeline/`)

| 파일 | 설명 |
|------|------|
| `__init__.py` | 패키지 초기화 |
| `config.py` | 설정 데이터클래스 (5개 Config + 편의 함수) |
| `data_ingest.py` | Stage 1: 데이터 수집 (YouTube/URL/로컬 지원) |
| `preprocessor.py` | Stage 2: 전처리 (YOLO Pose → RF Feature + ST-GCN Sequence) |
| `trainer.py` | Stage 3: 학습 엔진 (RF + ST-GCN Fine-tuning) |
| `_stgcn_model.py` | ST-GCN 모델 정의 (Fine-tuned + Original) |
| `orchestrator.py` | 4단계 파이프라인 오케스트레이션 + CLI |

### 1.2 GUI 통합 (`/home/gjkong/dev_ws/yolo/myproj/gui/`)

| 파일 | 설명 |
|------|------|
| `training_page.py` | PyQt6 학습 파이프라인 GUI (5개 패널 통합) |
| `main_window.py` | TrainingPage 통합 (관리자 메뉴에 "🎓 모델 학습" 추가) |

### 1.3 파이프라인 테스트 (`test_pipeline.py`)

```
============================================================
  테스트 결과 요약
============================================================
  dependencies         : PASS
  imports              : PASS
  config               : PASS
  data_ingest          : PASS
  preprocessor         : PASS
  trainer              : PASS
  orchestrator         : PASS
  gui                  : PASS

  총 결과: 8/8 테스트 통과
  🎉 모든 테스트 통과! 파이프라인 사용 준비 완료
```

---

## 2. 버그 수정 (오전)

### 2.1 샘플 수 부족 시 train_test_split 오류

**문제:** 데이터가 5개 미만일 때 분할 불가 오류 발생

**해결 (`preprocessor.py`):**
- 샘플 5개 미만 → 전체를 train으로 사용
- stratify 옵션 → 클래스별 최소 2개 이상일 때만 적용
- 오류 발생 시 fallback 처리

### 2.2 QThread 종료 오류

**문제:** GUI 닫힐 때 "QThread: Destroyed while thread is still running" 에러

**해결:**
- `training_page.py`에 `cleanup()` 메서드 추가
- `main_window.py`의 `closeEvent`에서 `cleanup()` 호출
- Worker 안전 종료: cancel → wait → terminate

### 2.3 TrainingPage 초기화 순서 오류

**문제:** `_on_nav_changed`가 `self.stack` 생성 전에 호출됨

**해결:** `_init_ui()`에서 `self.stack`을 사이드바보다 먼저 생성

---

## 3. 데이터 복원 (오전)

### 3.1 문제 상황

새 파이프라인이 생성한 데이터가 기존 데이터를 덮어씀:
- RF: 50개 feature (기존 모델은 181~183개 필요)
- ST-GCN: 빈 test_data.npy (128 bytes)

### 3.2 복원 작업

```bash
# RF 데이터 복원 (3class → binary)
cd /home/gjkong/dev_ws/yolo/myproj/dataset
mv binary binary_pipeline_generated
cp -r 3class binary

# ST-GCN 데이터 복원 (백업에서)
mv /home/gjkong/dev_ws/st_gcn/data/binary /home/gjkong/dev_ws/st_gcn/data/binary_pipeline_generated
cp -r /home/gjkong/dev_ws/st_gcn_backup/data/binary /home/gjkong/dev_ws/st_gcn/data/binary
```

### 3.3 복원 확인

```
ST-GCN: test_data.npy 465KB (정상)
RF: feature_columns.txt 184줄 (183개 feature)
```

---

## 4. 모델 성능 비교 테스트 (오전)

### 4.1 실행

```bash
cd /home/gjkong/dev_ws/yolo/myproj/scripts/admin
python compare_models_report_last.py
```

### 4.2 결과

| 모델 | Accuracy | F1 | AUC | Speed | Size | Samples |
|------|----------|-----|-----|-------|------|---------|
| 🌲 **Random Forest** | **94.92%** | **0.9189** | **0.9951** | **0.08ms** | 1.25MB | 295 |
| 📊 ST-GCN (Original) | 21.05% | 0.3478 | 0.6417 | 0.26ms | 29.74MB | 38 |
| 🚀 ST-GCN (Fine-tuned) | 86.84% | 0.6667 | 0.9000 | 0.25ms | 9.97MB | 38 |

### 4.3 결론

- **RF 최고 성능**: 정확도 94.92%, F1 0.9189, 속도 0.08ms
- **ST-GCN Fine-tuned**: 86.84% (RF 다음)
- **ST-GCN Original**: 21.05% (성능 저조)

### 4.4 리포트 저장 위치

```
/home/gjkong/dev_ws/yolo/myproj/scripts/admin/Model_Compare_Report/20260206_105111/
├── MODEL_COMPARISON_REPORT.md
├── dashboard_comparison.png
├── confusion_matrices.png
├── roc_curves.png
├── inference_time.png
└── model_size.png
```

---

## 5. ST-GCN Fine-tuning 설명 (오후)

### 5.1 사전 학습 모델 정보

| 항목 | 내용 |
|------|------|
| **파일명** | `stgcn_ntu60_hrnet.pth` |
| **크기** | 12.47 MB |
| **경로** | `/home/gjkong/dev_ws/st_gcn/pretrained/` |
| **학습 데이터셋** | NTU RGB+D 60 |
| **키포인트** | HRNet 기반 (COCO 17 keypoints 호환) |
| **원본 클래스** | 60개 행동 클래스 |

### 5.2 Fine-tuning 구조

```
stgcn_ntu60_hrnet.pth (NTU60, 60 classes)
         ↓
   Backbone (ST-GCN layers) → 동결 또는 낮은 LR (1e-5)
         ↓
   Head (FC layer) → 새로 학습 (1e-3)
         ↓
   best_model_finetuned.pth (Binary, 2 classes: Fall/Normal)
```

### 5.3 Fine-tuning 효과

| 모델 | 설명 | 정확도 |
|------|------|--------|
| ST-GCN Original | NTU60으로만 학습, 낙상 fine-tuning 안함 | 21.05% |
| **ST-GCN Fine-tuned** | NTU60 + 낙상 데이터로 fine-tuning | **86.84%** |

**65.79%p 향상!**

---

## 6. compare_models_report_last.py 수정 (오후)

### 6.1 추가 기능

`plot_precision_recall()` 함수 추가 → `precision_recall.png` 생성

| 차트 | 내용 |
|------|------|
| **Precision** | 낙상 예측 중 실제 낙상 비율 (정밀도) |
| **Recall** | 실제 낙상 중 감지한 비율 (재현율) |
| **비교** | Precision vs Recall 그룹 바 차트 |

### 6.2 수정된 출력 결과

```
Model_Compare_Report/YYYYMMDD_HHMMSS/
├── MODEL_COMPARISON_REPORT.md
├── dashboard_comparison.png
├── confusion_matrices.png
├── precision_recall.png      ← 새로 추가!
├── roc_curves.png
├── inference_time.png
└── model_size.png
```

---

## 7. 파일 구조 요약

```
/home/gjkong/dev_ws/yolo/myproj/
├── gui/
│   ├── main.py
│   ├── main_window.py          # ✅ TrainingPage 통합
│   ├── training_page.py        # ✅ 신규 (PyQt6)
│   └── ...
├── pipeline/                   # ✅ 신규 패키지
│   ├── __init__.py
│   ├── config.py
│   ├── data_ingest.py
│   ├── preprocessor.py
│   ├── trainer.py
│   ├── _stgcn_model.py
│   └── orchestrator.py
├── dataset/
│   ├── binary/                 # ✅ 복원됨 (183 features)
│   ├── 3class/
│   └── raw_videos/
├── test_pipeline.py            # ✅ 테스트 스크립트
└── scripts/admin/
    ├── compare_models_report_last.py  # ✅ Precision/Recall 추가
    └── Model_Compare_Report/
```

---

## 8. 다음 작업 (예정)

- [ ] ST-GCN 테스트 데이터 확장 (현재 38개 → 더 많은 샘플)
- [ ] Phase C: Optuna 하이퍼파라미터 튜닝 구현
- [ ] 학습 파이프라인 실제 운영 테스트
- [ ] 사용 매뉴얼 작성

---

**작성일시:** 2026-02-06 14:30
**작성자:** Claude AI Assistant
