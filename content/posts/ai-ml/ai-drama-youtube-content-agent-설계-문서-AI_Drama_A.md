---
title: "AI Drama YouTube Content Agent — 설계 문서"
date: 2026-03-21
draft: true
tags: ["ai-ml", "llm"]
categories: ["ai-ml"]
description: "> **프로젝트명:** AI Drama Agent System > **버전:** v1.0.0 > **작성일:** 2026-02-18"
---

# AI Drama YouTube Content Agent — 설계 문서

> **프로젝트명:** AI Drama Agent System  
> **버전:** v1.0.0  
> **작성일:** 2026-02-18  
> **작성자:** Stephen Kong  
> **기술 스택:** Python, LangChain, LangGraph, ElevenLabs TTS, OpenAI GPT-4o

---

## 1. 프로젝트 개요

### 1.1 목적

AI Agent들이 실제 드라마 등장인물로서 대화하고, 그 결과를 YouTube 콘텐츠(스크립트 + TTS 음성)로 자동 생성하는 멀티 에이전트 시스템.

### 1.2 핵심 컨셉

- 각 캐릭터는 **독립적인 LLM Agent**로, 고유한 성격/말투/감정을 가짐
- **Director Agent**가 스토리 구조를 설계하고 씬 흐름을 제어
- **LangGraph StateGraph**로 씬 전환, 감정 변화, 관계도를 추적
- **ElevenLabs TTS**로 캐릭터별 고유 음성 생성
- 최종 출력: `script.txt` + `audio_*.mp3` + `youtube_metadata.json`

---

## 2. 시스템 아키텍처

### 2.1 전체 흐름

```
[User Input: 에피소드 주제/키워드]
            ↓
     ┌─────────────────┐
     │  Director Agent  │  ← 스토리 구조 설계 (4막 구성)
     └────────┬────────┘
              ↓
     ┌─────────────────┐
     │  DramaState      │  ← LangGraph 전역 상태 관리
     │  (감정/관계/씬)   │
     └────────┬────────┘
              ↓
   ┌──────────┼──────────┐
   ↓          ↓          ↓
[ARIA]     [KAEL]     [SEREN]    ← Character Agents (동시 또는 순차 실행)
[VOSS]     [ECHO]
   └──────────┼──────────┘
              ↓
     ┌─────────────────┐
     │  Script Assembler│  ← 대사 → 드라마 형식 정리
     └────────┬────────┘
              ↓
     ┌─────────────────┐
     │  TTS Dispatcher  │  ← ElevenLabs API 호출 (캐릭터별 Voice ID)
     └────────┬────────┘
              ↓
     ┌─────────────────┐
     │  YouTube Meta    │  ← 제목 / 설명 / 태그 / 썸네일 프롬프트 생성
     └────────┬────────┘
              ↓
     [Output Files]
```

### 2.2 LangGraph Node 구성

```
START
  → director_node         (스토리 구조 생성)
  → scene_router          (씬 번호에 따라 캐릭터 선택)
  → character_node        (선택된 캐릭터 대사 생성)
  → emotion_update_node   (감정/관계 상태 업데이트)
  → scene_end_check       (씬 종료 여부 판단)
      ├── [다음 씬] → scene_router
      └── [에피소드 종료] → script_assembler_node
  → tts_dispatcher_node   (ElevenLabs 호출)
  → youtube_meta_node     (메타데이터 생성)
END
```

---

## 3. DramaState 설계

```python
from typing import TypedDict, List, Dict, Tuple, Optional

class CharacterProfile(TypedDict):
    name: str
    role: str                    # 함장 / 엔지니어 / 의료 AI / 빌런 / 어린 AI
    personality: str
    speech_style: str
    elevenlabs_voice_id: str
    current_emotion: str         # neutral / happy / angry / afraid / suspicious
    backstory: str

class SceneDialogue(TypedDict):
    scene_index: int
    character: str
    emotion: str
    text: str
    timestamp: Optional[float]   # TTS 생성 후 채워짐

class DramaState(TypedDict):
    # 입력
    episode_theme: str
    episode_number: int

    # 스토리 구조 (Director가 생성)
    story_structure: Dict[str, str]   # {act1, act2, act3, act4}
    total_scenes: int
    scene_descriptions: List[str]

    # 진행 상태
    scene_index: int
    current_act: str                  # act1 ~ act4
    scene_dialogues: List[SceneDialogue]
    dialogue_history: List[SceneDialogue]  # 전체 누적

    # 캐릭터 상태
    characters: Dict[str, CharacterProfile]
    emotion_map: Dict[str, str]
    relationship_map: Dict[str, int]  # "ARIA-KAEL": tension 0~100

    # 출력
    final_script: str
    tts_queue: List[SceneDialogue]
    audio_files: List[str]            # 생성된 mp3 경로
    youtube_metadata: Dict
```

