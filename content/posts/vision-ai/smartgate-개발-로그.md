---
title: "SmartGate 개발 로그"
date: 2026-03-21
draft: true
tags: ["vision-ai", "opencv", "mediapipe", "insightface"]
categories: ["vision-ai"]
description: "| 항목 | 내용 | |------|------| | 프로젝트명 | SmartGate - 2팩터 인증 게이트 시스템 |"
---

# SmartGate 개발 로그

## 프로젝트 개요
| 항목 | 내용 |
|------|------|
| 프로젝트명 | SmartGate - 2팩터 인증 게이트 시스템 |
| 개발일 | 2026-02-26 |
| 환경 | Ubuntu 24.04 / Python 3.12 / venv |
| 경로 | ~/dev_ws/smartgate/ |
| 목표 | 얼굴 인식 + 손가락 수신호/도형 드로잉 시퀀스 기반 스마트 대문 자동화 |

---

## 시스템 아키텍처

```
[카메라 입력 (노트북 / 추후 ESP Cam)]
         │
         ▼
┌─────────────────────────┐
│  1팩터: 얼굴 인식        │  InsightFace buffalo_sc
│  ArcFace 512d 임베딩    │  코사인 유사도 >= 0.40
└────────────┬────────────┘
             │ 성공
             ▼
┌─────────────────────────┐
│  2팩터: 제스처 인증      │  MediaPipe Hands (mp.solutions)
│  number: 수신호 시퀀스   │  예: ☝ → ✊ → 3개
│  shape : 도형 드로잉     │  예: ○ → △ → □
└────────────┬────────────┘
             │ 성공
             ▼
┌─────────────────────────┐
│  ESP32 시리얼 신호       │  GATE_OPEN / GATE_CLOSE
│  logs/smartgate.log     │  인증 이벤트 기록
└─────────────────────────┘
```

---

## 기술 스택

### 핵심 라이브러리 (동작 확인 버전)

| 분류 | 라이브러리 | 버전 | 역할 |
|------|-----------|------|------|
| 얼굴 인식 | insightface | 0.7.3 | ArcFace 512d 임베딩 추출 |
| 추론 엔진 | onnxruntime | 1.24.2 | InsightFace ONNX 모델 CPU 추론 |
| 손 인식 | mediapipe | **0.10.14** ※고정 | HandLandmarker 21개 키포인트 |
| 영상 처리 | opencv-python | 4.13.0.92 | 카메라 캡처 / 도형 분류 / 렌더링 |
| 한글 렌더링 | Pillow | 12.1.1 | cv2.putText 한글 깨짐 대체 |
| 수치 연산 | numpy | 2.4.2 | 임베딩 코사인 유사도 계산 |
| 설정 | PyYAML | 6.0.3 | config.yaml 파싱 |
| 시리얼 통신 | pyserial | 3.5 | ESP32 GATE_OPEN 신호 |

> ※ mediapipe 0.10.15+ 에서 `mp.solutions` AttributeError 발생 → 0.10.14 고정 필수

---

## 파일 구조

```
smartgate/
├── main.py                  # AuthState 상태 머신 메인 루프
├── register_face.py         # 얼굴 등록 유틸 (InsightFace 감지 검증)
├── config.yaml              # 전체 설정 (모드/얼굴/제스처/보안/ESP32)
├── requirements.txt         # 버전 고정 패키지 목록
├── modules/
│   ├── face_auth.py         # FaceAuthenticator - InsightFace 기반
│   ├── gesture_auth.py      # GestureAuthenticator v2.0 - 듀얼 모드
│   ├── gate_controller.py   # GateController - ESP32 시리얼 통신
│   ├── logger.py            # AuthLogger - 파일+콘솔 이중 로깅
│   └── cv2_text.py          # PIL 기반 한글 텍스트 렌더링
├── face_db/
│   ├── encodings.pkl        # ArcFace 512d 임베딩 캐시 (자동 생성)
│   └── known/
│       └── stephen/         # 서브디렉토리명 = 사용자 이름
│           ├── 001.jpg
│           └── ...          # 총 38장 등록
└── logs/
    └── smartgate.log
```

---

## 핵심 모듈 상세

### face_auth.py - InsightFace 기반 얼굴 인증
- **모델**: `buffalo_sc` (경량) / `buffalo_l` (고정밀) config로 선택
- **임베딩**: ArcFace 512d `normed_embedding` (정규화 완료)
- **매칭**: `np.dot(known_mat, emb)` 코사인 유사도, 임계값 `0.40`
- **캐시**: `face_db/encodings.pkl` — 이미지 mtime 비교 자동 갱신
- **디렉토리**: `face_db/known/<username>/` → voice_iot_controller 호환

