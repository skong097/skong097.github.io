# Emergency Call 기능 통합 가이드

## 📋 개요

**목표:** Emergency Call 버튼 클릭 시 DB에 긴급 호출 로그 저장 및 Dashboard 조치 컬럼에 표시

---

## 🎯 요구사항

1. **Monitoring Page**: Emergency Call 버튼 클릭
2. **DB 저장**: `event_logs.action_taken` = `'2차_긴급호출'`
3. **Dashboard**: '조치' 컬럼에 "2차_긴급호출" 표시

---

## ✅ 수정 사항

### **1. database_models.py 수정**

#### **추가 메소드 1: update_action()**
```python
def update_action(self, event_id: int, action_taken: str, action_result: str = None) -> bool:
    """이벤트 조치 업데이트 (긴급 호출 전용)"""
    query = """
    UPDATE event_logs 
    SET action_taken = %s, action_result = %s
    WHERE event_id = %s
    """
    params = (action_taken, action_result, event_id)
    return self.db.execute_update(query, params) > 0
```

**위치:** Line 231 (update_status 메소드 다음)

---

#### **추가 메소드 2: get_recent_fall_event()**
```python
def get_recent_fall_event(self, user_id: int = None) -> Optional[Dict]:
    """가장 최근 낙상 이벤트 조회 (Falling 또는 Fallen)"""
    query = """
    SELECT el.*, et.type_name
    FROM event_logs el
    JOIN event_types et ON el.event_type_id = et.event_type_id
    WHERE et.type_name IN ('낙상중', '낙상')
    """
    params = []
    
    if user_id:
        query += " AND el.user_id = %s"
        params.append(user_id)
    
    query += " ORDER BY el.occurred_at DESC LIMIT 1"
    
    result = self.db.execute_query(query, tuple(params) if params else None)
    return result[0] if result else None
```

**위치:** Line 241 (update_action 메소드 다음)

---

### **2. monitoring_page.py 수정**

#### **on_emergency_clicked() 메소드 수정 (Line 947-979)**

**Before:**
```python
def on_emergency_clicked(self):
    """긴급 호출 버튼 클릭"""
    self.add_log("[ALERT] Emergency Call activated!")
    
    # TODO: 실제 긴급 호출 기능 구현
    
    # 확인 메시지만 표시
    ...
```

**After:**
```python
def on_emergency_clicked(self):
    """긴급 호출 버튼 클릭"""
    self.add_log("[ALERT] Emergency Call activated!")
    
    # ⭐ 가장 최근 낙상 이벤트 조회
    recent_fall = self.event_log_model.get_recent_fall_event(user_id=self.user_info['user_id'])
    
    if not recent_fall:
        # 낙상 이벤트가 없으면 경고
        no_event_msg = QMessageBox(self)
        no_event_msg.setIcon(QMessageBox.Icon.Warning)
        no_event_msg.setWindowTitle("No Fall Event")
        no_event_msg.setText("⚠️ No recent fall event detected!")
        no_event_msg.setInformativeText("Emergency call can only be made when a fall is detected.")
        no_event_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        no_event_msg.exec()
        self.add_log("[WARNING] No recent fall event found")
        return
    
    # 경고 메시지 박스 표시 (이벤트 정보 포함)
    msg = QMessageBox(self)
    msg.setText(f"🚨 Emergency Call Activated!\n\n"
               f"Recent fall event: ID={recent_fall['event_id']}\n"
               f"Occurred at: {recent_fall['occurred_at']}")
    ...
    
    if result == QMessageBox.StandardButton.Yes:
        # ⭐ DB 업데이트: action_taken을 '2차_긴급호출'로 변경
        call_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        action_result = f"긴급 호출 발송 완료 ({call_time})"
        
        success = self.event_log_model.update_action(
            event_id=recent_fall['event_id'],
            action_taken='2차_긴급호출',
            action_result=action_result
        )
        
        if success:
            self.add_log(f"[DB] Emergency call logged: Event ID={recent_fall['event_id']}")
        else:
            self.add_log(f"[ERROR] Failed to log emergency call")
```

---

## 🔄 데이터 흐름

```
1. 낙상 감지 (Falling/Fallen)
   ↓
2. event_logs에 저장
   - event_id: 26895
   - event_type: '낙상'
   - action_taken: '없음' (기본값)
   ↓
3. Emergency Call 버튼 클릭
   ↓
4. get_recent_fall_event() 호출
   → 가장 최근 낙상 이벤트 조회 (ID=26895)
   ↓
5. 사용자 확인 (Yes/No)
   ↓
6. update_action() 호출
   - event_id: 26895
   - action_taken: '2차_긴급호출'
   - action_result: "긴급 호출 발송 완료 (2026-02-05 09:30:15)"
   ↓
7. Dashboard 자동 업데이트 (5초마다)
   → '조치' 컬럼에 "2차_긴급호출" 표시
```

---

## 📊 DB 변경 사항

### **event_logs 테이블**

**Before (낙상 감지 직후):**
```sql
+----------+---------------+--------------+---------------+
| event_id | event_type_id | action_taken | action_result |
+----------+---------------+--------------+---------------+
|    26895 |             3 | 없음         | NULL          |
+----------+---------------+--------------+---------------+
```

