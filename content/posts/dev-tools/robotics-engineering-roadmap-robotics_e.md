---
title: "Robotics Engineering Roadmap"
date: 2026-03-21
draft: true
tags: ["dev-tools", "pyqt6", "fastapi"]
categories: ["dev-tools"]
description: "> **Smart Factory × Physical AI × AIOps × Robot Network × Robot Security** > > Projects #8–#10: Smart Factory Dashboard "
---

# Robotics Engineering Roadmap

> **Smart Factory × Physical AI × AIOps × Robot Network × Robot Security**
>
> Projects #8–#10: Smart Factory Dashboard · Isaac Sim · Predictive Maintenance
>
> ROS2 · NVIDIA · AI/ML · Digital Twin · IoT · MLOps/AIOps
>
> **February 2026 | Stephen Kong | github.com/skong097**

---

## Executive Summary

Smart Factory Physical AI 프로젝트는 기존 7개 프로젝트 경험을 통합하여 산업용 로봇 모니터링, 디지털 트윈, 예측 정비 AI를 구현합니다. 2026년 Physical AI의 핵심 키워드인 NVIDIA Isaac Sim, ROS2, IoT 센서 네트워크, ML 기반 예측 정비를 포트폴리오에 추가합니다.

---

## 전체 프로젝트 맵 (10개)

기존 완료/진행 프로젝트와 신규 Smart Factory 프로젝트의 연결 구조:

| # | Project | Status | Keywords | Blog 소재 |
|---|---------|--------|----------|----------|
| 1 | Kevin 3D Patrol Sim | ✅ | Robotics, SLAM, OpenGL | 3D 시뮬레이션 개발기 |
| 2 | Kevin Patrol Dashboard | ✅ | ROS2, PyQt6, Monitoring | PyQt6 대시보드 + 3테마 |
| 3 | Home Safe Solution | ✅ | ST-GCN, Fall Detection | 낙상감지 91.89% 달성기 |
| 4 | EyeCon (피노키오) | ✅ | AI/ML, LLM, Real-time | 실시간 심리분석 Ollama |
| 5 | Home Guard Bot | ✅ | ROS2, FastAPI, LLM | guard_brain LLM 노드 |
| 6 | ROS2 Commander | ✅ | Education, Gamification | 게임으로 ROS2 학습 |
| 7 | MyPet | 🔧 | CV, Gesture Recognition | 핸드 제스처 가상 반려견 |
| 8 | **Smart Factory Dashboard** | 🆕 | Physical AI, Digital Twin, MLOps | 공장 모니터링 대시보드 |
| 9 | **Isaac Sim Integration** | 🆕 | NVIDIA, Simulation | Isaac Sim + ROS2 연동 |
| 10 | **Predictive Maintenance** | 🆕 | AI/ML, IoT, Time Series | 설비 고장 예측 AI |

---

## Project #8: Smart Factory Dashboard

공장 생산 라인의 로봇, 컨베이어, 센서, 카메라를 통합 모니터링하는 Digital Twin 기반 대시보드. Kevin Patrol Dashboard의 경험을 Smart Factory 도메인으로 확장합니다.

### 프로젝트 개요

| 항목 | 내용 |
|------|------|
| Project Name | Smart Factory Monitoring Dashboard |
| Category | Physical AI / Digital Twin / IoT |
| Tech Stack | Python, PyQt6, pyqtgraph, ROS2 (Jazzy), MQTT, OpenGL |
| Duration | 2주 (기존 Dashboard 코드 재활용) |
| 기존 연결 | Kevin Dashboard (v3.2) 구조 + DataProvider 추상화 패턴 |
| Blog 키워드 | Physical AI, Smart Factory, Digital Twin, ROS2, IoT, 모니터링 |

### 핵심 기능

- **Factory Floor 2D/3D View:** 공장 평면도 위에 로봇 ARM, 컨베이어, AGV 위치를 실시간 표시. OpenGL 3D 뷰 토글 가능
- **Production Line Monitor:** 각 스테이션별 생산량, 불량률, 택타임, 가동률 실시간 차트
- **Sensor Heatmap:** 온도/진동/압력/전류 센서 데이터를 히트맵으로 시각화. 이상치 자동 감지
- **Camera Vision Panel:** 공장 카메라 피드 + YOLO 기반 불량 검출 / 안전 구역 침범 감지
- **Alert & Event System:** 설비 이상, 안전 경고, 품질 이슈 토스트 알림 + 히스토리 로그
- **ROS2 Topic Dashboard:** 공장 내 모든 ROS2 토픽 상태 모니터링 (기존 TopicMonitor 확장)

