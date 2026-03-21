---
title: "GHOST-5 작업 일지 | Phase 1 — M01 완료"
date: 2026-03-21
draft: true
tags: ["ros2", "slam", "zenoh"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **현재 단계**: Phase 1 — M01 완료 (M02 진입 전) **작업자**: gjkong@pc"
---

# GHOST-5 작업 일지 | Phase 1 — M01 완료
**날짜**: 2026-03-18  
**현재 단계**: Phase 1 — M01 완료 (M02 진입 전)  
**작업자**: gjkong@pc  
**프로젝트 홈**: `/home/gjkong/ghost5`

---

## 오늘 작업 요약

| 순서 | 작업 내용 | 상태 |
|------|-----------|------|
| 1 | `ghost5_bringup/config/qos_profiles.py` 작성 | ✅ 완료 |
| 2 | `ghost5_bringup/config/zenoh_config.json5` 작성 | ✅ 완료 |
| 3 | M01 완료 조건 검증 스크립트 작성 | ✅ 완료 |

---

## 1. qos_profiles.py

**위치**: `ghost5_ws/src/ghost5_bringup/config/qos_profiles.py`

### 정의된 QoS 프로파일

| 프로파일 | Reliability | Durability | depth | 용도 |
|----------|-------------|------------|-------|------|
| `POSE_QOS` | BEST_EFFORT | VOLATILE | 5 | 로봇 위치 (10~20Hz) |
| `MAP_QOS` | RELIABLE | TRANSIENT_LOCAL | 1 | SLAM 병합 맵 |
| `VICTIM_QOS` | RELIABLE | TRANSIENT_LOCAL | 10 | 생존자 감지 (유실 불가) |
| `SWARM_CMD_QOS` | RELIABLE | VOLATILE | 20 | 군집 명령/Bully 선출 |
| `SENSOR_QOS` | BEST_EFFORT | VOLATILE | 3 | LiDAR/IMU Raw |
| `ELEVATION_QOS` | RELIABLE | TRANSIENT_LOCAL | 1 | 2.5D 고도맵 |
| `INTER_ROBOT_QOS` | BEST_EFFORT | VOLATILE | 5 | [B4] Inter-Robot 동적 장애물 (5Hz) |

- `TOPIC_QOS_MAP` 딕셔너리로 토픽명 → QoS 자동 매핑
- `get_qos(topic)` 헬퍼 함수 제공 (미등록 토픽 → SWARM_CMD_QOS 기본값)

---

## 2. zenoh_config.json5

**위치**: `ghost5_ws/src/ghost5_bringup/config/zenoh_config.json5`

### 주요 설정

| 항목 | 값 | 비고 |
|------|-----|------|
| mode | `router` | GCS PC 실행용 |
| listen | `tcp/0.0.0.0:7447`, `udp/224.0.0.224:7446` | TCP + 멀티캐스트 |
| connect | `tcp/localhost:7447` | 배포 시 GCS IP로 변경 |
| lowlatency | `true` | 재난 환경 저지연 필수 |
| compression | `false` | 저지연 우선 |
| gossip.multihop | `true` | 직접 연결 불가 로봇 간 탐색 |
| retry | 1s → 10s 지수 백오프 | 연결 재시도 |

> ⚠️ **배포 시 수정 필요**: `connect.endpoints`의 `localhost` → GCS 실제 IP

---

## 3. M01 완료 조건 검증 스크립트

**위치**: `ghost5_ws/tests/unit/test_m01_verify.py`

```bash
# venv 비활성화 후 실행
deactivate
source /opt/ros/jazzy/setup.bash
source ~/.bashrc
cd /home/gjkong/ghost5
python3 ghost5_ws/tests/unit/test_m01_verify.py
```

### 검증 항목

| 코드 | 항목 | 기대값 |
|------|------|--------|
| V1 | qos_profiles.py 임포트 + 7개 프로파일 타입 | QoSProfile 인스턴스 |
| V2 | zenoh_config.json5 파싱 | mode/listen/scouting 키 존재 |
| V3 | RMW_IMPLEMENTATION | `rmw_zenoh_cpp` |
| V4 | ROS_DOMAIN_ID | `42` |
| V5 | libzenohc.so ld 캐시 | ldconfig -p 확인 |
| V6 | ros2 pkg list | rmw_zenoh_cpp, zenoh_cpp_vendor |

---

## 4. 파일 배치 위치

```
ghost5_ws/src/ghost5_bringup/
└── config/
    ├── qos_profiles.py          # ← 오늘 작성
    └── zenoh_config.json5       # ← 오늘 작성

ghost5_ws/tests/unit/
└── test_m01_verify.py           # ← 오늘 작성
```

---

## 5. M01 완료 조건 최종 체크리스트

- [ ] `python3 test_m01_verify.py` — 전 항목 PASS 확인
- [ ] `ros2 topic list`에서 `/swarm/*` 토픽 확인 (노드 기동 후)
- [ ] 두 노드 간 POSE_QOS 통신 지연 < 50ms 확인
- [ ] `zenohd -c zenoh_config.json5` — Zenoh 라우터 정상 실행 확인

> ✅ 위 4개 항목 통과 시 M01 완료 → **M02 (SLAM 패키지 설정)** 진입

---

## 6. 다음 작업 (M02)

- [ ] `ghost5_slam` 패키지 생성
- [ ] `slam_toolbox` 파라미터 설정 (`slam_params.yaml`)
- [ ] 5대 로봇 개별 네임스페이스 SLAM 설정 (`/robot_N/`)
- [ ] Multi-Robot 지도 병합 설계 (map_merge_3d 또는 custom)

---

## 7. 참고 문서

| 문서 | 버전 | 위치 |
|------|------|------|
| GHOST5_plan_v2.md | v2.1 | `/home/gjkong/ghost5/` |
| GHOST5_구현단계_v2.md | v1.2 | `/home/gjkong/ghost5/` |
| 작업 일지 (전일) | 2026-03-17 | `GHOST5_작업일지_20260317_Phase1_M01.md` |

---

*다음 세션 시작 시 이 파일을 참고하여 M01 검증 완료 후 M02부터 진행.*
