---
title: "Home Safe Solution - 자동화 학습 파이프라인 설계서"
date: 2026-03-21
draft: true
tags: ["ai-ml"]
categories: ["ai-ml"]
description: "``` ┌─────────────────────────────────────────────────────────────────┐ │                    GUI Training Page (PyQt5)  "
---

# Home Safe Solution - 자동화 학습 파이프라인 설계서

## 2026-02-05 (수)

---

## 1. 시스템 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                    GUI Training Page (PyQt5)                     │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────────┐  │
│  │ Data      │ │ Preproc  │ │ Training  │ │ Results Viewer   │  │
│  │ Source    │ │ Config   │ │ Config    │ │ (비교 리포트)     │  │
│  │ Manager   │ │ Panel    │ │ & Monitor │ │                  │  │
│  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └────────┬─────────┘  │
└───────┼────────────┼─────────────┼─────────────────┼────────────┘
        │            │             │                 │
        ▼            ▼             ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              TrainingPipelineOrchestrator (Core)                 │
│                                                                 │
│  Stage 1        Stage 2          Stage 3          Stage 4       │
│  ┌──────────┐   ┌──────────┐    ┌──────────┐    ┌──────────┐   │
│  │ Data     │──▶│ Preproc  │──▶│ Training │──▶│ Auto      │   │
│  │ Ingest   │   │ Engine   │    │ Engine   │    │ Compare   │   │
│  └──────────┘   └──────────┘    └──────────┘    └──────────┘   │
│                                                                 │
│  - YouTube DL   - YOLO Pose     - RF (sklearn)   - compare_    │
│  - URL fetch    - Feature Ext   - ST-GCN (torch)   models.py   │
│  - Local files  - Sequence Gen  - Hyperparam      - Report     │
│  - Label mgmt   - Train/Val/    - Early stopping    generation │
│                    Test split   - Checkpoint mgmt              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 파일 구조

```
/home/gjkong/dev_ws/yolo/myproj/
├── gui/
│   ├── main.py                          # 기존 GUI 메인
│   ├── monitoring_page.py               # 기존 모니터링 페이지
│   ├── training_page.py                 # ⭐ 신규 - 학습 파이프라인 GUI
│   ├── training_data_panel.py           # ⭐ 신규 - 데이터 소스 패널
│   ├── training_config_panel.py         # ⭐ 신규 - 학습 설정 패널
│   ├── training_progress_widget.py      # ⭐ 신규 - 학습 진행 모니터
│   └── training_results_viewer.py       # ⭐ 신규 - 결과 리포트 뷰어
│
├── pipeline/                            # ⭐ 신규 디렉토리
│   ├── __init__.py
│   ├── orchestrator.py                  # 파이프라인 오케스트레이터
│   ├── data_ingest.py                   # Stage 1: 데이터 수집
│   ├── preprocessor.py                  # Stage 2: 전처리
│   ├── trainer.py                       # Stage 3: 학습 엔진
│   ├── auto_compare.py                  # Stage 4: 자동 비교
│   └── config.py                        # 파이프라인 설정 관리
│
├── scripts/admin/
│   └── Model_Compare_Report/            # 기존 비교 리포트
│
└── dataset/                             # 데이터셋 디렉토리
    ├── raw_videos/                      # ⭐ 원본 비디오 저장
    │   ├── fall/                        # 낙상 비디오
    │   └── normal/                      # 정상 비디오
    ├── binary/                          # RF 학습 데이터
    │   ├── train.csv
    │   ├── val.csv
    │   └── test.csv
    └── sequences/                       # ST-GCN 학습 데이터
        ├── train_data.npy
        ├── train_labels.npy
        ├── val_data.npy
        ├── val_labels.npy
        ├── test_data.npy
        └── test_labels.npy
```

---

## 3. Stage 1 - 데이터 수집 (data_ingest.py)

### 3.1 지원 소스 타입

| 소스 | 입력 형태 | 처리 방법 |
|------|----------|----------|
| YouTube | URL (단일/재생목록) | `yt-dlp` → mp4 |
| 인터넷 동영상 | HTTP/HTTPS URL | `requests` + `ffprobe` 검증 |
| 로컬 파일 | 파일 경로 / 폴더 경로 | 직접 복사 또는 심볼릭 링크 |
| 데이터셋 폴더 | 경로 (fall/, normal/ 구조) | 구조 검증 후 등록 |

