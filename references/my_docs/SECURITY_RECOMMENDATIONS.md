# 🔒 Home Safe Solution - 보안 적용 제안서

## 📋 프로젝트: vision_ai (Fall Detection System)
## 📅 작성일: 2026-01-30
## 🎯 GitHub: https://github.com/skong097/vision_ai

---

# 🚨 즉시 조치 필요 (Critical)

## 1. 하드코딩된 민감 정보 제거

### ⚠️ **1.1 데이터베이스 자격 증명**

#### **현재 상태 (위험):**
```python
# gui/database_models.py
config = {
    'host': 'localhost',
    'database': 'home_safe',
    'user': 'homesafe',
    'password': '*******'  # ❌ GitHub에 노출!
}
```

#### **위험도:** 🔴 **매우 높음**
- DB 접근 정보가 GitHub에 노출됨
- 악의적 사용자의 데이터베이스 접근 가능
- 사용자 개인정보, 이벤트 로그 유출 위험

#### **해결 방안:**

**Step 1: .env 파일 생성**
```bash
# 프로젝트 루트에 .env 파일 생성
cd /home/gjkong/dev_ws/yolo/myproj

cat > .env << 'EOF'
# Database Configuration
DB_HOST=localhost
DB_NAME=home_safe
DB_USER=homesafe
DB_PASSWORD=your_secure_password_here
DB_PORT=3306

# Security
SECRET_KEY=your-secret-key-here-use-random-string

# Application
DEBUG=False
LOG_LEVEL=INFO
EOF

chmod 600 .env  # 읽기/쓰기 권한 제한
```

**Step 2: database_models.py 수정**
```python
# gui/database_models.py
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self):
        # 환경 변수에서 읽기
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', 3306))
        }
        
        # 필수 값 검증
        if not all([self.config['database'], 
                    self.config['user'], 
                    self.config['password']]):
            raise ValueError(
                "Database credentials not found in environment variables.\n"
                "Please create .env file with DB_HOST, DB_NAME, DB_USER, DB_PASSWORD"
            )
        
        self.connection = None
        self.connect()
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            print(f"✅ Connected to database: {self.config['database']}")
        except mysql.connector.Error as err:
            print(f"❌ Database connection error: {err}")
            raise
```

**Step 3: .gitignore에 추가**
```bash
# .gitignore에 추가
echo ".env" >> .gitignore
echo "config.ini" >> .gitignore
```

**Step 4: 의존성 추가**
```bash
pip install python-dotenv
echo "python-dotenv==1.0.0" >> requirements.txt
```

---

### ⚠️ **1.2 하드코딩된 경로 제거**

#### **문제점:**
```python
# 약 15개 파일에서 발견됨
model_path = '/home/gjkong/dev_ws/yolo/myproj/models/yolo11s-pose.pt'
data_path = '/home/gjkong/dev_ws/yolo/myproj/data/'
```

**위험:**
- 다른 환경에서 실행 불가
- 사용자 경로가 GitHub에 노출 (보안 정보 유출)
- 이식성 저하

#### **해결 방안:**

**Step 1: .env에 경로 추가**
```bash
# .env
PROJECT_ROOT=/home/gjkong/dev_ws/yolo/myproj
MODEL_DIR=${PROJECT_ROOT}/models
DATA_DIR=${PROJECT_ROOT}/data
FEATURE_DIR=${PROJECT_ROOT}/features
```

