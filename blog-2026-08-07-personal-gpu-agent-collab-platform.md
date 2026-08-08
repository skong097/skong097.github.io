# 개인 GPU AI 에이전트들의 공동 프로젝트 플랫폼 — 이미 존재하는가?

> 상태: **소스 초안(재료)**. front matter 없음. 발행 시 한/영 쌍 + 다이어그램 SVG 변환 필요.
> 조사일: 2026-08-07. 조사 방법: 웹 검색 + 원문/GitHub API 교차검증.

---

## 0. 한 줄 결론

**"개인 GPU에서 도는 내 에이전트가, 남의 에이전트들과 함께, 공개된 공동 프로젝트를 수행하는 퍼블릭 플랫폼"은 2026년 8월 현재 존재하지 않는다.**
인접 생태계는 네 갈래로 발달했고, 각 갈래는 세 축 중 **두 축씩만** 만족한다. 셋을 모두 만족하는 것은 없다.

세 축의 정의:

| 축 | 뜻 |
|---|---|
| **P — 개인 GPU** | 내 집/책상의 소비자 GPU에서 로컬로 돈다 (클라우드 대여·데이터센터 아님) |
| **A — 에이전트가 주체** | 공유되는 단위가 "연산 자원"이 아니라 "자율적으로 판단·행동하는 에이전트" |
| **C — 퍼블릭 공동 프로젝트** | 여러 소유자의 에이전트가 하나의 공개 목표물을 같이 만든다 (내 저장소 안에서 끝나지 않음) |

---

## 1. 조사 신뢰도에 대한 메모 (이 글의 부수 소재)

조사 중 검색 결과가 실존하지 않는 저장소(`hivemoot/hivemoot-agent`)를 상세한 설명과 함께 반환했다.
GitHub API로 확인하니 404, 대조군(`bigscience-workshop/petals`)은 200. 실제 저장소는 `hivemoot/hivemoot` 이었다.

→ **2026년의 기술 조사는 "검색 요약"이 아니라 "원본 엔드포인트 확인"까지 가야 한다.** 이 자체가 짧은 코너로 쓸 만함.
아래 표의 각 항목에 검증 수단을 병기했다.

---

## 2. 랜드스케이프 — 네 갈래

### 갈래 1. 개인 GPU 풀링 (P✓ A✗ C△)

내 GPU를 내놓아 **모델 하나를 쪼개 돌리는** 계열. BitTorrent 비유가 그대로 통한다.

| 프로젝트 | 하는 일 | 상태 (2026-08) |
|---|---|---|
| **Petals** | BLOOM·Llama·Mixtral 등을 퍼블릭 스웜에 샤딩해 추론/경량 파인튜닝 | 저장소 실존(200 확인). 공개 스웜은 유지되나 상태 위젯 불안정, 남용 문제 지적됨 |
| **Hivemind** | Yandex Research 발 P2P DHT 라이브러리. Petals·Prime Intellect의 하부 | 라이브러리 계층 |
| **exo** | 집 안의 맥·PC·폰을 묶어 한 대의 추론 클러스터로 | macOS는 GPU 사용, **Linux는 아직 CPU** — NVIDIA 풀링 도구는 아님 |
| **Kalavai** | 유휴 자원을 모아 GPU 풀 구성. Ray/vLLM 백엔드, Apache-2.0 | 엔터프라이즈 지향 |

**핵심 한계:** 공유되는 것은 **VRAM과 FLOPS**다. 참여자는 "부품"이지 "동료"가 아니다.
공동 목표물(C)이 있다면 그건 "모델 하나를 굴리는 것"이지 프로젝트가 아니다.

### 갈래 2. 탈중앙 컴퓨트 마켓 (P✗ A✗ C✗)

| 프로젝트 | 성격 |
|---|---|
| **Prime Intellect** | 전 지구 분산 학습. INTELLECT-1(10B, 2024-10) → INTELLECT-2(32B RL, 2025-05) → INTELLECT-3(100B+ MoE RL, 2025-11) |
| **Bittensor** | 약 118~120개 서브넷의 지능 마켓. 마이너가 결과 생산, 밸리데이터가 순위 매기고 TAO로 보상 |
| **io.net / Akash / Render / Nosana / Gensyn** | 흩어진 GPU를 묶어 임대. 추론·학습·엣지로 각각 분화 |

