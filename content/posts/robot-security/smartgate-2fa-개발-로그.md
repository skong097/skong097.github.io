---
title: "SmartGate 2FA 개발 로그"
date: 2026-03-21
draft: true
tags: ["robot-security", "2fa"]
categories: ["robot-security"]
description: "**작성일:** 2026-02-28 **환경:** `~/dev_ws/smartgate` (독립 프로젝트) **Python:** venv | MediaPipe 0.10.14 | InsightFace buffalo_sc"
---

# SmartGate 2FA 개발 로그
**작성일:** 2026-02-28  
**환경:** `~/dev_ws/smartgate` (독립 프로젝트)  
**Python:** venv | MediaPipe 0.10.14 | InsightFace buffalo_sc

---

## 1. 프로젝트 구조

```
smartgate/
├── main.py                  # 메인 루프 + 상태머신
├── config.yaml              # 전체 설정 (프로파일 포함)
├── register_face.py         # 얼굴 등록 유틸리티
├── face_db/
│   ├── encodings.pkl        # ArcFace 임베딩 캐시 (자동생성)
│   └── known/<username>/    # 사용자별 얼굴 이미지
├── logs/
│   └── smartgate.log
└── modules/
    ├── face_auth.py         # InsightFace 얼굴 인증
    ├── gesture_auth.py      # MediaPipe 제스처 인증
    ├── liveness.py          # Liveness Detection (신규)
    ├── gate_controller.py   # ESP32 게이트 제어
    ├── logger.py            # AuthLogger
    └── cv2_text.py          # PIL 한글 렌더링
```

---

## 2. 인증 흐름 (상태머신)

```
IDLE
 │  얼굴 감지 + ArcFace 유사도 ≥ tolerance
 ▼
LIVENESS  ◀── 신규 추가
 │  챌린지 풀에서 N개 랜덤 선택 후 순차 수행
 │  (blink / yaw / nod / mouth_open)
 │  통과 시
 ▼
FACE_OK
 │  MediaPipe 손 제스처 시퀀스 입력
 │  예: ☝(1) → ✊(0) → 3개
 ▼
GESTURE_OK
 │  GateController.open_gate()
 ▼
IDLE (자동 복귀, open_duration_sec 후 닫힘)

※ 연속 실패 max_failures 회 → LOCKED (lockout_sec 초)
```

---

## 3. 모듈별 구현 내용

### 3-1. 얼굴 인증 — `modules/face_auth.py`

- **엔진:** InsightFace `buffalo_sc` (ArcFace 512d 임베딩)
- **비교:** 코사인 유사도 `np.dot(known_mat, emb)`
- **임계값:** `tolerance: 0.40` (권장 0.35~0.50)
- **캐시:** `encodings.pkl` — 이미지 mtime 비교로 자동 갱신
- **최소 얼굴:** `min_face_size: 80px` 이하 무시

### 3-2. 제스처 인증 — `modules/gesture_auth.py`

| 모드 | 설명 | 예시 |
|------|------|------|
| `number` | 손가락 수 시퀀스 | `[1, 0, 3]` ☝→✊→3개 |
| `shape` | 공중 도형 드로잉 | `["circle", "triangle", "square"]` |

- **안정화:** `hold_frames: 8` 연속 동일 프레임 유지 후 인정
- **쿨다운:** `cooldown_sec: 1.5` 동일 제스처 중복 방지
- **타임아웃:** `timeout_sec: 7.0`

### 3-3. Liveness Detection — `modules/liveness.py` (신규 v3.0)

#### 챌린지 종류

| 챌린지 | 측정 방법 | 랜드마크 |
|--------|-----------|----------|
| `blink` | EAR (Eye Aspect Ratio) < 임계값 | LEFT/RIGHT_EYE 6점 |
| `yaw` | 코끝-귀 x 비율 변화량 | NOSE_TIP, TEMPLE 양측 |
| `nod` | 코끝 Pitch 변화량 | NOSE_TIP, FOREHEAD, CHIN |
| `mouth_open` | MAR (Mouth Aspect Ratio) > 임계값 | 입술 6점 |