**Step 2: config.py 생성**
```python
# gui/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트 자동 감지
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# 환경 변수 우선, 없으면 자동 감지
MODEL_DIR = Path(os.getenv('MODEL_DIR', PROJECT_ROOT / 'models'))
DATA_DIR = Path(os.getenv('DATA_DIR', PROJECT_ROOT / 'data'))
FEATURE_DIR = Path(os.getenv('FEATURE_DIR', PROJECT_ROOT / 'features'))
SKELETON_DIR = Path(os.getenv('SKELETON_DIR', PROJECT_ROOT / 'skeleton'))

# 모델 파일 경로
YOLO_POSE_MODEL = MODEL_DIR / 'yolo11s-pose.pt'
RF_3CLASS_MODEL = MODEL_DIR / '3class' / 'random_forest_model.pkl'
RF_BINARY_MODEL = MODEL_DIR / 'binary' / 'random_forest_model.pkl'

# 디렉토리 존재 확인
def ensure_directories():
    """필요한 디렉토리 생성"""
    for dir_path in [MODEL_DIR, DATA_DIR, FEATURE_DIR, SKELETON_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

ensure_directories()

# 디버그 정보
if os.getenv('DEBUG', 'False').lower() == 'true':
    print(f"📂 PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"📂 MODEL_DIR: {MODEL_DIR}")
    print(f"📂 DATA_DIR: {DATA_DIR}")
```

**Step 3: 사용 예시**
```python
# gui/monitoring_page.py (수정 후)
from config import YOLO_POSE_MODEL, RF_3CLASS_MODEL

class MonitoringPage(QWidget):
    def __init__(self, user_info, db):
        # Before: 하드코딩
        # self.yolo_model = YOLO('/home/gjkong/.../yolo11s-pose.pt')
        
        # After: config 사용
        self.yolo_model = YOLO(str(YOLO_POSE_MODEL))
        self.rf_model = joblib.load(str(RF_3CLASS_MODEL))
```

---

## 2. .gitignore 개선

### **현재 누락된 중요 파일들:**

```gitignore
# ============================================
# 민감 정보 (절대 GitHub에 올리면 안 됨!)
# ============================================
.env
.env.*
config.ini
*.key
*.pem
credentials.json
secrets.yaml

# ============================================
# 데이터베이스
# ============================================
*.db
*.sqlite
*.sqlite3
*.sql
db_backup/

# ============================================
# 개인정보 포함 가능 파일
# ============================================
# 비디오 파일 (얼굴 포함)
data/*.mp4
data/*.avi
data/*.mov

# 가속도계 데이터 (개인 활동 패턴)
accel/*.csv

# 레이블링 데이터 (개인 정보 포함 가능)
labeled/*.csv
labeled/visualizations/*.png

# 이벤트 로그 (개인 활동 기록)
logs/*.log
*.log

# ============================================
# 대용량 모델 파일
# ============================================
# YOLO 모델 (GitHub 100MB 제한)
models/*.pt
models/*.pth
!models/README.md

# Random Forest 모델
models/3class/*.pkl
models/binary/*.pkl
!models/3class/feature_columns.txt
!models/binary/feature_columns.txt

# ============================================
# Python 캐시 및 가상환경
# ============================================
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# ============================================
# IDE 설정 (개인 설정)
# ============================================
.vscode/
.idea/
*.swp
*.swo
*~

# ============================================
# OS 파일
# ============================================
.DS_Store
Thumbs.db
desktop.ini

# ============================================
# 데이터 파일
# ============================================
# 원본 데이터 (용량 큼)
data/raw/
data/processed/

# 추출된 특징 (재생성 가능)
features/*.csv
skeleton/*.csv

# 데이터셋 (재생성 가능)
dataset/3class/*.csv
dataset/binary/*.csv

# ============================================
# 임시 파일
# ============================================
*.tmp
*.bak
*.backup
temp/
tmp/

# ============================================
# Jupyter Notebook
# ============================================
.ipynb_checkpoints/
*.ipynb_checkpoints

# ============================================
# 테스트 결과
# ============================================
test_output/
test_results/
htmlcov/
.coverage
.pytest_cache/
```

---

## 3. 비밀번호 보안 강화

### ✅ **현재 상태: 양호 (bcrypt 사용 중)**

```python
# gui/login_window.py
import bcrypt

# 회원가입
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# 로그인
if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
    # 인증 성공
```

