---
title: "Step 4: dashboard_page.py 수정 (최종)"
date: 2026-03-21
draft: true
tags: ["dev-tools"]
categories: ["dev-tools"]
description: "**파일**: `dashboard_page.py` **목적**: 최근 이벤트 테이블에 **'정상 탐지율'** 컬럼 추가 **Before:**"
---

# Step 4: dashboard_page.py 수정 (최종)

## 📋 수정 내용

**파일**: `dashboard_page.py`  
**목적**: 최근 이벤트 테이블에 **'정상 탐지율'** 컬럼 추가

---

## ✏️ 수정 사항

### 1. 테이블 컬럼 수 변경 (6개 → 7개)

**Before:**
```python
def create_recent_events_table(self) -> QTableWidget:
    table = QTableWidget()
    table.setColumnCount(6)
    table.setHorizontalHeaderLabels([
        '발생시간', '사용자', '이벤트 유형', '상태', '신뢰도', '조치'
    ])
```

**After:**
```python
def create_recent_events_table(self) -> QTableWidget:
    table = QTableWidget()
    table.setColumnCount(7)  # ⭐ 6개 → 7개
    table.setHorizontalHeaderLabels([
        '발생시간', '사용자', '이벤트 유형', '상태', '신뢰도', '정상 탐지율', '조치'
                                                            ⭐ 추가!
    ])
```

---

### 2. 컬럼 크기 조정 수정

**Before:**
```python
header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 발생시간
header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 사용자
header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 이벤트 유형
header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 상태
header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 신뢰도
header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # 조치
```

**After:**
```python
header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 발생시간
header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 사용자
header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 이벤트 유형
header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 상태
header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 신뢰도
header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # ⭐ 정상 탐지율
header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)           # 조치
```

---

### 3. update_recent_events()에 정상 탐지율 데이터 추가

**Before:**
```python
# 신뢰도
confidence = f"{event['confidence']*100:.1f}%" if event['confidence'] else 'N/A'
self.recent_table.setItem(i, 4, QTableWidgetItem(confidence))

# 조치
action = event['action_taken'] if event['action_taken'] else '없음'
self.recent_table.setItem(i, 5, QTableWidgetItem(action))
```

**After:**
```python
# 신뢰도
confidence = f"{event['confidence']*100:.1f}%" if event['confidence'] else 'N/A'
self.recent_table.setItem(i, 4, QTableWidgetItem(confidence))

# ⭐ 정상 탐지율
accuracy = event.get('accuracy')
if accuracy is not None:
    accuracy_text = f"{accuracy:.1f}%"
    accuracy_item = QTableWidgetItem(accuracy_text)
    
    # 색상 구분
    if accuracy >= 90:
        accuracy_item.setForeground(QColor('#27ae60'))  # 녹색
    elif accuracy >= 70:
        accuracy_item.setForeground(QColor('#f39c12'))  # 주황
    else:
        accuracy_item.setForeground(QColor('#e74c3c'))  # 빨강
    
    self.recent_table.setItem(i, 5, accuracy_item)
else:
    self.recent_table.setItem(i, 5, QTableWidgetItem('N/A'))

# 조치
action = event['action_taken'] if event['action_taken'] else '없음'
self.recent_table.setItem(i, 6, QTableWidgetItem(action))  # ⭐ 5 → 6
```

---

## 🎨 색상 구분

```python
if accuracy >= 90:
    색상 = 녹색 (#27ae60)  ✅ 우수
elif accuracy >= 70:
    색상 = 주황 (#f39c12)  ⚠️ 보통
else:
    색상 = 빨강 (#e74c3c)  ❌ 주의
```

---

## 📊 최종 테이블 구조

```
┌────────────┬────────┬──────────┬──────┬────────┬────────────┬──────┐
│ 발생시간   │ 사용자 │ 이벤트   │ 상태 │ 신뢰도 │ 정상탐지율 │ 조치 │
│            │        │ 유형     │      │        │    ⭐      │      │
├────────────┼────────┼──────────┼──────┼────────┼────────────┼──────┤
│ 2026-02-03 │ 홍길동 │ 정상     │ 발생 │ 85.3%  │ 92.5%      │ 없음 │
│ 19:30:15   │        │          │      │        │ (녹색)     │      │
├────────────┼────────┼──────────┼──────┼────────┼────────────┼──────┤
│ 2026-02-03 │ 홍길동 │ 정상     │ 발생 │ 80.1%  │ 75.2%      │ 없음 │
│ 19:30:20   │        │          │      │        │ (주황)     │      │
├────────────┼────────┼──────────┼──────┼────────┼────────────┼──────┤
│ 2026-02-03 │ 홍길동 │ 낙상     │ 발생 │ 95.7%  │ 68.5%      │ 확인 │
│ 19:30:25   │        │(빨강)    │      │        │ (빨강)     │ 중   │
└────────────┴────────┴──────────┴──────┴────────┴────────────┴──────┘
```

---

## 📂 생성된 파일

```
/mnt/user-data/outputs/dashboard_page_STEP4_FINAL.py
```

**수정 내용:**
- Line 150: `setColumnCount(7)` - 컬럼 수 변경
- Line 151-153: 헤더 레이블에 '정상 탐지율' 추가
- Line 172-178: 컬럼 크기 조정 (7개)
- Line 373-391: 정상 탐지율 데이터 표시 추가

