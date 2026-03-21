---
title: "Voice IoT Controller — 전체 작업 진행 내역"
date: 2026-03-21
draft: true
tags: ["smart-home", "esp32"]
categories: ["smart-home"]
description: "| 구분 | 내용 | |------|------| | 오전 세션 | ESP32-CAM 현관 보안 카메라 시스템 신규 구현 |"
---

# Voice IoT Controller — 전체 작업 진행 내역
## 작업일: 2026-02-24
## 프로젝트 경로: ~/dev_ws/voice_iot_controller/

---

## 1. 작업 개요

| 구분 | 내용 |
|------|------|
| 오전 세션 | ESP32-CAM 현관 보안 카메라 시스템 신규 구현 |
| 오후 세션 | UDP 스트림 연결 불가 원인 추적 및 완전 해결 |
| 최종 상태 | 영상 출력 정상, CLEAR 판정 동작 확인 |

---

## 2. 오전 세션 — ESP32-CAM 보안 카메라 시스템 구현

### 2-1. 구현 목표

```
ESP32-CAM (현관) → UDP → Python 서버
  → InsightFace 얼굴인식 + YOLOv8 감지
  → 판정: known / delivery / intruder / clear
  → WebSocket → 웹앱 실시간 알람 + 영상
```

### 2-2. 구현 완료 파일

| 파일 | 버전 | 내용 |
|------|------|------|
| `server/camera_stream.py` | v1.1 | UDP 수신 + SOI/EOI 자동 조립 + MJPEG 스트리밍 |
| `server/frame_analyzer.py` | v1.0 | InsightFace buffalo_sc + YOLOv8n 통합 분석 |
| `server/face_db.py` | v1.0 | 얼굴 DB REST API (등록/삭제/재빌드) |
| `server/main.py` | v0.8 | 카메라 시스템 통합, 라우터 등록 |
| `config/settings.yaml` | v1.1 | camera 블록 추가 |
| `web/index.html` | v0.8 | 현관 카메라 카드 + 침입 알람 모달 통합 |
| `esp32/esp_cam_entrance.ino` | v1.2 | ESP32-CAM UDP 펌웨어 (vflip=1, QVGA) |

### 2-3. 신규 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/camera/entrance/stream` | MJPEG HTTP 스트림 |
| GET | `/camera/entrance/snapshot` | 스냅샷 JPEG 1장 |
| GET | `/camera/entrance/status` | 카메라 + 판정 상태 JSON |
| GET | `/face-db/list` | 등록 인물 목록 |
| POST | `/face-db/register` | 얼굴 사진 등록 (multipart) |
| DELETE | `/face-db/{name}` | 인물 삭제 |
| POST | `/face-db/rebuild` | 인코딩 캐시 재빌드 |

### 2-4. 오전 트러블슈팅

#### python-multipart 누락
```bash
pip install python-multipart
echo "python-multipart" >> requirements.txt
```

#### ESP32-CAM DMA 메모리 할당 실패
```cpp
// v1.1 핵심 수정
config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
config.fb_count  = 1;
// PSRAM 없으면 QVGA 강제 (320x240)
```

#### 화면 거꾸로 + 프레임 끊김
```cpp
// v1.2 수정
s->set_vflip(s, 1);              // 상하 반전 ON
config.frame_size = FRAMESIZE_QVGA;
config.jpeg_quality = 12;
FRAME_INTERVAL_MS = 100;         // ~10fps
```

---

## 3. 오후 세션 — UDP 스트림 연결 불가 디버깅

### 3-1. 증상

```
- 웹앱 카메라 카드: "Connecting... UDP :5005" 에서 멈춤
- curl /camera/entrance/status → {"active": false}
- ESP32-CAM 시리얼: 프레임 정상 전송 중
- tcpdump: 패킷 없음
```

### 3-2. 디버깅 과정 (단계별)

| 단계 | 확인 내용 | 결과 |
|------|----------|------|
| 1 | 포트 5005 점유 확인 (`lsof -iUDP:5005`) | uvicorn 정상 점유 ✅ |
| 2 | FrameAnalyzer import 확인 | OK ✅ |
| 3 | 서버 재시작 + CAM 로그 확인 | 서버 정상 기동, active:false 유지 |
| 4 | camera_stream.py v1.2 디버그 로그 추가 | timeout — 수신 패킷 누적: 0개 확인 |
| 5 | PC IP 확인 (`ip addr`) | 192.168.0.154 정상 ✅ |
| 6 | Python UDP 수신 테스트 | OSError: Address already in use → 서버가 이미 점유 중 |
| 7 | ESP32-CAM ping 테스트 | 지연 953ms ~ 16,000ms, 패킷 손실 심각 ❌ |

### 3-3. 원인 파악

**근본 원인: ESP32 WiFi 절전모드 기본값 ON**

- PC USB 전원(500mA 제한) + WiFi 절전모드 ON
- UDP 전송 중 간헐적 WiFi 슬립 발생
- ping 지연 최대 16초, 패킷 대량 손실
- UDP 패킷이 PC에 전혀 도달하지 않음

### 3-4. 해결 — esp_cam_entrance.ino v1.2 → v1.3

```cpp
// connectWiFi() 내 WiFi 연결 완료 직후 2줄 추가
WiFi.setSleep(false);                   // 절전모드 OFF ← 핵심
WiFi.setTxPower(WIFI_POWER_19_5dBm);    // 최대 출력 고정
```

