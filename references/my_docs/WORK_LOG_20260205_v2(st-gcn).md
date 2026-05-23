# Home Safe Solution 개발 기록
## 2026-02-05 (수) - ST-GCN Pre-trained 모델 Fine-tuning 및 GUI 통합

---

## 📋 **작업 개요**

**목표:** 
1. ST-GCN Pre-trained 모델 Fine-tuning으로 정확도 향상
2. GUI에서 모델 정보 명시적 표시

**작업 시간:** 2026-02-05 전일

**결과:** ✅ 정확도 84.21% → 91.89% 향상 (+7.68%)

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

---

## 📂 **생성된 파일 목록**

### **Phase 1: Pre-trained 모델 적용**

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

### **2. 모델 구조 (Fine-tuned)**

```python
class STGCNFineTuned(nn.Module):
    """Fine-tuned ST-GCN 모델 구조"""
    
    # 레이어 명명: layers.0, layers.1, ... (기존과 다름!)
    # 기존 Original: st_gcn_networks.0, st_gcn_networks.1, ...
    
    def __init__(self):
        self.data_bn = nn.BatchNorm1d(...)
        self.layers = nn.ModuleList([
            STGCNBlock(3, 64, A, residual=False),
            STGCNBlock(64, 64, A),
            STGCNBlock(64, 64, A),
            STGCNBlock(64, 128, A, stride=2),
            STGCNBlock(128, 128, A),
            STGCNBlock(128, 128, A),
            STGCNBlock(128, 256, A, stride=2),
            STGCNBlock(256, 256, A),
            STGCNBlock(256, 256, A),
        ])
        self.fc = nn.Linear(256, 2)
```

### **3. 모델 구조 차이점**

| 항목 | Original | Fine-tuned |
|------|----------|------------|
| 레이어 이름 | `st_gcn_networks.X` | `layers.X` |
| BatchNorm | 없음 | `data_bn` |
| 체크포인트 형식 | 직접 | `{'state_dict': ...}` |
| 추론 모듈 | `stgcn_inference.py` | `stgcn_inference_finetuned.py` |

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

해결: Fine-tuned 모델 전용 추론 모듈 생성
- stgcn_inference_finetuned.py (새 파일)
```

---

## 📐 **GUI 개선 사항**

### **모델 선택 다이얼로그 (개선)**

```
┌─────────────────────────────────────────┐
│  🤖 낙상 감지 모델 선택                  │
├─────────────────────────────────────────┤
│  🌲 Random Forest         93.19%  ✅    │
│                                         │
│  ┌─ ST-GCN 모델 ──────────────────────┐ │
│  │ 📊 ST-GCN (Original)   84.21%  ✅  │ │
│  │ 🚀 ST-GCN (Fine-tuned) 91.89% ⭐권장│ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### **모델 정보 상단 바 (신규)**

```
🚀 모델: ST-GCN (Fine-tuned) │ 정확도: 91.89% │ ✅ 로드됨 │ 📁 best_model_finetuned.pth
```

### **모델별 아이콘**

| 모델 | 아이콘 | 의미 |
|------|--------|------|
| Random Forest | 🌲 | 전통적 ML |
| ST-GCN Original | 📊 | 기본 딥러닝 |
| ST-GCN Fine-tuned | 🚀 | 최적화된 딥러닝 |

---

## 📈 **최종 모델 성능 비교**

| 모델 | 정확도 | 추론 방식 | 지연시간 | 권장 |
|------|--------|----------|---------|------|
| Random Forest | **93.19%** | 프레임 단위 | 즉시 | ⭐ |
| ST-GCN Original | 84.21% | 60프레임 시퀀스 | ~2초 | |
| **ST-GCN Fine-tuned** | **91.89%** | 60프레임 시퀀스 | ~2초 | ⭐ |

**결론:** 
- 빠른 응답이 필요하면 → Random Forest (93.19%)
- 시계열 패턴 분석이 필요하면 → ST-GCN Fine-tuned (91.89%)

---

## 📁 **프로젝트 구조 (최종)**

```
/home/gjkong/dev_ws/st_gcn/
├── data/
│   └── binary/
│       ├── train_data.npy        # (174, 3, 60, 17, 1)
│       ├── train_labels.npy
│       ├── val_data.npy          # (37, 3, 60, 17, 1)
│       └── val_labels.npy
├── checkpoints/
│   └── best_model_binary.pth     # Original 모델 (84.21%)
├── checkpoints_finetuned/        # ⭐ 신규
│   ├── best_model_finetuned.pth  # Fine-tuned 모델 (91.89%)
│   └── final_model_finetuned.pth
├── pretrained/                   # ⭐ 신규
│   └── stgcn_ntu60_hrnet.pth     # PYSKL Pre-trained
├── download_pretrained.py        # ⭐ 신규
├── finetune_stgcn.py             # ⭐ 신규
├── test_stgcn_finetuned.py       # ⭐ 신규
└── stgcn_inference_finetuned.py  # ⭐ 신규

/home/gjkong/dev_ws/yolo/myproj/gui/
├── main.py
├── monitoring_page.py
├── model_selection_dialog.py     # 🔧 교체 필요
├── model_info_widget.py          # ⭐ 신규
├── stgcn_inference.py            # Original 모델용
├── stgcn_inference_finetuned.py  # ⭐ 신규 (Fine-tuned 모델용)
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
- [ ] monitoring_page.py 통합 (대기)
- [ ] 전체 GUI 테스트 (대기)

---

## 🚧 **남은 작업**

### 우선순위 높음
1. **GUI 통합 테스트**
   - `model_selection_dialog.py` 교체
   - `model_info_widget.py` 추가
   - `stgcn_inference_finetuned.py` 추가
   - `monitoring_page.py` 수정

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

### GUI 실행
```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui/
python main.py
```

---

## 📚 **참고 자료**

### 모델 경로
```
Original:    /home/gjkong/dev_ws/st_gcn/checkpoints/best_model_binary.pth
Fine-tuned:  /home/gjkong/dev_ws/st_gcn/checkpoints_finetuned/best_model_finetuned.pth
Pre-trained: /home/gjkong/dev_ws/st_gcn/pretrained/stgcn_ntu60_hrnet.pth
```

### 관련 문서
- `STGCN_PRETRAINED_PLAN.md` - Pre-trained 적용 계획
- `GUI_MODEL_DISPLAY_GUIDE.md` - GUI 통합 가이드

---

**작성자:** Claude (Anthropic AI Assistant)  
**작성일:** 2026-02-05  
**버전:** v3.1 (Pre-trained Fine-tuning)  
**상태:** Fine-tuning 완료, GUI 통합 대기
