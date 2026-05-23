# 🔧 Home Safe Solution - 자동화 학습 파이프라인 설계안

## 설계 배경

**현재 환경:**
- Random Forest: sklearn 기반, 프레임 단위 feature 벡터 → 빠른 학습
- ST-GCN: PyTorch 기반, (N,3,60,17,1) 시퀀스 → GPU 학습
- 비교 스크립트: `compare_models.py` 이미 존재

**요구 사항:**
- 학습 + 하이퍼파라미터 튜닝 + 자동 비교 리포트
- CLI + YAML config 조합 실행 방식

---

## 📐 아키텍처 개요

```
pipeline/
├── configs/                    # YAML 설정 파일
│   ├── default.yaml            # 기본 설정 (전체)
│   ├── rf_tuning.yaml          # RF 전용 튜닝 설정
│   └── stgcn_tuning.yaml       # ST-GCN 전용 튜닝 설정
├── trainers/                   # 모델별 학습/튜닝 모듈
│   ├── __init__.py
│   ├── base_trainer.py         # 공통 인터페이스
│   ├── rf_trainer.py           # RF 학습 + GridSearch/Optuna
│   └── stgcn_trainer.py        # ST-GCN 학습 + Optuna
├── reports/                    # 비교 리포트 생성
│   ├── __init__.py
│   └── report_generator.py     # 자동 비교 리포트
├── run_pipeline.py             # CLI 진입점 (메인)
├── requirements.txt
└── README.md
```

---

## 📋 튜닝 방식 추천

### 왜 이렇게 나누는가?

| 모델 | 추천 튜닝 방식 | 이유 |
|------|--------------|------|
| 🌲 **Random Forest** | **Optuna** (RandomSearch 대체) | 탐색 공간이 넓고, 베이지안 최적화가 불필요한 조합을 빠르게 제거 |
| 🚀 **ST-GCN** | **Optuna** | epoch마다 pruning 가능 → 나쁜 조합 조기 종료, GPU 시간 절약 |

> **Optuna를 양쪽 모두에 사용하는 이유:**
> - 통일된 인터페이스 (코드 일관성)
> - 베이지안 최적화 → GridSearch보다 적은 trial로 더 좋은 결과
> - Pruning → ST-GCN에서 나쁜 조합 조기 종료 (GPU 시간 절약)
> - 시각화 내장 (파라미터 중요도, 최적화 히스토리)

---

## 📝 YAML Config 구조

### default.yaml (전체 파이프라인)

