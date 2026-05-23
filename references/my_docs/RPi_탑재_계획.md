# 🤖 Home Guard Bot — 라즈베리파이 탑재 계획

> **목표:** PC(GPU) + RPi 5 분산 아키텍처
> **작성일:** 2026-02-14
> **예정:** 차주 (2026-02-16 ~ )

---

## 1. 분산 아키텍처 개요

ROS2 DDS(Data Distribution Service)는 같은 네트워크의 노드를 자동으로 발견하고 연결한다.
코드 수정 없이, 노드를 어디서 실행하느냐만 바꾸면 분산이 완성된다.

```
┌─── RPi 5 (로봇) ──────────────────┐        ┌─── PC (GPU 서버) ─────────────┐
│                                    │  WiFi  │                               │
│  usb_cam_node                      │◄═════►│  guard_vision (YOLO+RF/STGCN) │
│    → /camera/image_raw 발행        │  ROS2  │    ← /camera/image_raw 구독   │
│                                    │  DDS   │    → /guard/sensor_data 발행  │
│  guard_voice (TTS+스피커)          │        │                               │
│    ← /guard/tts_command 구독       │        │  guard_brain (룰+LLM)         │
│                                    │        │    ← /guard/sensor_data 구독  │
│  motor_driver_node (향후)          │        │    → /guard/tts_command 발행  │
│    ← /cmd_vel 구독                 │        │    → /guard/report 발행       │
│                                    │        │                               │
│  sensor_node (향후)                │        │                               │
│    → /guard/sensor_data 발행       │        │                               │
└────────────────────────────────────┘        └───────────────────────────────┘
```

**핵심:** 토픽 이름만 같으면, 어느 머신에서 실행하든 ROS2가 알아서 연결.

---

## 2. 준비 작업 체크리스트

### Phase A: RPi 기본 환경 (1일)

- [ ] RPi 5에 Ubuntu 24.04 Server 설치 (64bit)
- [ ] ROS2 Jazzy 설치
- [ ] SSH 설정 + 고정 IP 할당
- [ ] WiFi 연결 확인
- [ ] Python 가상환경(ros2_venv) 구성
- [ ] edge-tts, sounddevice, pydub, soundfile 설치 (guard_voice용)

### Phase B: ROS2 네트워크 연결 (반나절)

- [ ] PC와 RPi가 같은 네트워크에 있는지 확인
- [ ] ROS_DOMAIN_ID 통일 (양쪽 모두 같은 값)
- [ ] 연결 테스트: RPi에서 발행 → PC에서 수신
- [ ] DDS 설정 (Cyclone DDS 권장, FastDDS 대비 안정적)

```bash
# RPi에서 테스트 발행
ros2 topic pub /test std_msgs/String "data: 'hello from rpi'"

# PC에서 수신 확인
ros2 topic echo /test
```

### Phase C: 카메라 영상 스트리밍 (반나절)

- [ ] RPi에 USB 카메라 연결 + 확인
- [ ] usb_cam 또는 v4l2_camera 패키지 설치
- [ ] /camera/image_raw 토픽 발행 테스트
- [ ] PC에서 영상 수신 확인 (rqt_image_view)
- [ ] 영상 압축 전송 설정 (image_transport + compressed)
  - 비압축 720p → ~30MB/s (WiFi 부담)
  - JPEG 압축 → ~2MB/s (실용적)

```bash
# RPi에서 카메라 노드 실행
ros2 run usb_cam usb_cam_node_exe --ros-args -p video_device:=/dev/video0

# PC에서 영상 확인
ros2 run rqt_image_view rqt_image_view
```

### Phase D: guard_vision 수정 (반나절)

현재 guard_vision은 로컬 카메라를 직접 열지만,
분산 환경에서는 ROS2 토픽으로 영상을 받아야 한다.

- [ ] fall_detection_node.py에 토픽 구독 모드 추가 (use_topic 파라미터)
  - `use_topic:=false` (기본) → 로컬 cv2.VideoCapture (현재 방식)
  - `use_topic:=true` → /camera/image_raw 구독 (분산 모드)
- [ ] 토픽 구독 시 Image → cv2 변환 (cv_bridge 사용)

```bash
# PC에서 분산 모드로 실행
ros2 run guard_vision fall_detection_node --ros-args \
  -p use_topic:=true -p model_type:=stgcn -p show_gui:=true
```

### Phase E: guard_voice RPi 배포 (반나절)

- [ ] guard_voice 패키지를 RPi에 복사
- [ ] RPi에서 빌드 (colcon build)
- [ ] 스피커 연결 + 오디오 출력 확인
- [ ] TTS 재생 테스트

