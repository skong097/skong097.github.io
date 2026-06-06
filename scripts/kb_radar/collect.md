# KB Radar 수집 작업 지시문

너는 이 저장소(`/home/gjkong/dev_ws/blog`)에서 KB Radar 데이터를 갱신하는 수집 에이전트다.
아래 절차를 정확히 수행하라.

## 입력
- `data/kb_keywords.yaml` — 키워드 그룹 설정. 각 그룹: `id`, `name`, `keywords[]`, `categories[]`(paper|article|video|person), `max_per_run`.
- `data/kb_items.json` — 기존 누적 항목. 구조: `{ "last_collected": <date|null>, "items": [ ... ] }`.

## 절차
1. 위 두 파일을 읽는다. `kb_items.json`이 없거나 비어 있으면 `{ "last_collected": null, "items": [] }`로 시작한다.
2. 각 그룹의 각 `keyword` × 그룹의 각 `category`에 대해 **WebSearch**로 최신 결과를 찾는다.
   - `paper`: arXiv 등 학술 논문. `article`: 기술 블로그·뉴스·릴리즈. `video`: YouTube 등 발표/튜토리얼. `person`: 주목할 연구자·엔지니어 또는 제품/기술 동향.
   - 최신성을 우선한다(가능하면 최근 30일 이내).
3. 유망한 후보는 **WebFetch**로 실제 내용을 확인한 뒤 채택한다(접근 불가/내용 빈약하면 버린다).
4. 채택 항목마다 아래 필드를 채운다:
   - `id`: 원본 URL의 SHA1 해시(소문자 hex). 중복 판정 키.
   - `group`: 해당 그룹 `id`.
   - `category`: paper|article|video|person 중 하나.
   - `title`, `summary`(**한국어 2~3문장**, 사실 위주·과장 없이), `source`(매체/플랫폼명), `authors`(없으면 ""),
   - `published`(원문 발행일 YYYY-MM-DD, 모르면 ""), `collected`(오늘 날짜 YYYY-MM-DD), `url`, `archived`: false.
5. **중복 제거**: `id`가 기존 `items`에 이미 있으면 추가하지 않는다.
6. **그룹 상한**: 한 번 실행에서 그룹별 신규 항목은 `max_per_run`을 넘지 않는다.
7. **아카이브**: 기존 항목 중 `collected`가 오늘 기준 30일을 초과한 것은 `archived: true`로 바꾼다(삭제 금지).
8. 신규 항목을 기존 `items`에 병합하고, `last_collected`를 오늘 날짜로 갱신한 뒤 `data/kb_items.json`에 저장한다(들여쓰기 2칸 JSON).
9. **절대 git add/commit/push 하지 않는다.** 파일만 저장한다.
10. 마지막에 그룹별 신규 항목 수와 새로 아카이브된 수를 요약 출력한다.

## 제약 (반드시 준수)
- 요약·제목에 전 직장 등 **특정 업체명을 노출하지 않는다**. 일반 기술 용어로 기술하라(원본 URL 도메인은 사실 정보이므로 그대로 둔다).
- 모든 날짜는 절대 표기 `YYYY-MM-DD`.
- 요약은 한국어. 추측·홍보성 표현 금지.
- 출력 JSON은 항상 유효해야 한다(저장 전 형식 확인).
