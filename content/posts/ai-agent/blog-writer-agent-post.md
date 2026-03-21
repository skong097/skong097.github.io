---
title: "블로그 포스트를 자동으로 쓰는 AI Agent 만들기"
date: 2026-02-18
categories: ["ai-agent"]
tags: ["ai-agent", "llm", "fastapi", "ollama", "python", "자동화"]
description: "레퍼런스 md 파일을 읽고 Hugo 블로그 포스트를 자동으로 작성하는 AI Agent 개발기. LLM에게 JSON을 맡기면 안 되는 이유와 역할 분리 설계를 실제 삽질 경험으로 정리했다."
ShowToc: true
ShowReadingTime: true
draft: false
---

## 왜 만들었나?

블로그 포스트 작성이 항상 마지막 단계에서 막힌다.

프로젝트는 끝났고, 레퍼런스 문서도 있고, 정리된 보고서도 있다. 그런데 Hugo 형식으로 변환하고, 카테고리 잡고, front matter 쓰고, 본문 구조 잡는 데 매번 시간이 소요된다. 반복 작업이 분명한데 계속 손으로 하고 있었다.

그래서 만들었다. **레퍼런스 파일을 주면 Hugo 포스트를 자동으로 생성하는 AI Agent.**

---

## 설계 방향

처음엔 LLM이 모든 걸 판단하도록 설계했다.

```
요청 → LLM 판단 → 도구 선택 → 도구 호출 → 결과 관찰 → 반복
```

Guard Brain Agent(Phase 1)에서 썼던 Tool Use 패턴이다. 그런데 Blog Writer에서는 계속 문제가 생겼다.

LLM이 `scan_references(keyword="ST-GCN fine-tuning fall detection")`처럼 영문으로 검색했다. 파일은 한글로 저장되어 있으니 당연히 `found: 0`. LLM이 없는 파라미터명을 만들어냈다 (`specific_topic`, `application`). JSON 파싱이 중간에 계속 실패했다.

세 번의 삽질 끝에 설계를 바꿨다.

> **"흐름 제어는 코드가, 창작은 LLM이"**

---

## 최종 아키텍처

```
POST /agent/write
  {"request": "ST-GCN 파인튜닝 포스트 작성해줘"}
         │
         ▼
┌─────────────────────────────────┐
│       BlogWriterAgent.run()     │
│                                 │
│  Step 1. scan_references        │ ← 코드가 직접 실행
│          (한글 키워드 강제 추출)  │
│                                 │
│  Step 2. read_file              │ ← 코드가 직접 실행
│          (첫 번째 파일 자동 선택) │
│                                 │
│  Step 3. classify_category      │ ← 코드가 직접 실행
│          (키워드 스코어링)        │
│                                 │
│  Step 4. LLM 본문 생성 ★        │ ← LLM 전담
│          (마크다운 직접 출력)     │
│                                 │
│  Step 5. write_post             │ ← 코드가 직접 실행
└─────────────────────────────────┘
         │
         ▼
Hugo 포스트 md 파일 저장
```

LLM은 Step 4에서만 개입한다. JSON 없이 마크다운만 출력하도록 요청한다.

---

## 핵심 코드

### 1. 한글 키워드 강제 추출

LLM에게 검색어를 맡기지 않는다. 요청문에서 직접 추출한다.

```python
def _extract_keyword(self, request: str) -> str:
    stopwords = ["포스트", "작성해줘", "써줘", "만들어줘",
                 "블로그", "글", "달성한", "으로", "한"]
    words = request.split()
    return " ".join(
        [w for w in words if w not in stopwords and len(w) > 1][:3]
    )

# "ST-GCN 파인튜닝으로 낙상감지 91.89% 달성한 포스트 작성해줘"
# → "ST-GCN 파인튜닝으로 낙상감지"
```

### 2. **kwargs 방어적 설계

LLM이 파라미터명을 `keyword`, `specific_topic`, `query`, `application` 등으로 매번 다르게 만든다. 어떤 이름으로 오든 처리한다.

```python
def scan_references(**kwargs) -> dict:
    # 파라미터명 무관하게 첫 번째 문자열 값을 검색어로 사용
    search_term = ""
    for v in kwargs.values():
        if isinstance(v, str) and v.strip():
            search_term = v.strip()
            break
    ...
```

### 3. 레퍼런스 front matter 파싱

기존 레퍼런스 파일의 title, tags, summary를 그대로 가져온다. 중복 작성하지 않는다.

