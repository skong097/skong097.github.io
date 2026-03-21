---
title: "Voice IoT Controller — 개발 일지"
date: 2026-03-21
draft: true
tags: ["smart-home", "esp32", "fastapi", "whisper", "porcupine"]
categories: ["smart-home"]
description: "기존 Voice IoT Controller v0.7 (PIR 보안모드 완료) 기반으로 ESP32-CAM UDP 스트림을 활용한 현관 AI 보안 카메라 시스템을 신규 구현. **기존 시스템 스택**"
---

# Voice IoT Controller — 개발 일지
## 작업일: 2026-02-24
## 주제: ESP32-CAM 현관 보안 카메라 시스템 전체 구현

---

## 1. 작업 배경

기존 Voice IoT Controller v0.7 (PIR 보안모드 완료) 기반으로
ESP32-CAM UDP 스트림을 활용한 현관 AI 보안 카메라 시스템을 신규 구현.

**기존 시스템 스택**
- STT: faster-whisper small / 웨이크워드: Porcupine "자비스야"
- LLM: Ollama qwen2.5:7b
- TTS: edge-tts ko-KR-SunHiNeural
- 백엔드: FastAPI + WebSocket + TCP
- 디바이스: ESP32 (차고/욕실/침실/현관)
- 보안: PIR HC-SR501 기반 4모드 (외출/귀가/취침/기상)

---

## 2. 구현 목표

```
ESP32-CAM (현관) → UDP → Python 서버
  → InsightFace 얼굴인식 + YOLOv8 감지
  → 판정: known / delivery / intruder / clear
  → WebSocket → 웹앱 실시간 알람 + 영상
```

**알람 방식**
- `known`    : ✅ 초록 배지 + 로그
- `delivery` : 📦 CCTV 모달 + 짧은 비프음
- `intruder` : 🚨 전체 알람 모달 + 경보음(Web Audio) + TTS 음성

---

## 3. 구현 완료 파일

| 파일 | 버전 | 내용 |
|------|------|------|
| `server/camera_stream.py` | v1.0 | UDP 수신(단순/멀티파트) + MJPEG 스트리밍 |
| `server/frame_analyzer.py` | v1.0 | InsightFace buffalo_sc + YOLOv8n 통합 분석 |
| `server/face_db.py` | v1.0 | 얼굴 DB REST API (등록/삭제/재빌드) |
| `server/main.py` | v0.8 | 카메라 시스템 통합, 라우터 등록 |
| `config/settings.yaml` | v1.1 | camera 블록 추가, esp32_entrance cam 캡스 |
| `web/index.html` | v0.8 | 현관 카메라 카드 + 침입 알람 모달 통합 |
| `esp32/esp_cam_entrance.ino` | v1.1 | ESP32-CAM UDP 펌웨어 (메모리 버그 수정) |

---

## 4. 신규 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/camera/entrance/stream` | MJPEG HTTP 스트림 |
| GET | `/camera/entrance/snapshot` | 스냅샷 JPEG 1장 |
| GET | `/camera/entrance/status` | 카메라 + 판정 상태 JSON |
| GET | `/face-db/list` | 등록 인물 목록 |
| POST | `/face-db/register` | 얼굴 사진 등록 (multipart) |
| DELETE | `/face-db/{name}` | 인물 삭제 |
| POST | `/face-db/rebuild` | 인코딩 캐시 재빌드 |

**신규 WebSocket 메시지 타입**

| 타입 | 방향 | 내용 |
|------|------|------|
| `cam_alert` | 서버→클라이언트 | intruder / delivery 감지 알람 |
| `cam_notify` | 서버→클라이언트 | known (등록 얼굴) 귀가 알림 |

---

## 5. 트러블슈팅 기록

### 5-1. `python-multipart` 누락 오류
**증상**
```
RuntimeError: Form data requires "python-multipart" to be installed.
```
**원인** `face_db.py` `/register` 엔드포인트가 `Form + UploadFile` 사용.
앱 기동 시 라우터 등록 단계에서 즉시 체크 → 서버 자체가 뜨지 않음.

**해결**
```bash
pip install python-multipart
echo "python-multipart" >> requirements.txt
```

---