### gesture_auth.py v2.0 - 듀얼 모드 인증
#### number 모드 (손가락 수 시퀀스)
- `mp.solutions.hands` 21개 랜드마크
- 엄지: wrist x vs index_mcp x 방향 판별 후 TIP x vs PIP x
- 검지~소지: TIP y < PIP y (펴짐)
- `hold_frames=8` 연속 동일값 → 안정 제스처 인정
- `cooldown_sec=1.5` 동일 수신호 재인식 방지

#### shape 모드 (도형 드로잉 시퀀스)
- 검지(1개)만 펴면 검지 TIP 좌표 궤적 수집 시작
- 주먹(0)으로 도형 완성 신호
- `ShapeClassifier`: 64점 리샘플링 → `cv2.approxPolyDP()` 꼭짓점 수 + 원형도(circularity)
  - `circularity > 0.65` → circle
  - `vertices == 3` → triangle
  - `vertices == 4`, 종횡비 0.5~2.0 → square
- `draw_trail()`: 그라데이션 궤적선 + 시작/끝점 + 분류 결과 실시간 표시

### cv2_text.py - PIL 한글 렌더링
- `put_text()` / `put_text_centered()` — cv2.putText 대체
- 나눔폰트 우선 탐색 → `fc-list :lang=ko` 동적 탐색 → 기본폰트 폴백
- 그림자 효과 옵션 지원

### 인증 상태 머신 (main.py)
```
IDLE ──(얼굴 인식 성공)──▶ FACE_OK
FACE_OK ──(시퀀스 완성)──▶ GESTURE_OK ──▶ IDLE
FACE_OK ──(타임아웃)────▶ IDLE  fail_count++
fail_count >= 3 ─────────▶ LOCKED (30초)
LOCKED ──(30초 경과)────▶ IDLE  fail_count 초기화
```

---

## 인증 모드 설정 (config.yaml)

```yaml
gesture_auth:
  # number 모드
  mode: "number"
  sequence: [1, 0, 3]       # ☝ → ✊ → 3개
  timeout_sec: 7.0

  # shape 모드 (전환 시 주석 교체)
  # mode: "shape"
  # sequence: ["circle", "triangle", "square"]
  # timeout_sec: 15.0
```

---

## 트러블슈팅 기록

| 문제 | 원인 | 해결 |
|------|------|------|
| `face_recognition_models` 설치 오류 | git 접근 제한 | InsightFace로 전면 교체 |
| `mp.solutions` AttributeError | mediapipe 0.10.15+ API 변경 | `pip install mediapipe==0.10.14` 버전 고정 |
| `FaceAuthenticator` TypeError (5 args) | 파일 내 구버전 클래스 중복 잔존 | 파일 하단 구버전 클래스 완전 제거 |
| `cv2.imshow` 미구현 오류 | opencv-contrib-python (headless) 설치됨 | `pip install opencv-python` 으로 교체 |
| 등록 사용자 38번 중복 출력 | `dict.fromkeys()` 누락 | known_names 출력 시 중복 제거 적용 |
| 한글 깨짐 | cv2.putText 한글 미지원 | PIL + 나눔폰트 기반 cv2_text.py 추가 |

---

## 설치 순서

```bash
# 가상환경
python -m venv venv && source venv/bin/activate

# 패키지 (버전 고정)
pip install mediapipe==0.10.14
pip install insightface==0.7.3 onnxruntime==1.24.2
pip install opencv-python==4.13.0.92
pip install numpy==2.4.2 Pillow==12.1.1 PyYAML==6.0.3 pyserial==3.5

# 한글 폰트
sudo apt install fonts-nanum -y

# 얼굴 등록
python register_face.py

# 실행
python main.py
```

---

## 동작 확인 결과

| 항목 | 결과 |
|------|------|
| 얼굴 인식 | ✅ 정상 (stephen 38장, 유사도 ~0.74) |
| number 모드 [1,0,3] | ✅ 정상 동작 |
| shape 모드 ○△□ | ✅ 정상 동작 |
| 한글 UI | ✅ 나눔폰트 정상 렌더링 |
| ACCESS GRANTED | ✅ 정상 표시 |

---

## TODO (다음 단계)

- [ ] ESP Cam MJPEG 스트림 연동 (노트북 카메라 → ESP Cam 교체)
- [ ] ESP32 Arduino 펌웨어 작성 (GATE_OPEN 수신 → GPIO HIGH)
- [ ] YOLOv8 person detection 전처리 (사람 감지 시만 얼굴 인식 동작)
- [ ] 도형 인식 정확도 개선 (임계값 튜닝 / DTW 알고리즘 적용 검토)
- [ ] 등록 사용자 관리 UI
- [ ] 다중 시퀀스 지원 (사용자별 다른 PIN)
- [ ] 인증 성공 시 알림 (텔레그램/슬랙)
