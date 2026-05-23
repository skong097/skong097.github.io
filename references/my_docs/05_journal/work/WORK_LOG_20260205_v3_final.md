# Home Safe Solution 개발 기록
## 2026-02-05 (수) - ST-GCN Fine-tuning + GUI 통합 + 단일 대상자 추적

---

## 📋 **작업 개요**

**목표:**
1. ST-GCN Pre-trained 모델 Fine-tuning으로 정확도 향상
2. GUI에서 모델 정보 명시적 표시
3. 3모델 성능 비교 스크립트 완성
4. 실시간 탐지 시 단일 대상자 추적 통합

**작업 시간:** 2026-02-05 전일

**결과:**
- ✅ ST-GCN 정확도 84.21% → 91.89% 향상 (+7.68%)
- ✅ GUI 모델 선택 다이얼로그 개선 (3가지 옵션)
- ✅ 3모델 비교 스크립트(compare_models.py) 완성
- ✅ 단일 대상자 추적 기능 monitoring_page.py 통합

---

## 🎯 **주요 성과**

### **1. Pre-trained 모델 Fine-tuning** ✅

| 항목 | Before | After | 변화 |
|------|--------|-------|------|
| **Val Accuracy** | 84.21% | **91.89%** | **+7.68%** |
| Train Accuracy | 81.08% | 97.13% | +16.05% |
| Best Epoch | - | 17/50 | - |

### **2. GUI 모델 정보 표시** ✅
- 모델 선택 다이얼로그 개선 (3가지 옵션)
- 상단 바에 현재 모델 정보 표시
- 모델별 아이콘 구분 (🌲 RF, 📊 Original, 🚀 Fine-tuned)

### **3. 3모델 성능 비교 스크립트** ✅
- `compare_models.py` 완성
- RF / ST-GCN Original / ST-GCN Fine-tuned 각 고유 파이프라인 사용
- 자동 리포트 생성 (대시보드, Confusion Matrix, ROC, 추론 속도, 모델 크기)

### **4. 단일 대상자 추적 (select_target_person)** ✅
- `monitoring_page.py`에 `select_target_person` 활성화
- 다중 객체 감지 시 가장 큰 Bounding Box 1명만 추적
- Skeleton 및 낙상 감지 모두 대상자 1명에 집중

---

## 📂 **생성/수정된 파일 목록**

### **Phase 1: Pre-trained 모델 Fine-tuning**

| 파일 | 위치 | 설명 |
|------|------|------|
| `STGCN_PRETRAINED_PLAN.md` | `/home/gjkong/dev_ws/st_gcn/` | 적용 계획서 |
| `download_pretrained.py` | `/home/gjkong/dev_ws/st_gcn/` | 모델 다운로드 스크립트 |
| `finetune_stgcn.py` | `/home/gjkong/dev_ws/st_gcn/` | Fine-tuning 학습 스크립트 |
| `best_model_finetuned.pth` | `checkpoints_finetuned/` | Fine-tuned 모델 가중치 |

### **Phase 2: Fine-tuned 모델 추론**

| 파일 | 위치 | 설명 |
|------|------|------|
| `stgcn_inference_finetuned.py` | GUI 폴더 | Fine-tuned 모델 추론 모듈 |
| `test_stgcn_finetuned.py` | `/home/gjkong/dev_ws/st_gcn/` | 테스트 스크립트 |

### **Phase 3: GUI 모델 표시**

| 파일 | 위치 | 설명 |
|------|------|------|
| `model_selection_dialog_v2.py` | GUI 폴더 | 개선된 모델 선택 다이얼로그 |
| `model_info_widget.py` | GUI 폴더 | 모델 정보 표시 위젯 |
| `GUI_MODEL_DISPLAY_GUIDE.md` | - | GUI 통합 가이드 |

### **Phase 4: 모델 성능 비교**