### 시스템 아키텍처

```
[IoT Sensors] --MQTT--> [Data Ingestion Layer]
    |                         |
[ROS2 Nodes] --DDS-->  [FactoryDataProvider (ABC)]
    |                         |
[Camera/YOLO] -------> [Smart Factory Dashboard (PyQt6)]
                              |
                       [Alert Manager + Logger]
```

### 레이아웃 설계

```
┌─────────────────────┬─────────────────────┬────────────────┐
│  Factory Floor Map   │  Production Monitor  │  Alert History │
│  (2D/3D Digital Twin) │  (스테이션별 차트)  │  + Event Log   │
├─────────────────────┼─────────────────────┼────────────────┤
│  Sensor Heatmap      │  Camera Vision       │  ROS2 Topics  │
│  (온도/진동/압력)      │  (YOLO 불량검출)      │  Status Panel │
├─────────────────────┴─────────────────────┴────────────────┤
│  [SIM] [LIVE]  | ▶ START  ⏸ STOP  ⚠ ALERTS  ⚙ CONFIG    │
└──────────────────────────────────────────────────────────────┘
```

### 개발 타임라인 (2주)

| Phase | 기간 | 작업 내용 |
|-------|------|----------|
| 0 | Day 1 | 공장 레이아웃 설계 + FactoryDataProvider ABC 인터페이스 정의 |
| 1 | Day 2–3 | Factory Floor 2D 맵 + 로봇 ARM/AGV/컨베이어 시뮬레이션 |
| 2 | Day 4–5 | Production Line Monitor (실시간 차트) + Sensor Heatmap |
| 3 | Day 6–7 | Camera Vision Panel (YOLO 불량검출 시뮬레이션) |
| 4 | Day 8–9 | Alert System + ROS2 Topic Dashboard + MQTT 연동 |
| 5 | Day 10–12 | 통합 테스트, 테마 적용, README 작성, GitHub 배포 |

### 기존 프로젝트 재활용 매핑

| 기존 모듈 | Smart Factory 적용 | 변경점 |
|----------|-------------------|--------|
| SLAMMapWidget | Factory Floor Map | 공장 평면도 + 설비 배치 |
| CameraFeedWidget | Camera Vision Panel | YOLO 불량검출 추가 |
| SensorPlotWidget | Sensor Heatmap | 히트맵 시각화 추가 |
| TopicMonitorWidget | ROS2 Topic Dashboard | 공장 토픽 확장 |
| AlertManager | Alert & Event System | 설비 이상 규칙 추가 |
| DataProvider (ABC) | FactoryDataProvider | 공장 데이터 소스 추상화 |

---

## Project #9: NVIDIA Isaac Sim Integration

Kevin 순찰 로봇을 NVIDIA Isaac Sim에서 물리 시뮬레이션하고, ROS2 Bridge를 통해 기존 Dashboard와 연동합니다. Sim-to-Real 파이프라인으로 Physical AI 핵심 역량을 시연합니다.

### 프로젝트 개요

| 항목 | 내용 |
|------|------|
| Project Name | Kevin Robot Isaac Sim Digital Twin |
| Category | Physical AI / Simulation / Sim-to-Real |
| Tech Stack | NVIDIA Isaac Sim, Omniverse, ROS2 Humble/Jazzy, Python, URDF |
| Duration | 2–3주 |
| HW 요구 | NVIDIA RTX GPU (RTX 3070+), Ubuntu 22.04, 32GB+ RAM |
| 기존 연결 | Kevin 3D Sim → Isaac Sim 이전, Dashboard → ROS2 Bridge 연동 |
| Blog 키워드 | NVIDIA, Isaac Sim, Physical AI, Digital Twin, Sim-to-Real, ROS2 |

### 핵심 기능

- **URDF Robot Import:** Kevin 로봇 URDF 모델을 Isaac Sim에 임포트. 관절, 센서, 충돌 메시 설정
- **Warehouse Environment:** Isaac Sim 내장 Warehouse 에셋 + SimReady 자산으로 공장/창고 환경 구성
- **Sensor Simulation:** RTX LiDAR, RGB-D Camera, IMU 물리 기반 센서 시뮬레이션
- **ROS2 Bridge:** Isaac Sim ↔ ROS2 양방향 통신. /scan, /image_raw, /odom, /cmd_vel 토픽 발행/구독
- **Nav2 Navigation:** Occupancy Map 생성 → Nav2 경로 계획 → Waypoint Patrol 시뮬레이션
- **Synthetic Data Generation:** 합성 이미지/LiDAR 데이터 생성으로 낙상감지 모델 학습 데이터 확보