#### 랜덤화 구조
```
challenges_pool: [blink, yaw, nod, mouth_open]  (4종)
        ↓ num_challenges=2 개 랜덤 선택 (중복 없음)
        ↓ random_order=true 로 순서도 무작위
        ↓ yaw 방향 지시도 랜덤 (왼→오 / 오→왼)
경우의 수: 4P2 × 2(yaw 방향) = 24가지 조합
```

### 3-4. 게이트 제어 — `modules/gate_controller.py`

- **현재:** ESP32 시리얼 통신 (`GATE_OPEN\n` / `GATE_CLOSE\n`)
- **테스트:** `esp32.enabled: false` → 시뮬레이션 모드 (로그만 출력)
- **자동 닫힘:** `open_duration_sec: 5` 초 후 `threading.Timer`로 닫힘

---

## 4. 보안 위협 분석 및 대응

| 위협 | 위험도 | 대응 |
|------|--------|------|
| 2D 스푸핑 (사진/영상) | 매우 높음 | ✅ Liveness Detection 도입 |
| 제스처 탈취 (어깨 너머) | 낮음 | ✅ 시퀀스 조합으로 부분 방어 |
| 재전송 공격 (UDP 패킷) | 높음 | ⬜ AES-GCM 암호화 (향후 과제) |
| 물리적 무력화 | 보통 | ⬜ 실내외 제어부 분리 (향후 과제) |

---

## 5. 프로파일 전환 시스템 (v3.0)

`config.yaml`의 `active_profile` 한 줄만 변경하면 전환됩니다.

```yaml
liveness:
  active_profile: "laptop"   # "laptop" | "espcam"
```

### 프로파일 비교

| 파라미터 | laptop | espcam |
|----------|--------|--------|
| `challenges_pool` | blink, yaw, nod, mouth_open | blink, yaw |
| `num_challenges` | 2 | 2 |
| `timeout_sec` | 8.0s | 10.0s |
| `blink_consec_frames` | 2 | **1** (저FPS 대응) |
| `yaw_threshold` | 0.15 | **0.12** (압축 열화 대응) |

### ESP-CAM 환경 제약 (배포 시 고려사항)

| 항목 | 노트북 | ESP-CAM |
|------|--------|---------|
| FPS | 30fps | 5~10fps |
| 해상도 | 640×480 | SVGA 800×600 |
| 카메라 각도 | 정면 | 위에서 내려다봄 |
| 이미지 품질 | 선명 | JPEG 압축 열화 |
| `nod` 챌린지 | ✅ 안정 | ⚠️ 각도 문제로 불안정 |
| `mouth_open` | ✅ 안정 | ⚠️ 압축으로 랜드마크 정밀도 저하 |

---

## 6. 얼굴 등록 — `register_face.py`

```bash
cd ~/dev_ws/smartgate
python register_face.py
```

- 사용자 이름 입력 → `face_db/known/<name>/` 에 저장
- SPACE: 캡처 / q: 종료
- 등록 완료 후 `encodings.pkl` 자동 삭제 → 다음 실행 시 재임베딩
- 한글 UI: `modules/cv2_text.py` PIL 렌더링

---

## 7. 실행

```bash
cd ~/dev_ws/smartgate

# 일반 실행
python main.py

# ESP32 없이 테스트 (시뮬레이션)
# config.yaml: esp32.enabled: false 확인 후
python main.py

# Liveness 비활성화 (빠른 테스트)
# config.yaml: liveness.enabled: false
python main.py
```

**키 단축키**
- `q` : 종료
- `r` : 얼굴 DB 재임베딩

---

## 8. 향후 과제

- [ ] UDP AES-128 GCM 암호화 (ESP32-CAM 재전송 공격 방어)
- [ ] ESP-CAM 환경에서 `espcam` 프로파일 파라미터 튜닝
- [ ] 실내외 제어부 물리적 분리 아키텍처 적용
- [ ] Voice IoT Controller (`iot-repo-1`) 완전 통합
  - `camera_stream.py` → `SmartGateManager.push_frame()`
  - `GET /smartgate/status` API
  - `POST /smartgate/reload-faces` API
