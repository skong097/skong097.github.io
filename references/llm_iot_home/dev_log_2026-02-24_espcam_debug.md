# Voice IoT Controller — 개발 일지
## 작업일: 2026-02-24 (오후 세션)
## 주제: ESP32-CAM UDP 스트림 연결 디버깅 및 해결

---

## 1. 작업 배경

`dev_log_2026-02-24_espcam_security.md` 에서 구현 완료 후
웹앱 현관 카메라 카드에서 `Connecting... UDP :5005` 상태로 영상이 출력되지 않는 문제 발생.
오후 세션에서 원인 추적 및 완전 해결.

---

## 2. 증상

- 웹앱 카메라 카드: `Connecting...` 에서 멈춤
- `curl /camera/entrance/status` → `{"active": false}`
- `localhost:8000/camera/entrance/stream` 브라우저 직접 접근도 검은 화면
- ESP32-CAM 시리얼: 프레임 정상 전송 중 (`프레임 300 | 크기: 3844 bytes`)

---

## 3. 디버깅 과정

### Step 1 — 포트 점유 확인
```bash
sudo lsof -iUDP:5005
# → uvicorn(pid=4415) 이 5005 점유 중 → 서버 정상 기동 확인
```

### Step 2 — camera_stream.py 버전 확인
파일 내용 확인 결과 v1.0 (SOI/EOI 조립 로직 미적용) 으로 실행 중이었음.
→ v1.1 로 교체 필요 확인.

### Step 3 — FrameAnalyzer import 확인
```bash
python3 -c "from server.frame_analyzer import FrameAnalyzer; print('OK')"
# → OK (정상)
```

### Step 4 — 서버 재시작 후 CAM 로그 확인
```
[CameraStream] 시작 (mode=simple)
[CAM] UDP 수신 시작 — port=5005
[FrameAnalyzer] 모든 모델 로드 완료
[CameraStream] FrameAnalyzer 로드 완료
```
서버는 정상 기동 확인. 그러나 `active: false` 유지.

### Step 5 — camera_stream.py 디버그 로그 추가 (v1.2)
`_udp_simple_receiver()` 에 패킷 수신 로그 추가:
- timeout 시 수신 패킷 누적 카운터 출력
- 수신 패킷 크기/시작바이트/끝바이트 출력

결과: `timeout — 수신 패킷 누적: 0개` → **UDP 패킷이 PC에 전혀 도달하지 않음 확인**

### Step 6 — 네트워크 진단
```bash
ping 192.168.0.19
# → 응답 지연 953ms ~ 16,000ms, 패킷 손실 심각
```
**ESP32-CAM WiFi 연결이 매우 불안정한 상태 확인.**

### Step 7 — 원인 파악
ESP32-CAM 전원: PC USB 포트 (500mA 제한)
ESP32-CAM 카메라+WiFi 동시 동작 시 전류 소모 최대 500mA 이상 필요
→ 전원 부족으로 WiFi 불안정

추가 원인: `connectWiFi()` 에 `WiFi.setSleep(false)` 미설정
→ ESP32 기본 WiFi 절전모드 ON → UDP 전송 중 간헐적 슬립 → ping 지연 14~16초

---

## 4. 해결

### esp_cam_entrance.ino v1.1 → v1.3
`connectWiFi()` 함수 내 WiFi 연결 완료 직후 2줄 추가:

```cpp
// v1.3 핵심 수정: WiFi 절전모드 OFF + 최대 출력 고정
WiFi.setSleep(false);                   // 절전모드 OFF (ping 지연 해결)
WiFi.setTxPower(WIFI_POWER_19_5dBm);    // 최대 출력 (신호 안정화)
```

시리얼 확인 로그:
```
[WiFi] ✅ 연결 완료 — IP: 192.168.0.19
[WiFi] 절전모드: OFF | TxPower: 19.5dBm
```

업로드 후 결과:
```
[CameraStream][DBG] 패킷#2400 from ('192.168.0.19', 5006) | 크기=1460B | 시작=ffd8 끝=00a4
```
→ **UDP 패킷 수신 성공!**

---

## 5. 최종 결과

- 웹앱 현관 카메라 카드 영상 정상 출력 ✅
- `active: true` 상태 확인 ✅
- CLEAR 판정 오버레이 정상 표시 ✅
- 타임스탬프 표시 정상 ✅

---

## 6. 수정 파일 목록

| 파일 | 버전 | 주요 수정 |
|------|------|----------|
| `esp32/esp_cam_entrance.ino` | v1.3 | WiFi.setSleep(false), setTxPower 추가 |
| `server/camera_stream.py` | v1.2 | 디버그 로그 추가 (패킷 수신 확인용) |

---

## 7. 교훈 / 트러블슈팅 노트

| 항목 | 내용 |
|------|------|
| ESP32 WiFi 절전모드 | 기본값 ON → UDP 실시간 스트리밍 시 반드시 `WiFi.setSleep(false)` 설정 필요 |
| PC USB 전원 | ESP32-CAM 카메라+WiFi 동시 사용 시 500mA 부족 가능 → 5V 2A 어댑터 권장 |
| ping 지연 진단 | ESP32 WiFi 불안정 진단 시 ping 지연/손실로 먼저 확인 |
| UDP 수신 0개 | `active:false` 원인 추적 시 소켓 디버그 로그로 패킷 도달 여부 먼저 확인 |

---

## 8. PENDING 작업

- [ ] **얼굴 DB 등록** — `face_db/known/stephen/` 사진 3~5장 등록 (진행 예정)
- [ ] **camera_stream.py 디버그 로그 제거** — v1.2 → v1.3 (DEBUG 레벨로 변경)
- [ ] **침입 감지 E2E 테스트** — intruder/delivery 알람 실제 트리거 확인
- [ ] **InsightFace threshold 현장 튜닝** — 현재 0.45, 조명에 따라 조정
- [ ] **ESP32-CAM 5V 2A 어댑터 교체** — 안정적 전원 공급

---

## 9. 현재 상태 (2026-02-24 17:00 기준)

```
✅ ESP32-CAM v1.3 펌웨어 업로드 완료
✅ WiFi 절전모드 OFF 적용
✅ UDP 패킷 수신 정상
✅ 웹앱 영상 출력 정상
✅ CLEAR 판정 오버레이 정상
⬜ 얼굴 DB 등록 (stephen) — 진행 예정
⬜ 침입 감지 E2E 테스트
⬜ 디버그 로그 정리 (camera_stream.py v1.3)
```
