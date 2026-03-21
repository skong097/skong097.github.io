---
title: "카메라 선택 기능 통합 가이드"
date: 2026-03-21
draft: true
tags: ["vision-ai"]
categories: ["vision-ai"]
description: "**목표:** GUI 시작 시 카메라 선택 다이얼로그 표시 **기능:** - 사용 가능한 카메라 자동 감지 (0-9번)"
---

# 카메라 선택 기능 통합 가이드

## 📋 개요

**목표:** GUI 시작 시 카메라 선택 다이얼로그 표시

**기능:**
- 사용 가능한 카메라 자동 감지 (0-9번)
- 라디오 버튼으로 선택
- 새로고침 기능
- 선택한 카메라로 모니터링 시작

---

## ✅ 수정 사항

### **1. 새 파일: camera_selection_dialog.py**

#### **CameraSelectionDialog 클래스**
```python
class CameraSelectionDialog(QDialog):
    """카메라 선택 다이얼로그"""
    
    def detect_cameras(self):
        """사용 가능한 카메라 감지 (0-9번)"""
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # 카메라 정보 수집
                ret, frame = cap.read()
                if ret:
                    height, width = frame.shape[:2]
                    camera_name = f"{width}x{height}"
                    self.available_cameras.append((i, camera_name))
                cap.release()
```

#### **주요 기능**
1. **카메라 자동 감지**: 0-9번 테스트
2. **라디오 버튼**: 사용 가능한 카메라만 표시
3. **새로고침**: 카메라 목록 다시 감지
4. **확인/취소**: 선택한 카메라 반환

---

### **2. 수정: monitoring_page.py**

#### **__init__ 수정 (Line 86-101)**

**Before:**
```python
def __init__(self, user_info: dict, db: DatabaseManager):
    super().__init__()
    self.user_info = user_info
    self.db = db
    self.cap = None
    self.timer = None
    self.frame_count = 0
```

**After:**
```python
def __init__(self, user_info: dict, db: DatabaseManager):
    super().__init__()
    self.user_info = user_info
    self.db = db
    self.cap = None
    self.timer = None
    self.frame_count = 0
    
    # ⭐ 카메라 선택 (GUI 시작 시)
    from camera_selection_dialog import show_camera_selection_dialog
    selected_camera = show_camera_selection_dialog(self)
    
    if selected_camera is None:
        # 사용자가 취소를 누른 경우 기본 카메라 사용
        self.camera_index = 0
        print("[WARNING] 카메라 선택 취소됨. 기본 카메라(0번) 사용")
    else:
        self.camera_index = selected_camera
        print(f"[INFO] 카메라 {self.camera_index}번 선택됨")
```

---

#### **start_monitoring 수정 (Line 447-479)**

**Before:**
```python
def start_monitoring(self):
    """모니터링 시작"""
    self.add_log("[INFO] 웹캠 연결 시도...")
    
    try:
        # 웹캠 열기
        self.cap = cv2.VideoCapture(2)  # ❌ 하드코딩
        
        if not self.cap.isOpened():
            self.add_log("❌ 웹캠을 열 수 없습니다")
            return
        
        self.add_log("✅ 웹캠 연결 성공")
        ...
```

**After:**
```python
def start_monitoring(self):
    """모니터링 시작"""
    self.add_log(f"[INFO] 카메라 {self.camera_index}번 연결 시도...")
    
    try:
        # 웹캠 열기 (선택된 카메라 사용)
        self.cap = cv2.VideoCapture(self.camera_index)  # ✅ 동적
        
        if not self.cap.isOpened():
            self.add_log(f"❌ 카메라 {self.camera_index}번을 열 수 없습니다")
            return
        
        self.add_log(f"✅ 카메라 {self.camera_index}번 연결 성공")
        ...
```

---

## 🔄 데이터 흐름

