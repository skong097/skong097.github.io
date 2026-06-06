# /projects/ GitHub 프로젝트 그래프 뷰 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/projects/` 상단의 "Projects" 배너를 GitHub 퍼블릭 레포(fork·archived 제외)를 가져와 보여주는 동적 force-directed 그래프 뷰로 교체한다. 하단 하드코딩 카드 36개는 절대 수정하지 않는다.

**Architecture:** Hugo + PaperMod 정적 사이트. `scripts/fetch_github_repos.sh`가 api.github.com에서 레포를 받아 `data/github_repos.json`으로 저장(로컬 수동 + CI 빌드 전 자동). Hugo shortcode `github-graph`가 `site.Data.github_repos`를 주입해 바닐라 JS + SVG로 중앙 허브 + 언어 클러스터 force-directed 그래프를 렌더하고 영구 미세 드리프트로 항상 움직인다.

**Tech Stack:** Hugo 0.162(local)/0.146(CI) extended, bash + curl + python3(정제), 바닐라 JS + SVG, GitHub Actions, PaperMod 다크/라이트.

> **커밋 정책:** 에이전트는 `git add/commit/push`를 실행하지 않는다. 각 Task "Commit" 스텝은 사용자에게 명령 블록을 제시하는 것으로 처리한다.
> **검증 방식:** 단위 테스트 프레임워크가 없으므로 (1) 부재/실패 확인 → (2) 구현 → (3) 검증 명령 통과로 대응. 도구: `hugo`(빌드), `python3 -m json.tool`(JSON), `bash -n`(스크립트 문법), `grep`(산출 HTML).

---

## File Structure

| 경로 | 책임 | Task |
|---|---|---|
| `scripts/fetch_github_repos.sh` | GitHub API → 정제 JSON (탭완성) | 1 |
| `scripts/completion.bash` | `_fetch_github_repos` 핸들러 추가 | 1 |
| `data/github_repos.json` | 레포 데이터 스냅샷 (CI가 갱신) | 1 |
| `layouts/shortcodes/github-graph.html` | 그래프 CSS+SVG+JS | 2 |
| `content/projects/_index.md` | cover 숨김 + shortcode 삽입 (카드 무수정) | 3 |
| `.github/workflows/hugo_workflow.yml` | 빌드 전 fetch 스텝 | 4 |

---

## Task 1: 수집 스크립트 + 데이터 스냅샷

**Files:**
- Create: `scripts/fetch_github_repos.sh`
- Modify: `scripts/completion.bash`
- Create: `data/github_repos.json` (스크립트 실행 산출물)

- [ ] **Step 1: 파일 부재 확인**

Run: `ls scripts/fetch_github_repos.sh data/github_repos.json 2>&1`
Expected: 둘 다 `No such file or directory`

- [ ] **Step 2: `scripts/fetch_github_repos.sh` 작성**