### 5-2. ESP32-CAM 카메라 초기화 실패
**증상**
```
E (4488) cam_hal: cam_dma_config(301): frame buffer malloc failed
E (4488) camera: Camera config failed with error 0xffffffff
```
**원인** DMA 메모리 할당 실패. 3가지 복합 원인:
1. PSRAM 미감지 상태에서 VGA 해상도 시도 → 메모리 부족
2. `fb_count=2` → DMA 버퍼 2배 필요
3. `grab_mode` 미설정 → 내부 버퍼 관리 오류

**해결** 펌웨어 v1.0 → v1.1 수정
```cpp
// 핵심 3가지 수정
config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;  // 신규 추가
config.fb_count  = 1;                        // 2 → 1 고정
// PSRAM 없으면 QQVGA 강제
if (!hasPsram) config.frame_size = FRAMESIZE_QQVGA;
```
추가로 해상도 단계적 fallback (SVGA→QVGA→96x96) 및 3회 재시도 로직 구현.

**결과**
```
[CAM] PSRAM 감지: ❌ 없음
[CAM] 모드: DRAM → QQVGA(160x120) q=20
[CAM] ✅ 초기화 완료 — Heap여유: 211868 bytes
[UDP] 서버: 192.168.0.154:5005
[CAM] 프레임 1000 | 크기: 1644 bytes | Heap: 160664  ← 안정적
```

---

## 6. 시스템 최종 구성

### 하드웨어
```
ESP32-CAM (AI Thinker OV2640)
  IP  : 192.168.0.19
  해상도: QQVGA 160x120 (PSRAM 없음, DRAM 모드)
  FPS : ~6fps (FRAME_INTERVAL_MS=150)
  UDP : 192.168.0.154:5005 전송
  Heap: 156~161KB 안정 유지 (누수 없음)
```

### 소프트웨어 파이프라인
```
ESP32-CAM
  → UDP JPEG (~1,300~1,700 bytes/frame)
  → camera_stream.py (UDP 수신 스레드)
  → frame_analyzer.py (매 10프레임 분석)
      ├── YOLOv8n : person / suitcase / handbag 감지
      └── InsightFace buffalo_sc : 얼굴 임베딩 + cosine 매칭
  → verdict (known / delivery / intruder / clear)
  → WebSocket broadcast → index.html
      ├── intruder : 🚨 알람 모달 + Web Audio 경보음 + TTS
      ├── delivery : 📦 CCTV 모달 + 비프음
      └── known    : ✅ 초록 배지 + 로그
```

### 판정 우선순위
```
1. 등록 얼굴 매칭 (cosine dist < 0.45) → known
2. YOLO suitcase/handbag 감지          → delivery
3. person 감지 + 미등록 얼굴           → intruder
4. person 없음                         → clear
```

### 알람 쿨다운
- intruder : 30초
- delivery : 60초

---

## 7. 웹앱 UI 변경사항 (index.html v0.8)

### 추가된 CSS
- `.cam-stream-wrap` — 4:3 비율 스트림 컨테이너
- `.cam-verdict-badge` — known/delivery/intruder 판정 오버레이 배지
- `.cam-dot` — 상태 표시 도트 (초록/빨강/회색)
- `.cam-alert-overlay` / `.cam-alert-box` — 침입 알람 모달 전체 스타일
- `.cam-btn-snapshot`, `.cam-btn-confirm` 등 버튼 스타일

### 추가된 HTML
- `#card-cam` 현관 카메라 카드 (PIR 카드 다음)
  - ▶ 스트림 시작 / ■ 스트림 중지 토글 버튼
  - 📸 스냅샷 다운로드 버튼
  - 판정 배지 오버레이 + LIVE 표시
  - 마지막 이벤트 표시
- `#camAlertModal` ESP32-CAM 침입 알람 모달
  - 스냅샷 자동 로드
  - 신뢰도 표시
  - 확인/닫기 버튼

### 추가된 JS 함수
| 함수 | 역할 |
|------|------|
| `camToggleStream()` | 스트림 시작/중지 토글 |
| `onCamLoad()` | 스트림 연결 성공 처리 |
| `onCamError()` | 스트림 오류 + 5초 재시도 |
| `camSnapshot()` | 스냅샷 JPEG 다운로드 |
| `updateCamBadge()` | 판정 배지 업데이트 |
| `handleCamAlert()` | cam_alert WS 메시지 처리 |
| `handleCamNotify()` | cam_notify WS 메시지 처리 |
| `camAlertConfirm()` | 알람 해제 + 알람음 중지 |
| `startCamAlarm()` | Web Audio 경보음 시작 |
| `stopCamAlarm()` | 경보음 중지 |
| `playDeliveryBeep()` | 택배 단음 비프 |