| 파일 | 위치 | 설명 |
|------|------|------|
| `compare_models.py` | `/home/gjkong/dev_ws/st_gcn/` | 3모델 성능 비교 스크립트 |
| `COMPARE_MODELS_GUIDE.md` | `/home/gjkong/dev_ws/st_gcn/` | 비교 실행 가이드 |

### **Phase 5: 단일 대상자 추적 통합**

| 파일 | 위치 | 설명 |
|------|------|------|
| `monitoring_page.py` | GUI 폴더 | ⭐ 수정 - 단일 대상자 추적 통합 |
| `person_selection_helper.py` | GUI 폴더 | 참고용 헬퍼 (메서드는 클래스 내장) |

---

## 🔧 **기술 상세**

### **1. Fine-tuning 전략**

```python
# 차등 Learning Rate
optimizer = AdamW([
    {'params': backbone_params, 'lr': 1e-5},   # backbone: 낮은 lr
    {'params': head_params, 'lr': 1e-3}        # FC head: 높은 lr
])

# 학습 설정
epochs = 50
batch_size = 16
weight_decay = 1e-4
scheduler = CosineAnnealingLR
```

### **2. 모델 구조 차이점**

| 항목 | Original | Fine-tuned |
|------|----------|------------|
| 레이어 이름 | `st_gcn_networks.X` | `layers.X` |
| BatchNorm | 없음 | `data_bn` |
| 체크포인트 형식 | 직접 | `{'state_dict': ...}` |
| 추론 모듈 | `stgcn_inference.py` | `stgcn_inference_finetuned.py` |

### **3. 단일 대상자 추적 - monitoring_page.py 수정 내용**

**수정 포인트 (update_frame 메서드 내 3곳):**

| 수정 | Before (롤백 상태) | After (통합 완료) |
|------|-------------------|------------------|
| 대상자 선택 | `select_target_person` 주석 처리 | ✅ 활성화 `method='largest'` |
| 키포인트 | `keypoints[0]` 고정 (첫 번째 사람) | `keypoints_all[target_idx]` (대상자) |
| Skeleton | 전체 감지된 사람 그리기 | 대상자 1명만 그리기 |

**동작 흐름:**
```
YOLO 추론 → N명 감지
  ↓
select_target_person(method='largest') → 가장 큰 BBox 1명 선택
  ↓
target_keypoints만 필터링 → skeleton 1명만 그리기
  ↓
RF 또는 ST-GCN → 대상자 1명만 낙상 감지
```

**선택 방법 옵션 (select_target_person 메서드):**

| method | 설명 | 용도 |
|--------|------|------|
| `largest` | 가장 큰 BBox 면적 | **기본값, 추천** |
| `center` | 화면 중앙 최근접 | 고정 카메라 |
| `combined` | 면적 60% + 중앙 40% | 혼합 환경 |

### **4. 모델 비교 스크립트 설계**

각 모델의 **고유 테스트 파이프라인**을 존중하여 공정 비교:

| 모델 | 입력 형태 | 추론 방식 | 테스트 데이터 |
|------|----------|----------|-------------|
| 🌲 Random Forest | feature 벡터 | 프레임 단위 → 다수결 | RF 전용 test set |
| 📊 ST-GCN Original | (N,3,60,17,1) | 60프레임 시퀀스 배치 | val_data.npy |
| 🚀 ST-GCN Fine-tuned | (N,3,60,17,1) | 60프레임 시퀀스 배치 | val_data.npy |

**출력 결과:**
```
~/dev_ws/yolo/myproj/scripts/admin/Model_Compare_Report/
└── 20260205_HHMMSS/
    ├── MODEL_COMPARISON_REPORT.md   # 종합 보고서
    ├── dashboard_comparison.png     # 종합 대시보드
    ├── confusion_matrices.png       # Confusion Matrix
    ├── roc_curves.png               # ROC Curve / AUC
    ├── inference_time.png           # 추론 속도 비교
    └── model_size.png               # 모델 크기/파라미터
```

---

## 📊 **Fine-tuning 학습 로그**

