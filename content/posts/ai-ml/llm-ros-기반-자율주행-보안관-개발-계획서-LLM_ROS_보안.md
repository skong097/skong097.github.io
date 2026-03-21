---
title: "🤖 LLM + ROS 기반 자율주행 보안관 — 개발 계획서"
date: 2026-03-21
draft: true
tags: ["ai-ml", "llm"]
categories: ["ai-ml"]
description: "> **프로젝트명:** Home Guard Bot (가칭) > **작성일:** 2026-02-12 > **수정일:** 2026-02-13"
---

# 🤖 LLM + ROS 기반 자율주행 보안관 — 개발 계획서

> **프로젝트명:** Home Guard Bot (가칭)
> **작성일:** 2026-02-12
> **수정일:** 2026-02-13
> **작성자:** stephen.kong
> **개발 루트:** `/home/gjkong/dev_ws/ironman`
> **상태:** Phase 1 진행 중

---

## 1. 프로젝트 개요

### 1.1 목적

가정 내 고령자, 아동, 반려동물의 안전을 실시간으로 모니터링하는 **자율 순찰 로봇**을 개발한다. 단순 이동이 아닌, Vision AI 기반 **지능형 보안** 역할을 수행하며, LLM을 활용한 **상황 인지 및 자연어 상호작용**을 통해 차별화된 사용자 경험을 제공한다.

### 1.2 핵심 가치

기존 Home Safe Solution 프로젝트에서 구축한 **낙상 감지 기술 (RF + ST-GCN 듀얼 모델)**을 로봇 플랫폼에 탑재하여, 고정 카메라의 한계를 넘어 **능동적 순찰 + 실시간 감지**를 구현한다.

### 1.3 기존 자산 활용

| 기존 프로젝트 | 활용 방식 |
|--------------|----------|
| Random Forest 낙상 감지 (F1 94.5%) | 프레임 단위 즉시 감지 — 로봇 온보드 추론 |
| ST-GCN Fine-tuned (Acc 99.63%) | 60-프레임 시계열 분석 — 서버 측 정밀 판단 |
| YOLO11s-Pose | 키포인트 추출 파이프라인 재사용 |
| PyQt6 GUI + MySQL DB | 관제 대시보드 확장 |
| path_config.py 경로 관리 체계 | 동일 패턴 적용 |

---

## 2. 핵심 기능 (Functional Specifications)

### 2.1 지능형 낙상 감지 (Elderly Care)

거실, 침실을 순찰하다가 사람이 바닥에 쓰러져 있는 포즈를 감지하면, 즉시 경보를 울리고 등록된 보호자에게 위치 정보를 전송한다.

- **감지 모델:** RF (즉시) + ST-GCN (정밀) 듀얼 파이프라인
- **알림 체계:** 1차 음성 경고 → 2차 보호자 메시지 → 3차 긴급 호출
- **로봇 행동:** 감지 위치에 정지 → 카메라로 상황 녹화 → 서버 전송

### 2.2 미등록자 침입 알림

집 내부에 등록되지 않은 얼굴이 포착될 경우 사진을 촬영하여 실시간으로 전송한다.

- **기술:** Face Recognition (dlib/InsightFace) + 등록 얼굴 DB
- **시나리오:** 미등록 얼굴 감지 → 사진 캡처 → 보호자 앱/PC에 즉시 전송
- **예외 처리:** 마스크 착용, 저조도 환경 대응

### 2.3 위험 구역 접근 제한

주방(가스레인지), 베란다 등 위험 구역에 아이나 반려동물이 접근하면 로봇이 음성으로 경고를 보낸다.

- **구현:** 사전 정의된 위험 구역 좌표 (SLAM 맵 기반)
- **감지 대상:** YOLO 기반 사람/동물 객체 + 구역 진입 판단
- **경고:** TTS 음성 출력 + 관제 대시보드 알림

### 2.4 PyQt6 기반 원격 관제 대시보드

PC에서 로봇의 카메라 화면을 실시간으로 보고, 수동으로 로봇을 조종하거나 센서 데이터를 확인할 수 있다.

- **실시간 스트리밍:** 로봇 카메라 영상 (WebSocket/MJPEG)
- **수동 조작:** 가상 조이스틱 (전진/후진/회전/정지)
- **센서 모니터링:** 온도, 습도, 가스, 배터리 잔량
- **이벤트 이력:** 순찰 로그, 감지 이벤트 타임라인

### 2.5 LLM 상황 인지 및 상호작용