```yaml
# ===== 파이프라인 설정 =====
pipeline:
  name: "HomeSafe_AutoTrain"
  output_dir: "/home/gjkong/dev_ws/pipeline_results"
  models: ["random_forest", "stgcn_finetuned"]   # 실행할 모델 선택
  auto_report: true                                # 자동 비교 리포트
  seed: 42

# ===== Random Forest =====
random_forest:
  # 데이터 경로
  data:
    features: "/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/train_features.npy"
    labels: "/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/train_labels.npy"
    test_features: "/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/test_features.npy"
    test_labels: "/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/test_labels.npy"
  
  # 저장 경로
  output:
    model_path: "/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/random_forest_model.pkl"
    backup: true   # 기존 모델 백업 후 덮어쓰기
  
  # Optuna 튜닝 설정
  tuning:
    n_trials: 100           # 탐색 횟수
    cv_folds: 5             # Cross Validation
    scoring: "accuracy"     # 평가 지표
    timeout: 600            # 최대 시간(초) - 10분
    
    # 탐색 범위
    search_space:
      n_estimators: [50, 500]           # int range
      max_depth: [5, 50]                # int range (null 포함)
      min_samples_split: [2, 20]        # int range
      min_samples_leaf: [1, 10]         # int range
      max_features: ["sqrt", "log2"]    # categorical
      class_weight: ["balanced", null]  # categorical

# ===== ST-GCN =====
stgcn:
  # 데이터 경로
  data:
    train_data: "/home/gjkong/dev_ws/st_gcn/data/binary/train_data.npy"
    train_labels: "/home/gjkong/dev_ws/st_gcn/data/binary/train_labels.npy"
    val_data: "/home/gjkong/dev_ws/st_gcn/data/binary/val_data.npy"
    val_labels: "/home/gjkong/dev_ws/st_gcn/data/binary/val_labels.npy"
  
  # 저장 경로
  output:
    model_path: "/home/gjkong/dev_ws/st_gcn/checkpoints_finetuned/best_model_finetuned.pth"
    backup: true
  
  # Pre-trained 모델
  pretrained:
    path: "/home/gjkong/dev_ws/st_gcn/pretrained/stgcn_ntu60_hrnet.pth"
    use_pretrained: true
  
  # Optuna 튜닝 설정
  tuning:
    n_trials: 30            # 탐색 횟수 (GPU 고려)
    max_epochs: 50          # 최대 epoch
    pruning: true           # 조기 종료
    pruning_warmup: 10      # 10 epoch 이후부터 pruning
    timeout: 3600           # 최대 시간(초) - 1시간
    
    # 탐색 범위
    search_space:
      learning_rate_backbone: [1.0e-6, 1.0e-4]   # log scale
      learning_rate_head: [1.0e-4, 1.0e-2]        # log scale
      batch_size: [8, 16, 32]                      # categorical
      weight_decay: [1.0e-5, 1.0e-3]              # log scale
      dropout: [0.0, 0.5]                          # float range
      scheduler: ["cosine", "step", "plateau"]     # categorical

# ===== 비교 리포트 =====
report:
  output_dir: "/home/gjkong/dev_ws/yolo/myproj/scripts/admin/Model_Compare_Report"
  include:
    - confusion_matrix
    - roc_curve
    - inference_time
    - model_size
    - hyperparameter_importance    # Optuna 파라미터 중요도
    - optimization_history         # Optuna 최적화 히스토리
```

---

## 🔄 파이프라인 실행 흐름

```
                    ┌─────────────────┐
                    │  run_pipeline.py │  ← CLI 진입점
                    │  (YAML 로드)     │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
    ┌───────────────────┐     ┌───────────────────┐
    │  RF Trainer        │     │  ST-GCN Trainer    │
    │                   │     │                   │
    │  1. 데이터 로드    │     │  1. 데이터 로드    │
    │  2. Optuna 튜닝   │     │  2. Optuna 튜닝   │
    │     - n_trials회   │     │     - n_trials회   │
    │     - CV 5-fold    │     │     - pruning      │
    │  3. Best 파라미터  │     │  3. Best 파라미터  │
    │  4. 최종 학습      │     │  4. 최종 학습      │
    │  5. 모델 저장      │     │  5. 모델 저장      │
    └────────┬──────────┘     └────────┬──────────┘
             │                         │
             └────────────┬────────────┘
                          ▼
              ┌───────────────────────┐
              │  Report Generator     │
              │                       │
              │  1. 모델별 테스트     │
              │  2. 성능 비교 차트    │
              │  3. 리포트 생성(.md)  │
              │  4. Optuna 시각화     │
              └───────────────────────┘
```

---

## 💻 CLI 사용법

```bash
# 전체 파이프라인 실행 (기본 config)
python run_pipeline.py

# 특정 config 지정
python run_pipeline.py --config configs/default.yaml

# RF만 튜닝
python run_pipeline.py --model random_forest

# ST-GCN만 튜닝
python run_pipeline.py --model stgcn_finetuned

# 튜닝 없이 현재 모델로 비교 리포트만
python run_pipeline.py --report-only

# trial 수 오버라이드
python run_pipeline.py --rf-trials 200 --stgcn-trials 50

# dry-run (설정 확인만)
python run_pipeline.py --dry-run
```

---

## 📊 출력 구조

