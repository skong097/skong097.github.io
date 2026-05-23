---
title: "ROS2 Jazzy + FastAPI로 Guard Brain 만들기"
date: 2026-02-10
tags: ["ros2", "fastapi", "llm", "tts", "python", "robotics"]
categories: ["ros2"]
summary: "ROS2 Jazzy의 guard_brain 노드에서 LLM과 센서 데이터를 융합하는 지능형 경비 로봇 시스템 구축 과정"
cover:
  image: "images/guard-brain-architecture.png"
  alt: "Home Guard Bot 아키텍처"
draft: true
ShowToc: true
TocOpen: true
---

## 배경

경비 로봇이 단순히 순찰만 하는 게 아니라, 상황을 판단하고 음성으로 응대할 수 있으면 어떨까? Home Guard Bot 프로젝트는 LLM(대형 언어 모델)을 ROS2 노드에 통합하여 "생각하는 로봇"을 만드는 시도입니다.

### 목표

- FastAPI v0.2: TTS + JSON 응답 통합
- ROS2 Jazzy: guard_brain 노드에서 LLM + 센서 데이터 융합
- 실시간 음성 응답 (guard_voice 노드)

## 아키텍처

<!-- FastAPI ↔ ROS2 ↔ LLM 데이터 흐름 다이어그램 추가 -->

## 구현

<!-- 핵심 코드: guard_brain 노드, FastAPI 라우터, TTS 통합 -->

## 결과

<!-- 데모 시나리오: 침입자 감지 → LLM 판단 → 음성 경고 -->

## 배운 점

<!-- ROS2와 HTTP API 연동 시 주의점, 추론 지연 최적화 -->

## 다음 단계

- guard_vision 노드 통합
- 추론 속도 개선 (로컬 LLM 최적화)
