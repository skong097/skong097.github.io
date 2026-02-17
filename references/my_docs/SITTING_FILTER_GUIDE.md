# monitoring_page.py 수정 가이드
# 앉기 오판 방지 필터 적용 (Option A)

작성일: 2026-02-03
목적: Fallen 70% 오판 방지 (앉기 감지)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 수정 위치 1: 파일 상단 (import 아래, class 정의 전)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

위치: Line 35 (from database_models import DatabaseManager 아래)

추가할 코드:

```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⭐ 앉기 오판 방지 필터 (Option A) ⭐
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_sitting_posture(keypoints):
    """
    앉은 자세 감지
    
    Args:
        keypoints: (17, 3) numpy array [x, y, conf]
    
    Returns:
        bool: True if sitting
        float: sitting confidence (0-1)
    """
    try:
        # 키포인트 추출
        nose = keypoints[0, :2]
        left_shoulder = keypoints[5, :2]
        right_shoulder = keypoints[6, :2]
        left_hip = keypoints[11, :2]
        right_hip = keypoints[12, :2]
        left_knee = keypoints[13, :2]
        right_knee = keypoints[14, :2]
        
        # Confidence 확인
        key_confs = [
            keypoints[0, 2],   # nose
            keypoints[5, 2],   # left_shoulder
            keypoints[6, 2],   # right_shoulder
            keypoints[11, 2],  # left_hip
            keypoints[12, 2],  # right_hip
        ]
        
        if np.mean(key_confs) < 0.5:
            return False, 0.0
        
        # 중심점 계산
        shoulder_center = (left_shoulder + right_shoulder) / 2
        hip_center = (left_hip + right_hip) / 2
        
        # ===== 조건 1: 머리-골반 높이 차이 =====
        head_hip_height = abs(nose[1] - hip_center[1])
        sitting_score_1 = 0.0
        
        if head_hip_height > 150:
            sitting_score_1 = 1.0
        elif head_hip_height > 120:
            sitting_score_1 = 0.8
        elif head_hip_height > 100:
            sitting_score_1 = 0.5
        else:
            sitting_score_1 = 0.0
        
        # ===== 조건 2: 상체 각도 =====
        torso_vector = shoulder_center - hip_center
        torso_angle = np.arctan2(abs(torso_vector[1]), abs(torso_vector[0])) * 180 / np.pi
        
        sitting_score_2 = 0.0
        if 70 < torso_angle < 110:
            sitting_score_2 = 1.0
        elif 60 < torso_angle < 120:
            sitting_score_2 = 0.7
        elif 50 < torso_angle < 130:
            sitting_score_2 = 0.4
        else:
            sitting_score_2 = 0.0
        
        # ===== 조건 3: 무릎 위치 =====
        knee_above_hip = False
        if keypoints[13, 2] > 0.3 and keypoints[14, 2] > 0.3:
            left_knee_above = left_knee[1] < left_hip[1] - 20
            right_knee_above = right_knee[1] < right_hip[1] - 20
            knee_above_hip = left_knee_above or right_knee_above
        
        sitting_score_3 = 1.0 if knee_above_hip else 0.0
        
        # ===== 종합 판정 =====
        total_score = (
            sitting_score_1 * 0.5 +
            sitting_score_2 * 0.3 +
            sitting_score_3 * 0.2
        )
        
        is_sitting = total_score > 0.6
        
        return is_sitting, total_score
        
    except Exception as e:
        print(f"[ERROR] is_sitting_posture: {e}")
        return False, 0.0


def apply_sitting_filter(keypoints, prediction, proba, fallen_threshold=0.80):
    """
    Fallen 오판 방지 필터
    
    Args:
        keypoints: (17, 3) numpy array
        prediction: int (0=Normal, 1=Falling, 2=Fallen)
        proba: array [p_normal, p_falling, p_fallen]
        fallen_threshold: Fallen 판정 최소 임계값 (80%)
    
    Returns:
        filtered_prediction: int
        filtered_proba: array
        filter_message: str
    """
    # 1. Fallen이 아니면 필터 적용 안함
    if prediction != 2:
        return prediction, proba, None
    
    # 2. Fallen 확률이 임계값 미만이면 필터 적용 안함
    if proba[2] < fallen_threshold:
        return prediction, proba, None
    
    # 3. 앉은 자세인지 확인
    is_sit, sit_confidence = is_sitting_posture(keypoints)
    
    if is_sit and sit_confidence > 0.6:
        # 앉은 자세로 판단 → Fallen을 Normal로 재분류
        filtered_proba = proba.copy()
        
        filtered_proba[0] = proba[2] * 0.8  # Normal로 80%
        filtered_proba[2] = proba[2] * 0.2  # Fallen 20%
        filtered_proba[1] = proba[1]
        
        # 정규화
        total = filtered_proba.sum()
        filtered_proba /= total
        
        filtered_prediction = np.argmax(filtered_proba)
        
        message = f"Sitting detected (conf: {sit_confidence:.1%}) - Filtered Fallen → Normal"
        
        return filtered_prediction, filtered_proba, message
    
    # 4. 앉은 자세가 아니면 원본 유지
    return prediction, proba, None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 수정 위치 2: update_frame() 메소드 내부
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

찾기: "# Fallen 알림" 또는 "if prediction == 2:"

현재 코드 (대략 Line 550-580):

```python
# Random Forest 예측
prediction, proba, _ = self.predict_fall(dynamic_features)

