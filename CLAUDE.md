# 블로그 작성 규칙

## 이 블로그의 지식 구조 (비전)

이 블로그는 지식을 모으고 키워 결국 개인 세컨드 브레인으로 흘려보내는 파이프라인이다.

1. **바깥 지식 수집·학습** — KB Radar(`/kb-radar/`, `data/kb_keywords.yaml` 기반 자동 수집)로 외부 논문·기사·영상·인물 동향을 주기적으로 긁어와 요약·학습한다.
2. **내부 지식 기록·확장** — 프로젝트와 포스트(`content/`)로 개인적/내부적 작업을 기록·관리하며 지식을 확장한다.
3. **세컨드 브레인으로 통합** — 위 모든 지식은 추후 **nextbrain의 LLM wiki**에 저장되어 사용자의 세컨드 브레인이 되는 파이프라인의 일부다.

→ 즉 KB Radar(외부 입력)와 포스트/프로젝트(내부 입력)가 모두 nextbrain LLM wiki라는 종착지로 모인다.

## 다이어그램 박스 → SVG 변환 (필수)

박스문자(`┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ │ ─ ═ ║` 등)로 그린 **다이어그램은 코드펜스에 두지 않고 SVG 이미지로 변환한다.** 코드펜스(plain ``` ```)는 폰트/화면폭/한글 더블폭에 따라 정렬이 무너지고 글자가 깨져 보인다.

### 변환 대상 vs 유지 대상

| 종류 | 처리 |
|---|---|
| **파일/디렉터리 구조 트리** (`├── main.py`) | → **SVG** |
| **아키텍처·블록 다이어그램** (`┌──┐` 박스, 노드/화살표) | → **SVG** |
| **플로우차트·시퀀스·HUD 목업** (박스문자로 그린 도형) | → **SVG** |
| 실제 소스 코드 (bash/python/yaml 등) | 코드펜스 유지 (` ```bash ` 등 언어 지정) |
| 마크다운 표 | 마크다운 표 유지 (박스문자로 표 그리지 말 것) |
| 단순 가로 구분선 (`─────`) | 무시 (또는 `---`) |

판별 기준: **"이게 실행 가능한 코드인가?"** 아니면(=그림이면) SVG로 변환.

### 변환 방법 (고정 패턴)

1. SVG를 `static/images/diagrams/<프로젝트>-<무엇>.svg` 에 손수 작성.
   - 예: `moca-reactivefallback-tree.svg`, `gaze-puzzle-file-tree.svg`, `moca-ema-formula.svg`
2. 마크다운에서 깨진 코드펜스 블록을 figure 쇼트코드로 교체:
   ```
   {{< figure src="/images/diagrams/<파일>.svg" alt="<한글 설명>" >}}
   ```
3. `alt` 는 스크린리더/SEO용으로 다이어그램 내용을 한글 한 문장으로 요약.

### SVG 스타일 템플릿 (터미널 카드)

기존 `static/images/diagrams/moca-reactivefallback-tree.svg`, `gaze-puzzle-file-tree.svg` 를 레퍼런스로 동일 스타일 유지:

- 다크 라운드 카드: `fill="#0c1117"`, 테두리 `stroke="rgba(94,242,184,0.16)"`, `rx="14"`
- 상단 타이틀바(높이 46): 신호등 점 `#ff5f57 / #febc2e / #28c840`, 우상단 라벨 `<kind> — <name>` (`fill="#5d6b78"`, `font-size="12"`)
- 폰트: `font-family="'JetBrains Mono', ui-monospace, 'SFMono-Regular', Menlo, monospace"`
- 색 코드: 폴더/루트 `#6cb6ff`, 강조노드 초록 `#5ef2b8`, 보조 주황 `#f0a36b`, 이미지/기타 `#b9a7e6`, 주석/뮤트 `#8c98a4`·`#6272a4`, 커넥터선 `#3a4654`
- 트리 커넥터는 텍스트 박스문자 대신 SVG `path`(세로 spine + 가로 tick)로 그린다 → 정렬 깨짐 원천 차단
- 루트에 `role="img"` + `aria-label` 지정

## 기타

- 전 직장 업체명(NCsoft 등) 절대 노출 금지.
- Hugo 템플릿에서 `site.Data` 유지(CI Hugo 0.146 호환 — `hugo.Data` 로 바꾸면 빌드 실패).