### Sim-to-Real 파이프라인

```
[1. URDF Import] → [2. Isaac Sim Environment] → [3. Sensor Setup]
        ↓                      ↓                       ↓
[4. ROS2 Bridge] → [5. Nav2 + SLAM] → [6. Dashboard 연동]
        ↓                      ↓                       ↓
[7. Synthetic Data] → [8. Model Training] → [9. Real Robot Deploy]
```

### 개발 타임라인 (2–3주)

| Phase | 기간 | 작업 내용 |
|-------|------|----------|
| 0 | Day 1–2 | Isaac Sim 설치 + ROS2 Workspace 구성 + ROS2 Bridge 확인 |
| 1 | Day 3–4 | Kevin URDF 제작 + Isaac Sim 임포트 + 관절 설정 |
| 2 | Day 5–7 | Warehouse 환경 구성 + LiDAR/Camera/IMU 센서 추가 |
| 3 | Day 8–10 | ROS2 Bridge 연결 + /scan, /odom, /image_raw 토픽 발행 |
| 4 | Day 11–13 | Nav2 Navigation + Occupancy Map + Waypoint Patrol |
| 5 | Day 14–16 | Dashboard 연동 (SIM → LIVE 모드 전환 테스트) |
| 6 | Day 17–18 | Synthetic Data 생성 + 문서화 + GitHub 배포 |

### Isaac Sim ↔ ROS2 토픽 매핑

| Isaac Sim Sensor | ROS2 Topic | Message Type | Dashboard Panel |
|-----------------|------------|--------------|-----------------|
| RTX LiDAR | /scan | LaserScan | Factory Floor Map |
| RGB Camera | /image_raw | Image | Camera Vision |
| Depth Camera | /depth | Image | 3D Reconstruction |
| IMU | /imu | Imu | Sensor Plot |
| Odometry | /odom | Odometry | Robot Position |
| Joint States | /joint_states | JointState | Robot Status |
| Nav2 Path | /nav2/path | Path | Floor Map Overlay |

---

## Project #10: Predictive Maintenance AI

IoT 센서 데이터 기반으로 설비 고장을 예측하는 ML 시스템. 진동, 온도, 압력, 전류 등 다채널 시계열 데이터를 분석하여 잔여 수명(RUL)을 예측하고, Smart Factory Dashboard와 연동합니다.

### 프로젝트 개요

| 항목 | 내용 |
|------|------|
| Project Name | Smart Factory Predictive Maintenance AI |
| Category | AI/ML / IoT / Time Series / Anomaly Detection |
| Tech Stack | Python, scikit-learn, XGBoost, LSTM, PyQt6, MQTT, pandas |
| Duration | 2주 |
| Dataset | NASA C-MAPSS (Turbofan), CWRU Bearing, Kaggle Predictive Maintenance |
| 기존 연결 | ST-GCN 학습 경험 + RF 비교 + Smart Factory Dashboard 연동 |
| Blog 키워드 | Predictive Maintenance, RUL, IoT, ML, Time Series, Smart Factory |

### 핵심 기능

- **Multi-Sensor Data Pipeline:** MQTT로 센서 데이터 수집 → pandas 전처리 → Feature Engineering
- **Anomaly Detection:** Isolation Forest + Autoencoder로 실시간 이상 패턴 감지
- **RUL Prediction:** LSTM + XGBoost 앙상블로 잔여 수명 예측. NASA C-MAPSS 데이터셋 학습
- **Model Comparison:** RF vs XGBoost vs LSTM vs Autoencoder 성능 비교 리포트 자동 생성
- **Dashboard Integration:** Smart Factory Dashboard에 Maintenance Panel 추가 — 설비별 건강도 게이지, RUL 예측치, 정비 스케줄 표시
- **Training GUI:** 기존 GUI 학습 인터페이스 재활용 — 모델 선택, 하이퍼파라미터 조정, 학습/평가 시각화

### ML 파이프라인

```
[Raw Sensor Data] → [Preprocessing] → [Feature Engineering]
       |                   |                    |
  MQTT/CSV           Cleaning,          Rolling stats,
  Ingestion         Normalization       FFT, Wavelets
                                              |
                    ┌─────────────┬───────────┬────────────┐
                    |  Anomaly    |  RUL         |  Health      |
                    |  Detection  |  Prediction  |  Score       |
                    | (IsoForest) | (LSTM+XGB)   | (Composite)  |
                    └─────────────┴─────────────┴────────────┘
                              |
                    [Dashboard + Alert System]
```