```python
def _extract_ref_meta(self, ref_content: str) -> dict:
    meta = {"title": "", "tags": [], "summary": "", "body": ""}
    fm_match = re.match(r"^---\s*([\s\S]*?)---\s*([\s\S]*)", ref_content)
    if fm_match:
        fm   = fm_match.group(1)
        meta["body"] = fm_match.group(2).strip()
        # title, tags, summary 정규식 추출
        ...
    return meta
```

### 4. LLM 본문 생성 (JSON 없음)

```python
def _llm_write_body(self, title: str, ref_body: str, summary: str) -> str:
    prompt = f"""다음 레퍼런스를 바탕으로 기술 블로그 포스트 본문을 한국어로 작성해주세요.

제목: {title}
레퍼런스 내용:
{ref_body[:3000]}

규칙:
- front matter(---) 없이 본문만 작성
- ## 섹션 헤더 사용
- 코드 블록은 ```python 형식으로
- 마크다운 형식으로만 출력"""

    response = ollama.chat(
        model=self.model,
        options={"num_predict": 4096, "temperature": 0.4},
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"].strip()
```

JSON 강제가 없으니 파싱 실패도 없다.

---

## 실행 결과

```bash
curl -X POST http://localhost:8101/agent/write \
  -H "Content-Type: application/json" \
  -d '{"request": "ST-GCN 파인튜닝으로 낙상감지 91.89% 달성한 포스트 작성해줘"}'
```

```
[Step 1] scan_references — 'ST-GCN 파인튜닝으로 낙상감지'
  found: 6개

[Step 2] read_file — stgcn-finetuning-fall-detection.md
  title: ST-GCN 파인튜닝으로 낙상감지 91.89% 달성기

[Step 3] classify_category
  category: ai-ml

[Step 4] LLM 본문 생성 중...
  생성 완료 — 3339자

[Step 5] write_post — st-gcn-파인튜닝으로-낙상감지-91-89--달성기.md
  ✅ 저장 완료
```

저장된 파일의 front matter:

```yaml
---
title: "ST-GCN 파인튜닝으로 낙상감지 91.89% 달성기"
date: 2026-02-18
categories: ["ai-ml"]
tags: ["st-gcn", "computer-vision", "fall-detection", "python", "deep-learning"]
description: "ST-GCN 모델을 3클래스 낙상감지에 맞춰 파인튜닝하고 84.21% → 91.89%로 끌어올린 과정과 삽질 기록"
ShowToc: true
ShowReadingTime: true
draft: false
---
```

title, tags, description 모두 레퍼런스에서 정확히 추출됐다.

---

## 삽질 기록

**시도 1**: LLM이 JSON 안에 JSON 중첩  
→ `num_predict` 제한 추가

**시도 2**: `unexpected keyword argument 'specific_topic'`  
→ `**kwargs` 방식으로 전환

**시도 3**: `scan_references found: 0` 반복  
→ 한글 키워드 코드 강제 추출

**시도 4**: front matter 두 개 중복  
→ `_extract_ref_meta()`로 파싱 분리

**시도 5**: 파싱 실패 계속  
→ **LLM을 본문 생성 전용으로 분리** (근본 해결)

결국 핵심 교훈은 하나다.

> 로컬 LLM(EXAONE 7.8B)은 긴 시스템 프롬프트에서 JSON 형식을 안정적으로 지키지 못한다.
> 판단과 흐름 제어는 코드가, 텍스트 생성은 LLM이 담당해야 한다.

---

## 프로젝트 구조

```
~/dev_ws/ai_agent/blog_writer_agent/
├── config.py      ← 경로 설정 (REFERENCES_DIR, POSTS_DIR)
├── tools.py       ← 도구 4개 (**kwargs 방어적 설계)
├── prompts.py     ← LLM 본문 생성 프롬프트
├── agent.py       ← 에이전트 코어
├── main.py        ← FastAPI 서버 (포트 8101)
└── requirements.txt
```

Guard Brain Agent(포트 8100)와 완전히 분리된 독립 환경이다.

---

## 다음 단계

지금은 레퍼런스 파일 1개만 읽는다. 다음엔 관련 파일 여러 개를 통합해서 더 풍부한 본문을 생성할 예정이다. Guard Brain Agent와 연동해서 보안 이벤트가 발생하면 자동으로 포스트 초안을 생성하는 흐름도 재미있을 것 같다.

---

*전체 코드는 [GitHub](https://github.com/skong097/ai_agent)에 공개 예정입니다.*
