---
title: "GHOST-5 작업 일지 | Phase 1 — M01 완료 + M02 완료"
date: 2026-03-21
draft: true
tags: ["ros2", "slam", "zenoh"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **현재 단계**: Phase 1 — M01 ✅ / M02 ✅ / M03 대기 **작업자**: gjkong@pc"
---

# GHOST-5 작업 일지 | Phase 1 — M01 완료 + M02 완료
**날짜**: 2026-03-18  
**현재 단계**: Phase 1 — M01 ✅ / M02 ✅ / M03 대기  
**작업자**: gjkong@pc  
**프로젝트 홈**: `/home/gjkong/ghost5`  
**기반 문서**: GHOST5_plan_v2.1 / GHOST5_구현단계_v2.md v1.2

---

## 전체 작업 요약

| 순서 | 모듈 | 작업 내용 | 검증 | 상태 |
|------|------|-----------|------|------|
| 1 | M01 | qos_profiles.py 작성 | — | ✅ |
| 2 | M01 | zenoh_config.json5 작성 | — | ✅ |
| 3 | M01 | test_m01_verify.py 작성 + 실행 | 21/21 PASS | ✅ |
| 4 | M02 | ghost5_interfaces 파일 16개 작성 | — | ✅ |
| 5 | M02 | package.xml + CMakeLists.txt 작성 | — | ✅ |
| 6 | M02 | test_m02_verify.py 작성 + 실행 | 44/44 PASS | ✅ |

---

## M01 — rmw_zenoh + QoS 프로파일 ✅

### 생성 파일

| 파일 | 위치 |
|------|------|
| `qos_profiles.py` | `ghost5_ws/src/ghost5_bringup/config/` |
| `zenoh_config.json5` | `ghost5_ws/src/ghost5_bringup/config/` |
| `test_m01_verify.py` | `ghost5_ws/tests/unit/` |

### qos_profiles.py 정의 프로파일

| 프로파일 | Reliability | Durability | depth | 용도 |
|----------|-------------|------------|-------|------|
| `POSE_QOS` | BEST_EFFORT | VOLATILE | 5 | 로봇 위치 10~20Hz |
| `MAP_QOS` | RELIABLE | TRANSIENT_LOCAL | 1 | SLAM 병합 맵 |
| `VICTIM_QOS` | RELIABLE | TRANSIENT_LOCAL | 10 | 생존자 감지 |
| `SWARM_CMD_QOS` | RELIABLE | VOLATILE | 20 | 군집 명령/Bully |
| `SENSOR_QOS` | BEST_EFFORT | VOLATILE | 3 | LiDAR/IMU Raw |
| `ELEVATION_QOS` | RELIABLE | TRANSIENT_LOCAL | 1 | 2.5D 고도맵 |
| `INTER_ROBOT_QOS` | BEST_EFFORT | VOLATILE | 5 | Inter-Robot [B4] 5Hz |

- `TOPIC_QOS_MAP` 딕셔너리 + `get_qos()` 헬퍼 함수 포함

### zenoh_config.json5 주요 설정

| 항목 | 값 |
|------|-----|
| mode | `router` (GCS PC 실행) |
| listen | `tcp/0.0.0.0:7447`, `udp/224.0.0.224:7446` |
| connect | `tcp/localhost:7447` (배포 시 GCS IP 변경) |
| lowlatency | `true` |
| gossip.multihop | `true` |
| retry | 1s → 10s 지수 백오프 |

### M01 검증 결과
```
결과: 21/21 통과  |  실패: 0  ✅
```

> 📌 pyjson5 미설치 — fallback 정규화 파싱으로 통과.  
> 필요 시: `source ~/ghost5/venv/bin/activate && pip install pyjson5`

---

## M02 — ghost5_interfaces (커스텀 메시지/서비스/액션) ✅

### 생성 파일 (16개)

```
ghost5_ws/src/ghost5_interfaces/
├── package.xml
├── CMakeLists.txt
├── msg/
│   ├── RobotStatus.msg          # 로봇 상태 (배터리/모드/위치/오류 플래그)
│   ├── VictimDetection.msg      # 3-센서 융합 생존자 감지 결과
│   ├── SwarmCommand.msg         # 군집 명령 (CMD 열거형, target_id)
│   ├── BullyMessage.msg         # Bully 리더 선출 (term_id, election_uuid)
│   ├── FrontierArray.msg        # MMPF Frontier 후보 목록 + 클레임 상태
│   ├── RobotPoseArray.msg       # 5대 위치 배열 [B4] Inter-Robot
│   └── ElevationCell.msg        # 2.5D 고도맵 셀 (z_min/max, slope_deg)
├── srv/
│   ├── ClaimFrontier.srv        # Frontier 선점 요청/응답
│   ├── GetLeader.srv            # 현재 Bully 리더 조회
│   ├── SetBlackboard.srv        # Redis 키-값 쓰기 (TTL 포함)
│   ├── GetBlackboard.srv        # Redis 키-값 읽기
│   └── ReportVictim.srv         # 생존자 GCS DB 보고
└── action/
    ├── NavigateToPose.action    # 목표 지점 이동 (Nav2 호환, 진행률 피드백)
    ├── ExploreFrontier.action   # Frontier 자율 탐색 (협력 모드)
    ├── SearchVictim.action      # 구역 생존자 탐색 (다각형 영역)
    └── MergeMap.action          # 5대 로봇 지도 병합 (Delta/전체)
```

### M02 검증 결과
```
결과: 44/44 통과  |  실패: 0  ✅
  V1: 인터페이스 파일 16개 존재
  V2: package.xml 의존성 5개
  V3: CMakeLists.txt 16개 등록
  V4: colcon build 성공
  V5: ros2 interface list 16개 타입 확인
```

---

## 현재 Phase 1 진행 현황

```
Phase 1 — 기반 인프라 (M01~M04)
  ├── M01  rmw_zenoh + QoS 프로파일        ✅ 완료 (21/21)
  ├── M02  ghost5_interfaces               ✅ 완료 (44/44)
  ├── M03  Redis HA Blackboard             ⏳ 대기
  └── M04  SROS2 보안                      ⏳ 대기
```

---

## 다음 작업 — M03 (Redis HA Blackboard)

### 생성 예정 파일
```
ghost5_ws/src/ghost5_swarm/
├── package.xml
├── CMakeLists.txt
└── ghost5_swarm/
    ├── __init__.py
    ├── blackboard.py          # Redis HA 클라이언트 래퍼
    ├── semantic_memory.py     # 군집 상태 구조화 저장소
    └── blackboard_node.py     # SetBlackboard / GetBlackboard 서비스 서버
```

### 핵심 구현 목표
- Redis Sentinel HA 구성 (Leader/Replica/Sentinel 3노드)
- `blackboard.py` — 재연결 자동 처리, TTL 관리, JSON 직렬화
- `semantic_memory.py` — 로봇 상태/Frontier/생존자 정보 구조화 키 설계
- SetBlackboard / GetBlackboard 서비스 서버 ROS2 노드

---

## 전체 파일 위치 요약

| 파일 | 경로 |
|------|------|
| qos_profiles.py | `ghost5_ws/src/ghost5_bringup/config/` |
| zenoh_config.json5 | `ghost5_ws/src/ghost5_bringup/config/` |
| test_m01_verify.py | `ghost5_ws/tests/unit/` |
| ghost5_interfaces/ (16개) | `ghost5_ws/src/ghost5_interfaces/` |
| test_m02_verify.py | `ghost5_ws/tests/unit/` |

---

## 참고 문서

| 문서 | 버전 | 위치 |
|------|------|------|
| GHOST5_plan_v2.md | v2.1 | `/home/gjkong/ghost5/` |
| GHOST5_구현단계_v2.md | v1.2 | `/home/gjkong/ghost5/` |
| 작업 일지 (전일) | 2026-03-17 | `GHOST5_작업일지_20260317_Phase1_M01.md` |

---

*다음 세션 시작 시 이 파일을 참고하여 M03 (Redis HA Blackboard)부터 진행.*
