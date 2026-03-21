---
title: "얼굴 인식 알고리즘 — Voice IoT Controller"
date: 2026-03-21
draft: true
tags: ["vision-ai", "yolo", "insightface"]
categories: ["vision-ai"]
description: "``` JPEG 프레임 입력 (ESP32-CAM UDP) │"
---

# 얼굴 인식 알고리즘 — Voice IoT Controller
## 기준 파일: `server/frame_analyzer.py` v1.0
## 작성일: 2026-02-24

---

## 1. 전체 파이프라인

```
JPEG 프레임 입력 (ESP32-CAM UDP)
        │
        ▼
┌─────────────────────────┐
│  [1] YOLOv8n 객체 감지   │  person 없음 → clear (종료)
└─────────────┬───────────┘
              │ person 감지
              ▼
┌─────────────────────────────────────┐
│  [2] InsightFace buffalo_sc         │
│      ① RetinaFace  — 얼굴 검출      │
│      ② ArcFace     — 임베딩 추출    │
└─────────────┬───────────────────────┘
              │ 512차원 normed_embedding
              ▼
┌─────────────────────────────────────┐
│  [3] Cosine Similarity — DB 매칭    │
│      등록 DB의 평균 임베딩과 비교    │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  [4] 판정                           │
│      known / delivery / intruder    │
│      / clear                        │
└─────────────────────────────────────┘
```

---

## 2. [1단계] YOLOv8n 객체 감지

### 설정값
```python
YOLO_MODEL       = "yolov8n.pt"    # nano 경량 모델
YOLO_CONF        = 0.50            # 신뢰도 50% 미만 무시
PERSON_CLASS     = "person"
DELIVERY_CLASSES = {"backpack", "handbag", "suitcase", "box"}
```

### 역할
- 프레임에서 사람/물체 존재 여부를 먼저 판단
- **person이 없으면 InsightFace를 호출하지 않음** → CPU 절약
- person이 있을 때만 얼굴 인식 단계로 진행
- 택배 판정을 위해 `suitcase`, `handbag` 등 패키지 클래스도 감지

### 출력 형식
```python
[
    {"label": "person", "confidence": 0.92, "x": 10, "y": 20, "w": 80, "h": 120},
    {"label": "suitcase", "confidence": 0.75, "x": 50, "y": 80, "w": 60, "h": 90},
]
```

---

## 3. [2단계] InsightFace buffalo_sc

### 모델 구성 (2단계)

#### ① RetinaFace — 얼굴 검출
```python
self._face_app.prepare(ctx_id=0, det_size=(320, 320))
```
- 입력 프레임에서 **얼굴 영역(bbox)** 검출
- **5점 랜드마크** (양쪽 눈, 코, 양쪽 입꼬리) 추출
- 랜드마크 기반으로 얼굴을 **정면으로 정렬(align)** → 인식률 향상

#### ② ArcFace — 임베딩 추출
```python
emb = face.normed_embedding  # 512차원 단위벡터 (L2 정규화 완료)
```
- 정렬된 얼굴 이미지를 **512차원 벡터**로 변환
- `normed_embedding`: 이미 L2 정규화된 단위벡터

### ArcFace 핵심 원리
같은 사람의 얼굴은 벡터 공간에서 **방향이 유사**하고,
다른 사람은 벡터 방향이 달라집니다.

```
같은 사람 A의 사진 1, 2, 3
    → 512차원 벡터 방향이 유사 (cosine 거리 작음)

다른 사람 A vs B
    → 512차원 벡터 방향이 다름 (cosine 거리 큼)
```

조명 변화, 약간의 각도 차이, 표정 변화에도 비교적 안정적인 이유가 여기 있습니다.

---

## 4. [3단계] Cosine Similarity 매칭

### 수식
```python
# normed_embedding이므로 내적 = cosine similarity
score    = float(np.dot(embedding, entry["embedding"]))
distance = 1.0 - score  # 0=동일, 1=완전히 다름

if distance < FACE_THRESHOLD:  # 0.45
    confidence = 1.0 - (distance / FACE_THRESHOLD)
    return name, confidence
else:
    return "unknown", 0.0
```

### distance 값 해석

| distance 범위 | 의미 | 판정 |
|---------------|------|------|
| 0.00 ~ 0.20 | 매우 높은 유사도 | known (고신뢰) |
| 0.20 ~ 0.45 | 유사 | known (저신뢰) |
| 0.45 이상 | 다른 사람 | unknown |
| 1.00 | 완전히 다른 얼굴 | unknown |

### 임계값 0.45 튜닝 가이드