# 예측 결과 표시
frame = self.draw_prediction(frame, prediction, proba)

# 우측 패널 업데이트
self.update_fall_status(prediction, proba)

# DB 저장
self.save_fall_event(prediction, proba, dynamic_features)

# Fallen 알림
if prediction == 2:
    self.add_log(f"[ALERT] Fallen detected! ({proba[2]:.1%})")
```

↓↓↓ 다음과 같이 변경 ↓↓↓

```python
# Random Forest 예측
prediction, proba, _ = self.predict_fall(dynamic_features)

# ⭐⭐⭐ 앉기 필터 적용! ⭐⭐⭐
filtered_prediction, filtered_proba, filter_msg = apply_sitting_filter(
    keypoints=filtered_keypoints,
    prediction=prediction,
    proba=proba,
    fallen_threshold=0.80  # 80% 이상만 Fallen
)

# 필터 메시지 로그
if filter_msg:
    self.add_log(f"[FILTER] {filter_msg}")

# 예측 결과 표시 (필터링된 결과 사용)
frame = self.draw_prediction(frame, filtered_prediction, filtered_proba)

# 우측 패널 업데이트 (필터링된 결과 사용)
self.update_fall_status(filtered_prediction, filtered_proba)

# DB 저장 (필터링된 결과 사용)
self.save_fall_event(filtered_prediction, filtered_proba, dynamic_features)

# Fallen 알림 (필터링 후에도 Fallen이면)
if filtered_prediction == 2:
    if filter_msg:
        # 필터를 통과했음에도 Fallen -> 진짜 낙상!
        self.add_log(f"[ALERT] ⚠️ Real Fallen detected! (passed sitting filter)")
    else:
        self.add_log(f"[ALERT] Fallen detected! ({filtered_proba[2]:.1%})")
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 수정 위치 3: __init__() 메소드 - 로그 메시지 추가
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

위치: Line 93-95 (모델 로드 성공 후)

현재:
```python
print(f"✅ 낙상 감지 모델 로드 성공! (93.19% 정확도)")
print(f"   Feature: {len(self.feature_columns)}개")
print(f"   경로: {model_path}")
```

추가:
```python
print(f"✅ 낙상 감지 모델 로드 성공! (93.19% 정확도)")
print(f"   Feature: {len(self.feature_columns)}개")
print(f"   경로: {model_path}")
print(f"✅ 앉기 오판 방지 필터 활성화! (Fallen threshold: 80%)")  # ⭐ 추가
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 요약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

총 3곳 수정:

1. ✅ 파일 상단: is_sitting_posture() + apply_sitting_filter() 함수 추가
2. ✅ update_frame(): 필터 적용 코드 추가 (예측 직후)
3. ✅ __init__(): 로그 메시지 추가

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 예상 효과
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before (현재):
- 실제: 앉아있음
- 예측: Fallen 70% ❌
- DB 저장: Fallen 이벤트 (오판)

After (필터 적용):
- 실제: 앉아있음
- 1차 예측: Fallen 70%
- 필터 감지: Sitting (85%)
- 최종 예측: Normal 70% ✅
- DB 저장: Normal 이벤트 (정상)
- 로그: [FILTER] Sitting detected - Filtered Fallen → Normal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



mysql -u root -p

USE home_safe_db;

ALTER TABLE event_logs 
ADD COLUMN accuracy FLOAT DEFAULT NULL 
COMMENT '정상 탐지율 (최근 5분 평균, %)';

DESCRIBE event_logs;

exit;

✅ Step 1: event_logs 테이블에 accuracy 컬럼 추가
✅ Step 2: database_models.py 수정 (accuracy 파라미터)
✅ Step 3: monitoring_page.py 수정 (accuracy 저장)
✅ Step 4: dashboard_page.py 수정 (정상 탐지율 표시)
✅ 뷰 재생성: v_event_details (accuracy 포함)





SELECT event_id, event_type_id, action_taken, action_result
FROM event_logs
WHERE action_taken = '2차_긴급호출'
ORDER BY event_id DESC
LIMIT 5;
```