- **상황 요약:** "지금 거실 상태가 어때?" → LLM이 카메라 + 센서 데이터 종합하여 자연어 응답
- **순찰 보고:** 매 순찰 완료 시 LLM이 상황 보고서 자동 생성
- **음성 대화:** "누구냐! 손 들어!", "순찰 중 이상 무!" 같은 보안관 컨셉 대사

---

## 3. 시스템 아키텍처

### 3.1 전체 구조

```
┌─────────────────────────────────────────────────────┐
│                   관제 PC (PyQt6)                    │
│  ┌───────────┐ ┌──────────┐ ┌────────────────────┐  │
│  │ 영상 뷰어  │ │ 조이스틱  │ │ 이벤트/센서 대시보드 │  │
│  └─────┬─────┘ └────┬─────┘ └─────────┬──────────┘  │
│        └────────────┼────────────────┘              │
│                     │ TCP/WebSocket                  │
└─────────────────────┼───────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────┐
│          상위 제어기 (Main Brain)                     │
│          Laptop / Mini PC (Ubuntu + ROS2)            │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌────────┐  │
│  │ YOLO Pose│ │ RF/ST-GCN│ │ Ollama  │ │ SLAM   │  │
│  │ 객체인식  │ │ 낙상감지  │ │  LLM    │ │Nav2    │  │
│  └────┬─────┘ └────┬─────┘ └────┬────┘ └───┬────┘  │
│       └────────────┼───────────┼──────────┘        │
│                    │ ROS2 Topics                     │
│  ┌─────────────────┼───────────────────────────┐    │
│  │            ROS2 통신 레이어                    │    │
│  │   /cmd_vel  /camera  /sensor  /alert         │    │
│  └─────────────────┬───────────────────────────┘    │
└────────────────────┼────────────────────────────────┘
                     │ Serial / Wi-Fi
┌────────────────────┼────────────────────────────────┐
│          하위 제어기 (Body)                           │
│          ESP32 / Arduino                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ 모터제어  │ │ 초음파    │ │ 환경센서  │            │
│  │ L298N    │ │ 장애물회피 │ │ 온습도/가스│            │
│  └──────────┘ └──────────┘ └──────────┘            │
└─────────────────────────────────────────────────────┘
```

### 3.2 상위 제어기 (Main Brain)

로봇에 탑재되는 메인 컴퓨팅 유닛.

| 구성 요소 | 기술 | 역할 |
|----------|------|------|
| 비전 처리 | YOLO11s-Pose + MediaPipe | 객체 인식, 키포인트 추출 |
| 낙상 감지 | RF + ST-GCN | 듀얼 모델 추론 |
| 자율 주행 | ROS2 + Nav2 + SLAM | 경로 계획, 장애물 회피, 자율 순찰 |
| 지능형 판단 | Ollama (EXAONE 3.5 7.8B) | 상황 인지, 자연어 보고서, 의사결정 |
| 음성 출력 | TTS (gTTS / Piper) | 보안관 대사, 경고 음성 |
| 통신 서버 | ROS2 + WebSocket | 관제 PC와 실시간 데이터 교환 |

### 3.3 하위 제어기 (Body)

물리적 구동 및 센서 수집 담당.

| 구성 요소 | 하드웨어 | 역할 |
|----------|---------|------|
| MCU | ESP32 (Wi-Fi 내장) | 모터 제어, 센서 통합 |
| 구동부 | DC 모터 + L298N 드라이버 | 차동 구동 (2WD/4WD) |
| 장애물 회피 | HC-SR04 초음파 센서 ×3 | 전방/좌/우 거리 측정 |
| 환경 센서 | DHT22 + MQ-2 | 온습도, 가스 감지 |
| 전원 | LiPo 배터리 + 전압 분배기 | 배터리 잔량 모니터링 |
| 카메라 | USB 웹캠 or RPi 카메라 | 상위 제어기에 직접 연결 |

### 3.4 통신 구조

```
관제 PC  ←── WebSocket (영상/제어/이벤트) ──→  상위 제어기 (ROS2)
                                                    │
                                              micro-ROS / Serial
                                                    │
                                              하위 제어기 (ESP32)
```

| 구간 | 프로토콜 | 데이터 |
|------|---------|--------|
| 관제 PC ↔ 상위 제어기 | WebSocket (TCP) | 영상 스트림, 조작 명령, 센서 데이터, 이벤트 알림 |
| 상위 제어기 ↔ 하위 제어기 | micro-ROS (Serial/Wi-Fi) | /cmd_vel (속도 명령), /sensor (센서 데이터) |
| ROS2 내부 | Topic/Service/Action | SLAM, Navigation, Vision 노드 간 통신 |

---

## 4. 기술 스택