```bash
#!/usr/bin/env bash
# fetch_github_repos.sh — GitHub 퍼블릭 레포를 그래프 뷰 데이터로 수집
# 옵션:
#   -h, --help        사용법 출력
#   --user <name>     대상 GitHub 사용자 (기본: skong097)
#   --output <path>   출력 JSON 경로 (기본: data/github_repos.json)
# 동작: api.github.com 에서 레포를 받아 fork/archived 제외, 필요한 필드만 추려 JSON 저장.
#       GITHUB_TOKEN 환경변수가 있으면 인증 헤더로 사용(rate limit 완화). git 커밋은 안 함.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GH_USER="skong097"
OUTPUT="$REPO_ROOT/data/github_repos.json"

usage() { sed -n '2,8p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --user) GH_USER="${2:-}"; shift 2 ;;
    --user=*) GH_USER="${1#*=}"; shift ;;
    --output) OUTPUT="${2:-}"; shift 2 ;;
    --output=*) OUTPUT="${1#*=}"; shift ;;
    *) echo "알 수 없는 옵션: $1" >&2; usage; exit 2 ;;
  esac
done

AUTH=()
if [[ -n "${GITHUB_TOKEN:-}" ]]; then AUTH=(-H "Authorization: Bearer ${GITHUB_TOKEN}"); fi

echo "[gh-graph] ${GH_USER} 레포 수집 중…"
RAW="$(curl -sS "${AUTH[@]}" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/users/${GH_USER}/repos?per_page=100&sort=updated")"

printf '%s' "$RAW" | python3 -c '
import json, sys, datetime
raw = json.load(sys.stdin)
if not isinstance(raw, list):
    sys.stderr.write("GitHub API 응답이 예상과 다릅니다: %s\n" % str(raw)[:300]); sys.exit(1)
user, out_path = sys.argv[1], sys.argv[2]
repos = []
for r in raw:
    if r.get("fork") or r.get("archived"): continue
    repos.append({
        "name": r.get("name",""),
        "description": r.get("description") or "",
        "language": r.get("language") or "Other",
        "url": r.get("html_url",""),
        "stars": r.get("stargazers_count",0),
        "updated": (r.get("updated_at") or "")[:10],
        "topics": r.get("topics") or [],
    })
repos.sort(key=lambda x: x["updated"], reverse=True)
out = {"fetched": datetime.date.today().isoformat(), "user": user, "repos": repos}
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("[gh-graph] %d개 레포 저장 → %s" % (len(repos), out_path))
' "$GH_USER" "$OUTPUT"
```

- [ ] **Step 3: 실행 권한 부여 + 문법 확인**

Run: `chmod +x scripts/fetch_github_repos.sh && bash -n scripts/fetch_github_repos.sh && echo "syntax ok"`
Expected: `syntax ok`

- [ ] **Step 4: `--help` / 잘못된 옵션 검증 (네트워크 미사용)**

Run: `scripts/fetch_github_repos.sh --help; echo "---"; scripts/fetch_github_repos.sh --bad; echo "exit=$?"`
Expected: 사용법 출력(`fetch_github_repos.sh — GitHub 퍼블릭 레포를 그래프 뷰 데이터로 수집`, `--user`, `--output`) + `알 수 없는 옵션: --bad` + `exit=2`

- [ ] **Step 5: 실제 수집 실행 (네트워크)**

Run: `scripts/fetch_github_repos.sh`
Expected: `[gh-graph] N개 레포 저장 → .../data/github_repos.json` (N ≥ 0). 네트워크가 막혀 실패하면 BLOCKED로 보고.

- [ ] **Step 6: 데이터 유효성·필터 검증**

Run:
```
python3 -m json.tool data/github_repos.json >/dev/null && echo "JSON OK"
python3 -c '
import json
d=json.load(open("data/github_repos.json"))
print("user:", d["user"], "| fetched:", d["fetched"], "| repos:", len(d["repos"]))
req=["name","description","language","url","stars","updated","topics"]
print("missing-field:", [r.get("name") for r in d["repos"] if any(k not in r for k in req)] or "none")
print("languages:", sorted({r["language"] for r in d["repos"]}))
'
```
Expected: `JSON OK` + user=skong097 + 각 항목에 7개 필드 완비(`missing-field: none`).

- [ ] **Step 7: `scripts/completion.bash`에 핸들러 추가**

기존 파일 끝(마지막 `complete -F _run_kb_radar ...` 줄 다음)에 아래를 **추가**한다:
```bash

_fetch_github_repos() {
  local cur prev opts
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  opts="-h --help --user --output"
  case "$prev" in
    --output) COMPREPLY=( $(compgen -f -- "$cur") ); return 0 ;;
    --user) return 0 ;;
  esac
  COMPREPLY=( $(compgen -W "$opts" -- "$cur") )
}
complete -F _fetch_github_repos fetch_github_repos.sh ./fetch_github_repos.sh scripts/fetch_github_repos.sh
```

