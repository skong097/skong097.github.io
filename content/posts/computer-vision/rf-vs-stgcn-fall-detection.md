---
title: Random Forest vs ST-GCN — 낙상감지 모델 비교 실전 가이드
date: 2026-02-08
tags:
- random-forest
- st-gcn
- model-comparison
- fall-detection
- python
categories:
- computer-vision
summary: 프레임 기반 Random Forest(93.19%)와 시계열 ST-GCN(91.89%)을 실전 낙상감지에 적용하고 비교한 결과
cover:
  image: images/covers/post-rf-vs-stgcn.png
  alt: RF vs ST-GCN Model Comparison
  hidden: false
draft: true
ShowToc: true
TocOpen: true
---

## 배경

낙상 감지에 어떤 모델이 최적일까? 이 질문에 답하기 위해 두 가지 접근법을 직접 비교했습니다.

- **Random Forest**: 프레임 단위 특징 추출 → 즉시 분류
- **ST-GCN**: 시간적 골격 그래프 → 시퀀스 기반 분류

정확도만 보면 RF가 높지만, 실제 운영에서는 그렇게 단순하지 않았습니다.

## 비교 결과

| 지표 | Random Forest | ST-GCN (Fine-tuned) |
|------|:---:|:---:|
| 정확도 | **93.19%** | 91.89% |
| 추론 시간 | **즉시 (~ms)** | ~2초 |
| 시간적 패턴 | ✗ | **✓** |
| 학습 데이터량 | 적어도 OK | 많이 필요 |

## 어떤 상황에 어떤 모델을?

<!-- 실전 시나리오별 추천: 빠른 응답 vs 정확한 패턴 인식 -->

## 앙상블 가능성

<!-- 두 모델을 결합한 2단계 파이프라인 설계 -->

## 배운 점

<!-- 모델 비교 자동화 스크립트, 실전 배포 시 고려사항 -->

## 다음 단계

- GUI에서 실시간 모델 전환 기능
- 두 모델 앙상블 파이프라인 구현
