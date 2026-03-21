---
title: "GHOST-5 작업 일지 | Phase 1 — M04 작성 완료 (검증 전)"
date: 2026-03-21
draft: true
tags: ["ros2"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **현재 단계**: Phase 1 — M04 작성 완료 / 검증 대기 **작업자**: gjkong@pc"
---

# GHOST-5 작업 일지 | Phase 1 — M04 작성 완료 (검증 전)
**날짜**: 2026-03-18  
**현재 단계**: Phase 1 — M04 작성 완료 / 검증 대기  
**작업자**: gjkong@pc  
**프로젝트 홈**: `/home/gjkong/ghost5`

---

## 오늘 작업 요약

| 순서 | 작업 내용 | 상태 |
|------|-----------|------|
| 1 | `setup_sros2.sh` — Keystore/인증서/정책 자동 생성 | ✅ 완료 |
| 2 | `ghost5_policy.xml` — 노드별 최소 권한 정책 | ✅ 완료 |
| 3 | `test_m04_verify.py` — 검증 스크립트 | ✅ 완료 |
| 4 | Keystore 생성 + 환경변수 설정 + 검증 | ⏳ 실기기 실행 필요 |

---

## 생성 파일

```
ghost5_ws/src/ghost5_bringup/
├── scripts/
│   └── setup_sros2.sh        # Keystore 자동 생성 스크립트
└── config/
    └── ghost5_policy.xml     # SROS2 노드별 권한 정책

ghost5_ws/tests/unit/
└── test_m04_verify.py
```

---

## 핵심 설계 요약

### setup_sros2.sh 처리 순서

| Step | 내용 |
|------|------|
| 1 | `ros2 security create_keystore` — Keystore 초기화 |
| 2 | robot_0~4 각 7개 노드 인증서 생성 (35개) + GCS 2개 = **37개** |
| 3 | `ros2 security generate_artifacts` — ghost5_policy.xml 적용 |
| 4 | `.bashrc` 환경변수 자동 등록 |

### ghost5_policy.xml 권한 구조

| 노드 | 퍼블리시 | 구독 | 서비스 |
|------|---------|------|--------|
| robot_0/swarm_node (Leader) | 군집 전체 | 군집 전체 | 전체 서비스 |
| robot_1~4/swarm_node (Explorer) | 자신 상태 + 공통 | 공통 토픽 + cmd | claim/get_leader/blackboard |
| robot_0/blackboard_node | — | — | set/get_blackboard |
| robot_0/victim_detector | victim_detected | scan/depth | report_victim |
| gcs/monitor_node | **금지** | swarm/robot_* 전체 | get_blackboard/get_leader |
| gcs/gcs_api_node | **금지** | swarm/** | swarm/** |

### SROS2 취약점 대응

| 취약점 | 대응 |
|--------|------|
| V1: 인증서 만료 미갱신 | `--force` 플래그로 전체 keystore 재생성 |
| V2: 정책 업데이트 레이스 | 노드 중단 → 배포 → 재시작 절차 |
| V3: 기본값 취약성 | `ROS_SECURITY_STRATEGY=Enforce` 강제 |
| V4: 도메인 격리 우회 | `ROS_DOMAIN_ID=42` 고정 |

---

## 실기기 실행 순서

```bash
# 1. 파일 배치
cp -r ghost5_bringup/ ~/ghost5/ghost5_ws/src/ghost5_bringup/
cp test_m04_verify.py ~/ghost5/ghost5_ws/tests/unit/

# 2. ROS2 소싱
deactivate
source /opt/ros/jazzy/setup.bash

# 3. Keystore 생성 (GCS PC에서 1회)
cd ~/ghost5/ghost5_ws/src/ghost5_bringup
bash scripts/setup_sros2.sh

# 4. 환경변수 적용
source ~/.bashrc

# 5. 검증
cd ~/ghost5/ghost5_ws
python3 tests/unit/test_m04_verify.py
```

---

## Phase 1 전체 진행 현황

```
Phase 1 — 기반 인프라 (M01~M04)
  ├── M01  rmw_zenoh + QoS         ✅ 완료 (21/21)
  ├── M02  ghost5_interfaces       ✅ 완료 (44/44)
  ├── M03  Redis HA Blackboard     ✅ 완료 (57/57)
  └── M04  SROS2 보안              ⏳ 검증 대기
```

---

*다음 세션: test_m04_verify.py 결과 확인 후 Phase 2 (M05: SLAM) 진입.*
