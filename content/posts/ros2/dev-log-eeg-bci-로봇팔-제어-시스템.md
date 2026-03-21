---
title: "DEV_LOG — EEG BCI 로봇팔 제어 시스템"
date: 2026-03-21
draft: true
tags: ["ros2", "rclpy"]
categories: ["ros2"]
description: "**날짜:** 2026-03-12 **세션:** BCI Pipeline 초기 설계 및 코드 작성 | 레이어 | 기술 스택 |"
---

# DEV_LOG — EEG BCI 로봇팔 제어 시스템

**날짜:** 2026-03-12  
**세션:** BCI Pipeline 초기 설계 및 코드 작성

---

## 시스템 구성

| 레이어 | 기술 스택 |
|--------|-----------|
| EEG 장비 | Muse 2 / Muse S (4ch, 256Hz) |
| 데이터 수신 | pylsl (Lab Streaming Layer) + mind-monitor 앱 |
| 신호처리 | scipy (Butterworth BPF 8–30Hz, notch 50Hz) |
| BCI 패러다임 | Motor Imagery (왼손/오른손/휴식) |
| 분류기 | MNE CSP (4 components) + sklearn LDA |
| 통신 | ROS2 Jazzy — /bci_command (std_msgs/String) |
| 로봇 | UR 로봇팔 (UR5e 등) + MoveIt2 |

---

## 아키텍처 흐름

```
Muse 2
  └─[BLE]→ mind-monitor 앱
              └─[LSL]→ MuseLSLReceiver (pylsl)
                          └─[numpy]→ EEGPreprocessor (BPF + z-score)
                                        └─[MNE CSP]→ MotorImageryClassifier (LDA)
                                                         └─[rclpy]→ /bci_command
                                                                       └─[ROS2]→ BCIURController Node
                                                                                   └─[MoveIt2]→ UR 로봇팔
```

---

## 생성 파일

| 파일 | 역할 |
|------|------|
| `eeg_bci_pipeline.py` | EEG 수신 / 전처리 / MI 분류 / ROS2 발행 통합 |
| `bci_ur_controller_node.py` | ROS2 노드 — /bci_command 구독 → UR Cartesian 이동 |
| `bci_calibration.ipynb` | 캘리브레이션 데이터 수집 + 학습 + 평가 Notebook |

---

## 실행 순서

### Step 1. 환경 준비
```bash
# Muse 2: mind-monitor 앱에서 LSL 스트리밍 활성화
# Python 의존성
pip install pylsl mne scikit-learn scipy numpy joblib matplotlib

# ROS2 Jazzy 환경
source /opt/ros/jazzy/setup.bash
```

### Step 2. 캘리브레이션 (Jupyter)
```bash
jupyter notebook bci_calibration.ipynb
# 셀 순서대로 실행 → mi_model.pkl 생성
# 예상 시간: 약 18분 (3클래스 × 30회)
# 목표 정확도: 5-fold CV 70% 이상
```

### Step 3. ROS2 노드 실행
```bash
# 터미널 1: UR 드라이버
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=192.168.1.10

# 터미널 2: BCI 컨트롤러 노드
ros2 run bci_ur_pkg bci_ur_controller

# 터미널 3: BCI 메인 파이프라인
python eeg_bci_pipeline.py
```

---

## 주요 파라미터

| 파라미터 | 값 | 비고 |
|---------|-----|------|
| 샘플레이트 | 256 Hz | Muse 2 기본값 |
| 버퍼 길이 | 4초 (1024샘플) | MI epoch 기준 |
| 대역통과 | 8–30 Hz | mu(8–12) + beta(13–30) |
| CSP 컴포넌트 | 4 | 과적합 방지 |
| 신뢰도 임계값 | 0.65 | REST fallback |
| 명령 주기 | 1.0초 | BCIPipeline.INFERENCE_INTERVAL |
| 이동 스텝 | 0.05m | URRobotController.STEP_M |

---

## 다음 작업

- [ ] 캘리브레이션 데이터 수집 및 모델 학습
- [ ] CV 정확도 70% 이상 확인
- [ ] UR 드라이버 연동 테스트 (시뮬레이션 먼저)
- [ ] MoveIt2 액션 서버 연동 (현재는 Pose topic 발행)
- [ ] 온라인 적응 학습 (Covariate shift 보정)
- [ ] GUI 피드백 화면 추가 (현재 명령 표시)

---

## 알려진 이슈

- Muse 2 채널 4개(TP9, AF7, AF8, TP10)는 MI 분류에 최소 채널 → CSP 컴포넌트 최대 4개 제한
- mind-monitor LSL 스트림 이름은 기기마다 다를 수 있음 → `resolve_stream()` 결과로 확인 필요
- UR 작업 공간 제한 클리핑 적용됨 (x,y: ±0.6m, z: 0.1–0.8m)