- [ ] **Step 8: completion.bash 문법 확인**

Run: `bash -n scripts/completion.bash && echo "syntax ok" && grep -c "_fetch_github_repos" scripts/completion.bash`
Expected: `syntax ok` + `2` (함수 정의 + complete 등록)

- [ ] **Step 9: Commit (사용자에게 명령 블록 제시)**

```bash
git add scripts/fetch_github_repos.sh scripts/completion.bash data/github_repos.json
git commit -m "feat(projects): GitHub 레포 수집 스크립트 + 데이터 스냅샷 추가

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: github-graph shortcode (force-directed SVG)

**Files:**
- Create: `layouts/shortcodes/github-graph.html`

- [ ] **Step 1: shortcode 부재 확인**

Run: `ls layouts/shortcodes/github-graph.html 2>&1`
Expected: `No such file or directory`

- [ ] **Step 2: `layouts/shortcodes/github-graph.html` 작성 (전체)**

```html
{{/* github-graph — /projects/ 상단 GitHub 레포 force-directed 그래프 뷰
     데이터: data/github_repos.json (scripts/fetch_github_repos.sh / CI 생성)
     의존성 없음(바닐라 JS + SVG). PaperMod 다크/라이트 연동. */}}
<div class="gh-graph-wrap" id="ghGraph">
  <div class="gh-graph-head">
    <span class="gh-graph-title">GitHub Projects</span>
    <span class="gh-graph-sub" id="ghGraphSub"></span>
  </div>
  <svg class="gh-graph-svg" id="ghGraphSvg" viewBox="0 0 960 420" preserveAspectRatio="xMidYMid meet" aria-label="GitHub 프로젝트 그래프"></svg>
  <div class="gh-graph-tip" id="ghGraphTip" hidden></div>
  <div class="gh-graph-empty" id="ghGraphEmpty" hidden>
    GitHub 프로젝트를 준비 중입니다 ·
    <a href="https://github.com/skong097" target="_blank" rel="noopener">github.com/skong097</a>
  </div>
</div>

<style>
.gh-graph-wrap{
  --gh-bg:#f0f2f5; --gh-card:#ffffff; --gh-border:#e2e6ea;
  --gh-text:#1a202c; --gh-text2:#64748b; --gh-edge:#cbd5e1; --gh-hub:#0891b2;
  position:relative; background:var(--gh-bg); border:1px solid var(--gh-border);
  border-radius:14px; margin:0 0 2rem; overflow:hidden;
  font-family:'Noto Sans KR',sans-serif; transition:background .3s,border-color .3s;
}
[data-theme="dark"] .gh-graph-wrap{
  --gh-bg:#0a0e17; --gh-card:#111827; --gh-border:#1e2d3d;
  --gh-text:#e2e8f0; --gh-text2:#64748b; --gh-edge:#243244; --gh-hub:#00e5ff;
}
.gh-graph-head{
  position:absolute; top:0; left:0; right:0; z-index:2; pointer-events:none;
  display:flex; align-items:baseline; gap:.6rem; padding:.9rem 1.1rem;
}
.gh-graph-title{ font-family:'JetBrains Mono',monospace; font-weight:700; font-size:1rem; color:var(--gh-hub); }
.gh-graph-sub{ font-family:'JetBrains Mono',monospace; font-size:.7rem; color:var(--gh-text2); }
.gh-graph-svg{ display:block; width:100%; height:420px; touch-action:none; cursor:grab; }
.gh-edge{ stroke:var(--gh-edge); stroke-width:1; transition:opacity .2s; }
.gh-node{ cursor:pointer; }
.gh-node circle{ transition:opacity .2s, stroke-width .2s; }
.gh-node-label{ fill:var(--gh-text); font-family:'JetBrains Mono',monospace; font-size:9px; pointer-events:none; user-select:none; }
.gh-hub-label{ fill:var(--gh-text); font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:700; pointer-events:none; }
.gh-dim{ opacity:.15; }
.gh-graph-tip{
  position:absolute; z-index:3; max-width:260px; pointer-events:none;
  background:var(--gh-card); border:1px solid var(--gh-border); border-radius:8px;
  padding:.6rem .7rem; font-size:.74rem; color:var(--gh-text); line-height:1.45;
  box-shadow:0 6px 20px rgba(0,0,0,.18);
}
.gh-graph-tip .t-name{ font-weight:700; color:var(--gh-hub); display:block; margin-bottom:.2rem; }
.gh-graph-tip .t-meta{ color:var(--gh-text2); font-family:'JetBrains Mono',monospace; font-size:.68rem; margin-top:.3rem; }
.gh-graph-empty{ padding:3rem 1rem; text-align:center; color:var(--gh-text2); font-size:.85rem; }
.gh-graph-empty a{ color:var(--gh-hub); }
@media (max-width:768px){ .gh-graph-svg{ height:300px; } }
</style>

