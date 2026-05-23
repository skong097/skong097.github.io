# ST-GCN 실시간 영상 GUI 추론 구현 계획서

## 📋 문서 정보

| 항목 | 내용 |
|------|------|
| **작성일** | 2026-02-05 (수) |
| **프로젝트명** | Home Safe Solution - ST-GCN 모델 통합 |
| **목표** | 기존 GUI에 ST-GCN 실시간 추론 기능 추가 |
| **접근 방식** | 기존 GUI 변경 없이 모델 선택 옵션 추가 |

---

## 1. 프로젝트 개요

### 1.1 배경
- 현재 Home Safe Solution은 **Random Forest 모델** (93.19% 정확도)로 낙상 감지 수행
- **ST-GCN 모델** (84.21% 정확도)이 별도로 학습 완료됨
- 사용자가 두 모델 중 선택하여 사용할 수 있도록 GUI 통합 필요

### 1.2 목표
```
✅ 기존 GUI 코드 최소 변경 (기존 기능 100% 유지)
✅ ST-GCN 실시간 추론 모듈 추가
✅ 모델 선택 UI 제공 (Random Forest / ST-GCN)
✅ 60 프레임 버퍼링을 통한 시계열 추론
✅ 향후 Pre-trained 모델 교체 용이한 구조
```

### 1.3 제약 조건
- 기존 `monitoring_page.py` 핵심 로직 유지
- PyQt6 기반 GUI 프레임워크 유지
- YOLO Pose (17 keypoints) 그대로 사용
- 실시간 처리 (최소 15 FPS 이상)

---

## 2. 현재 시스템 분석

### 2.1 기존 프로젝트 구조

```
/home/gjkong/dev_ws/yolo/myproj/gui/
├── main.py                      # 앱 진입점
├── main_window.py               # 메인 윈도우
├── monitoring_page.py           # ⭐ 핵심 (1,490 lines)
├── input_selection_dialog.py    # 입력 소스 선택
├── video_control_panel.py       # 동영상 재생 제어
├── camera_selection_dialog.py   # 카메라 선택 (백업)
├── database_models.py           # DB 모델
├── one_euro_filter.py           # 키포인트 필터
├── login_page.py                # 로그인
├── dashboard_page.py            # 대시보드
├── event_log_page.py            # 이벤트 로그
└── user_management_page.py      # 사용자 관리
```

### 2.2 ST-GCN 프로젝트 구조

```
/home/gjkong/dev_ws/st_gcn/
├── checkpoints/
│   ├── best_model_binary.pth    # ⭐ 사용할 모델 (2 클래스)
│   ├── best_model.pth           # 3 클래스 모델
│   └── ...
├── models/
│   ├── st_gcn.py                # ⭐ 모델 정의
│   ├── graph.py                 # ⭐ 그래프 정의
│   └── __init__.py
├── data/
│   └── binary/
│       ├── train_data.npy       # Shape: (174, 3, 60, 17, 1)
│       └── ...
└── data_integrated/
    └── fall-*.mp4               # 테스트 동영상 70개
```

### 2.3 데이터 형식

#### ST-GCN 입력 형식
```python
Input Shape: (N, C, T, V, M)
- N = Batch size (추론 시 1)
- C = 3 (x, y, confidence)
- T = 60 (프레임 수, 약 3초 @20fps)
- V = 17 (COCO keypoints)
- M = 1 (단일 사람)

실제 Shape: (1, 3, 60, 17, 1)
```

#### YOLO Pose 출력 형식 (기존)
```python
# 현재 monitoring_page.py에서 추출하는 형식
keypoints: (17, 3)  # [x, y, confidence] × 17 joints
```

### 2.4 현재 추론 흐름 (Random Forest)