### 3.2 지원 동영상 포맷

`*.mp4`, `*.avi`, `*.mov`, `*.mkv`, `*.webm`, `*.flv`, `*.wmv`, `*.m4v`

### 3.3 라벨링 전략

```python
class LabelStrategy:
    FOLDER_BASED = "folder"      # fall/ , normal/ 폴더 구조
    FILENAME_BASED = "filename"  # fall-01.mp4, normal-03.mp4
    CSV_MANIFEST = "csv"         # manifest.csv (파일명, 라벨)
    MANUAL = "manual"            # GUI에서 직접 라벨 지정
```

### 3.4 데이터 수집 설정 (GUI)

```
┌─────────────────────────────────────────────────────┐
│  📥 데이터 소스 관리                                  │
│                                                      │
│  소스 타입: [YouTube ▼]                               │
│                                                      │
│  URL/경로: [https://youtube.com/watch?v=...    ] [+] │
│                                                      │
│  라벨:  ○ Fall  ○ Normal  ○ 자동 (폴더/파일명 기반)   │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │ # │ 소스          │ 라벨   │ 상태    │ 삭제  │    │
│  │ 1 │ fall-01.mp4   │ Fall   │ ✅ 완료 │  🗑  │    │
│  │ 2 │ youtube/abc.. │ Normal │ ⏳ 대기 │  🗑  │    │
│  │ 3 │ normal-02.avi │ Normal │ ✅ 완료 │  🗑  │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  총 비디오: 25개 (Fall: 12, Normal: 13)              │
│  [📂 폴더 일괄 추가]  [📋 CSV 가져오기]  [▶ 다운로드] │
└─────────────────────────────────────────────────────┘
```

---

## 4. Stage 2 - 전처리 (preprocessor.py)

### 4.1 전처리 파이프라인

```
원본 비디오 (mp4/avi/...)
    │
    ▼
[1] FFmpeg 정규화
    - 해상도 통일 (640x480 기본)
    - FPS 통일 (30fps 기본)
    - 코덱 통일 (H.264)
    │
    ▼
[2] YOLO Pose Estimation
    - YOLOv8-pose 추론
    - 17개 키포인트 추출 (COCO format)
    - 프레임별 키포인트 시퀀스 저장
    │
    ├──────────────────────┐
    ▼                      ▼
[3a] RF 특징 추출          [3b] ST-GCN 시퀀스 생성
    - 관절 각도 계산        - 60프레임 슬라이딩 윈도우
    - 거리/비율 특징         - (3, 60, 17, 1) 텐서
    - 속도/가속도 특징       - 정규화 (center, scale)
    - feature_columns.txt   - overlap stride 설정
    │                      │
    ▼                      ▼
[4a] RF Dataset            [4b] ST-GCN Dataset
    - train.csv             - train_data.npy
    - val.csv               - val_data.npy
    - test.csv              - test_data.npy
```

### 4.2 전처리 설정

```python
@dataclass
class PreprocessConfig:
    # 비디오 정규화
    target_resolution: tuple = (640, 480)
    target_fps: int = 30
    
    # YOLO Pose
    yolo_model: str = "yolov8m-pose.pt"
    confidence_threshold: float = 0.5
    
    # ST-GCN 시퀀스
    sequence_length: int = 60          # 프레임 수
    sequence_stride: int = 30          # 슬라이딩 윈도우 stride
    normalize_method: str = "center"   # center / minmax / none
    
    # 데이터 분할
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    random_seed: int = 42
    stratify: bool = True              # 라벨 비율 유지
```

---

## 5. Stage 3 - 학습 엔진 (trainer.py)

### 5.1 RF 학습 설정

```python
@dataclass
class RFTrainConfig:
    n_estimators: list = field(default_factory=lambda: [50, 100, 200, 300])
    max_depth: list = field(default_factory=lambda: [None, 10, 20, 30])
    min_samples_split: list = field(default_factory=lambda: [2, 5, 10])
    min_samples_leaf: list = field(default_factory=lambda: [1, 2, 4])
    
    # 튜닝 방법
    tuning_method: str = "grid"        # grid / random / bayesian
    cv_folds: int = 5
    scoring: str = "f1"                # accuracy / f1 / recall
```

### 5.2 ST-GCN 학습 설정