<script>
(function(){
  const GD = JSON.parse({{ (site.Data.github_repos) | jsonify }});
  const repos = (GD && GD.repos) || [];
  const user  = (GD && GD.user) || "skong097";
  const svg = document.getElementById('ghGraphSvg');
  const tip = document.getElementById('ghGraphTip');
  const wrap = document.getElementById('ghGraph');
  const sub = document.getElementById('ghGraphSub');

  if (!repos.length){
    document.getElementById('ghGraphEmpty').hidden = false;
    svg.style.display = 'none';
    return;
  }
  sub.textContent = repos.length + " repos";

  const SVGNS = "http://www.w3.org/2000/svg";
  const W = 960, H = 420, CX = W/2, CY = H/2;
  const LANG_COLORS = {
    "Python":"#3b82f6","C++":"#f97316","C":"#64748b","JavaScript":"#eab308",
    "TypeScript":"#0ea5e9","HTML":"#ef4444","CSS":"#8b5cf6","Shell":"#22c55e",
    "Jupyter Notebook":"#f59e0b","Java":"#dc2626","Go":"#06b6d4","Rust":"#a16207",
    "Dockerfile":"#0d9488","Other":"#94a3b8"
  };
  function colorOf(lang){
    if (LANG_COLORS[lang]) return LANG_COLORS[lang];
    let h=0; for(let i=0;i<lang.length;i++) h=(h*31+lang.charCodeAt(i))%360;
    return "hsl("+h+",60%,55%)";
  }
  function esc(s){ return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }

  // ── 노드/엣지 구성: 허브 + 언어 + 레포 ──
  const nodes = [];
  const edges = [];
  const byId = {};
  function addNode(n){ n.x=CX+(Math.random()-0.5)*200; n.y=CY+(Math.random()-0.5)*120; n.vx=0; n.vy=0; nodes.push(n); byId[n.id]=n; return n; }

  const hub = addNode({id:"__hub", type:"hub", label:user, r:24});
  hub.x=CX; hub.y=CY;
  const langSet = {};
  repos.forEach(r=>{ langSet[r.language]=(langSet[r.language]||0)+1; });
  Object.keys(langSet).forEach(lang=>{
    const ln = addNode({id:"lang:"+lang, type:"lang", label:lang, color:colorOf(lang), r:13});
    edges.push({a:hub.id, b:ln.id, rest:140});
  });
  repos.forEach(r=>{
    const rn = addNode({id:"repo:"+r.name, type:"repo", label:r.name, color:colorOf(r.language), r:6+Math.min(6,r.stars), data:r});
    edges.push({a:"lang:"+r.language, b:rn.id, rest:64});
  });

  // ── SVG 요소 생성 ──
  const edgeEls = edges.map(e=>{
    const l=document.createElementNS(SVGNS,"line"); l.setAttribute("class","gh-edge"); svg.appendChild(l);
    e.el=l; return e;
  });
  const nodeEls = nodes.map(n=>{
    const g=document.createElementNS(SVGNS,"g"); g.setAttribute("class","gh-node");
    const c=document.createElementNS(SVGNS,"circle");
    c.setAttribute("r",n.r);
    c.setAttribute("fill", n.type==="hub" ? "var(--gh-hub)" : (n.color||"#94a3b8"));
    c.setAttribute("stroke","var(--gh-card)"); c.setAttribute("stroke-width","2");
    g.appendChild(c);
    if(n.type!=="repo" || n.r>=8){
      const t=document.createElementNS(SVGNS,"text");
      t.setAttribute("class", n.type==="hub"?"gh-hub-label":"gh-node-label");
      t.setAttribute("text-anchor","middle"); t.setAttribute("dy", n.r + 11);
      t.textContent = n.type==="hub" ? "@"+n.label : n.label;
      g.appendChild(t);
    }
    svg.appendChild(g); n.g=g; n.c=c;
    return n;
  });

  // ── 인접 맵(하이라이트용) ──
  const adj = {};
  nodes.forEach(n=> adj[n.id]=new Set([n.id]));
  edges.forEach(e=>{ adj[e.a].add(e.b); adj[e.b].add(e.a); });

  // ── 인터랙션 ──
  const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let dragging=null, hover=null, langFilter=null;

  function showTip(n, evt){
    const r=n.data;
    let html = '<span class="t-name">'+esc(n.type==="repo"?r.name:n.label)+'</span>';
    if(n.type==="repo"){
      if(r.description) html += esc(r.description);
      html += '<div class="t-meta">'+esc(r.language)+' · ★'+r.stars+' · '+esc(r.updated)+'</div>';
    } else if(n.type==="lang"){
      html += '<div class="t-meta">'+langSet[n.label]+' repos</div>';
    } else {
      html += '<div class="t-meta">GitHub 프로필</div>';
    }
    tip.innerHTML=html; tip.hidden=false;
    const wr=wrap.getBoundingClientRect();
    tip.style.left=Math.min(wr.width-270,(evt.clientX-wr.left+12))+"px";
    tip.style.top=(evt.clientY-wr.top+12)+"px";
  }
  function hideTip(){ tip.hidden=true; }

  function applyHighlight(){
    const focus = hover ? adj[hover.id] : null;
    nodeEls.forEach(n=>{
      let on=true;
      if(focus) on=focus.has(n.id);
      else if(langFilter) on = (n.type==="hub")||(n.id==="lang:"+langFilter)||(n.type==="repo"&&n.data.language===langFilter);
      n.g.classList.toggle("gh-dim", !on);
    });
    edgeEls.forEach(e=>{
      let on=true;
      if(focus) on = (e.a===hover.id||e.b===hover.id);
      else if(langFilter) on = (e.a==="lang:"+langFilter)||(e.b==="lang:"+langFilter)||(e.a==="__hub"&&e.b==="lang:"+langFilter);
      e.el.classList.toggle("gh-dim", !on);
    });
  }

  nodeEls.forEach(n=>{
    n.g.addEventListener("pointerenter", e=>{ hover=n; showTip(n,e); applyHighlight(); });
    n.g.addEventListener("pointermove", e=>{ if(hover===n) showTip(n,e); });
    n.g.addEventListener("pointerleave", ()=>{ hover=null; hideTip(); applyHighlight(); });
    n.g.addEventListener("pointerdown", e=>{ dragging=n; n.g.setPointerCapture(e.pointerId); svg.style.cursor="grabbing"; });
    n.g.addEventListener("pointerup", e=>{
      svg.style.cursor="grab";
      if(dragging===n && Math.abs(n.vx)<2 && Math.abs(n.vy)<2){
        if(n.type==="repo"){ window.open(n.data.url,"_blank","noopener"); }
        else if(n.type==="hub"){ window.open("https://github.com/"+user,"_blank","noopener"); }
        else if(n.type==="lang"){ langFilter = (langFilter===n.label)?null:n.label; applyHighlight(); }
      }
      dragging=null;
    });
  });
  svg.addEventListener("pointermove", e=>{
    if(!dragging) return;
    const pt=svg.getBoundingClientRect();
    dragging.x=(e.clientX-pt.left)/pt.width*W;
    dragging.y=(e.clientY-pt.top)/pt.height*H;
    dragging.vx=0; dragging.vy=0;
  });

  // ── 물리 시뮬레이션 ──
  function tick(){
    for(let i=0;i<nodes.length;i++){
      const a=nodes[i];
      for(let j=i+1;j<nodes.length;j++){
        const b=nodes[j];
        let dx=a.x-b.x, dy=a.y-b.y; let d2=dx*dx+dy*dy; if(d2<1)d2=1;
        const f=2200/d2; const d=Math.sqrt(d2);
        const fx=f*dx/d, fy=f*dy/d;
        a.vx+=fx; a.vy+=fy; b.vx-=fx; b.vy-=fy;
      }
    }
    edges.forEach(e=>{
      const a=byId[e.a], b=byId[e.b];
      let dx=b.x-a.x, dy=b.y-a.y; let d=Math.sqrt(dx*dx+dy*dy)||1;
      const f=(d-e.rest)*0.02; const fx=f*dx/d, fy=f*dy/d;
      a.vx+=fx; a.vy+=fy; b.vx-=fx; b.vy-=fy;
    });
    nodes.forEach(n=>{
      const g = n.type==="hub"?0.06:0.004;
      n.vx += (CX-n.x)*g; n.vy += (CY-n.y)*g;
      if(!reduce && n!==dragging){ n.vx += (Math.random()-0.5)*0.3; n.vy += (Math.random()-0.5)*0.3; }
      n.vx*=0.9; n.vy*=0.9;
      if(n.type==="hub" || n===dragging){ /* 허브/드래그 중엔 자유 적용 최소화 */ }
      n.x+=n.vx; n.y+=n.vy;
      n.x=Math.max(n.r+4,Math.min(W-n.r-4,n.x));
      n.y=Math.max(n.r+16,Math.min(H-n.r-14,n.y));
    });
  }
  function render(){
    edges.forEach(e=>{ const a=byId[e.a],b=byId[e.b]; e.el.setAttribute("x1",a.x); e.el.setAttribute("y1",a.y); e.el.setAttribute("x2",b.x); e.el.setAttribute("y2",b.y); });
    nodes.forEach(n=>{ n.g.setAttribute("transform","translate("+n.x+","+n.y+")"); });
  }
  if(reduce){
    for(let k=0;k<400;k++) tick();
    render();
  } else {
    (function loop(){ tick(); render(); requestAnimationFrame(loop); })();
  }
})();
</script>
```

- [ ] **Step 3: shortcode 단독 렌더 검증 (임시 테스트 페이지)**

Run:
```
mkdir -p content/_ghtest && printf -- '---\ntitle: ghtest\n---\n{{< github-graph >}}\n' > content/_ghtest/index.md
hugo --quiet 2>&1 | tail -5; echo "exit=${PIPESTATUS[0]}"
grep -c "gh-graph-wrap\|ghGraphSvg" public/_ghtest/index.html
grep -o "GitHub Projects" public/_ghtest/index.html | head -1
rm -rf content/_ghtest public/_ghtest
```
Expected: `exit=0` + `gh-graph-wrap`/`ghGraphSvg` 카운트 ≥1 + `GitHub Projects` 출력. (데이터가 있으면 빈 상태 대신 SVG가 들어감.)

- [ ] **Step 4: 데이터 주입 확인**

Run: (Step 3을 반복하되 삭제 전에) — 또는 Task 3 통합 후 확인. 간단 확인:
```
mkdir -p content/_ghtest && printf -- '---\ntitle: ghtest\n---\n{{< github-graph >}}\n' > content/_ghtest/index.md
hugo --quiet >/dev/null 2>&1
python3 -c '
import re
h=open("public/_ghtest/index.html",encoding="utf-8").read()
m=re.search(r"JSON\.parse\((.*?)\);\s*\n\s*const repos",h,re.S)
print("데이터 주입 패턴:", "발견" if m else "없음(빈데이터면 정상일 수 있음)")
print("repos 키 존재:", "\"repos\"" in h)
'
rm -rf content/_ghtest public/_ghtest
```
Expected: `"repos" 키 존재: True` (Task 1에서 만든 데이터가 주입됨).

- [ ] **Step 5: Commit (사용자에게 명령 블록 제시)**

```bash
git add layouts/shortcodes/github-graph.html
git commit -m "feat(projects): GitHub force-directed 그래프 shortcode 추가