```
┌─────────────────────────────────────────────────────────────────┐
│  update_frame() in monitoring_page.py                           │
├─────────────────────────────────────────────────────────────────┤
│  1. cap.read() → frame                                          │
│  2. YOLO Pose → keypoints (17, 3)                               │
│  3. OneEuroFilter → filtered keypoints                          │
│  4. extract_features() → features (1D vector)                   │
│  5. Random Forest → prediction (Normal/Falling/Fallen)          │
│  6. UI 업데이트 + DB 저장                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 구현 설계

### 3.1 목표 추론 흐름 (ST-GCN 추가)

```
┌─────────────────────────────────────────────────────────────────┐
│  update_frame() - 수정 버전                                      │
├─────────────────────────────────────────────────────────────────┤
│  1. cap.read() → frame                                          │
│  2. YOLO Pose → keypoints (17, 3)                               │
│  3. OneEuroFilter → filtered keypoints                          │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────────────────────┐    │
│  │ if Random Forest │    │ if ST-GCN                       │    │
│  ├─────────────────┤    ├─────────────────────────────────┤    │
│  │ 4a. extract()   │    │ 4b. buffer.append(keypoints)    │    │
│  │ 5a. RF predict  │    │ 5b. if len(buffer) >= 60:       │    │
│  │                 │    │     ST-GCN predict              │    │
│  └─────────────────┘    └─────────────────────────────────┘    │
│                                                                 │
│  6. UI 업데이트 + DB 저장                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 새로 생성할 파일

#### 파일 1: `stgcn_inference.py` (신규)
```
위치: /home/gjkong/dev_ws/yolo/myproj/gui/stgcn_inference.py
역할: ST-GCN 모델 로드 및 추론 래퍼 클래스
의존성: torch, numpy, models.st_gcn, models.graph
```

**주요 클래스/함수:**
```python
class STGCNInference:
    def __init__(self, model_path, device='cuda'):
        """모델 로드 및 초기화"""
        
    def preprocess(self, keypoints_buffer):
        """60 프레임 keypoints → (1, 3, 60, 17, 1) 텐서 변환"""
        
    def predict(self, keypoints_buffer):
        """추론 수행 → (label, confidence) 반환"""
        
    def get_label_name(self, label_idx):
        """0 → 'Normal', 1 → 'Fall'"""
```

#### 파일 2: `model_selection_dialog.py` (신규)
```
위치: /home/gjkong/dev_ws/yolo/myproj/gui/model_selection_dialog.py
역할: 모델 선택 다이얼로그 (Random Forest / ST-GCN)
의존성: PyQt6
```

**UI 구성:**
```
┌─────────────────────────────────────────┐
│  🤖 낙상 감지 모델 선택                  │
├─────────────────────────────────────────┤
│                                         │
│  ○ Random Forest (권장)                 │
│    - 정확도: 93.19%                     │
│    - 프레임 단위 즉시 추론               │
│                                         │
│  ○ ST-GCN (시계열 분석)                 │
│    - 정확도: 84.21%                     │
│    - 60 프레임(3초) 시퀀스 분석          │
│                                         │
├─────────────────────────────────────────┤
│           [확인]    [취소]               │
└─────────────────────────────────────────┘
```

### 3.3 수정할 기존 파일

#### `monitoring_page.py` 수정 사항

**A. Import 추가**
```python
# 기존
from one_euro_filter import OneEuroFilter

# 추가
from stgcn_inference import STGCNInference
from model_selection_dialog import show_model_selection_dialog
```

**B. `__init__` 수정**
```python
# 기존 input_selection_dialog 호출 후 추가
self.model_type = 'random_forest'  # 또는 'stgcn'
self.stgcn_model = None
self.keypoints_buffer = []  # ST-GCN용 60 프레임 버퍼

# 모델 선택 다이얼로그 (선택적)
# model_config = show_model_selection_dialog(self)
# self.model_type = model_config['type']
```

**C. `start_monitoring` 수정**
```python
# ST-GCN 모델 초기화 (필요 시)
if self.model_type == 'stgcn' and self.stgcn_model is None:
    self.stgcn_model = STGCNInference(
        model_path='/home/gjkong/dev_ws/st_gcn/checkpoints/best_model_binary.pth',
        device='cuda' if torch.cuda.is_available() else 'cpu'
    )
    self.keypoints_buffer = []
```

