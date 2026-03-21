---
title: "GHOST-5 통합 관제 GUI 설계 — v2"
date: 2026-03-21
draft: true
tags: ["ros2", "zenoh"]
categories: ["ros2"]
description: "> 작성일: 2026-03-17 > 기준 문서: `ghost5_module_roadmap.svg`, `plan.md v1.3` > 해당 모듈: **Phase 5 — M13 (GCS API) + M14 (Foxglov"
---

# GHOST-5 통합 관제 GUI 설계 — v2

> 작성일: 2026-03-17  
> 기준 문서: `ghost5_module_roadmap.svg`, `plan.md v1.3`  
> 해당 모듈: **Phase 5 — M13 (GCS API) + M14 (Foxglove 통합 시각화)**

---

## 1. 화면 구성 개요

```
┌──────────────────────────────────────────────────────────────┐
│  상단 바  : GHOST-5 GCS | ACTIVE | rmw_zenoh | 리더: G-02   │
├──────────────────────────┬───────────────────────────────────┤
│                          │  로봇 상태 카드 (5 units)         │
│   통합 맵                │  G-01 ~ G-05 포즈/배터리/CPU      │
│   (Merged OccupancyGrid) ├───────────────────────────────────┤
│   로봇 포즈 오버레이     │  생존자 감지 이벤트               │
│                          │  S-01 (열화상 + 움직임 + VAD)     │
├──────────────────────────┤                                   │
│  로봇별 커버리지 게이지  ├───────────────────────────────────┤
│  G-01~05 + 전체 68%      │  시스템 이벤트 타임라인           │
├─────────────┬────────────┤  Bully선출/Gossip병합/Frontier    │
│  경로       │  Gossip    │  재할당 등 시간순 로그            │
│  히트맵     │  동기화    │                                   │
│  미니뷰     │  테이블    │                                   │
├─────────────┴────────────┴───────────────────────────────────┤
│  하단 통계 바: 커버리지 | Frontier수 | 생존자 | 연결 | 리더  │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 패널별 상세 설명

### 2-1. 상단 바
| 항목 | 내용 |
|---|---|
| 시스템 상태 | ACTIVE / STANDBY / ERROR 배지 |
| 미들웨어 | rmw_zenoh 연결 여부 |
| 현재 리더 | Bully Algorithm 선출 결과 (G-01 ~ G-05) |
| 타임스탬프 | ROS2 클럭 기준 실시간 |

---

### 2-2. 통합 맵 (좌 메인)
- **데이터 소스**: `/merged_map` (Gossip Protocol 병합 OccupancyGrid)
- **오버레이 항목**

| 마커 | 의미 | 색상 |
|---|---|---|
| 숫자 원 (주황 링) | 현재 Bully 리더 | `#EF9F27` |
| 숫자 원 (파랑) | 일반 로봇 | `#185FA5` |
| 소형 점 | Frontier 후보 셀 | `#EF9F27 50%` |
| 빨간 펄스 점 | 생존자 감지 위치 | `#E24B4A` |
| 초록 반투명 영역 | 탐색 완료 구역 | `#085041 25%` |
| 회색 블록 | 장애물 (OccupancyGrid = 100) | `#444441` |

- **ROS2 토픽**: `/ghost_X/amcl_pose`, `/merged_map`, `/swarm/survivor_detections`

---

### 2-3. 로봇별 탐색 커버리지 게이지
- 각 로봇이 담당 구역 대비 실제로 탐색한 비율을 바 차트로 표시
- 배터리 임계값(35%) 이하 시 바 색상 → 빨강(`#E24B4A`) 자동 전환
- 하단에 Gossip 병합 기준 전체 커버리지(68%) 별도 표시
- **데이터 소스**: M13 GCS API `GET /robots/{id}/coverage`

---

### 2-4. 경로 히트맵 미니뷰
- 5대 로봇의 누적 이동 궤적을 맵 위에 열분포 형태로 오버레이
- 중복 탐색 구역, 생존자 감지 반경, 미탐색 음영 구역 시각화
- 리더(G-02) 궤적은 주황(`#EF9F27`)으로 구분
- **데이터 소스**: M13 GCS API `GET /robots/{id}/trajectory`