```
============================================================
ST-GCN Fine-tuning for Fall Detection
============================================================

[Device] cuda
[Dataset] Train: 174 samples, Val: 37 samples

------------------------------------------------------------
Epoch | Train Loss |  Train Acc |   Val Loss |    Val Acc
------------------------------------------------------------
    1 |     0.5722 |     78.74% |     0.5443 |     78.38%
    6 |     0.4542 |     79.31% |     0.3444 |     86.49%  [BEST]
    8 |     0.3771 |     87.36% |     0.2814 |     89.19%  [BEST]
   17 |     0.2560 |     90.23% |     0.2184 |     91.89%  [BEST] ⭐
   25 |     0.1750 |     94.83% |     0.2755 |     86.49%
   50 |     0.1551 |     93.68% |     0.2490 |     89.19%
------------------------------------------------------------

[Result]
  Best Epoch: 17
  Best Val Acc: 91.89%
```

---

## 🐛 **해결된 문제**

### **Issue 1: 데이터 파일명 불일치**
```
FileNotFoundError: train_label.npy
해결: train_labels.npy (복수형)으로 수정
```

### **Issue 2: Pre-trained 가중치 매칭률 낮음**
```
Matched layers: 5/156
원인: PYSKL 모델 구조와 우리 모델 구조 다름
결과: 그래도 91.89% 달성 (대부분 FC head 학습 효과)
```

### **Issue 3: 모델 구조 불일치**
```
Missing key(s): "st_gcn_networks.0.gcn.conv.weight"...
Unexpected key(s): "layers.0.gcn.0.weight"...
해결: Fine-tuned 모델 전용 추론 모듈 생성 (stgcn_inference_finetuned.py)
```

### **Issue 4: 단일 대상자 추적 롤백**
```
원인: 이전 작업 시 적용했으나 다른 기능 수정 과정에서 롤백됨
해결: select_target_person 활성화 + 데이터 흐름을 단일 대상자로 통일
수정 파일: monitoring_page.py (update_frame 메서드)
```

---

## 📈 **최종 모델 성능 비교**

| 모델 | 정확도 | 추론 방식 | 지연시간 | 권장 |
|------|--------|----------|---------|------|
| 🌲 Random Forest | **93.19%** | 프레임 단위 | 즉시 | ⭐ |
| 📊 ST-GCN Original | 84.21% | 60프레임 시퀀스 | ~2초 | |
| 🚀 ST-GCN Fine-tuned | **91.89%** | 60프레임 시퀀스 | ~2초 | ⭐ |

**결론:**
- 빠른 응답이 필요하면 → Random Forest (93.19%)
- 시계열 패턴 분석이 필요하면 → ST-GCN Fine-tuned (91.89%)

---

## 📁 **프로젝트 구조 (최종)**

```
/home/gjkong/dev_ws/st_gcn/
├── data/binary/
│   ├── train_data.npy        # (174, 3, 60, 17, 1)
│   ├── train_labels.npy
│   ├── val_data.npy          # (37, 3, 60, 17, 1)
│   └── val_labels.npy
├── checkpoints/
│   └── best_model_binary.pth     # Original 모델 (84.21%)
├── checkpoints_finetuned/
│   ├── best_model_finetuned.pth  # Fine-tuned 모델 (91.89%)
│   └── final_model_finetuned.pth
├── pretrained/
│   └── stgcn_ntu60_hrnet.pth     # PYSKL Pre-trained
├── download_pretrained.py
├── finetune_stgcn.py
├── test_stgcn_finetuned.py
├── compare_models.py             # ⭐ 3모델 비교 스크립트
└── COMPARE_MODELS_GUIDE.md       # ⭐ 비교 실행 가이드

/home/gjkong/dev_ws/yolo/myproj/gui/
├── main.py
├── monitoring_page.py            # ⭐ 수정 - 단일 대상자 추적 통합
├── model_selection_dialog.py     # 🔧 교체 필요
├── model_info_widget.py          # ⭐ 신규
├── person_selection_helper.py    # 참고용 헬퍼
├── stgcn_inference.py            # Original 모델용
├── stgcn_inference_finetuned.py  # Fine-tuned 모델용
└── stgcn/
    ├── __init__.py
    ├── st_gcn.py
    └── graph.py
```

