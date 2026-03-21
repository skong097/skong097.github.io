---
title: "MyPet Phase 1 개발일지 — 2025-02-15"
date: 2026-03-21
draft: true
tags: ["dev-tools"]
categories: ["dev-tools"]
description: "Phase 1 가상 반려견 시스템의 비주얼/사운드/UI 품질 업그레이드 - OpenGameArt 'Dog' (rmazanek, CC0) → dog_medium.png - 6x6 그리드, 셀 60x38px, 6개 애니"
---

# MyPet Phase 1 개발일지 — 2025-02-15

## 오늘의 목표
Phase 1 가상 반려견 시스템의 비주얼/사운드/UI 품질 업그레이드

---

## 1. 스프라이트 강아지 업그레이드

### 1-1. OpenGameArt 픽셀 스프라이트 시도
- OpenGameArt "Dog" (rmazanek, CC0) → dog_medium.png
- 6x6 그리드, 셀 60x38px, 6개 애니메이션 행
- `SpriteSheet` 클래스 구현 (행별 프레임 추출, 알파 블렌딩)
- **결과**: 픽셀아트가 만화풍이라 실물 느낌 부족 → 방향 전환

### 1-2. 실물 강아지 사진 시도
- 검정 배경 + 흰 배경 쌍 12장 업로드
- 검정/흰 배경 차이를 이용한 **알파 매트 추출** (alpha = 1 - (W - B) / 255)
- GrabCut 단독보다 훨씬 깨끗한 결과
- **문제**: 엎드림 포즈 원본이 몸통 잘림 → idle에 sit 이미지 대체

### 1-3. AI 일러스트 스프라이트 시트 (최종 채택)
- 3x3 그리드 일러스트 한 장에서 **8개 포즈** 자동 추출
- 체크무늬 배경 제거: HSV 채도 + 밝기 기반 마스킹 + 최대 컨투어 필터
- `pet_renderer.py`를 **개별 포즈 이미지 로딩 방식**으로 전환

### 최종 포즈 매핑 (8종)

| 상태 | 포즈 파일 | 설명 |
|------|----------|------|
| IDLE | lie_side.png | 엎드려 쉬기 (측면) |
| STAND | stand_side.png | 서있기 (측면) |
| SIT | sit_back.png | 앉은 뒷모습 |
| STAY | lie_front.png | 엎드려 대기 (정면) |
| BARK / PRAISE | sit_bark.png | 정면 앉음, 입 벌림 |
| COME / WALK / RUN | stand_right.png | 측면 서있기 |
| SPIN | sit_side.png | 측면 앉아 짖기 |
| TURN | stand_back.png | 뒷모습 |

---

## 2. 효과음 시스템

### 사운드 파일 생성 (Python 합성, 7종)

| 파일 | 설명 | 길이 |
|------|------|------|
| bark.wav | 두 번 짧은 짖기 (300-500Hz 글라이드 + 하모닉스) | 0.8s |
| whine.wav | 낑낑거림 (800-1200Hz 비브라토) | 1.2s |
| pant.wav | 헉헉 호흡 (4회 사이클, 노이즈 기반) | 1.5s |
| eat.wav | 쩝쩝 먹기 (5회 클릭, 팝+스티키 사운드) | 1.0s |
| praise.wav | 밝은 차임 (C5-E5-G5-C6 아르페지오) | 0.8s |
| spin.wav | 휘리릭 회전 (300→2800Hz 스윕) | 0.6s |
| come.wav | 발걸음 (4회 탭 사운드) | 1.0s |

### 명령 → 사운드 매핑 (config.py)

```python
COMMAND_SOUND_MAP = {
    "BARK": "BARK", "EAT": "EAT", "COME": "COME",
    "RUN": "PANT", "WALK": "COME", "PRAISE": "PRAISE",
    "SPIN": "SPIN", "STAY": "WHINE",
}
```

### sound_manager.py 개선
- 중복 재생 방지 (쿨다운 0.5초)
- `play_on_state_change()` — 상태 변경 시에만 재생
- `set_volume()` — 전체 볼륨 조절
- 볼륨 키: `+`/`-` (0.1단위), `m` (음소거 토글)

---

## 3. 전체화면 지원

