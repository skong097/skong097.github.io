---
title: "다중 로봇 플릿 모니터링 대시보드 만들기 — Kevin Patrol Fleet"
date: 2026-02-16
tags: ["pyqt6", "python", "robotics", "dashboard", "fleet", "ros2"]
categories: ["robotics"]
summary: "5~10대 자율 순찰 로봇을 하나의 화면에서 모니터링하는 PyQt6 대시보드를 설계하고 구현한 과정"
cover:
  image: "images/fleet-dashboard-cyber.png"
  alt: "Kevin Patrol Fleet Dashboard"
draft: true
ShowToc: true
TocOpen: true
---

## 배경

자율 순찰 로봇 1대를 모니터링하는 대시보드(v3.2.1)는 이미 완성된 상태였습니다. 하지만 실제 운영 환경에서는 여러 대의 로봇이 동시에 순찰합니다. "로봇 3대가 건물 각 층을 돌고 있는데, 2층 로봇에서 낙상이 감지됐다" — 이런 상황을 단일 화면에서 즉시 파악하려면 다중 로봇 모니터링이 필수였습니다.

### 요구사항

- 5~10대 규모 로봇 플릿 지원
- 로봇 선택 한 번으로 모든 패널 데이터 전환
- Fleet Overview: 전체 로봇 위치를 하나의 맵에서 한눈에
- 기존 단일 로봇 버전과 완전히 분리된 코드베이스

## 설계 원칙

가장 중요한 결정은 **기존 DataProvider 인터페이스를 건드리지 않는 것**이었습니다.

```
data_provider.py (수정 금지)
    ↑
robot_manager.py (새로 추가 — DataProvider 위에 래핑)
```

`RobotManager`가 `robot_id → DataProvider` 매핑을 관리하고, 대시보드는 활성 로봇의 provider만 조회합니다. 이렇게 하면 단일 로봇 버전에 영향을 주지 않으면서 다중 로봇을 지원할 수 있습니다.

### 하위 호환성

```python
# 단일 provider를 넘겨도 자동으로 RobotManager 래핑
def __init__(self, provider_or_manager):
    if isinstance(provider_or_manager, RobotManager):
        self.robot_manager = provider_or_manager
    else:
        self.robot_manager = RobotManager()
        self.robot_manager.register("kevin_01", provider_or_manager, ...)
```

## 핵심 구현

### RobotManager

```python
class RobotManager:
    def register(self, robot_id, provider, display_name="", color=""):
        """로봇 등록 — 색상 자동 할당, 등록 순서 유지"""

    def get(self, robot_id) -> DataProvider | None:
        """선택된 로봇의 DataProvider 반환"""

    def get_fleet_summary(self) -> list[dict]:
        """전체 로봇의 위치/배터리/모드/속도 요약"""

    def get_merged_grid(self):
        """전체 로봇의 SLAM 그리드 병합 (탐색 범위 시각화용)"""

    def get_all_detections(self) -> list[dict]:
        """전체 로봇의 감지 이벤트 수집"""
```

### RobotSelectorBar

타이틀바 아래에 로봇 선택 버튼을 배치합니다. `QButtonGroup(exclusive=True)`로 라디오 버튼 동작을 구현하고, 선택된 로봇은 고유 색상으로 하이라이트됩니다.

### Fleet Overview 미니맵

가장 공들인 부분입니다. 단순히 로봇 위치만 찍는 게 아니라:

1. **SLAM 그리드 배경**: 전체 로봇의 탐색 영역을 병합하여 QImage로 캐시 (1초마다 갱신)
2. **모드별 색상 코딩**: 순찰 중(녹색), 정지(파란색), 긴급(빨간색)
3. **감지 이벤트 시각화**: Face(파란 아이콘, 3초 페이드아웃), Fall(빨간 펄스, 5초 페이드아웃)
4. **클릭으로 로봇 선택**: `robot_clicked` 시그널 → 셀렉터 연동

```python
# 감지 이벤트 페이드아웃 렌더링
alpha = 1.0 - (elapsed / duration)  # 시간에 따라 투명해짐
painter.setBrush(QColor(255, 50, 50, int(200 * alpha)))
```

## 프로젝트 분리 구조

```
kevin_patrol/
├── core/
│   ├── data_provider.py      ← 수정 없음
│   └── robot_manager.py      ← 신규 (래핑)
├── dashboard/                 ← 단일 로봇 v3.2.1 (동결)
├── dashboard_fleet/           ← 다중 로봇 v3.3 (신규)
├── run_dashboard.py           ← 단일
└── run_fleet.py               ← 다중
```

방식 C(dashboard_fleet + core에 robot_manager 추가)를 선택한 이유는 `core/`를 공유하면서도 기존 코드에 영향을 주지 않기 때문입니다.

## 결과

- 3대 로봇이 각각 다른 영역/속도/반경으로 독립 순찰
- Fleet Overview에서 전체 상태를 실시간 파악
- 로봇 클릭 한 번으로 6개 패널 데이터 즉시 전환
- Alert History에 `[Kevin-01]` 태그로 어떤 로봇의 이벤트인지 즉시 구분

## 배운 점

1. **인터페이스를 건드리지 마라**: 기존 DataProvider 위에 래핑하는 방식이 가장 안전했습니다
2. **QImage 캐시**: Fleet Overview에서 SLAM 그리드를 매 프레임 그리면 성능이 떨어집니다. 1초 주기 캐시로 해결
3. **위젯 리셋**: 로봇 전환 시 이전 데이터가 잔류하는 문제 — `clear_data()` 메서드가 필수

## 다음 단계

- Phase 3: 분할 화면 뷰 (2~4대 동시 모니터링)
- Phase 4: ROS2 네임스페이스 기반 실제 로봇 연동