---

## ✅ **완료 체크리스트**

### Pre-trained 모델 적용
- [x] PYSKL 모델 조사 및 선택
- [x] 다운로드 스크립트 작성
- [x] Fine-tuning 스크립트 작성
- [x] Fine-tuning 실행 (91.89% 달성)
- [x] 모델 구조 불일치 해결

### GUI 통합
- [x] Fine-tuned 추론 모듈 작성
- [x] 모델 선택 다이얼로그 개선
- [x] 모델 정보 표시 위젯 작성
- [x] 통합 가이드 작성
- [ ] monitoring_page.py GUI 위젯 통합 (대기)
- [ ] 전체 GUI 테스트 (대기)

### 모델 성능 비교
- [x] compare_models.py 작성
- [x] 각 모델 고유 파이프라인 구현
- [x] 자동 리포트 생성 기능
- [x] COMPARE_MODELS_GUIDE.md 작성

### 단일 대상자 추적
- [x] select_target_person 메서드 활성화
- [x] update_frame 데이터 흐름 수정 (단일 대상자)
- [x] Skeleton 그리기 1명으로 제한
- [x] RF / ST-GCN 모두 대상자 키포인트 사용
- [x] 다중 감지 시 로그 메시지 개선

---

## 🚧 **남은 작업**

### 우선순위 높음
1. **GUI 위젯 통합 테스트**
   - `model_selection_dialog.py` 교체
   - `model_info_widget.py` 추가
   - `monitoring_page.py` 교체 (단일 대상자 추적 버전)
   - 전체 동작 확인

### 우선순위 중간
2. **모델 앙상블** (RF + ST-GCN 결합)
3. **실시간 모델 전환** 기능

### 우선순위 낮음
4. **더 많은 데이터로 재학습**
5. **PYSKL 모델 구조 직접 사용** (매칭률 개선)

---

## 📝 **커맨드 요약**

### Fine-tuning 실행
```bash
cd /home/gjkong/dev_ws/st_gcn/
python finetune_stgcn.py --epochs 50 --batch-size 16
```

### Fine-tuned 모델 테스트
```bash
cd /home/gjkong/dev_ws/st_gcn/
python test_stgcn_finetuned.py \
    --video data_integrated/fall-01-cam0.mp4 \
    --model checkpoints_finetuned/best_model_finetuned.pth
```

### 모델 비교 실행
```bash
cd /home/gjkong/dev_ws/st_gcn/
python compare_models.py
```

### GUI 실행
```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui/
python main.py
```

---

## 📚 **참고 자료**

### 모델 경로
```
RF:          /home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/random_forest_model.pkl
Original:    /home/gjkong/dev_ws/st_gcn/checkpoints/best_model_binary.pth
Fine-tuned:  /home/gjkong/dev_ws/st_gcn/checkpoints_finetuned/best_model_finetuned.pth
Pre-trained: /home/gjkong/dev_ws/st_gcn/pretrained/stgcn_ntu60_hrnet.pth
```

### 관련 문서
- `STGCN_PRETRAINED_PLAN.md` - Pre-trained 적용 계획
- `GUI_MODEL_DISPLAY_GUIDE.md` - GUI 통합 가이드
- `COMPARE_MODELS_GUIDE.md` - 모델 비교 실행 가이드
- `WORK_LOG_20260205_v2(st-gcn).md` - 이전 버전 작업 기록

---

**작성자:** Claude (Anthropic AI Assistant)
**작성일:** 2026-02-05
**버전:** v3 (Final - Fine-tuning + 비교 스크립트 + 단일 대상자 추적)
**상태:** Fine-tuning 완료, 비교 스크립트 완료, 단일 대상자 추적 통합 완료, GUI 위젯 통합 테스트 대기
