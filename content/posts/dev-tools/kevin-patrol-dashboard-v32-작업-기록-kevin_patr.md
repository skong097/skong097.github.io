---
title: "Kevin Patrol Dashboard v3.2 — 작업 기록"
date: 2026-03-21
draft: true
tags: ["dev-tools"]
categories: ["dev-tools"]
description: "**작업일**: 2026-02-16 **세션**: 테마 시스템 고도화 + UI 일관성 개선 **기반**: app.py v3.2 (Cyber Theme 통합 완료 상태에서 시작)"
---

# Kevin Patrol Dashboard v3.2 — 작업 기록

**작업일**: 2026-02-16  
**세션**: 테마 시스템 고도화 + UI 일관성 개선  
**기반**: app.py v3.2 (Cyber Theme 통합 완료 상태에서 시작)

---

## 1. 테마 토글 시스템 구현

### 1-1. 테마 로더 범용화

기존 `_load_cyber_theme_qss()` 단일 로더를 `_load_theme_qss(theme_name)` 범용 로더로 변경.

```python
def _load_theme_qss(theme_name: str = "cyber") -> str:
    qss_map = {
        "cyber":   "kevin_patrol_cyber_theme.qss",
        "classic": "kevin_patrol_classic_theme.qss",
        "ironman": "kevin_patrol_ironman_theme.qss",
    }
```

### 1-2. PyQtGraph 테마 동기화

`PYQTGRAPH_THEMES` 딕셔너리로 테마별 플롯 색상(배경/축/그리드) 관리.

| 테마 | background | foreground | axis_pen | grid_alpha |
|------|-----------|-----------|---------|-----------|
| cyber | #0d1117 | #5a6a7a | #2a3a4a | 0.1 |
| classic | #161b22 | #8b949e | #30363d | 0.2 |
| ironman | #120804 | #9a7040 | #4a2000 | 0.08 |

`_apply_pyqtgraph_theme()` 메서드가 테마 전환 시 `plot_top`, `plot_bot` 실시간 업데이트.

### 1-3. 타이틀바 토글 버튼

🎨 버튼 클릭으로 3개 테마 순환: `CYBER → CLASSIC → JARVIS → CYBER`

```python
def _toggle_theme(self):
    theme_cycle = ["cyber", "classic", "ironman"]
    theme_labels = {"cyber": "CYBER", "classic": "CLASSIC", "ironman": "JARVIS"}
    idx = theme_cycle.index(self._current_theme)
    self._current_theme = theme_cycle[(idx + 1) % len(theme_cycle)]
```

### 1-4. DashboardWindow 테마 상태 관리

```python
self._current_theme = "cyber"  # "cyber" | "classic" | "ironman"
self.setStyleSheet(_load_theme_qss(self._current_theme))
```

---

## 2. Iron Man HUD 테마 (JARVIS) — v1 → v2 → v3 진화

**파일**: `kevin_patrol_ironman_theme.qss`

### v1 → v2: 배경 일관성 개선

v1은 배경색이 `#0c0604`, `#1a0e08`, `#241208`, `#120a06` 네 가지가 혼재하여 일관성 부족.

v2에서 배경을 2단계로 통일:

| 용도 | v1 색상 | v2 색상 | 비고 |
|------|--------|--------|------|
| 최하단 배경 | #0c0604 | #080402 | 거의 순수 블랙 |
| 패널/위젯 | #1a0e08 | #0e0806 | 미세하게 밝은 블랙 |
| 입력/hover | #241208 | #140c08 | hover/active 전용 |
| 보더 | #3a1c0c | #2a1608 | 다크 브론즈 |

### v2 → v3: Iron Man HUD 느낌 극대화

v2는 배경 통일은 됐지만 전체적으로 밋밋하고 Iron Man 느낌 부족. v3에서 대폭 강화:

**색상 채도 업**:

| 요소 | v2 | v3 | 변화 |
|------|----|----|------|
| 배경 (deep) | #080402 | #0a0200 | 레드 틴트 강화 |
| 배경 (panel) | #0e0806 | #120804 | 따뜻한 다크 |
| 보더 (기본) | #2a1608 | #4a2000 | 다크 골드로 밝게 |
| 보더 (활성) | #ff3c1a | #cc3300 | 글로잉 레드 |
| 텍스트 (주요) | #e8d0a8 | #ffe0b0 | 밝은 골드 |
| 텍스트 (보조) | #6a4a30 | #9a7040 | 웜 브론즈 밝게 |
| 액센트 레드 | #ff3c1a | #ff4422 | 더 선명 |
| 액센트 골드 | #ffc040 | #ffcc33 | 더 밝고 생생 |

**HUD 글로잉 보더 시스템**:
- QGroupBox: `border-top: 2px solid #cc3300` — 상단 레드 글로우
- QGroupBox::title: `border: 1px solid #cc8800` + `border-bottom: 2px solid #ff4422` — 골드 프레임 + 레드 하단
- QPushButton: `border-bottom: 2px solid #cc3300` — 하단 레드 라인, hover 시 `#ffcc33` 골드로 전환
- QTabWidget::pane: `border-top: 2px solid #cc3300`
- QToolTip: `border-bottom: 2px solid #ffcc33`

**프로그레스바 5단계 아크 리액터 그라데이션**:
```css
stop: 0 #882000 → stop: 0.3 #cc3300 → stop: 0.6 #ff4422 → stop: 0.85 #ff9900 → stop: 1 #ffcc33
```

**슬라이더**: 핸들 `border: 2px solid #ffcc33` 골드 테두리, sub-page 레드→골드 그라데이션

---

## 3. 버튼 사이즈 통일

### 문제

타이틀바 모드 버튼(60px폭, 높이 미지정), Command Bar 버튼(높이 36, 폭 미지정), 테마 버튼(90x26) — 모두 제각각.

### 해결

상수 기반 사이즈 관리 도입:

```python
BTN_TITLEBAR_W = 90       # 타이틀바 버튼 가로
BTN_TITLEBAR_H = 30       # 타이틀바 버튼 세로
BTN_COMMAND_W  = 130      # Command Bar 버튼 가로
BTN_COMMAND_H  = 36       # Command Bar 버튼 세로
```

| 그룹 | 대상 | 사이즈 |
|------|------|--------|
| 타이틀바 | SIM, LIVE, REC, 🎨 THEME | 90 × 30 |
| Command Bar | PATROL, STOP, SET GOAL, SLAM RESET, ALERTS | 130 × 36 |
| 사이드바 | Clear All | 높이 36 (Command Bar와 동일) |

---

## 4. 타이틀바 레이아웃 개선

### 4-1. 위젯 순서 변경

**변경 전**: `[SIM] [LIVE] [REC]` → `● Connected` → `[🎨 CYBER]`  
**변경 후**: `[SIM] [LIVE] [REC]` → `[🎨 CYBER]` → `● Connected`

이유: 기능 버튼(모드+테마)은 묶고, 상태 인디케이터(Connected)는 맨 끝에 분리.

### 4-2. Connected 라벨 고정폭 + 중앙 정렬

모드 전환 시 텍스트 길이 변화("● Connected", "○ LIVE (no link)", "▶ PLAYBACK")로 버튼들이 밀리는 문제 해결.

```python
self.conn_label = QLabel("● Connected")
self.conn_label.setFixedSize(160, BTN_TITLEBAR_H)
self.conn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
self.conn_label.setStyleSheet(
    f"color: {ACCENT_GREEN}; font-weight: bold; padding-top: 2px;")
```

- `setFixedSize(160, 30)`: 텍스트 변해도 레이아웃 고정
- `AlignCenter`: 🎨 버튼과 우측 끝 사이 중앙 배치
- `padding-top: 2px`: 버튼 텍스트 baseline과 수직 위치 맞춤

---

## 5. Alert 토스트 팝업 위치 변경

### 문제

토스트가 우측 상단(y=50)에서 아래로 쌓여 Topic Monitor 패널을 가림.

### 해결 (1차: Alert History 위 → 2차: Status+Detection 하단)

1차로 Alert History 위젯 위에 배치했으나, 최종적으로 **Status+Detection 패널 하단 빈 공간**으로 이동.

