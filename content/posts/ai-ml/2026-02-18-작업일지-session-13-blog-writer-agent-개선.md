---
title: "2026-02-18 작업일지 (Session 13: Blog Writer Agent 개선)"
date: 2026-03-21
draft: true
tags: ["ai-ml", "llm"]
categories: ["ai-ml"]
description: "**작성일**: 2026-02-18 **세션**: Session 12 이후 연속 작업 Blog Writer Agent v1 완성 이후 실전 테스트를 통해 발견된 문제들을 개선."
---

# 2026-02-18 작업일지 (Session 13: Blog Writer Agent 개선)

**작성일**: 2026-02-18  
**세션**: Session 12 이후 연속 작업

---

## 작업 개요

Blog Writer Agent v1 완성 이후 실전 테스트를 통해 발견된 문제들을 개선.  
다양한 주제로 포스트 자동 생성 테스트 및 품질 향상.

---

## 1. 개선 사항

### 1-1. 다국어 키워드 자동 확장 (tools.py)

**문제**: LLM이 영문 키워드로 검색 → 한글 파일 `found: 0`  
**해결**: `KEYWORD_ALIASES` 딕셔너리로 영문↔한글 자동 확장

```python
KEYWORD_ALIASES = {
    "random forest": ["random forest", "랜덤 포레스트", "rf_tuning", "RF"],
    "st-gcn":        ["st-gcn", "stgcn", "ST_GCN", "시공간"],
    "a*":            ["A*", "astar", "경로", "pathfinding"],
    ...
}
```

---

### 1-2. 파일명 유사도 기반 best file 선택 (agent.py)

**문제**: `found: 98개` 중 엉뚱한 파일 선택  
**해결**: 파일명에 키워드 단어가 많이 포함된 파일 우선 선택 + 보너스 점수

```python
def file_score(f):
    fname = f["file"].lower()
    word_score = sum(1 for w in kw_words if w in fname)
    has_rf    = "rf" in fname
    has_stgcn = "stgcn" in fname
    bonus = 100 if (has_rf and has_stgcn) else (10 if word_score >= 2 else 0)
    return word_score + bonus
best = max(scan["files"], key=file_score)
```

---

### 1-3. 연속 하이픈 정리 (tools.py)

**문제**: 파일명에 `---` 연속 하이픈 생성  
(`random-forest-vs-st-gcn---낙상감지-모델-비교-실전-가이드.md`)  
**해결**: `write_post`에서 연속 하이픈 정리

```python
safe_name = re.sub(r"-{2,}", "-", safe_name)  # 연속 하이픈 정리
```

---

### 1-4. 스타일 가이드 자동 로드 (agent.py)

**문제**: 매번 프롬프트에 하드코딩된 말투 규칙  
**해결**: 서버 시작 시 `blog_strategy_guide.md`에서 자동 로드

```python
def _load_style_guide(self) -> str:
    guide_path = os.path.join(REFERENCES_DIR, 'my_docs/blog_strategy_guide.md')
    start = content.find('### 3.2 작성 톤 & 스타일')
    end   = content.find('## 4.', start)
    return content[start:end].strip()
```

시작 로그:
```
📖 스타일 가이드 로드 완료 (1314자)
```

---

### 1-5. my_docs 자동 동기화 (agent.py + config.py)

**문제**: `~/dev_ws/my_docs/` 아래 프로젝트 문서를 Agent가 못 찾음  
**해결**: 서버 시작 시 자동으로 `references/my_docs/`에 복사

```python
def _sync_references(self):
    """my_docs → blog/references/my_docs 자동 동기화 (읽기 전용 복사)"""
    # 원본이 더 최신이거나 없으면 복사
    if not os.path.exists(dst_path) or \
       os.path.getmtime(src_path) > os.path.getmtime(dst_path):
        shutil.copy2(src_path, dst_path)
```

시작 로그:
```
🔄 레퍼런스 동기화 완료 (124개 업데이트)  ← 첫 실행
🔄 레퍼런스 동기화 완료 (0개 업데이트)    ← 이후 (변경 없을 때)
```

**중요**: `~/dev_ws/my_docs/` 원본은 절대 수정하지 않음

---

### 1-6. 글쓰기 원칙 개선 (agent.py 프롬프트)

**문제**: 매 문장이 일관되게 친근해서 오히려 인위적인 느낌  
**해결**: 자연스러운 말투 원칙으로 교체

```
이전: "옆자리 동료한테 설명하듯이" 강제
이후:
- 편한 존댓말. 단, 매 문장을 억지로 친근하게 쓰지 말 것
- 기술적 사실은 담담하게, 삽질/실수는 솔직하게, 성과는 숫자로
- 논문 투 금지, 모호한 표현 금지
```

---

## 2. 생성된 포스트 현황

| 파일 | 카테고리 | 상태 |
|------|---------|------|
| blog-writer-agent-post.md | ai-agent | ✅ |
| st-gcn-파인튜닝으로-낙상감지-91-89--달성기.md | ai-ml | ✅ |
| rf-vs-stgcn-fall-detection.md | computer-vision | ✅ |
| stgcn-finetuning-fall-detection.md | computer-vision | ✅ |
| pyqt6-dark-theme-system.md | dev-tools | ✅ |
| astar-pathfinding-los-smoothing.md | robotics | ✅ |
| kevin-patrol-fleet-dashboard.md | robotics | ✅ |
| ros2-guard-brain-fastapi.md | ros2 | ✅ |
| eyecon-multimodal-psychology-ai.md | vision-ai | ✅ |

**총 9개** — 목표 10개까지 1개 남음!

---

## 3. 정리된 중복 파일

```bash
# 삭제한 중복/오류 파일
rm content/posts/ai-ml/random-forest-vs-st-gcn---낙상감지-모델-비교-실전-가이드.md
rm content/posts/ai-ml/st-gcn-파인튜닝으로-낙상감지-91-89--달성기.md
```

---

## 4. Blog Writer Agent 역할 재정의

```
Agent 담당 (80%):        사람 담당 (20%):
- 레퍼런스 기반 초안      - 말투/뉘앙스 다듬기
- front matter 작성      - 스크린샷/동영상 삽입
- 섹션 구조 잡기          - 실제 경험 디테일 보강
- 코드 스니펫 초안        - 오류/부정확한 내용 수정
                         - 최종 퀄리티 검수
```

---

## 5. 레퍼런스 파일명 원칙 (교훈)

```
✅ 좋은 예:
rf-stgcn-model-comparison.md
astar-pathfinding-los-smoothing.md
eyecon-multimodal-psychology.md

❌ 나쁜 예:
WORK_LOG_20260205_v2(st-gcn).md
2026-02-07_WORK_LOG_FINAL_v2.md
```

**규칙**: 핵심 키워드 2개 이상 파일명에 포함, 날짜/버전보다 내용 중심

---

## 6. 수정된 파일 목록

| 파일 | 변경 내용 |
|------|---------|
| `config.py` | `PROJECTS_DIR` 추가 |
| `tools.py` | `KEYWORD_ALIASES` 다국어 확장, 연속 하이픈 정리 |
| `agent.py` | `_load_style_guide()`, `_sync_references()`, 파일 선택 로직, 프롬프트 개선 |

---

## 다음 세션 후보

- 마지막 10번째 포스트 작성 (guard-brain-tool-use-agent 또는 ROS2 학습 회고)
- GitHub 커밋 — ai_agent 전체 push
- 블로그 공개 준비 검토
