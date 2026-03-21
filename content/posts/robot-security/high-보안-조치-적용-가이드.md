---
title: "🔴 HIGH 보안 조치 적용 가이드"
date: 2026-03-21
draft: true
tags: ["robot-security", "jwt", "hmac"]
categories: ["robot-security"]
description: "> **iot-repo-1 · Voice IoT Controller** > 작성일: 2026-03-06 | NIST SP 800-213 / OWASP IoT Top 10 기반 이 문서는 HIGH 우선순위 보안 3개 "
---

# 🔴 HIGH 보안 조치 적용 가이드

> **iot-repo-1 · Voice IoT Controller**  
> 작성일: 2026-03-06 | NIST SP 800-213 / OWASP IoT Top 10 기반

---

## 개요

이 문서는 HIGH 우선순위 보안 3개 항목의 적용 절차를 단계별로 안내합니다.  
생성된 파일 목록:

```
security_output/
├── server/
│   ├── auth.py                  ← ① FastAPI JWT 인증 모듈
│   ├── face_store.py            ← ② 얼굴 임베딩 암호화 저장
│   ├── esp32_secure.py          ← ③ TCP HMAC 서명 통신
│   └── main_auth_patch.py       ← main.py 적용 참조 예시
├── docs/
│   └── esp32_hmac_verify.cpp    ← ESP32 펌웨어 HMAC 검증 코드
└── scripts/
    └── harden_setup.sh          ← 보안 초기화 자동화 스크립트
```

---

## 사전 준비: 패키지 설치

```bash
pip install python-jose[cryptography] passlib[bcrypt] cryptography
```

---

## STEP 1 — 보안 초기화 (최초 1회)

```bash
# 프로젝트 루트에서 실행
bash scripts/harden_setup.sh
```

**실행 결과:**
- `.env` 자동 생성 (JWT_SECRET, FACE_ENC_KEY, ESP32_SECRET 랜덤 발급)
- `settings.yaml`, `face_db/` 파일 권한 강화 (`chmod 600/700`)
- `.gitignore`에 민감 파일 추가

> ⚠️ `.env`는 절대 git에 커밋하지 마세요.

---

## STEP 2 — 얼굴 임베딩 암호화 적용

**적용 대상:** `server/camera_stream.py`, `server/frame_analyzer.py`, `server/smartgate/manager.py`

### 2-1. 파일 복사

```bash
cp security_output/server/face_store.py server/face_store.py
```

### 2-2. 기존 pickle 로드 코드 교체

기존 코드 (camera_stream.py 등에서 찾아 교체):
```python
# ❌ 기존 — 평문 로드
with open("face_db/encodings.pkl", "rb") as f:
    face_db = pickle.load(f)
```

교체 코드:
```python
# ✅ 변경 — 암호화 로드
from server.face_store import load_embeddings, save_embeddings
face_db = load_embeddings()
```

저장 시:
```python
# ❌ 기존
with open("face_db/encodings.pkl", "wb") as f:
    pickle.dump(face_db, f)

# ✅ 변경
from server.face_store import save_embeddings
save_embeddings(face_db)
```

### 2-3. 환경변수 로드 후 서버 기동

```bash
export $(cat .env | grep -v '^#' | xargs)
python main.py
```

서버 최초 기동 시 기존 `encodings.pkl`이 자동으로 암호화 변환됩니다.

---

## STEP 3 — FastAPI JWT 인증 적용

### 3-1. 파일 복사

```bash
cp security_output/server/auth.py server/auth.py
```

### 3-2. main.py에 로그인 엔드포인트 추가

`main_auth_patch.py`를 참고해 `main.py`에 다음을 추가:

```python
from server.auth import verify_token, create_access_token

# 로그인 엔드포인트
@app.post("/auth/token")
async def login(username: str, password: str):
    # TODO: 실제 패스워드 해시 검증 추가
    token = create_access_token(subject=username)
    return {"access_token": token, "token_type": "bearer"}
```

### 3-3. 보호할 엔드포인트에 Depends 추가