| 구분 | 기술 | 구현 내용 |
|------|------|----------|
| 비전 AI | YOLO11s-Pose + MediaPipe | 사람 식별 및 Pose Landmark 기반 낙상 감지 |
| 낙상 감지 | RF + ST-GCN | 프레임 즉시(RF) + 시계열 정밀(ST-GCN) 듀얼 판단 |
| 얼굴 인식 | InsightFace or dlib | 등록/미등록 얼굴 판별 |
| 자율 주행 | ROS2 Jazzy + Nav2 | SLAM 맵 기반 자율 순찰 경로 계획 |
| LLM | Ollama + EXAONE 3.5 7.8B | 상황 인지, 자연어 보고서, 음성 대화 |
| 음성 | gTTS / Piper TTS | 보안관 컨셉 대사, 경고 음성 출력 |
| 제어/통신 | Python (ROS2 rclpy) + micro-ROS | PC-ESP32 간 실시간 명령 하달 |
| GUI | PyQt6 | 로봇 시야 스트리밍, 센서 모니터링, 수동 조작 조이스틱 |
| DB | MySQL 8.0 | 순찰 로그, 이벤트 이력, 사용자 관리 |
| 하드웨어 | ESP32 + 모터 + 센서 | 무선 통신을 활용한 구동 및 환경 감지 |

---

## 5. 개발 단계 (Phase Plan)

### Phase 1: 기반 구축 (2주)

> 목표: ROS2 환경 세팅 + LLM 연동 검증 + guard_brain 노드 구축

**상위 제어기:**
- ~~ROS2 Jazzy 설치 및 워크스페이스 구성~~ ✅ 완료
- USB 카메라 ROS2 노드 (`usb_cam`) 연동
- 기본 텔레오퍼레이션: 키보드 → /cmd_vel 퍼블리시

**LLM 연동 (선행 검증):** ✅ 완료
- ~~Ollama + EXAONE 3.5 7.8B 설치 및 검증~~ ✅
- ~~보안관 시스템 프롬프트 설계 (few-shot + 4등급 판단)~~ ✅
- ~~FastAPI v0.2 API 서버 (JSON 파싱 + TTS 대사 생성)~~ ✅
- ~~ROS2 guard_brain 패키지 생성 (brain_node + sensor_sim_node)~~ ✅
- ~~ROS2 + Ollama 통합 테스트 (4개 시나리오 전체 성공)~~ ✅

**통합 테스트 결과 (2026-02-13):**

| 시나리오 | 등급 | TTS 대사 | 추론 시간 |
|---------|------|---------|----------|
| 거실 정상 | [정상] | "정상 상태입니다. 계속 감시하겠습니다." | ~14초 |
| 침실 낙상 | [위험] | "위험! 낙상 감지, 즉시 확인하세요." | ~17초 |
| 주방 가스 | [경고] | "경고! 가스 누출 위험, 가스 차단하세요." | ~16초 |
| 베란다 무인 | [주의] | "주의! 습도 높고 배터리 충전 확인 필요." | ~14초 |

**하위 제어기:** (미착수)
- ESP32 + L298N 모터 드라이버 회로 구성
- micro-ROS 또는 rosserial 기반 /cmd_vel 구독 → 모터 제어
- 초음파 센서 3개 연동 → /sensor 퍼블리시

**알려진 이슈:**
- ROS2 엔트리포인트 shebang 문제: `ros2 run` 대신 `python -m` 방식으로 우회 중
- EXAONE 3.5 추론 시간 14~18초 — 실시간 대응에는 느림 → 룰 기반 즉시 판단 + LLM 비동기 보고서 방식 검토

**산출물:**
- ~~guard_brain 노드 ROS2 통합 테스트 성공~~ ✅
- 키보드로 로봇 이동 제어 가능 (미착수)
- 카메라 영상 ROS2 토픽 확인 (미착수)

---

### Phase 2: SLAM + 자율 주행 (2주)

> 목표: 맵 생성 + 자율 순찰 경로

**SLAM:**
- LiDAR (RPLiDAR A1) 또는 Depth Camera (RealSense D435) 선택
- `slam_toolbox` 또는 `cartographer`로 2D 맵 생성
- 실내 환경 맵핑 및 저장

**Navigation:**
- Nav2 스택 설정 (planner + controller + recovery)
- 웨이포인트 기반 순찰 경로 정의
- 장애물 동적 회피 (costmap + 초음파 퓨전)

**위험 구역:**
- SLAM 맵 위에 위험 구역 폴리곤 정의 (주방, 베란다 등)
- 구역 진입 감지 로직 구현

