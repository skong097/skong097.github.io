---
title: "블로그 레퍼런스 자동 분류 체계 설계"
date: 2026-03-21
draft: true
tags: ["ros2", "nav2", "slam", "gazebo"]
categories: ["ros2"]
description: "**작성일**: 2026-02-17 **업데이트**: 2026-02-18 — `ai-agent` 카테고리 추가 **목적**: ~/dev_ws/blog/references 에 수집된 .md 파일을 기술 스택 카테고리별"
---

# 블로그 레퍼런스 자동 분류 체계 설계

**작성일**: 2026-02-17  
**업데이트**: 2026-02-18 — `ai-agent` 카테고리 추가  
**목적**: ~/dev_ws/blog/references 에 수집된 .md 파일을 기술 스택 카테고리별로 자동 분류

---

## 1. 카테고리 체계

Dashboard Skill Radar 도메인 8개 + **AI Agent 1개** + 콘텐츠 유형 3개 = **총 12개 카테고리**.

### 1-1. 기술 스택 → 블로그 카테고리 매핑

```
기술 스택 카테고리          → 블로그 카테고리 (태그)
─────────────────────────────────────────────
ROS2                       → ros2
AI/ML/DL                   → ai-ml (RF, ST-GCN, YOLO, LLM)
AI Agent                   → ai-agent (자동화 도구 → 협업 Flow)   ← NEW
Vision AI                  → vision-ai (Pose Estimation, Fall Detection)
Robotics                   → robotics (Kevin Patrol, 자율주행, SLAM)
AIOps/MLOps                → mlops (파이프라인, 학습 자동화)
Robot Network              → robot-network
Robot Security             → robot-security
Big Data                   → big-data
```

### 1-2. 기술 스택 카테고리 (8개)

| # | 카테고리 ID | 표시명 | 대상 기술 / 태그 |
|---|-----------|--------|-----------------|
| 1 | `ros2` | ROS2 | ROS2 노드, 토픽, Nav2, Gazebo, Launch, Action, Service |
| 2 | `ai-ml` | AI / ML / DL | RF, ST-GCN, LSTM, LLM, Ollama, EXAONE, 모델 튜닝 |
| 3 | `ai-agent` | AI Agent | 자동화 도구, Tool Use, 자율 판단, Guard Brain, LLM 기반 제어, 에이전트 협업 Flow |
| 4 | `vision-ai` | Vision AI | YOLO Pose, Pose Estimation, Fall Detection, OpenCV, 키포인트 |
| 5 | `robotics` | Robotics | Kevin Patrol, 자율주행, SLAM, A*, 경로 계획, 시뮬레이션 |
| 6 | `mlops` | AIOps / MLOps | 학습 파이프라인 자동화, 데이터 전처리, 모델 배포, 비교 실험 |
| 7 | `robot-network` | Robot Network | 로봇 통신, DDS, 멀티로봇 네트워크, Fleet 통신, 프로토콜 |
| 8 | `robot-security` | Robot Security | 로봇 보안, 인증, 암호화, 침입 감지, 보안관, 접근 제어 |
| 9 | `big-data` | Big Data | 대용량 데이터 처리, 로그 분석, 데이터 수집/저장, DB, 통계 |

### 1-3. 콘텐츠 유형 카테고리 (3개)

| # | 카테고리 ID | 표시명 | 대상 |
|---|-----------|--------|------|
| 10 | `dev-tools` | Dev Tools / GUI | PyQt6, Dashboard, 다크 테마, FastAPI, Hugo, 블로그 |
| 11 | `project` | Project Planning | 프로젝트 계획서, 로드맵, 전략 문서 |
| 12 | `worklog` | Work Log | 일일 작업 기록, 버그 수정 로그, 개발 일지 |

---

## 2. 분류 방법: 키워드 스코어링

### 2-1. 원리

각 카테고리에 가중치가 부여된 키워드 세트를 정의. md 파일 내용(제목 + 본문 앞부분)에서 키워드 출현 빈도를 카운트하여 **가장 높은 스코어의 카테고리**에 배정.

### 2-2. 스코어링 규칙

```
스코어 = (high 키워드 출현 × 3) + (medium 키워드 출현 × 2) + (low 키워드 출현 × 1)
```

