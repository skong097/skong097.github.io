---
title: "2026-02-18 작업일지 (Session 10: AI Agent 카테고리 블로그 반영)"
date: 2026-03-21
draft: true
tags: ["dev-tools", "hugo"]
categories: ["dev-tools"]
description: "**작성일**: 2026-02-18 **세션**: Session 9 이후 추가 작업 블로그 분류 체계(`blog_ref_classification_design.md`)에 `ai-agent` 카테고리를 추가하고,"
---

# 2026-02-18 작업일지 (Session 10: AI Agent 카테고리 블로그 반영)

**작성일**: 2026-02-18  
**세션**: Session 9 이후 추가 작업

---

## 작업 개요

블로그 분류 체계(`blog_ref_classification_design.md`)에 `ai-agent` 카테고리를 추가하고,  
블로그 관련 파일 4개에 AI Agent 내용을 **추가(기존 내용 변경 없음)** 반영.

---

## 1. 분류 체계 업데이트 ✅

**파일**: `blog_ref_classification_design.md`

- 카테고리 수: 11개 → **12개** (`ai-agent` 신설)
- 매핑 테이블에 `AI Agent → ai-agent` 행 추가
- 키워드 세트 추가:
  - **high**: ai agent, 에이전트, tool use, function calling, 자율 판단, guard brain, llm 제어, 자동화 도구, agentic, multi-agent, 에이전트 협업, agent flow, orchestration
  - **medium**: 자동화, trigger, action, react pattern, chain, workflow, 도구 호출, state machine, event-driven, callback
  - **low**: task, execute, invoke, schedule, 실행, 판단
- 동점 우선순위: `vision-ai > ai-agent > ai-ml > ...` 으로 업데이트
- **섹션 7 신설**: AI Agent 성장 로드맵
  - Phase 1: 단일 자동화 도구 (Tool Use, 단일 LLM 루프)
  - Phase 2: 에이전트 협업 Flow (Multi-Agent, Orchestration)

---

## 2. hugo.yaml 업데이트 ✅

**추가 위치 2곳 (기존 내용 변경 없음)**

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| `description` | `ROS2 · AI/ML · Computer Vision · Robotics` | `ROS2 · AI/ML · AI Agent · Computer Vision · Robotics` |
| `homeInfoParams.Content` | `...LLM 통합 등 실전 프로젝트 경험을 공유합니다.` | 마지막에 `AI Agent 기반 자동화 도구 개발과 에이전트 협업 Flow 구축도 함께 다룹니다.` 추가 |

---

## 3. content/about/index.md 업데이트 ✅

**추가 위치 2곳 (기존 내용 변경 없음)**

- 기술 스택 그리드: `AI Agent` 카드 추가 (DevOps 카드 뒤, 6번째)
  - 태그: Tool Use, LLM 제어, 자율 판단, Agent Flow, Orchestration
- 주요 프로젝트: `Guard Brain Agent` 카드 추가 (ROS2 Commander 뒤, 7번째)
  - 설명: LLM 기반 자율 판단 AI 에이전트

---

## 4. data/roadmap_data.yaml 업데이트 ✅

**추가 위치 2곳 (기존 내용 변경 없음)**

`domains` 맨 끝 (devops 다음) 추가:
```yaml
- id: ai_agent
  name: "AI Agent"
  icon: "AGT"
  proficiency: 30
  learning_target: 75
  skills:
    - { name: "Tool Use",       level: 40 }
    - { name: "LLM 제어",       level: 45 }
    - { name: "자율 판단",      level: 30 }
    - { name: "Agent Flow",     level: 20 }
    - { name: "Orchestration",  level: 15 }
```

`blog_posts` 맨 끝 추가:
- "LLM 기반 Guard Brain AI 에이전트 설계" — planned
- "AI Agent 자동화 도구 개발 입문 — Tool Use 패턴" — planned

---

## 5. layouts/dashboard/single.html 업데이트 ✅

**추가 위치 2줄 (기존 내용 변경 없음)**

```javascript
// DOMAIN_COLORS (다크모드) — 503번 라인
ai_agent: "#00ffcc"   // 민트 계열

// DOMAIN_COLORS_LIGHT (라이트모드) — 510번 라인  
ai_agent: "#00897b"   // 틸 계열
```

---

## 수정된 파일 목록

| 파일 | 경로 | 작업 |
|------|------|------|
| `blog_ref_classification_design.md` | `~/dev_ws/blog/` | ai-agent 카테고리 + 섹션 7 추가 |
| `hugo.yaml` | `~/dev_ws/blog/` | description + Content 문구 추가 |
| `index.md` | `content/about/` | 기술스택 카드 + 프로젝트 카드 추가 |
| `roadmap_data.yaml` | `data/` | ai_agent 도메인 + blog_posts 2개 추가 |
| `single.html` | `layouts/dashboard/` | DOMAIN_COLORS 색상 2줄 추가 |

---

## 배포 절차

```bash
# 1. 파일 교체 후
hugo server -D   # 로컬 확인
# → Dashboard Skill Radar에 AI Agent 꼭짓점 추가 확인
# → About 페이지 기술스택 카드 확인
# → 홈 페이지 description 확인

# 2. 확인 완료 후
git add .
git commit -m "feat: add AI Agent category to blog and dashboard"
git push
```

---

## 다음 세션 (Step 2)

- `content/posts/ai-agent/` 디렉토리 생성
- 첫 번째 AI Agent 포스트 작성
  - 후보: "LLM 기반 Guard Brain AI 에이전트 설계" 또는 "Tool Use 패턴 입문"
