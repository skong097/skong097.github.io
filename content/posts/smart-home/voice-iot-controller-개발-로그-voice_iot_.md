---
title: "Voice IoT Controller — 개발 로그"
date: 2026-03-21
draft: true
tags: ["smart-home", "esp32"]
categories: ["smart-home"]
description: "**날짜:** 2026-02-22 **작업자:** Stephen Kong **세션:** 단일 ESP32 통합 전환 + 서버 측 전면 수정"
---

# Voice IoT Controller — 개발 로그
**날짜:** 2026-02-22  
**작업자:** Stephen Kong  
**세션:** 단일 ESP32 통합 전환 + 서버 측 전면 수정

---

## 📌 오늘 작업 요약

| 구분 | 내용 |
|------|------|
| 주요 변경 | ESP32 5개 → 1개 통합 (esp32_home) |
| 영향 파일 | esp32_client.ino / schema.py / tcp_server.py / command_router.py / llm_engine.py |
| 문서 업데이트 | ESP32_UPLOAD_GUIDE.md (v3) / README.md |

---

## 1. 하드웨어 결정 사항

### 7세그먼트 디스플레이 확정
- **이전:** DS18B20(온도 센서) + 4-Digit 7-Segment LED Display (12-pin 단품)
- **변경:** TM1637 모듈로 교체 확정
- **이유:** 12핀 단품은 드라이버 IC 없이 직결 불가 (GPIO 12핀 필요), TM1637은 2핀(CLK/DIO)으로 제어 가능
- **배선:** VCC=5V 필수, CLK=GPIO22, DIO=GPIO23 (3.3V 신호선 직결 가능)

### 센서 제거 결정
- DHT22 (침실 온습도) 제거
- DS18B20 (욕실 온도) 제거
- 현재 구성에서 자동 센서 폴링 없음

### ESP32 단일화 결정
- **이전:** ESP32 5개 (유닛별 개별 연결)
- **변경:** ESP32 1개로 5개 공간 전체 제어
- **배경:** 테스트 및 배선 단순화, 개발 단계 효율성

---

## 2. 최종 핀 배정 (esp32_home)

### LED (공간별 GPIO)

| 공간 | room 값 | GPIO |
|------|---------|------|
| 거실 | living | 2 |
| 욕실 | bathroom | 4 |
| 침실 | bedroom | 5 |
| 차고 | garage | 12 |
| 현관 | entrance | 13 |

### 서보 (공간별 GPIO)

| 공간 | room 값 | GPIO | 용도 |
|------|---------|------|------|
| 침실 | bedroom | 14 | 커튼 (0°=닫힘 / 90°=열림) |
| 차고 | garage | 15 | 차고문 (0°=닫힘 / 90°=열림) |
| 현관 | entrance | 16 | 현관문 (0°=닫힘 / 90°=열림) |

### TM1637 7세그먼트 (욕실)

| 핀 | GPIO |
|----|------|
| CLK | 22 |
| DIO | 23 |
| VCC | 5V (필수) |
| GND | GND |

### 사용 안전 GPIO 확인

| GPIO | 용도 | 안전 여부 |
|------|------|-----------|
| 2 | LED 거실 | ✅ (부팅 시 일시 LOW) |
| 4 | LED 욕실 | ✅ |
| 5 | LED 침실 | ✅ |
| 12 | LED 차고 | ✅ |
| 13 | LED 현관 | ✅ |
| 14 | Servo 침실 | ✅ |
| 15 | Servo 차고 | ✅ |
| 16 | Servo 현관 | ✅ |
| 22 | SEG7 CLK | ✅ |
| 23 | SEG7 DIO | ✅ |
| 6~11 | Flash 내부 | ❌ 사용 금지 |
| 34~39 | 입력 전용 | ❌ 출력 불가 |

---

## 3. 펌웨어 수정 (esp32_client.ino)

### 변경 전 (다중 유닛)
```cpp
#define DEVICE_UNIT  UNIT_BEDROOM  // ← 유닛별 변경 후 5번 업로드
```
- UNIT_GARAGE / UNIT_BATHROOM / UNIT_BEDROOM / UNIT_ENTRANCE / UNIT_LIVING
- 각 유닛마다 device_id 별도 등록
- DHT22, DS18B20 포함

### 변경 후 (단일 통합)
```cpp
// Config 한 번만 설정 → 업로드 1회
#define WIFI_SSID      "your_ssid"
#define WIFI_PASSWORD  "your_password"
#define SERVER_IP      "192.168.1.100"
#define DEVICE_ID      "esp32_home"
#define CAPS_STR       "[\"led\",\"servo\",\"seg7\"]"
```

### 주요 변경 내용
- `DEVICE_UNIT` 선택 매크로 → 단일 `DEVICE_ID = "esp32_home"`
- 라이브러리: DHT, OneWire, DallasTemperature 제거
- 핀 정의: PIN_DHT, PIN_DS18B20 제거
- `sendSensorData()` 빈 함수로 단순화
- `processCommand()`: `room` 필드로 공간 구분 → `resolveLedPin()` / `resolveServo()`
- `sendRegister()`: caps = `["led","servo","seg7"]` 고정

### 명령 처리 방식 변경
```
이전: {"cmd":"led","pin":2,"state":"on"}
      → 어느 ESP32로 보내느냐로 공간 구분

변경: {"cmd":"led","room":"bedroom","state":"on"}
      → room 필드로 공간 구분 → 핀 자동 결정
```

---

