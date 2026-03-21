---
title: PyQt6에서 3테마 다크 시스템 구축하기 — Cyber / Classic / JARVIS
date: 2026-02-12
tags:
- pyqt6
- python
- ui
- theme
- dark-mode
- qss
categories:
- dev-tools
summary: QSS 외부 파일 + 상수 딕셔너리 + paintEvent 동기화로 PyQt6 애플리케이션에 실시간 테마 전환을 구현한 방법
cover:
  image: images/covers/post-pyqt6-dark-theme.png
  alt: PyQt6 Dark Theme System
  hidden: false
draft: false
ShowToc: true
TocOpen: true
---


---

## 배경

Kevin Patrol Dashboard는 원래 하드코딩된 단일 다크 테마였습니다. 하지만 데모 시연, 개인 취향, 환경에 따라 분위기를 바꾸고 싶었습니다. "버튼 하나로 테마를 전환할 수 있으면 좋겠다"에서 출발했습니다.


---

### 3가지 테마 컨셉

- **Cyber**: 딥 네이비 + 시안 액센트 — 보안 관제 콘솔 느낌
- **Classic**: GitHub Dark 톤 + 그레이 — 개발자 친화적
- **JARVIS (Iron Man)**: 다크 브론즈 + 레드/골드 — SF 느낌


---

## 접근 방법: 3계층 테마 시스템

테마 전환이 어려운 이유는 PyQt6에서 색상을 제어하는 방법이 여러 곳에 분산되어 있기 때문입니다.

1. **QSS (스타일시트)**: QGroupBox, QPushButton 등 표준 위젯
2. **paintEvent**: SLAM Map, Camera Feed 등 커스텀 위젯
3. **PyQtGraph**: Sensor Plot의 배경/전경/커브 색상

이 3가지를 하나의 테마 전환 흐름으로 통일해야 합니다.

```python
def _toggle_theme(self):
    # 1. QSS 전환
    self.setStyleSheet(_load_theme_qss(theme_name))
    # 2. PyQtGraph 색상 전환
    self._apply_pyqtgraph_theme(theme_name)
    # 3. 커스텀 위젯 배경 전환
    self._apply_panel_bg_theme(theme_name)
```


---

## 구현


---

### 테마별 배경색 상수

```python
PANEL_BG_THEMES = {
    "cyber":   (10, 14, 20),
    "classic": (22, 27, 34),
    "ironman": (18, 8, 4),
}

PANEL_HIGHLIGHT_THEMES = {
    "cyber":   (0, 229, 255, 25),
    "classic": (139, 148, 158, 20),
    "ironman": (204, 51, 0, 30),
}
```


---

### paintEvent 통일

모든 커스텀 위젯에 `_panel_bg` 인스턴스 변수를 추가하고, `paintEvent`에서 이 변수를 참조하도록 통일했습니다.

<!-- 상세 구현 코드 추가 -->


---

## 결과

- 버튼 하나로 6개 패널 + 사이드바 + 플롯 + 배경이 동시에 전환
- 3테마 모두 입체감 일관성 확보 (상단 하이라이트 라인)
- QSS 파일은 외부 분리되어 디자이너가 독립적으로 수정 가능


---

## 배운 점

1. **QSS만으로는 부족하다**: `paintEvent`로 직접 그리는 위젯은 QSS가 적용되지 않습니다
2. **상수 딕셔너리 중앙 관리**: 색상을 한 곳에서 관리해야 일관성이 유지됩니다
3. **입체감의 핵심**: 상단에 1px 하이라이트 라인만 넣어도 패널이 살아납니다


---

## 다음 단계

- 사용자 커스텀 테마 (JSON 기반)
- 테마별 아이콘 세트