```
1. GUI 시작 (main.py)
   ↓
2. MonitoringPage.__init__() 호출
   ↓
3. CameraSelectionDialog 표시
   ↓
4. 사용 가능한 카메라 자동 감지 (0-9번)
   ↓
5. 사용자가 카메라 선택
   ┌───────────────────────────────┐
   │ 📹 카메라를 선택하세요         │
   ├───────────────────────────────┤
   │ ○ 카메라 0: 640x480 (내장)   │
   │ ● 카메라 2: 1280x720 (USB)   │ ← 선택
   │                               │
   │ [🔄 새로고침] [✓ 확인] [✗ 취소]│
   └───────────────────────────────┘
   ↓
6. self.camera_index = 2 저장
   ↓
7. Start 버튼 클릭
   ↓
8. cv2.VideoCapture(2) 실행
   ↓
9. 모니터링 시작 ✅
```

---

## 🖥️ 화면 예시

### **1. 카메라 선택 다이얼로그**

```
┌──────────────────────────────────────────┐
│           📹 카메라를 선택하세요         │
│                                          │
│  사용 가능한 카메라 목록입니다.          │
│  원하는 카메라를 선택해주세요.           │
│                                          │
│ ╔════════════════════════════════════╗  │
│ ║ 사용 가능한 카메라                  ║  │
│ ╠════════════════════════════════════╣  │
│ ║ ○ 카메라 0: 640x480 (내장 웹캠)   ║  │
│ ║ ● 카메라 2: 1280x720 (USB 카메라) ║  │ ← 선택됨
│ ╚════════════════════════════════════╝  │
│                                          │
│     [🔄 새로고침] [✓ 확인] [✗ 취소]      │
└──────────────────────────────────────────┘
```

---

### **2. 카메라가 없을 때**

```
┌──────────────────────────────────────────┐
│           📹 카메라를 선택하세요         │
│                                          │
│  사용 가능한 카메라 목록입니다.          │
│  원하는 카메라를 선택해주세요.           │
│                                          │
│ ╔════════════════════════════════════╗  │
│ ║ 사용 가능한 카메라                  ║  │
│ ╠════════════════════════════════════╣  │
│ ║                                    ║  │
│ ║  ⚠️ 사용 가능한 카메라를          ║  │
│ ║     찾을 수 없습니다.              ║  │
│ ║                                    ║  │
│ ╚════════════════════════════════════╝  │
│                                          │
│     [🔄 새로고침]  [✗ 취소]              │
└──────────────────────────────────────────┘
```

---

## 🚀 배포 방법

### **Step 1: 파일 복사**

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 백업
cp monitoring_page.py monitoring_page.py.backup_before_camera_selection

# 새 파일 추가
cp ~/Downloads/camera_selection_dialog.py .

# 기존 파일 교체
cp ~/Downloads/monitoring_page_with_camera_selection.py monitoring_page.py
```

---

### **Step 2: 파일 확인**

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 파일 구조 확인
ls -la *.py | grep -E "(camera|monitoring)"

# 예상 출력:
# -rw-r--r-- 1 gjkong gjkong  XXXX camera_selection_dialog.py
# -rw-r--r-- 1 gjkong gjkong  XXXX monitoring_page.py
# -rw-r--r-- 1 gjkong gjkong  XXXX monitoring_page.py.backup_before_camera_selection
```

---

### **Step 3: 코드 검증**

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# camera_index가 있는지 확인
grep -n "self.camera_index" monitoring_page.py

# 예상 출력:
# 95:  self.camera_index = 0
# 97:  self.camera_index = selected_camera
# 98:  print(f"[INFO] 카메라 {self.camera_index}번 선택됨")
# 453: self.cap = cv2.VideoCapture(self.camera_index)
```

---

### **Step 4: 캐시 삭제 및 재시작**

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 캐시 삭제
rm -rf __pycache__
find . -name "*.pyc" -delete

# GUI 재시작
python main.py
```

---

## ✅ 테스트 방법

### **1. GUI 시작**
```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui
python main.py
```

---

### **2. 카메라 선택 다이얼로그 확인**

**예상 동작:**
1. GUI 창이 열리기 전에 카메라 선택 다이얼로그 표시
2. 사용 가능한 카메라 목록 표시 (0, 2번 등)
3. 라디오 버튼으로 선택
4. "확인" 클릭

---

### **3. 터미널 로그 확인**

```
[INFO] 카메라 감지 중...
[INFO] 카메라 0번 감지: 640x480 (내장 웹캠)
[INFO] 카메라 2번 감지: 1280x720 (USB 카메라)
[INFO] 총 2개 카메라 감지 완료
[INFO] 카메라 2번 선택됨  ← 사용자가 선택한 카메라
```