**산출물:**
- 실내 맵 생성 완료
- 웨이포인트 3~5개 순환 순찰 동작
- 위험 구역 정의 및 접근 감지

---

### Phase 3: Vision AI 통합 (2주)

> 목표: 기존 낙상 감지 모델 ROS2 노드화 + 얼굴 인식

**낙상 감지 노드:**
- `/camera/image_raw` 구독 → YOLO Pose → 키포인트 추출
- RF 모델: 프레임 단위 즉시 판단 (로봇 온보드)
- ST-GCN: 60프레임 버퍼 → 정밀 판단
- 감지 결과 `/fall_detection` 토픽 퍼블리시

**얼굴 인식 노드:**
- 등록 얼굴 DB 구축 (사전 등록)
- 실시간 얼굴 매칭 → 미등록자 감지 시 `/intruder_alert` 퍼블리시

**위험 구역 경고:**
- 사람/동물 감지 + 로봇 위치 + 구역 맵 → 접근 판단
- TTS 경고 음성 출력

**산출물:**
- 순찰 중 낙상 감지 → 정지 + 알림
- 미등록 얼굴 → 사진 캡처 + 전송
- 위험 구역 접근 → 음성 경고

---

### Phase 4: LLM 통합 + 음성 (1주)

> 목표: guard_brain 고도화 + 보안관 컨셉 음성 노드

**LLM 연동:** (Phase 1에서 기본 검증 완료)
- ~~Ollama + EXAONE 3.5 7.8B 로컬 설치~~ ✅ Phase 1 완료
- ~~ROS2 guard_brain 노드: 센서 데이터 → LLM → JSON 응답~~ ✅ Phase 1 완료
- 추론 속도 개선: 룰 기반 즉시 판단 + LLM 비동기 보고서
- ROS2 Service 인터페이스 (`/guard/ask_llm`) 구현
- 프롬프트 고도화: 카메라 감지 결과 연동

**보안관 컨셉 대사:**
- 상황별 대사 템플릿 정의
- TTS 출력 (gTTS 또는 Piper 오프라인 TTS)
- 순찰 시작: "순찰을 시작합니다."
- 이상 감지: "경고! 이상 징후를 감지했습니다."
- 침입자: "미등록 인원 발견! 확인 바랍니다."
- 순찰 완료: "순찰 완료. 이상 없습니다."

**순찰 보고서:**
- 매 순찰 완료 시 LLM이 요약 생성 → DB 저장

**산출물:**
- "거실 상태 보고해" → 자연어 응답
- 상황별 TTS 음성 출력
- 순찰 보고서 자동 생성

---

### Phase 5: 관제 대시보드 (2주)

> 목표: PyQt6 통합 관제 시스템

**실시간 모니터링:**
- 로봇 카메라 영상 스트리밍 (WebSocket → QLabel)
- 로봇 위치 맵 오버레이 (SLAM 맵 + 현재 위치)
- 센서 데이터 실시간 표시 (온도, 습도, 가스, 배터리)

**수동 조작:**
- 가상 조이스틱 위젯 (마우스/키보드 → /cmd_vel)
- 긴급 정지 버튼
- 웨이포인트 클릭 이동 (맵 위 클릭 → 네비게이션 Goal)

**이벤트 관리:**
- 감지 이벤트 타임라인 (낙상, 침입, 구역이탈)
- 이벤트 상세: 캡처 이미지, 시간, 위치, 조치 상태
- 순찰 로그 + LLM 보고서 조회

**알림 체계:**
- 데스크탑 알림 (QSystemTrayIcon)
- 보호자 SMS/메시지 발송 (SolAPI 연동)

**산출물:**
- 통합 관제 대시보드 완성
- 실시간 영상 + 맵 + 센서 + 이벤트 한눈에 확인

---

### Phase 6: 통합 테스트 + 최적화 (1주)

> 목표: 전체 시나리오 테스트 + 안정성 확보

**시나리오 테스트:**
- 시나리오 A: 순찰 중 낙상 감지 → 정지 → 알림 → 보호자 전송
- 시나리오 B: 미등록자 침입 → 사진 캡처 → 즉시 전송
- 시나리오 C: 아이 주방 접근 → 음성 경고 → 관제 알림
- 시나리오 D: 배터리 저하 → 자동 복귀

**성능 최적화:**
- 추론 속도 최적화 (YOLO TensorRT, RF n_jobs 조정)
- 통신 지연 최소화
- 배터리 소모 최적화 (비순찰 시 저전력 모드)

**자동 복귀:**
- 배터리 잔량 임계치 설정 → 충전 도크 위치로 Nav2 Goal
- 충전 중 저전력 감시 모드