**D. `update_frame` 수정**
```python
# 기존 keypoints 추출 후 분기 처리
if self.model_type == 'random_forest':
    # 기존 Random Forest 로직 (변경 없음)
    features = self.extract_features(keypoints)
    prediction = self.rf_model.predict(features)
    
elif self.model_type == 'stgcn':
    # ST-GCN 버퍼링 및 추론
    self.keypoints_buffer.append(keypoints)
    
    if len(self.keypoints_buffer) > 60:
        self.keypoints_buffer.pop(0)  # 슬라이딩 윈도우
    
    if len(self.keypoints_buffer) >= 60:
        label, confidence = self.stgcn_model.predict(self.keypoints_buffer)
        # UI 업데이트
    else:
        # 버퍼링 중 표시 (예: "Buffering... 45/60")
        pass
```

### 3.4 프로젝트 구조 (최종)

```
/home/gjkong/dev_ws/yolo/myproj/gui/
├── main.py
├── main_window.py
├── monitoring_page.py              # 🔧 수정 (분기 로직 추가)
├── input_selection_dialog.py
├── video_control_panel.py
├── model_selection_dialog.py       # ⭐ 신규 (모델 선택 UI)
├── stgcn_inference.py              # ⭐ 신규 (ST-GCN 추론 모듈)
├── stgcn/                          # ⭐ 신규 (ST-GCN 모델 복사)
│   ├── __init__.py
│   ├── st_gcn.py                   # 모델 정의
│   └── graph.py                    # 그래프 정의
├── database_models.py
├── one_euro_filter.py
├── login_page.py
├── dashboard_page.py
├── event_log_page.py
└── user_management_page.py
```

---

## 4. 구현 단계별 작업 계획

### Phase 1: ST-GCN 추론 모듈 개발 (Day 1)

| 순서 | 작업 | 예상 시간 | 산출물 |
|------|------|----------|--------|
| 1-1 | ST-GCN 모델 파일 복사 | 10분 | `stgcn/st_gcn.py`, `stgcn/graph.py` |
| 1-2 | `stgcn_inference.py` 작성 | 1시간 | 추론 래퍼 클래스 |
| 1-3 | 단독 테스트 스크립트 작성 | 30분 | `test_stgcn_inference.py` |
| 1-4 | 동영상 파일로 추론 테스트 | 30분 | 테스트 결과 확인 |

**Phase 1 검증:**
```bash
# 테스트 명령
cd /home/gjkong/dev_ws/yolo/myproj/gui
python test_stgcn_inference.py --video /home/gjkong/dev_ws/st_gcn/data_integrated/fall-01-cam0.mp4
```

### Phase 2: GUI 통합 (Day 1~2)

| 순서 | 작업 | 예상 시간 | 산출물 |
|------|------|----------|--------|
| 2-1 | `model_selection_dialog.py` 작성 | 1시간 | 모델 선택 UI |
| 2-2 | `monitoring_page.py` 수정 | 2시간 | 통합 코드 |
| 2-3 | 버퍼링 상태 UI 추가 | 30분 | 버퍼 진행률 표시 |
| 2-4 | 통합 테스트 | 1시간 | 전체 기능 검증 |

**Phase 2 검증:**
```bash
# GUI 실행
cd /home/gjkong/dev_ws/yolo/myproj/gui
python main.py
# → 모델 선택 → ST-GCN 선택 → 동영상 재생 → 추론 확인
```

### Phase 3: 최적화 및 안정화 (Day 2)

| 순서 | 작업 | 예상 시간 | 산출물 |
|------|------|----------|--------|
| 3-1 | GPU 메모리 최적화 | 30분 | 메모리 누수 방지 |
| 3-2 | 추론 속도 측정 | 30분 | FPS 로그 |
| 3-3 | 에러 핸들링 추가 | 30분 | 예외 처리 |
| 3-4 | 문서화 (WORK_LOG) | 30분 | 작업 기록 |

---

## 5. 기술 상세

### 5.1 ST-GCN 추론 모듈 상세 설계

