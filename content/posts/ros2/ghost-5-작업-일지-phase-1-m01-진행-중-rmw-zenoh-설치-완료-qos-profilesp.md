---
title: "GHOST-5 작업 일지 | Phase 1 — M01 진행 중 (rmw_zenoh 설치 완료 / qos_profiles.py 작성 전)"
date: 2026-03-21
draft: true
tags: ["ros2", "nav2", "slam", "zenoh"]
categories: ["ros2"]
description: "**날짜**: 2026-03-17 **현재 단계**: Phase 1 — M01 진행 중 (rmw_zenoh 설치 완료 / qos_profiles.py 작성 전) **작업자**: gjkong@pc"
---

# GHOST-5 작업 일지 | Phase 1 — M01 진행 중 (rmw_zenoh 설치 완료 / qos_profiles.py 작성 전)
**날짜**: 2026-03-17  
**현재 단계**: Phase 1 — M01 진행 중 (rmw_zenoh 설치 완료 / qos_profiles.py 작성 전)  
**작업자**: gjkong@pc  
**프로젝트 홈**: `/home/gjkong/ghost5`

---

## 오늘 작업 요약

| 순서 | 작업 내용 | 상태 |
|------|-----------|------|
| 1 | GHOST5_plan_v2.md → v2.1 업데이트 (Inter-Robot 동적 장애물 등록 반영) | ✅ 완료 |
| 2 | GHOST5_구현단계_v2.md → v1.2 업데이트 ([B4] 보완 반영) | ✅ 완료 |
| 3 | 워크스페이스 디렉토리 구조 생성 | ✅ 완료 |
| 4 | Python 가상환경(venv) 생성 및 패키지 설치 | ✅ 완료 |
| 5 | ROS2 환경변수 등록 (.bashrc) | ✅ 완료 |
| 6 | ros-jazzy-rmw-zenoh-cpp 설치 | ✅ 완료 |
| 7 | libzenohc.so ld 캐시 등록 | ✅ 완료 |

---

## 1. 문서 업데이트 내용

### GHOST5_plan_v2.md → v2.1
- **10.2** `nav2_params.yaml` local_costmap에 `robot_layer` (ObstacleLayer) 추가
- **10.3 신규 섹션** — Inter-Robot 동적 장애물 등록 설계 + 구현 코드
  - `inter_robot_costmap_layer.py` 신규 파일 설계
  - `/swarm/robot_poses_array` QoS 토픽 추가 (BEST_EFFORT, 5Hz)
  - 역할 분담 표 (정적/동적 충돌 회피 레이어 구분)
- **변경이력** v2.1 항목 추가

### GHOST5_구현단계_v2.md → v1.2
- **M06** 완료 조건에 `[B4]` 항목 3개 추가
- **M06** 본문에 `[보완 B4]` 참조 링크 + 핵심 요약 추가
- **12.4 신규 섹션** — [B4] Inter-Robot 동적 장애물 등록 상세
- **변경이력** v1.2 항목 추가
- **푸터** `[B1][B2][B3][B4]` 업데이트

---

## 2. 워크스페이스 디렉토리 구조

```
/home/gjkong/ghost5/
├── ghost5_init_ws.sh          # 초기화 스크립트
├── ghost5_ws/                 # ROS2 워크스페이스 (시스템 Python)
│   ├── src/
│   │   ├── ghost5_interfaces/     # 커스텀 메시지/서비스/액션
│   │   ├── ghost5_bringup/        # 런치 + 설정 파일
│   │   ├── ghost5_slam/           # SLAM + 지도 병합 + Elevation
│   │   ├── ghost5_navigation/     # Nav2 + Frontier + [B4] Inter-Robot
│   │   ├── ghost5_swarm/          # 군집 지능 (Bully, Redis, Rendezvous)
│   │   ├── ghost5_victim/         # 생존자 감지 (US-016, IR, YOLOv8n)
│   │   ├── ghost5_viz/            # GCS API + Foxglove 시각화
│   │   ├── ghost5_drone_sim/      # Fake Drone / PX4 Bridge (Phase 6~7)
│   │   └── ghost5_drone_integration/  # 드론-로봇 통합 (Phase 6~7)
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   └── scripts/
│       └── benchmark/
└── venv/                      # Python 가상환경 (FastAPI, Redis 등)
```

---

## 3. 환경 설정 완료 내용

### 3.1 Python 가상환경 (venv)
```bash
# 위치: /home/gjkong/ghost5/venv
# 생성 옵션: --system-site-packages (ROS2 시스템 패키지 접근 허용)

설치 패키지:
  fastapi    0.135.1
  numpy      2.4.3
  pytest     9.0.2
  redis      7.3.0
  uvicorn    (latest)
  httpx      (latest)
```

### 3.2 ROS2 환경변수 (~/.bashrc)
```bash
# GHOST-5 ROS2 환경
export RMW_IMPLEMENTATION=rmw_zenoh_cpp
export ROS_DOMAIN_ID=42
```

### 3.3 rmw_zenoh 설치
```bash
# 설치
sudo apt install ros-jazzy-rmw-zenoh-cpp

# libzenohc.so ld 캐시 등록 (미등록 시 로딩 실패)
echo "/opt/ros/jazzy/opt/zenoh_cpp_vendor/lib" | sudo tee /etc/ld.so.conf.d/zenoh.conf
sudo ldconfig

# 확인
ros2 pkg list | grep zenoh
# → rmw_zenoh_cpp
# → zenoh_cpp_vendor
```

> ⚠️ **주의사항**: `ros2` 명령어는 반드시 venv 비활성화 상태에서 실행  
> venv 활성화 상태에서 실행 시 `librmw_zenoh_cpp.so` 로딩 실패 에러 발생

---

## 4. ROS2 / venv 사용 규칙

| 작업 | 환경 |
|------|------|
| `colcon build` | 시스템 Python (venv 비활성화) |
| `ros2 run / launch` | 시스템 Python (venv 비활성화) |
| `ros2 pkg list` 등 ROS2 CLI | 시스템 Python (venv 비활성화) |
| FastAPI GCS 서버 실행 | venv 활성화 |
| 벤치마크 스크립트 실행 | venv 활성화 |
| pytest 단위 테스트 | venv 활성화 |

```bash
# venv 활성화
source ~/ghost5/venv/bin/activate

# venv 비활성화
deactivate
```

---

## 5. 다음 작업 (M01 잔여)

- [ ] `ghost5_bringup/config/qos_profiles.py` 작성
- [ ] `ghost5_bringup/config/zenoh_config.json5` 작성
- [ ] M01 완료 조건 체크
  - [ ] `ros2 topic list`에서 `/swarm/*` 토픽 확인
  - [ ] 두 노드 간 POSE_QOS 통신 지연 < 50ms 확인
  - [ ] Zenoh 라우터 정상 실행 확인

---

## 6. 참고 문서

| 문서 | 버전 | 위치 |
|------|------|------|
| GHOST5_plan_v2.md | v2.1 | `/home/gjkong/ghost5/` |
| GHOST5_구현단계_v2.md | v1.2 | `/home/gjkong/ghost5/` |

---

*다음 세션 시작 시 이 파일을 참고하여 M01 잔여 작업(qos_profiles.py, zenoh_config.json5)부터 이어서 진행.*