중앙 허브 + 언어 클러스터, 영구 드리프트 물리, 호버 툴팁·드래그·클릭,
PaperMod 다크/라이트 연동, reduced-motion 폴백.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: /projects/ 페이지 통합 (배너 숨김 + shortcode 삽입)

**Files:**
- Modify: `content/projects/_index.md` (front matter cover + 본문 최상단만; 카드 영역 무수정)

- [ ] **Step 1: 현재 상태 확인 (카드 수 기준선 기록)**

Run:
```
grep -n "hidden: false" content/projects/_index.md
grep -c "project-card-link" content/projects/_index.md
grep -c "github-graph" content/projects/_index.md
```
Expected: cover `hidden: false` 라인 존재 + project-card-link **36** + github-graph **0**

- [ ] **Step 2: front matter에서 배너 숨김**

`content/projects/_index.md`의 front matter에서:
```yaml
cover:
  image: images/covers/projects-cover.png
  alt: Projects
  hidden: false
```
의 `hidden: false`를 다음으로 바꾼다(단일 페이지에서만 숨김):
```yaml
cover:
  image: images/covers/projects-cover.png
  alt: Projects
  hidden: false
  hiddenInSingle: true
```

- [ ] **Step 3: 본문 최상단에 shortcode 삽입**

front matter 닫는 `---` 다음 줄(현재 빈 줄 뒤, `<style>` 앞)에 shortcode 한 줄과 빈 줄을 삽입한다. 즉 파일이 이렇게 시작하도록:
```
---
title: 프로젝트
layout: single
url: /projects/
ShowToc: false
ShowReadingTime: false
hideMeta: true
cover:
  image: images/covers/projects-cover.png
  alt: Projects
  hidden: false
  hiddenInSingle: true
---

{{< github-graph >}}

<style>
```
**그 아래 `<style>`부터 끝까지(카드 36개 포함)는 한 글자도 바꾸지 않는다.**