```python
# stgcn_inference.py 핵심 구조

import torch
import numpy as np
from stgcn.st_gcn import Model
from stgcn.graph import Graph

class STGCNInference:
    """ST-GCN 실시간 추론 클래스"""
    
    LABELS = ['Normal', 'Fall']  # Binary classification
    SEQUENCE_LENGTH = 60         # 60 frames
    NUM_KEYPOINTS = 17           # COCO keypoints
    NUM_CHANNELS = 3             # x, y, confidence
    
    def __init__(self, model_path: str, device: str = 'auto'):
        """
        Args:
            model_path: best_model_binary.pth 경로
            device: 'cuda', 'cpu', 또는 'auto'
        """
        # 디바이스 설정
        if device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # 모델 로드
        self.model = Model(
            num_class=2,      # Binary: Normal, Fall
            num_point=17,     # COCO keypoints
            num_person=1,
            in_channels=3,    # x, y, confidence
            graph_args={}
        )
        
        # 가중치 로드
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        print(f"[ST-GCN] Model loaded on {self.device}")
    
    def preprocess(self, keypoints_buffer: list) -> torch.Tensor:
        """
        60 프레임 keypoints 버퍼를 텐서로 변환
        
        Args:
            keypoints_buffer: list of (17, 3) arrays, length=60
            
        Returns:
            tensor: (1, 3, 60, 17, 1)
        """
        # (60, 17, 3) numpy array
        data = np.array(keypoints_buffer)  # (T, V, C)
        
        # Normalize coordinates to [0, 1] (이미 정규화되어 있다면 생략)
        # data[:, :, 0] /= frame_width
        # data[:, :, 1] /= frame_height
        
        # (T, V, C) → (C, T, V)
        data = data.transpose(2, 0, 1)  # (3, 60, 17)
        
        # (C, T, V) → (1, C, T, V, 1)
        data = data[np.newaxis, :, :, :, np.newaxis]  # (1, 3, 60, 17, 1)
        
        # Tensor 변환
        tensor = torch.tensor(data, dtype=torch.float32).to(self.device)
        
        return tensor
    
    @torch.no_grad()
    def predict(self, keypoints_buffer: list) -> tuple:
        """
        낙상 여부 추론
        
        Args:
            keypoints_buffer: list of (17, 3) arrays, length >= 60
            
        Returns:
            (label_name: str, confidence: float)
        """
        # 최근 60 프레임만 사용
        buffer = keypoints_buffer[-self.SEQUENCE_LENGTH:]
        
        # 전처리
        input_tensor = self.preprocess(buffer)
        
        # 추론
        output = self.model(input_tensor)
        
        # Softmax → 확률
        probs = torch.softmax(output, dim=1)
        confidence, predicted = torch.max(probs, 1)
        
        label_idx = predicted.item()
        label_name = self.LABELS[label_idx]
        conf_value = confidence.item()
        
        return label_name, conf_value
    
    def get_buffer_status(self, current_length: int) -> str:
        """버퍼 상태 문자열 반환"""
        if current_length >= self.SEQUENCE_LENGTH:
            return "Ready"
        else:
            return f"Buffering... {current_length}/{self.SEQUENCE_LENGTH}"
```

### 5.2 모델 선택 다이얼로그 상세 설계

