---
title: "Kevin Patrol Dashboard v3.3 — Multi-Robot Fleet 작업 기록"
date: 2026-03-21
draft: true
tags: ["robotics", "slam", "fleet", "patrol"]
categories: ["robotics"]
description: "**작업일**: 2026-02-16 **세션**: Phase 1~2 완료 — 다중 로봇 모니터링 + Fleet Overview **기반**: app.py v3.2.1 (패널 배경 통일 완료 상태)"
---

# Kevin Patrol Dashboard v3.3 — Multi-Robot Fleet 작업 기록

**작업일**: 2026-02-16  
**세션**: Phase 1~2 완료 — 다중 로봇 모니터링 + Fleet Overview  
**기반**: app.py v3.2.1 (패널 배경 통일 완료 상태)  
**결과**: app_fleet.py v3.3 (~2360 lines)

---

## 전체 완료 현황

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 1 | RobotManager + DataProvider 다중화 + RobotSelectorBar | ✅ 완료 |
| Phase 2 | Fleet Overview 미니맵 (SLAM 배경 + 상태 색상 + 감지 이벤트 + 클릭 선택) | ✅ 완료 |
| Phase 3 | 분할 화면 뷰 (2~4대 동시 패널 그리드) | ⬜ 미착수 |
| Phase 4 | ROS2 네임스페이스 기반 실제 로봇 연동 | ⬜ 미착수 |

---

## 1. 프로젝트 분리 구조 (방식 C)

기존 단일 로봇 `dashboard/`를 동결 보존, `dashboard_fleet/` 분기:

```
kevin_patrol/
├── core/
│   ├── data_provider.py          ← 기존 (수정 없음, 인터페이스 보호)
│   ├── robot_manager.py          ← 신규 (DataProvider 위에 래핑)
│   └── __init__.py
├── dashboard/                     ← 단일 로봇 v3.2.1 (동결)
│   ├── app.py
│   ├── kevin_patrol_cyber_theme.qss
│   ├── kevin_patrol_classic_theme.qss
│   ├── kevin_patrol_ironman_theme.qss
│   └── __init__.py
├── dashboard_fleet/               ← 다중 로봇 v3.3 (신규)
│   ├── app.py                     ← v3.3 (~2360 lines)
│   ├── robot_selector.py          ← RobotSelectorBar 위젯
│   ├── kevin_patrol_*.qss         ← 심볼릭 링크
│   └── __init__.py
├── sim/
├── run_dashboard.py               ← 단일 로봇 진입점 (기존)
└── run_fleet.py                   ← 다중 로봇 진입점 (신규)
```

**핵심 원칙**: `data_provider.py` 수정 금지. `robot_manager.py`가 그 위에 래핑.

---

## 2. Phase 1: RobotManager + RobotSelectorBar

### 2-1. core/robot_manager.py (180 lines)

```python
class RobotManager:
    register(robot_id, provider, display_name, color)
    unregister(robot_id)
    get(robot_id) → DataProvider | None
    get_all() → dict[str, DataProvider]
    robot_ids() → list[str]              # 등록 순서 유지
    display_name(robot_id) → str
    color(robot_id) → str
    count() → int
    get_fleet_summary() → list[dict]     # 전체 로봇 요약
    get_merged_grid() → (ndarray, dict)  # 병합 SLAM 그리드
    get_all_detections() → list[dict]    # 전체 로봇 감지 이벤트
```

- `DEFAULT_ROBOT_COLORS`: 10색 자동 할당 팔레트
- 등록 순서를 `_order` 리스트로 유지 (UI 버튼 순서 보장)

### 2-2. dashboard_fleet/robot_selector.py (161 lines)

```python
class RobotSelectorBar(QWidget):
    robot_changed = pyqtSignal(str)      # robot_id
    refresh()                             # 버튼 갱신
    select_robot(robot_id)               # 프로그래밍 방식 선택
    get_active_id() → str
    update_connection_status()           # 연결 카운터 갱신
```

**UI**: `🤖 Fleet | [Kevin-01] [Kevin-02] [Kevin-03]  3/3`

### 2-3. DashboardWindow 변경

- 생성자: `provider` → `provider_or_manager` (하위 호환 래핑)
- `_get_active_provider()` 헬퍼로 모든 provider 참조 통일
- `_on_robot_changed()`: Sensor Plot / Face Detection 클리어, Fleet Overview 동기화
- `_on_fleet_robot_clicked()`: 미니맵 클릭 → 셀렉터 연동
- Command Bar (PATROL/STOP/SLAM RESET): active provider 기반

### 2-4. 위젯 리셋 메서드

| 위젯 | 메서드 | 내용 |
|------|--------|------|
| SensorPlotWidget | `clear_data()` | deque 5개 + curve 4개 초기화 |
| FaceDetectionWidget | `clear_data()` | face_db + next_id + detections 초기화 |

### 2-5. Alert History 로봇 태그

알림 메시지에 `[Kevin-01]`, `[Kevin-02]` 등 로봇 이름 태그 추가:
```
15:56:27 ℹ [Kevin-02] Face detected at (4, 7)
15:56:30 🚨 [Kevin-01] Fall detected at (3, -7)
```

---

## 3. Phase 2: Fleet Overview 미니맵

### 3-1. FleetOverviewWidget 위치