- [ ] **Step 4: 빌드 + 통합 검증 (카드 보존 확인)**

Run:
```
hugo --quiet 2>&1 | tail -5; echo "exit=${PIPESTATUS[0]}"
echo "card-links: $(grep -c 'project-card-link' public/projects/index.html)"
echo "graph: $(grep -c 'gh-graph-wrap' public/projects/index.html)"
echo "cover-banner: $(grep -c 'projects-cover.png' public/projects/index.html)"
```
Expected: `exit=0` + `card-links` 36 (하단 카드 보존) + `graph` ≥1 (그래프 삽입) + `cover-banner` 0 (상단 배너 숨겨짐).

- [ ] **Step 5: 로컬 육안 확인 (선택)**

Run: `./run_server.sh` → `http://localhost:1313/projects/` 접속 → 상단에 움직이는 그래프, 그 아래 기존 카드들 확인. Ctrl+C로 종료.
Expected: 상단 그래프(노드가 천천히 움직임, 호버 툴팁, 클릭 시 새 탭) + 하단 카드 정상.

- [ ] **Step 6: Commit (사용자에게 명령 블록 제시)**

```bash
git add content/projects/_index.md
git commit -m "feat(projects): 상단 배너를 GitHub 그래프 뷰로 교체

cover hiddenInSingle 처리 후 본문 최상단에 github-graph shortcode 삽입.
하단 하드코딩 카드는 무수정.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: CI 빌드 전 자동 갱신

**Files:**
- Modify: `.github/workflows/hugo_workflow.yml`

- [ ] **Step 1: 현재 빌드 스텝 확인**

Run: `grep -n "Setup Pages\|Build with Hugo\|Checkout" .github/workflows/hugo_workflow.yml`
Expected: `Checkout`, `Setup Pages`, `Build with Hugo` 스텝이 이 순서로 존재.

- [ ] **Step 2: fetch 스텝 추가 (Build with Hugo 직전)**

`.github/workflows/hugo_workflow.yml`에서 `- name: Build with Hugo`로 시작하는 블록 **바로 앞**에 아래 스텝을 삽입한다(들여쓰기는 다른 `- name:` 스텝과 동일하게 6칸):
```yaml
      - name: Refresh GitHub repos data
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          bash scripts/fetch_github_repos.sh || echo "fetch 실패 — 커밋된 스냅샷으로 빌드"
```

- [ ] **Step 3: 워크플로 YAML 유효성 검증**

Run: `python3 -c "import yaml,sys; d=yaml.safe_load(open('.github/workflows/hugo_workflow.yml')); steps=d['jobs']['build']['steps']; names=[s.get('name') for s in steps]; print(names); assert 'Refresh GitHub repos data' in names; i=names.index('Refresh GitHub repos data'); assert i < names.index('Build with Hugo'), 'fetch must precede build'; print('order OK')"`
Expected: 스텝 이름 리스트 출력 + `order OK` (fetch가 Build보다 앞).

- [ ] **Step 4: 로컬 빌드 영향 없음 확인**

Run: `hugo --quiet 2>&1 | tail -3; echo "exit=${PIPESTATUS[0]}"`
Expected: `exit=0` (워크플로 변경은 로컬 빌드에 영향 없음).

- [ ] **Step 5: Commit (사용자에게 명령 블록 제시)**

```bash
git add .github/workflows/hugo_workflow.yml
git commit -m "ci(projects): 빌드 전 GitHub 레포 데이터 자동 갱신 스텝 추가

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

