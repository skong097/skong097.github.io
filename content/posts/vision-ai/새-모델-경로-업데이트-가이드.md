---
title: "새 모델 경로 업데이트 가이드"
date: 2026-03-21
draft: true
tags: ["vision-ai", "yolo"]
categories: ["vision-ai"]
description: "**날짜:** 2026-01-31 **목적:** 새로 학습한 모델(93.19% 정확도)을 실시간 감지에 적용 ```python"
---

# 새 모델 경로 업데이트 가이드

**날짜:** 2026-01-31  
**목적:** 새로 학습한 모델(93.19% 정확도)을 실시간 감지에 적용

---

## 📋 변경 요약

### 변경 전 (기존)
```python
# monitoring_page.py line 58
yolo_path = '/home/gjkong/dev_ws/yolo/myproj/models/yolo11s-pose.pt'

# monitoring_page.py line 75-76
model_path = '/home/gjkong/dev_ws/yolo/myproj/models/3class/random_forest_model.pkl'
feature_path = '/home/gjkong/dev_ws/yolo/myproj/models/3class/feature_columns.txt'
```

### 변경 후 (신규)
```python
# monitoring_page.py line 58
yolo_path = '/home/gjkong/dev_ws/yolo/myproj/models/yolo11s-pose.pt'  # 동일

# monitoring_page.py line 75-76
model_path = '/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/random_forest_model.pkl'
feature_path = '/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/feature_columns.txt'
```

**핵심 변경:**
- `models/3class/` → `models_integrated/3class/`

---

## 🔧 수정 방법

### 방법 1: 수동 수정 (추천)

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 텍스트 에디터로 열기
nano monitoring_page.py
# 또는
code monitoring_page.py
```

**수정 위치:**

#### Line 75-76 수정
```python
# 변경 전
model_path = '/home/gjkong/dev_ws/yolo/myproj/models/3class/random_forest_model.pkl'
feature_path = '/home/gjkong/dev_ws/yolo/myproj/models/3class/feature_columns.txt'

# 변경 후
model_path = '/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/random_forest_model.pkl'
feature_path = '/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/feature_columns.txt'
```

저장: `Ctrl + O` → `Enter` → `Ctrl + X`

---

### 방법 2: sed 명령어 (자동)

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 백업
cp monitoring_page.py monitoring_page.py.backup

# 자동 변경
sed -i 's|models/3class/|models_integrated/3class/|g' monitoring_page.py

# 확인
grep "models_integrated" monitoring_page.py
```

---

### 방법 3: 새 파일 적용 (가장 안전)

새로운 `monitoring_page.py` 파일을 제공하겠습니다.

---

## ✅ 변경 후 확인

### 1. 파일 존재 확인
```bash
# 새 모델 파일 확인
ls -lh /home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/random_forest_model.pkl
ls -lh /home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/feature_columns.txt

# 결과 예시:
# -rw-r--r-- 1 gjkong gjkong 2.1M Jan 31 10:30 random_forest_model.pkl
# -rw-r--r-- 1 gjkong gjkong 5.2K Jan 31 10:30 feature_columns.txt
```

### 2. 경로 변경 확인
```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 변경된 경로 확인
grep "models_integrated/3class" monitoring_page.py

# 출력 예시:
# model_path = '/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/random_forest_model.pkl'
# feature_path = '/home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/feature_columns.txt'
```

### 3. GUI 실행 테스트
```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui
python main.py
```

**확인 사항:**
- [ ] GUI 정상 실행
- [ ] 로그인 성공
- [ ] 실시간 모니터링 페이지 접속
- [ ] 콘솔에 "✅ 낙상 감지 모델 로드 성공!" 메시지 확인
- [ ] Feature 개수 확인 (181개)

---

## 🎯 기대 효과

### 변경 전 (기존 모델)
```
성능: 알 수 없음 (이전 학습)
데이터: 불명확
클래스: 3-Class
```

### 변경 후 (새 모델)
```
성능: 93.19% ⭐⭐⭐⭐⭐
데이터: 정상 40개 + 낙상 30개 (균형)
클래스: 3-Class (Normal, Falling, Fallen)

클래스별 성능:
- Normal:  98.5% (오탐 1.5%)
- Falling: 76.6% 
- Fallen:  92.1%
```

---

## 🚨 트러블슈팅

### 문제 1: 모델 로드 실패
```
오류: FileNotFoundError: ... models_integrated/3class/random_forest_model.pkl

해결:
1. 모델 파일 존재 확인
   ls /home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/

2. 파일이 없으면 재학습
   cd /home/gjkong/dev_ws/yolo/myproj
   python run_training_pipeline.py
```