**산출물:**
- 4개 시나리오 정상 동작 확인
- 데모 영상 촬영

---

## 6. 하드웨어 BOM (Bill of Materials)

| 품목 | 모델/사양 | 수량 | 용도 |
|------|----------|------|------|
| 메인 컴퓨터 | Jetson Orin Nano / 노트북 | 1 | 비전 AI + ROS2 + LLM |
| MCU | ESP32-WROOM-32 | 1 | 모터 제어, 센서 수집 |
| 카메라 | USB 웹캠 (720p+) | 1 | 비전 입력 |
| LiDAR | RPLiDAR A1 | 1 | SLAM 맵핑 (선택) |
| 깊이 카메라 | Intel RealSense D435 | 1 | SLAM 대안 (선택) |
| 모터 드라이버 | L298N | 1 | DC 모터 제어 |
| DC 모터 | JGA25-370 + 바퀴 | 2~4 | 차동 구동 |
| 초음파 센서 | HC-SR04 | 3 | 장애물 회피 |
| 온습도 센서 | DHT22 | 1 | 환경 모니터링 |
| 가스 센서 | MQ-2 | 1 | 가스 누출 감지 |
| 배터리 | LiPo 11.1V 5000mAh | 1 | 전원 |
| 스피커 | USB/Bluetooth 스피커 | 1 | TTS 음성 출력 |
| 프레임 | 로봇 차체 (3D 프린트/알루미늄) | 1 | 본체 |

---

## 7. 소프트웨어 구조 (ROS2 패키지)

```
home_guard_ws/
├── src/
│   ├── guard_bringup/           # Launch 파일, 파라미터
│   │   ├── launch/
│   │   │   ├── robot_bringup.launch.py
│   │   │   ├── navigation.launch.py
│   │   │   └── full_system.launch.py
│   │   └── config/
│   │       ├── nav2_params.yaml
│   │       ├── slam_params.yaml
│   │       └── patrol_waypoints.yaml
│   │
│   ├── guard_vision/            # 비전 AI 노드
│   │   ├── guard_vision/
│   │   │   ├── yolo_pose_node.py        # YOLO Pose 키포인트 추출
│   │   │   ├── fall_detection_node.py   # RF + ST-GCN 낙상 감지
│   │   │   ├── face_recognition_node.py # 얼굴 인식/미등록자 감지
│   │   │   └── zone_monitor_node.py     # 위험 구역 접근 감지
│   │   └── models/                      # 학습된 모델 파일
│   │
│   ├── guard_brain/             # LLM + 의사결정 노드
│   │   └── guard_brain/
│   │       ├── llm_service_node.py      # Ollama LLM 연동
│   │       ├── situation_analyzer.py    # 상황 종합 판단
│   │       └── patrol_manager_node.py   # 순찰 스케줄 관리
│   │
│   ├── guard_voice/             # 음성 출력 노드
│   │   └── guard_voice/
│   │       ├── tts_node.py              # TTS 음성 합성
│   │       └── voice_lines.yaml         # 보안관 대사 템플릿
│   │
│   ├── guard_hw/                # 하드웨어 인터페이스
│   │   └── guard_hw/
│   │       ├── esp32_bridge_node.py     # ESP32 시리얼/WiFi 브리지
│   │       └── sensor_aggregator.py     # 센서 데이터 통합
│   │
│   ├── guard_dashboard/         # PyQt6 관제 대시보드
│   │   └── guard_dashboard/
│   │       ├── main.py
│   │       ├── main_window.py
│   │       ├── camera_view.py           # 실시간 영상
│   │       ├── map_view.py              # SLAM 맵 + 로봇 위치
│   │       ├── joystick_widget.py       # 수동 조작
│   │       ├── sensor_panel.py          # 센서 모니터링
│   │       └── event_timeline.py        # 이벤트 이력
│   │
│   └── guard_msgs/              # 커스텀 메시지/서비스 정의
│       ├── msg/
│       │   ├── FallDetection.msg
│       │   ├── IntruderAlert.msg
│       │   └── SensorData.msg
│       └── srv/
│           ├── AskLLM.srv
│           └── PatrolCommand.srv
│
├── path_config.py               # 경로 중앙 관리
└── README.md
```

---

## 8. ROS2 토픽/서비스 설계

### 8.1 Topics