> 참고: 푸시 후 GitHub Actions가 `secrets.GITHUB_TOKEN`으로 fetch → 빌드하므로, 새 레포/업데이트가 매 배포 시 자동 반영된다.

---

## Self-Review 결과

- **Spec 커버리지**: 데이터흐름(T1·T4), fetch 스크립트·탭완성(T1), 스키마(T1), CI 자동갱신(T4), 그래프 구조/물리/인터랙션/폴백/접근성(T2), 페이지 통합·배너 숨김·카드 보존(T3) — 스펙 11개 섹션 대응됨.
- **플레이스홀더**: 없음. 모든 코드/명령/기대출력 구체값.
- **타입/이름 일관성**: 데이터 키(`fetched`,`user`,`repos`,`name`,`description`,`language`,`url`,`stars`,`updated`,`topics`)가 T1 스크립트 → T2 shortcode(`r.name`/`r.language`/`r.url`/`r.stars`/`r.updated`/`r.description`)에서 동일. shortcode 요소 id(`ghGraphSvg`,`ghGraphTip`,`ghGraphEmpty`,`ghGraphSub`,`ghGraph`)와 CSS 클래스(`gh-graph-*`,`gh-node`,`gh-edge`,`gh-dim`)가 HTML/JS/CSS에서 일치. `fetch_github_repos.sh` 이름이 T1 스크립트 → T1 completion → T4 워크플로에서 동일.
- **범위 보호**: T3에서 카드(`project-card-link` 36개) 수가 빌드 산출물에서 그대로인지 검증으로 무수정 보장.