**예상 결과:**
```
+----------+---------------+-----------------+-------------------------------------+
| event_id | event_type_id | action_taken    | action_result                       |
+----------+---------------+-----------------+-------------------------------------+
|    27318 |             3 | 2차_긴급호출    | 긴급 호출 발송 완료 (2026-02-04    |
|          |               |                 | 09:32:59)                           |
+----------+---------------+-----------------+-------------------------------------+
```

---

## 📊 **Dashboard 예상 화면**
```
최근 이벤트
┌────────────┬────────┬──────┬──────┬────────┬────────────┬─────────────┐
│ 발생시간   │ 사용자 │ 유형 │ 상태 │ 신뢰도 │ 정상탐지율 │ 조치        │
├────────────┼────────┼──────┼──────┼────────┼────────────┼─────────────┤
│ 09:32:57   │ 관리자 │ 낙상 │ 발생 │ 70.0%  │ 5.8%       │ 2차_긴급호출│ ⭐
│ 09:32:56   │ 관리자 │ 낙상 │ 발생 │ 70.0%  │ 5.8%       │ 없음        │
└────────────┴────────┴──────┴──────┴────────┴────────────┴─────────────┘











[DB] 낙상 saved (ID: 28615, Acc: 0.0%)
[10:03:38] [ALERT] Emergency Call activated!
[10:03:38] [DEBUG] YOLO 결과: 1개
[10:03:38] [ALERT] Fallen detected! (70.0%)
[10:03:38] [DB] Event saved: ID=28616, Type=낙상, Conf=0.70, Acc=0.0%
[10:03:38] [YOLO] ✅ Keypoints: 2개!
[10:03:38] [DB] 낙상 saved (ID: 28617, Acc: 0.0%)
[10:03:39] [ALERT] Emergency call confirmed!
[10:03:39] [DB] Emergency call logged: Event ID=28615
[10:03:39] [DB] 낙상 saved (ID: 28618, Acc: 0.0%)
[10:03:40] [DEBUG] YOLO 결과: 1개
[10:03:40] [ALERT] Fallen detected! (70.0%)
[10:03:40] [DB] Event saved: ID=28619, Type=낙상, Conf=0.70, Acc=0.0%
[10:03:40] [YOLO] ✅ Keypoints: 2개!
[10:03:40] [DB] 낙상 saved (ID: 28620, Acc: 0.0%)
[10:03:41] [DEBUG] YOLO 결과: 1개
[10:03:41] [ALERT] Fallen detected! (70.0%)
[10:03:41] [DB] Event saved: ID=28621, Type=낙상, Conf=0.70, Acc=0.0%
[10:03:41] [YOLO] ✅ Keypoints: 2개!
[10:03:41] [DB] 낙상 saved (ID: 28622, Acc: 0.0%)
[10:03:42] [INFO] 프레임: 2200
[10:03:42] [DB] 낙상 saved (ID: 28623, Acc: 0.0%)
[10:03:43] [DEBUG] YOLO 결과: 1개
[10:03:43] [ALERT] Fallen detected! (70.0%)
[10:03:43] [DB] Event saved: ID=28624, Type=낙상, Conf=0.70, Acc=0.0%











-- MySQL 접속
mysql -u root -p

USE home_safe_db;

-- 기존 뷰 삭제
DROP VIEW IF EXISTS v_event_details;

-- 새 뷰 생성 (accuracy 포함)
CREATE VIEW v_event_details AS
SELECT 
    el.*,
    u.name as user_name,
    et.type_name as event_type,
    et.severity
FROM event_logs el
JOIN users u ON el.user_id = u.user_id
JOIN event_types et ON el.event_type_id = et.event_type_id;

-- 확인
SELECT event_id, event_type, confidence, accuracy 
FROM v_event_details 
ORDER BY event_id DESC 
LIMIT 5;

exit;