| 토픽 이름 | 메시지 타입 | 방향 | 설명 |
|----------|-----------|------|------|
| `/camera/image_raw` | sensor_msgs/Image | Pub | 카메라 원본 영상 |
| `/cmd_vel` | geometry_msgs/Twist | Sub | 이동 속도 명령 |
| `/scan` | sensor_msgs/LaserScan | Pub | LiDAR 스캔 데이터 |
| `/guard/fall_detection` | guard_msgs/FallDetection | Pub | 낙상 감지 결과 |
| `/guard/intruder_alert` | guard_msgs/IntruderAlert | Pub | 침입자 알림 |
| `/guard/sensor_data` | guard_msgs/SensorData | Pub | 환경 센서 통합 |
| `/guard/tts_command` | std_msgs/String | Sub | TTS 출력 요청 |
| `/guard/patrol_status` | std_msgs/String | Pub | 순찰 상태 |

### 8.2 Services

| 서비스 이름 | 타입 | 설명 |
|-----------|------|------|
| `/guard/ask_llm` | guard_msgs/AskLLM | LLM에 상황 질의 |
| `/guard/patrol_command` | guard_msgs/PatrolCommand | 순찰 시작/정지/복귀 |

---

## 9. 보안관 컨셉 요소

### 9.1 음성 인터랙션

| 상황 | 대사 |
|------|------|
| 순찰 시작 | "순찰을 시작합니다. 안전을 지키겠습니다." |
| 순찰 완료 | "순찰 완료. 이상 없습니다." |
| 낙상 감지 | "위험 감지! 쓰러진 분이 있습니다. 긴급 연락 중입니다." |
| 미등록자 | "경고! 미확인 인원을 감지했습니다. 신원을 확인하세요." |
| 위험 구역 접근 | "위험 구역입니다! 뒤로 물러서세요." |
| 배터리 저하 | "배터리가 부족합니다. 충전소로 복귀합니다." |
| LLM 보고 | (동적 생성) "현재 거실에 1명이 있으며, 온도 24도, 이상 징후 없습니다." |

### 9.2 순찰 로그

MySQL에 매 순찰 결과를 저장한다.

```sql
CREATE TABLE patrol_logs (
    patrol_id INT AUTO_INCREMENT PRIMARY KEY,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    waypoints_visited INT,
    persons_detected INT,
    events_detected INT,
    llm_summary TEXT,          -- LLM 생성 보고서
    battery_start FLOAT,
    battery_end FLOAT,
    status ENUM('진행중', '완료', '중단') DEFAULT '진행중'
);
```

### 9.3 자동 복귀

배터리가 20% 이하로 떨어지면 현재 순찰을 중단하고 충전 도크 위치로 Nav2 Goal을 설정하여 자동 복귀한다.

---

## 10. 일정 요약

| Phase | 기간 | 핵심 마일스톤 |
|-------|------|-------------|
| Phase 1 | 1~2주차 | ROS2 세팅 + ESP32 구동 + 키보드 텔레오퍼 |
| Phase 2 | 3~4주차 | SLAM 맵 생성 + Nav2 자율 순찰 |
| Phase 3 | 5~6주차 | 낙상 감지 + 얼굴 인식 + 위험 구역 경고 |
| Phase 4 | 7주차 | LLM 연동 + TTS 음성 |
| Phase 5 | 8~9주차 | PyQt6 관제 대시보드 |
| Phase 6 | 10주차 | 통합 테스트 + 데모 |

**총 예상 기간: 약 10주**

---

## 11. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| LLM 추론 속도 (EXAONE 3.5 7.8B: 14~18초) | 실시간 대화 지연 | 룰 기반 즉시 판단 + LLM 비동기 보고서, 2.4B 모델 전환 검토, TensorRT-LLM |
| 배터리 지속 시간 | 순찰 범위 제한 | 저전력 모드 + 순찰 주기 조정 |
| SLAM 정밀도 (가정 환경) | 네비게이션 오류 | LiDAR + 초음파 퓨전, 맵 주기적 업데이트 |
| ESP32 통신 불안정 | 모터 제어 지연 | 유선 Serial 우선, Wi-Fi는 백업 |
| 얼굴 인식 오탐 | 불필요한 알림 | 2차 확인 (LLM 판단) + 임계값 조정 |

---

## 12. 확장 가능성

- **멀티 로봇 협업:** 복수 로봇 간 구역 분담 순찰
- **클라우드 연동:** AWS/GCP에 이벤트 데이터 백업 + 원격 모니터링
- **모바일 앱:** Flutter 기반 보호자용 모바일 앱
- **스마트홈 연동:** Home Assistant / MQTT 브리지
- **강화학습:** 순찰 경로 최적화 (에너지 효율 + 커버리지)

---

## 13. 개발 환경 설정

### 13.1 개발 환경 개요