### 수정된 항목
- 기존 CCTV 모달 스트림 URL: `/camera/stream` → `/camera/entrance/snapshot`
- `handleServerMsg()` 에 `cam_alert` / `cam_notify` 분기 추가

---

## 8. settings.yaml v1.1 변경사항

### 신규 `camera` 블록
```yaml
camera:
  udp_port: 5005
  multipart: false
  analyze_every: 10
  stream_fps: 15
  jpeg_quality: 80
  face_threshold: 0.45      # 현장 조명에 따라 0.40~0.50 튜닝
  yolo_conf: 0.50
  yolo_model: "yolov8n.pt"
  face_model: "buffalo_sc"
  cooldown_intruder: 30
  cooldown_delivery: 60
  face_db_dir: "face_db/known"
  encodings_cache: "face_db/encodings.pkl"
  cam_cmd_port: 5006
```

### `esp32_entrance` 수정
```yaml
caps: ["led", "servo", "cam"]   # cam 추가
cam:
  device: "ESP32-CAM (AI Thinker OV2640)"
  udp_port: 5005
  resolution: "QQVGA"
  fps: 10
  flash_gpio: 4
```

### `state_polling` 블록 신규 추가
```yaml
state_polling:
  interval: 30
```

---

## 9. 설치 패키지

```bash
pip install opencv-python-headless ultralytics insightface onnxruntime
pip install python-multipart   # face_db /register Form 처리용

# requirements.txt에 추가
opencv-python-headless>=4.9.0
ultralytics>=8.1.0
insightface>=0.7.3
onnxruntime>=1.17.0
python-multipart
```

---

## 10. 환경변수 플래그

```bash
# 카메라 없이 기존처럼 실행
DISABLE_CAM=1 ./run_server.sh

# 전체 실행 (카메라 포함)
./run_server.sh
```

---

## 11. PENDING 작업

- [ ] 얼굴 DB 등록 (face_db/known/stephen/ 에 사진 3~5장 추가)
- [ ] InsightFace threshold 현장 튜닝 (현재 0.45, 조명에 따라 조정)
- [ ] YOLOv8 택배 감지 정확도 검증 (기본 COCO: suitcase/handbag)
- [ ] ESP32-CAM 해상도 업그레이드 검토 (PSRAM 모듈 추가 시 QVGA→VGA)
- [ ] Telegram 침입 사진 전송 연동 (중장기)
- [ ] 야간 모드: 조도 기반 플래시 LED 자동 점등
- [ ] `gui/dashboard.py` (PyQt6) 카메라 뷰 연동 검토
- [ ] `pipeline_metrics.csv` 에 frame_analyzer 분석 시간 기록 연동

---

## 12. 실행 확인 체크리스트

```
✅ python-multipart 설치
✅ ESP32-CAM 펌웨어 v1.1 업로드
✅ Wi-Fi 연결 (192.168.0.19)
✅ UDP 전송 (192.168.0.154:5005)
✅ 프레임 전송 안정 (1,250+ 프레임, Heap 안정)
✅ 서버 UDP 수신 시작
✅ YOLOv8n 로드 완료
✅ InsightFace 로드 완료
✅ analysis_loop task 시작
✅ WebSocket 연결 (ws_client_0001)
⬜ 얼굴 DB 등록 (0명 → stephen 등록 필요)
⬜ 웹앱 스트림 실시간 확인
⬜ 침입 알람 E2E 테스트
```

---

## 13. 추가 트러블슈팅 (오후 작업)

### 13-1. 웹앱 현관 카메라 카드 — 검은 화면 문제

**증상**
- 웹앱 카메라 카드에서 ▶ 스트림 시작 눌러도 검은 화면
- `/camera/entrance/stream` 새 탭에서도 페이지 안 열림
- `/camera/entrance/status` → `active: true` (서버는 정상 수신 중)

**tcpdump 확인 결과**
```
15:23:37 wlp4s0 In  IP 192.168.0.19.5006 > pc.5005: UDP, length 1460
15:23:55 wlp4s0 In  IP 192.168.0.19.5006 > pc.5005: UDP, length 1460
15:25:19 wlp4s0 In  IP 192.168.0.19.5006 > pc.5005: UDP, length 1460
```