---

## 🔄 배포 방법

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 백업
cp dashboard_page.py dashboard_page.py.backup_step4

# 새 파일로 교체
cp ~/Downloads/dashboard_page_STEP4_FINAL.py dashboard_page.py
```

---

## ✅ 테스트 방법

### 1. GUI 실행
```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui
python main.py
```

### 2. Dashboard 페이지 이동

### 3. 최근 이벤트 테이블 확인

**예상 화면:**
```
최근 이벤트
┌────────────────────┬────────┬──────────┬──────┬────────┬────────────┬──────┐
│ 발생시간           │ 사용자 │ 이벤트   │ 상태 │ 신뢰도 │ 정상탐지율 │ 조치 │
├────────────────────┼────────┼──────────┼──────┼────────┼────────────┼──────┤
│ 2026-02-03 19:30:15│ 홍길동 │ 정상     │ 발생 │ 85.3%  │ 92.5%      │ 없음 │
│                    │        │          │      │        │ (녹색)     │      │
├────────────────────┼────────┼──────────┼──────┼────────┼────────────┼──────┤
│ 2026-02-03 19:30:20│ 홍길동 │ 정상     │ 발생 │ 80.1%  │ 93.1%      │ 없음 │
│                    │        │          │      │        │ (녹색)     │      │
└────────────────────┴────────┴──────────┴──────┴────────┴────────────┴──────┘
```

---

## 🎯 데이터 흐름

```
1. Monitoring Page
   → 정확도 계산 (5분 평균)
   → DB 저장 (accuracy 컬럼)
   
2. event_logs 테이블
   ┌─────────┬────────────┬──────────┐
   │ event_id│ confidence │ accuracy │
   ├─────────┼────────────┼──────────┤
   │ 22518   │ 0.853      │ 92.5     │ ⭐
   └─────────┴────────────┴──────────┘
   
3. Dashboard Page
   → DB 조회 (v_event_details 뷰)
   → 테이블에 표시
   → 색상 구분 (녹색/주황/빨강)
```

---

## 📝 코드 변경 요약

| 항목 | 변경 사항 |
|------|-----------|
| 컬럼 수 | 6개 → 7개 |
| 헤더 레이블 | '정상 탐지율' 추가 |
| 컬럼 인덱스 | 조치: 5 → 6 |
| 색상 로직 | 정확도 기반 색상 구분 추가 |
| 총 라인 수 | 376 → 395 (+19 lines) |

---

## ⚠️ 주의사항

1. **v_event_details 뷰 확인**
   ```sql
   -- accuracy 컬럼이 뷰에 포함되어 있는지 확인
   DESC v_event_details;
   
   -- 만약 없다면 뷰 재생성 필요
   DROP VIEW IF EXISTS v_event_details;
   CREATE VIEW v_event_details AS
   SELECT 
       el.*,
       u.name as user_name,
       et.type_name as event_type,
       et.severity
   FROM event_logs el
   JOIN users u ON el.user_id = u.user_id
   JOIN event_types et ON el.event_type_id = et.event_type_id;
   ```

2. **기존 데이터**: accuracy가 NULL인 이벤트는 'N/A'로 표시됩니다

3. **색상 표시**: 
   - 90% 이상: 녹색 (우수)
   - 70-90%: 주황 (보통)
   - 70% 미만: 빨강 (주의)

---

## 🎉 최종 완성!

### 전체 시스템 흐름:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Monitoring Page                                          │
│    - YOLO Pose 검출                                         │
│    - 낙상 예측 (Random Forest)                              │
│    - AccuracyTracker: 5분 정확도 계산                      │
│    - 영상 오버레이: "Detection Acc: 92.5%"                  │
│    - DB 저장: accuracy 포함                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. event_logs 테이블                                        │
│    ┌──────────┬────────────┬──────────┬──────────┐         │
│    │ event_id │ event_type │ confidence│ accuracy │         │
│    ├──────────┼────────────┼──────────┼──────────┤         │
│    │ 22518    │ 정상       │ 0.853    │ 92.5     │ ⭐      │
│    │ 22519    │ 정상       │ 0.801    │ 93.1     │ ⭐      │
│    └──────────┴────────────┴──────────┴──────────┘         │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Dashboard Page                                           │
│    최근 이벤트 테이블                                       │
│    ┌──────────┬──────┬────────┬────────────┬──────┐       │
│    │ 발생시간 │ 유형 │ 신뢰도 │ 정상탐지율 │ 조치 │       │
│    ├──────────┼──────┼────────┼────────────┼──────┤       │
│    │ 19:30:15 │ 정상 │ 85.3%  │ 92.5% ✅   │ 없음 │       │
│    │ 19:30:20 │ 정상 │ 80.1%  │ 93.1% ✅   │ 없음 │       │
│    └──────────┴──────┴────────┴────────────┴──────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ 완료 체크리스트

- [x] Step 1: event_logs 테이블에 accuracy 컬럼 추가
- [x] Step 2: database_models.py 수정 (accuracy 파라미터)
- [x] Step 3: monitoring_page.py 수정 (accuracy 저장)
- [x] Step 4: dashboard_page.py 수정 (정상 탐지율 표시)

---

**모든 단계 완료!** 🎉🎉🎉

파일을 배포하고 테스트해보세요! 😊