| 항목 | 사양 |
|------|------|
| OS | Ubuntu 24.04 LTS |
| Python | 3.12+ |
| CUDA | 12.8 |
| GPU | NVIDIA (CUDA 지원) |
| ROS2 | Jazzy Jalisco |
| IDE | VSCode + Jupyter Notebook |
| DB | MySQL 8.0 |
| 개발 루트 | `/home/gjkong/dev_ws/ironman` |

### 13.2 Python 가상환경 구성

```bash
# ROS2 전용 가상환경 (Ollama, ROS2 노드 실행용)
cd /home/gjkong/dev_ws
python3 -m venv ros2_venv
source ros2_venv/bin/activate

# 프로젝트 가상환경 (Vision AI, GUI 등)
cd /home/gjkong/dev_ws/ironman
python3 -m venv ironman_venv
source ironman_venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

> ⚠️ **ROS2 노드 실행 시 주의:** `colcon build`로 생성된 엔트리포인트는 시스템 Python을 참조하므로, `ros2 run` 대신 `python -m` 방식으로 실행해야 venv 패키지를 인식합니다.
> ```bash
> # ❌ ros2 run guard_brain brain_node  (shebang이 시스템 Python 참조)
> # ✅ python -m guard_brain.brain_node  (venv Python 사용)
> ```

### 13.3 핵심 패키지 (requirements.txt 기반)

현재 개발 환경의 전체 패키지는 `requirements.txt`에 정의되어 있으며, 주요 패키지를 기능별로 분류하면 다음과 같다.

**Vision AI / ML:**

| 패키지 | 버전 | 용도 |
|--------|------|------|
| torch | 2.9.1 | PyTorch (ST-GCN 추론, GPU) |
| torchvision | 0.24.1 | 이미지 전처리 |
| ultralytics | 8.4.7 | YOLO11 Pose (객체/키포인트 감지) |
| mediapipe | 0.10.14 | Pose Landmark, Face Mesh |
| opencv-python | 4.13.0.90 | 영상 처리 |
| opencv-contrib-python | 4.11.0.86 | 확장 영상 처리 |
| scikit-learn | 1.8.0 | Random Forest 낙상 감지 |
| tensorflow | 2.16.1 | TensorFlow (보조 모델) |
| onnxruntime-gpu | 1.23.2 | ONNX 모델 GPU 추론 |

**CUDA / GPU:**

| 패키지 | 버전 | 용도 |
|--------|------|------|
| nvidia-cublas-cu12 | 12.8.4.1 | cuBLAS 라이브러리 |
| nvidia-cudnn-cu12 | 9.10.2.21 | cuDNN |
| nvidia-cuda-runtime-cu12 | 12.8.90 | CUDA 런타임 |
| triton | 3.5.1 | Triton 커널 컴파일러 |

**GUI / 대시보드:**

| 패키지 | 버전 | 용도 |
|--------|------|------|
| PyQt6 | 6.10.2 | 관제 대시보드 GUI |
| PyQt6-Charts | 6.10.0 | 차트 위젯 |
| matplotlib | 3.10.8 | 데이터 시각화 |
| seaborn | 0.13.2 | 통계 시각화 |

**데이터 / DB:**

| 패키지 | 버전 | 용도 |
|--------|------|------|
| mysql-connector-python | 9.5.0 | MySQL 연결 |
| PyMySQL | 1.1.2 | MySQL 대안 드라이버 |
| SQLAlchemy | 2.0.46 | ORM |
| pandas | 3.0.0 | 데이터 처리 |
| numpy | 2.4.1 | 수치 연산 |

**통신 / API:**

| 패키지 | 버전 | 용도 |
|--------|------|------|
| fastapi | 0.128.0 | REST API 서버 |
| uvicorn | 0.40.0 | ASGI 서버 |
| websockets | 16.0 | WebSocket 통신 (영상 스트리밍) |
| websocket-client | 1.9.0 | WebSocket 클라이언트 |
| requests | 2.32.5 | HTTP 클라이언트 |
| httpx | 0.28.1 | 비동기 HTTP |

**음성 / 알림:**

| 패키지 | 버전 | 용도 |
|--------|------|------|
| sounddevice | 0.5.5 | 오디오 입출력 |
| solapi | 5.0.3 | SMS/알림 발송 |
| bcrypt | 5.0.0 | 비밀번호 해싱 |

**ML 최적화 / 실험:**

| 패키지 | 버전 | 용도 |
|--------|------|------|
| optuna | 4.7.0 | 하이퍼파라미터 튜닝 |
| jax / jaxlib | 0.4.34 | JAX 수치 연산 |
| tensorboard | 2.16.2 | 학습 모니터링 |

**Jupyter / 개발 도구:**

| 패키지 | 버전 | 용도 |
|--------|------|------|
| jupyter | 1.1.1 | Jupyter Notebook |
| jupyterlab | 4.5.2 | JupyterLab IDE |
| ipykernel | 7.1.0 | IPython 커널 |
| ipywidgets | 8.1.8 | 인터랙티브 위젯 |

### 13.4 추가 설치 필요 패키지 (Phase별)

기존 `requirements.txt`에 포함되지 않은 패키지로, 각 Phase 진행 시 추가 설치한다.

```bash
# Phase 1: ROS2 + 하드웨어
# (ROS2는 apt로 별도 설치, pip 패키지 아님)
sudo apt install ros-jazzy-desktop ros-jazzy-nav2-bringup
pip install pyserial           # ESP32 Serial 통신
pip install ollama             # Ollama Python 클라이언트