### 📈 **추가 개선 사항:**

#### **3.1 비밀번호 정책 강화**

```python
# gui/password_policy.py (새로 생성)
import re

class PasswordPolicy:
    """비밀번호 정책 검증"""
    
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    
    SPECIAL_CHARS = r'!@#$%^&*(),.?":{}|<>'
    
    @classmethod
    def validate(cls, password: str) -> tuple[bool, list[str]]:
        """비밀번호 검증
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # 길이 검사
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"최소 {cls.MIN_LENGTH}자 이상이어야 합니다")
        
        # 대문자 검사
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("대문자를 1개 이상 포함해야 합니다")
        
        # 소문자 검사
        if cls.REQUIRE_LOWERCASE and not re.search(r'[A-Z]', password):
            errors.append("소문자를 1개 이상 포함해야 합니다")
        
        # 숫자 검사
        if cls.REQUIRE_DIGIT and not re.search(r'[0-9]', password):
            errors.append("숫자를 1개 이상 포함해야 합니다")
        
        # 특수문자 검사
        if cls.REQUIRE_SPECIAL and not re.search(f'[{re.escape(cls.SPECIAL_CHARS)}]', password):
            errors.append(f"특수문자({cls.SPECIAL_CHARS})를 1개 이상 포함해야 합니다")
        
        # 일반적인 패턴 검사
        common_patterns = [
            (r'(.)\1{2,}', "같은 문자가 3번 이상 연속되면 안 됩니다"),
            (r'(012|123|234|345|456|567|678|789)', "연속된 숫자는 피해주세요"),
            (r'(abc|bcd|cde|def|efg|fgh)', "연속된 문자는 피해주세요"),
        ]
        
        for pattern, message in common_patterns:
            if re.search(pattern, password.lower()):
                errors.append(message)
        
        # 약한 비밀번호 체크
        weak_passwords = [
            'password', '12345678', 'qwerty', 'admin', 'letmein',
            'welcome', 'monkey', '1234567890', 'Password1!',
        ]
        
        if password.lower() in weak_passwords:
            errors.append("너무 흔한 비밀번호입니다")
        
        return (len(errors) == 0, errors)
    
    @classmethod
    def get_strength(cls, password: str) -> tuple[int, str]:
        """비밀번호 강도 측정
        
        Returns:
            (strength_score, strength_text)
            strength_score: 0~100
        """
        score = 0
        
        # 길이 (최대 40점)
        score += min(len(password) * 4, 40)
        
        # 문자 종류 (각 15점, 최대 60점)
        if re.search(r'[a-z]', password):
            score += 15
        if re.search(r'[A-Z]', password):
            score += 15
        if re.search(r'[0-9]', password):
            score += 15
        if re.search(f'[{re.escape(cls.SPECIAL_CHARS)}]', password):
            score += 15
        
        # 강도 분류
        if score < 30:
            return (score, '매우 약함')
        elif score < 50:
            return (score, '약함')
        elif score < 70:
            return (score, '보통')
        elif score < 90:
            return (score, '강함')
        else:
            return (score, '매우 강함')
```

#### **3.2 회원가입 화면에 적용**

