# Kevin Patrol Dashboard v3.3 — Multi-Robot Fleet 작업 기록

**작업일**: 2026-02-16  
**세션**: Phase 1 — RobotManager + RobotSelectorBar + DataProvider 다중화  
**기반**: app.py v3.2.1 (패널 배경 통일 완료 상태)

---

## 1. 프로젝트 분리 구조 (방식 C)

기존 단일 로봇 `dashboard/` 를 동결 보존하고, `dashboard_fleet/` 분기:

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
│   ├── app.py                     ← dashboard/app.py 기반 확장
│   ├── robot_selector.py          ← RobotSelectorBar 위젯
│   ├── kevin_patrol_cyber_theme.qss   ← 심볼릭 링크 또는 복사
│   ├── kevin_patrol_classic_theme.qss
│   ├── kevin_patrol_ironman_theme.qss
│   └── __init__.py
├── sim/
├── run_dashboard.py               ← 단일 로봇 진입점 (기존)
└── run_fleet.py                   ← 다중 로봇 진입점 (신규)
```

**핵심 원칙**: `data_provider.py` 수정 금지. `robot_manager.py`가 그 위에 래핑.

---

## 2. 신규 파일: core/robot_manager.py (124 lines)

다중 로봇 DataProvider 관리자.

```python
class RobotManager:
    def register(robot_id, provider, display_name, color)
    def unregister(robot_id)
    def get(robot_id) -> DataProvider | None
    def get_all() -> dict[str, DataProvider]
    def robot_ids() -> list[str]          # 등록 순서 유지
    def display_name(robot_id) -> str
    def color(robot_id) -> str
    def count() -> int
    def get_fleet_summary() -> list[dict]  # Phase 2 Fleet Overview용
```

- `DEFAULT_ROBOT_COLORS`: 10색 자동 할당 팔레트
- 등록 순서를 `_order` 리스트로 유지 (UI 버튼 순서 보장)

---

## 3. 신규 파일: dashboard_fleet/robot_selector.py (161 lines)

타이틀바 아래 로봇 선택 위젯.

```python
class RobotSelectorBar(QWidget):
    robot_changed = pyqtSignal(str)  # robot_id

    def refresh()                    # RobotManager 상태 → 버튼 생성
    def select_robot(robot_id)       # 프로그래밍 방식 선택
    def get_active_id() -> str       # 현재 선택 로봇
    def update_connection_status()   # 연결 카운터 갱신
```

**UI 구성**: `🤖 Fleet | [Kevin-01] [Kevin-02] [Kevin-03]  3/3`

- `QButtonGroup(exclusive=True)`: 라디오 버튼 동작
- 선택된 버튼: 해당 로봇 색상으로 하이라이트
- 비선택 버튼: `TEXT_SECONDARY` 색상
- 우측 카운터: `connected/total` (전원 연결이면 녹색, 아니면 빨간색)

---

## 4. dashboard_fleet/app.py 변경사항 (1899 lines)

### 4-1. DashboardWindow 생성자

```python
# 하위 호환: 단일 DataProvider → RobotManager 래핑
def __init__(self, provider_or_manager):
    if isinstance(provider_or_manager, RobotManager):
        self.robot_manager = provider_or_manager
    else:
        self.robot_manager = RobotManager()
        self.robot_manager.register("kevin_01", provider_or_manager, ...)
    self._active_robot_id = self.robot_manager.robot_ids()[0]
```

### 4-2. _build_ui 변경

타이틀바 아래에 `RobotSelectorBar` 1줄 추가:

```python
self.robot_selector = RobotSelectorBar(self.robot_manager)
self.robot_selector.refresh()
self.robot_selector.robot_changed.connect(self._on_robot_changed)
main_layout.addWidget(self.robot_selector)
```

### 4-3. _get_active_provider 헬퍼

```python
def _get_active_provider(self) -> DataProvider | None:
    return self.robot_manager.get(self._active_robot_id)
```

`self.provider` 직접 참조 → `self._get_active_provider()` 로 전환:
- `_on_patrol()`, `_on_stop()`, `_on_slam_reset()`, `_update_all()`

### 4-4. _on_robot_changed 신규

```python
def _on_robot_changed(self, robot_id):
    self._active_robot_id = robot_id
    self.sensor_plot.clear_data()      # 이전 로봇 센서 데이터 클리어
    self.face_detection.clear_data()   # 이전 로봇 얼굴 DB 클리어
    self.slam_map.clear_goal()         # Goal 마커 클리어
```

### 4-5. 위젯 리셋 메서드 추가

| 위젯 | 메서드 | 내용 |
|------|--------|------|
| SensorPlotWidget | `clear_data()` | deque 5개 + curve 4개 초기화, `_start_time` 리셋 |
| FaceDetectionWidget | `clear_data()` | `_face_db`, `_next_id`, `detections` 초기화 |

### 4-6. main() — 다중 로봇 초기화

```python
ROBOT_CONFIGS = [
    {"id": "kevin_01", "name": "Kevin-01", "start_x": -5.0, "start_z": -10.0, "start_yaw": 0.0},
    {"id": "kevin_02", "name": "Kevin-02", "start_x":  8.0, "start_z": -5.0,  "start_yaw": 1.57},
    {"id": "kevin_03", "name": "Kevin-03", "start_x": -3.0, "start_z":  8.0,  "start_yaw": 3.14},
]

manager = RobotManager()
for cfg in ROBOT_CONFIGS:
    sim = MockSimForDashboard()
    sim.robot_x = cfg["start_x"]  # ... 초기 위치 설정
    provider = SimDataProvider(sim)
    manager.register(cfg["id"], provider, display_name=cfg["name"])

window = DashboardWindow(manager)
```

---

## 5. QSS 파일 처리

`dashboard_fleet/` 에서 QSS를 로드할 때 경로가 `__file__` 기준이므로, 3가지 옵션:

1. **심볼릭 링크** (추천): `ln -s ../dashboard/kevin_patrol_*.qss dashboard_fleet/`
2. **복사**: 동일 파일 유지 (테마 수정 시 양쪽 반영 필요)
3. **QSS 경로를 상대 참조**: `_load_theme_qss()`에서 `dashboard/` 경로도 탐색

배포 환경에 따라 선택. 개발 중에는 심볼릭 링크가 편리.

---

## 6. 실행 방법

```bash
# 단일 로봇 (기존 — 변경 없음)
cd kevin_patrol
python run_dashboard.py

# 다중 로봇 (신규)
python run_fleet.py
```

---

## 변경 파일 요약

| 파일 | 상태 | 내용 |
|------|------|------|
| core/robot_manager.py | 신규 | RobotManager 클래스 (124 lines) |
| dashboard_fleet/app.py | 신규 (dashboard/app.py 기반) | v3.3 Multi-Robot (1899 lines) |
| dashboard_fleet/robot_selector.py | 신규 | RobotSelectorBar 위젯 (161 lines) |
| dashboard_fleet/__init__.py | 신규 | 패키지 초기화 |
| run_fleet.py | 신규 | 다중 로봇 진입점 (16 lines) |
| dashboard/app.py | 변경 없음 | v3.2.1 동결 |
| core/data_provider.py | 변경 없음 | 인터페이스 보호 |
| *.qss | 변경 없음 | 심볼릭 링크 또는 복사 |
