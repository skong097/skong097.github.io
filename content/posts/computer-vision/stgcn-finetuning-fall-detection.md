---
title: ST-GCN 파인튜닝으로 낙상감지 91.89% 달성기
date: 2026-02-14
tags:
- st-gcn
- computer-vision
- fall-detection
- python
- deep-learning
categories:
- computer-vision
summary: ST-GCN 모델을 3클래스 낙상감지에 맞춰 파인튜닝하고 84.21% → 91.89%로 끌어올린 과정과 삽질 기록
cover:
  image: images/covers/post-stgcn-finetuning.png
  alt: ST-GCN Fine-tuning for Fall Detection
  hidden: false
draft: true
ShowToc: true
TocOpen: true
---

## 배경

Home Safe Solution 프로젝트에서 실시간 낙상 감지가 필요했습니다. 영상에서 사람의 행동을 분류해야 하는데, 단순 프레임 기반 분석으로는 "쓰러지는 동작"과 "앉는 동작"을 구분하기 어려웠습니다. 시간적 패턴(temporal pattern)을 학습할 수 있는 ST-GCN을 선택했습니다.

### 목표

- 3클래스 분류: Normal, Fall, Lying
- 기존 pre-trained 모델 정확도 84.21% → 90%+ 달성
- 추론 시간 2초 이내 (실시간 대시보드 연동)

## 접근 방법

<!-- 여기에 학습 데이터 구성, 하이퍼파라미터 튜닝 과정, 실패와 성공 기록 추가 -->

## 구현

<!-- 핵심 코드: 모델 구조 변경, 데이터 전처리, 학습 루프 -->

## 결과

| 지표 | Before | After |
|------|--------|-------|
| 정확도 | 84.21% | **91.89%** |
| 추론 시간 | ~2.5초 | ~2초 |
| 모델 크기 | — | — |

## 배운 점

<!-- 트러블슈팅 기록 추가 -->

## 다음 단계

- Random Forest와의 앙상블 검토
- 실시간 GUI 연동 최적화