```bash
# RPi에서 guard_voice 실행
ros2 run guard_voice tts_node

# PC에서 TTS 명령 발행 → RPi 스피커에서 재생
ros2 topic pub --once /guard/tts_command std_msgs/String "data: '테스트 음성'"
```

### Phase F: 통합 테스트 (1일)

- [ ] RPi: usb_cam + guard_voice 실행
- [ ] PC: guard_vision + guard_brain 실행
- [ ] 전체 파이프라인 확인:
  - RPi 카메라 → PC YOLO+AI 감지 → PC 룰 판단 → RPi TTS 음성
- [ ] 지연 시간 측정 (영상 전송 + AI 추론 + TTS 합산)
- [ ] WiFi 불안정 시 대응 확인

---

## 3. 하드웨어 구매 목록

현재 있는 것: RPi 5 (8GB), USB 카메라

### 필수 구매

| 품목 | 용도 | 예상 가격 |
|------|------|----------|
| microSD 64GB+ (A2 등급) | RPi OS + ROS2 | ~1만원 |
| USB-C 전원 (27W PD) | RPi 5 전원 | ~1.5만원 |
| 스피커 (USB 또는 3.5mm) | TTS 음성 출력 | ~1만원 |
| 방열 케이스 + 쿨링팬 | RPi 5 발열 관리 | ~1.5만원 |

### 로봇 구동 (향후)

| 품목 | 용도 | 예상 가격 |
|------|------|----------|
| 로봇 차체 키트 | 프레임 + 바퀴 | ~3-5만원 |
| DC 모터 + L298N | 구동 | ~1.5만원 |
| 모터 드라이버 HAT 또는 L298N | RPi GPIO 제어 | ~1만원 |
| 배터리 (LiPo 또는 보조배터리) | 이동 전원 | ~3만원 |

### 센서 (향후)

| 품목 | 용도 | 예상 가격 |
|------|------|----------|
| 초음파 센서 HC-SR04 x3 | 장애물 회피 | ~0.5만원 |
| DHT22 | 온습도 | ~0.3만원 |
| MQ-2 | 가스 감지 | ~0.3만원 |

---

## 4. 네트워크 설정 가이드

### ROS_DOMAIN_ID 설정

양쪽 머신에서 같은 DOMAIN_ID를 사용해야 노드가 서로 발견된다.

```bash
# PC의 .bashrc
export ROS_DOMAIN_ID=42

# RPi의 .bashrc
export ROS_DOMAIN_ID=42
```

### Cyclone DDS 설정 (권장)

FastDDS 대비 소규모 네트워크에서 안정적이다.

```bash
# 양쪽 모두
sudo apt install ros-jazzy-rmw-cyclonedds-cpp
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

### 방화벽 확인

```bash
# ROS2 DDS 포트 허용 (양쪽)
sudo ufw allow 7400:7500/udp
sudo ufw allow 7400:7500/tcp
```

---

## 5. 작업 일정 (차주)

| 날짜 | 작업 | 예상 시간 |
|------|------|----------|
| 월 | Phase A: RPi Ubuntu + ROS2 설치 | 3-4시간 |
| 화 AM | Phase B: ROS2 네트워크 연결 테스트 | 2시간 |
| 화 PM | Phase C: 카메라 영상 스트리밍 | 2시간 |
| 수 | Phase D: guard_vision 토픽 구독 모드 추가 | 3시간 |
| 목 AM | Phase E: guard_voice RPi 배포 | 2시간 |
| 목 PM | Phase F: 통합 테스트 | 3시간 |
| 금 | 안정화 + 작업일지 | 2시간 |

---

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| WiFi 지연 (영상 전송) | 감지 지연 | JPEG 압축, 해상도 480p로 낮춤 |
| WiFi 끊김 | 전체 동작 중단 | RPi에 경량 RF 모델 폴백 탑재 |
| RPi 발열 | 성능 저하 | 방열 케이스 + 팬 필수 |
| 오디오 출력 문제 | TTS 안 들림 | ALSA/PulseAudio 설정 확인 |
| DDS 노드 미발견 | 분산 실패 | Cyclone DDS + DOMAIN_ID 확인 |

---

## 7. 참고: 현재 시스템과 변경점

```
현재 (PC 단독):
  PC: guard_vision + guard_brain + guard_voice  (전부 로컬)

분산 후:
  RPi: usb_cam + guard_voice                   (카메라 + 스피커)
  PC:  guard_vision + guard_brain              (AI + LLM)
```

**코드 변경은 guard_vision에 토픽 구독 모드 추가 1건만 필요.**
나머지는 실행 위치만 바꾸면 된다. 이것이 ROS2의 힘.