---

### **4. 모니터링 시작**

**비전 홈 케어 → 실시간 모니터링**
1. "Start" 버튼 클릭
2. 로그 확인:
   ```
   [INFO] 카메라 2번 연결 시도...
   ✅ 카메라 2번 연결 성공
   [INFO] 모니터링 시작 (10 FPS)
   ```

---

### **5. 다른 카메라로 테스트**

```bash
# GUI 종료 후 재시작
python main.py

# 카메라 선택 다이얼로그에서 다른 카메라 선택 (예: 0번)
# 확인 클릭
# Start 버튼 클릭
# 로그 확인: "카메라 0번 연결 성공" ✅
```

---

## 🎯 주요 기능

### **1. 자동 감지**
- 0-9번 카메라 자동 테스트
- 사용 가능한 카메라만 표시

### **2. 정보 표시**
- 카메라 번호
- 해상도 (예: 1280x720)
- 카메라 종류 (내장/USB)

### **3. 새로고침**
- 카메라 목록 다시 감지
- USB 카메라 연결/해제 후 사용

### **4. 기본값**
- 취소 시: 카메라 0번 사용
- 오류 시: 기본 카메라 사용

---

## ⚠️ 주의사항

### **1. 카메라 권한**
```bash
# 카메라 권한 확인
ls -la /dev/video*

# 권한 없을 경우
sudo usermod -a -G video $USER
# 로그아웃 후 재로그인
```

---

### **2. 여러 카메라 동시 사용**
- 다른 프로그램이 카메라를 사용 중이면 열리지 않음
- Zoom, Skype 등 종료 필요

---

### **3. 카메라 번호 변경**
- USB 카메라 재연결 시 번호가 바뀔 수 있음
- "새로고침" 버튼으로 다시 감지

---

## 🔮 향후 개선 사항

### **1. 카메라 미리보기**
```python
# 선택한 카메라의 실시간 미리보기 표시
def show_preview(self, camera_id):
    cap = cv2.VideoCapture(camera_id)
    ret, frame = cap.read()
    if ret:
        # QLabel에 미리보기 표시
        self.preview_label.setPixmap(...)
    cap.release()
```

---

### **2. 해상도 선택**
```python
# 카메라별 지원 해상도 감지
resolutions = [
    (640, 480),
    (1280, 720),
    (1920, 1080)
]

# 드롭다운 메뉴로 선택
```

---

### **3. 설정 저장**
```python
# 선택한 카메라를 config.json에 저장
{
    "camera_index": 2,
    "remember_camera": true
}

# 다음 실행 시 자동으로 해당 카메라 사용
```

---

### **4. 고급 설정**
```python
# 카메라 파라미터 조정
- 밝기 (Brightness)
- 대비 (Contrast)
- 노출 (Exposure)
- FPS
```

---

## 📂 생성된 파일

```
/mnt/user-data/outputs/
├── camera_selection_dialog.py                 # 새 파일 (다이얼로그)
├── monitoring_page_with_camera_selection.py   # 수정된 파일
└── CAMERA_SELECTION_GUIDE.md                  # 이 문서
```

---

## 📊 코드 변경 요약

### **camera_selection_dialog.py (새 파일)**
- 총 라인: ~220 lines
- 주요 클래스: CameraSelectionDialog
- 주요 메소드:
  - detect_cameras(): 카메라 자동 감지
  - on_camera_selected(): 카메라 선택 이벤트
  - refresh_cameras(): 새로고침
  - show_camera_selection_dialog(): 헬퍼 함수

---

### **monitoring_page.py (수정)**
- 수정 위치: Line 86-101 (__init__)
- 추가 코드: 13 lines
- 수정 위치: Line 447-479 (start_monitoring)
- 수정 라인: 3 lines

**총 변경:** +13 lines, ~3 modified

---

## 🎉 완료!

카메라 선택 기능이 완전히 통합되었습니다! 🎬

**테스트 후 결과를 알려주세요!** 😊

---

**작성:** Stephen Kong  
**날짜:** 2026-02-05  
**버전:** v1.0