### 구현 방식
- `f` 키로 전체화면/윈도우 모드 토글
- `cv2.namedWindow("MyPet", cv2.WINDOW_NORMAL)` 한 번만 생성
- `cv2.setWindowProperty`로 전체화면/일반 전환 (윈도우 파괴 없음)
- 시작 시 `tkinter`로 화면 해상도 감지 (백업: xrandr)
- `imshow` 직전 `cv2.resize(canvas, (screen_w, screen_h))`로 명시적 확대

### 해결한 이슈들
- `destroyWindow` 후 재생성 시 크래시 → 윈도우 파괴 없이 속성만 변경
- `getWindowImageRect`가 타이틀바 크기(98x28) 반환 → 사용 제거
- `WINDOW_NORMAL` 자동 스케일링 미동작 → 명시적 `cv2.resize` 적용

---

## 4. 강아지 이동 범위 제한

### pet_controller.py 수정
- 좌우 마진: `0.18` (화면 양쪽 18% 진입 불가 → 스프라이트 잘림 방지)
- Y축: `PET_PLAY_AREA_Y_MIN(0.40) ~ Y_MAX(0.82)` 유지
- RUN/WALK 시 벽 충돌 → **자동 방향 반전** (자연스러운 왕복)
- 초기 위치: 플레이 영역 중앙 `(0.5, 0.61)`

---

## 수정된 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| pet_renderer.py | 일러스트 포즈 이미지 로딩, 알파 블렌딩, 모션 효과 |
| config.py | 사운드 매핑 7종, COMMAND_SOUND_MAP 추가 |
| sound_manager.py | 쿨다운, 볼륨 조절, 상태 변경 트리거 |
| main.py | 전체화면 토글, 볼륨 키, 동적 캔버스 크기 |
| pet_controller.py | 이동 범위 제한(margin 0.18), 벽 반전 |

### 추가된 에셋

```
assets/sprites/
  ├── sit_bark.png      # 앉음 정면 입벌림
  ├── stand_side.png     # 서있음 측면
  ├── stand_right.png    # 서있음 측면 (오른쪽)
  ├── lie_front.png      # 엎드림 정면
  ├── lie_side.png       # 엎드림 측면
  ├── sit_side.png       # 앉음 측면
  ├── stand_back.png     # 서있음 뒷모습
  └── sit_back.png       # 앉음 뒷모습

assets/sounds/
  ├── bark.wav
  ├── whine.wav
  ├── pant.wav
  ├── eat.wav
  ├── praise.wav
  ├── spin.wav
  └── come.wav
```

---

## 키 조작 가이드 (최종)

| 키 | 기능 |
|----|------|
| q | 종료 |
| f | 전체화면 토글 |
| 1 | 거실 배경 |
| 2 | 야외 배경 |
| Tab | 배경 전환 |
| n | 다음 야외 사진 |
| +/= | 볼륨 업 |
| - | 볼륨 다운 |
| m | 음소거 토글 |
| s/d/r/w/b/e/p/t/c/g | 데모 모드 명령 |

---

## Phase 1 진행 상황

| 항목 | 상태 |
|------|------|
| 프로젝트 구조 + 메인 루프 | ✅ 완료 |
| 손 제스처 인식 (12종) | ✅ 완료 |
| 강아지 FSM + 감정 시스템 | ✅ 완료 |
| 강아지 렌더링 (8포즈 일러스트) | ✅ 완료 |
| 배경 시스템 (거실 도형 + 야외 사진) | ✅ 완료 |
| UI 오버레이 (PIP, 감정바, HUD) | ✅ 완료 |
| 효과음 7종 + 볼륨 조절 | ✅ 완료 |
| 전체화면 토글 | ✅ 완료 |
| 이동 범위 제한 + 벽 반전 | ✅ 완료 |
| 훈련 모드 (미션/레벨업) | 🔲 미완료 |
| 제스처 ML 분류기 개선 | 🔲 미완료 |

## 다음 단계 후보
- 훈련 모드 (미션 시스템, 레벨업, gamification)
- 제스처 ML 분류기 개선
- Phase 1.5 → AR 오버레이 / EyeCon 감정 교감 / 강화학습 AI
