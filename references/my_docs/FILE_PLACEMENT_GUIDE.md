# Home Safe Solution - 파일 배치 가이드

## 📁 정확한 디렉토리 구조

```
/home/gjkong/dev_ws/yolo/myproj/
│
├── gui/                                    # GUI 폴더 (기존)
│   ├── main.py                             # 기존 메인
│   ├── login_window.py                     # 기존 로그인
│   ├── main_window.py                      # 기존 메인 윈도우
│   ├── monitoring_page.py                  # 기존 모니터링
│   └── training_page.py                    # ⭐ 신규 추가
│
├── pipeline/                               # ⭐ 신규 폴더 생성
│   ├── __init__.py
│   ├── config.py
│   ├── data_ingest.py
│   ├── preprocessor.py
│   ├── trainer.py
│   ├── _stgcn_model.py
│   └── orchestrator.py
│
├── scripts/admin/
│   └── Model_Compare_Report/               # 기존 비교 리포트
│
├── models/                                 # 기존 모델 폴더
│   └── binary/
│       └── random_forest_model.pkl
│
├── dataset/                                # 데이터셋
│   ├── raw_videos/
│   │   ├── fall/
│   │   └── normal/
│   ├── binary/
│   │   ├── train.csv
│   │   ├── val.csv
│   │   └── test.csv
│   └── sequences/
│       └── *.npy
│
└── test_pipeline.py                        # ⭐ 테스트 스크립트 (루트)
```

## 🔧 설치 순서

### 1. pipeline/ 폴더 생성 및 파일 복사
```bash
cd /home/gjkong/dev_ws/yolo/myproj
mkdir -p pipeline

# 다운로드 받은 파일들 복사
cp ~/Downloads/pipeline/*.py ./pipeline/
```

### 2. training_page.py를 gui/ 폴더에 복사
```bash
cp ~/Downloads/training_page.py ./gui/
```

### 3. 테스트 스크립트 복사
```bash
cp ~/Downloads/test_pipeline.py ./
```

### 4. 테스트 실행
```bash
cd /home/gjkong/dev_ws/yolo/myproj
python test_pipeline.py
```

## ⚠️ config.py 경로 수정 필요

`pipeline/config.py` 파일 상단의 경로가 맞는지 확인:

```python
# ============================================================
# 경로 설정 (프로젝트 환경에 맞게 수정)
# ============================================================
BASE_DIR = Path("/home/gjkong/dev_ws")
PROJECT_DIR = BASE_DIR / "yolo/myproj"
ST_GCN_DIR = BASE_DIR / "st_gcn"
GUI_DIR = PROJECT_DIR / "gui"
DATASET_DIR = PROJECT_DIR / "dataset"
PIPELINE_DIR = PROJECT_DIR / "pipeline"
REPORT_DIR = PROJECT_DIR / "scripts/admin/Model_Compare_Report"
```

## 🔗 main_window.py 통합

`gui/main_window.py`에서:

```python
# import 추가
from training_page import TrainingPage

# MainWindow 클래스에서
class MainWindow(QMainWindow):
    def __init__(self, user_info):
        # ...
        self.training_page = TrainingPage()
        # stacked_widget 또는 tab에 추가
```

## 📋 실행 방법

```bash
# GUI 실행
cd /home/gjkong/dev_ws/yolo/myproj/gui
python main.py

# 또는 CLI로 파이프라인만 실행
cd /home/gjkong/dev_ws/yolo/myproj
python -m pipeline.orchestrator --help
```