```python
# gui/login_window.py (RegisterDialog 수정)
from password_policy import PasswordPolicy

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... 기존 코드 ...
        
        # 비밀번호 강도 표시 추가
        self.password_strength_label = QLabel()
        self.password_strength_label.setStyleSheet('font-size: 11px;')
        
        # 비밀번호 입력 시 실시간 검증
        self.password_input.textChanged.connect(self.on_password_changed)
    
    def on_password_changed(self, text):
        """비밀번호 변경 시 강도 표시"""
        if not text:
            self.password_strength_label.setText('')
            return
        
        score, strength = PasswordPolicy.get_strength(text)
        
        # 색상 설정
        colors = {
            '매우 약함': '#e74c3c',
            '약함': '#e67e22',
            '보통': '#f39c12',
            '강함': '#27ae60',
            '매우 강함': '#2ecc71',
        }
        
        color = colors.get(strength, '#95a5a6')
        self.password_strength_label.setText(f'강도: {strength} ({score}점)')
        self.password_strength_label.setStyleSheet(f'color: {color}; font-size: 11px;')
    
    def on_register_clicked(self):
        """회원가입 버튼 클릭"""
        # ... 기존 입력 검증 ...
        
        password = self.password_input.text()
        
        # 비밀번호 정책 검증 ✅
        is_valid, errors = PasswordPolicy.validate(password)
        if not is_valid:
            QMessageBox.warning(
                self,
                '비밀번호 오류',
                '비밀번호가 보안 정책을 만족하지 않습니다:\n\n' + '\n'.join(f'• {e}' for e in errors)
            )
            return
        
        # ... 나머지 회원가입 로직 ...
```

---

## 4. 로그인 보안 강화

### **4.1 로그인 시도 제한 (Brute Force 방어)**

```python
# gui/login_security.py (새로 생성)
from datetime import datetime, timedelta
from collections import defaultdict
import threading

class LoginSecurity:
    """로그인 보안 관리"""
    
    MAX_ATTEMPTS = 5  # 최대 시도 횟수
    LOCKOUT_MINUTES = 15  # 잠금 시간 (분)
    
    def __init__(self):
        self.attempts = defaultdict(list)  # {username: [attempt_time, ...]}
        self.lock = threading.Lock()
    
    def is_locked_out(self, username: str) -> tuple[bool, int]:
        """계정 잠금 확인
        
        Returns:
            (is_locked, remaining_minutes)
        """
        with self.lock:
            attempts = self.attempts[username]
            
            if not attempts:
                return (False, 0)
            
            # 최근 시도만 유지
            lockout_time = timedelta(minutes=self.LOCKOUT_MINUTES)
            recent_attempts = [
                t for t in attempts
                if datetime.now() - t < lockout_time
            ]
            self.attempts[username] = recent_attempts
            
            if len(recent_attempts) >= self.MAX_ATTEMPTS:
                oldest_attempt = min(recent_attempts)
                unlock_time = oldest_attempt + lockout_time
                remaining = (unlock_time - datetime.now()).seconds // 60
                return (True, remaining)
            
            return (False, 0)
    
    def record_attempt(self, username: str):
        """로그인 시도 기록"""
        with self.lock:
            self.attempts[username].append(datetime.now())
    
    def clear_attempts(self, username: str):
        """로그인 성공 시 초기화"""
        with self.lock:
            self.attempts[username] = []
    
    def get_remaining_attempts(self, username: str) -> int:
        """남은 시도 횟수"""
        with self.lock:
            recent = [
                t for t in self.attempts[username]
                if datetime.now() - t < timedelta(minutes=self.LOCKOUT_MINUTES)
            ]
            return max(0, self.MAX_ATTEMPTS - len(recent))
```

#### **로그인 화면에 적용:**

