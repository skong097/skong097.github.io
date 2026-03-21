---
title: "Stephen Kong's Development Principles & Patterns"
date: 2026-03-21
draft: true
tags: ["vision-ai", "yolo"]
categories: ["vision-ai"]
description: "**작성일:** 2026-02-05 **프로젝트:** Home Safe Solution - 낙상 감지 시스템 **목적:** 일관된 개발 원칙 및 패턴 유지"
---

# Stephen Kong's Development Principles & Patterns

**작성일:** 2026-02-05  
**프로젝트:** Home Safe Solution - 낙상 감지 시스템  
**목적:** 일관된 개발 원칙 및 패턴 유지

---

## 📋 목차

1. [개발 환경](#개발-환경)
2. [보안 원칙](#보안-원칙)
3. [코딩 원칙](#코딩-원칙)
4. [프로젝트 구조](#프로젝트-구조)
5. [데이터베이스 설계](#데이터베이스-설계)
6. [AI/ML 개발](#aiml-개발)
7. [UI/UX 원칙](#uiux-원칙)
8. [문서화 규칙](#문서화-규칙)
9. [버전 관리](#버전-관리)
10. [개발 프로세스](#개발-프로세스)

---

## 🖥️ 개발 환경

### **주요 도구**
- **IDE:** VSCode, Jupyter Notebook
- **언어:** Python (주력)
- **가상환경:** venv (`yolo_venv`)
- **버전 관리:** Git/GitHub

### **개발 경로**
```bash
/home/gjkong/dev_ws/yolo/myproj/
├── gui/                 # PyQt6 GUI 애플리케이션
├── models/              # YOLO 모델
├── models_integrated/   # Random Forest 모델
└── data/               # 학습 데이터
```

### **가상환경 활성화**
```bash
source /home/gjkong/dev_ws/yolo/yolo_venv/bin/activate
```

---

## 🔒 보안 원칙

### **1. 데이터베이스 접속 정보**

**개발 환경:**
```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'home_safe',
    'user': 'homesafe',
    'password': 'homesafe2026',
    'charset': 'utf8mb4'
}
```

**운영 환경:**
- 환경 변수 사용
- 설정 파일 분리 (.gitignore 추가)
- 암호화된 비밀번호

### **2. 사용자 인증**
- bcrypt 해싱 사용
- 평문 비밀번호 절대 저장 금지
- 세션 관리 철저

### **3. SQL Injection 방지**
```python
# ✅ GOOD: 파라미터 바인딩
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))

# ❌ BAD: 문자열 포맷팅
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

### **4. 민감 정보 관리**
- API 키는 환경 변수로
- 개인정보는 암호화
- 로그에 민감정보 출력 금지

---

## 💻 코딩 원칙

### **1. 코드 품질**

#### **주석 작성 (한글 선호)**
```python
# ✅ GOOD: 명확한 설명
def update_action(self, event_id: int, action_taken: str):
    """이벤트 조치 업데이트 (긴급 호출 전용)"""
    query = """
    UPDATE event_logs 
    SET action_taken = %s
    WHERE event_id = %s
    """
    return self.db.execute_update(query, (action_taken, event_id))

# ❌ BAD: 주석 없음
def update_action(self, event_id, action_taken):
    query = "UPDATE event_logs SET action_taken = %s WHERE event_id = %s"
    return self.db.execute_update(query, (action_taken, event_id))
```

#### **일관된 네이밍**
```python
# 변수: snake_case
event_id = 123
user_info = {'name': 'Stephen'}

# 클래스: PascalCase
class EventLog:
    pass

# 상수: UPPER_SNAKE_CASE
DB_CONFIG = {...}
MAX_RETRIES = 3
```

#### **타입 힌팅**
```python
# ✅ GOOD
def create(self, user_id: int, event_type: str, confidence: float = None) -> Optional[int]:
    pass

# ❌ BAD
def create(self, user_id, event_type, confidence=None):
    pass
```

### **2. 에러 처리**

```python
# ✅ GOOD: try-except 사용
try:
    event_id = self.event_log_model.create(...)
    if event_id:
        self.add_log(f"[DB] Event saved: ID={event_id}")
    else:
        self.add_log(f"[ERROR] Failed to save event")
except Exception as e:
    self.add_log(f"[ERROR] DB error: {str(e)}")
```

### **3. 로그 메시지**

```python
# ✅ GOOD: 구조화된 로그
self.add_log("[ALERT] Fallen detected! (70.0%)")
self.add_log("[DB] Event saved: ID=28615, Type=낙상, Conf=0.70, Acc=0.0%")
self.add_log("[ERROR] Failed to connect to camera")
self.add_log("[INFO] System started successfully")

# 로그 레벨
# [DEBUG] - 디버깅 정보
# [INFO] - 일반 정보
# [ALERT] - 경고 (낙상 감지 등)
# [ERROR] - 에러
# [DB] - 데이터베이스 작업
# [YOLO] - YOLO 관련
```

---

## 🏗️ 프로젝트 구조

### **디렉토리 구조**
```
myproj/
├── gui/
│   ├── main.py                  # 메인 앱
│   ├── monitoring_page.py       # 실시간 모니터링
│   ├── dashboard_page.py        # 대시보드
│   ├── database_models.py       # DB 모델
│   └── one_euro_filter.py       # 필터
├── models/
│   └── yolo11s-pose.pt         # YOLO 모델
├── models_integrated/
│   └── 3class/
│       └── random_forest_model.pkl
└── data/
    ├── videos/                  # 학습 비디오
    └── sequences/               # 시퀀스 데이터
```

### **모듈 분리**
- **GUI:** PyQt6 기반 인터페이스
- **모델:** AI/ML 모델 (YOLO, Random Forest)
- **데이터베이스:** MySQL 연동 (database_models.py)
- **유틸리티:** 필터, 헬퍼 함수

---

## 🗄️ 데이터베이스 설계

### **1. 테이블 설계 원칙**

#### **정규화**
- 중복 데이터 최소화
- 외래 키 제약조건 활용
- 인덱스 적절히 사용

#### **네이밍 규칙**
```sql
-- 테이블: snake_case, 복수형
event_logs
event_types
users

-- 컬럼: snake_case
event_id
event_type_id
occurred_at

-- 뷰: v_ 접두사
v_event_details
v_user_statistics
```

### **2. 주요 테이블**

#### **event_logs (이벤트 로그)**
```sql
CREATE TABLE event_logs (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    event_type_id INT NOT NULL,
    event_status ENUM('발생','조치중','완료'),
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence FLOAT,
    accuracy FLOAT COMMENT '정상 탐지율 (최근 5분 평균, %)',
    action_taken ENUM('없음','1차_메시지발송','2차_긴급호출'),
    action_result TEXT,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (event_type_id) REFERENCES event_types(event_type_id),
    INDEX idx_occurred_at (occurred_at),
    INDEX idx_event_status (event_status)
);
```

### **3. 뷰 활용**

```sql
-- v_event_details: 조인된 상세 정보
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

**장점:**
- 복잡한 JOIN 캡슐화
- 코드 간소화
- 보안 (특정 컬럼만 노출)

---

## 🤖 AI/ML 개발

### **1. 모델 선택 원칙**

#### **데이터 기반 의사결정**
```
데이터 양 < 500 시퀀스
→ 간단한 모델 (Random Forest, SVM)
→ 복잡한 모델 (ST-GCN, AS-GCN) 지양

데이터 양 > 1000 시퀀스
→ 딥러닝 모델 고려
```

#### **ROI (투자 대비 효과) 고려**
```
Random Forest: 93.19% 정확도
ST-GCN (예상): 95% 정확도
→ 추가 데이터 수집 비용: 950만원
→ 개발 시간: 18개월
→ 성능 향상: +2%
→ 결정: Random Forest 유지 ✅
```

### **2. 모델 학습**

#### **데이터 전처리**
```python
# YOLO Pose → Skeleton → Features
keypoints = yolo_model(frame)
filtered_kp = one_euro_filter.filter(keypoints)
features = extract_features(filtered_kp)
```

#### **학습 프로세스**
```python
# 1. 데이터 로드
X_train, y_train = load_sequences()

# 2. 모델 학습
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# 3. 검증
accuracy = model.score(X_test, y_test)
print(f"Test Accuracy: {accuracy:.2%}")

# 4. 저장
joblib.dump(model, 'random_forest_model.pkl')
```

### **3. 과적합 방지**

```python
# ✅ GOOD: 교차 검증
from sklearn.model_selection import cross_val_score
scores = cross_val_score(model, X, y, cv=5)
print(f"CV Scores: {scores.mean():.2%} ± {scores.std():.2%}")

# Train: 95%, Test: 63% → 과적합!
# → 데이터 추가 필요
```

---

## 🎨 UI/UX 원칙

### **1. 간결함 추구**

```python
# ✅ GOOD: 필요한 정보만
┌────────────────────────────────────────┐
│ Fall Detection                         │
├────────────────────────────────────────┤
│ [DANGER] Fallen                        │
│ Confidence: 70.0%                      │
│                                        │
│ Fallen: 70% ████████████████░░░░░░    │
└────────────────────────────────────────┘

# ❌ BAD: 불필요한 정보
┌────────────────────────────────────────┐
│ Fall Detection System v2.0             │
│ AI Model: Random Forest                │
│ Accuracy: 93.19%                       │
│ Frame: 28144                           │
│ FPS: 20                                │
│ ...                                    │
└────────────────────────────────────────┘
```

### **2. 색상 구분으로 직관성**

```python
# 정확도 색상
if accuracy >= 90:
    color = GREEN    # 안전
elif accuracy >= 70:
    color = YELLOW   # 주의
else:
    color = RED      # 위험

# 이벤트 타입 색상
if event_type == '정상':
    color = GREEN
elif event_type == '낙상중':
    color = ORANGE
elif event_type == '낙상':
    color = RED
```

### **3. 실시간 피드백**

```python
# ✅ GOOD: 즉각적인 피드백
- Emergency Call 클릭 → 팝업 즉시 표시
- 낙상 감지 → [ALERT] 로그 즉시 출력
- Dashboard → 5초마다 자동 갱신

# ❌ BAD: 지연된 피드백
- 버튼 클릭 → 3초 후 반응
- 이벤트 발생 → 로그 없음
```

---

## 📝 문서화 규칙

### **1. 일일 작업 로그**

**작성 시점:** 하루 마지막 코드 작성 후

**파일명 규칙:**
```
WORK_LOG_YYYYMMDD_FINAL.md
WORK_LOG_20260204_FINAL.md
```

**구조:**
```markdown
# 작업 일지 - YYYY년 MM월 DD일

## 📋 작업 개요
- 프로젝트: 
- 주요 작업:
- 작업 시간:
- 최종 상태:

## 🎯 주요 성과
1. ...
2. ...

## 📂 생성된 파일
- ...

## 🐛 트러블슈팅
- 문제:
- 원인:
- 해결:

## ✅ 완료 체크리스트
- [ ] ...

## 🚀 다음 단계
- ...
```

### **2. 코드 주석**

```python
# ✅ GOOD: 함수/클래스 docstring
def update_action(self, event_id: int, action_taken: str, 
                 action_result: str = None) -> bool:
    """
    이벤트 조치 업데이트 (긴급 호출 전용)
    
    Args:
        event_id: 이벤트 ID
        action_taken: 조치 내역 ('없음', '1차_메시지발송', '2차_긴급호출')
        action_result: 조치 결과 (선택)
    
    Returns:
        bool: 업데이트 성공 여부
    """
    query = """
    UPDATE event_logs 
    SET action_taken = %s, action_result = %s
    WHERE event_id = %s
    """
    params = (action_taken, action_result, event_id)
    return self.db.execute_update(query, params) > 0
```

### **3. 가이드 문서**

**배포 가이드:**
```markdown
## 🚀 배포 방법

### Step 1: 백업
```bash
cp file.py file.py.backup_YYYYMMDD
```

### Step 2: 파일 교체
```bash
cp ~/Downloads/file_new.py file.py
```

### Step 3: 캐시 삭제
```bash
rm -rf __pycache__
```

### Step 4: 재시작
```bash
python main.py
```
```

---

## 🔄 버전 관리

### **1. Git 사용 규칙**

#### **커밋 메시지 규칙**
```bash
# 형식: [타입] 간결한 설명

# 타입
[ADD] 새로운 기능 추가
[FIX] 버그 수정
[UPDATE] 기능 업데이트
[REFACTOR] 코드 리팩토링
[DOCS] 문서 수정
[TEST] 테스트 코드

# 예시
git commit -m "[ADD] Emergency Call 기능 추가"
git commit -m "[FIX] Detection Acc 표시 오류 수정"
git commit -m "[UPDATE] dashboard_page.py 조치 컬럼 추가"
git commit -m "[DOCS] WORK_LOG_20260204 작성"
```

#### **브랜치 전략**
```bash
main         # 운영 브랜치 (안정)
develop      # 개발 브랜치
feature/*    # 기능 개발 브랜치
hotfix/*     # 긴급 수정 브랜치

# 예시
git checkout -b feature/emergency-call
git checkout -b hotfix/accuracy-display
```

### **2. 백업 규칙**

#### **파일 백업**
```bash
# 수정 전 항상 백업
cp monitoring_page.py monitoring_page.py.backup_emergency
cp database_models.py database_models.py.backup_20260204

# 백업 파일 네이밍
{filename}.backup_{description}
{filename}.backup_{YYYYMMDD}
```

#### **데이터베이스 백업**
```bash
# 일일 백업
mysqldump -u homesafe -p home_safe > backup_20260204.sql

# 중요 작업 전 백업
mysqldump -u homesafe -p home_safe > backup_before_schema_change.sql
```

---

## 🔁 개발 프로세스

### **1. 새로운 기능 개발**

```
Step 1: 요구사항 명확히
→ 무엇을 만들 것인가?
→ 왜 필요한가?
→ 성공 기준은?

Step 2: 설계
→ DB 스키마 변경 필요?
→ API 설계
→ UI/UX 디자인

Step 3: 단계별 구현
→ Step 1: DB 수정
→ Step 2: 모델 수정
→ Step 3: GUI 수정
→ Step 4: 테스트

Step 4: 테스트
→ 단위 테스트
→ 통합 테스트
→ 사용자 테스트

Step 5: 배포
→ 백업
→ 파일 교체
→ 캐시 삭제
→ 재시작
→ 검증

Step 6: 문서화
→ 코드 주석
→ 가이드 문서
→ 작업 일지
```

### **2. 버그 수정**

```
Step 1: 재현
→ 언제 발생하는가?
→ 어떤 조건에서?
→ 재현 가능한가?

Step 2: 원인 파악
→ 로그 확인
→ 코드 검토
→ DB 상태 확인

Step 3: 수정
→ 최소한의 변경
→ 테스트 코드 작성
→ 회귀 테스트

Step 4: 배포
→ 핫픽스 브랜치
→ 긴급 배포
→ 모니터링
```

### **3. 코드 리뷰**

```
체크리스트:
□ 코드 가독성
□ 주석 충분한가?
□ 에러 처리 되어있나?
□ SQL Injection 방지?
□ 테스트 통과?
□ 성능 문제 없나?
□ 문서화 되었나?
```

---

## 🎯 핵심 원칙 요약

### **DO (해야 할 것)**

```
✅ 코드 작성 전 요구사항 명확히
✅ 단계별 접근 (Step-by-step)
✅ 항상 백업 후 수정
✅ 에러 처리 철저히
✅ 로그 메시지 명확하게
✅ 주석 작성 (한글 OK)
✅ 타입 힌팅 사용
✅ 파라미터 바인딩 (SQL Injection 방지)
✅ 테스트 후 배포
✅ 문서화 습관화
✅ 가상환경 사용
✅ Git 커밋 메시지 명확히
✅ 데이터 기반 의사결정
✅ ROI 고려
✅ 간결한 UI/UX
✅ 실시간 피드백
```

### **DON'T (하지 말아야 할 것)**

```
❌ 테스트 없이 배포
❌ 백업 없이 수정
❌ 주석 없는 코드
❌ 하드코딩된 비밀번호
❌ SQL Injection 취약점
❌ 과도한 UI 요소
❌ 불필요한 기능
❌ 문서화 미루기
❌ 커밋 메시지 대충
❌ 직접 main 브랜치 수정
❌ 에러 무시
❌ 로그 없이 작업
❌ 과적합 무시
❌ 데이터 없이 모델 선택
```

---

## 📊 프로젝트 현황 (2026-02-05 기준)

### **완성된 기능**
```
✅ 실시간 낙상 감지 (YOLO + Random Forest 93.19%)
✅ 5분 정확도 측정 시스템
✅ 영상 오버레이 (Detection Acc)
✅ DB 자동 저장 (event_logs)
✅ Emergency Call 기능
✅ Dashboard 7개 컬럼 (조치 포함)
✅ 실시간 자동 갱신 (5초)
```

### **기술 스택**
```
Frontend: PyQt6
Backend: Python 3.x
Database: MySQL 8.0
AI/ML: YOLO11s-pose, Random Forest
Tools: VSCode, Jupyter, Git
```

### **성능 지표**
```
모델 정확도: 93.19% (Random Forest)
실시간 FPS: 20 FPS
추론 시간: ~40ms/frame
정확도 측정: 5분 슬라이딩 윈도우
```

---

## 🔮 향후 계획

### **단기 (1-2주)**
- [ ] 추가 데이터 수집 (60개 비디오)
- [ ] 실제 긴급 연락처 SMS/이메일 발송
- [ ] 성능 최적화 (GPU 가속)

### **중기 (1-3개월)**
- [ ] 모바일 앱 개발
- [ ] 클라우드 배포
- [ ] 다중 사용자 지원

### **장기 (6개월+)**
- [ ] 딥러닝 모델 재검토 (데이터 충분 시)
- [ ] 추가 센서 통합 (웨어러블)
- [ ] 해외 시장 진출

---

## 📞 연락처 및 리소스

### **GitHub**
- Repository: `skong097/pai-1`
- 주요 파일: `myproject/`

### **문서 위치**
```
/home/gjkong/dev_ws/yolo/myproj/docs/
├── WORK_LOG_20260203_FINAL.md
├── WORK_LOG_20260204_FINAL.md
├── EMERGENCY_CALL_INTEGRATION_GUIDE.md
└── claude.md (이 문서)
```

### **백업 위치**
```
/home/gjkong/dev_ws/yolo/myproj/backups/
└── YYYYMMDD/
```

---

## 🙏 마무리

이 문서는 **살아있는 문서**입니다. 

프로젝트가 진행되면서:
- 새로운 원칙이 추가될 수 있습니다
- 기존 원칙이 수정될 수 있습니다
- 더 나은 방법이 발견될 수 있습니다

**중요한 것은:**
- 일관성 유지
- 지속적인 개선
- 문서화 습관

---

**작성:** Stephen Kong  
**날짜:** 2026-02-05  
**버전:** v1.0

**"좋은 코드는 스스로 설명하지만, 훌륭한 개발자는 여전히 문서를 작성한다."**