**적용 후 시리얼 로그:**
```
[WiFi] ✅ 연결 완료 — IP: 192.168.0.19
[WiFi] 절전모드: OFF | TxPower: 19.5dBm
```

**적용 후 서버 로그:**
```
[CameraStream][DBG] 패킷#2400 from ('192.168.0.19', 5006) | 크기=1460B | 시작=ffd8 끝=00a4
```

### 3-5. 최종 결과

```
✅ UDP 패킷 수신 정상
✅ 웹앱 영상 출력 정상
✅ CLEAR 판정 오버레이 정상
✅ 타임스탬프 표시 정상
```

---

## 4. 최종 수정 파일 목록

| 파일 | 최종 버전 | 주요 변경 |
|------|----------|----------|
| `server/camera_stream.py` | v1.2 | SOI/EOI 자동 조립 + 디버그 로그 추가 |
| `server/frame_analyzer.py` | v1.0 | InsightFace + YOLOv8n 통합 |
| `server/face_db.py` | v1.0 | 얼굴 DB REST API |
| `server/main.py` | v0.8 | 카메라 라우터 통합 |
| `config/settings.yaml` | v1.1 | camera 블록 추가 |
| `web/index.html` | v0.8 | 현관 카메라 카드 + 알람 모달 |
| `esp32/esp_cam_entrance.ino` | v1.3 | WiFi.setSleep(false) + setTxPower 추가 |

---

## 5. 문서 산출물

| 파일 | 내용 |
|------|------|
| `docs/dev_log_2026-02-24_espcam_security.md` | 오전 구현 전체 기록 |
| `docs/dev_log_2026-02-24_espcam_debug.md` | 오후 디버깅 기록 |
| `docs/얼굴_인식_알고리즘.md` | InsightFace + ArcFace 알고리즘 상세 설명 |

---

## 6. 시스템 최종 구성

### 하드웨어
```
ESP32-CAM (AI Thinker OV2640)
  IP        : 192.168.0.19
  해상도    : QVGA 320x240 (PSRAM 없음, DRAM 모드)
  FPS       : ~10fps (FRAME_INTERVAL_MS=100)
  UDP 전송  : 192.168.0.154:5005
  WiFi 절전 : OFF (v1.3 수정)
  Heap      : 146~165KB 안정 유지
```

### 소프트웨어 파이프라인
```
ESP32-CAM
  → UDP JPEG (~3,800~3,970 bytes/frame, MTU 분할)
  → camera_stream.py v1.2 (SOI/EOI 자동 조립)
  → frame_analyzer.py (매 10프레임 분석)
      ├── YOLOv8n      : person / suitcase / handbag 감지
      └── InsightFace  : 얼굴 임베딩 + cosine 매칭 (threshold=0.45)
  → verdict → WebSocket → index.html
      ├── known    : ✅ 초록 배지 + 로그
      ├── delivery : 📦 CCTV 모달 + 비프음 (쿨다운 60초)
      └── intruder : 🚨 알람 모달 + 경보음 + TTS (쿨다운 30초)
```

---

## 7. 트러블슈팅 핵심 노트

| 문제 | 원인 | 해결 |
|------|------|------|
| UDP 패킷 미수신 | ESP32 WiFi 절전모드 ON (기본값) | `WiFi.setSleep(false)` |
| ping 지연 14~16초 | PC USB 전원 부족 + 절전모드 | `WiFi.setTxPower(WIFI_POWER_19_5dBm)` |
| 검은 화면 (SOI/EOI) | QVGA ~3,900 bytes → MTU 분할, 첫 패킷만 처리 | SOI/EOI 자동 조립 로직 |
| DMA 메모리 실패 | PSRAM 없이 VGA 시도, fb_count=2 | QVGA 강제 + fb_count=1 |
| python-multipart | face_db /register Form 처리 | `pip install python-multipart` |

---

## 8. PENDING 작업

- [ ] **얼굴 DB 등록** — `face_db/known/stephen/` 사진 3~5장
- [ ] **침입 감지 E2E 테스트** — intruder / delivery 알람 실제 트리거
- [ ] **camera_stream.py 디버그 로그 정리** — WARNING → DEBUG 레벨로 변경 (v1.3)
- [ ] **InsightFace threshold 현장 튜닝** — 현재 0.45, 조명에 따라 조정
- [ ] **ESP32-CAM 전원 교체** — 5V 2A 어댑터 (안정적 전원 공급)
- [ ] **YOLOv8 택배 감지 정확도 검증** — suitcase/handbag 실제 테스트
- [ ] **Telegram 침입 사진 전송 연동** (중장기)
- [ ] **야간 모드** — 조도 기반 플래시 LED 자동 점등
- [ ] **gui/dashboard.py PyQt6 카메라 뷰 연동** 검토

---

## 9. 현재 상태 (2026-02-24 작업 종료 기준)

```
✅ ESP32-CAM 펌웨어 v1.3 업로드 완료
✅ WiFi 절전모드 OFF 적용
✅ UDP 패킷 수신 정상 (192.168.0.19 → 192.168.0.154:5005)
✅ SOI/EOI 자동 조립 정상
✅ YOLOv8n + InsightFace 모델 로드 완료
✅ 웹앱 현관 카메라 카드 영상 출력 정상
✅ CLEAR 판정 오버레이 정상
✅ WebSocket 연결 정상
⬜ 얼굴 DB 등록 (0명 → stephen 등록 필요)
⬜ 침입 감지 E2E 테스트
⬜ 디버그 로그 정리 (camera_stream.py v1.3)
```