```
pipeline_results/
└── 20260206_143022/                    # 타임스탬프 폴더
    ├── pipeline_log.txt                # 전체 실행 로그
    ├── random_forest/
    │   ├── optuna_study.db             # Optuna 결과 DB
    │   ├── best_params.json            # 최적 하이퍼파라미터
    │   ├── best_model.pkl              # 최적 모델
    │   ├── param_importance.png        # 파라미터 중요도
    │   └── optimization_history.png    # 최적화 히스토리
    ├── stgcn_finetuned/
    │   ├── optuna_study.db
    │   ├── best_params.json
    │   ├── best_model.pth
    │   ├── training_curve.png          # 학습 곡선
    │   ├── param_importance.png
    │   └── optimization_history.png
    └── comparison_report/
        ├── MODEL_COMPARISON_REPORT.md  # 종합 보고서
        ├── dashboard_comparison.png
        ├── confusion_matrices.png
        ├── roc_curves.png
        ├── inference_time.png
        └── model_size.png
```

---

## 🔑 핵심 구현 포인트

### 1. RF Optuna Objective 함수

```python
def rf_objective(trial, X, y, cv_folds):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 50, 500),
        'max_depth': trial.suggest_int('max_depth', 5, 50),
        'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
        'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2']),
        'class_weight': trial.suggest_categorical('class_weight', ['balanced', None]),
    }
    
    model = RandomForestClassifier(**params, random_state=42, n_jobs=-1)
    scores = cross_val_score(model, X, y, cv=cv_folds, scoring='accuracy')
    return scores.mean()
```

### 2. ST-GCN Optuna Objective + Pruning

```python
def stgcn_objective(trial, train_loader, val_loader, config):
    lr_backbone = trial.suggest_float('lr_backbone', 1e-6, 1e-4, log=True)
    lr_head = trial.suggest_float('lr_head', 1e-4, 1e-2, log=True)
    batch_size = trial.suggest_categorical('batch_size', [8, 16, 32])
    weight_decay = trial.suggest_float('weight_decay', 1e-5, 1e-3, log=True)
    dropout = trial.suggest_float('dropout', 0.0, 0.5)
    
    model = build_stgcn_model(dropout=dropout)
    # ... 학습 루프 ...
    
    for epoch in range(max_epochs):
        train_loss = train_one_epoch(model, train_loader)
        val_acc = evaluate(model, val_loader)
        
        # Optuna pruning (나쁜 조합 조기 종료)
        trial.report(val_acc, epoch)
        if trial.should_prune():
            raise optuna.TrialPruned()
    
    return best_val_acc
```

### 3. 모델 백업 전략

```python
# 기존 모델 자동 백업 후 교체
# random_forest_model.pkl → random_forest_model_backup_20260206.pkl
# best_model_finetuned.pth → best_model_finetuned_backup_20260206.pth
```

---

## ⚙️ 필요 패키지

```bash
pip install optuna optuna-dashboard   # 튜닝 엔진 + 웹 대시보드
pip install pyyaml                     # YAML config
pip install scikit-learn numpy torch   # 이미 설치됨
pip install matplotlib plotly          # 시각화
```

### (선택) Optuna Dashboard로 실시간 모니터링
```bash
# 튜닝 중 브라우저에서 실시간 확인
optuna-dashboard sqlite:///pipeline_results/20260206_143022/random_forest/optuna_study.db
```

---

## 📅 구현 우선순위

| 순서 | 항목 | 예상 시간 |
|------|------|----------|
| 1 | 프로젝트 구조 + YAML config | 30분 |
| 2 | base_trainer.py (공통 인터페이스) | 20분 |
| 3 | rf_trainer.py (RF + Optuna) | 40분 |
| 4 | stgcn_trainer.py (ST-GCN + Optuna + Pruning) | 1시간 |
| 5 | report_generator.py (기존 compare_models.py 연동) | 30분 |
| 6 | run_pipeline.py (CLI 진입점) | 30분 |
| 7 | 테스트 + 디버깅 | 30분 |

**총 예상: ~3.5시간**

---

**작성일:** 2026-02-05
**상태:** 설계안 (구현 대기)