```
threshold 낮춤 (0.35~0.40)
    → 엄격: 오인식 줄지만 등록 인물도 미인식 가능
    → 현관 조명이 밝고 카메라 위치 고정된 환경에 적합

threshold 높임 (0.48~0.55)
    → 관대: 인식률 높아지지만 오인식 증가 가능
    → 현관 조명이 어둡거나 다양한 각도가 필요한 환경에 적합
```

### 얼굴 DB 등록 방식 — 평균 임베딩

```python
# 여러 장 사진의 임베딩을 평균내어 대표 벡터 생성
mean_emb = np.mean(embeddings, axis=0)
mean_emb = mean_emb / np.linalg.norm(mean_emb)  # 재정규화
db.append({"name": name, "embedding": mean_emb})
```

사진 3~5장을 등록하면 다양한 각도/조명의 평균값이 대표 벡터가 되어
단일 사진 등록보다 인식률이 올라갑니다.

**권장 등록 사진 조건:**
- 정면 1장, 약간 좌/우 각도 각 1장
- 현관 실제 조명 환경과 유사한 조건
- 마스크 미착용 (기본 모델 기준)
- 해상도: 최소 100x100 이상

---

## 5. [4단계] 판정 로직

### 우선순위

```python
# 1순위: 등록 얼굴 매칭
if matched_name:
    → known

# 2순위: 패키지 감지 + 얼굴 미검출 (택배 기사가 고개 숙임 등)
elif pkg_boxes and not face_unknown:
    → delivery

# 3순위: 미등록 인물 (얼굴 감지됐으나 DB 매칭 실패)
elif face_unknown or (person_boxes and not matched_name):
    → intruder

# 4순위: 사람 없음
else:
    → clear
```

### 판정별 알람 동작

| 판정 | 웹앱 동작 | TTS | 쿨다운 |
|------|----------|-----|--------|
| `known` | ✅ 초록 배지 + 귀가 로그 | 없음 | 없음 |
| `delivery` | 📦 CCTV 모달 + 비프음 | "현관에 택배가 도착했습니다" | 60초 |
| `intruder` | 🚨 알람 모달 + 경보음 | "현관에 미등록 인물이 감지되었습니다" | 30초 |
| `clear` | 배지 없음 | 없음 | 없음 |

---

## 6. 성능 최적화

### 분석 주기 제한
```python
ANALYZE_EVERY = 10  # camera_stream.py
# 10fps 기준 → 1초에 1번만 분석 (CPU 절약)
```

### 비동기 executor 실행
```python
# FastAPI 이벤트 루프 블로킹 방지
verdict = await loop.run_in_executor(None, analyzer.analyze, jpeg_bytes)
```

### 조기 종료 (Early Exit)
```python
# YOLO에서 person 미감지 → InsightFace 호출 생략
if not person_boxes:
    return self._verdict("clear", ...)
```

---

## 7. 모델 비교

| 항목 | buffalo_sc (현재) | buffalo_l (고정확도) |
|------|-------------------|----------------------|
| 모델 크기 | 경량 | 대형 |
| 속도 | 빠름 (CPU 적합) | 느림 (GPU 권장) |
| 정확도 | 보통 | 높음 |
| 권장 환경 | Raspberry Pi / 임베디드 | 서버 / GPU 환경 |

---

## 8. 현재 시스템 한계 및 개선 방향

| 항목 | 현황 | 개선 방법 |
|------|------|----------|
| 카메라 해상도 | QVGA 320x240 (낮음) | ESP32-CAM PSRAM 모듈 추가 → VGA |
| 얼굴 DB | 0명 (등록 필요) | stephen 사진 3~5장 등록 |
| 인식 모델 | buffalo_sc (경량) | buffalo_l 교체 시 정확도 향상 |
| threshold | 0.45 (미튜닝) | 현장 조명 테스트 후 0.40~0.50 조정 |
| 야간 인식 | 미지원 | 조도 기반 플래시 LED 자동 점등 연동 |
| 마스크 착용 | 인식률 저하 | 마스크 특화 모델 추가 고려 |

---

## 9. 얼굴 DB 등록 명령어

```bash
# API로 등록 (권장)
curl -X POST http://localhost:8000/face-db/register \
  -F "name=stephen" \
  -F "file=@photo1.jpg"

# 폴더에 직접 복사 후 재빌드
mkdir -p face_db/known/stephen
cp *.jpg face_db/known/stephen/
curl -X POST http://localhost:8000/face-db/rebuild

# 등록 확인
curl http://localhost:8000/face-db/list

# ESP32-CAM 스냅샷으로 등록
curl http://localhost:8000/camera/entrance/snapshot -o face_db/known/stephen/snap1.jpg
```
