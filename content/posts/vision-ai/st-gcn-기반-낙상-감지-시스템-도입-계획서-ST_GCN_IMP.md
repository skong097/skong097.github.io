---
title: "ST-GCN 기반 낙상 감지 시스템 도입 계획서"
date: 2026-03-21
draft: true
tags: ["vision-ai", "yolo"]
categories: ["vision-ai"]
description: "**프로젝트명:** Home Safe Solution - ST-GCN 버전 **작성일:** 2026-02-03 **작성자:** Stephen Kong"
---

# ST-GCN 기반 낙상 감지 시스템 도입 계획서

**프로젝트명:** Home Safe Solution - ST-GCN 버전  
**작성일:** 2026-02-03  
**작성자:** Stephen Kong  
**프로젝트 경로:** `/home/gjkong/dev_ws/st_gcn`  
**기존 프로젝트:** `/home/gjkong/dev_ws/yolo/myproj` (유지)

---

## 📋 목차

1. [개요](#1-개요)
2. [ST-GCN 기술 검토](#2-st-gcn-기술-검토)
3. [기존 데이터 활용 가능성](#3-기존-데이터-활용-가능성)
4. [시스템 아키텍처](#4-시스템-아키텍처)
5. [작업 계획](#5-작업-계획)
6. [디렉토리 구조](#6-디렉토리-구조)
7. [구현 로드맵](#7-구현-로드맵)
8. [리스크 및 대응](#8-리스크-및-대응)
9. [성능 비교 계획](#9-성능-비교-계획)
10. [의사결정 가이드](#10-의사결정-가이드)

---

## 1. 개요

### 1.1 목적

**현재 시스템 (Random Forest) 한계 극복:**
- Falling 감지율 76.6% (개선 필요)
- Frame 단위 독립 예측 (시간적 맥락 부족)
- 수동 Feature Engineering (181개)

**ST-GCN 도입으로 기대 효과:**
- Falling 85%+ 감지 (시간적 패턴 학습)
- End-to-End 학습 (자동 Feature 추출)
- 시공간 관계 모델링

### 1.2 현재 시스템 상태

```yaml
프로젝트: /home/gjkong/dev_ws/yolo/myproj
모델: Random Forest (181 features)
데이터: 70개 비디오
  - 정상 (ADL): 40개
  - 낙상: 30개
성능:
  - Overall: 93.19%
  - Normal: 98.5%
  - Falling: 76.6% ⚠️
  - Fallen: 92.1%
GUI: PyQt6 (작동 중)
DB: MySQL (연동 완료)
```

### 1.3 ST-GCN 프로젝트 목표

```yaml
프로젝트: /home/gjkong/dev_ws/st_gcn (신규)
모델: ST-GCN (Spatial Temporal GCN)
데이터: 기존 70개 활용 + 증강
목표 성능:
  - Overall: 94%+
  - Normal: 98%+
  - Falling: 85%+ ⭐
  - Fallen: 93%+
GUI: 기존 GUI 재활용 (모델만 교체)
DB: 기존 DB 활용
```

---

## 2. ST-GCN 기술 검토

### 2.1 ST-GCN이란?

**Spatial Temporal Graph Convolutional Network**

```
개념:
- 인체 Skeleton을 그래프로 모델링
- 관절(Joint) = Node
- 뼈(Bone) = Edge
- 시공간 합성곱으로 행동 인식

입력: Skeleton 시퀀스 (N, C, T, V, M)
  N: Batch size
  C: Channels (x, y, confidence)
  T: Time frames (30-60)
  V: Vertices (17 keypoints)
  M: Number of people (1)

출력: 행동 클래스 (Normal/Falling/Fallen)
```

### 2.2 핵심 원리

#### Spatial Graph Convolution
```python
# 관절 간 공간적 관계
nose → shoulders → elbows → wrists
hips → knees → ankles

# 그래프 구조
A = Adjacency Matrix (17×17)
  A[i,j] = 1 if joint i and j are connected
  A[i,j] = 0 otherwise
```

#### Temporal Convolution
```python
# 시간에 따른 움직임 패턴
Frame t → Frame t+1 → Frame t+2
  
# 낙상 시퀀스 예시
Standing → Falling → Fallen
 (정상)     (낙상중)   (쓰러짐)
```

### 2.3 Random Forest vs ST-GCN

| 항목 | Random Forest | ST-GCN |
|------|--------------|--------|
| **입력** | 181 features (수동) | Raw Skeleton (17×T) |
| **시간 정보** | Rolling window (5-10) | 전체 시퀀스 (30-60) |
| **공간 관계** | 수동 계산 (각도, 거리) | 그래프 구조 (자동) |
| **학습 방식** | 통계적 분류 | 딥러닝 (CNN) |
| **Feature** | 수동 설계 필수 | 자동 학습 |
| **Falling 감지** | 76.6% | 85%+ (예상) |
| **학습 시간** | 10분 | 1-3시간 |
| **추론 시간** | 10ms/frame | 30ms/frame |
| **모델 크기** | 2MB | 50-100MB |
| **데이터 요구** | 50+ 비디오 | 200+ 비디오 (권장) |

---

## 3. 기존 데이터 활용 가능성

### 3.1 사용 가능한 데이터

#### ✅ Skeleton 데이터 (완벽!)
```bash
위치: /home/gjkong/dev_ws/yolo/myproj/skeleton_integrated/

파일: fall-01-skeleton.csv ~ fall-70-skeleton.csv

형식:
  - frame_id
  - timestamp_ms
  - 17 keypoints × 3 (x, y, confidence)
    - nose, left_eye, right_eye, left_ear, right_ear
    - left_shoulder, right_shoulder
    - left_elbow, right_elbow
    - left_wrist, right_wrist
    - left_hip, right_hip
    - left_knee, right_knee
    - left_ankle, right_ankle
  - acc_x, acc_y, acc_z, acc_mag

총 프레임: 10,420개
총 비디오: 70개
```

**ST-GCN 입력으로 완벽하게 활용 가능!** ✅

#### ✅ 라벨 데이터
```bash
위치: /home/gjkong/dev_ws/yolo/myproj/labeled_integrated/

파일: fall-01-labeled.csv ~ fall-70-labeled.csv

라벨:
  - label_3class: 0 (Normal), 1 (Falling), 2 (Fallen)
  - label_binary: 0 (Normal), 1 (Fall)

분포:
  - Normal:  5,906 프레임 (56.7%)
  - Falling: 1,708 프레임 (16.4%)
  - Fallen:  2,806 프레임 (26.9%)
```

#### ✅ 원본 비디오 (선택적)
```bash
위치: /home/gjkong/dev_ws/yolo/myproj/data_integrated/

파일: fall-01-cam0.mp4 ~ fall-70-cam0.mp4

용도:
  - 데이터 증강 (필요시 추가 추출)
  - 검증용
  - 시각화
```

### 3.2 데이터 변환 필요 사항

#### CSV → NumPy Array
```python
# 현재: CSV 파일 (70개)
fall-01-skeleton.csv
  frame_id, x_0, y_0, conf_0, ..., x_16, y_16, conf_16

# 변환 → NumPy Array
shape: (N, C, T, V, M)
  N: 70 samples
  C: 3 (x, y, confidence)
  T: 30-60 frames (시퀀스 길이 통일)
  V: 17 keypoints
  M: 1 person

예시:
  video_1: (3, 45, 17, 1)  # 45 프레임
  video_2: (3, 52, 17, 1)  # 52 프레임
  → Padding/Truncate → (3, 60, 17, 1)
```

#### 시퀀스 분할
```python
# 긴 비디오를 고정 길이 시퀀스로 분할

원본: 300 프레임 (15초 @ 20 FPS)
분할: 60 프레임씩 슬라이딩 윈도우
  - Seq 1: Frame 0-59
  - Seq 2: Frame 30-89 (stride=30)
  - Seq 3: Frame 60-119
  ...

효과: 70 비디오 → 200-300 시퀀스 (증강)
```

### 3.3 데이터 부족 문제 대응

#### 현재 데이터: 70개 (부족)
- ST-GCN 권장: 200-500개
- 현재: 70개 ⚠️

#### 해결 방안

**방법 1: 시간 증강 (추천!) ⭐**
```python
# 슬라이딩 윈도우
70 비디오 × 5 시퀀스 = 350 샘플

# 시간 축 변환
- 속도 변화: 0.8x, 1.0x, 1.2x
- 70 × 3 = 210 샘플

# 조합
70 비디오 → 350-500 시퀀스
```

**방법 2: 공간 증강**
```python
# Skeleton 변형
- Jittering: 약간의 노이즈 추가
- Scaling: 크기 변화
- Rotation: 약간 회전
- Flipping: 좌우 반전

# 증강 배수: 2-3배
70 × 2 = 140 샘플
```

**방법 3: 추가 데이터 수집**
```python
# UR Fall Dataset에서 추가
- 낙상: +30개
- 정상: +30개
→ 총 130개

# 공개 데이터셋
- NTU RGB+D (Skeleton 포함)
- HMDB51
→ 전이 학습 가능
```

---

## 4. 시스템 아키텍처

### 4.1 전체 구조

```
┌─────────────────────────────────────────────────────────┐
│                    기존 시스템 (유지)                      │
│  /home/gjkong/dev_ws/yolo/myproj                        │
│  - Random Forest 모델                                    │
│  - GUI (PyQt6)                                          │
│  - DB (MySQL)                                           │
│  - 운영 중 ✅                                            │
└─────────────────────────────────────────────────────────┘
                            ↓
              데이터 공유 (Skeleton, Labels)
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  ST-GCN 시스템 (신규)                     │
│  /home/gjkong/dev_ws/st_gcn                             │
│  - ST-GCN 모델 개발                                      │
│  - 학습 및 검증                                          │
│  - 성능 비교                                             │
│  - A/B 테스트 준비                                       │
└─────────────────────────────────────────────────────────┘
                            ↓
              성능 검증 후 통합 결정
                            ↓
┌─────────────────────────────────────────────────────────┐
│               최종 시스템 (통합 또는 선택)                  │
│  - Random Forest 유지 OR                                │
│  - ST-GCN으로 교체 OR                                   │
│  - 앙상블 (두 모델 조합)                                  │
└─────────────────────────────────────────────────────────┘
```

### 4.2 데이터 파이프라인

```python
# Phase 1: 데이터 준비
기존 Skeleton CSV (70개)
      ↓
시퀀스 변환 (NumPy)
      ↓
데이터 증강 (350개)
      ↓
Train/Val/Test 분할 (70/15/15%)
      ↓
ST-GCN 학습

# Phase 2: 학습
ST-GCN 네트워크
      ↓
Loss: CrossEntropy
Optimizer: Adam
      ↓
Epochs: 50-100
      ↓
Best Model 저장

# Phase 3: 평가
Test Set 평가
      ↓
성능 비교 (vs Random Forest)
      ↓
오류 분석
      ↓
개선 또는 배포 결정

# Phase 4: 통합
GUI 모델 교체
      ↓
실시간 테스트
      ↓
A/B 테스트
      ↓
최종 배포
```

---

## 5. 작업 계획

### Phase 0: 환경 구축 (1일)

#### 작업 내용
```bash
# 1. 프로젝트 디렉토리 생성
mkdir -p /home/gjkong/dev_ws/st_gcn
cd /home/gjkong/dev_ws/st_gcn

# 2. 가상환경 생성
python3 -m venv st_gcn_venv
source st_gcn_venv/bin/activate

# 3. 필수 패키지 설치
pip install torch torchvision
pip install numpy pandas scikit-learn
pip install matplotlib seaborn
pip install opencv-python
pip install pyyaml tensorboard

# 4. ST-GCN 라이브러리
git clone https://github.com/yysijie/st-gcn.git
# 또는 직접 구현

# 5. 디렉토리 구조 생성
```

#### 체크리스트
- [ ] 프로젝트 디렉토리 생성
- [ ] Python 가상환경 구성
- [ ] PyTorch 설치 (GPU 확인)
- [ ] ST-GCN 라이브러리 준비
- [ ] Git 초기화

---

### Phase 1: 데이터 준비 (2-3일)

#### 작업 1.1: 데이터 복사 및 링크
```bash
# 기존 데이터 심볼릭 링크
ln -s /home/gjkong/dev_ws/yolo/myproj/skeleton_integrated data/skeleton_raw
ln -s /home/gjkong/dev_ws/yolo/myproj/labeled_integrated data/labels_raw

# 또는 복사 (안전)
cp -r /home/gjkong/dev_ws/yolo/myproj/skeleton_integrated data/skeleton_raw
cp -r /home/gjkong/dev_ws/yolo/myproj/labeled_integrated data/labels_raw
```

#### 작업 1.2: CSV → NumPy 변환
```python
# scripts/prepare_data.py

import pandas as pd
import numpy as np
from pathlib import Path

def load_skeleton_csv(csv_path):
    """
    CSV에서 Skeleton 로드
    
    Returns:
        skeleton: (T, 17, 3) - T frames, 17 joints, (x,y,conf)
        label: (T,) - frame별 label
    """
    df = pd.read_csv(csv_path)
    
    # Keypoints 추출
    keypoints = []
    for i in range(17):
        x = df[f'x_{i}'].values
        y = df[f'y_{i}'].values
        conf = df[f'conf_{i}'].values
        keypoints.append(np.stack([x, y, conf], axis=1))
    
    skeleton = np.stack(keypoints, axis=1)  # (T, 17, 3)
    
    # Labels
    labels = df['label_3class'].values  # (T,)
    
    return skeleton, labels

def create_sequences(skeleton, labels, seq_len=60, stride=30):
    """
    긴 비디오를 고정 길이 시퀀스로 분할
    
    Args:
        skeleton: (T, 17, 3)
        labels: (T,)
        seq_len: 시퀀스 길이 (60 프레임 = 3초)
        stride: 슬라이딩 간격
    
    Returns:
        sequences: (N, 3, 60, 17, 1)
        seq_labels: (N,) - 시퀀스의 대표 라벨
    """
    T = skeleton.shape[0]
    sequences = []
    seq_labels = []
    
    for start in range(0, T - seq_len + 1, stride):
        end = start + seq_len
        
        seq = skeleton[start:end]  # (60, 17, 3)
        seq = seq.transpose(2, 0, 1)  # (3, 60, 17)
        seq = seq[..., np.newaxis]  # (3, 60, 17, 1)
        
        # 시퀀스의 대표 라벨 (최빈값)
        seq_label = np.bincount(labels[start:end]).argmax()
        
        sequences.append(seq)
        seq_labels.append(seq_label)
    
    return np.array(sequences), np.array(seq_labels)

def process_all_videos():
    """전체 비디오 처리"""
    
    skeleton_dir = Path('data/skeleton_raw')
    label_dir = Path('data/labels_raw')
    output_dir = Path('data/processed')
    output_dir.mkdir(exist_ok=True)
    
    all_sequences = []
    all_labels = []
    
    for skeleton_file in sorted(skeleton_dir.glob('fall-*-skeleton.csv')):
        video_id = skeleton_file.stem.replace('-skeleton', '')
        label_file = label_dir / f'{video_id}-labeled.csv'
        
        # Skeleton & Labels 로드
        skeleton, labels = load_skeleton_csv(label_file)
        
        # 시퀀스 생성
        sequences, seq_labels = create_sequences(skeleton, labels)
        
        all_sequences.append(sequences)
        all_labels.append(seq_labels)
        
        print(f"{video_id}: {len(sequences)} sequences")
    
    # 전체 데이터
    all_sequences = np.concatenate(all_sequences, axis=0)
    all_labels = np.concatenate(all_labels, axis=0)
    
    # 저장
    np.save(output_dir / 'sequences.npy', all_sequences)
    np.save(output_dir / 'labels.npy', all_labels)
    
    print(f"\n✅ 총 {len(all_sequences)} 시퀀스 생성")
    print(f"   Shape: {all_sequences.shape}")
    print(f"   Labels: {all_labels.shape}")
    
    # 클래스 분포
    unique, counts = np.unique(all_labels, return_counts=True)
    for cls, count in zip(unique, counts):
        cls_name = {0: 'Normal', 1: 'Falling', 2: 'Fallen'}[cls]
        print(f"   {cls_name}: {count} ({count/len(all_labels)*100:.1f}%)")

if __name__ == "__main__":
    process_all_videos()
```

#### 작업 1.3: 데이터 증강
```python
# scripts/augment_data.py

def temporal_augment(sequence, label, speed_factors=[0.8, 1.2]):
    """시간 축 증강"""
    augmented = []
    
    for speed in speed_factors:
        # 시간 축 리샘플링
        T = sequence.shape[1]
        new_T = int(T * speed)
        
        # 보간
        indices = np.linspace(0, T-1, new_T)
        aug_seq = np.zeros((3, new_T, 17, 1))
        
        for c in range(3):
            for v in range(17):
                aug_seq[c, :, v, 0] = np.interp(
                    indices, 
                    np.arange(T), 
                    sequence[c, :, v, 0]
                )
        
        # 60 프레임으로 맞추기
        if new_T < 60:
            # Padding
            pad = np.zeros((3, 60-new_T, 17, 1))
            aug_seq = np.concatenate([aug_seq, pad], axis=1)
        else:
            # Truncate
            aug_seq = aug_seq[:, :60, :, :]
        
        augmented.append((aug_seq, label))
    
    return augmented

def spatial_augment(sequence, label):
    """공간 축 증강"""
    augmented = []
    
    # 1. Jittering
    noise = np.random.normal(0, 2.0, sequence.shape)
    jittered = sequence + noise
    augmented.append((jittered, label))
    
    # 2. Scaling
    scale = np.random.uniform(0.9, 1.1)
    scaled = sequence * scale
    augmented.append((scaled, label))
    
    return augmented
```

#### 작업 1.4: Train/Val/Test 분할
```python
# scripts/split_dataset.py

from sklearn.model_selection import train_test_split

# 로드
sequences = np.load('data/processed/sequences.npy')
labels = np.load('data/processed/labels.npy')

# 분할 (70/15/15)
X_train, X_temp, y_train, y_temp = train_test_split(
    sequences, labels, test_size=0.3, stratify=labels, random_state=42
)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42
)

# 저장
np.save('data/processed/train_data.npy', X_train)
np.save('data/processed/train_labels.npy', y_train)
np.save('data/processed/val_data.npy', X_val)
np.save('data/processed/val_labels.npy', y_val)
np.save('data/processed/test_data.npy', X_test)
np.save('data/processed/test_labels.npy', y_test)

print(f"Train: {len(X_train)}")
print(f"Val:   {len(X_val)}")
print(f"Test:  {len(X_test)}")
```

#### 체크리스트
- [ ] 기존 데이터 링크/복사
- [ ] CSV → NumPy 변환 스크립트
- [ ] 시퀀스 생성 (70 → 200-300)
- [ ] 데이터 증강 구현
- [ ] Train/Val/Test 분할
- [ ] 데이터 통계 확인

---

### Phase 2: ST-GCN 모델 구현 (3-4일)

#### 작업 2.1: ST-GCN 네트워크 구현
```python
# models/st_gcn.py

import torch
import torch.nn as nn
import torch.nn.functional as F

class STGCN(nn.Module):
    """
    ST-GCN for Fall Detection
    
    Input: (N, C, T, V, M)
        N: Batch
        C: Channels (3: x, y, conf)
        T: Time frames (60)
        V: Vertices (17 keypoints)
        M: People (1)
    
    Output: (N, num_classes)
        num_classes: 3 (Normal, Falling, Fallen)
    """
    
    def __init__(self, num_classes=3, in_channels=3):
        super(STGCN, self).__init__()
        
        # Skeleton Graph
        self.graph = SkeletonGraph()
        self.A = torch.tensor(
            self.graph.A, 
            dtype=torch.float32, 
            requires_grad=False
        )
        
        # ST-GCN Layers
        self.st_gcn_networks = nn.ModuleList([
            STGCNBlock(in_channels, 64, self.A, stride=1),
            STGCNBlock(64, 64, self.A, stride=1),
            STGCNBlock(64, 64, self.A, stride=1),
            STGCNBlock(64, 128, self.A, stride=2),
            STGCNBlock(128, 128, self.A, stride=1),
            STGCNBlock(128, 128, self.A, stride=1),
            STGCNBlock(128, 256, self.A, stride=2),
            STGCNBlock(256, 256, self.A, stride=1),
            STGCNBlock(256, 256, self.A, stride=1),
        ])
        
        # Global Pooling
        self.pool = nn.AdaptiveAvgPool2d(1)
        
        # Classifier
        self.fc = nn.Linear(256, num_classes)
    
    def forward(self, x):
        # x: (N, C, T, V, M)
        N, C, T, V, M = x.size()
        x = x.permute(0, 4, 3, 1, 2).contiguous()  # (N, M, V, C, T)
        x = x.view(N * M, V, C, T)
        
        # ST-GCN Layers
        for gcn in self.st_gcn_networks:
            x = gcn(x)
        
        # Global Pooling
        x = self.pool(x)  # (N*M, C, 1, 1)
        x = x.view(N, M, -1).mean(dim=1)  # (N, C)
        
        # Classification
        x = self.fc(x)  # (N, num_classes)
        
        return x

class STGCNBlock(nn.Module):
    """ST-GCN Block"""
    
    def __init__(self, in_channels, out_channels, A, stride=1):
        super(STGCNBlock, self).__init__()
        
        # Spatial GCN
        self.gcn = GCN(in_channels, out_channels, A)
        
        # Temporal CNN
        self.tcn = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, (9, 1), (stride, 1), (4, 0)),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
        
        # Residual
        if stride != 1 or in_channels != out_channels:
            self.residual = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 1, (stride, 1)),
                nn.BatchNorm2d(out_channels)
            )
        else:
            self.residual = nn.Identity()
    
    def forward(self, x):
        res = self.residual(x)
        x = self.gcn(x)
        x = self.tcn(x)
        x = x + res
        return F.relu(x)

class SkeletonGraph:
    """17 Keypoints Skeleton Graph"""
    
    def __init__(self):
        self.num_nodes = 17
        self.edges = [
            (0, 1), (0, 2),  # nose - eyes
            (1, 3), (2, 4),  # eyes - ears
            (0, 5), (0, 6),  # nose - shoulders
            (5, 7), (7, 9),  # left arm
            (6, 8), (8, 10), # right arm
            (5, 11), (6, 12),# shoulders - hips
            (11, 13), (13, 15), # left leg
            (12, 14), (14, 16), # right leg
        ]
        
        # Adjacency Matrix
        self.A = self.get_adjacency_matrix()
    
    def get_adjacency_matrix(self):
        A = np.zeros((self.num_nodes, self.num_nodes))
        for i, j in self.edges:
            A[i, j] = 1
            A[j, i] = 1
        
        # Self-connections
        A = A + np.eye(self.num_nodes)
        
        return A
```

#### 작업 2.2: 학습 스크립트
```python
# scripts/train.py

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from models.st_gcn import STGCN

# 데이터 로드
X_train = torch.FloatTensor(np.load('data/processed/train_data.npy'))
y_train = torch.LongTensor(np.load('data/processed/train_labels.npy'))
X_val = torch.FloatTensor(np.load('data/processed/val_data.npy'))
y_val = torch.LongTensor(np.load('data/processed/val_labels.npy'))

# DataLoader
train_dataset = TensorDataset(X_train, y_train)
val_dataset = TensorDataset(X_val, y_val)

train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=16)

# 모델
model = STGCN(num_classes=3, in_channels=3)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = model.to(device)

# Loss & Optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 학습
num_epochs = 100
best_val_acc = 0

for epoch in range(num_epochs):
    # Train
    model.train()
    train_loss = 0
    train_correct = 0
    
    for X_batch, y_batch in train_loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        
        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()
        
        train_loss += loss.item()
        train_correct += (outputs.argmax(1) == y_batch).sum().item()
    
    train_acc = train_correct / len(train_dataset)
    
    # Validation
    model.eval()
    val_loss = 0
    val_correct = 0
    
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            
            outputs = model(X_batch)
            loss = criterion(outputs, y_batch)
            
            val_loss += loss.item()
            val_correct += (outputs.argmax(1) == y_batch).sum().item()
    
    val_acc = val_correct / len(val_dataset)
    
    print(f"Epoch {epoch+1}/{num_epochs}")
    print(f"  Train Loss: {train_loss/len(train_loader):.4f}, Acc: {train_acc:.4f}")
    print(f"  Val Loss: {val_loss/len(val_loader):.4f}, Acc: {val_acc:.4f}")
    
    # Best Model 저장
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), 'checkpoints/best_model.pth')
        print(f"  ✅ Best model saved! (Val Acc: {val_acc:.4f})")
```

#### 체크리스트
- [ ] ST-GCN 모델 구현
- [ ] Skeleton Graph 정의
- [ ] 학습 스크립트 작성
- [ ] 검증 루프 구현
- [ ] Best Model 저장
- [ ] TensorBoard 로깅

---

### Phase 3: 평가 및 비교 (2일)

#### 작업 3.1: 테스트 평가
```python
# scripts/evaluate.py

# Test Set 평가
X_test = torch.FloatTensor(np.load('data/processed/test_data.npy'))
y_test = torch.LongTensor(np.load('data/processed/test_labels.npy'))

test_dataset = TensorDataset(X_test, y_test)
test_loader = DataLoader(test_dataset, batch_size=16)

# 모델 로드
model = STGCN(num_classes=3)
model.load_state_dict(torch.load('checkpoints/best_model.pth'))
model.eval()

# 평가
all_preds = []
all_labels = []

with torch.no_grad():
    for X_batch, y_batch in test_loader:
        outputs = model(X_batch)
        preds = outputs.argmax(1)
        
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(y_batch.cpu().numpy())

# Confusion Matrix
from sklearn.metrics import confusion_matrix, classification_report

cm = confusion_matrix(all_labels, all_preds)
report = classification_report(
    all_labels, all_preds,
    target_names=['Normal', 'Falling', 'Fallen']
)

print(report)
print(cm)
```

#### 작업 3.2: Random Forest와 비교
```python
# scripts/compare_models.py

# ST-GCN 결과
st_gcn_results = {
    'accuracy': 0.95,
    'normal': 0.98,
    'falling': 0.87,
    'fallen': 0.94
}

# Random Forest 결과 (기존)
rf_results = {
    'accuracy': 0.9319,
    'normal': 0.985,
    'falling': 0.766,
    'fallen': 0.921
}

# 비교 표
import pandas as pd

df = pd.DataFrame({
    'Random Forest': rf_results,
    'ST-GCN': st_gcn_results
})

print(df)
```

#### 체크리스트
- [ ] Test Set 평가
- [ ] Confusion Matrix 생성
- [ ] 클래스별 성능 분석
- [ ] Random Forest와 비교
- [ ] 오류 분석 (Failing 집중)

---

### Phase 4: GUI 통합 (2일)

#### 작업 4.1: ST-GCN 추론 모듈
```python
# gui/st_gcn_detector.py

import torch
import numpy as np
from collections import deque

class STGCNDetector:
    """ST-GCN 기반 낙상 감지"""
    
    def __init__(self, model_path, seq_len=60):
        self.model = STGCN(num_classes=3)
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()
        
        self.seq_len = seq_len
        self.frame_buffer = deque(maxlen=seq_len)
        
        self.class_names = {0: 'Normal', 1: 'Falling', 2: 'Fallen'}
    
    def add_frame(self, keypoints):
        """프레임 추가"""
        # keypoints: (17, 3)
        self.frame_buffer.append(keypoints)
    
    def predict(self):
        """예측"""
        if len(self.frame_buffer) < self.seq_len:
            return 0, [1.0, 0.0, 0.0]  # Not enough frames
        
        # 시퀀스 준비
        sequence = np.array(list(self.frame_buffer))  # (60, 17, 3)
        sequence = sequence.transpose(2, 0, 1)  # (3, 60, 17)
        sequence = sequence[np.newaxis, ..., np.newaxis]  # (1, 3, 60, 17, 1)
        
        # 예측
        with torch.no_grad():
            x = torch.FloatTensor(sequence)
            output = self.model(x)
            probs = torch.softmax(output, dim=1)[0]
            pred = output.argmax(1).item()
        
        return pred, probs.cpu().numpy()
```

#### 작업 4.2: GUI 수정 (최소한)
```python
# gui/monitoring_page.py 수정

# Line 68-107: 모델 로드 부분 수정

# ❌ 기존
self.rf_model = joblib.load(model_path)

# ✅ 변경 (ST-GCN)
from st_gcn_detector import STGCNDetector
self.st_gcn_detector = STGCNDetector(
    model_path='/home/gjkong/dev_ws/st_gcn/checkpoints/best_model.pth',
    seq_len=60
)

# 예측 부분 수정
def update_frame(self):
    # ... YOLO Pose 처리 ...
    
    # ST-GCN 예측
    if self.st_gcn_detector:
        self.st_gcn_detector.add_frame(keypoints)
        prediction, proba = self.st_gcn_detector.predict()
        
        # UI 업데이트
        self.update_fall_info(prediction, proba)
```

#### 체크리스트
- [ ] ST-GCN 추론 모듈 작성
- [ ] GUI 모델 교체
- [ ] 실시간 테스트
- [ ] 성능 측정 (FPS)
- [ ] A/B 테스트 준비

---

## 6. 디렉토리 구조

### 최종 디렉토리 구조

```
/home/gjkong/dev_ws/st_gcn/
├── README.md
├── requirements.txt
├── config.yaml
│
├── data/
│   ├── skeleton_raw/          # 기존 데이터 링크
│   ├── labels_raw/             # 기존 라벨 링크
│   └── processed/              # 변환된 데이터
│       ├── sequences.npy       # (N, 3, 60, 17, 1)
│       ├── labels.npy          # (N,)
│       ├── train_data.npy
│       ├── train_labels.npy
│       ├── val_data.npy
│       ├── val_labels.npy
│       ├── test_data.npy
│       └── test_labels.npy
│
├── models/
│   ├── __init__.py
│   ├── st_gcn.py              # ST-GCN 모델
│   ├── graph.py               # Skeleton Graph
│   └── layers.py              # Custom Layers
│
├── scripts/
│   ├── prepare_data.py        # CSV → NumPy
│   ├── augment_data.py        # 데이터 증강
│   ├── split_dataset.py       # Train/Val/Test
│   ├── train.py               # 학습
│   ├── evaluate.py            # 평가
│   └── compare_models.py      # 모델 비교
│
├── gui/
│   ├── st_gcn_detector.py     # ST-GCN 추론
│   └── monitoring_page.py     # GUI (수정)
│
├── checkpoints/
│   └── best_model.pth         # Best Model
│
├── logs/
│   └── tensorboard/           # TensorBoard
│
└── results/
    ├── confusion_matrix.png
    ├── performance_report.txt
    └── comparison.csv
```

---

## 7. 구현 로드맵

### 타임라인 (총 2-3주)

```
Week 1: 환경 구축 및 데이터 준비
├── Day 1: 환경 구축, PyTorch 설치
├── Day 2-3: 데이터 변환 (CSV → NumPy)
├── Day 4-5: 데이터 증강, Train/Val/Test 분할
└── Day 6-7: 데이터 검증, 시각화

Week 2: ST-GCN 구현 및 학습
├── Day 8-10: ST-GCN 모델 구현
├── Day 11-12: 학습 스크립트 작성
├── Day 13-14: 모델 학습 (50-100 epochs)
└── 중간 평가: Falling 성능 확인

Week 3: 평가 및 통합
├── Day 15-16: Test Set 평가, 성능 비교
├── Day 17-18: GUI 통합, 실시간 테스트
├── Day 19-20: A/B 테스트, 최종 결정
└── Day 21: 문서화 및 배포 준비
```

### 마일스톤

| 마일스톤 | 완료 조건 | 기한 |
|---------|----------|------|
| **M1: 환경 구축** | PyTorch, ST-GCN 준비 | Day 1 |
| **M2: 데이터 준비** | 200+ 시퀀스 생성 | Day 7 |
| **M3: 모델 구현** | ST-GCN forward 성공 | Day 10 |
| **M4: 학습 완료** | Val Acc 85%+ | Day 14 |
| **M5: 평가 완료** | Test 결과 분석 | Day 16 |
| **M6: GUI 통합** | 실시간 테스트 성공 | Day 18 |
| **M7: 배포 결정** | Random Forest vs ST-GCN | Day 21 |

---

## 8. 리스크 및 대응

### 리스크 분석

#### 리스크 1: 데이터 부족 (High)
```
문제: 70개 비디오 부족 (권장 200-500개)
확률: 90%
영향: 과적합, 성능 저하

대응:
1. 시간 증강 (70 → 300 시퀀스)
2. 공간 증강 (×2-3배)
3. Transfer Learning (NTU RGB+D)
4. Data Augmentation 강화

완화: 
- 증강으로 200-300 시퀀스 확보
- Early Stopping으로 과적합 방지
```

#### 리스크 2: 성능 미달 (Medium)
```
문제: ST-GCN이 Random Forest보다 낮을 수 있음
확률: 30%
영향: 프로젝트 실패

대응:
1. 하이퍼파라미터 튜닝
2. 앙상블 (ST-GCN + RF)
3. 모델 아키텍처 수정
4. Random Forest 유지 결정

완화:
- 점진적 개선
- A/B 테스트로 검증
```

#### 리스크 3: 실시간 성능 (Low)
```
문제: ST-GCN 추론 속도 느림 (30ms/frame)
확률: 50%
영향: GUI 지연, FPS 저하

대응:
1. 모델 경량화 (TorchScript)
2. GPU 가속
3. 배치 추론
4. 프레임 스킵

완화:
- 30 FPS 유지 가능 (33ms/frame)
- 필요시 경량 모델로 전환
```

#### 리스크 4: 통합 복잡도 (Medium)
```
문제: GUI 통합 시 호환성 문제
확률: 40%
영향: 개발 지연

대응:
1. 최소 수정 원칙
2. 래퍼 클래스 사용
3. 기존 인터페이스 유지
4. 점진적 통합

완화:
- Random Forest 백업 유지
- A/B 스위칭 가능
```

---

## 9. 성능 비교 계획

### 비교 메트릭

| 메트릭 | Random Forest | ST-GCN (목표) | 중요도 |
|--------|--------------|--------------|--------|
| **Overall Accuracy** | 93.19% | 94%+ | High |
| **Normal** | 98.5% | 98%+ | Medium |
| **Falling** | 76.6% | 85%+ | ⭐ Critical |
| **Fallen** | 92.1% | 93%+ | High |
| **추론 시간** | 10ms | 30ms | Medium |
| **모델 크기** | 2MB | 100MB | Low |
| **학습 시간** | 10분 | 2시간 | Low |

### A/B 테스트 계획

```python
# 실시간 비교
Phase 1: 오프라인 테스트 (1주)
  - Test Set 평가
  - 오류 분석
  - 성능 비교

Phase 2: 실시간 테스트 (1주)
  - GUI에서 동시 실행
  - FPS 측정
  - 사용자 경험 평가

Phase 3: 최종 결정
  Decision Matrix:
    - Falling 85%+ → ST-GCN 채택
    - Falling < 80% → Random Forest 유지
    - 중간 → 앙상블 고려
```

---

## 10. 의사결정 가이드

### 시나리오별 결정

#### 시나리오 A: ST-GCN 성공 (Falling 85%+)
```
✅ ST-GCN 채택
✅ Random Forest 백업 유지
✅ GUI 통합
✅ 실전 배포

다음 단계:
1. GUI 완전 통합
2. 실사용 데이터 수집
3. 지속적 개선
```

#### 시나리오 B: ST-GCN 부분 성공 (80-85%)
```
⚠️ 앙상블 고려
  - ST-GCN + Random Forest
  - 투표 또는 가중 평균
  
⚠️ 추가 개선
  - 데이터 추가 수집
  - 하이퍼파라미터 튜닝
  - 모델 아키텍처 수정
```

#### 시나리오 C: ST-GCN 실패 (<80%)
```
❌ Random Forest 유지
❌ ST-GCN 보류

교훈:
- 데이터 부족이 원인
- 추후 데이터 확보 후 재시도
- 다른 접근 (LSTM, Transformer) 고려
```

### 최종 권장 사항

#### 즉시 시작 조건 ✅
```
1. PyTorch 환경 구축 가능
2. 2-3주 개발 시간 확보
3. GPU 사용 가능 (권장)
4. 데이터 증강 활용 동의
5. 실험적 접근 수용
```

#### 보류 조건 ⏸️
```
1. 시간 부족 (2주 미만)
2. GPU 없음 (학습 매우 느림)
3. Random Forest 성능 만족
4. 안정성 최우선
5. 즉시 배포 필요
```

---

## 부록

### A. 참고 자료

**ST-GCN 논문:**
- Yan et al., "Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition", AAAI 2018

**구현 참고:**
- https://github.com/yysijie/st-gcn
- https://github.com/open-mmlab/mmskeleton

**데이터셋:**
- UR Fall Detection Dataset (현재 사용 중)
- NTU RGB+D (Transfer Learning용)

### B. FAQ

**Q1: 70개 비디오로 충분한가요?**
A: 부족하지만 증강으로 200-300 시퀀스 확보 가능. 최소 조건 충족.

**Q2: Random Forest보다 정말 좋아질까요?**
A: Falling 성능은 높은 확률로 개선. Overall은 비슷하거나 약간 향상.

**Q3: 실시간 추론이 가능한가요?**
A: 가능. GPU 사용 시 30ms/frame (30 FPS 유지 가능).

**Q4: 기존 시스템을 유지하나요?**
A: 네. 완전히 별도 프로젝트로 진행. 기존 시스템 무중단.

**Q5: 실패하면 어떻게 하나요?**
A: Random Forest 계속 사용. ST-GCN은 실험으로 간주.

---

## 최종 요약

### ✅ ST-GCN 도입 가능
```
기존 Skeleton 데이터 활용 가능 ✅
시간/공간 증강으로 데이터 확보 ✅
별도 프로젝트로 안전 실험 ✅
성공 시 큰 성능 향상 기대 ✅
```

### 📋 다음 단계
```
1. 의사결정: ST-GCN 시작 여부
2. Phase 0: 환경 구축 (1일)
3. Phase 1: 데이터 준비 (3일)
4. Phase 2: 모델 구현 및 학습 (1주)
5. Phase 3: 평가 및 비교 (2일)
6. Phase 4: GUI 통합 (2일)
7. 최종 결정: 채택 or 보류
```

### 🎯 권장 사항
```
⭐ 시작 추천!
이유:
- 기술적으로 가능
- 높은 개선 가능성
- 리스크 관리 가능
- 학습 기회

조건:
- 2-3주 시간 확보
- 실험적 접근 수용
- 기존 시스템 유지
```

---

**작성 완료: 2026-02-03**  
**검토자: Stephen Kong**  
**승인 대기 중**