```python
# model_selection_dialog.py 핵심 구조

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QRadioButton, QButtonGroup, QPushButton, QGroupBox
)
from PyQt6.QtCore import Qt

class ModelSelectionDialog(QDialog):
    """낙상 감지 모델 선택 다이얼로그"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("낙상 감지 모델 선택")
        self.setFixedSize(400, 300)
        self.selected_model = 'random_forest'  # 기본값
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 제목
        title = QLabel("🤖 낙상 감지 모델을 선택하세요")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 모델 선택 그룹
        group = QGroupBox("사용 가능한 모델")
        group_layout = QVBoxLayout()
        
        # Radio Buttons
        self.btn_group = QButtonGroup(self)
        
        # Random Forest
        self.rf_radio = QRadioButton("Random Forest (권장)")
        self.rf_radio.setChecked(True)
        rf_desc = QLabel("  • 정확도: 93.19%\n  • 프레임 단위 즉시 추론")
        rf_desc.setStyleSheet("color: gray; margin-left: 20px;")
        group_layout.addWidget(self.rf_radio)
        group_layout.addWidget(rf_desc)
        
        # ST-GCN
        self.stgcn_radio = QRadioButton("ST-GCN (시계열 분석)")
        stgcn_desc = QLabel("  • 정확도: 84.21%\n  • 60프레임(3초) 시퀀스 분석")
        stgcn_desc.setStyleSheet("color: gray; margin-left: 20px;")
        group_layout.addWidget(self.stgcn_radio)
        group_layout.addWidget(stgcn_desc)
        
        self.btn_group.addButton(self.rf_radio)
        self.btn_group.addButton(self.stgcn_radio)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
        # 버튼
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("확인")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_selected_model(self) -> dict:
        """선택된 모델 정보 반환"""
        if self.rf_radio.isChecked():
            return {'type': 'random_forest', 'name': 'Random Forest'}
        else:
            return {'type': 'stgcn', 'name': 'ST-GCN'}


def show_model_selection_dialog(parent=None) -> dict:
    """모델 선택 다이얼로그 표시"""
    dialog = ModelSelectionDialog(parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_selected_model()
    else:
        # 취소 시 기본값
        return {'type': 'random_forest', 'name': 'Random Forest'}
```

### 5.3 monitoring_page.py 수정 포인트

```python
# ========== 수정 1: Import 추가 ==========
# 기존 imports 아래에 추가
try:
    from stgcn_inference import STGCNInference
    STGCN_AVAILABLE = True
except ImportError:
    STGCN_AVAILABLE = False
    print("[Warning] ST-GCN module not available")

from model_selection_dialog import show_model_selection_dialog


# ========== 수정 2: __init__ 수정 ==========
# input_selection_dialog 호출 후 추가

# 모델 선택
model_config = show_model_selection_dialog(self)
self.model_type = model_config['type']
self.model_name = model_config['name']

# ST-GCN 관련 변수 초기화
self.stgcn_model = None
self.keypoints_buffer = []
self.stgcn_buffer_size = 60


# ========== 수정 3: start_monitoring 수정 ==========
# 기존 코드 후 추가

if self.model_type == 'stgcn':
    if STGCN_AVAILABLE and self.stgcn_model is None:
        try:
            self.stgcn_model = STGCNInference(
                model_path='/home/gjkong/dev_ws/st_gcn/checkpoints/best_model_binary.pth'
            )
            self.keypoints_buffer = []
            print(f"[ST-GCN] Model initialized")
        except Exception as e:
            print(f"[ST-GCN] Failed to load model: {e}")
            self.model_type = 'random_forest'  # Fallback


# ========== 수정 4: update_frame 수정 ==========
# keypoints 추출 후, 기존 RF 추론 코드를 조건문으로 감싸기

# 모델별 분기 처리
if self.model_type == 'random_forest':
    # ===== 기존 Random Forest 코드 (변경 없음) =====
    features = self.extract_features(filtered_keypoints)
    prediction = self.rf_model.predict(features.reshape(1, -1))
    # ... 기존 로직 유지 ...
    
elif self.model_type == 'stgcn':
    # ===== ST-GCN 추론 =====
    # 버퍼에 keypoints 추가
    self.keypoints_buffer.append(filtered_keypoints.copy())
    
    # 버퍼 크기 유지 (슬라이딩 윈도우)
    if len(self.keypoints_buffer) > self.stgcn_buffer_size:
        self.keypoints_buffer.pop(0)
    
    # 추론 수행
    if len(self.keypoints_buffer) >= self.stgcn_buffer_size:
        label, confidence = self.stgcn_model.predict(self.keypoints_buffer)
        
        # 결과 매핑
        if label == 'Fall':
            event_type = '낙상'
            color = (0, 0, 255)  # Red
        else:
            event_type = '정상'
            color = (0, 255, 0)  # Green
        
        # UI 업데이트 (기존 방식과 동일)
        self.update_status_display(event_type, confidence)
        
    else:
        # 버퍼링 중 표시
        buffer_status = f"Buffering... {len(self.keypoints_buffer)}/{self.stgcn_buffer_size}"
        self.update_status_display('버퍼링', 0.0, buffer_status)
```