```python
from server.auth import verify_token
from fastapi import Depends

@app.post("/command")
async def send_command(cmd: dict, user=Depends(verify_token)):
    ...

@app.post("/smartgate/arm")
async def arm_gate(user=Depends(verify_token)):
    ...

@app.post("/face/register")
async def register_face(data: dict, user=Depends(verify_token)):
    ...
```

### 3-4. 대시보드(index_dashboard.html) 토큰 주입

로그인 후 받은 JWT를 localStorage에 저장하고 모든 fetch에 헤더 추가:

```javascript
// 로그인
const res = await fetch('/auth/token?username=stephen&password=yourpw', {method:'POST'});
const { access_token } = await res.json();
localStorage.setItem('jwt', access_token);

// 이후 API 호출 시
const headers = { 'Authorization': `Bearer ${localStorage.getItem('jwt')}` };
await fetch('/command', { method: 'POST', headers, body: JSON.stringify(cmd) });

// WebSocket 연결 시
const ws = new WebSocket(`ws://서버IP:8000/ws?token=${localStorage.getItem('jwt')}`);
```

---

## STEP 4 — TCP :9000 HMAC 서명 적용

### 4-1. 파일 복사

```bash
cp security_output/server/esp32_secure.py server/esp32_secure.py
```

### 4-2. command_router.py TCP 송신 부분 교체

```python
# ❌ 기존 — 평문 TCP 전송
writer.write(json.dumps(cmd).encode() + b"\n")

# ✅ 변경 — HMAC 서명 패킷 전송
from server.esp32_secure import SecureTCPClient
client = SecureTCPClient(host=ESP32_IP, port=9000)
await client.send(cmd)
```

### 4-3. ESP32 펌웨어 업데이트

`docs/esp32_hmac_verify.cpp`의 `verifyAndParse()` 함수를 ESP32 TCP 수신 루프에 통합합니다.  
`SECRET_KEY`를 `.env`의 `ESP32_SECRET` 값과 동일하게 설정하세요.

> 💡 ESP32 시크릿 키 관리: NVS(Non-Volatile Storage)에 저장하면 펌웨어 소스 노출 시에도 안전합니다.

---

## 검증 방법

### JWT 인증 테스트

```bash
# 토큰 발급
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/token?username=stephen&password=yourpw" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 인증 필요 엔드포인트 호출
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/report

# 토큰 없이 호출 → 401 응답 확인
curl http://localhost:8000/command -X POST -d '{}' -H "Content-Type: application/json"
```

### 얼굴 임베딩 암호화 확인

```bash
# 암호화 파일 생성 확인
ls -la face_db/
# face_db/encodings.enc 존재, encodings.pkl.bak 으로 백업됨

# 평문 읽기 시도 → 깨진 바이너리 확인
python3 -c "import pickle; pickle.load(open('face_db/encodings.enc','rb'))"
# → 오류 발생 = 암호화 정상
```

### HMAC 패킷 검증 테스트

```python
# Python에서 직접 검증
from server.esp32_secure import build_signed_packet
import json

packet = build_signed_packet({"action": "led_on", "room": "living_room"})
parsed = json.loads(packet)
print("ts:", parsed["ts"])
print("sig:", parsed["sig"][:16], "...")
print("cmd:", parsed["cmd"])
```

---

## 적용 우선순위 요약

| 순서 | 항목 | 소요 시간 | 서버 재시작 필요 |
|------|------|-----------|-----------------|
| 1 | `harden_setup.sh` 실행 | 1분 | ❌ |
| 2 | 얼굴 임베딩 암호화 (`face_store.py`) | 30분 | ✅ |
| 3 | FastAPI JWT 인증 (`auth.py`) | 1~2시간 | ✅ |
| 4 | TCP HMAC 서명 (`esp32_secure.py`) | 2~3시간 | ✅ + ESP32 OTA |

---

## 관련 보안 기준

| 항목 | NIST SP 800-213 | OWASP IoT Top 10 |
|------|----------------|-----------------|
| JWT 인증 | §4.3 Access Control | OT2 Insecure Network Services |
| 얼굴 임베딩 암호화 | §4.5 Data Protection | OT6 Insufficient Privacy Protection |
| TCP HMAC 서명 | §4.2 Communication Security | OT1 Weak Passwords / OT3 Insecure Services |

---

*iot-repo-1 · Stephen · 2026-03-06*
