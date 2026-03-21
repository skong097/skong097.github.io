---
title: "🎮 Spot the Difference — 검지 포인팅 숨은그림찾기"
date: 2026-03-21
draft: true
tags: ["vision-ai", "yolo", "opencv", "mediapipe"]
categories: ["vision-ai"]
description: "MediaPipe Hands 기반 **검지 포인팅**으로 사진 속 차이점을 찾는 비전 AI 게임. 키보드 없이 **손 제스처만으로** 게임 전체를 조작할 수 있습니다. ```"
---

# 🎮 Spot the Difference — 검지 포인팅 숨은그림찾기

MediaPipe Hands 기반 **검지 포인팅**으로 사진 속 차이점을 찾는 비전 AI 게임.
키보드 없이 **손 제스처만으로** 게임 전체를 조작할 수 있습니다.

## 📁 파일 구조

```
gaze_puzzle/
├── main.py               # 게임 실행 진입점
├── hand_tracker.py        # MediaPipe Hands 검지 추적 + 제스처 인식
├── puzzle_generator.py    # 초급(낙서) + 중급(YOLO/영역변형) 퍼즐 생성기
├── requirements.txt       # Python 패키지 목록
├── README.md
└── assets/                # 퍼즐 사진 (jpg/png, 자동 인식)
    ├── 01_marathon.jpg
    ├── 02_hobbit_door.jpg
    └── ...
```

## 🔧 환경 설정

```bash
cd gaze_puzzle
python3 -m venv gaze_venv
source gaze_venv/bin/activate    # Windows: gaze_venv\Scripts\activate
pip install -r requirements.txt
```

**주요 패키지:**

| 패키지 | 용도 |
|--------|------|
| mediapipe | 손 관절 추적 (21 keypoints) |
| opencv-python | 영상 처리 + 게임 렌더링 |
| numpy (<2) | 수치 연산 (MediaPipe 호환 필수) |
| ultralytics | YOLO v8 객체 감지 (중급 모드) |

> ⚠️ **numpy 2.x는 MediaPipe와 호환되지 않습니다.** `numpy<2` 버전을 유지해야 합니다.

## ▶️ 실행

```bash
source gaze_venv/bin/activate
python main.py
```

웹캠이 연결되어 있어야 합니다. 게임 창(1280×720)이 열리면 손을 카메라에 보여주세요.

## 🎮 조작법

### 손 제스처 (키보드 없이 조작)

| 제스처 | 동작 | 유지 시간 | 허용 상태 |
|--------|------|---------|---------|
| ☝️ 검지 포인팅 | 차이점 가리키기 | 0.8초 유지 → 발견! | playing |
| 👋 손바닥 → 뒤집기 | 새 게임 / 다음 레벨 | 0.5초 유지 후 플립 | ready, clear |
| 👊 주먹 쥐기 | 현재 레벨 재시작 | 1.5초 유지 | playing |
| 🤞 검지+중지 교차 | 게임 종료 | 2.0초 유지 | 항상 |

**포인팅 판별:** 검지만 펴고 중지 접으면 초록 커서(활성), 아니면 주황 커서(비활성)

**플립 제스처 흐름:**
```
손바닥 보이기 (0.5초) → PIP에 "PALM..." → "FLIP NOW!" → 손 뒤집기 → 트리거!
```

### 키보드 (보조)

| 키 | 동작 |
|----|------|
| N | 새 게임 / 다음 레벨 |
| R | 현재 레벨 재시작 |
| Q | 종료 |
| M | 모드 전환 (초급 ↔ 중급) |

## 🎯 게임 모드

**[M] 키**로 전환합니다.

### 초급 (EASY) — 코믹 낙서

사진 위에 코믹 낙서가 추가됩니다. 이질적이라서 쉽게 찾을 수 있습니다.

