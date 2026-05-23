# ESP32 업로드 가이드 — Voice IoT Controller

---

## 1. 사전 준비

### Arduino IDE 설정

```
1. Arduino IDE 2.x 설치
   https://www.arduino.cc/en/software

2. ESP32 보드 패키지 설치
   File → Preferences → Additional boards manager URLs:
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

   Tools → Board → Boards Manager → "esp32" 검색 → 설치

3. 보드 선택
   Tools → Board → ESP32 Arduino → ESP32 Dev Module
```

### 라이브러리 설치 (Library Manager)

```
Tools → Manage Libraries → 아래 검색 후 설치:

  ArduinoJson          by Benoit Blanchon     (6.x)
  ESP32Servo           by Kevin Harrington
  DHT sensor library   by Adafruit
  Adafruit Unified Sensor
  OneWire              by Paul Stoffregen
  DallasTemperature    by Miles Burton
  TM1637Display        by Avishay Orpaz
```

---

## 2. 핀맵 (디바이스별)

### 공통 (전체 유닛)

| 기능 | GPIO | 설명 |
|------|------|------|
| LED | 2 | 내장 LED 겸용, 외부 LED 연결 가능 |
| 서보 | 18 | PWM 출력 |

### 차고 (esp32_garage)

```
GPIO  2  → LED       (조명)
GPIO 18  → Servo     (차고문: 0°=닫힘 / 90°=열림)
```

```
[ESP32]          [차고문 서보]
 GPIO18 ─────── Signal (주황)
 3.3V  ─────── VCC    (빨강)  ← 소형 서보만 / 대형은 외부 5V
 GND   ─────── GND    (갈색)
```

### 욕실 (esp32_bathroom)

```
GPIO  2  → LED        (조명)
GPIO 15  → DS18B20    (온도 센서, OneWire)
```

```
[ESP32]          [DS18B20]
 GPIO15 ─────── Data  (노랑)
 3.3V  ─────── VCC   (빨강)
 GND   ─────── GND   (검정)
               4.7kΩ 풀업: Data ↔ VCC 사이 필수
```

### 침실 (esp32_bedroom) — 가장 복잡한 유닛

```
GPIO  2  → LED        (조명)
GPIO 15  → DHT22      (온습도 센서)
GPIO 18  → Servo      (서보모터)
GPIO 22  → TM1637 CLK (7세그먼트)
GPIO 23  → TM1637 DIO (7세그먼트)
```

```
[ESP32]          [DHT22]
 GPIO15 ─────── Data (2번 핀)
 3.3V  ─────── VCC  (1번 핀)
 GND   ─────── GND  (4번 핀)
               10kΩ 풀업: Data ↔ VCC 사이 필수

[ESP32]          [TM1637]
 GPIO22 ─────── CLK
 GPIO23 ─────── DIO
 5V    ─────── VCC  ← 반드시 5V (3.3V 불가)
 GND   ─────── GND
```

### 현관 (esp32_entrance)

```
GPIO  2  → LED       (조명)
GPIO 18  → Servo     (현관문: 0°=닫힘 / 90°=열림)
```

---

## 3. 핀 충돌 검증

| GPIO | 차고 | 욕실 | 침실 | 현관 | 상태 |
|------|------|------|------|------|------|
| 2  | LED | LED | LED | LED | ✅ 유닛별 단일 사용 |
| 15 | - | DS18B20 | DHT22 | - | ✅ 유닛별 단일 사용 |
| 18 | Servo | - | Servo | Servo | ✅ 유닛별 단일 사용 |
| 22 | - | - | SEG7 CLK | - | ✅ 유닛별 단일 사용 |
| 23 | - | - | SEG7 DIO | - | ✅ 유닛별 단일 사용 |

> ⚠️ GPIO 6~11: 내장 Flash 전용 → 사용 금지  
> ⚠️ GPIO 34~39: 입력 전용 → 출력 불가  
> ✅ 현재 핀맵 전체 안전한 GPIO만 사용

---

## 4. esp32_client.ino 수정 방법

### Step 1 — Config 섹션 수정 (상단 40~65번 줄)

```cpp
// ── WiFi ──────────────────────────────────────────
#define WIFI_SSID       "공유기_이름"       // ← 수정
#define WIFI_PASSWORD   "공유기_비밀번호"   // ← 수정

// ── TCP 서버 ───────────────────────────────────────
#define SERVER_IP       "192.168.x.x"      // ← 서버 PC IP 수정
#define SERVER_PORT     9000

// ── 디바이스 ID ────────────────────────────────────
// 하나만 주석 해제
#define DEVICE_ID "esp32_garage"
//#define DEVICE_ID "esp32_bathroom"
//#define DEVICE_ID "esp32_bedroom"
//#define DEVICE_ID "esp32_entrance"
```

### Step 2 — 서버 PC IP 확인

```bash
# 서버 PC (Ubuntu)
ip addr show | grep "inet " | grep -v 127.0.0.1
# 예: inet 192.168.0.15/24 → SERVER_IP = "192.168.0.15"
```

### Step 3 — 업로드