### 문제 2: Feature 개수 불일치
```
오류: Feature 개수가 다릅니다 (예상: 181, 실제: XXX)

해결:
1. feature_columns.txt 확인
   wc -l /home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/feature_columns.txt

2. 파일 내용 확인
   head /home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/feature_columns.txt
```

### 문제 3: GUI 실행 안 됨
```
오류: ModuleNotFoundError: No module named 'joblib'

해결:
pip install joblib
```

### 문제 4: 경로 변경 안 됨
```
확인:
grep "models/3class" monitoring_page.py

출력 있으면 → 아직 변경 안 됨
출력 없으면 → 변경 완료
```

---

## 📝 변경 체크리스트

- [ ] 1. monitoring_page.py 백업
- [ ] 2. Line 75-76 수정
- [ ] 3. 파일 저장
- [ ] 4. 새 모델 파일 존재 확인
- [ ] 5. 경로 변경 확인 (grep)
- [ ] 6. GUI 실행 테스트
- [ ] 7. 모델 로드 메시지 확인
- [ ] 8. 실시간 감지 테스트

---

## 🎯 테스트 시나리오

### 1. 정상 활동 테스트
```
시나리오:
- 서 있기
- 앉기
- 걷기
- 눕기 (침대/소파)

기대 결과:
✅ Normal로 분류
✅ 초록색 표시
✅ 오경보 없음
```

### 2. 낙상 시뮬레이션
```
시나리오:
- 천천히 주저앉기
- 빠르게 넘어지기 (안전하게!)

기대 결과:
✅ Falling → Fallen 전환
✅ 주황색 → 빨강색
✅ 이벤트 로그 기록
```

### 3. 오탐 확인
```
시나리오:
- 빠르게 앉기
- 물건 줍기
- 신발 신기

기대 결과:
✅ Normal 유지
✅ 오탐률 1.5% 이하
```

---

## 📊 성능 모니터링

### 실시간 로그 확인
```bash
# GUI 실행 후 콘솔 출력 확인
cd /home/gjkong/dev_ws/yolo/myproj/gui
python main.py 2>&1 | tee monitoring.log

# 로그에서 확인할 내용:
# - "✅ 낙상 감지 모델 로드 성공!"
# - "Feature: 181개"
# - 예측 결과 (Normal/Falling/Fallen)
# - Confidence 값
```

### 데이터베이스 확인
```sql
-- 이벤트 로그 확인
SELECT 
    occurred_at,
    event_type,
    confidence,
    notes
FROM event_logs
ORDER BY occurred_at DESC
LIMIT 10;
```

---

## 🔄 롤백 방법

문제 발생 시 이전 모델로 되돌리기:

```bash
cd /home/gjkong/dev_ws/yolo/myproj/gui

# 백업에서 복원
cp monitoring_page.py.backup monitoring_page.py

# 또는 직접 수정
sed -i 's|models_integrated/3class/|models/3class/|g' monitoring_page.py
```

---

## 📚 참고 정보

### 모델 파일 정보
```
경로: /home/gjkong/dev_ws/yolo/myproj/models_integrated/3class/

파일:
- random_forest_model.pkl    (2.1 MB)
- feature_columns.txt         (5.2 KB)

학습 데이터:
- 정상: 40개 (adl-01~40)
- 낙상: 30개 (fall-01~30)
- 총 70개 비디오

성능:
- Accuracy:  93.19%
- Precision: 93.14%
- Recall:    93.19%
- F1-Score:  93.03%
```

### Feature 정보
```
총 181개 피처:
- 정적 피처: 64개 (관절 각도, 높이, BBox)
- 동적 피처: 117개 (속도, 가속도, 통계)

중요 피처 (예상):
- hip_height
- spine_angle
- velocity_y
- acc_mag
- aspect_ratio
```

---

## 다음 단계

경로 수정 완료 후:

1. **실시간 테스트** (30분)
   - 정상 활동 테스트
   - 낙상 시뮬레이션
   - 오탐/미탐 확인

2. **성능 모니터링** (1주일)
   - 일일 사용 로그 수집
   - 오탐/미탐 사례 기록
   - 사용자 피드백 수집

3. **추가 개선** (필요시)
   - Falling 성능 개선 (76.6% → 85%+)
   - 알림 시스템 추가
   - 대시보드 고도화

---

**문서 끝**