**낙서 14종:** 콧수염, 뿔, 왕관, 하트, 별, 안경, 번개, 화살표, 소용돌이, 고양이 귀, 날개, 천사 링, 반창고, 꽃

### 중급 (MEDIUM) — YOLO 객체 복제 + 사진 영역 변형

사진 속 실제 내용을 기반으로 자연스러운 차이점을 생성합니다.

**YOLO 감지 성공 시 (사람, 자동차 등):**

| 변형 | 설명 |
|------|------|
| clone_shift | 객체를 다른 위치에 복제 |
| clone_flip | 좌우 반전하여 복제 |
| clone_scale | 70~90% 축소하여 복제 |
| remove | 객체를 inpainting으로 제거 |

**YOLO 감지 실패 시 (풍경 사진 등):**

| 변형 | 설명 |
|------|------|
| region_clone | 텍스처 풍부한 영역을 다른 위치에 seamless clone |
| region_remove | 영역을 inpainting으로 제거 |
| region_color | 색조를 미묘하게 변경 |
| region_flip | 부분 좌우 반전 |
| texture_swap | 먼 거리의 두 영역 텍스처 교환 |

## 📊 난이도 (레벨별)

| 레벨 | 차이점 수 | 초급 낙서 크기 | 중급 패치 크기 |
|------|---------|-------------|-------------|
| 1 | 3~4개 | 큼 (25~40px) | 큼 (35~55px) |
| 2 | 4~6개 | 중간 (18~32px) | 중간 (25~40px) |
| 3+ | 5~8개 | 작음 (12~22px) | 작음 (18~30px) |

## 🎉 축하 애니메이션

레벨 클리어 시 **3곳(좌/중/우)에서 120개 파티클**이 발사됩니다.

- 5가지 도형: 원, 별, 하트, 사각형, 다이아몬드
- 8가지 색상
- 물리: 중력 + 회전 + 페이드아웃
- 지속 시간: 2~4초

## 🖼️ 사진 추가

`assets/` 폴더에 jpg 또는 png 파일을 넣으면 자동으로 인식됩니다.
게임 시작 시 **랜덤 사진**에서 시작하며, N키/플립 제스처로 다음 사진으로 순환합니다.
대기 화면에서는 **2.5초 간격 슬라이드쇼**로 미리보기가 표시됩니다.

## 🖥️ 화면 구성 (1280×720)

```
┌──────────────────────────────────────────────────┐
│ Time: 12.3s  Found: 2/4  Level: 1  EASY  Score: 80│
│                     Flip:Next Fist:Restart Cross:Quit│
├───────────────┬──────────────────────────────────┤
│               │                                  │
│   ORIGINAL    │        FIND DIFFERENCES!         │
│               │                                  │
│               │                                  │
│         ┌─────┴──────┐                           │
│         │  CAMERA    │                           │
│         │  (PIP)     │                           │
└─────────┴────────────┴───────────────────────────┘
```

## ⚙️ 주요 파라미터

| 항목 | 값 | 파일 |
|------|-----|------|
| Dwell 판정 시간 | 0.8초 | `main.py` |
| 판정 범위 보정 | -5px | `main.py` |
| 커서 스무딩 | 0.4 | `hand_tracker.py` |
| 플립 손바닥 유지 | 0.5초 | `hand_tracker.py` |
| 주먹 유지 | 1.5초 | `hand_tracker.py` |
| 교차 유지 | 2.0초 | `hand_tracker.py` |
| 슬라이드쇼 간격 | 2.5초 | `main.py` |

## 🧰 기술 스택

| 기술 | 역할 |
|------|------|
| MediaPipe Hands | 21개 손 관절 추적, 포인팅/주먹/교차 제스처 판별 |
| OpenCV | 영상 캡처, 게임 렌더링, seamlessClone, inpainting |
| YOLO v8n | 사진 속 객체 감지 (중급 모드) |
| NumPy | 좌표 연산, 스무딩, 외적 계산 |
