# 실시간 정확도 그래프 통합 가이드

## 📊 개요

monitoring_page.py에 실시간 정확도 그래프를 추가합니다.

**레이아웃 변경:**
- 기존: 2칼럼 (영상 70% | 정보 30%)
- 변경: 3칼럼 (영상 50% | 그래프 30% | 정보 20%)

---

## 🔧 수정 위치 (7단계)

### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### 1. 파일 상단 import 추가 (Line 10-20)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### 2. AccuracyGraphWidget 클래스 추가 (Line 200 근처, AccuracyMonitor 뒤)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# accuracy_graph_widget.py의 AccuracyGraphWidget 클래스 전체 복사


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### 3. __init__() 메소드에 추가 (Line 310)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def __init__(self, user_info: dict, db: DatabaseManager):
    # ... 기존 코드 ...
    
    # 정확도 모니터 초기화
    log_dir = '/home/gjkong/dev_ws/yolo/myproj/accuracy_logs'
    self.accuracy_monitor = AccuracyMonitor(save_dir=log_dir)
    
    # ⭐ 그래프 업데이트 타이머
    self.graph_update_interval = 1  # 1초마다
    self.last_graph_update = time.time()
    
    self.init_ui()


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### 4. init_ui() 메소드 수정 - 3칼럼 레이아웃 (Line 320)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def init_ui(self):
    """UI 초기화 - 3칼럼 레이아웃"""
    layout = QHBoxLayout(self)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)
    
    # 왼쪽: 영상 (50%)
    left_panel = self.create_video_panel()
    layout.addWidget(left_panel, 5)
    
    # ⭐ 중앙: 그래프 (30%)
    center_panel = self.create_graph_panel()
    layout.addWidget(center_panel, 3)
    
    # 오른쪽: 정보 (20%)
    right_panel = self.create_info_panel()
    layout.addWidget(right_panel, 2)


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### 5. create_graph_panel() 메소드 추가 (create_video_panel 뒤)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_graph_panel(self) -> QWidget:
    """그래프 패널 (중앙)"""
    panel = QWidget()
    panel.setStyleSheet("background-color: #2c3e50; border-radius: 10px;")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(10)
    
    # 타이틀
    title_label = QLabel("📊 실시간 정확도 추이")
    title_label.setFont(QFont('맑은 고딕', 12, QFont.Weight.Bold))
    title_label.setStyleSheet("color: white; padding: 5px;")
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title_label)
    
    # 그래프 위젯
    self.accuracy_graph = AccuracyGraphWidget(
        parent=panel,
        width=6,
        height=4,
        dpi=80,
        max_points=60  # 60초 = 1분
    )
    layout.addWidget(self.accuracy_graph)
    
    # 범례 설명
    legend_label = QLabel(
        "• 파란선: 전체 정확도\n"
        "• 녹색선: Normal\n"
        "• 주황선: Falling\n"
        "• 빨강선: Fallen\n"
        "━━━━━━━━━━━━━━━\n"
        "• 녹색 점선: 목표 (90%)\n"
        "• 주황 점선: 경고 (70%)"
    )
    legend_label.setFont(QFont('맑은 고딕', 8))
    legend_label.setStyleSheet("color: #ecf0f1; padding: 5px;")
    layout.addWidget(legend_label)
    
    return panel


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### 6. update_frame()에서 그래프 업데이트 (Line 680 근처)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # 정확도 기록
    class_name = self.class_names[filtered_prediction]
    self.accuracy_monitor.record_prediction(
        predicted_state=class_name,
        confidence=filtered_proba[filtered_prediction]
    )
    
    # 정확도 UI 업데이트
    self.update_accuracy_display()
    
    # ⭐ 그래프 업데이트 (1초마다)
    current_time = time.time()
    if current_time - self.last_graph_update >= self.graph_update_interval:
        self.update_accuracy_graph()
        self.last_graph_update = current_time


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### 7. update_accuracy_graph() 메소드 추가 (update_accuracy_display 뒤)
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def update_accuracy_graph(self):
    """정확도 그래프 업데이트 (1초마다)"""
    try:
        stats = self.accuracy_monitor.get_stats()
        
        # 경과 시간 (초)
        elapsed = stats['elapsed_time']
        
        # 정확도 데이터
        overall_acc = stats['overall_accuracy']
        class_acc = stats['class_accuracy']
        
        # 그래프 업데이트
        self.accuracy_graph.update_plot(
            timestamp=elapsed,
            overall_acc=overall_acc,
            class_acc=class_acc
        )
    except Exception as e:
        # 에러 무시 (그래프는 선택 기능)
        pass


### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
### 8. start_monitoring()에 추가
### ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def start_monitoring(self):
    try:
        self.add_log("[INFO] 웹캠 초기화 중...")
        
        # 카메라 열기
        self.cap = cv2.VideoCapture(2)  # USB 카메라
        
        if not self.cap.isOpened():
            self.add_log("❌ 웹캠을 열 수 없습니다")
            return
        
        # ... 기존 코드 ...
        
        # ⭐ 그래프 초기화
        if hasattr(self, 'accuracy_graph'):
            self.accuracy_graph.clear_plot()
        
        # 타이머 시작
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(50)  # 20 FPS
        
        # ... 기존 코드 ...


---

## 📐 레이아웃 변경 요약

### Before (2칼럼):
```
┌────────────────────┬──────────┐
│                    │          │
│                    │  정보    │
│      영상          │  패널    │
│     (70%)          │  (30%)   │
│                    │          │
└────────────────────┴──────────┘
```

### After (3칼럼):
```
┌──────────────┬──────────┬──────┐
│              │          │      │
│              │  그래프  │ 정보 │
│    영상      │  패널    │ 패널 │
│   (50%)      │  (30%)   │(20%) │
│              │          │      │
└──────────────┴──────────┴──────┘
```

---

## 🎨 그래프 디자인

### 색상:
- 배경: #2c3e50 (어두운 회색)
- 전체 정확도: #3498db (파랑, 굵은 선)
- Normal: #27ae60 (녹색)
- Falling: #f39c12 (주황)
- Fallen: #e74c3c (빨강)

### 기준선:
- 90%: 녹색 점선 (목표)
- 70%: 주황 점선 (경고)

### 업데이트:
- 1초마다 자동 갱신
- 최근 60초 데이터 표시

---

## 📊 예상 화면

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[영상 패널]            [그래프 패널]          [정보 패널]
                      
  ▶ Start  ⏹ Stop     📊 실시간 정확도 추이    ⚪ Standby
                      
  ┌─────────────┐      100% ┬─────────────    Ground Truth:
  │             │       90% ┼─ ─ ─ ─ ─ ─     ⚪ Normal
  │   웹캠      │       80% ┤                 ⚪ Falling
  │   영상      │       70% ┼─ ─ ─ ─ ─ ─     ⚪ Fallen
  │             │       60% ┤     📈         
  │  Frame:123  │       50% ┴─────────────    정확도: 92.5%
  │  YOLO: ON   │          0  20  40  60초    샘플: 148/160
  └─────────────┘      
                       • 파란선: 전체          Normal: 95%
  [DANGER] Fallen      • 녹색선: Normal        Falling: 85%
  Confidence: 70%      • 주황선: Falling       Fallen: 90%
                       • 빨강선: Fallen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ✅ 완료 체크리스트

- [ ] matplotlib import 추가
- [ ] AccuracyGraphWidget 클래스 추가
- [ ] __init__()에 그래프 타이머 변수 추가
- [ ] init_ui() 3칼럼으로 수정
- [ ] create_graph_panel() 메소드 추가
- [ ] update_frame()에 그래프 업데이트 추가
- [ ] update_accuracy_graph() 메소드 추가
- [ ] start_monitoring()에 그래프 초기화 추가

---

## 🧪 테스트 방법

### 1. 독립 테스트 (그래프만):
```bash
cd /mnt/user-data/outputs
python accuracy_graph_widget.py

# 60초 동안 랜덤 데이터로 그래프 시뮬레이션
```

### 2. 통합 테스트 (GUI 전체):
```bash
cd /home/gjkong/dev_ws/yolo/myproj
python main.py

# Start 버튼 클릭
# Ground Truth 선택
# 1초마다 그래프 업데이트 확인
```

---

## 📦 필요한 패키지

```bash
# matplotlib이 없다면 설치
pip install matplotlib --break-system-packages
```

---

## 💡 추가 기능 (선택사항)

### 그래프 저장 버튼:
```python
def save_graph(self):
    '''그래프 이미지로 저장'''
    filename = f'accuracy_graph_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    self.accuracy_graph.fig.savefig(filename, dpi=150, facecolor='#2c3e50')
    self.add_log(f"[SAVE] 그래프 저장: {filename}")
```

### 시간 범위 변경:
```python
# __init__()에서
self.accuracy_graph = AccuracyGraphWidget(
    max_points=120  # 2분
    # 또는
    max_points=300  # 5분
)
```