### 개발 타임라인 (2주)

| Phase | 기간 | 작업 내용 |
|-------|------|----------|
| 0 | Day 1–2 | NASA C-MAPSS + CWRU Bearing 데이터셋 분석 + EDA |
| 1 | Day 3–4 | Feature Engineering (Rolling stats, FFT, PCA) + 전처리 파이프라인 |
| 2 | Day 5–7 | Anomaly Detection (Isolation Forest + Autoencoder) 구현 |
| 3 | Day 8–10 | RUL Prediction (LSTM + XGBoost) 모델 학습 + 평가 |
| 4 | Day 11–12 | Model Comparison Report 자동 생성 (기존 비교 프레임워크 활용) |
| 5 | Day 13–14 | Dashboard Maintenance Panel 통합 + MQTT 실시간 연동 + 문서화 |

### 모델 비교 전략

기존 Home Safe Solution에서 확립한 RF vs ST-GCN 비교 프레임워크를 재활용:

| Model | Task | 장점 | 단점 | 적용 장면 |
|-------|------|------|------|----------|
| Random Forest | Anomaly | 빠른 추론, 해석 용이 | 시계열 약함 | 실시간 이상감지 |
| XGBoost | RUL | 고성능, 특징 중요도 | 순차 패턴 약함 | 잔여수명 예측 |
| LSTM | RUL | 시계열 패턴 학습 | 학습 느림 | 장기 열화 예측 |
| Iso Forest | Anomaly | 비지도, 라벨 불필요 | 임계값 튜닝 필요 | 신규 이상 탐지 |
| Autoencoder | Anomaly | 복잡 패턴 학습 | 학습 불안정 | 다채널 이상감지 |

---

## 블로그 포스팅 전략

10개 프로젝트 완성 후 주간 5편 포스팅 + 5편 예비 운영 전략:

### 1차 포스팅 (주간 1: 기존 프로젝트 5편)

| 요일 | 프로젝트 | 포스트 제목 (안) | 타겟 키워드 |
|------|---------|----------------|------------|
| 월 | Kevin Patrol Dashboard | PyQt6로 로봇 모니터링 대시보드 만들기 | ROS2, PyQt6, Dashboard |
| 화 | Home Safe Solution | ST-GCN 파인튜닝으로 낙상감지 91.89% 달성기 | ST-GCN, Fall Detection |
| 수 | Home Guard Bot | ROS2 + FastAPI로 Guard Brain LLM 노드 만들기 | ROS2, FastAPI, LLM |
| 목 | EyeCon (피노키오) | Ollama EXAONE 7.8B로 실시간 대화 분석 만들기 | LLM, Emotion AI |
| 금 | ROS2 Commander | 게임으로 배우는 ROS2 — Pygame 학습 게임 개발기 | ROS2, Education, Game |

### 예비 포스팅 (주간 1 예비: 5편)

- **Kevin 3D Sim:** Pygame + OpenGL로 3D 순찰 로봇 시뮬레이터 만들기
- **MyPet:** 핸드 제스처 인식 가상 반려견 개발기
- **Smart Factory Dashboard:** Physical AI 공장 모니터링 대시보드 구축기
- **Isaac Sim Integration:** NVIDIA Isaac Sim으로 Kevin 로봇 디지털 트윈 구축기
- **Predictive Maintenance:** IoT 센서 + ML로 설비 고장 예측 AI 만들기

### 순환 구조

```
[10개 프로젝트 축적] → [5편 포스팅 + 5편 예비]
      ↓                       ↓
[1주일간 포스팅]     [다음 주 5개 프로젝트 수행]
      ↓                       ↓
[10개 다시 축적] → [반복...]
```

---

## 통합 기술 스택 키워드

포트폴리오 전체를 관통하는 기술 키워드:

| 분류 | 기술 |
|------|------|
| 프레임워크 | ROS2 Jazzy, NVIDIA Isaac Sim, Omniverse, FastAPI |
| AI/ML | ST-GCN, LSTM, XGBoost, Random Forest, Isolation Forest, Autoencoder, YOLO |
| LLM | Ollama EXAONE 7.8B, guard_brain |
| Vision | OpenCV, MediaPipe, pyqtgraph, OpenGL |
| GUI | PyQt6, Pygame, pyqtgraph |
| 데이터 | pandas, numpy, scikit-learn, MQTT, JSON |
| 시뮬레이션 | Isaac Sim, Gazebo, Pygame+OpenGL, Digital Twin |
| 배포 | GitHub, GitHub Pages (Hugo), Docker |
| AIOps/MLOps | MLflow, Model Registry, CI/CD Pipeline, Prometheus, Grafana |
| Robot Network | DDS, Zenoh, MQTT, Fast-RTPS, CycloneDDS, Multi-Robot Mesh |
| Robot Security | SROS2, DDS Security, TLS/DTLS, Access Control, IDS |
| 키워드 | Physical AI, Smart Factory, Digital Twin, IoT, ROS2, NVIDIA, AIOps, 1인개발자 |

---

## Keyword #1: AIOps / MLOps

AIOps는 AI를 활용하여 IT/OT 운영을 자동화하는 방법론이며, MLOps는 ML 모델의 개발→배포→모니터링 전체 라이프사이클을 관리합니다. Smart Factory에서는 두 개념이 융합되어 설비 이상감지 모델의 자동 재학습, 프로덕션 라인 모니터링, 장애 예측 및 자동 복구를 실현합니다.

### 핵심 개념

- **MLOps:** ML 모델 버전 관리, 데이터 파이프라인, 자동 학습/배포, A/B 테스트, 모델 드리프트 감지
- **AIOps:** IT/OT 시스템 이상감지, 근본 원인 분석(RCA), 예측적 장애 대응, 알람 압축
- **LLMOps:** LLM 프롬프트 버전 관리, 비용 모니터링, 할루시네이션 필터링, RAG 파이프라인
- **AgentOps:** 자율 AI 에이전트 오케스트레이션 — 로봇 의사결정 로그, 툴 사용 추적

### Smart Factory 적용 방안

```
[Sensor Data] → [Data Pipeline] → [Feature Store]
                                        |
                              [Model Training (MLOps)]
                              - Experiment Tracking (MLflow)
                              - Model Registry + Versioning
                              - Auto Retrain on Drift
                                        |
                              [Model Serving (FastAPI/TF Serving)]
                                        |
                              [AIOps Monitoring Layer]
                              - Anomaly Detection on Predictions
                              - Alert Routing + Auto-Remediation
                              - Prometheus + Grafana Dashboard
```

### 프로젝트 연결점

| 기존 프로젝트 | AIOps/MLOps 확장 | 구현 방법 |
|-------------|-----------------|----------|
| #10 Predictive Maint. | MLOps 파이프라인 | MLflow 실험 추적 + 모델 레지스트리 |
| #8 Smart Factory Dash | AIOps 모니터링 | Grafana 패널 + 이상감지 알람 |
| #5 Home Guard Bot | LLMOps 적용 | guard_brain 프롬프트 버전 관리 |
| #3 Home Safe Solution | 모델 드리프트 감지 | ST-GCN 성능 모니터링 + 자동 재학습 |

---

## Keyword #2: Robot Network

다수 로봇 간 실시간 통신, 협조, 작업 분배를 위한 네트워크 아키텍처. ROS2는 DDS(Data Distribution Service) 미들웨어를 통해 분산 통신을 지원하며, Zenoh, Fast-RTPS, CycloneDDS 등의 구현체를 선택할 수 있습니다.

### 핵심 기술 비교

| Middleware | Protocol | 장점 | 단점 | 적용 장면 |
|-----------|----------|------|------|----------|
| Fast-RTPS | UDP/DDS | ROS2 기본, 안정적 | 대규모 트래픽 부하 | 소규모 멀티로봇 |
| CycloneDDS | UDP/DDS | 고성능, 저지연 | 설정 복잡도 | 산업용 실시간 |
| Zenoh | TCP/UDP | 최소 트래픽, 매시 네트워크 | 새로운 생태계 | 불안정 네트워크/탐사 |
| MQTT | TCP | 경량, IoT 표준 | QoS 제한적 | IoT 센서 데이터 수집 |
| DDS Disc. Server | UDP/DDS | 중앙 디스커버리 | 단일 장애점 | 100+ 로봇 플릿 |

### Multi-Robot 통신 격리 전략

- **Namespace Isolation:** 로봇별 고유 namespace로 토픽 충돌 방지 (/robot_01/scan, /robot_02/scan)
- **DDS Domain ID:** 로봇 그룹별 Domain ID 분리로 네트워크 격리 (최대 232개)
- **DDS Partition:** 토픽별 파티션 설정으로 세밀한 통신 제어
- **Discovery Server:** 중앙 디스커버리 서버로 대규모 플릿 관리 (Fast-DDS Discovery Server)
- **Zenoh Bridge:** ROS2 DDS ↔ Zenoh 브리지로 불안정 네트워크에서 통신 최적화