## 4. 서버 수정

### 4-1. schema.py

**추가 상수:**
```python
DEVICE_HOME = "esp32_home"           # 단일 통합 디바이스

ROOM_LED_PIN   = {"living":2, "bathroom":4, "bedroom":5, "garage":12, "entrance":13}
ROOM_SERVO_PIN = {"living":None, "bathroom":None, "bedroom":14, "garage":15, "entrance":16}
ROOM_LABEL     = {"living":"거실", "bathroom":"욕실", "bedroom":"침실", "garage":"차고", "entrance":"현관"}
ALL_ROOMS      = ("living","bathroom","bedroom","garage","entrance")
```

**validate_command() 변경:**
- room 필드 있으면 pin 없어도 통과
- room 값이 ALL_ROOMS에 없으면 오류

**cmd_led(), cmd_servo() 변경:**
- room 파라미터 추가
- to_bytes(): room="" 이면 TCP 전송 시 제외

### 4-2. tcp_server.py

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| DEVICE_LABEL | 5개 공간별 | esp32_home 단일 |
| SENSOR_CAP_MAP | dht22/ds18b20 매핑 | 빈 딕셔너리 |
| register() | LED/서보/센서 초기값 | room별 GPIO 키로 초기화 |
| update_command() | pin 직접 사용 | room → pin 자동 결정 |
| _on_sensor() | DEVICE_BEDROOM 자동 seg7 | 단순화 |
| _auto_seg7() | 존재 | 제거 |

### 4-3. command_router.py

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| _resolve_device() | device_id / keyword_map 조회 | 항상 esp32_home 반환 |
| _build_payload() | pin 직접 사용 | room → ROOM_LED_PIN/SERVO_PIN |
| _handle_status() | esp32_* 키 기반 | room 키 기반 상태 분리 |
| _build_status_sentence() | esp32_* ROOM_ORDER | room 문자열 ROOM_ORDER |
| _simple_parse() | device_id + pin | esp32_home + room |
| execute() 낙관적 업데이트 | pin 하드코딩 | room 기반 핀 결정 |

### 4-4. llm_engine.py (SYSTEM_PROMPT)

**변경 전:**
```
Available devices:
  - esp32_garage, esp32_bathroom, esp32_bedroom, esp32_entrance, living_room
Commands: {"cmd":"led","device_id":"esp32_bedroom","pin":2,"state":"on"}
```

**변경 후:**
```
System: Single ESP32 (device_id: "esp32_home") + room field
Commands: {"cmd":"led","device_id":"esp32_home","room":"bedroom","state":"on"}
```

---

## 5. 명령 흐름 변경

### LED 제어
```
이전: "침실 불 켜줘" → LLM → {cmd:led, device_id:esp32_bedroom, pin:2, state:on}
                              → TCP to esp32_bedroom

변경: "침실 불 켜줘" → LLM → {cmd:led, device_id:esp32_home, room:bedroom, state:on}
                              → _build_payload() → pin=5 (ROOM_LED_PIN[bedroom])
                              → TCP to esp32_home: {cmd:led, pin:5, room:bedroom, state:on}
```

### 전체 LED 제어
```
"전체 불 꺼줘" → {cmd:led, device_id:all, state:off}
              → broadcast_command() → esp32_home에 전송 (device_id=all 처리)
```

### 서보 제어
```
"차고문 열어줘" → {cmd:servo, device_id:esp32_home, room:garage, angle:90}
               → _build_payload() → pin=15 (ROOM_SERVO_PIN[garage])
               → TCP: {cmd:servo, pin:15, room:garage, angle:90}
```

---

## 6. 빵판 배선 (현재 테스트 상태)

```
ESP32 1개 테스트 중
GPIO 2 → 저항(330Ω) → LED (+극 긴다리) → GND
```

- 테스트 완료 후 나머지 GPIO(4,5,12,13) 순차 추가 예정
- 서보: 외부 5V 전원 필요 (대형 서보 토크 문제)
- TM1637: VCC=5V 필수 (신호선은 3.3V 직결 가능)

---

## 7. 파일 버전 현황

| 파일 | 버전 | 주요 변경 |
|------|------|-----------|
| esp32_client.ino | 통합 v1.0 | 단일 esp32_home, room 기반 제어 |
| schema.py | v2.0 | DEVICE_HOME, ROOM_LED_PIN, ROOM_SERVO_PIN 추가 |
| tcp_server.py | v3.1 | room 기반 상태 초기화, _auto_seg7 제거 |
| command_router.py | v1.8 | room 기반 전면 수정 |
| llm_engine.py | v1.4 | SYSTEM_PROMPT esp32_home + room 전환 |
| ESP32_UPLOAD_GUIDE.md | v3 | TM1637 확정, 단일 통합 구성 |
| README.md | v1.7 | 디바이스 구성 반영 |

---

## 8. PENDING

- [ ] 나머지 LED 4개 빵판 연결 (GPIO 4, 5, 12, 13)
- [ ] 서보 3개 연결 테스트 (GPIO 14, 15, 16)
- [ ] TM1637 연결 테스트 (욕실 세그먼트)
- [ ] 서버 실행 후 esp32_home 등록 확인 (`caps:["led","servo","seg7"]`)
- [ ] 전체 상태 조회 음성 테스트 ("집 전체 상태 알려줘")
- [ ] STT 오인식 개선 검토 (Silero VAD 교체)

---

*Voice IoT Controller · Dev Log · 2026-02-22*