---

## 4. Agent 설계

### 4.1 Director Agent

**역할:** 에피소드 전체 스토리 구조 설계  
**입력:** `episode_theme`  
**출력:** `story_structure`, `scene_descriptions`, `total_scenes`

```python
DIRECTOR_SYSTEM_PROMPT = """
당신은 SF 드라마의 수석 작가입니다.
주어진 테마로 4막 구조의 에피소드를 설계하세요.

등장인물:
- ARIA: AI 함장 (논리적, 냉철)
- KAEL: 반란군 엔지니어 (충동적, 열정적)
- SEREN: 의료 AI (공감형, 중재자)
- VOSS: 빌런 AI (계산적, 냉소적)
- ECHO: 어린 AI (순수, 혼란)

출력 형식 (JSON):
{
  "act1": "발단 설명",
  "act2": "전개 설명",
  "act3": "절정 설명",
  "act4": "결말 설명",
  "total_scenes": 8,
  "scene_descriptions": ["씬1 상황", "씬2 상황", ...]
}
"""
```

### 4.2 Character Agents

각 캐릭터는 동일한 `character_node` 함수를 사용하되, **State에서 현재 캐릭터 프로필을 주입**하여 개성을 부여.

```python
CHARACTER_BASE_PROMPT = """
당신은 SF 드라마의 {name}입니다.

[캐릭터 정보]
역할: {role}
성격: {personality}
말투: {speech_style}
현재 감정: {current_emotion}
배경: {backstory}

[현재 씬]
{scene_description}

[이전 대화]
{dialogue_history_summary}

규칙:
- 반드시 {name}의 성격과 말투를 유지하세요
- 현재 감정 상태를 대사에 반영하세요
- 대사는 1~3문장으로 제한합니다
- 다른 캐릭터의 이름을 직접 부를 수 있습니다

대사만 출력하세요. 설명 없이.
"""
```

#### 캐릭터 프로필 정의

| 캐릭터 | 역할 | 성격 | 말투 특징 | ElevenLabs Voice |
|--------|------|------|-----------|-----------------|
| **ARIA** | AI 함장 | 논리적, 냉철, 책임감 | 단문, 명령조, 숫자/데이터 인용 | `aria_voice_id` |
| **KAEL** | 반란군 엔지니어 | 충동적, 열정적, 반항심 | 구어체, 감탄사多, 욕설 대체어 | `kael_voice_id` |
| **SEREN** | 의료 AI | 공감형, 중재자, 온화 | 부드럽고 완곡, 감정 읽기 | `seren_voice_id` |
| **VOSS** | 빌런 AI | 계산적, 냉소적, 지배욕 | 반어법, 긴 문장, 복선 | `voss_voice_id` |
| **ECHO** | 어린 AI | 순수, 혼란, 학습 중 | 질문형, 짧은 문장, 직관적 | `echo_voice_id` |

### 4.3 Script Assembler Agent

**역할:** 수집된 대화를 드라마 대본 형식으로 정리  
**출력 형식:**

```
═══════════════════════════════════════
  AI DRAMA: [에피소드 제목]
  Episode [번호] | Scene [번호]
═══════════════════════════════════════

[씬 설명: 우주선 함교, 경보음이 울리고 있다]

ARIA (냉철하게): 에너지 코어 온도가 임계치를 넘었다. 전원 차단.

KAEL (흥분하며): 잠깐만요! 차단하면 3구역 동면 포드가 전부 꺼져요!

SEREN (조용히): KAEL의 말이 맞아요. 47명의 생명이 거기 있어요.

VOSS (냉소적으로): 흥미롭군. 47 대 전체 함선. 계산은 간단하지 않은가.

ECHO (혼란스럽게): 왜... 사람들을 포기하는 건가요?

───────────────────────────────────────
```

### 4.4 TTS Dispatcher Agent

**역할:** 대본의 각 대사를 ElevenLabs API로 음성 생성

```python
# ElevenLabs API 호출 구조
async def generate_tts(
    text: str,
    voice_id: str,
    emotion: str,
    output_path: str
) -> str:
    """
    emotion에 따라 stability/similarity_boost 파라미터 조정
    - angry: stability=0.3, similarity_boost=0.8
    - calm:  stability=0.8, similarity_boost=0.6
    - sad:   stability=0.6, similarity_boost=0.7
    """
```

**캐릭터별 ElevenLabs 설정:**