```python
class AlertManager:
    def __init__(self, parent_window, history_widget, status_panel=None):
        self.status_panel = status_panel  # g4_panel 참조

    def _reposition_toasts(self):
        panel = self.status_panel
        if panel and panel.isVisible():
            pos = panel.mapTo(self.parent, QPoint(0, 0))
            base_x = pos.x() + 4
            base_bottom = pos.y() + panel.height()
            area_w = panel.width() - 8

        # 아래에서 위로 쌓기: 패널 하단부터
        y = base_bottom
        for t in reversed(self._active_toasts):
            t.setFixedWidth(min(350, area_w))
            y -= t.height() + 4
            t.move(base_x, max(0, y))
```

- `g4_panel`을 `self.g4_panel`로 인스턴스 변수화하여 AlertManager에 전달
- 패널 하단에서 위로 쌓임, 왼쪽 정렬 (`base_x = pos.x() + 4`)
- Topic Monitor, Alert History 모두 가리지 않음

---

## 6. 패널 배경색 통일 시도 (롤백)

### 시도 내용

`_widget_bg_color()` 헬퍼 함수로 부모 QGroupBox의 palette 배경색을 동적으로 가져와 모든 패널에 적용 시도.

### 롤백 사유

QSS 환경에서 `palette().color(backgroundRole())`가 실제 QSS 색상을 반환하지 않아, 오히려 모든 패널 배경이 깨짐. 원본 하드코딩 값으로 원복.

### 현재 상태 (원본 유지)

| 패널 | 배경색 처리 |
|------|-----------|
| SLAM Map | `QColor(10, 14, 20)` — paintEvent 하드코딩 |
| Camera Feed | `QColor(10, 14, 20)` — paintEvent 하드코딩 |
| Sensor Plot | PyQtGraph `PYQTGRAPH_THEMES` — 테마별 동기화 |
| Face Detection | `QColor(PANEL_BG)` — paintEvent 하드코딩 |
| Topic Monitor | 배경 없음 (QSS QGroupBox 배경만) |
| Robot Status | 배경 없음 (QSS QGroupBox 배경만) |

### 향후 과제

Topic Monitor, Robot Status 패널에 다른 패널과 동일한 입체감 부여 필요. QSS palette 연동이 아닌, 테마별 배경색 상수를 직접 참조하는 방식 검토.

---

## 7. UI 디테일 개선

### 7-1. 패널 타이틀 변경

`🤖 Status + 🧑 Face` → `🤖 Status + 🔍 Detection`

### 7-2. Face Detection Total 텍스트 개선

**변경 전**: 좌측 정렬, `TEXT_DIM` 색상, Consolas 8pt  
**변경 후**: 우측 정렬, `TEXT_SECONDARY` 색상, `_get_mono_font(10)` (JetBrains Mono 10pt)

```python
total_text = f"Total: {len(self._face_db)} faces / {total} detections"
fm = painter.fontMetrics()
text_w = fm.horizontalAdvance(total_text)
painter.drawText(w - text_w - 8, h - 6, total_text)
```

### 7-3. Clear All 버튼 폰트 통일

`QFont("Consolas", 9)` + `font-size: 9px` → `_get_mono_font(10)` — Total 텍스트와 동일한 10pt로 통일.

---

## 최종 파일 구조

```
dashboard/
├── app.py                            ← v3.2 (3테마 순환 토글, ~1715 lines)
├── kevin_patrol_cyber_theme.qss      ← 시안 사이버 테마
├── kevin_patrol_classic_theme.qss    ← GitHub Dark 클래식 테마
└── kevin_patrol_ironman_theme.qss    ← JARVIS HUD 테마 (v3 — 글로잉 보더)
```

---

## 변경 파일 요약

| 파일 | 변경 내용 |
|------|----------|
| app.py | 테마 로더 범용화, 3테마 토글, 버튼 사이즈 통일, 타이틀바 순서/정렬, 토스트 위치→Status+Detection 하단, Total 우측 정렬, Clear All 폰트 통일, 패널 타이틀 변경, PyQtGraph ironman 색상 v3 업데이트 |
| kevin_patrol_ironman_theme.qss | v3 — 글로잉 보더, 색상 채도 강화, HUD 느낌 극대화 |
| kevin_patrol_classic_theme.qss | 변경 없음 (이전 세션에서 생성) |
| kevin_patrol_cyber_theme.qss | 변경 없음 (이전 세션에서 생성) |
