---
title: "Kevin Smart Home — 개발 원칙 (DEV_RULES)"
date: 2026-03-21
draft: true
tags: ["smart-home", "esp32", "fastapi"]
categories: ["smart-home"]
description: "> **작성일:** 2026-02-19 > **작성자:** Stephen Kong > **적용 범위:** Kevin Smart Home 프로젝트 전체"
---

# Kevin Smart Home — 개발 원칙 (DEV_RULES)

> **작성일:** 2026-02-19  
> **작성자:** Stephen Kong  
> **적용 범위:** Kevin Smart Home 프로젝트 전체  
> ⚠️ 이 문서는 프로젝트 진행 시 항상 먼저 읽고 개발을 시작한다.

---

## 원칙 1. 통합 버전 제공

- 모든 수정 내역은 **통합 버전(완성본)으로 제공**한다.
- 부분 코드 패치, diff 형태로 제공하지 않는다.
- 파일 수정이 발생하면 해당 파일 전체를 새로 제공한다.
- 예시:
  - ❌ "37번 줄을 이렇게 바꾸세요"
  - ✅ 수정된 파일 전체를 다운로드 가능하게 제공

---

## 원칙 2. 일일 작업 기록

- 모든 작업 내용은 **그날 작업 종료 전 DEV_LOG.md에 기록**한다.
- 기록 위치: `/home/gjkong/dev_ws/kevin_smarthome/docs/DEV_LOG.md`
- 기록 형식:

```markdown
## YYYY-MM-DD | vX.X.X 작업 내용 요약

### 작업 내용
- 변경된 파일 목록 및 설명
- 핵심 설계 결정사항

### 다음 작업
- [ ] 다음 할 일

### 오늘의 작업 요약
- 한 줄 요약
```

- 작업 종료 시 Claude가 DEV_LOG 업데이트본을 자동으로 제공한다.

---

## 원칙 3. 기존 프로젝트 보호

기존 프로젝트를 참고하거나 코드를 활용할 때:

- **기존 프로젝트의 파일을 절대 수정하지 않는다.**
- **기존 프로젝트의 디렉토리 구조를 절대 변경하지 않는다.**
- 코드 재사용 시 반드시 **복사(copy)** 후 Kevin Smart Home 프로젝트 내에서 수정한다.

### 참조 가능한 기존 프로젝트 경로

| 프로젝트 | 경로 | 참조 목적 |
|---------|------|-----------|
| Kevin Patrol | `/home/gjkong/dev_ws/kevin_patrol/` | PyQt6 대시보드, PyOpenGL 3D, RobotManager |
| Home Guard Bot | `/home/gjkong/dev_ws/ironman/` | FastAPI 서버, ROS2 노드 구조 |
| AI Drama Agent | `/home/gjkong/dev_ws/ai_drama_agent/` | LangGraph StateGraph |
| micro-ROS | `/home/gjkong/dev_ws/ros2_class/` | ESP32 펌웨어 기반 |

### 금지 사항

```
❌ 기존 프로젝트 파일 직접 편집
❌ 기존 프로젝트 디렉토리 이동/삭제
❌ 기존 프로젝트 requirements.txt 수정
✅ 파일 복사 후 kevin_smarthome/ 내에서 수정
✅ import 경로는 kevin_smarthome 기준으로 재작성
```

---

## 개발 시작 체크리스트

매 개발 세션 시작 시 아래를 확인한다:

- [ ] 이 문서(DEV_RULES.md) 확인
- [ ] 최신 DEV_LOG.md 확인 (지난 작업 내용 파악)
- [ ] 가상환경 활성화: `source kevin_smarthome_venv/bin/activate`
- [ ] 프로젝트 루트 이동: `cd /home/gjkong/dev_ws/kevin_smarthome`
- [ ] 기존 프로젝트 참조 시 경로 확인 (수정 금지)

---

## 프로젝트 정보

```
프로젝트명: Kevin Smart Home
루트 경로:  /home/gjkong/dev_ws/kevin_smarthome
가상환경:   kevin_smarthome_venv
문서 경로:  docs/
  - DEV_RULES.md       ← 이 파일 (개발 원칙)
  - DEV_LOG.md         ← 일일 작업 기록
  - Kevin_Smart_Home_Design.md ← 전체 설계 문서
```

---

*Kevin Smart Home | DEV_RULES v1.0 | 2026-02-19*