```python
# gui/login_window.py (수정)
from login_security import LoginSecurity

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.user_model = User(self.db)
        self.security = LoginSecurity()  # ✅ 추가
        self.init_ui()
    
    def on_login_clicked(self):
        """로그인 버튼 클릭"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # 입력 검증
        if not username or not password:
            QMessageBox.warning(self, '입력 오류', '아이디와 비밀번호를 입력하세요.')
            return
        
        # 계정 잠금 확인 ✅
        is_locked, remaining_minutes = self.security.is_locked_out(username)
        if is_locked:
            QMessageBox.critical(
                self,
                '계정 잠금',
                f'로그인 시도가 {LoginSecurity.MAX_ATTEMPTS}회를 초과했습니다.\n\n'
                f'{remaining_minutes}분 후에 다시 시도하세요.\n\n'
                f'보안을 위해 일시적으로 계정이 잠겼습니다.'
            )
            return
        
        # 로그인 시도
        user = self.user_model.authenticate(username, password)
        
        if user:
            # 성공 시 초기화 ✅
            self.security.clear_attempts(username)
            
            # 로그인 이력 기록
            self.user_model.record_login(user['user_id'])
            
            # 메인 화면으로
            self.login_success.emit(user)
            self.close()
        else:
            # 실패 시 기록 ✅
            self.security.record_attempt(username)
            
            # 남은 시도 횟수 표시
            remaining = self.security.get_remaining_attempts(username)
            
            if remaining > 0:
                QMessageBox.warning(
                    self,
                    '로그인 실패',
                    f'아이디 또는 비밀번호가 잘못되었습니다.\n\n'
                    f'남은 시도 횟수: {remaining}회'
                )
            else:
                QMessageBox.critical(
                    self,
                    '계정 잠금',
                    f'로그인 시도가 {LoginSecurity.MAX_ATTEMPTS}회를 초과했습니다.\n\n'
                    f'{LoginSecurity.LOCKOUT_MINUTES}분 후에 다시 시도하세요.'
                )
```

---

### **4.2 세션 타임아웃**

```python
# gui/main_window.py (수정)
from datetime import datetime, timedelta
from PyQt6.QtCore import QTimer

class MainWindow(QMainWindow):
    SESSION_TIMEOUT_MINUTES = 30  # 30분 무활동 시 자동 로그아웃
    
    def __init__(self, user_info: dict):
        super().__init__()
        self.user_info = user_info
        self.db = DatabaseManager()
        self.last_activity = datetime.now()  # ✅ 마지막 활동 시간
        
        self.init_ui()
        
        # 세션 타임아웃 타이머 ✅
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self.check_session_timeout)
        self.session_timer.start(60000)  # 1분마다 체크
    
    def check_session_timeout(self):
        """세션 타임아웃 체크"""
        timeout = timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)
        
        if datetime.now() - self.last_activity > timeout:
            QMessageBox.warning(
                self,
                '세션 만료',
                f'{self.SESSION_TIMEOUT_MINUTES}분 동안 활동이 없어\n'
                f'보안을 위해 자동 로그아웃됩니다.'
            )
            self.logout()
    
    def update_activity(self):
        """활동 시간 업데이트"""
        self.last_activity = datetime.now()
    
    def mousePressEvent(self, event):
        """마우스 클릭 시"""
        self.update_activity()
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """키보드 입력 시"""
        self.update_activity()
        super().keyPressEvent(event)
```

---

## 5. 데이터 보안

### **5.1 개인정보 보호**

#### **문제점:**
- 비디오 파일에 얼굴/신체 포함
- 이벤트 로그에 활동 패턴 기록
- 가속도계 데이터에 개인 활동 패턴

#### **해결 방안:**

**데이터 익명화:**
```python
# scripts/data_anonymization.py (새로 생성)
import cv2
import numpy as np

class DataAnonymizer:
    """데이터 익명화"""
    
    @staticmethod
    def blur_faces(frame: np.ndarray) -> np.ndarray:
        """얼굴 블러 처리"""
        # YOLO face detection 사용 (선택사항)
        # 또는 간단하게 상단 영역만 블러
        height = frame.shape[0]
        top_region = frame[:height//3, :]  # 상단 1/3 (얼굴 영역)
        top_region = cv2.GaussianBlur(top_region, (99, 99), 30)
        frame[:height//3, :] = top_region
        return frame
    
    @staticmethod
    def remove_metadata(video_path: str):
        """비디오 메타데이터 제거"""
        # ffmpeg 사용
        import subprocess
        output_path = video_path.replace('.mp4', '_anon.mp4')
        subprocess.run([
            'ffmpeg', '-i', video_path,
            '-map_metadata', '-1',  # 메타데이터 제거
            '-c:v', 'copy', '-c:a', 'copy',
            output_path
        ])
        return output_path
```

