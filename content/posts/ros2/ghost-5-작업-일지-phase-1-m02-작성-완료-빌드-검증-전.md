---
title: "GHOST-5 작업 일지 | Phase 1 — M02 작성 완료 (빌드 검증 전)"
date: 2026-03-21
draft: true
tags: ["ros2", "nav2", "slam"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **현재 단계**: Phase 1 — M02 완료 (빌드 검증 전) / M03 진입 준비 **작업자**: gjkong@pc"
---

# GHOST-5 작업 일지 | Phase 1 — M02 작성 완료 (빌드 검증 전)
**날짜**: 2026-03-18  
**현재 단계**: Phase 1 — M02 완료 (빌드 검증 전) / M03 진입 준비  
**작업자**: gjkong@pc  
**프로젝트 홈**: `/home/gjkong/ghost5`

---

## 오늘 작업 요약

| 순서 | 작업 내용 | 상태 |
|------|-----------|------|
| 1 | M01 최종 검증 21/21 PASS | ✅ 완료 |
| 2 | `ghost5_interfaces` 전체 파일 작성 (16개) | ✅ 완료 |
| 3 | M02 완료 조건 검증 스크립트 작성 | ✅ 완료 |
| 4 | colcon build + ros2 interface list 검증 | ⏳ 실기기 실행 필요 |

---

## M02 생성 파일 목록

### 배치 경로
```
ghost5_ws/src/ghost5_interfaces/
├── package.xml
├── CMakeLists.txt
├── msg/
│   ├── RobotStatus.msg          # 로봇 상태 (배터리/모드/위치/오류)
│   ├── VictimDetection.msg      # 3-센서 융합 생존자 감지
│   ├── SwarmCommand.msg         # 군집 명령 (CMD 열거형)
│   ├── BullyMessage.msg         # Bully 리더 선출 메시지
│   ├── FrontierArray.msg        # MMPF Frontier 후보 목록
│   ├── RobotPoseArray.msg       # 5대 위치 배열 [B4]
│   └── ElevationCell.msg        # 2.5D 고도맵 셀
├── srv/
│   ├── ClaimFrontier.srv        # Frontier 선점 요청
│   ├── GetLeader.srv            # 현재 리더 조회
│   ├── SetBlackboard.srv        # Redis 키-값 쓰기
│   ├── GetBlackboard.srv        # Redis 키-값 읽기
│   └── ReportVictim.srv         # 생존자 GCS 보고
└── action/
    ├── NavigateToPose.action    # 목표 지점 이동 (Nav2 호환)
    ├── ExploreFrontier.action   # Frontier 자율 탐색
    ├── SearchVictim.action      # 구역 생존자 탐색
    └── MergeMap.action          # 지도 병합
```

### 인터페이스 설계 요약

| 파일 | 핵심 필드 | 연결 모듈 |
|------|-----------|-----------|
| RobotStatus.msg | mode(열거), battery, rssi, 오류플래그 | swarm, viz |
| VictimDetection.msg | confidence×3, fused, status(열거) | victim, viz |
| SwarmCommand.msg | command(열거), target_id, target_pose | swarm |
| BullyMessage.msg | msg_type(열거), term_id, election_uuid | swarm |
| FrontierArray.msg | positions[], scores[], claimed_by[] | navigation |
| RobotPoseArray.msg | poses[], robot_ids[], footprint_radii[] | navigation [B4] |
| ElevationCell.msg | z_min/max/mean, slope_deg, is_traversable | slam |
| ClaimFrontier.srv | frontier_index, duration → success, expires | navigation |
| GetLeader.srv | requester_id → leader_id, term_id | swarm |
| SetBlackboard.srv | key, value, ttl → success | swarm |
| GetBlackboard.srv | key → found, value, remaining_ttl | swarm |
| ReportVictim.srv | VictimDetection → victim_id, is_duplicate | victim, viz |
| NavigateToPose.action | goal_pose, speed_limit ↔ distance_remaining | navigation |
| ExploreFrontier.action | max_frontiers, cooperative ↔ progress | navigation |
| SearchVictim.action | search_area, min_confidence ↔ candidates | victim |
| MergeMap.action | source_ids, incremental ↔ cells_processed | slam |

---

## M02 완료 조건 검증 방법

```bash
# 1. 파일 배치
cp -r ghost5_interfaces/ ghost5_ws/src/

# 2. venv 비활성화 + ROS2 소싱
deactivate
source /opt/ros/jazzy/setup.bash

# 3. 빌드
cd ghost5_ws
colcon build --packages-select ghost5_interfaces

# 4. 검증 스크립트 실행
source install/setup.bash
python3 tests/unit/test_m02_verify.py
```

### 예상 통과 항목 (V1~V3: 파일 검증)
- V1: 16개 파일 존재 확인
- V2: package.xml 의존성 5개
- V3: CMakeLists.txt 16개 등록

### 빌드 후 통과 항목 (V4~V5)
- V4: colcon build 성공
- V5: `ros2 interface list`에서 16개 ghost5_interfaces 타입 확인

---

## 다음 작업 — M03 (Redis HA Blackboard)

- [ ] `ghost5_swarm` 패키지 생성
- [ ] `blackboard.py` — Redis HA 클라이언트 래퍼
- [ ] `semantic_memory.py` — 구조화된 군집 상태 저장소
- [ ] SetBlackboard / GetBlackboard 서비스 서버 노드
- [ ] Redis sentinel 설정 (HA 구성)

---

## 참고 문서

| 문서 | 버전 | 위치 |
|------|------|------|
| GHOST5_plan_v2.md | v2.1 | `/home/gjkong/ghost5/` |
| GHOST5_구현단계_v2.md | v1.2 | `/home/gjkong/ghost5/` |
| 작업 일지 M01 완료 | 2026-03-18 | `GHOST5_작업일지_20260318_Phase1_M01완료.md` |

---

*다음 세션: M02 빌드 검증(test_m02_verify.py) 완료 후 M03 진입.*
