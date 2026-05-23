# Kevin Patrol Dashboard — 개발 기록

**날짜**: 2025-02-15  
**프로젝트**: Kevin Patrol Dashboard v3.1  
**기술 스택**: PyQt6 + PyQtGraph + DataProvider 추상화 레이어  

---

## 오늘 작업 요약

### 버그 수정: Face Detection 파이프라인 미연결

**증상**  
대시보드의 Face Detection 패널에 "No faces detected" 고정 표시.  
Alert History에 "New face detected"가 한 번 기록되긴 하지만,  
FaceDetectionWidget에는 face 데이터가 전달되지 않음.

**원인 분석**

데이터 흐름을 추적한 결과, `SimDataProvider.get_detections()`가  
`_active_detections`의 face 이벤트를 전혀 읽지 않는 것이 원인이었다.

```
MockSimForDashboard.tick()
  └── _active_detections에 face/fall 랜덤 생성  ← face 여기에 저장됨
  └── persons 리스트: _active_detections의 fall만 체크 → fallen=True 설정

SimDataProvider.get_detections()
  └── s.persons에서 fallen==True인 것만 Detection으로 반환  ← face 누락!

DashboardWindow._on_update()
  └── detections = p.get_detections()  ← face Detection이 없음
  └── face_detection.update_data(detections, pose)  ← 빈 리스트 전달
  └── FaceDetectionWidget → "No faces detected"
```

핵심 문제: `MockSimForDashboard`는 `_active_detections` 리스트에  
`("face", x, z, timestamp)` 튜플로 face 이벤트를 저장하지만,  
`SimDataProvider.get_detections()`는 `s.persons`의 `fallen` 플래그만  
참조하여 fall 타입 Detection만 생성했다.

**수정 파일**: `core/data_provider.py` — `SimDataProvider.get_detections()`

**수정 내용**

기존 코드 (fall만 반환):
```python
def get_detections(self) -> List[Detection]:
    s = self._sim
    detections = []
    for i, (px, pz, fallen) in enumerate(s.persons):
        if fallen:
            detections.append(Detection(
                type="fall", x=px, z=pz,
                confidence=0.95, active=True,
                timestamp=time.time()
            ))
    return detections
```

수정 후 (fall + face 모두 반환):
```python
def get_detections(self) -> List[Detection]:
    s = self._sim
    detections = []
    now = time.time()

    # 1) persons 리스트에서 낙상 감지
    for i, (px, pz, fallen) in enumerate(s.persons):
        if fallen:
            detections.append(Detection(
                type="fall", x=px, z=pz,
                confidence=0.95, active=True,
                timestamp=now
            ))

    # 2) _active_detections에서 face 등 추가 감지
    active_dets = getattr(s, '_active_detections', [])
    for det_tuple in active_dets:
        if len(det_tuple) >= 4:
            det_type, dx, dz, dt = (det_tuple[0], det_tuple[1],
                                     det_tuple[2], det_tuple[3])
        elif len(det_tuple) >= 3:
            det_type, dx, dz, dt = (det_tuple[0], det_tuple[1],
                                     det_tuple[2], now)
        else:
            continue

        # fall은 persons에서 이미 처리 → 중복 방지
        if det_type == "fall":
            continue

        detections.append(Detection(
            type=det_type, x=dx, z=dz,
            confidence=0.85, active=True,
            timestamp=now
        ))

    return detections
```

**수정 후 데이터 흐름**:
```
MockSimForDashboard.tick()
  └── _active_detections = [("face", x, z, t), ...]

SimDataProvider.get_detections()
  ├── s.persons → fallen → Detection(type="fall")
  └── s._active_detections → face → Detection(type="face")  ← 추가됨

DashboardWindow._on_update()
  └── detections = [Detection(type="face", ...), ...]
  └── face_detection.update_data(detections)  ← face 전달됨!
  └── camera_feed.update_data(..., detections)  ← 바운딩 박스도 표시
```

**검증 결과**

수정 후 대시보드에서 확인된 정상 동작:

- Face Detection 패널: History에 5명 등록 (Resident-2, Resident-1, Guest-B, Guest-A, Unknown)
- 누적 카운트: "Total: 5 faces / 151 detections"
- Alert History: "Face detected at (-9, -11)" 등 다수 기록
- 토스트 알림: 우상단 팝업 정상 표시
- Camera Feed: face 바운딩 박스 오버레이 정상 표시

---

## Detection 타입 정리

| 타입 | 의미 | 소스 | 대시보드 반영 |
|------|------|------|---------------|
| `face` | 사람 존재 감지 (카메라 얼굴 인식) | `_active_detections` | Face Detection 패널 + Camera Feed 바운딩 박스 + Alert |
| `fall` | 낙상 위험 감지 | `persons` (fallen=True) | Camera Feed 바운딩 박스 + Alert (danger) |

- face: 순찰 구역에 사람이 있음 → 신원 식별 (Resident/Guest/Unknown) 확장 가능
- fall: 감지된 사람이 쓰러진 위험 상황 → `/alert` → `guard_brain` LLM 경보 파이프라인

`MockSimForDashboard.tick()`에서 `random.choice(["face", "face", "fall"])`로  
face 비중 2/3 — 순찰 중 사람 만남 빈도가 낙상보다 높은 것이 자연스러움.

---

## 파일 구조 (현재)

```
kevin_patrol/
├── run_dashboard.py          — 대시보드 실행 스크립트
├── run_sim.py                — 3D 시뮬레이터 실행 스크립트
├── core/
│   └── data_provider.py      — DataProvider 추상화 레이어 (★ 오늘 수정)
├── dashboard/
│   └── app.py                — 통합 모니터링 GUI (v3.1, 1563 lines)
└── sim/
    └── kevin_3d_sim.py       — 3D Patrol Simulator
```

---

## 다음 단계

- Camera Feed에서 face 바운딩 박스 FOV 내 표시 확인 (순찰 모드 중)
- `kevin_3d_sim.py` 본체에도 `_active_detections` face 이벤트 생성 로직 추가
  (현재는 MockSim에만 있음)
- Phase 4 ROS2DataProvider 구현 시 `/face_event` 토픽 → Detection(type="face") 매핑