사이드바 최상단 (Topic Monitor 위):
```
사이드바
├── 🌍 Fleet Overview    ← 신규
├── 📡 Topic Monitor
└── 🔔 Alert History
```

### 3-2. SLAM 그리드 배경

- `RobotManager.get_merged_grid()`: 전체 로봇의 SLAM 그리드 병합
  - free 영역 합집합, 장애물 우선
- QImage 캐시: 10프레임(1초)마다 래스터화 → 성능 유지
- free 영역: 어두운 녹색 / 벽: 어두운 주황

### 3-3. 로봇 표시

- 방향 삼각형: **모드별 색상** (auto_patrol=녹색, manual=파란색, charging=노란색, emergency=빨간색)
- 선택된 로봇: 글로우 링 + 굵은 이름
- 마우스 호버: 커서 변경 + 약한 글로우
- **클릭 시**: `robot_clicked` 시그널 → 셀렉터 연동 → 전체 패널 전환
- 이름 라벨 + 미니 배터리 바

### 3-4. 감지 이벤트 시각화

- `RobotManager.get_all_detections()`: 전체 로봇의 감지 수집
- **Face 감지**: 파란 원 + 사람 아이콘 (머리+몸), 3초 페이드아웃
- **Fall 감지**: 빨간 펄스 링 + 다이아몬드 + "FALL" 라벨, 5초 페이드아웃
- 중복 방지: `_prev_det_keys` set으로 동일 이벤트 재등록 차단

### 3-5. 하단 요약 바

```
● 3 patrol  ● 0 idle  👤 1  ⚠ 1 fall
```

배터리 부족 로봇이 있으면 `⚠ N alert` 표시.

### 3-6. 테마 동기화

`_apply_panel_bg_theme()`에 fleet_overview 포함 → 3테마 모두 배경색 동기화.

---

## 4. MockSim 다중 궤적

각 로봇이 **다른 영역에서 다른 속도/반경으로** 순찰:

| 로봇 | 중심 좌표 | 반경 | 속도 | 위상 |
|------|----------|------|------|------|
| Kevin-01 | (-6, -4) | 6m | 0.30 | 0° |
| Kevin-02 | (8, 2) | 5m | 0.25 | 120° |
| Kevin-03 | (2, 10) | 7m | 0.35 | 240° |

MockSimForDashboard 생성자에 파라미터 추가:
```python
MockSimForDashboard(patrol_radius, patrol_speed,
                    patrol_offset_x, patrol_offset_z, patrol_phase)
```

---

## 5. 파일 목록 및 라인 수

| 파일 | 상태 | Lines | 내용 |
|------|------|-------|------|
| core/robot_manager.py | 신규 | 180 | RobotManager 클래스 |
| dashboard_fleet/app.py | 신규 | ~2360 | v3.3 Multi-Robot Fleet Dashboard |
| dashboard_fleet/robot_selector.py | 신규 | 161 | RobotSelectorBar 위젯 |
| dashboard_fleet/__init__.py | 신규 | 1 | 패키지 초기화 |
| run_fleet.py | 신규 | 16 | 다중 로봇 진입점 |
| dashboard/app.py | 변경 없음 | ~1786 | v3.2.1 동결 |
| core/data_provider.py | 변경 없음 | — | 인터페이스 보호 |
| *.qss × 3 | 변경 없음 | — | 심볼릭 링크 |

---

## 6. 실행 방법

```bash
# 단일 로봇 (기존 — 변경 없음)
cd ~/dev_ws/kevin_patrol
python run_dashboard.py

# 다중 로봇 Fleet (신규)
python run_fleet.py
```

---

## 7. UI 레이아웃 (v3.3 최종)

```
┌──────────────────────────────────────────────────────────────────┐
│  🤖 Kevin Patrol Dashboard  v3.3                                │
│  [SIM] [LIVE] [REC]  [🎨 CYBER]  ● Connected                   │
├──────────────────────────────────────────────────────────────────┤
│  🤖 Fleet | [Kevin-01] [Kevin-02] [Kevin-03]              3/3   │
├──────────────────┬──────────────────┬────────────────────────────┤
│                  │                  │  🌍 Fleet Overview          │
│   🗺 SLAM Map    │  📷 Camera Feed  │  (전체 로봇 위치 + SLAM     │
│   (선택된 로봇)   │  (선택된 로봇)    │   배경 + 감지 이벤트)       │
│                  │                  │  ● 3 patrol ● 0 idle       │
├──────────────────┼──────────────────┼────────────────────────────┤
│                  │                  │  📡 Topic Monitor           │
│   📊 Sensor Plot │  🤖 Status +     │  (선택된 로봇의 토픽)        │
│   (선택된 로봇)   │  🔍 Detection    ├────────────────────────────┤
│                  │                  │  🔔 Alert History           │
│                  │                  │  (전체 로봇 통합 + 태그)      │
├──────────────────┴──────────────────┴────────────────────────────┤
│  ▶ PATROL  ⏸ STOP  📍 SET GOAL  🔄 SLAM RESET   ⚠ ALERTS      │
└──────────────────────────────────────────────────────────────────┘
```

---

## 8. 다음 단계

- **Phase 3**: 분할 화면 뷰 — [SINGLE] [SPLIT-2] [SPLIT-4] 모드
- **Phase 4**: ROS2 네임스페이스 기반 실제 로봇 연동
- **추가 개선**: Fleet Overview에 순찰 궤적 트레일, 로봇 간 거리 표시
