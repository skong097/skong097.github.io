---
title: "GUI 모델 정보 표시 통합 가이드"
date: 2026-03-21
draft: true
tags: ["ai-ml"]
categories: ["ai-ml"]
description: "GUI에서 현재 로드된 모델 정보를 명시적으로 표시하도록 개선합니다. | 파일 | 설명 | |------|------|"
---

# GUI 모델 정보 표시 통합 가이드

## 📋 개요

GUI에서 현재 로드된 모델 정보를 명시적으로 표시하도록 개선합니다.

---

## 📦 새 파일

| 파일 | 설명 |
|------|------|
| `model_selection_dialog_v2.py` | 개선된 모델 선택 다이얼로그 |
| `model_info_widget.py` | 모델 정보 표시 위젯 |
| `stgcn_inference_finetuned.py` | Fine-tuned 모델 추론 모듈 |

---

## 🔧 통합 방법

### Step 1: 파일 복사

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui/

# 새 파일 복사
cp ~/Downloads/model_selection_dialog_v2.py ./model_selection_dialog.py
cp ~/Downloads/model_info_widget.py ./
cp ~/Downloads/stgcn_inference_finetuned.py ./
```

---

### Step 2: monitoring_page.py 수정

#### 2-1. Import 추가 (파일 상단)

```python
# ========== 모델 정보 위젯 ==========
from model_info_widget import ModelInfoWidget, ModelInfoBar
```

#### 2-2. __init__에서 모델 정보 바 추가 (UI 초기화 부분)

기존 코드에서 메인 레이아웃 설정 부분을 찾아 수정:

```python
def __init__(self, ...):
    # ... 기존 코드 ...
    
    # ========== 모델 선택 ==========
    from model_selection_dialog import show_model_selection_dialog
    self.model_config = show_model_selection_dialog(self)
    self.model_type = self.model_config.get('type', 'random_forest')
    self.model_name = self.model_config.get('name', 'Random Forest')
    
    # ========== 메인 레이아웃 ==========
    main_layout = QVBoxLayout(self)
    
    # ⭐ 모델 정보 바 추가 (최상단)
    self.model_info_bar = ModelInfoBar()
    self.model_info_bar.set_model_info(self.model_config)
    main_layout.addWidget(self.model_info_bar)
    
    # ... 나머지 UI 코드 ...
```

#### 2-3. ST-GCN 모델 로드 분기 처리

`start_monitoring` 또는 `init_stgcn_model` 메서드에서:

```python
def init_stgcn_model(self):
    """ST-GCN 모델 초기화"""
    try:
        model_version = self.model_config.get('model_version', 'original')
        model_path = self.model_config.get('model_path')
        
        if model_version == 'finetuned':
            # Fine-tuned 모델 사용
            from stgcn_inference_finetuned import STGCNInference
            self.stgcn_model = STGCNInference(model_path=model_path)
            self.add_log(f"[INFO] ST-GCN Fine-tuned 모델 로드: {model_path}")
        else:
            # Original 모델 사용
            from stgcn_inference import STGCNInference
            self.stgcn_model = STGCNInference(model_path=model_path)
            self.add_log(f"[INFO] ST-GCN Original 모델 로드: {model_path}")
        
        # 모델 정보 바 업데이트
        self.model_info_bar.set_status("✅ 추론 준비 완료")
        
        return True
        
    except Exception as e:
        self.add_log(f"[ERROR] ST-GCN 로드 실패: {e}")
        self.model_info_bar.set_status("❌ 로드 실패")
        return False
```

#### 2-4. 추론 중 상태 업데이트 (선택)

`update_frame` 메서드에서 추론 시:

```python
# 추론 시작 시
self.model_info_bar.set_status("🔄 추론 중...")

# 결과 표시 시
if label == 'Fall':
    self.model_info_bar.set_status("🚨 낙상 감지!")
else:
    self.model_info_bar.set_status("✅ 정상")
```

---

### Step 3: 사이드바에 상세 정보 위젯 추가 (선택)

`init_sidebar` 또는 `init_info_panel`에서:

```python
def init_info_panel(self):
    # ... 기존 코드 ...
    
    # ⭐ 모델 상세 정보 위젯 추가
    self.model_info_widget = ModelInfoWidget()
    self.model_info_widget.set_model_info(self.model_config)
    sidebar_layout.addWidget(self.model_info_widget)
```

---

## 📐 UI 레이아웃 (예상)

```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 모델: ST-GCN (Fine-tuned) │ 정확도: 91.89% │ ✅ 로드됨   │  ← 상단 바
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    ┌────────────────────────┐  ┌─────────────────────────┐  │
│    │                        │  │ 🤖 현재 모델            │  │
│    │                        │  │ ─────────────────────── │  │
│    │   실시간 영상           │  │ ST-GCN (Fine-tuned)    │  │
│    │   + 스켈레톤            │  │ 🚀 ST-GCN Fine-tuned   │  │
│    │                        │  │ 정확도: 91.89%         │  │
│    │                        │  │ 📁 best_model_ft.pth   │  │
│    │                        │  │ ✅ 모델 로드됨          │  │
│    └────────────────────────┘  └─────────────────────────┘  │
│                                                             │
│    [OK] Normal                 Confidence: 87.3%            │
│    ⏳ ST-GCN 버퍼링... 45/60                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎨 모델별 표시

### Random Forest
```
🌲 모델: Random Forest │ 정확도: 93.19% │ ✅ 로드됨
```

### ST-GCN Original
```
📊 모델: ST-GCN (Original) │ 정확도: 84.21% │ ✅ 로드됨
📁 best_model_binary.pth
```

### ST-GCN Fine-tuned
```
🚀 모델: ST-GCN (Fine-tuned) │ 정확도: 91.89% │ ✅ 로드됨
📁 best_model_finetuned.pth
```

---

## ✅ 체크리스트

- [ ] `model_selection_dialog.py` 교체
- [ ] `model_info_widget.py` 복사
- [ ] `stgcn_inference_finetuned.py` 복사
- [ ] `monitoring_page.py` Import 추가
- [ ] `monitoring_page.py` 모델 정보 바 추가
- [ ] `monitoring_page.py` ST-GCN 분기 처리
- [ ] 테스트 실행

---

## 🧪 테스트

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui/

# 위젯 단독 테스트
python model_info_widget.py

# 다이얼로그 단독 테스트
python model_selection_dialog.py

# 전체 GUI 테스트
python main.py
```

---

**작성일:** 2026-02-05
