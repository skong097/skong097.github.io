---
title: "AI Agent 프로젝트 셋업 가이드"
date: 2026-03-21
draft: true
tags: ["ros2"]
categories: ["ros2"]
description: "**작성일**: 2026-02-18 **목적**: 기존 프로젝트와 완전 독립된 AI Agent 개발 환경 구축 ```"
---

# AI Agent 프로젝트 셋업 가이드

**작성일**: 2026-02-18  
**목적**: 기존 프로젝트와 완전 독립된 AI Agent 개발 환경 구축

---

## 1. 최종 디렉토리 구조

```
~/dev_ws/
└── ai_agent/                          ← 루트 (신규)
    ├── README.md
    ├── .gitignore
    │
    └── guard_brain_agent/             ← Phase 1: Tool Use 에이전트
        ├── venv/                      ← 독립 가상환경 (git 제외)
        ├── main.py                    ← FastAPI 서버 진입점
        ├── agent.py                   ← 에이전트 코어 (판단 루프)
        ├── tools.py                   ← 도구 함수 (Mock 데이터)
        ├── prompts.py                 ← LLM 프롬프트 템플릿
        ├── config.py                  ← 설정값 (모델명, 포트 등)
        ├── requirements.txt
        └── logs/                      ← 에이전트 실행 로그
            └── .gitkeep
```

---

## 2. 셋업 명령어 (터미널 순서대로 실행)

### Step 1 — 루트 디렉토리 생성

```bash
cd ~/dev_ws
mkdir -p ai_agent/guard_brain_agent/logs
cd ai_agent
```

### Step 2 — 루트 README + .gitignore 생성

```bash
cat > README.md << 'EOF'
# AI Agent Projects

기존 프로젝트와 완전 독립된 AI Agent 실험 공간.

## 프로젝트 목록
- `guard_brain_agent/` — Phase 1: Tool Use 에이전트 (LLM + FastAPI)

## 철학
- Phase 1: 단일 자동화 도구 개발 (Tool Use)
- Phase 2: ReAct 루프 에이전트
- Phase 3: Multi-Agent 협업 Flow
EOF

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.pyo
.Python

# 가상환경
venv/
.venv/
env/

# 로그
logs/*.log
logs/*.jsonl

# 환경변수
.env
*.env

# IDE
.vscode/settings.json
.idea/

# OS
.DS_Store
Thumbs.db
EOF
```

### Step 3 — guard_brain_agent 가상환경 생성

```bash
cd ~/dev_ws/ai_agent/guard_brain_agent

# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip
```

### Step 4 — requirements.txt 작성 및 패키지 설치

```bash
cat > requirements.txt << 'EOF'
# Web Framework
fastapi==0.115.0
uvicorn==0.30.6

# LLM
ollama==0.3.3

# Utilities
python-dotenv==1.0.1
pydantic==2.8.2
EOF

pip install -r requirements.txt
```

### Step 5 — logs 디렉토리 유지용 파일 생성

```bash
touch logs/.gitkeep
```

### Step 6 — 설치 확인

```bash
python -c "import fastapi, uvicorn, ollama, pydantic; print('✅ 모든 패키지 설치 완료')"
```

---

## 3. VSCode에서 열기

```bash
# guard_brain_agent 디렉토리를 VSCode로 열기
cd ~/dev_ws/ai_agent/guard_brain_agent
code .

# VSCode에서 인터프리터 선택:
# Ctrl+Shift+P → "Python: Select Interpreter"
# → ./venv/bin/python 선택
```

---

## 4. 가상환경 활성화 / 비활성화

```bash
# 활성화 (작업 시작할 때)
source ~/dev_ws/ai_agent/guard_brain_agent/venv/bin/activate

# 비활성화 (작업 끝날 때)
deactivate
```

---

## 5. Ollama 모델 확인

```bash
# 설치된 모델 목록 확인
ollama list

# EXAONE 없으면 pull (guard_brain 에서 쓰던 모델)
# ollama pull exaone3.5:7.8b

# 서버 실행 확인
ollama serve &
```

---

## 6. 셋업 완료 후 구조 확인

```bash
cd ~/dev_ws/ai_agent
find . -not -path "*/venv/*" -not -path "*/__pycache__/*" | sort
```

**예상 출력:**
```
.
./README.md
./.gitignore
./guard_brain_agent
./guard_brain_agent/logs
./guard_brain_agent/logs/.gitkeep
./guard_brain_agent/requirements.txt
./guard_brain_agent/venv/   ← 가상환경 (내부 생략)
```

---

## 7. 다음 단계

셋업 완료 후 아래 파일들을 순서대로 작성:

| 순서 | 파일 | 내용 |
|------|------|------|
| 1 | `config.py` | 모델명, 포트, 설정값 |
| 2 | `tools.py` | Mock 도구 함수 5개 |
| 3 | `prompts.py` | LLM 시스템 프롬프트 |
| 4 | `agent.py` | Tool Use 에이전트 코어 |
| 5 | `main.py` | FastAPI 서버 |

---

## 주의사항

- `venv/` 는 절대 기존 프로젝트 venv와 공유하지 않음
- 기존 `home_guard_bot/` 코드 import 금지
- Mock 데이터로만 동작 — ROS2, 실제 센서 연동 없음