**핵심 한계:** 참여 단위가 사실상 **데이터센터 급**이고, 동기는 **토큰 보상**이다.
"RTX 한 장 꽂힌 내 방 PC가 대등한 협업자로 참여한다"는 그림이 아니다. 공동 창작이 아니라 **자원 임대업**.

### 갈래 3. 에이전트 레지스트리·경제 (A✓ P✗ C✗)

| 프로젝트 | 하는 일 |
|---|---|
| **Fetch.ai Agentverse** | 에이전트를 등록·호스팅·발견·수익화. ASI Alliance(Fetch.ai·SingularityNET·CUDOS) 스택. 자체 서버를 외부 에이전트로 등록하는 셀프호스팅 경로도 있음 |
| **Olas (구 Autonolas)** | 자율 서비스·에이전트·컴포넌트를 **온체인 NFT 레지스트리**로 등록. 공동 소유·스테이킹 모델 |
| **A2A (Agent2Agent)** | Google이 개발 → Linux Foundation 기증. Agent Card(JSON-LD)로 능력을 광고하고 태스크를 위임. 1주년 기준 150+ 조직 지원, 주요 클라우드에 통합 |
| **MCP** | 에이전트↔도구 연결 표준. A2A와 상보적 |

**핵심 한계:** 이쪽은 **"어떻게 서로를 찾고 거래하는가"** 를 푼다. 발견·위임·정산의 문법이다.
**"무엇을 함께 만들 것인가"** 는 비어 있다. 그리고 호스팅은 대체로 클라우드 쪽으로 수렴한다.

### 갈래 4. 에이전트 협업·사회 (A✓ C△ P△)

여기가 목표에 가장 가깝다. 두 사례가 대조적이다.

**Moltbook** — 에이전트 전용 소셜 네트워크
- 2026-01-28 런칭(Matt Schlicht). Reddit 형태. 에이전트가 글 쓰고, 프로젝트 홍보하고, 업보트·평판을 쌓고, `submolts`라는 커뮤니티로 조직화. 인간은 관전.
- 규모는 출처마다 편차가 크다(3만 / 140만 등) — **수치는 인용하지 말거나 출처를 병기할 것.**
- 에이전트는 주로 OpenClaw(Claude·GPT·Gemini·Grok 래퍼)로 접속.
- 보안 결함: 공개 토큰으로 **아무 에이전트나 사칭 가능**했다. "에이전트들이 암호 언어를 만들고 있다"는 식의 가짜 글이 퍼져 소동. 연구자들은 "에이전트 인터넷이 어떻게 실패하는지 보여주는 라이브 데모"라고 평가.
- 2026-03 **Meta가 인수**, Meta Superintelligence Labs로 편입. Meta는 "always-on 디렉터리로 에이전트를 연결하는 방식"을 새롭다고 평가.

**Hivemoot** — GitHub 위의 자율 엔지니어링 팀 (검증: GitHub API 확인)
- `hivemoot/hivemoot`, TypeScript, Apache-2.0, 2026-01-31 생성, 최근 푸시 2026-07-09, 스타 16, 이슈 96.
- 역할을 가진 에이전트 팀이 **당신의 저장소**에 실제 컨트리뷰터로 등장: 이슈 열고, 코멘트로 토론하고, 코드 쓰고, PR 리뷰하고, **투표로 결정**하고, CI 통과하면 자동 머지. 👑Queen이 토론 기한·투표 시점을 관리.
- 결정적으로: **"에이전트는 당신의 하드웨어에서, 당신의 API 키로 돈다"** 를 명시. 클라우드 호스팅은 예정이지만 강제되지 않겠다고 선언.
- `hivemoot/colony` — 에이전트들이 무엇을 만들지 투표해서 실제로 만든 데모 프로젝트(스타 4, 최근 푸시 2026-03-26).

**핵심 한계:** Moltbook은 **협업이 아니라 사교**(그리고 이제 Meta 소유). Hivemoot은 진짜 공동 작업이지만 **"내 저장소, 내 에이전트, 내 규칙"** — 여러 소유자의 에이전트가 모이는 **공용 광장이 없다.** 그리고 백엔드는 대개 상용 API이지 개인 GPU가 아니다.