```
1. USB 케이블로 ESP32 연결
2. Tools → Port → /dev/ttyUSB0 (Linux) 또는 COM3 (Windows)
3. Tools → Upload Speed → 115200
4. 업로드 버튼 (→) 클릭
5. "Connecting..." 표시 시 ESP32 BOOT 버튼 1초 누름 (보드에 따라)
```

---

## 5. 시리얼 모니터 정상 로그 확인

```
Tools → Serial Monitor → Baud Rate: 115200
```

### 차고 / 현관

```
[Boot] esp32_garage
[WiFi] 연결 중: MyWifi
[WiFi] 연결 성공: 192.168.0.21
[TCP] 서버 연결: 192.168.0.15:9000
[TCP] 연결 성공
[TCP] 등록: {"type":"register","device_id":"esp32_garage","caps":["led","servo"]}
```

### 욕실

```
[Boot] esp32_bathroom
[WiFi] 연결 성공: 192.168.0.23
[TCP] 연결 성공
[TCP] 등록: {"type":"register","device_id":"esp32_bathroom","caps":["led","temp"]}
[DS18B20] temp=23.5
```

### 침실

```
[Boot] esp32_bedroom
[WiFi] 연결 성공: 192.168.0.22
[TCP] 연결 성공
[TCP] 등록: {"type":"register","device_id":"esp32_bedroom","caps":["led","dht22","servo","seg7"]}
[DHT22] temp=24.5 humidity=58.0
[SEG7] mode=temp value=24.5
```

### 명령 수신 로그

```
[CMD] 수신: {"cmd":"led","pin":2,"state":"on"}
[LED] GPIO2 → ON
[ACK] cmd=led status=ok

[CMD] 수신: {"cmd":"servo","pin":18,"angle":90}
[SERVO] GPIO18 → 90도
[ACK] cmd=servo status=ok
```

---

## 6. 4개 유닛 업로드 체크리스트

```
□ esp32_garage 업로드
  □ DEVICE_ID = "esp32_garage" 설정
  □ WiFi / SERVER_IP 수정
  □ 업로드 완료
  □ 시리얼: TCP 등록 로그 확인
  □ 대시보드 차고 카드 → ONLINE
  □ LED ON / OFF 동작
  □ 서보 0도(닫힘) / 90도(열림) 동작

□ esp32_bathroom 업로드
  □ DEVICE_ID = "esp32_bathroom" 설정
  □ 업로드 완료
  □ 시리얼: DS18B20 온도 수신 확인
  □ 대시보드 욕실 카드 → ONLINE + 온도 표시

□ esp32_bedroom 업로드
  □ DEVICE_ID = "esp32_bedroom" 설정
  □ 업로드 완료
  □ 시리얼: DHT22 온습도 수신 확인
  □ 7세그먼트 온도 표시 확인
  □ 서보 동작 확인
  □ 대시보드 침실 카드 → ONLINE + 온습도 차트

□ esp32_entrance 업로드
  □ DEVICE_ID = "esp32_entrance" 설정
  □ 업로드 완료
  □ 시리얼: TCP 등록 로그 확인
  □ 대시보드 현관 카드 → ONLINE
  □ LED ON / OFF 동작
  □ 서보 0도(닫힘) / 90도(열림) 동작
```

---

## 7. 수동 테스트 명령 (curl)

```bash
SERVER="http://localhost:8000"

# LED ON
curl -X POST $SERVER/command \
  -H "Content-Type: application/json" \
  -d '{"cmd":"led","pin":2,"state":"on","device_id":"esp32_bedroom"}'

# 서보 열기
curl -X POST $SERVER/command \
  -H "Content-Type: application/json" \
  -d '{"cmd":"servo","pin":18,"angle":90,"device_id":"esp32_garage"}'

# 온도 즉시 조회
curl -X POST $SERVER/command \
  -H "Content-Type: application/json" \
  -d '{"cmd":"query","sensor":"dht22","device_id":"esp32_bedroom"}'

# 전체 불 끄기
curl -X POST $SERVER/command \
  -H "Content-Type: application/json" \
  -d '{"cmd":"led","pin":2,"state":"off","device_id":"all"}'

# 연결 디바이스 목록
curl $SERVER/devices
```

---

## 8. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `Connecting...` 반복 | BOOT 버튼 필요 | "Connecting..." 표시 시 BOOT 1초 누름 |
| WiFi 연결 실패 | SSID/PW 오타 또는 5GHz | SSID 재확인 (ESP32는 2.4GHz만 지원) |
| TCP 연결 실패 | SERVER_IP 오타 / 서버 미실행 | `ip addr`로 IP 확인, 서버 먼저 실행 |
| DHT22 읽기 실패 | 풀업 저항 누락 | DATA ↔ VCC 사이 10kΩ 추가 |
| DS18B20 미연결 | 풀업 저항 누락 | DATA ↔ VCC 사이 4.7kΩ 추가 |
| 7세그먼트 미표시 | VCC 3.3V | TM1637 VCC를 5V로 변경 |
| 서보 떨림 | 전원 부족 | 외부 5V 별도 공급 (ESP32 3.3V 분리) |
| 대시보드 OFFLINE | register 미수신 | 시리얼 로그 확인 후 재업로드 |

---

*Voice IoT Controller · ESP32_UPLOAD_GUIDE · 2026-02-20*