**저장 시 자동 익명화:**
```python
# gui/monitoring_page.py (비디오 저장 시)
from data_anonymization import DataAnonymizer

def save_fall_video(self, frames):
    """낙상 비디오 저장 (익명화 적용)"""
    anonymizer = DataAnonymizer()
    
    # 얼굴 블러 처리
    anonymized_frames = [
        anonymizer.blur_faces(frame)
        for frame in frames
    ]
    
    # 비디오 저장
    # ...
```

---

### **5.2 데이터베이스 암호화**

#### **민감 컬럼 암호화:**

```python
# gui/encryption.py (새로 생성)
from cryptography.fernet import Fernet
import os
import base64

class DataEncryption:
    """데이터 암호화"""
    
    def __init__(self):
        # 환경 변수에서 키 로드
        key = os.getenv('ENCRYPTION_KEY')
        
        if not key:
            # 키가 없으면 생성 (최초 1회만)
            key = Fernet.generate_key()
            print(f"⚠️ ENCRYPTION_KEY 생성됨. .env에 저장하세요:")
            print(f"ENCRYPTION_KEY={key.decode()}")
        else:
            key = key.encode()
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """데이터 암호화"""
        if not data:
            return None
        encrypted = self.cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """데이터 복호화"""
        if not encrypted_data:
            return None
        decoded = base64.b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(decoded)
        return decrypted.decode()
```

**적용 예시:**
```python
# gui/database_models.py
from encryption import DataEncryption

class User:
    def __init__(self, db):
        self.db = db
        self.encryption = DataEncryption()
    
    def create(self, username, password, name, gender, phone=None):
        """사용자 생성"""
        # 비밀번호는 bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # 전화번호는 암호화 ✅
        encrypted_phone = None
        if phone:
            encrypted_phone = self.encryption.encrypt(phone)
        
        query = """
        INSERT INTO users (username, password_hash, name, gender, phone_encrypted)
        VALUES (%s, %s, %s, %s, %s)
        """
        self.db.execute(query, (username, password_hash, name, gender, encrypted_phone))
    
    def get_phone(self, user_id):
        """전화번호 조회 (복호화)"""
        query = "SELECT phone_encrypted FROM users WHERE user_id = %s"
        result = self.db.fetch_one(query, (user_id,))
        
        if result and result['phone_encrypted']:
            return self.encryption.decrypt(result['phone_encrypted'])
        return None
```

---

## 6. 로깅 및 감사

### **6.1 보안 이벤트 로깅**

```python
# gui/security_logger.py (새로 생성)
import logging
from datetime import datetime
from pathlib import Path

class SecurityLogger:
    """보안 이벤트 로거"""
    
    def __init__(self):
        # 로그 디렉토리
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # 보안 로그 파일
        log_file = log_dir / 'security.log'
        
        # 로거 설정
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # 파일 핸들러 (일별 로테이션)
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10
        )
        
        # 포맷
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
    
    def log_login_success(self, username, ip='unknown'):
        """로그인 성공"""
        self.logger.info(f"LOGIN_SUCCESS | username={username} | ip={ip}")
    
    def log_login_failure(self, username, ip='unknown'):
        """로그인 실패"""
        self.logger.warning(f"LOGIN_FAILURE | username={username} | ip={ip}")
    
    def log_account_lockout(self, username):
        """계정 잠금"""
        self.logger.warning(f"ACCOUNT_LOCKOUT | username={username}")
    
    def log_password_change(self, username):
        """비밀번호 변경"""
        self.logger.info(f"PASSWORD_CHANGE | username={username}")
    
    def log_user_created(self, username, created_by):
        """사용자 생성"""
        self.logger.info(f"USER_CREATE | username={username} | by={created_by}")
    
    def log_user_deleted(self, username, deleted_by):
        """사용자 삭제"""
        self.logger.warning(f"USER_DELETE | username={username} | by={deleted_by}")
    
    def log_session_timeout(self, username):
        """세션 타임아웃"""
        self.logger.info(f"SESSION_TIMEOUT | username={username}")
    
    def log_unauthorized_access(self, username, resource):
        """권한 없는 접근"""
        self.logger.error(f"UNAUTHORIZED_ACCESS | username={username} | resource={resource}")
```

