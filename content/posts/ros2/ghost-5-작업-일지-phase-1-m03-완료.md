---
title: "GHOST-5 작업 일지 | Phase 1 — M03 완료 ✅"
date: 2026-03-21
draft: true
tags: ["ros2"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **현재 단계**: Phase 1 — M03 완료 / M04 진입 준비 **작업자**: gjkong@pc"
---

# GHOST-5 작업 일지 | Phase 1 — M03 완료 ✅
**날짜**: 2026-03-18  
**현재 단계**: Phase 1 — M03 완료 / M04 진입 준비  
**작업자**: gjkong@pc  
**프로젝트 홈**: `/home/gjkong/ghost5`

---

## 오늘 작업 요약

| 순서 | 작업 내용 | 상태 |
|------|-----------|------|
| 1 | `blackboard.py` — Redis HA 클라이언트 래퍼 | ✅ 완료 |
| 2 | `semantic_memory.py` — 의미론적 이벤트 메모리 | ✅ 완료 |
| 3 | `blackboard_node.py` — SetBlackboard/GetBlackboard 서비스 서버 | ✅ 완료 |
| 4 | `package.xml` / `setup.py` / `setup.cfg` | ✅ 완료 |
| 5 | `redis-ghost5-master.conf` / `redis-ghost5-replica.conf` | ✅ 완료 |
| 6 | Redis 서버 설치 및 ghost5 설정으로 실행 | ✅ 완료 |
| 7 | M03 완료 조건 검증 **57/57 PASS** | ✅ 완료 |

---

## M03 최종 검증 결과

```
결과: 57/57 통과  |  실패: 0
✅ PASS  M03 완료 조건 모두 충족 🎉
→ M04 (SROS2 보안) 진행 가능
```

| 항목 | 결과 |
|------|------|
| V1: ghost5_swarm 파일 8개 존재 | ✅ |
| V2: blackboard.py 클래스 3개 + 메서드 10개 | ✅ |
| V3: semantic_memory.py 클래스 3개 + 메서드 7개 | ✅ |
| V4: Redis ping + role=master 확인 | ✅ |
| V5: Blackboard 기능 (set/get, claim, victim, leader) | ✅ |
| V6: SemanticMemory 기능 (record, blocked, summary) | ✅ |
| V7: colcon build ghost5_swarm | ✅ |
| V8: ROS2 서비스 타입 2개 확인 | ✅ |

---

## 트러블슈팅 기록

| 문제 | 원인 | 해결 |
|------|------|------|
| `No module named 'redis'` | 시스템 Python에 redis 미설치 | `pip install redis --break-system-packages` |
| `redis-server: command not found` | Redis 서버 미설치 | `sudo apt install redis-server` |
| `AUTH called without any password` | 기본 Redis(비밀번호 없음)가 실행 중 | `sudo systemctl stop redis-server` 후 ghost5 설정으로 재실행 |

> ⚠️ **주의**: 재부팅 시 기본 Redis가 자동 재시작될 수 있음  
> → `sudo systemctl disable redis-server` 로 자동시작 비활성화 권장  
> → ghost5 Redis 자동시작이 필요하면 별도 systemd 서비스 등록 필요 (M04 이후 검토)

---

## 확정된 파일 위치

```
ghost5_ws/src/ghost5_swarm/
├── package.xml                  ✅
├── setup.py                     ✅
├── setup.cfg                    ✅
├── resource/ghost5_swarm        ✅
└── ghost5_swarm/
    ├── __init__.py              ✅
    ├── blackboard.py            ✅  GhostBlackboard (Redis HA 클라이언트)
    ├── semantic_memory.py       ✅  SemanticMemory (이벤트 메모리)
    └── blackboard_node.py       ✅  ROS2 서비스 서버

ghost5_ws/tests/unit/
└── test_m03_verify.py           ✅

/etc/redis/
└── redis-ghost5-master.conf     ✅  현재 실행 중 (0.0.0.0:6379)
```

---

## Phase 1 전체 진행 현황

```
Phase 1 — 기반 인프라 (M01~M04)
  ├── M01  rmw_zenoh + QoS         ✅ 완료 (21/21)
  ├── M02  ghost5_interfaces       ✅ 완료 (44/44)
  ├── M03  Redis HA Blackboard     ✅ 완료 (57/57)
  └── M04  SROS2 보안              ⏳ 대기
```

---

## 다음 작업 — M04 (SROS2 보안)

- [ ] `setup_sros2.sh` — keystore 생성 스크립트
- [ ] `ghost5_policy.xml` — 노드별 토픽/서비스 권한 정책
- [ ] SROS2 환경 통합 테스트
- [ ] `test_m04_verify.py`

---

## 참고 문서

| 문서 | 버전 | 위치 |
|------|------|------|
| GHOST5_plan_v2.md | v2.1 | `/home/gjkong/ghost5/` |
| GHOST5_구현단계_v2.md | v1.2 | `/home/gjkong/ghost5/` |
| 작업 일지 M02 | 2026-03-18 | `GHOST5_작업일지_20260318_Phase1_M02.md` |

---

*다음 세션: M04 (SROS2 보안) 진입.*
