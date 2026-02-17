# ST-GCN Pre-trained 모델 적용 계획

## 📋 현재 상황

| 항목 | 현재 값 |
|------|---------|
| 모델 | 직접 학습한 ST-GCN |
| 정확도 | 84.21% |
| 학습 데이터 | 174 샘플 (매우 적음) |
| Keypoints | COCO 17 (YOLO Pose) |
| 시퀀스 길이 | 60 frames |

---

## 🎯 목표

Pre-trained 모델의 강력한 특징 추출 능력을 활용하여 **정확도 90%+ 달성**

---

## 🔍 사용 가능한 Pre-trained 옵션

### Option 1: PYSKL ST-GCN++ (권장)
```
장점:
- HRNet 2D skeleton (COCO 17 keypoints와 유사)
- NTU RGB+D 60/120 클래스에서 학습 (대규모 데이터)
- 다양한 action에서 검증된 backbone
- 공식 지원 + 문서화 우수

단점:
- 60개 클래스 → 2개 클래스로 변환 필요
- 환경 설정 복잡

다운로드:
- https://download.openmmlab.com/mmaction/pyskl/
```

### Option 2: GajuuzZ Human-Falling-Detect-Tracks
```
장점:
- 이미 Fall Detection에 특화 (7개 액션)
- Le2i Fall Detection Dataset으로 학습
- 실제 낙상 데이터 사용

단점:
- AlphaPose 13 keypoints (COCO 17과 다름)
- 30 프레임 시퀀스 (우리는 60)
- keypoint 매핑 필요

모델: tsstg-model.pth
```

### Option 3: 공식 ST-GCN (Kinetics-skeleton)
```
장점:
- 원본 논문 구현
- 400개 action 클래스 학습

단점:
- OpenPose 18 keypoints (COCO 17과 다름)
- 오래된 PyTorch 버전 필요
```

---

## ✅ 선택: Option 1 - PYSKL 기반 Transfer Learning

### 이유:
1. **Keypoint 호환성**: HRNet 17 keypoints ≈ COCO 17 keypoints
2. **대규모 사전 학습**: NTU RGB+D (56,000+ 동영상)
3. **검증된 성능**: Top-1 Acc 90%+ (action recognition)
4. **유지보수**: OpenMMLab 공식 지원

---

## 📐 구현 계획

### Phase 1: PYSKL 환경 설정 (30분)
```bash
# 별도 conda 환경 생성
conda create -n pyskl python=3.10
conda activate pyskl

# PYSKL 설치
git clone https://github.com/kennymckormick/pyskl.git
cd pyskl
pip install -e .
```

### Phase 2: Pre-trained 모델 다운로드 (10분)
```bash
# ST-GCN++ NTU60 XSub 2D 모델 다운로드
wget https://download.openmmlab.com/mmaction/pyskl/ckpt/stgcnpp/stgcnpp_ntu60_xsub_hrnet/j.pth

# 또는 ST-GCN (더 가벼움)
wget https://download.openmmlab.com/mmaction/pyskl/ckpt/stgcn/stgcn_pyskl_ntu60_xsub_hrnet/j.pth
```

### Phase 3: 모델 구조 분석 및 변환 (1시간)
```python
# Pre-trained 체크포인트 분석
import torch
checkpoint = torch.load('j.pth')
print(checkpoint.keys())
print(checkpoint['state_dict'].keys())

# 마지막 FC layer 확인
# cls_head.fc_cls: (256, 60) → (256, 2) 로 변경
```

### Phase 4: Fine-tuning 스크립트 작성 (2시간)
```python
# 1. Pre-trained backbone 로드
# 2. FC layer를 2 클래스로 교체
# 3. backbone은 freeze 또는 낮은 learning rate
# 4. 우리 데이터로 fine-tuning
```

### Phase 5: 통합 테스트 (1시간)
```python
# 1. GUI에서 새 모델 테스트
# 2. 성능 비교 (기존 vs pre-trained)
# 3. 추론 속도 확인
```

---

## 🔧 핵심 코드 (예상)