# Ollama + EXAONE 3.5 설치
curl -fsSL https://ollama.com/install.sh | sh
ollama pull exaone3.5:7.8b

# Phase 2: SLAM
sudo apt install ros-jazzy-slam-toolbox ros-jazzy-cartographer

# Phase 3: 얼굴 인식
pip install insightface         # 얼굴 인식
pip install onnxruntime-gpu     # (이미 설치됨)

# Phase 4: TTS (LLM은 Phase 1에서 완료)
pip install gtts                # Google TTS
pip install piper-tts           # 오프라인 TTS (선택)

# Phase 5: 대시보드 확장
# PyQt6 (이미 설치됨)
pip install pyqtgraph           # 실시간 그래프 (선택)
```

### 13.5 프로젝트 초기 디렉토리 구조

```bash
# 프로젝트 초기화
cd /home/gjkong/dev_ws/ironman
mkdir -p home_guard_ws/src

# ROS2 워크스페이스 초기화
cd home_guard_ws
colcon build
source install/setup.bash
```

```
/home/gjkong/dev_ws/ironman/
├── requirements.txt                # Python 의존성
├── path_config.py                  # 경로 중앙 관리
├── README.md
├── LLM_ROS_보안관_개발계획서.md
└── home_guard_ws/                  # ROS2 워크스페이스
    └── src/
        ├── guard_bringup/
        ├── guard_vision/
        ├── guard_brain/
        ├── guard_voice/
        ├── guard_hw/
        ├── guard_dashboard/
        └── guard_msgs/
```

### 13.6 경로 관리 정책 (필수 준수)

> ⚠️ **모든 소스 코드에서 절대 경로 사용을 금지한다.**

이전 Home Safe Solution 프로젝트에서 절대 경로 하드코딩으로 인해 프로젝트 공유 및 이전 시 대규모 수정 작업이 발생한 경험을 바탕으로, 본 프로젝트는 **처음부터 상대 경로만 사용**하는 것을 원칙으로 한다.

**원칙:**

- 모든 파일 경로는 `path_config.py`를 통해 중앙 관리한다.
- `path_config.py`는 `__file__` 기준으로 프로젝트 루트를 자동 감지하므로, 프로젝트 폴더를 통째로 옮겨도 수정 없이 동작한다.
- ROS2 launch 파일, YAML 파라미터에서도 `$(find pkg)` 등 ROS2 상대 경로 규칙을 따른다.
- DB 설정(system_settings)에 저장하는 경로도 프로젝트 루트 기준 상대 경로로 기록한다.

**금지 사항:**

```python
# ❌ 절대 금지
model_path = '/home/gjkong/dev_ws/ironman/models/yolo11s-pose.pt'
BASE_DIR = Path("/home/gjkong/dev_ws")

# ✅ 올바른 방법
from path_config import PATHS
model_path = str(PATHS.YOLO_MODEL)
```

**path_config.py 구조:**

```python
import os
from pathlib import Path

DEV_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))

class _Paths:
    def __init__(self):
        self.DEV_ROOT = DEV_ROOT
        self.ROS_WS = DEV_ROOT / "home_guard_ws"
        self.MODELS = DEV_ROOT / "models"
        # ... 프로젝트 성장에 따라 확장

PATHS = _Paths()
```

**코드 리뷰 체크리스트:**

- [ ] `/home/` 또는 `~/`로 시작하는 경로가 소스 코드에 없는가?
- [ ] 새 경로가 필요할 때 `path_config.py`에 먼저 등록했는가?
- [ ] `git push` 전 `grep -rn "/home/" --include="*.py"` 로 절대 경로 누출을 확인했는가?