---

### 2-5. Gossip 동기화 상태 테이블
| 컬럼 | 설명 |
|---|---|
| 노드 | G-01 ~ G-05 |
| 송신 | 누적 Gossip 메시지 송신 수 |
| 수신 | 누적 Gossip 메시지 수신 수 |
| Δ맵 | 마지막 병합 시 델타 맵 크기 (bytes) |
| 상태 | OK / 지연 / 단절 |

- G-05처럼 배터리 부족 → Gossip 지연 즉시 감지 가능
- **데이터 소스**: `/swarm/gossip_stats` 토픽 또는 M13 `GET /gossip/status`
- 마지막 병합 시각 + 라운드 수 표시

---

### 2-6. 로봇 상태 카드 (우측 상단)
각 카드 구성:
```
[ ID ] 이름 (★리더 표시)
       x=X.XX  y=Y.YY  YAW°
       BAT ████░░░  CPU ████░░░
       [상태 배지: 탐색중 / 이동중 / 대기 / 배터리부족 / 오프라인]
```
- 리더 카드: 테두리 주황(`#EF9F27`)
- 배터리 35% 이하: 빨간 배지 + 바 색상 전환
- **데이터 소스**: `/ghost_X/status`, `/ghost_X/amcl_pose`, M13 `GET /robots/status`

---

### 2-7. 생존자 감지 이벤트
- 3-센서 트리거 결과 표시
  - 열화상 (MLX90640): 체온 임계값 초과 온도 표시
  - 움직임 (PIR): 감지 여부
  - 음성 VAD (Silero): 음성 신호 감지 여부
- 감지 로봇 ID, 좌표(x, y), 감지 시각 기록
- **데이터 소스**: `/swarm/survivor_detections`, M13 `GET /survivors`

---

### 2-8. 이벤트 타임라인
실시간 스크롤 로그. 색상 코딩:

| 색상 | 이벤트 종류 |
|---|---|
| 빨강 `#E24B4A` | 생존자 감지, 배터리 경고, 로봇 오프라인 |
| 주황 `#EF9F27` | Bully 리더 선출, Election Storm 방지 |
| 초록 `#1D9E75` | Gossip 맵 병합, 노드 연결 수립 |
| 파랑 `#378ADD` | MMPF Frontier 재할당, Nav2 이벤트 |

- **데이터 소스**: M13 `GET /events?cursor=xxx` (커서 기반 페이징)

---

### 2-9. 하단 통계 바
| 항목 | 데이터 소스 |
|---|---|
| 맵 커버리지 % | `GET /map/coverage` |
| 활성 Frontier 수 | `GET /map/frontiers/count` |
| 생존자 감지 수 | `GET /survivors/count` |
| 로봇 연결 수 | `GET /robots/connected` |
| 현재 리더 | `/swarm/leader_id` |
| 운영 시간 | 세션 시작 기준 경과 시간 |

---

## 3. M16 이후 드론 통합 시 변경 사항

```
통합 맵    → 드론 마커 추가 (고도 정보 포함, 다이아몬드 형태 구분)
로봇 카드  → 하단에 드론 상태 행 추가 (고도, 속도, Zenoh 연결)
이벤트     → PX4 SITL 이벤트 / Fallback 인수 이벤트 추가
Gossip 테이블 → drone_0 행 추가
```

---

## 4. 구현 파일

| 파일 | 설명 |
|---|---|
| `ghost5_gcs_ui_v2.html` | 전체 GUI 설계 화면 (독립 실행 가능 HTML) |
| `ghost5_gcs_ui_v2.md` | 본 설계 문서 |

---

## 5. 관련 모듈 의존 관계

```
M01 (rmw_zenoh)
  └─ M03 (Redis Blackboard)
       └─ M08 (Bully Leader Election)
       └─ M09 (MMPF Frontier)
       └─ M10 (Multi-Robot SLAM)
            └─ M11 (생존자 감지)
            └─ M12 (Rendezvous + RSSI)
                 └─ M13 (GCS FastAPI)   ← 백엔드
                 └─ M14 (Foxglove)      ← 프론트엔드 (본 설계)
```