### Smart Factory 적용 아키텍처

```
[AGV 로봇 플릿]                [순찰 로봇 Kevin]
  /agv_01/odom                 /kevin/scan
  /agv_01/cmd_vel              /kevin/image_raw
       |                            |
       +--------- DDS/Zenoh --------+
                    |
          [Factory ROS2 Network]
          - Discovery Server
          - Namespace Isolation
          - QoS: RELIABLE + TRANSIENT_LOCAL
                    |
     [Smart Factory Dashboard (MQTT Bridge)]
```

---

## Keyword #3: Robot Security

로봇 시스템의 사이버 보안은 Physical AI 시대의 핵심 과제입니다. ROS2는 DDS Security 확장과 SROS2 툴을 통해 인증, 암호화, 접근 제어를 지원하지만, 여전히 취약점이 존재합니다.

### ROS2 보안 아키텍처

- **DDS Security Plugin:** DDS 통신 계층에서 인증(Authentication), 암호화(Encryption), 접근제어(Access Control) 제공
- **SROS2:** ROS2 그래프에 보안 정책을 적용하는 개발자 도구. CA 인증서, 권한 파일, Governance 파일 생성
- **Enclave:** 노드별 보안 경계 설정. 각 enclave는 고유 키 쌍과 x.509 인증서 보유
- **Governance:** 전체 DDS 트래픽 암호화 정책 정의 (default: encrypt all)
- **Permission:** 각 enclave가 publish/subscribe 가능한 토픽을 명시적으로 제한

### 알려진 취약점 및 위협

| 취약점 유형 | 설명 | SROS2 방어 여부 |
|-----------|------|----------------|
| Topic Sniffing | 비인증 노드가 토픽 목록 및 데이터 도청 | ✅ SROS2 적용 시 차단 |
| Topic Injection | 악의적 메시지 발행으로 로봇 오동작 유도 | ✅ SROS2 적용 시 차단 |
| Service Flooding | DDS Service 대량 요청으로 DoS 공격 | ⚠️ 부분적 방어 (요청 제한 필요) |
| Keystore Exfiltration | 공급망 공격으로 SROS2 인증서 탈취 | ❌ SROS2로 방어 불가 |
| Discovery Spoofing | 가짜 노드 등록으로 네트워크 침투 | ⚠️ 부분적 방어 |
| Parameter Tampering | 로봇 파라미터 무단 변경 | ✅ SROS2 적용 시 차단 |
| Authorized Node Attack | 인증된 노드가 권한 범위 내 악의적 행위 | ❌ 방어 불가 (행위 감지 필요) |

### Smart Factory 보안 적용 방안

- **Phase 1 - SROS2 기본 적용:** Kevin 순찰 로봇 그래프에 SROS2 보안 정책 적용 (Nav2 + SLAM 그래프 보안)
- **Phase 2 - 네트워크 분리:** DDS Domain ID + Namespace로 공장 영역별 통신 격리
- **Phase 3 - IDS 구축:** ros2_tracing + ML 기반 이상 행위 감지 (Anomaly Detection on ROS2 traces)
- **Phase 4 - 공급망 보안:** 패키지 무결성 검증, 인증서 순환 정책, Secure Boot

---

## 최신 논문 리뷰 (Keyword별)

각 키워드별 핵심 논문과 Smart Factory 프로젝트 연결점:

### 1. AIOps / MLOps 논문

#### [P1] A Joint Study of the Challenges, Opportunities, and Roadmap of MLOps and AIOps
**ACM Computing Surveys, 2024 | SLR 93편 분석**

- **핵심:** MLOps와 AIOps의 과제/기회/로드맵을 체계적으로 정리. 44,903건 → 93편 필터링.
- **발견:** AIOps는 5G/6G 등 복잡 환경에서 발전 중. MLOps는 전통 산업 환경에서 더 활발. 배포 단계에서 AIOps 활용은 아직 미흡한 상황.
- **프로젝트 연결:** #10 Predictive Maintenance의 MLOps 파이프라인 설계 참고. 모델 버전 관리 + 자동 재학습 구현 방향 제시.

#### [P2] The Complete MLOps/LLMOps Roadmap for 2026
**Medium (Sanjeeb Panda), Jan 2026 | 로드맵 가이드**

