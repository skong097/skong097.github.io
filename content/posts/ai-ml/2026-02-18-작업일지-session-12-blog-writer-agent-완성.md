---
title: "2026-02-18 작업일지 (Session 12: Blog Writer Agent 완성)"
date: 2026-03-21
draft: true
tags: ["ai-ml", "llm", "exaone"]
categories: ["ai-ml"]
description: "**작성일**: 2026-02-18 **세션**: Session 11 이후 추가 작업 기존 프로젝트와 완전 독립된 환경에서"
---

# 2026-02-18 작업일지 (Session 12: Blog Writer Agent 완성)

**작성일**: 2026-02-18  
**세션**: Session 11 이후 추가 작업

---

## 작업 개요

기존 프로젝트와 완전 독립된 환경에서  
**Blog Writer Agent v1** 개발 및 동작 검증 완료.

---

## 1. 환경 구축 ✅

```
~/dev_ws/ai_agent/blog_writer_agent/
├── config.py      ← 설정값 (모델명, 포트 8101, 블로그 경로)
├── tools.py       ← 도구 함수 4개
├── prompts.py     ← LLM 프롬프트 (본문 생성 전용)
├── agent.py       ← 에이전트 코어 (코드 제어 + LLM 본문 생성)
├── main.py        ← FastAPI 서버
├── requirements.txt
└── logs/
```

---

## 2. 구현 내용

### tools.py — 도구 4개 (파라미터명 유연하게 **kwargs 처리)

| 도구 | 기능 |
|------|------|
| `scan_references(keyword)` | references/ 디렉토리 md 파일 키워드 탐색 |
| `read_file(path)` | md 파일 내용 읽기 (앞 5000자) |
| `classify_category(text)` | 키워드 스코어링 카테고리 분류 |
| `write_post(filename, category, content)` | Hugo 포스트 파일 저장 |

### agent.py — 핵심 설계 원칙

**"코드가 흐름 제어 + LLM은 본문 생성 전용"**

```
Step 1: scan_references  ← 코드가 직접 실행 (한글 키워드 강제)
Step 2: read_file        ← 코드가 직접 실행 (첫 번째 파일 자동)
Step 3: classify_category ← 코드가 직접 실행
Step 4: LLM 본문 생성    ← LLM에게 마크다운 직접 출력 요청 (JSON 없음)
Step 5: write_post       ← 코드가 직접 실행
```

---

## 3. 튜닝 과정 (삽질 기록)

| 시도 | 문제 | 원인 | 해결 |
|------|------|------|------|
| 1차 | LLM이 JSON 안에 JSON 중첩 | 응답 너무 길어 파싱 실패 | `num_predict` 제한 추가 |
| 2차 | `unexpected keyword argument 'specific_topic'` | LLM이 파라미터명 자유 생성 | `**kwargs` 방식으로 전환 |
| 3차 | `scan_references found: 0` 반복 | LLM이 영문 키워드로 검색, 파일은 한글 | Step 0에서 한글 키워드 강제 실행 |
| 4차 | front matter 두 개 중복 | fallback이 레퍼런스 내용 그대로 붙임 | `_extract_ref_meta()`로 파싱 분리 |
| 5차 | 파싱 실패 계속 | EXAONE이 긴 시스템 프롬프트에서 JSON 불안정 | **LLM을 본문 생성 전용으로 분리** |

---

## 4. 최종 실행 결과

**입력**: `"ST-GCN 파인튜닝으로 낙상감지 91.89% 달성한 포스트 작성해줘"`

```
Step 1: scan_references → 6개 발견
Step 2: read_file       → title: "ST-GCN 파인튜닝으로 낙상감지 91.89% 달성기"
Step 3: classify_category → ai-ml
Step 4: LLM 본문 생성   → 3339자
Step 5: write_post      → 저장 완료
```

**저장 경로**: `content/posts/ai-ml/st-gcn-파인튜닝으로-낙상감지-91-89--달성기.md`

**출력 퀄리티**:
- front matter 정확 (중복 없음)
- 제목/태그/description: 레퍼런스에서 정확히 추출
- 본문: 개요/배경/목표/구현/결과/배운점/다음단계 구조
- 코드 블록 python 언어 명시
- 결과 테이블 포함
- `draft: true` 자동 설정

---

## 5. 핵심 인사이트

**LLM에게 JSON 판단을 맡기면 불안정하다**  
EXAONE 같은 로컬 모델은 시스템 프롬프트가 길어질수록 JSON 형식 준수율이 떨어진다.  
→ 흐름 제어는 코드가, 창작(본문 작성)은 LLM이 담당하는 역할 분리가 핵심.

**파라미터명은 LLM이 자유롭게 만든다**  
`keyword`, `specific_topic`, `application`, `query` 등 매번 달라짐.  
→ `**kwargs`로 받아서 첫 번째 문자열 값을 사용하는 방어적 설계 필요.

**한글 파일을 영문 키워드로 검색하면 항상 실패**  
→ 요청문에서 직접 한글 키워드를 추출해서 코드가 강제 실행.

---

## 6. 수정된 파일 목록

| 파일 | 주요 변경 |
|------|---------|
| `agent.py` | 코드 제어 방식으로 전환, LLM 본문 생성 전용 분리 |
| `tools.py` | 모든 함수 `**kwargs` 방식으로 전환 |
| `prompts.py` | 시스템 프롬프트 단순화, JSON 강제 제거 |

---

## 다음 세션 후보

1. **다른 포스트로 추가 테스트** — Kevin Fleet, Guard Brain 포스트
2. **blog_writer_agent README.md** 작성
3. **GitHub 커밋** — ai_agent 전체 push
4. **Blog Writer Agent 블로그 포스팅** — 오늘 만든 에이전트 자체를 포스트로
