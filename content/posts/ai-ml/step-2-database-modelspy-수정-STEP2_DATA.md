---
title: "Step 2: database_models.py 수정"
date: 2026-03-21
draft: true
tags: ["ai-ml"]
categories: ["ai-ml"]
description: "**파일**: `database_models.py` **클래스**: `EventLog` **메소드**: `create()`"
---

# Step 2: database_models.py 수정

## 📋 수정 내용

**파일**: `database_models.py`  
**클래스**: `EventLog`  
**메소드**: `create()`

---

## ✏️ 수정 사항

### 1. 파라미터 추가

**Before:**
```python
def create(self, user_id: int, event_type: str, confidence: float = None,
           hip_height: float = None, spine_angle: float = None,
           hip_velocity: float = None, **kwargs) -> Optional[int]:
```

**After:**
```python
def create(self, user_id: int, event_type: str, confidence: float = None,
           hip_height: float = None, spine_angle: float = None,
           hip_velocity: float = None, accuracy: float = None, **kwargs) -> Optional[int]:
                                        ⭐ 추가!
```

---

### 2. SQL INSERT 쿼리 수정

**Before:**
```python
query = """
INSERT INTO event_logs (user_id, event_type_id, event_status, confidence,
                       hip_height, spine_angle, hip_velocity, video_path,
                       thumbnail_path, notes)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
```

**After:**
```python
query = """
INSERT INTO event_logs (user_id, event_type_id, event_status, confidence,
                       hip_height, spine_angle, hip_velocity, accuracy,
                       video_path, thumbnail_path, notes)
                                                  ⭐ 추가!
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    ⭐ %s 하나 추가!
```

---

### 3. params 튜플 수정

**Before:**
```python
params = (
    user_id, event_type_id, kwargs.get('event_status', '발생'),
    confidence, hip_height, spine_angle, hip_velocity,
    kwargs.get('video_path'), kwargs.get('thumbnail_path'),
    kwargs.get('notes')
)
```

**After:**
```python
params = (
    user_id, event_type_id, kwargs.get('event_status', '발생'),
    confidence, hip_height, spine_angle, hip_velocity, accuracy,
                                                       ⭐ 추가!
    kwargs.get('video_path'), kwargs.get('thumbnail_path'),
    kwargs.get('notes')
)
```

---

## 📂 생성된 파일

```
/mnt/user-data/outputs/database_models_STEP2.py
```

**수정 내용:**
- Line 177: accuracy 파라미터 추가
- Line 189: docstring 업데이트
- Line 193: SQL INSERT 쿼리에 accuracy 컬럼 추가
- Line 199: params 튜플에 accuracy 값 추가

---

## 🔄 배포 방법

```bash
# 1. 백업
cd /home/gjkong/dev_ws/yolo/myproj
cp database_models.py database_models.py.backup_step2

# 2. 새 파일로 교체
cp ~/Downloads/database_models_STEP2.py database_models.py

# 3. 확인
grep -A 5 "def create" database_models.py | grep accuracy
```

---

## ✅ 테스트 방법

```python
# Python으로 테스트
from database_models import DatabaseManager, EventLog

db = DatabaseManager()
event_model = EventLog(db)

# accuracy 파라미터로 이벤트 생성
event_id = event_model.create(
    user_id=1,
    event_type='정상',
    confidence=0.85,
    hip_height=100.0,
    accuracy=92.5,  # ⭐ 새로 추가된 파라미터!
    event_status='발생',
    notes='Test with accuracy'
)

print(f"✅ Event ID: {event_id}")

# DB 확인
query = "SELECT event_id, confidence, accuracy FROM event_logs WHERE event_id = %s"
result = db.execute_query(query, (event_id,))
print(f"✅ Saved: {result}")
```

**예상 결과:**
```
✅ Event ID: 12345
✅ Saved: [{'event_id': 12345, 'confidence': 0.85, 'accuracy': 92.5}]
```

---

## 📊 변경 요약

| 항목 | 수정 전 | 수정 후 |
|------|---------|---------|
| 파라미터 수 | 6개 | 7개 (+accuracy) |
| SQL 컬럼 수 | 10개 | 11개 (+accuracy) |
| VALUES 수 | 10개 (%s) | 11개 (%s) |

---

## ⚠️ 주의사항

1. **Step 1 필수**: `event_logs` 테이블에 `accuracy` 컬럼이 먼저 추가되어야 합니다!
   ```sql
   SHOW COLUMNS FROM event_logs LIKE 'accuracy';
   ```

2. **하위 호환성**: `accuracy=None`이 기본값이므로 기존 코드도 작동합니다
   ```python
   # 기존 코드 (accuracy 없이) - 작동 OK
   event_model.create(user_id=1, event_type='정상', confidence=0.8)
   
   # 새 코드 (accuracy 포함) - 작동 OK
   event_model.create(user_id=1, event_type='정상', confidence=0.8, accuracy=92.5)
   ```

---

## 🎯 다음 단계

Step 2 완료 후:
- [ ] Step 3: monitoring_page.py 수정 (accuracy 저장)
- [ ] Step 4: dashboard_page.py 수정 (정상 탐지율 표시)

---

**Step 2 완료!** ✅

다음 단계를 진행하시겠어요? 😊