- **핵심:** 2026년 MLOps → LLMOps → AgentOps로 진화하는 로드맵. Foundation Model + RAG + Guardrail 오케스트레이션 필수.
- **발견:** 프로덕션 AI 시스템은 더 이상 단일 모델이 아닌 복합 컴포넌트 오케스트레이션 필요.
- **프로젝트 연결:** #5 Home Guard Bot의 guard_brain LLMOps 적용. 프롬프트 버전 관리 + 비용 모니터링 구현 참고.

### 2. Robot Network 논문

#### [P3] Communication Isolation For Multi-Robot Systems Using ROS2
**ACM SAC 2025 (IRMAS Track) | 멀티로봇 통신 격리**

- **핵심:** ROS2에서 멀티로봇 통신 격리 방법 4가지 비교 — Domain ID, Namespace, DDS Partition, Zenoh Bridge.
- **발견:** Zenoh가 네트워크 트래픽 최소화에 유리. DDS Partition은 세밀한 토픽별 제어 가능. 100+ 로봇 시 Domain ID 충돌 위험.
- **프로젝트 연결:** #8 Smart Factory 내 다수 로봇(AGV + Kevin + ARM) 통신 격리 설계에 직접 적용.

#### [P4] Performance Comparison of ROS2 Middlewares for Multi-robot Mesh Networks
**J. Intelligent & Robotic Systems, 2025 | Springer | RMW 성능 비교**

- **핵심:** FastRTPS vs CycloneDDS vs Zenoh의 매시 네트워크 성능 비교. 행성 탐사 등 극한 환경 시나리오.
- **발견:** Zenoh가 지연, 도달성, 데이터 오버헤드, CPU 사용률 모두에서 우수. 불안정 네트워크에서도 안정적.
- **프로젝트 연결:** #9 Isaac Sim에서 Zenoh Bridge 테스트 및 #8 Factory 네트워크 RMW 선택 근거 자료.

#### [P5] A Systematic Literature Review of DDS Middleware in Robotic Systems
**MDPI Robotics, May 2025 | SLR 2006–2024 | DDS 종합 조사**

- **핵심:** DDS 미들웨어의 로봇 응용 및 과제를 체계적으로 분석. 멀티로봇 협조, 실시간 처리, 클라우드-엣지 아키텍처 등.
- **발견:** 보안 취약성, 성능/확장성 요구사항, 실시간 데이터 전송 복잡성이 주요 과제로 도출.
- **프로젝트 연결:** Smart Factory 전체 DDS 아키텍처 설계 + QoS 정책 수립 참고 자료.

#### [P6] ROS2 DDS 통신 지연 최적화 수식 (DGIST, IEEE INFOCOM 2025)
**Park Kyung-joon 연구팀, IEEE INFOCOM 2025 | 세계 최초 DDS 성능 최적화 수식**

- **핵심:** ROS2 DDS의 신뢰성 전송 구조(heartbeat/data period)에 대한 지연 모델 수식 제안.
- **발견:** 35개 시나리오에서 평균 3.7% 오차로 실측값 일치. 통신 파라미터 설정이 로봇 성능에 결정적 영향.
- **프로젝트 연결:** #8/#9 프로젝트의 ROS2 QoS 파라미터 튜닝 시 직접 활용 가능한 수식.

### 3. Robot Security 논문

#### [P7] On the (In)Security of Secure ROS2
**ACM CCS 2022 | Deng et al. (NTU) | ROS2 보안 핵심 논문**

