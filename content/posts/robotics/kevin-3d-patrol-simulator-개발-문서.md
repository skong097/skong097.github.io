---
title: "Kevin 3D Patrol Simulator — 개발 문서"
date: 2026-03-21
draft: true
tags: ["robotics", "slam", "patrol"]
categories: ["robotics"]
description: "**날짜**: 2025-02-15 **파일**: `kevin_3d_sim.py` (1,087 lines) **플랫폼**: Pygame + PyOpenGL"
---

# Kevin 3D Patrol Simulator — 개발 문서

**날짜**: 2025-02-15  
**파일**: `kevin_3d_sim.py` (1,087 lines)  
**플랫폼**: Pygame + PyOpenGL  

---

## 개요

Kevin 자율순찰 로봇을 3D 환경에서 시뮬레이션하는 게임.  
ROS2 토픽 모니터, LiDAR 시각화, Nav2 웨이포인트 순찰, 낙상 감지 등  
실제 로봇 시스템의 핵심 기능을 시각적으로 체험할 수 있다.

## 설치

```bash
pip install pygame PyOpenGL PyOpenGL_accelerate numpy
python kevin_3d_sim.py
```

## 조작법

| 키 | 기능 |
|---|---|
| WASD | 로봇 이동 |
| Mouse | 시점 회전 |
| TAB | 자동 순찰 모드 토글 |
| L | LiDAR 시각화 토글 |
| F | 낙상 이벤트 트리거 |
| M | 미니맵 토글 |
| 1 / 2 / 3 | 1인칭 / 3인칭 / 탑뷰 카메라 |
| ESC | 종료 |

## 아키텍처

### 클래스 구조

```
Kevin3DSim          — 메인 시뮬레이션 루프
├── TopicMonitor    — ROS2 토픽 상태 시뮬레이션
├── HUD             — 2D 오버레이 (토픽 모니터, 미니맵, 상태바)
└── CameraMode      — 카메라 모드 열거형 (1인칭/3인칭/탑뷰)
```

### 3D 렌더링 함수

| 함수 | 설명 |
|---|---|
| `draw_box()` | 범용 3D 박스 (벽, 장애물, 로봇 부품) |
| `draw_cylinder()` | 원기둥 (LiDAR 센서) |
| `draw_robot()` | Kevin 로봇 모델 (본체+바퀴+카메라+LiDAR+LED) |
| `draw_person()` | 사람 모델 (서 있는/쓰러진 상태) |
| `draw_lidar_rays()` | 360° LiDAR 레이캐스트 시각화 (72 rays) |
| `draw_waypoint()` | Nav2 웨이포인트 마커 (펄스 애니메이션) |
| `draw_floor()` | 바닥 + 그리드 |
| `draw_skybox()` | 그라데이션 배경 |

### ROS2 토픽 시뮬레이션

실시간으로 8개 토픽의 상태를 HUD에 표시:

- `/cmd_vel` — 로봇 속도 명령 (Twist)
- `/scan` — LiDAR 스캔 데이터 (LaserScan)
- `/image_raw` — 카메라 영상 (Image)
- `/odom` — 위치 추정 (Odometry)
- `/detection` — 낙상 감지 결과
- `/alert` — 긴급 알림
- `/robot_status` — 로봇 상태
- `/nav2/path` — 순찰 경로

### 맵 구조

- 40×40 단위의 실내 환경
- 외벽 + 내부 복도 구조의 벽
- 12개 장애물 (가구)
- 10개 순찰 웨이포인트
- 5명의 사람 (낙상 감지 대상)

### 핵심 기능

1. **수동 조종**: WASD + 마우스로 로봇 직접 조종, 벽/장애물 충돌 판정
2. **자동 순찰**: TAB으로 Nav2 스타일 웨이포인트 순찰 활성화, 부드러운 회전 + 경로 추종
3. **LiDAR 시각화**: 72개 레이의 레이캐스트, 거리에 따른 색상 변화, 히트 포인트 표시
4. **낙상 감지**: F키로 가장 가까운 사람의 낙상 이벤트 트리거, 알림 오버레이 + 토픽 상태 변경
5. **3종 카메라**: 1인칭(로봇 시점), 3인칭(팔로우), 탑뷰(전략 뷰)
6. **미니맵**: 벽/장애물/웨이포인트/로봇 위치를 2D로 표시

## 향후 개선 방향

- SLAM 맵 빌딩 시각화 (occupancy grid 실시간 생성)
- 얼굴 인식 시뮬레이션 (face_detect 노드)
- guard_brain LLM 대화 통합
- 다중 로봇 시뮬레이션
- 사운드 효과 (경보음, 모터 소리)
- 성능 최적화 (디스플레이 리스트 / VBO)
