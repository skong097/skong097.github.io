---
title: "이슈 기록 — WebSocket JWT 인증 실패"
date: 2026-03-21
draft: true
tags: ["robot-security", "jwt"]
categories: ["robot-security"]
description: "**날짜:** 2026-03-06 **프로젝트:** Voice IoT Controller (`iot-repo-1`) **상태:** 🔴 미해결"
---

# 이슈 기록 — WebSocket JWT 인증 실패

**날짜:** 2026-03-06  
**프로젝트:** Voice IoT Controller (`iot-repo-1`)  
**상태:** 🔴 미해결

---

## 증상

브라우저 대시보드가 WebSocket `/ws` 연결 시 지속적으로 403 거부됨.

```
INFO:     127.0.0.1:xxxxx - "WebSocket /ws" 403
WARNING   server.api_routes - [AUTH] WebSocket JWT 검증 실패 — 연결 거부
INFO:     connection rejected (403 Forbidden)
INFO:     connection closed
```

- 약 3~4초 간격으로 반복 재연결 시도 후 매번 403
- ESP32 보드 연결 여부와 무관 (브라우저 ↔ 서버 간 문제)

---

## 원인 분석

`api_routes.py`에서 WebSocket 엔드포인트에 JWT 인증 추가 후,  
브라우저 `index_dashboard.html`이 토큰 없이 연결 시도하는 상황.

```
브라우저                        서버
ws://localhost:8000/ws   →   token 없음 → 403 거부
ws://localhost:8000/ws?token=xxx  →  정상 연결 예정
```

---

## 시도한 조치

### 1) `index_dashboard.html` 수정 (완료)
- JWT 토큰 관리 모듈 추가: `fetchToken()`, `getAuthHeaders()`
- `connectWS()`: `?token=xxx` 쿼리 파라미터 포함
- `window.onload`: 페이지 로드 시 `/auth/token` 자동 호출
- 보호 fetch 엔드포인트 8곳에 `Authorization` 헤더 추가

### 2) 파일 교체 확인 (완료)
```bash
grep -n "fetchToken\|jwt_token" ~/dev_ws/iot-repo-1/web/index_dashboard.html
# → 6줄 정상 검출 확인
```

### 3) 브라우저 강력 새로고침 시도 (Ctrl+Shift+R)
→ 여전히 403 지속

---

## 미확인 사항 (다음 세션 체크리스트)

- [ ] 브라우저 콘솔(F12) `sessionStorage.getItem('jwt_token')` 값 확인
- [ ] 브라우저 콘솔에서 `/auth/token` 수동 호출 결과 확인
  ```javascript
  fetch('/auth/token', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username:'dashboard', password:''})
  }).then(r => r.json()).then(console.log)
  ```
- [ ] `fetchToken()` 호출 자체가 실패하는지 여부 (네트워크 탭 확인)
- [ ] `window.onload`가 `async`로 제대로 동작하는지 확인
- [ ] 서버 `/auth/token` 엔드포인트 정상 응답 여부 확인

---

## 관련 파일

| 파일 | 비고 |
|------|------|
| `server/api_routes.py` | WebSocket JWT 검증 코드 위치 |
| `web/index_dashboard.html` | 수정 완료, 교체 확인됨 |
| `server/auth.py` | JWT 발급/검증 모듈 |