---

## 6. 테스트 계획

### 6.1 단위 테스트

| 테스트 항목 | 입력 | 예상 출력 | 확인 방법 |
|------------|------|----------|----------|
| 모델 로드 | model_path | 로드 성공 메시지 | print 확인 |
| 전처리 | 60 × (17, 3) | (1, 3, 60, 17, 1) | shape 확인 |
| 추론 | 정상 동작 시퀀스 | 'Normal', 0.7+ | 결과 확인 |
| 추론 | 낙상 동작 시퀀스 | 'Fall', 0.7+ | 결과 확인 |

### 6.2 통합 테스트

| 시나리오 | 테스트 내용 | 예상 결과 |
|----------|------------|----------|
| RF → 카메라 | 기존 기능 유지 확인 | 정상 작동 |
| RF → 파일 | 기존 기능 유지 확인 | 정상 작동 |
| ST-GCN → 카메라 | 실시간 추론 | 버퍼링 후 추론 |
| ST-GCN → 파일 | 동영상 추론 | 버퍼링 후 추론 |
| 모델 전환 | RF ↔ ST-GCN | 재시작 시 적용 |

### 6.3 성능 테스트

```bash
# FPS 측정
python main.py --measure-fps

# 목표:
# - Random Forest: 20+ FPS (기존 유지)
# - ST-GCN (GPU): 15+ FPS
# - ST-GCN (CPU): 10+ FPS
```

---

## 7. 향후 개선 계획

### 7.1 Pre-trained 모델 적용 (Phase 4)

```
목표: PYSKL Pre-trained → Fine-tuning → 성능 향상
예상 시기: 데이터 추가 수집 후
기대 효과: 84% → 90%+ 정확도 향상
```

### 7.2 추가 기능

| 우선순위 | 기능 | 설명 |
|---------|------|------|
| 높음 | 모델 앙상블 | RF + ST-GCN 결합 (Voting) |
| 중간 | 실시간 모델 전환 | GUI에서 즉시 전환 |
| 중간 | 신뢰도 임계값 설정 | 사용자 조절 가능 |
| 낮음 | 다중 사람 추적 | M > 1 지원 |

---

## 8. 체크리스트

### 작업 시작 전
- [ ] CUDA 사용 가능 여부 확인 (`nvidia-smi`)
- [ ] PyTorch 버전 확인 (`torch.__version__`)
- [ ] 기존 GUI 정상 작동 확인 (`python main.py`)
- [ ] ST-GCN 모델 파일 존재 확인 (`best_model_binary.pth`)

### Phase 1 완료 조건
- [ ] `stgcn/st_gcn.py` 복사 완료
- [ ] `stgcn/graph.py` 복사 완료
- [ ] `stgcn_inference.py` 작성 완료
- [ ] 단독 테스트 통과

### Phase 2 완료 조건
- [ ] `model_selection_dialog.py` 작성 완료
- [ ] `monitoring_page.py` 수정 완료
- [ ] Random Forest 기존 기능 유지 확인
- [ ] ST-GCN 실시간 추론 작동 확인

### Phase 3 완료 조건
- [ ] 메모리 누수 없음 확인
- [ ] FPS 목표 달성
- [ ] 에러 핸들링 완료
- [ ] WORK_LOG 작성 완료

---

## 9. 참고 자료

### 프로젝트 경로
```
기존 GUI: /home/gjkong/dev_ws/yolo/myproj/gui/
ST-GCN:   /home/gjkong/dev_ws/st_gcn/
모델:     /home/gjkong/dev_ws/st_gcn/checkpoints/best_model_binary.pth
테스트 영상: /home/gjkong/dev_ws/st_gcn/data_integrated/fall-*.mp4
```

### 관련 문서
- `WORK_LOG_20260204.md` - 어제 작업 기록
- `st_gcn.py` - 모델 구조 정의
- `graph.py` - 스켈레톤 그래프 정의

---

**작성자:** Claude (Anthropic AI Assistant)  
**작성일:** 2026-02-05  
**버전:** v1.0  
**문서 타입:** 구현 계획서 (Implementation Plan)
