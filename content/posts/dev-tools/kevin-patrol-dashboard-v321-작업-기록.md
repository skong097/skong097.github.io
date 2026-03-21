---
title: "Kevin Patrol Dashboard v3.2.1 — 작업 기록"
date: 2026-03-21
draft: true
tags: ["dev-tools"]
categories: ["dev-tools"]
description: "**작업일**: 2026-02-16 **세션**: 패널 배경색 통일 + 입체감 일관성 확보 **기반**: app.py v3.2 (3테마 토글 완료 상태에서 시작)"
---

# Kevin Patrol Dashboard v3.2.1 — 작업 기록

**작업일**: 2026-02-16  
**세션**: 패널 배경색 통일 + 입체감 일관성 확보  
**기반**: app.py v3.2 (3테마 토글 완료 상태에서 시작)

---

## 1. 패널 배경색 중앙 관리 시스템

### 1-1. 문제 (v3.2 미해결 과제)

패널마다 배경 처리 방식이 제각각이었음:

| 패널 | v3.2 배경 처리 | 문제 |
|------|---------------|------|
| SLAM Map | `QColor(10, 14, 20)` 하드코딩 | 테마 전환 시 변경 안됨 |
| Camera Feed | `QColor(10, 14, 20)` 하드코딩 | 동일 |
| Face Detection | `QColor(PANEL_BG)` 하드코딩 | 동일 |
| Sensor Plot | PyQtGraph `PYQTGRAPH_THEMES` | 이미 테마 동기화 (유지) |
| Topic Monitor | paintEvent 없음 (QSS만) | 배경 직접 제어 불가, 입체감 없음 |
| Robot Status | paintEvent 없음 (QSS만) | 동일 |

v3.2에서 `_widget_bg_color()` 동적 palette 방식을 시도했으나 QSS 환경에서 실제 색상을 반환하지 않아 롤백됨.

### 1-2. 해결: PANEL_BG_THEMES 딕셔너리

테마별 배경색 상수를 직접 참조하는 방식 채택 (v3.2 로그의 "향후 과제" 그대로 구현):

```python
PANEL_BG_THEMES = {
    "cyber":   (10, 14, 20),      # 딥 네이비
    "classic": (22, 27, 34),      # GitHub Dark 톤
    "ironman": (18, 8, 4),        # #120804 — 다크 브론즈
}
```

각 위젯에 `self._panel_bg = QColor(...)` 인스턴스 변수 추가, paintEvent에서 이 값 참조.

---

## 2. 입체감 하이라이트 시스템

### 2-1. PANEL_HIGHLIGHT_THEMES

```python
PANEL_HIGHLIGHT_THEMES = {
    "cyber":   (0, 229, 255, 25),    # 시안 글로우 (미세)
    "classic": (139, 148, 158, 20),  # 그레이 하이라이트
    "ironman": (204, 51, 0, 30),     # 레드 글로우
}
```

### 2-2. 적용 방식

paintEvent에서 배경 fill 후 상단 1px 하이라이트 라인:

```python
def paintEvent(self, event):
    painter = QPainter(self)
    w, h = self.width(), self.height()
    painter.fillRect(0, 0, w, h, self._panel_bg)
    # 상단 하이라이트 라인 (입체감)
    painter.setPen(QPen(self._panel_highlight, 1))
    painter.drawLine(0, 0, w, 0)
    painter.end()
    super().paintEvent(event)
```

### 2-3. 적용 대상

| 패널 | paintEvent | 배경 | 하이라이트 |
|------|-----------|------|-----------|
| SLAM Map | 기존 (수정) | `_panel_bg` ✅ | — (맵 데이터가 덮음) |
| Camera Feed | 기존 (수정) | `_panel_bg` ✅ | — (카메라 프레임이 덮음) |
| Face Detection | 기존 (수정) | `_panel_bg` ✅ | `_panel_highlight` ✅ |
| Sensor Plot | PyQtGraph (유지) | PYQTGRAPH_THEMES ✅ | — (PyQtGraph 자체 관리) |
| Topic Monitor | **신규 추가** | `_panel_bg` ✅ | `_panel_highlight` ✅ |
| Robot Status | **신규 추가** | `_panel_bg` ✅ | `_panel_highlight` ✅ |

---

## 3. 테마 전환 동기화 흐름

```
_toggle_theme()
  → self._current_theme 변경
  → setStyleSheet(_load_theme_qss(...))       # QSS
  → _apply_pyqtgraph_theme(theme_name)        # 플롯 색상
  → _apply_panel_bg_theme(theme_name)          # 패널 배경 + 하이라이트 (신규)
```

`_apply_panel_bg_theme()` 구현:

```python
def _apply_panel_bg_theme(self, theme_name: str):
    bg_rgb = PANEL_BG_THEMES.get(theme_name, PANEL_BG_THEMES["cyber"])
    hl_rgba = PANEL_HIGHLIGHT_THEMES.get(theme_name, PANEL_HIGHLIGHT_THEMES["cyber"])
    bg_color = QColor(*bg_rgb)
    hl_color = QColor(*hl_rgba)

    for widget in [self.slam_map, self.camera_feed, self.face_detection,
                   self.topic_monitor, self.robot_status]:
        widget._panel_bg = bg_color
        if hasattr(widget, '_panel_highlight'):
            widget._panel_highlight = hl_color
        widget.update()
```

---

## 4. 변경 요약

| 파일 | 변경 내용 |
|------|----------|
| app.py | `PANEL_BG_THEMES` + `PANEL_HIGHLIGHT_THEMES` 상수 추가, SLAMMapWidget/CameraFeedWidget/FaceDetectionWidget `_panel_bg` 도입 및 paintEvent 수정, TopicMonitorWidget/RobotStatusWidget paintEvent 신규 추가, `_apply_panel_bg_theme()` 메서드 추가, `_toggle_theme()`에 호출 연결, 버전 v3.2 → v3.2.1 |

---

## 최종 파일 구조

```
dashboard/
├── app.py                            ← v3.2.1 (패널 배경 통일 + 입체감, ~1730 lines)
├── kevin_patrol_cyber_theme.qss      ← 시안 사이버 테마 (변경 없음)
├── kevin_patrol_classic_theme.qss    ← GitHub Dark 클래식 테마 (변경 없음)
└── kevin_patrol_ironman_theme.qss    ← JARVIS HUD 테마 v3 (변경 없음)
```

---

## 미해결 → 해결 상태

| 미해결 과제 (v3.2) | 상태 |
|-------------------|------|
| 패널 배경색 불일치 (6개 패널 제각각) | ✅ 해결 — PANEL_BG_THEMES 중앙 관리 |
| Topic Monitor / Robot Status 입체감 없음 | ✅ 해결 — paintEvent 추가 + 하이라이트 |