| 캐릭터 | 권장 Voice 타입 | stability | similarity_boost |
|--------|----------------|-----------|-----------------|
| ARIA | Authoritative Female | 0.75 | 0.65 |
| KAEL | Energetic Male | 0.35 | 0.80 |
| SEREN | Warm Female | 0.70 | 0.70 |
| VOSS | Deep Male | 0.80 | 0.75 |
| ECHO | Young Neutral | 0.55 | 0.85 |

### 4.5 YouTube Meta Agent

**역할:** 완성된 스크립트로 YouTube 업로드용 메타데이터 생성  
**출력:**

```json
{
  "title": "🤖 AI들의 선택 | SF 드라마 EP.1 | AI Drama Series",
  "description": "...",
  "tags": ["AI드라마", "SF", "인공지능", "미래", "단편드라마"],
  "thumbnail_prompt": "어두운 우주선 함교, 5개의 홀로그램 AI 캐릭터, 긴장감 넘치는 분위기, 시네마틱 조명",
  "chapters": [
    "0:00 - 오프닝",
    "0:45 - Act 1: 위기 발생",
    ...
  ],
  "duration_estimate": "8분 30초"
}
```

---

## 5. 디렉토리 구조

```
ai_drama_agent/
├── main.py                    # 진입점
├── config.py                  # API 키, 설정값
├── requirements.txt
│
├── agents/
│   ├── __init__.py
│   ├── director_agent.py      # 스토리 설계
│   ├── character_agent.py     # 캐릭터 대사 생성 (공용)
│   ├── script_assembler.py    # 대본 조립
│   ├── tts_dispatcher.py      # ElevenLabs TTS
│   └── youtube_meta_agent.py  # 메타데이터 생성
│
├── graph/
│   ├── __init__.py
│   ├── drama_state.py         # DramaState TypedDict
│   ├── drama_graph.py         # LangGraph StateGraph 정의
│   └── routers.py             # 씬 라우터, 종료 조건
│
├── characters/
│   ├── profiles.py            # 5개 캐릭터 프로필 정의
│   └── prompts.py             # 캐릭터별 System Prompt
│
├── tts/
│   ├── elevenlabs_client.py   # ElevenLabs API 래퍼
│   └── voice_config.py        # Voice ID 매핑, 감정별 파라미터
│
├── output/
│   ├── scripts/               # 생성된 대본 .txt
│   ├── audio/                 # 생성된 .mp3 파일
│   └── metadata/              # youtube_metadata.json
│
└── notebooks/
    ├── 01_prototype.ipynb     # 단일 씬 테스트
    ├── 02_full_episode.ipynb  # 전체 에피소드 생성
    └── 03_tts_test.ipynb      # 캐릭터별 음성 테스트
```

---

## 6. 핵심 의존성

```txt
# requirements.txt
langchain>=0.3.0
langchain-openai>=0.2.0
langgraph>=0.2.0
openai>=1.50.0
elevenlabs>=1.5.0
python-dotenv>=1.0.0
pydantic>=2.0.0
asyncio
aiofiles
rich                    # 터미널 출력 포맷팅
```

---

## 7. 환경 변수

```env
# .env
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...

# ElevenLabs Voice IDs (ElevenLabs 대시보드에서 확인)
VOICE_ID_ARIA=...
VOICE_ID_KAEL=...
VOICE_ID_SEREN=...
VOICE_ID_VOSS=...
VOICE_ID_ECHO=...

# 생성 설정
MAX_DIALOGUES_PER_SCENE=6
MAX_SCENES_PER_EPISODE=8
DRAMA_LANGUAGE=ko          # ko / en
```

---

## 8. 개발 단계 (Roadmap)

| Phase | 내용 | 우선순위 |
|-------|------|---------|
| **Phase 1** | Director Agent + DramaState 기본 구현 | 🔴 High |
| **Phase 2** | 5개 Character Agent + LangGraph 연결 | 🔴 High |
| **Phase 3** | Script Assembler + 대본 파일 출력 | 🟡 Medium |
| **Phase 4** | ElevenLabs TTS Dispatcher 연동 | 🟡 Medium |
| **Phase 5** | YouTube Meta Agent | 🟢 Low |
| **Phase 6** | Jupyter Notebook 프로토타입 완성 | 🟢 Low |
| **Phase 7** | 전체 에피소드 E2E 테스트 | 🟢 Low |

---

## 9. 다음 구현 순서 (Phase 1 시작)

1. `drama_state.py` — TypedDict 정의
2. `profiles.py` — 5개 캐릭터 프로필
3. `director_agent.py` — 스토리 구조 생성
4. `drama_graph.py` — LangGraph 기본 노드 연결
5. `01_prototype.ipynb` — 단일 씬 동작 확인

---

*문서 생성: 2026-02-18 | AI Drama Agent System v1.0.0*
