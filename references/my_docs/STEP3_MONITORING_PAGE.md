# Step 3: monitoring_page.py 수정

## 📋 수정 내용

**파일**: `monitoring_page.py`  
**메소드**: `save_fall_event()`  
**목적**: DB에 정확도(accuracy) 저장

---

## ✏️ 수정 사항

### 1. 정확도 가져오기 추가

**Before:**
```python
def save_fall_event(self, prediction, proba, features):
    # DB 저장
    confidence = float(proba[prediction])
    hip_height = features.get('hip_height', 0.0)
    
    # spine_angle, hip_velocity는 현재 계산 안 함 (None)
    event_id = self.event_log_model.create(
        user_id=self.user_info['user_id'],
        event_type=event_type,
        confidence=confidence,
        hip_height=hip_height,
        spine_angle=None,
        hip_velocity=None,
        event_status='발생',
        notes=f'AI Detection - {self.class_names[prediction]}'
    )
```

**After:**
```python
def save_fall_event(self, prediction, proba, features):
    # DB 저장
    confidence = float(proba[prediction])
    hip_height = features.get('hip_height', 0.0)
    
    # ⭐ 정확도 가져오기 (최근 5분 평균)
    accuracy = self.accuracy_tracker.get_accuracy()
    
    # spine_angle, hip_velocity는 현재 계산 안 함 (None)
    event_id = self.event_log_model.create(
        user_id=self.user_info['user_id'],
        event_type=event_type,
        confidence=confidence,
        hip_height=hip_height,
        spine_angle=None,
        hip_velocity=None,
        accuracy=accuracy,  # ⭐ 정확도 저장
        event_status='발생',
        notes=f'AI Detection - {self.class_names[prediction]}'
    )
```

---

### 2. 로그 메시지에 정확도 추가

**Before:**
```python
if event_id:
    if prediction == 0:
        self.safe_add_log(f"[DB] Normal saved (ID: {event_id})")
    else:
        self.safe_add_log(f"[DB] {event_type} saved (ID: {event_id})")
```

**After:**
```python
if event_id:
    if prediction == 0:
        self.safe_add_log(f"[DB] Normal saved (ID: {event_id}, Acc: {accuracy:.1f}%)")
    else:
        self.safe_add_log(f"[DB] {event_type} saved (ID: {event_id}, Acc: {accuracy:.1f}%)")
```

---

## 📊 동작 흐름

```
1. 낙상 감지 예측
   ↓
2. save_fall_event() 호출
   ↓
3. accuracy_tracker.get_accuracy() 
   → 최근 5분 평균 정확도 계산
   ↓
4. event_log_model.create(
      ...,
      accuracy=92.5,  # ⭐ DB에 저장
      ...
   )
   ↓
5. GUI 로그에 표시
   "[DB] Normal saved (ID: 12345, Acc: 92.5%)"
```

---

## 📂 생성된 파일

```
/mnt/user-data/outputs/monitoring_page_STEP3_FINAL.py
```

**수정 내용:**
- Line 888: `accuracy = self.accuracy_tracker.get_accuracy()` 추가
- Line 897: `accuracy=accuracy` 파라미터 추가
- Line 905, 908: 로그 메시지에 정확도 표시 추가

---

## 🔄 배포 방법

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 백업
cp monitoring_page.py monitoring_page.py.backup_step3

# 새 파일로 교체
cp ~/Downloads/monitoring_page_STEP3_FINAL.py monitoring_page.py
```

---

## ✅ 테스트 방법

### 1. GUI 실행
```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui
python main.py
```

### 2. Start 버튼 클릭

### 3. 로그 확인
```
[DB] Normal saved (ID: 22518, Acc: 92.5%)  ⭐ 정확도 표시!
[DB] Normal saved (ID: 22519, Acc: 93.1%)
[DB] Normal saved (ID: 22520, Acc: 92.8%)
```

### 4. DB 확인
```sql
SELECT event_id, event_type_id, confidence, accuracy 
FROM event_logs 
ORDER BY event_id DESC 
LIMIT 5;
```

**예상 결과:**
```
+----------+---------------+------------+----------+
| event_id | event_type_id | confidence | accuracy |
+----------+---------------+------------+----------+
|    22520 |             1 |      0.850 |    92.8  | ⭐
|    22519 |             1 |      0.823 |    93.1  | ⭐
|    22518 |             1 |      0.801 |    92.5  | ⭐
+----------+---------------+------------+----------+
```

---

## 🎯 정확도 값 의미

```python
accuracy = self.accuracy_tracker.get_accuracy()
```

- **값**: 0.0 ~ 100.0 (%)
- **의미**: 최근 5분 동안의 평균 정확도
- **계산**:
  ```
  정확도 = (정확한 예측 수 / 전체 예측 수) × 100
  
  예시:
  - 최근 5분 동안 3000개 예측
  - 정확한 예측: 2775개
  - 정확도 = (2775 / 3000) × 100 = 92.5%
  ```

---

## 📝 코드 변경 요약

| 항목 | 변경 사항 |
|------|-----------|
| 추가 코드 | `accuracy = self.accuracy_tracker.get_accuracy()` |
| 파라미터 추가 | `accuracy=accuracy` |
| 로그 수정 | `Acc: {accuracy:.1f}%` 추가 |
| 총 라인 수 | 1,129 → 1,132 (+3 lines) |

---

## ⚠️ 주의사항

1. **의존성**: Step 1, Step 2가 먼저 완료되어야 합니다!
   - Step 1: DB 컬럼 추가 ✅
   - Step 2: database_models.py 수정 ✅

2. **AccuracyTracker**: 이미 monitoring_page.py에 통합되어 있습니다
   ```python
   # Line 151
   self.accuracy_tracker = AccuracyTracker(window_seconds=300)
   ```

3. **초기값**: 시스템 시작 직후에는 accuracy가 0.0일 수 있습니다
   ```
   샘플 없음 → 0.0%
   1분 후 → ~85%
   5분 후 → ~90% (안정화)
   ```

---

## 🎉 예상 결과

### GUI 로그 화면:
```
[00:19:05] [YOLO] ✅ Keypoints: 1개!
[00:19:05] [INFO] Normal - 85.3%
[00:19:05] [DB] Normal saved (ID: 22518, Acc: 92.5%)  ⭐

[00:19:10] [YOLO] ✅ Keypoints: 1개!
[00:19:10] [INFO] Normal - 80.1%
[00:19:10] [DB] Normal saved (ID: 22519, Acc: 93.1%)  ⭐
```

### 영상 오버레이:
```
┌──────────────────────────┐
│  Recent 5 min            │
│  ─────────────────────── │
│  Detection Acc:  92.5%   │ ⭐ 실시간 표시
│  ████████████░░░░░░░░    │
└──────────────────────────┘
```

### DB 저장:
```sql
event_id: 22518
confidence: 0.850
accuracy: 92.5  ⭐ DB에 저장됨!
```

---

## 🎯 다음 단계

Step 3 완료 후:
- ✅ Step 1: DB 컬럼 추가 (완료)
- ✅ Step 2: database_models.py 수정 (완료)
- ✅ Step 3: monitoring_page.py 수정 (완료)
- ⏭️ **Step 4: dashboard_page.py 수정** (다음)

---

**Step 3 완료!** ✅

파일을 배포하고 테스트한 후 "Step 4 진행" 이라고 말씀해주세요! 😊
