---
title: "Change Log - Home Safe Solution"
date: 2026-03-21
draft: true
tags: ["vision-ai", "yolo"]
categories: ["vision-ai"]
description: "- 노트북 환경 최적화 물리 필터 적용: `is_physical_fall = (h_vel > 10.0) and (a_ratio > 1.2) and (s_angle > 75.0) and (hip_y > 300)` - "
---

# Change Log - Home Safe Solution

## 대상 파일 : realtime_fall_detection.py

## [v1.1.2] - 2026-02-01
### Changed
- 노트북 환경 최적화 물리 필터 적용: `is_physical_fall = (h_vel > 10.0) and (a_ratio > 1.2) and (s_angle > 75.0) and (hip_y > 300)`
- 엉덩이 높이(hip_y) 하단 제한 및 척추 각도(s_angle) 엄격화로 앉아 있는 상태 오탐지 제거 시도 -> 증상 동일


## [v1.1.0] - 2026-02-01
### Added
- 실시간 탐지 시 '앉기' 동작 오탐지 방지를 위한 3중 물리 필터 로직 추가
- GUI 상단에 실시간 물리 지표(Spine Angle, Aspect Ratio, Velocity) 출력 기능 추가

### Changed
- 낙상 판정 로직: 단순 모델 예측에서 물리 지표(AND 조건) 검증 방식으로 변경
- 임계값 상향 조정: 
  * `h_vel` (수직 속도): 5.0 -> 10.0
  * `a_ratio` (종횡비): 1.2 -> 1.5
  * `s_angle` (척추 각도): 60.0 -> 75.0

### Fixed
- 사용자가 의자에 앉아 있을 때 'Fallen'으로 오인되는 이슈 해결

---

## [v1.0.0] - 2026-01-28
### Added
- YOLO v8/v11 Pose 기반 실시간 낙상 감지 초기 버전 릴리스
- Random Forest 3클래스(Normal, Falling, Fallen) 분류 모델 통합