- 제목(파일명 + 첫 번째 # 헤더)에서 발견 시 **가중치 2배**
- 본문은 **앞 3000자**만 스캔 (성능 + 핵심 내용 집중)
- 동점 시 카테고리 우선순위: vision-ai > ai-agent > ai-ml > robotics > ros2 > mlops > robot-network > robot-security > big-data > dev-tools > project > worklog

### 2-3. 복수 카테고리 허용

스코어 1위와 2위 차이가 30% 이내면 **보조 카테고리**로 함께 태깅.

```
예: kevin_patrol_mocksim_optimization_log.md
  → robotics (1위, 스코어 24)
  → dev-tools (2위, 스코어 18)  ← 차이 25% → 보조 태그 포함

예: home-safe-solution-vision-ai-project.md
  → vision-ai (1위, 스코어 32)
  → ai-ml (2위, 스코어 28)  ← 차이 12.5% → 보조 태그 포함

예: LLM_ROS_보안관_개발계획서.md
  → robot-security (1위, 스코어 20)
  → ros2 (2위, 스코어 16)  ← 차이 20% → 보조 태그 포함

예: guard_brain_fastapi.md
  → ai-agent (1위, 스코어 22)
  → ros2 (2위, 스코어 17)  ← 차이 22% → 보조 태그 포함
```

---

## 3. 키워드 세트 (12개 카테고리)

### ros2
- **high**: ros2, jazzy, humble, nav2, gazebo, colcon, ament, launch, rclpy, guard_brain
- **medium**: subscriber, publisher, tf2, urdf, rviz, rosbag, dds, qos, cmd_vel
- **low**: robot, sensor, lidar

### ai-ml
- **high**: random forest, st-gcn, lstm, transformer, fine-tuning, epoch, learning rate, f1-score, confusion matrix, llm, ollama, exaone
- **medium**: accuracy, precision, recall, auc, roc, train, validation, batch size, optimizer, 모델 학습
- **low**: model, feature, predict, classification

### ai-agent
- **high**: ai agent, 에이전트, agent, tool use, function calling, autonomous decision, 자율 판단, guard brain, llm 제어, 자동화 도구, agentic, multi-agent, 에이전트 협업, agent flow, orchestration
- **medium**: 자동화, automation, trigger, action, react pattern, plan-and-execute, chain, workflow, 도구 호출, 상태 관리, state machine, event-driven, callback
- **low**: task, execute, invoke, schedule, 실행, 판단, response

### vision-ai
- **high**: yolo, pose estimation, keypoint, 낙상, skeleton, bounding box, opencv, mediapipe, coco 17, home safe
- **medium**: frame, video, camera, inference, webcam, detection, tracking
- **low**: image, pixel, resolution

### robotics
- **high**: kevin patrol, 자율주행, slam, a*, 경로 계획, path planning, waypoint, occupancy grid, patrol
- **medium**: 3d sim, collision, 충돌, obstacle, autonomous, mocksim, fleet, multi-robot, 순찰
- **low**: motor, imu, odometry

### mlops
- **high**: pipeline, 파이프라인, data augmentation, feature engineering, auto labeling, 모델 비교, deploy
- **medium**: preprocessing, 전처리, normalization, 정규화, dataset, undersample, smote
- **low**: script, automation, batch, csv, pkl

### robot-network
- **high**: robot network, 로봇 네트워크, 로봇 통신, fleet 통신, multi-robot communication, swarm, mesh network
- **medium**: dds, protocol, 프로토콜, bandwidth, latency, 네트워크, network topology, 통신, 동기화
- **low**: socket, tcp, udp, mqtt, wireless

### robot-security
- **high**: robot security, 로봇 보안, 보안관, 침입 감지, intrusion detection, authentication, 인증, encryption, 암호화, access control, 접근 제어
- **medium**: vulnerability, 취약점, firewall, 방화벽, certificate, tls, ssl, token, bcrypt, hash, 권한
- **low**: security, 보안, threat, 위협, attack

### big-data
- **high**: big data, 빅데이터, 대용량 데이터, 데이터 레이크, data lake, hadoop, spark, kafka, elasticsearch
- **medium**: 로그 분석, log analysis, 데이터 수집, data collection, mysql, mongodb, 통계, 시계열, time series, 데이터베이스
- **low**: data, 데이터, db, query, sql, nosql

### dev-tools
- **high**: pyqt6, dashboard, 대시보드, dark theme, 다크 테마, fastapi, gui, widget, qss, hugo, github pages, 블로그
- **medium**: layout, sidebar, panel, chart, plot, toast, alert, ui, ux, css
- **low**: button, window, font, style

### project
- **high**: 계획서, 프로젝트 계획, project plan, roadmap, 로드맵, 전략, strategy, milestone, 개발계획서
- **medium**: 요구사항, requirement, architecture, 설계, 목표, objective, scope
- **low**: overview, 개요, summary

### worklog
- **high**: 작업일지, work_log, work log, 작업 기록, dev_log, bugfix, 버그 수정, 개발 일지
- **medium**: 수정, fix, 변경, change, 이슈, issue, 해결, resolved, 적용
- **low**: 완료, done, 진행중

---

## 4. 분류 결과 출력

### 4-1. 터미널 리포트

```
📊 블로그 레퍼런스 분류 결과
═══════════════════════════════════════

🤖 Robotics (12개)
   kevin_patrol_mocksim_optimization_log.md    [+dev-tools]    ← kevin_patrol
   kevin_multi_patrol_bugfix_log.md            [+dev-tools]    ← my_docs
   ...

🧠 AI / ML / DL (8개)
   rf-stgcn-model-comparison-final.md          [+vision-ai]    ← downloads
   ...

🕵️ AI Agent (N개)
   guard_brain_fastapi.md                      [+ros2]         ← my_docs
   LLM_ROS_보안관_개발계획서.md                  [+robot-security] ← ironman
   ...

👁 Vision AI (6개)
   home-safe-solution-vision-ai-project.md     [+ai-ml]        ← downloads
   ...

🔒 Robot Security (2개)
   SECURITY_RECOMMENDATIONS.md                                  ← my_docs

🌐 Robot Network (1개)
   ...

📦 Big Data (1개)
   ...
```

### 4-2. 분류 인덱스 파일

`references/.category_index.json`:

```json
{
  "robotics": [
    {"file": "kevin_patrol/development.md", "score": 24, "sub": "dev-tools", "keywords": ["kevin patrol", "a*", "slam"]}
  ],
  "robot-security": [
    {"file": "ironman/LLM_ROS_보안관_개발계획서.md", "score": 20, "sub": "ros2", "keywords": ["보안관", "로봇 보안"]}
  ]
}
```

### 4-3. Hugo 포스트 생성 시 활용

```yaml
# 블로그 포스트 front matter에 자동 반영
categories: ["robotics"]
tags: ["kevin-patrol", "a-star", "slam", "pyqt6"]
```

---

## 5. 실행 워크플로우

```
1. 초기 수집      $ python collect_blog_refs.py --init
2. 일상 수집      $ python collect_blog_refs.py
3. 카테고리 분류  $ python collect_blog_refs.py --classify
4. 현황 확인      $ python collect_blog_refs.py --status
5. 블로그 작성 시 → .category_index.json 참조 → 포스트 작성
```

---

## 6. 향후 확장

| 항목 | 설명 |
|------|------|
| LLM 기반 분류 | 키워드 스코어링으로 애매한 파일을 LLM에 질의하여 정밀 분류 |
| 자동 태그 추출 | 본문 키워드 빈도 → Hugo tags 자동 생성 |
| 블로그 포스트 초안 생성 | 카테고리 + 레퍼런스 md → 포스트 템플릿 자동 생성 |
| 중복 콘텐츠 감지 | 해시 + 유사도 비교로 중복 레퍼런스 경고 |
| 카테고리별 통계 대시보드 | 기술 스택 커버리지 시각화 |

---

## 7. AI Agent 카테고리 성장 로드맵

`ai-agent`는 단순 분류 카테고리를 넘어 블로그의 **핵심 성장 축**으로 설정.

### Phase 1 — 자동화 도구 개발 (현재)
> "AI가 특정 작업을 자율적으로 수행하는 단일 도구를 만든다"

| 콘텐츠 예시 | 연관 프로젝트 |
|-------------|-------------|
| LLM 기반 Guard Brain 구현 | Home Guard Bot |
| FastAPI + Ollama 자율 응답 시스템 | 보안관 프로젝트 |
| Tool Use 패턴으로 센서 데이터 해석 | EyeCon / Kevin Patrol |
| 이벤트 기반 자동 알림 에이전트 | Home Safe Solution |

**키 개념**: Tool Use, Function Calling, 단일 LLM 루프, 상태 머신

### Phase 2 — 에이전트 간 협업 Flow (향후)
> "여러 에이전트가 역할을 분담하고 결과를 주고받는 파이프라인을 구성한다"

| 콘텐츠 예시 | 연관 기술 |
|-------------|---------|
| Vision Agent → Decision Agent → Action Agent 파이프라인 | ROS2 + LLM |
| 멀티로봇 에이전트 협업 (Fleet 내 역할 분배) | Kevin Fleet |
| Supervisor Agent + Worker Agent 패턴 | Orchestration |
| 에이전트 간 메시지 큐 설계 | ROS2 Topic / Action |

**키 개념**: Multi-Agent, Orchestration, ReAct, Plan-and-Execute, Agent Memory

### 태그 진화 전략

```
Phase 1 태그: ai-agent, tool-use, llm-control, automation
Phase 2 태그: ai-agent, multi-agent, agent-flow, orchestration, collaboration
```