**원인 분석**
QVGA(320x240) JPEG 크기 ~3,000+ bytes → UDP MTU(1500) 초과로 **2개 패킷 분할 전송**.
기존 `_udp_simple_receiver()`는 SOI(`\xff\xd8`)로 시작하는 **첫 번째 패킷만 저장**하고
두 번째 조각(EOI 포함)을 버렸음 → 불완전 JPEG → cv2.imdecode 실패 → 검은 화면.

**해결: `camera_stream.py` `_udp_simple_receiver()` SOI/EOI 자동 조립으로 교체**

```python
# 수정 핵심 로직
# 1. SOI(\xff\xd8) + EOI(\xff\xd9) 모두 있으면 → 단일 완전 JPEG, 바로 사용
# 2. SOI만 있으면 → frame_buf 에 누적 시작
# 3. 중간 패킷 → frame_buf 에 append
# 4. EOI 확인 시 → 조립 완료, _latest_frame 업데이트
# 5. 0.5초 타임아웃 → 손상 프레임 자동 폐기 + 버퍼 초기화
```

추가 개선:
- `SO_RCVBUF = 1MB` 소켓 수신 버퍼 확대
- 분할 패킷 조립 타임아웃 0.5초

---

### 13-2. 화면 거꾸로 + 프레임 끊김 문제

**증상**
- 화면이 상하 반전으로 출력됨
- 프레임이 자주 끊김 (6fps 미만)

**원인**
- `vflip=0` (정방향) → ESP32-CAM 현관 설치 방향 거꾸로
- QQVGA(160x120) 해상도 너무 작아 JPEG 품질 불안정
- `STREAM_FPS_LIMIT=15` 서버 전송 속도가 수신 속도보다 빠름
- `FRAME_QUEUE_SIZE=5` 버퍼 부족

**해결: 펌웨어 + 서버 동시 수정**

`esp_cam_entrance.ino` v1.1 → v1.2:
```cpp
config.frame_size   = FRAMESIZE_QVGA;   // QQVGA → QVGA (320x240)
config.jpeg_quality = 12;               // 20 → 12 (더 선명)
FRAME_INTERVAL_MS   = 100;              // 150ms → 100ms (~10fps)
s->set_vflip(s, 1);                     // 0 → 1 (상하 반전 ON)
```

`camera_stream.py` v1.1:
```python
FRAME_QUEUE_SIZE = 10    # 5 → 10 (버퍼 여유)
STREAM_FPS_LIMIT = 10    # 15 → 10 (끊김 방지)
JPEG_QUALITY     = 70    # 80 → 70 (전송량 감소)
# mjpeg_generator: 동일 프레임 재전송 스킵 (last_sent)
# placeholder: 1초 쓰로틀 (매 프레임 전송 방지)
```

---

## 14. 최종 수정 파일 목록 (오후)

| 파일 | 버전 | 주요 수정 |
|------|------|----------|
| `server/camera_stream.py` | v1.1 | SOI/EOI 자동 조립, FPS/품질 최적화, 중복 프레임 스킵 |
| `esp32/esp_cam_entrance.ino` | v1.2 | vflip=1, QVGA, q=12, 100ms 간격 |
| `web/index.html` | v0.8 | 현관 카메라 카드 + 침입 알람 모달 통합 |
| `config/settings.yaml` | v1.1 | camera 블록 추가 |
| `server/main.py` | v0.8 | 카메라 라우터 + 엔드포인트 통합 |

---

## 15. 현재 상태 (2026-02-24 15:30 기준)

```
✅ ESP32-CAM 펌웨어 v1.1 업로드 완료
✅ Wi-Fi 연결 (192.168.0.19)
✅ UDP 패킷 전송 확인 (tcpdump)
✅ 서버 active:true (프레임 수신 중)
✅ python-multipart 설치 완료
✅ YOLOv8n + InsightFace 로드 완료
✅ 웹앱 카메라 카드 UI 통합
⬜ camera_stream.py v1.1 적용 (SOI/EOI 조립) → 재시작 필요
⬜ esp_cam_entrance.ino v1.2 업로드 (vflip=1) → 재업로드 필요
⬜ 영상 정상 출력 최종 확인
⬜ 얼굴 DB 등록 (face_db/known/stephen/)
⬜ 침입 감지 E2E 테스트
```
