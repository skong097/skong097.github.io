---
title: "GHOST-5 M08 — Bully Algorithm Leader Election 작업 로그"
date: 2026-03-21
draft: true
tags: ["ros2"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **Phase**: 3 — 군집 지능 **모듈**: M08"
---

# GHOST-5 M08 — Bully Algorithm Leader Election 작업 로그

**날짜**: 2026-03-18  
**Phase**: 3 — 군집 지능  
**모듈**: M08  
**작업자**: Stephen Kong (`gjkong`)

---

## 개요

5대 중 생존 로봇 중 최고 ID가 3초 내 리더로 선출되는 분산 선거 시스템 구현.  
v1.2 Split-Brain 방지 쿼럼, v1.3 Election Storm 방지 Backoff,  
[B2] 지수 백오프 + Write Lock으로 Redis HA 레이스 컨디션 방지.

---

## 생성 파일

| 파일 경로 | 설명 |
|---|---|
| `ghost5_swarm/ghost5_swarm/leader_election.py` | Bully Algorithm + Quorum + Backoff |
| `ghost5_swarm/ghost5_swarm/election_guard.py` | [B2] 지수 백오프 Write Lock |
| `ghost5_swarm/ghost5_swarm/__init__.py` | 패키지 초기화 |
| `ghost5_swarm/setup.py` | ghost5_swarm 패키지 설치 설정 |
| `ghost5_swarm/package.xml` | ghost5_swarm 패키지 의존성 정의 |
| `tests/unit/test_leader_election_m08.py` | M08 완료 조건 검증 스크립트 |

---

## 핵심 설계

### Bully Algorithm
```
1. Leader Heartbeat 3초 미수신 → 사망 투표 + 선거 발동
2. 자신보다 높은 ID에 ELECTION 전송
3. 3초 내 응답 없으면 쿼럼 확인 후 VICTORY 선언
4. 최고 ID 생존 로봇이 Leader
```

### [v1.3] Election Storm 방지 Backoff
```
delay = (MAX_ROBOT_ID - my_id) × 0.1s
Robot-5: 0.0s → Robot-4: 0.1s → Robot-3: 0.2s → Robot-1: 0.4s
```

### [v1.2] Split-Brain 방지 쿼럼
```
VICTORY 전 최소 3대 /swarm/leader_dead 투표 확인
쿼럼 미달 → 5s 대기 후 재시도 (최대 3회)
최대 재시도 초과 → 강제 선언
```

### [B2] ElectionGuard 지수 백오프
```
delay = min(0.5 × 2^attempt, 8.0) × random(0.5, 1.0)
총 최대 대기 ~19.5s (리더 교체 윈도우 충분히 커버)
WRITE_LOCK_KEY: 'swarm:election:write_lock' (TTL 10s)
```

---

## 빌드

```bash
# resource 마커 생성
mkdir -p ~/ghost5/ghost5_ws/src/ghost5_swarm/resource
touch ~/ghost5/ghost5_ws/src/ghost5_swarm/resource/ghost5_swarm

# venv 비활성화 상태
cd ~/ghost5/ghost5_ws
colcon build --packages-select ghost5_swarm --symlink-install
source install/setup.bash

# 실행 (robot_id=5, total=5)
ros2 run ghost5_swarm leader_election 5 5
```

---

## 완료 조건 검증

```bash
# 로직 단위 테스트
python3 tests/unit/test_leader_election_m08.py
```

| 완료 조건 | 하드웨어/멀티프로세스 필요 | 상태 |
|---|---|---|
| 5대 시뮬 → Robot-5 Leader 선출 | ✅ | ⬜ |
| Robot-5 종료 → Robot-4 3초 내 선출 | ✅ | ⬜ |
| Election Storm 없음 확인 | ✅ | ⬜ |
| 쿼럼 미달 승격 차단 확인 | ✅ | ⬜ |
| [B2] 지수 백오프 로그 확인 | ✅ | ⬜ |
| [B2] WriteBlockedError 발생/복구 | ✅ | ⬜ |

---

## 카피 위치

```bash
# ghost5_swarm 패키지 전체
cp -r ~/Downloads/ghost5_ws/src/ghost5_swarm \
      ~/ghost5/ghost5_ws/src/

# resource 마커 (필수)
mkdir -p ~/ghost5/ghost5_ws/src/ghost5_swarm/resource
touch ~/ghost5/ghost5_ws/src/ghost5_swarm/resource/ghost5_swarm

# 검증 스크립트
cp ~/Downloads/ghost5_ws/tests/unit/test_leader_election_m08.py \
   ~/ghost5/ghost5_ws/tests/unit/
```