```python
@dataclass
class STGCNTrainConfig:
    # 기본 하이퍼파라미터
    epochs: int = 50
    batch_size: int = 16
    
    # Learning Rate
    backbone_lr: float = 1e-5
    head_lr: float = 1e-3
    weight_decay: float = 1e-4
    
    # 스케줄러
    scheduler: str = "cosine"          # cosine / step / plateau
    
    # Early Stopping
    early_stopping: bool = True
    patience: int = 10
    min_delta: float = 0.001
    
    # Fine-tuning 옵션
    use_pretrained: bool = True
    freeze_backbone_epochs: int = 5    # 초기 N 에포크 backbone 동결
    
    # 튜닝 범위 (Optuna 사용 시)
    tuning_enabled: bool = False
    n_trials: int = 20
    tuning_params: dict = field(default_factory=lambda: {
        "backbone_lr": (1e-6, 1e-4),
        "head_lr": (1e-4, 1e-2),
        "batch_size": [8, 16, 32],
        "weight_decay": (1e-5, 1e-3),
    })
```

### 5.3 학습 GUI 모니터

```
┌─────────────────────────────────────────────────────┐
│  📈 학습 진행 상황                                    │
│                                                      │
│  현재 단계: [████████████░░░░░░] ST-GCN 학습 (3/4)   │
│                                                      │
│  ┌── RF 학습 ──────────────────────────────────────┐ │
│  │ 상태: ✅ 완료  |  Best F1: 0.9189               │ │
│  │ 최적 파라미터: n_estimators=100, max_depth=20   │ │
│  │ 소요 시간: 45초                                  │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌── ST-GCN Fine-tuning ──────────────────────────┐ │
│  │ Epoch: [████████░░░] 17/50                      │ │
│  │                                                  │ │
│  │   Train Loss  ───────────────────▶  0.2560      │ │
│  │   Train Acc   ───────────────────▶  90.23%      │ │
│  │   Val Loss    ───────────────────▶  0.2184      │ │
│  │   Val Acc     ───────────────────▶  91.89% ⭐   │ │
│  │                                                  │ │
│  │   Best Val Acc: 91.89% (Epoch 17)              │ │
│  │   Early Stop: 0/10                              │ │
│  │                                                  │ │
│  │   [실시간 Loss/Acc 그래프]                       │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  [⏸ 일시정지]  [⏹ 중단]  [📊 중간 결과 보기]         │
└─────────────────────────────────────────────────────┘
```

---

## 6. Stage 4 - 자동 비교 (auto_compare.py)

### 6.1 자동 트리거 흐름

```
학습 완료 (RF + ST-GCN)
    │
    ▼
새 모델 체크포인트 → 임시 경로에 저장
    │
    ▼
compare_models.py 자동 실행
    - 기존 모델 vs 새 모델 비교
    - 리포트 자동 생성
    │
    ▼
성능 비교 결과 판정
    ├── 새 모델이 더 좋으면 → 모델 교체 제안
    └── 기존 모델이 더 좋으면 → 유지 권장
    │
    ▼
GUI에 결과 표시 + 사용자 승인
    ├── [✅ 새 모델 적용] → 모델 파일 교체
    └── [❌ 기존 유지]    → 새 모델 아카이브
```

### 6.2 비교 리포트 자동 생성 경로

```
~/dev_ws/yolo/myproj/scripts/admin/Model_Compare_Report/
└── 20260205_HHMMSS/
    ├── MODEL_COMPARISON_REPORT.md
    ├── dashboard_comparison.png
    ├── confusion_matrices.png
    ├── roc_curves.png
    ├── inference_time.png
    └── model_size.png
```

---

## 7. Orchestrator 핵심 인터페이스

```python
class TrainingPipelineOrchestrator:
    """전체 파이프라인 오케스트레이터"""
    
    # 시그널 (GUI 연동)
    stage_changed = Signal(str, int)        # (stage_name, progress%)
    log_message = Signal(str)               # 로그 메시지
    training_metric = Signal(dict)          # 실시간 메트릭
    pipeline_finished = Signal(dict)        # 최종 결과
    pipeline_error = Signal(str)            # 에러 발생
    
    def run_full_pipeline(self, config: PipelineConfig):
        """전체 파이프라인 실행 (비동기)"""
        # Stage 1: 데이터 수집
        # Stage 2: 전처리
        # Stage 3: 학습
        # Stage 4: 자동 비교
    
    def run_from_stage(self, stage: int, config: PipelineConfig):
        """특정 스테이지부터 실행 (이전 결과 재사용)"""
    
    def pause(self): ...
    def resume(self): ...
    def cancel(self): ...
```