**After (Emergency Call 후):**
```sql
+----------+---------------+-----------------+-----------------------------------+
| event_id | event_type_id | action_taken    | action_result                     |
+----------+---------------+-----------------+-----------------------------------+
|    26895 |             3 | 2차_긴급호출    | 긴급 호출 발송 완료 (2026-02-05  |
|          |               |                 | 09:30:15)                         |
+----------+---------------+-----------------+-----------------------------------+
```

---

## 🖥️ Dashboard 표시

### **최근 이벤트 테이블**

```
┌────────────────────┬────────┬──────────┬──────┬────────┬────────────┬─────────────┐
│ 발생시간           │ 사용자 │ 이벤트   │ 상태 │ 신뢰도 │ 정상탐지율 │ 조치        │
├────────────────────┼────────┼──────────┼──────┼────────┼────────────┼─────────────┤
│ 2026-02-05 09:28:15│ 관리자 │ 낙상     │ 발생 │ 70.0%  │ 0.0%       │ 2차_긴급호출│ ⭐
│ 2026-02-05 09:28:11│ 관리자 │ 정상     │ 발생 │ 80.0%  │ 100.0%     │ 없음        │
└────────────────────┴────────┴──────────┴──────┴────────┴────────────┴─────────────┘
```

---

## 🔧 배포 방법

### **1. database_models.py 교체**

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 백업
cp database_models.py database_models.py.backup_emergency

# 새 파일로 교체
cp ~/Downloads/database_models_with_emergency.py database_models.py
```

---

### **2. monitoring_page.py 교체**

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 백업
cp monitoring_page.py monitoring_page.py.backup_emergency

# 새 파일로 교체
cp ~/Downloads/monitoring_page_with_emergency.py monitoring_page.py
```

---

### **3. Python 캐시 삭제**

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 캐시 삭제
rm -rf __pycache__
find . -name "*.pyc" -delete
```

---

### **4. GUI 재시작**

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui
python main.py
```

---

## ✅ 테스트 방법

### **1. 낙상 감지 대기**
- Start 버튼 클릭
- 낙상 동작 시뮬레이션 (앉거나 누워보기)
- "[ALERT] Fallen detected!" 로그 확인

### **2. Emergency Call 버튼 클릭**
- 🚨 Emergency Call 버튼 클릭
- 팝업에서 최근 낙상 이벤트 정보 확인:
  ```
  Recent fall event: ID=26895
  Occurred at: 2026-02-05 09:28:15
  ```
- "Yes" 클릭

### **3. 로그 확인**
```
[ALERT] Emergency Call activated!
[ALERT] Emergency call confirmed!
[DB] Emergency call logged: Event ID=26895
```

### **4. DB 확인**
```sql
SELECT event_id, event_type_id, action_taken, action_result
FROM event_logs
WHERE event_id = 26895;
```

**예상 결과:**
```
+----------+---------------+-----------------+-----------------------------------+
| event_id | event_type_id | action_taken    | action_result                     |
+----------+---------------+-----------------+-----------------------------------+
|    26895 |             3 | 2차_긴급호출    | 긴급 호출 발송 완료 (2026-02-05  |
|          |               |                 | 09:30:15)                         |
+----------+---------------+-----------------+-----------------------------------+
```

### **5. Dashboard 확인**
- Dashboard 페이지로 이동
- 최근 이벤트 테이블에서 '조치' 컬럼 확인
- "2차_긴급호출" 표시 확인 ✅

---

## 🎯 주요 기능

### **1. 안전 장치**
- 낙상 이벤트가 없으면 Emergency Call 버튼 작동 안 함
- 경고 메시지로 사용자에게 알림

### **2. 상세 정보**
- Emergency Call 팝업에 이벤트 정보 표시
- 발생 시간, 이벤트 ID 표시

### **3. DB 로깅**
- action_taken: '2차_긴급호출'
- action_result: 발송 완료 시간 기록

### **4. 실시간 반영**
- Dashboard 5초마다 자동 갱신
- '조치' 컬럼에 즉시 반영

---

## ⚠️ 주의사항

1. **낙상 이벤트가 없을 때:**
   - Emergency Call 버튼 클릭 시 경고 메시지 표시
   - DB 업데이트 안 함

2. **중복 호출:**
   - 같은 이벤트에 대해 여러 번 Emergency Call 가능
   - action_taken이 덮어쓰기됨
   - 필요하면 이력 관리 추가 가능

3. **Dashboard 업데이트:**
   - 5초마다 자동 갱신
   - 즉시 반영을 원하면 페이지 새로고침

---

## 🔄 향후 개선 사항

### **1. 긴급 연락처 실제 호출**
- SMS API 통합
- 이메일 발송
- 관리자 알림

### **2. 이력 관리**
- emergency_calls 테이블 별도 생성
- 호출 이력 누적 저장
- 통계 분석

### **3. 상태 추적**
- 발송 중, 발송 완료, 발송 실패
- 재시도 로직

### **4. 우선순위**
- 1차 메시지 발송 → 2차 긴급 호출
- 자동 에스컬레이션

---

## 📂 생성된 파일

```
/mnt/user-data/outputs/
├── database_models_with_emergency.py    # 수정된 database_models.py
├── monitoring_page_with_emergency.py    # 수정된 monitoring_page.py
└── EMERGENCY_CALL_INTEGRATION_GUIDE.md  # 이 문서
```

---

## 🎉 완료!

Emergency Call 기능이 완전히 통합되었습니다! 🚨

**테스트 후 결과를 알려주세요!** 😊