### 1. Pre-trained 가중치 로드 + FC 교체
```python
import torch
import torch.nn as nn

# 기존 ST-GCN 모델 구조 로드
from stgcn.st_gcn import Model

# 모델 생성 (60 클래스로 초기화)
model = Model(num_class=60, num_point=17, num_person=1, 
              graph='coco', in_channels=3)

# Pre-trained 가중치 로드
checkpoint = torch.load('stgcn_ntu60_hrnet.pth', weights_only=False)
state_dict = checkpoint['state_dict']

# 'backbone.' prefix 제거 (PYSKL 형식)
new_state_dict = {}
for k, v in state_dict.items():
    if k.startswith('backbone.'):
        new_key = k.replace('backbone.', '')
        new_state_dict[new_key] = v

# Backbone만 로드 (FC layer 제외)
model_dict = model.state_dict()
pretrained_dict = {k: v for k, v in new_state_dict.items() 
                   if k in model_dict and 'fc' not in k}
model_dict.update(pretrained_dict)
model.load_state_dict(model_dict, strict=False)

# FC layer를 2 클래스로 교체
model.fc = nn.Linear(256, 2)
```

### 2. Fine-tuning 설정
```python
# Backbone freeze (선택적)
for name, param in model.named_parameters():
    if 'fc' not in name:
        param.requires_grad = False  # backbone 고정

# 또는 차등 learning rate
optimizer = torch.optim.Adam([
    {'params': model.fc.parameters(), 'lr': 1e-3},
    {'params': [p for n, p in model.named_parameters() if 'fc' not in n], 'lr': 1e-5}
])
```

---

## 📊 예상 결과

| 모델 | 정확도 | 비고 |
|------|--------|------|
| 현재 (scratch) | 84.21% | 174 샘플로 학습 |
| Pre-trained + Fine-tune | **90-95%** | Transfer learning |
| Pre-trained + Freeze backbone | 88-92% | FC만 학습 |

---

## ⚠️ 주의 사항

### 1. Keypoint 순서 확인
```
PYSKL HRNet:  0-nose, 1-left_eye, 2-right_eye, ...
YOLO COCO:    0-nose, 1-left_eye, 2-right_eye, ...
→ 동일한 순서! 별도 매핑 불필요
```

### 2. 입력 형식 확인
```
PYSKL: (N, C, T, V, M) = (batch, 3, frames, 17, 1)
우리:  (N, C, T, V, M) = (batch, 3, 60, 17, 1)
→ 호환!
```

### 3. 시퀀스 길이
```
PYSKL 기본: 100 frames (NTU RGB+D)
우리: 60 frames
→ 모델 구조는 동일, 입력만 다름 (문제 없음)
```

---

## 📅 일정

| 단계 | 예상 시간 | 설명 |
|------|----------|------|
| Phase 1 | 30분 | 환경 설정 |
| Phase 2 | 10분 | 모델 다운로드 |
| Phase 3 | 1시간 | 모델 분석/변환 |
| Phase 4 | 2시간 | Fine-tuning |
| Phase 5 | 1시간 | 통합 테스트 |
| **총계** | **~5시간** | |

---

## 🚀 시작하기

### Step 1: 현재 환경에서 PYSKL 모델만 다운로드
```bash
cd /home/gjkong/dev_ws/st_gcn/

# 디렉토리 생성
mkdir -p pretrained

# ST-GCN NTU60 HRNet (17 keypoints) 다운로드
cd pretrained
wget https://download.openmmlab.com/mmaction/pyskl/ckpt/stgcn/stgcn_pyskl_ntu60_xsub_hrnet/j.pth \
     -O stgcn_ntu60_hrnet.pth

# 또는 ST-GCN++ (더 좋은 성능)
wget https://download.openmmlab.com/mmaction/pyskl/ckpt/stgcnpp/stgcnpp_ntu60_xsub_hrnet/j.pth \
     -O stgcnpp_ntu60_hrnet.pth
```

### Step 2: 체크포인트 구조 분석
```python
import torch
ckpt = torch.load('pretrained/stgcn_ntu60_hrnet.pth', weights_only=False)
for k in ckpt['state_dict'].keys():
    print(k)
```

이후 단계는 분석 결과에 따라 진행합니다.

---

**작성일:** 2026-02-05  
**상태:** 계획 수립 완료, 실행 대기
