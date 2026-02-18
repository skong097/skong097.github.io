---
title: "ST-GCN 파인튜닝으로 낙상감지 91.89% 달성기"
date: 2026-02-18
categories: ["ai-ml"]
tags: ["st-gcn", "computer-vision", "fall-detection", "python", "deep-learning"]
description: "ST-GCN 모델을 3클래스 낙상감지에 맞춰 파인튜닝하고 84.21% → 91.89%로 끌어올린 과정과 삽질 기록"
ShowToc: true
ShowReadingTime: true
draft: true
---

## 개요

본 포스트에서는 Home Safe Solution 프로젝트에서 실시간 낙상 감지 시스템의 성능 향상을 위해 ST-GCN 모델을 파인튜닝한 과정을 상세히 공유합니다. 특히, 3클래스 낙상 감지 분류(Normal, Fall, Lying)에서 기존 모델의 정확도를 84.21%에서 91.89%로 끌어올리는 데 초점을 맞추고 있습니다. 이 과정에서 겪은 시행착오와 해결 방법도 함께 다루어, 유사한 과제를 수행하는 연구자 및 엔지니어들에게 유용한 인사이트를 제공합니다.

## 배경

Home Safe Solution 프로젝트는 가정 내 실시간 낙상 감지 시스템 구축을 목표로 하고 있습니다. 기존의 프레임 기반 분석 방법으로는 "쓰러지는 동작"과 "앉는 동작"을 명확히 구분하는 데 어려움이 있었습니다. 이러한 한계를 극복하기 위해 시간적 패턴을 효과적으로 학습할 수 있는 **ST-Graph Convolutional Network (ST-GCN)** 모델을 도입하였습니다. ST-GCN은 시퀀스 데이터의 동적 특성을 잘 포착하여 낙상 감지에 적합한 선택이었습니다.

## 목표

- **3클래스 분류**: Normal, Fall, Lying 동작 분류
- **정확도 향상**: 기존 pre-trained 모델의 정확도 84.21%를 90% 이상으로 향상
- **실시간 성능**: 추론 시간을 2초 이내로 단축하여 실시간 대시보드 연동 가능

## 접근 방법

### 학습 데이터 구성
파인튜닝을 위해 다양한 환경과 조건에서 수집된 낙상 및 정상 동작 데이터셋을 활용했습니다. 데이터는 다음과 같이 구성되었습니다:
- **데이터 증강**: 회전, 밝기 조정 등을 통해 데이터 다양성 증가
- **라벨링**: 각 동작에 대한 정확한 라벨링을 통해 모델 학습의 질 향상

### 하이퍼파라미터 튜닝
- **학습률**: 초기값 0.001에서 시작하여 점진적으로 감소시키며 최적값 탐색
- **배치 크기**: 32에서 시작하여 64로 조정하여 학습 효율성 향상
- **에폭 수**: 50 에폭으로 설정하고 조기 중단 조건을 추가하여 과적합 방지

#### 실패와 성공 기록
- **실패 사례**: 초기 하이퍼파라미터 설정에서 과적합 현상 발생
  ```python
  # 초기 설정 예시
  optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
  scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min')
  ```
  - **해결책**: 드롭아웃 추가 및 데이터 증강 강화로 과적합 문제 해결
  ```python
  # 드롭아웃 적용 예시
  model.add_module('dropout', nn.Dropout(p=0.5))
  ```

## 구현

### 핵심 코드: 모델 구조 변경 및 학습 루프
ST-GCN 모델의 구조를 유지하면서 파인튜닝을 위한 핵심 코드는 다음과 같습니다:
```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# 모델 로드 및 일부 레이어 파인튜닝
model = torch.hub.load('your_repo', 'st_gcn_model', pretrained=True)
for param in model.parameters():
    param.requires_grad = True  # 파인튜닝을 위한 파라미터 설정

# 하이퍼파라미터 설정
lr = 0.0001
optimizer = torch.optim.Adam(model.parameters(), lr=lr)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min')

# 데이터 로더 설정
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

# 학습 루프
for epoch in range(50):
    model.train()
    for batch in train_loader:
        inputs, labels = batch
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
    
    # 검증 단계
    model.eval()
    with torch.no_grad():
        val_loss = 0
        for batch in val_loader:
            inputs, labels = batch
            outputs = model(inputs)
            val_loss += criterion(outputs, labels).item()
        scheduler.step(val_loss)
        print(f'Epoch {epoch+1}, Validation Loss: {val_loss/len(val_loader)}')
```

### 데이터 전처리
- **정규화**: 입력 데이터의 픽셀 값을 0~1 범위로 정규화
- **패딩**: 시퀀스 길이 일치를 위해 패딩 추가

## 결과

| 지표           | Before       | After       |
|----------------|--------------|-------------|
| **정확도**      | 84.21%       | **91.89%**  |
| **추론 시간**  | ~2.5초       | ~2초        |
| **모델 크기**  | —            | —           |

## 배운 점

- **데이터 증강의 중요성**: 데이터 증강을 통해 모델의 일반화 능력 향상
- **하이퍼파라미터 최적화**: 초기 설정의 중요성과 조기 중단 조건의 효과 확인
- **과적합 방지**: 드롭아웃과 정규화 기법의 효과적 적용

## 다음 단계

- **앙상블 방법 검토**: Random Forest와의 앙상블을 통해 성능 향상 시도
- **실시간 GUI 연동 최적화**: 추론 시간을 더욱 단축하여 실시간 모니터링 시스템 강화

이러한 노력과 결과를 통해 ST-GCN 모델의 낙상 감지 성능이 크게 향상되었으며, 앞으로의 개선 방향도 명확히 제시되었습니다. 이러한 경험은 실시간 안전 감지 시스템 개발에 있어 중요한 참고 자료가 될 것입니다.