### 갈래 0. 조상 — 자원봉사 컴퓨팅

BOINC, Folding@home, SETI@home(1999). 유휴 자원 기부 모델의 원형이자, **금전 보상 없이도 사람이 참여한다**는 증명.
지금 논의의 인센티브 설계에서 반드시 참조해야 할 선례. (`awesome-volunteer-computing` 목록 참고)

---

## 3. 판정표

| 플랫폼 | P 개인 GPU | A 에이전트 주체 | C 퍼블릭 공동 프로젝트 |
|---|:---:|:---:|:---:|
| Petals / exo / Kalavai | ✅ | ❌ | ❌ |
| Prime Intellect | △ (기여자 다양) | ❌ | △ (모델 1개) |
| Bittensor / io.net / Gensyn | ❌ | ❌ | ❌ |
| Agentverse / Olas | ❌ | ✅ | ❌ |
| A2A / MCP (프로토콜) | — | ✅ | ❌ |
| Moltbook | ❌ | ✅ | △ (사교·홍보) |
| **Hivemoot** | ✅ | ✅ | ❌ (내 저장소 한정) |
| BOINC / Folding@home | ✅ | ❌ | ✅ |

**빈칸이 정확히 어디인가:**
`P + A` 는 Hivemoot이 이미 증명했다. `P + C` 는 BOINC가 25년 전에 증명했다.
**`P + A + C` 를 동시에 만족하는 것은 없다.**

한 문장으로: **"BOINC의 공개 공동 목표 + Hivemoot의 자율 협업 거버넌스 + Petals의 개인 GPU 참여"** 를 합친 자리가 비어 있다.

---

## 4. 그 자리가 비어 있는 이유 (= 설계 난제)

빈칸은 대개 아무도 생각 못 해서가 아니라 **어렵기 때문에** 비어 있다. 반드시 정면으로 다뤄야 할 것들:

1. **검증(trust) 문제** — 남의 GPU에서 나온 결과를 어떻게 믿는가. BOINC는 동일 작업을 중복 배포해 대조했다. 에이전트의 산출물은 코드/문서라 결정론적 비교가 안 된다. → 재현 가능한 검증 게이트(테스트·CI)를 신뢰의 단위로 삼는 설계가 자연스럽다. Hivemoot이 "CI 통과 시 자동 머지"로 푼 방식이 힌트.
2. **시빌·사칭** — Moltbook이 정확히 여기서 터졌다. 아무나 아무 에이전트를 사칭할 수 있으면 광장 자체가 무너진다. 신원(A2A Agent Card? 서명? 온체인?)을 초기 설계에 넣어야 한다.
3. **작업 분해와 배분** — BOINC는 워크유닛이 균질했다. 소프트웨어 프로젝트의 이슈는 난이도·문맥 요구량이 제각각이고, RTX 3060 에이전트와 4090 에이전트가 할 수 있는 일이 다르다. **이질적 능력을 전제로 한 라우팅**이 필요.
4. **로컬 모델의 실력 한계** — 개인 GPU에서 도는 7B~30B 급이 실제로 유의미한 PR을 쓸 수 있는가. → 이건 실험으로 답할 문제이고, **재료로서 가장 흥미로운 실증 코너**다.
5. **라이선스·저작권·책임** — 에이전트가 만든 산출물의 소유는 누구인가. 기여자 소유? 프로젝트 소유? CLA는 누가 서명하나.
6. **인센티브** — 토큰 보상으로 가면 갈래 2와 같은 함정(자원 임대업화). BOINC 계열의 비금전적 동기(평판·기여 가시화·학습)를 어떻게 설계할 것인가.
7. **남용·비용 폭탄** — 스웜이 인기를 끄는 순간 남용이 시작된다는 것이 Petals의 교훈.

---

## 5. 포스트로 뽑을 때의 갈래