**적용:**
```python
# gui/login_window.py
from security_logger import SecurityLogger

class LoginWindow(QDialog):
    def __init__(self):
        # ...
        self.sec_logger = SecurityLogger()  # ✅
    
    def on_login_clicked(self):
        # ...
        user = self.user_model.authenticate(username, password)
        
        if user:
            self.sec_logger.log_login_success(username)  # ✅
            # ...
        else:
            self.sec_logger.log_login_failure(username)  # ✅
            # ...
```

---

## 7. 코드 보안

### **7.1 SQL Injection 방지**

#### ✅ **현재 상태: 양호 (Parameterized Queries 사용)**

```python
# 좋은 예 (현재 코드)
query = "SELECT * FROM users WHERE username = %s"
result = self.db.execute(query, (username,))  # ✅ 파라미터화

# 나쁜 예 (사용하면 안 됨!)
query = f"SELECT * FROM users WHERE username = '{username}'"  # ❌ SQL Injection 취약!
```

#### **추가 검증:**
모든 SQL 쿼리에서 파라미터화 사용 확인

---

### **7.2 Input Validation**

```python
# gui/input_validator.py (새로 생성)
import re

class InputValidator:
    """입력 검증"""
    
    @staticmethod
    def is_valid_username(username: str) -> bool:
        """사용자명 검증
        - 4~20자
        - 영문, 숫자, 언더스코어만
        """
        if not username:
            return False
        return bool(re.match(r'^[a-zA-Z0-9_]{4,20}$', username))
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """이메일 검증"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """전화번호 검증 (한국)"""
        # 010-1234-5678 또는 01012345678
        pattern = r'^01[0-9]-?[0-9]{3,4}-?[0-9]{4}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def sanitize_string(text: str) -> str:
        """문자열 정제 (XSS 방지)"""
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 특수문자 이스케이프
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        return text.strip()
```

**적용:**
```python
# gui/login_window.py (RegisterDialog)
from input_validator import InputValidator

def on_register_clicked(self):
    username = self.username_input.text().strip()
    
    # 사용자명 검증 ✅
    if not InputValidator.is_valid_username(username):
        QMessageBox.warning(
            self,
            '입력 오류',
            '사용자명은 4~20자의 영문, 숫자, 언더스코어만 사용 가능합니다.'
        )
        return
    
    # ...
```

---

## 8. 네트워크 보안 (향후 확장 시)

### **8.1 HTTPS 사용 (웹 서비스 배포 시)**

```python
# 향후 FastAPI 백엔드 구축 시
from fastapi import FastAPI
import uvicorn

app = FastAPI()

if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8000,
        ssl_keyfile='/path/to/key.pem',      # ✅ SSL 인증서
        ssl_certfile='/path/to/cert.pem',    # ✅ SSL 인증서
    )
```

### **8.2 API 인증 (JWT)**

```python
# 향후 API 구축 시
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

def verify_token(credentials = Depends(security)):
    """JWT 토큰 검증"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')
```

---

## 9. 배포 체크리스트

### **배포 전 확인사항:**