- **핵심:** SROS2의 보안 매커니즘을 형식 검증(CSP#)으로 분석하여 취약점 발견. 물리 멀티로봇 테스트베드에서 검증.
- **발견:** 공격자가 SROS2 보안을 완전히 무효화하고 미인가 권한 획득 / 정보 탈취 가능. Private Broadcast Encryption 기반 방어책 제안.
- **프로젝트 연결:** Kevin 순찰 로봇의 Nav2+SLAM 그래프 보안 적용 시 이 논문의 취약점 테스트케이스 참고.

#### [P8] Formal Analysis and Detection for ROS2 Communication Security Vulnerability
**MDPI Electronics, May 2024 | Yang et al. | ROS2 통신 보안 취약점 7개 분석**

- **핵심:** ROS2 통신 메커니즘 기반 7개 보안 취약점 정의 + ROS2Tester 검증 도구 개발.
- **발견:** SROS2 적용 시 비인증 공격 차단 가능하나, 인증된 노드의 악의적 행위는 여전히 방어 불가. 행위 기반 감지 필요.
- **프로젝트 연결:** Smart Factory 보안 Phase 3 (IDS 구축) 설계 시 ROS2Tester 방법론 참고.

#### [P9] Supply Chain Exploitation of Secure ROS 2 Systems
**ResearchGate, Oct 2025 | 공급망 공격 PoC**

- **핵심:** 트로잔화된 sros2 CLI로 keystore 탈취 → DNS 엑스필트레이션 → 인증된 노드로 스푸핑 공격 성공.
- **발견:** SROS2의 공급망 보안이 취약. 패키지 무결성 검증과 Secure Boot가 필수적임을 실증.
- **프로젝트 연결:** Smart Factory 보안 Phase 4 (공급망 보안) 설계 시 이 공격 시나리오 방어 필수.

#### [P10] ROS 2 in a Nutshell: A Survey
**Preprints.org, May 2025 | 7,371편 중 435편 ROS2 특화 분석 | 최대 규모 서베이**

- **핵심:** ROS1→ROS2 전환의 아키텍처, 미들웨어, 실시간, 보안, 멀티로봇 분야 종합 서베이. 435편 체계적 분석.
- **발견:** 보안(SROS2), 실시간 처리, 멀티로봇 시스템이 주요 연구 방향. 마이그레이션 복잡성과 결정적 실행 문제가 주요 배리어.
- **프로젝트 연결:** 전체 Smart Factory 프로젝트의 ROS2 아키텍처 설계 및 블로그 기술 게시물 참고 자료.

### 논문 요약 테이블

| # | 논문 | 출처/년도 | Keyword | 프로젝트 연결 |
|---|------|----------|---------|------------|
| P1 | MLOps & AIOps Challenges (SLR) | ACM CS, 2024 | AIOps/MLOps | #10 MLOps Pipeline |
| P2 | MLOps/LLMOps Roadmap 2026 | Medium, 2026 | AIOps/MLOps | #5 LLMOps |
| P3 | Multi-Robot Comm. Isolation | ACM SAC, 2025 | Robot Network | #8 Factory Network |
| P4 | ROS2 RMW Mesh Comparison | Springer, 2025 | Robot Network | #9 Isaac Sim RMW |
| P5 | DDS Middleware in Robotics (SLR) | MDPI, 2025 | Robot Network | #8 DDS Architecture |
| P6 | ROS2 DDS Delay Optimization | INFOCOM, 2025 | Robot Network | #8/#9 QoS Tuning |
| P7 | (In)Security of Secure ROS2 | ACM CCS, 2022 | Robot Security | Kevin SROS2 적용 |
| P8 | ROS2 Comm. Vuln. Analysis (7) | MDPI, 2024 | Robot Security | IDS 구축 Phase 3 |
| P9 | Supply Chain Exploitation PoC | ResearchGate, 2025 | Robot Security | 공급망 보안 Phase 4 |
| P10 | ROS 2 in a Nutshell (435편) | Preprints, 2025 | All Keywords | 전체 아키텍처 |

---

## 즉시 실행 체크리스트

오늘부터 시작할 수 있는 액션 아이템:

### Project #8: Smart Factory Dashboard

- [ ] Kevin Dashboard v3.2 코드베이스 복사 + 공장 도메인 리네이밍
- [ ] FactoryDataProvider ABC 인터페이스 정의 (get_production_status, get_sensor_heatmap 등)
- [ ] MQTT 브로커 설치 (mosquitto) + 테스트 센서 발행기 작성
- [ ] Factory Floor 2D 맵 데이터 설계 (JSON: 스테이션, 로봇, 컨베이어 위치)

### Project #9: Isaac Sim Integration

- [ ] NVIDIA Isaac Sim 설치 + GPU 호환성 확인 (RTX 3070+)
- [ ] Kevin 로봇 URDF 파일 제작 (링크, 조인트, 메시 정의)
- [ ] ROS2 Humble Workspace 구성 + Isaac Sim ROS2 Bridge 테스트
- [ ] Warehouse 환경 에셋 선택 + 커스터마이징

### Project #10: Predictive Maintenance AI

- [ ] NASA C-MAPSS 데이터셋 다운로드 + EDA 노트북 작성
- [ ] CWRU Bearing 데이터셋 분석 + 진동 신호 시각화
- [ ] Feature Engineering 파이프라인 설계 (config → preprocessor → trainer)
- [ ] 기존 Model Compare Report 프레임워크 복사 + PdM 용 수정