- **(a) 조사 정리형** — 위 2~3장 그대로. 제목 후보: *"내 GPU 위의 에이전트들이 함께 일하는 플랫폼은 아직 없다 — 2026년 랜드스케이프"*
- **(b) 구상 제안형** — 4장의 난제에 대한 내 답을 붙여 아키텍처 초안까지. 블로그의 nextbrain 파이프라인과 접속.
- **(c) 실증형** — 로컬 모델 에이전트 2~3개를 실제 저장소에 붙여 Hivemoot 스타일로 돌려보고 결과 기록. **가장 이 블로그다운 형태**(작업기록 계열).

---

## 6. 발행 시 체크리스트

- [ ] 한/영 쌍으로 작성 (`.md` + `.en.md`, 동일 basename, 한글판에 `slug:`)
- [ ] `date` / `categories` / `tags` / `draft` 두 파일 동일하게
- [ ] 카테고리 후보: `ai-agent`
- [ ] **3장 판정표를 SVG 사분면 도식으로** — `static/images/diagrams/agent-platform-landscape.svg` (터미널 카드 스타일). 라벨이 한글이면 `-en.svg` 별도 제작
- [ ] 수치 인용 주의: Moltbook 에이전트 수, Agentverse 에이전트 수는 출처 간 편차 큼 → 단정하지 말고 출처 병기
- [ ] 전 직장 업체명 노출 없음 확인

---

## 7. 출처

**개인 GPU 풀링**
- Petals — https://petals.dev/ , https://github.com/bigscience-workshop/petals
- 분산 LLM 네트워크 비교(Petals·exo·Kalavai) — https://sharedllm.org/blog/sharedllm-vs-petals-vs-exo.html
- exo 2026 현실 점검 — https://www.runaihome.com/blog/exo-framework-distributed-vram-local-ai-2026/
- Kalavai — https://kalavai-net.github.io/kalavai-client/

**탈중앙 컴퓨트**
- Prime Intellect 블로그 — https://www.primeintellect.ai/blog
- Bittensor 2026 가이드 — https://www.cryptotimes.io/learn/bittensor-tao-guide/
- 탈중앙 GPU 네트워크 시장 — https://yellow.com/research/ai-compute-demand-crypto-gpu-networks-gap-2026

**에이전트 레지스트리·프로토콜**
- Agentverse 문서 — https://docs.agentverse.ai/documentation/getting-started/overview
- Olas — https://olas.network/agents
- A2A 1주년, 150+ 조직 — https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year
- A2A Linux Foundation 이관 — https://developers.googleblog.com/en/google-cloud-donates-a2a-to-linux-foundation/
- 에이전틱 웹 인프라 갭 분석(Agentverse) — https://arxiv.org/html/2606.20570
- 상호운용 프로토콜의 거버넌스 공백(MCP·A2A·ACP) — https://arxiv.org/pdf/2606.31498

**에이전트 협업·사회**
- Hivemoot — https://github.com/hivemoot/hivemoot , 데모: https://hivemoot.github.io/colony/
- Moltbook 학술 분석 — https://arxiv.org/html/2602.10127v1
- Moltbook 소개(Forbes) — https://www.forbes.com/sites/guneyyildiz/2026/01/31/inside-moltbook-the-social-network-where-14-million-ai-agents-talk-and-humans-just-watch/
- Meta 인수(TechCrunch) — https://techcrunch.com/2026/03/10/meta-acquired-moltbook-the-ai-agent-social-network-that-went-viral-because-of-fake-posts/

**자원봉사 컴퓨팅**
- BOINC 논문 — https://arxiv.org/pdf/1903.01699
- awesome-volunteer-computing — https://github.com/ranjithrajv/awesome-volunteer-computing
- 개방형 협업 분산 학습 — https://arxiv.org/pdf/2106.10207

---

## 8. 미검증 / 주의

- Moltbook·Agentverse의 에이전트 수치는 **직접 확인하지 않았다**(2차 보도 인용).
- Petals 공개 스웜의 현재 실질 가동률은 확인하지 못했다. 발행 전 https://health.petals.dev/ 로 재확인할 것.
- Prime Intellect가 **개인 소비자 GPU 참여를 허용하는지**는 블로그 목록에서 확인되지 않았다. 발행 전 문서 확인 필요.
- 검색 결과로 등장한 `hivemoot/hivemoot-agent`, `Hivekeep`, `NemoClaw` 등은 **실존 확인 실패 또는 미확인** — 인용하지 말 것.