```bash
# ============================================
# 1. 환경 변수 설정 확인
# ============================================
[ ] .env 파일 생성 및 설정
[ ] ENCRYPTION_KEY 생성 및 저장
[ ] DB_PASSWORD 안전한 값으로 변경
[ ] SECRET_KEY 랜덤 생성

# ============================================
# 2. .gitignore 확인
# ============================================
[ ] .env 파일이 .gitignore에 포함됨
[ ] config.ini가 .gitignore에 포함됨
[ ] 민감 데이터 파일들이 제외됨
[ ] 개인정보 포함 파일들이 제외됨

# ============================================
# 3. GitHub 업로드 전 확인
# ============================================
[ ] git log로 커밋 이력 확인
[ ] 민감 정보가 커밋에 포함되지 않았는지 확인
[ ] README에 .env.example 추가

# ============================================
# 4. 보안 설정 확인
# ============================================
[ ] 비밀번호 정책 적용됨
[ ] 로그인 시도 제한 활성화됨
[ ] 세션 타임아웃 설정됨
[ ] 보안 로깅 활성화됨

# ============================================
# 5. 코드 보안 확인
# ============================================
[ ] SQL Injection 취약점 없음 (Parameterized Queries 사용)
[ ] XSS 취약점 없음 (Input Validation 적용)
[ ] 하드코딩된 경로 없음 (config 사용)
[ ] 하드코딩된 비밀번호 없음

# ============================================
# 6. 데이터 보안 확인
# ============================================
[ ] 민감 데이터 암호화 적용
[ ] 비디오 얼굴 블러 처리 (옵션)
[ ] 개인정보 수집 최소화
[ ] 데이터 보관 기간 정책 수립

# ============================================
# 7. 문서화
# ============================================
[ ] README 업데이트
[ ] .env.example 생성
[ ] 보안 정책 문서 작성
[ ] 설치 가이드 업데이트
```

---

## 10. .env.example 생성

```bash
# .env.example
# 이 파일을 .env로 복사하고 실제 값으로 변경하세요

# Database Configuration
DB_HOST=localhost
DB_NAME=home_safe
DB_USER=homesafe
DB_PASSWORD=your_secure_password_here
DB_PORT=3306

# Security
SECRET_KEY=generate_random_string_here
ENCRYPTION_KEY=generate_with_Fernet_generate_key

# Application
DEBUG=False
LOG_LEVEL=INFO

# Project Paths (선택사항, 자동 감지 가능)
# PROJECT_ROOT=/path/to/your/project
# MODEL_DIR=${PROJECT_ROOT}/models
# DATA_DIR=${PROJECT_ROOT}/data

# Session
SESSION_TIMEOUT_MINUTES=30

# Login Security
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_MINUTES=15
```

---

## 📋 적용 우선순위

### 🔴 **즉시 (Critical)**
1. ✅ `.env` 파일 생성 및 DB 자격 증명 이동
2. ✅ `.gitignore` 업데이트 (민감 파일 제외)
3. ✅ 하드코딩된 경로 제거 (`config.py` 생성)
4. ✅ GitHub에서 이미 업로드된 민감 정보 확인 및 제거

### 🟡 **중요 (High)**
5. ✅ 비밀번호 정책 강화
6. ✅ 로그인 시도 제한
7. ✅ 세션 타임아웃
8. ✅ 보안 로깅

### 🟢 **권장 (Medium)**
9. ✅ 민감 데이터 암호화
10. ✅ Input Validation
11. ✅ 데이터 익명화
12. ✅ 배포 체크리스트 작성

---

## 📦 필요한 패키지

```bash
pip install python-dotenv
pip install cryptography
pip install pyjwt  # (향후 API 구축 시)

# requirements.txt에 추가
echo "python-dotenv==1.0.0" >> requirements.txt
echo "cryptography==41.0.7" >> requirements.txt
```

---

## 🎯 다음 단계

1. `.env` 파일 생성 및 설정
2. `config.py` 생성
3. `database_models.py` 수정
4. `.gitignore` 업데이트
5. GitHub에 푸시 전 민감 정보 제거 확인

**수고하셨습니다!** 🔒✨