---

## 8. GUI 통합 - training_page.py

### 8.1 전체 레이아웃

```
┌─────────────────────────────────────────────────────────────────┐
│  🏠 Home Safe Solution - Training Pipeline                      │
├─────────┬───────────────────────────────────────────────────────┤
│         │                                                       │
│  📥     │  ┌─────────────────────────────────────────────────┐  │
│  Data   │  │  [현재 활성 패널 영역]                            │  │
│  Source │  │                                                   │  │
│         │  │  데이터 소스 / 전처리 설정 / 학습 설정 /          │  │
│  ⚙️     │  │  학습 모니터 / 결과 뷰어                          │  │
│  Preproc│  │                                                   │  │
│         │  │                                                   │  │
│  🎯     │  └─────────────────────────────────────────────────┘  │
│  Train  │                                                       │
│         │  ┌─────────────────────────────────────────────────┐  │
│  📊     │  │  진행 상태 바 + 로그 출력                         │  │
│  Results│  │  Stage: [■■■■■□□□□□] 전처리 (50%)                │  │
│         │  │  > YOLO 포즈 추정 중... (23/50 비디오)            │  │
│         │  └─────────────────────────────────────────────────┘  │
├─────────┴───────────────────────────────────────────────────────┤
│  [▶ 전체 실행]  [⏸ 일시정지]  [⏹ 중단]  [📂 리포트 폴더 열기]  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 GUI 연동 시그널 흐름

```
Orchestrator (Worker Thread)          GUI (Main Thread)
─────────────────────                 ─────────────────
stage_changed ──────────────────────▶ 진행바 + 단계 표시 업데이트
log_message ────────────────────────▶ 로그 텍스트 영역 추가
training_metric ────────────────────▶ 실시간 차트 업데이트
pipeline_finished ──────────────────▶ 결과 뷰어 활성화
pipeline_error ─────────────────────▶ 에러 다이얼로그 표시
```

---

## 9. 의존성 패키지

```bash
# 데이터 수집
pip install yt-dlp requests

# 전처리
pip install ultralytics opencv-python ffmpeg-python

# 학습
pip install scikit-learn torch numpy pandas

# 하이퍼파라미터 튜닝 (선택)
pip install optuna

# 시각화
pip install matplotlib

# GUI
pip install PyQt5
```

---

## 10. 구현 우선순위

### Phase A: 핵심 파이프라인 (pipeline/)
1. `config.py` - 설정 데이터클래스 정의
2. `data_ingest.py` - 데이터 수집 (YouTube + URL + 로컬)
3. `preprocessor.py` - 전처리 (YOLO → Feature/Sequence)
4. `trainer.py` - 학습 엔진 (RF + ST-GCN)
5. `auto_compare.py` - 자동 비교 트리거
6. `orchestrator.py` - 전체 오케스트레이션

### Phase B: GUI 통합 (gui/)
1. `training_page.py` - 메인 학습 페이지
2. `training_data_panel.py` - 데이터 소스 패널
3. `training_config_panel.py` - 학습 설정 패널
4. `training_progress_widget.py` - 진행 모니터
5. `training_results_viewer.py` - 결과 뷰어

### Phase C: 고급 기능
1. Optuna 하이퍼파라미터 자동 튜닝
2. 데이터 증강 (Data Augmentation)
3. 모델 앙상블 학습
4. 학습 이력 관리 및 버전 비교

---

## 11. 커맨드 라인 실행 (GUI 없이)

```bash
# 전체 파이프라인 실행
python -m pipeline.orchestrator \
    --data-dir ./dataset/raw_videos/ \
    --label-strategy folder \
    --train-rf --train-stgcn \
    --auto-compare

# 특정 스테이지만 실행
python -m pipeline.orchestrator \
    --stage preprocess \
    --data-dir ./dataset/raw_videos/

# 학습만 실행 (기존 데이터 사용)
python -m pipeline.orchestrator \
    --stage train \
    --train-stgcn \
    --epochs 100 \
    --auto-compare
```

---

**작성일:** 2026-02-05
**상태:** 설계 완료, 구현 대기
