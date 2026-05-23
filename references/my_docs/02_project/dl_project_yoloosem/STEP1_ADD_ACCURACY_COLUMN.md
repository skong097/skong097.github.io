# event_logs 테이블에 accuracy 컬럼 추가

## SQL 스크립트

```sql
-- event_logs 테이블에 accuracy 컬럼 추가
ALTER TABLE event_logs 
ADD COLUMN accuracy FLOAT DEFAULT NULL 
COMMENT '정상 탐지율 (최근 5분 평균, %)';
```

---

## 실행 방법

### **방법 1: MySQL 커맨드라인**

```bash
# MySQL 접속
mysql -u root -p

# 데이터베이스 선택
USE home_safe_db;

# 컬럼 추가
ALTER TABLE event_logs 
ADD COLUMN accuracy FLOAT DEFAULT NULL 
COMMENT '정상 탐지율 (최근 5분 평균, %)';

# 확인
DESCRIBE event_logs;

# 종료
exit;
```

---

### **방법 2: Python 스크립트로 실행**

```python
#!/usr/bin/env python3
"""
event_logs 테이블에 accuracy 컬럼 추가
"""

import mysql.connector
from mysql.connector import Error

def add_accuracy_column():
    try:
        # DB 연결
        connection = mysql.connector.connect(
            host='localhost',
            database='home_safe_db',
            user='root',
            password='your_password'  # 실제 비밀번호로 변경
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # accuracy 컬럼 추가
            alter_query = """
            ALTER TABLE event_logs 
            ADD COLUMN accuracy FLOAT DEFAULT NULL 
            COMMENT '정상 탐지율 (최근 5분 평균, %)'
            """
            
            cursor.execute(alter_query)
            connection.commit()
            
            print("✅ accuracy 컬럼 추가 완료!")
            
            # 테이블 구조 확인
            cursor.execute("DESCRIBE event_logs")
            columns = cursor.fetchall()
            
            print("\n현재 테이블 구조:")
            print("-" * 80)
            for col in columns:
                print(f"{col[0]:<20} {col[1]:<15} {col[2]}")
            
    except Error as e:
        print(f"❌ 오류 발생: {e}")
        
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("\n✅ DB 연결 종료")

if __name__ == "__main__":
    add_accuracy_column()
```

---

### **방법 3: database_models.py를 통해 실행**

```python
# database_models.py의 DatabaseManager 사용
from database_models import DatabaseManager

db = DatabaseManager()

# SQL 실행
alter_query = """
ALTER TABLE event_logs 
ADD COLUMN accuracy FLOAT DEFAULT NULL 
COMMENT '정상 탐지율 (최근 5분 평균, %)'
"""

try:
    db.execute_update(alter_query)
    print("✅ accuracy 컬럼 추가 완료!")
except Exception as e:
    print(f"❌ 오류: {e}")
```

---

## 예상 테이블 구조 (수정 후)

```
+-----------------+---------------+------+-----+---------+----------------+
| Field           | Type          | Null | Key | Default | Extra          |
+-----------------+---------------+------+-----+---------+----------------+
| event_id        | int           | NO   | PRI | NULL    | auto_increment |
| user_id         | varchar(50)   | NO   | MUL | NULL    |                |
| event_type_id   | int           | YES  | MUL | NULL    |                |
| occurred_at     | datetime      | NO   |     | CURRENT |                |
| confidence      | float         | YES  |     | NULL    |                |
| hip_height      | float         | YES  |     | NULL    |                |
| spine_angle     | float         | YES  |     | NULL    |                |
| hip_velocity    | float         | YES  |     | NULL    |                |
| event_status    | varchar(20)   | NO   |     | 발생    |                |
| action_taken    | text          | YES  |     | NULL    |                |
| notes           | text          | YES  |     | NULL    |                |
| accuracy        | float         | YES  |     | NULL    |                | ⭐ 새로 추가!
+-----------------+---------------+------+-----+---------+----------------+
```

---

## 확인 방법

```sql
-- 1. 컬럼이 추가되었는지 확인
DESCRIBE event_logs;

-- 2. accuracy 컬럼만 확인
SHOW COLUMNS FROM event_logs LIKE 'accuracy';

-- 3. 기존 데이터 확인 (accuracy는 NULL)
SELECT event_id, event_type_id, confidence, accuracy 
FROM event_logs 
ORDER BY event_id DESC 
LIMIT 5;
```

---

## 주의사항

1. **백업 권장**: 테이블 구조 변경 전 백업
   ```bash
   mysqldump -u root -p home_safe_db event_logs > event_logs_backup.sql
   ```

2. **NULL 허용**: 기존 데이터는 accuracy가 NULL로 설정됨

3. **기본값**: 새로 추가되는 데이터만 accuracy 값이 저장됨

---

## 다음 단계

Step 1 완료 후:
- [ ] Step 2: database_models.py 수정 (create 메소드에 accuracy 파라미터 추가)
- [ ] Step 3: monitoring_page.py 수정 (accuracy 저장)
- [ ] Step 4: dashboard_page.py 수정 (정상 탐지율 컬럼 표시)

---

**어느 방법으로 실행하시겠어요?** 😊

1. MySQL 커맨드라인
2. Python 스크립트
3. database_models.py 사용
