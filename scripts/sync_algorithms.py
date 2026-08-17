#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK
"""알고리즘 딕셔너리 정본(nextbrain MOC) → 공개 섹션(content/algorithms/_index.md) 생성.

정본에만 있는 열(기존 노트 링크 · 내 앵커)은 공개본에서 **떨어뜨린다**.
손으로 두 벌 유지하지 않기 위한 스크립트이므로, 공개본을 직접 편집하지 말 것.

사용:
  scripts/sync_algorithms.py            # 생성/갱신
  scripts/sync_algorithms.py --check    # 최신인지만 확인 (CI용, 어긋나면 exit 1)
"""
import argparse
import re
import sys
from pathlib import Path

try:
    import argcomplete
except ImportError:
    argcomplete = None

REPO = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = Path.home() / "nextbrain/wiki/_index/MOC-알고리즘딕셔너리.md"
DEFAULT_OUTPUT = REPO / "content/algorithms/_index.md"

SECTOR_RE = re.compile(r"^## (S\d+)\. (.+)$")

FRONTMATTER = """---
title: 알고리즘 딕셔너리
layout: single
url: /algorithms/
summary: "자율주행 · AGV · 다중로봇에 실제로 쓰이는 알고리즘을 섹터별로 정리한 사전. 각 항목은 '이게 없으면 뭐가 안 되는가'라는 한 줄로 요약했다."
ShowToc: true
TocOpen: false
ShowReadingTime: false
hideMeta: true
---

로봇을 만들다 보면 같은 알고리즘을 **3주 뒤에 다시 검색하고 있다.** 그때마다
"이게 정확히 뭘 푸는 거였지"부터 되짚는 게 아까워서, 실제로 쓰이는 것들을 섹터로 잘라 사전으로 만들었다.

각 항목의 설명은 정의가 아니라 **"이게 없으면 뭐가 안 되는가"** 다. 알고리즘은 답이 아니라
누군가 겪은 문제의 해결책이고, 문제를 모르면 언제 써야 할지도 모르기 때문이다.

> **이 페이지는 색인이다.** 항목별 상세(동작 원리 · 원전 논문 · 구현 코드 · 내가 쓰면서 겪은 것)는
> 하나씩 글로 풀어 이 아래에 붙여 나간다. 아직 링크가 없는 항목은 안 쓴 것이다.

**도메인 표기** — `AV` 자율주행차량 · `AGV` 산업 무인운반차/AMR · `MR` 다중로봇·플릿

"""

FOOTER = """
---

## 이 사전을 쓰는 법

**항목 수를 세는 용도가 아니다.** 내가 지금 겪는 문제를 왼쪽 「푸는 문제」 열에서 찾고,
그 줄의 알고리즘부터 파고들라고 만든 표다.

미완인 것을 밝혀 둔다 — 항목별 **특허 지형**과 **최신 적용 사례(CES 등)** 는 아직 조사하지 않았다.
상세 글을 쓸 때 항목마다 채운다.
"""


def parse(src: Path):
    """MOC 에서 (섹터코드, 섹터명, [(알고리즘, 푸는 문제, 도메인)]) 목록을 뽑는다."""
    sectors, cur = [], None
    for line in src.read_text(encoding="utf-8").splitlines():
        m = SECTOR_RE.match(line)
        if m:
            cur = (m.group(1), m.group(2).strip(), [])
            sectors.append(cur)
            continue
        if cur is None or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5:            # 항목 표만 5열 — 범례·백로그 표는 걸러진다
            continue
        name, problem, domain = cells[0], cells[1], cells[2]
        if name.startswith("---") or name.startswith("알고리즘"):
            continue
        cur[2].append((name, problem, domain))
    return [s for s in sectors if s[2]]


def render(sectors) -> str:
    out = [FRONTMATTER]
    total = sum(len(s[2]) for s in sectors)
    out.append(f"현재 **{len(sectors)}개 섹터 · {total}개 항목**.\n")
    for code, title, rows in sectors:
        out.append(f"\n## {code}. {title}\n")
        out.append("| 알고리즘 | 푸는 문제 | 도메인 |")
        out.append("|---|---|:---:|")
        for name, problem, domain in rows:
            out.append(f"| {name} | {problem} | {domain} |")
        out.append("")
    out.append(FOOTER)
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description="알고리즘 딕셔너리 정본 → 공개 섹션 생성")
    p.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="정본 MOC 경로")
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="공개본 출력 경로")
    p.add_argument("--check", action="store_true", help="갱신하지 않고 최신 여부만 확인")
    if argcomplete:
        argcomplete.autocomplete(p)
    args = p.parse_args()

    if not args.source.exists():
        print(f"정본을 찾을 수 없다: {args.source}", file=sys.stderr)
        return 2

    sectors = parse(args.source)
    if not sectors:
        print(f"항목 표를 하나도 못 읽었다 — 정본 표 형식이 바뀌었나: {args.source}", file=sys.stderr)
        return 2
    new = render(sectors)
    total = sum(len(s[2]) for s in sectors)

    if args.check:
        old = args.output.read_text(encoding="utf-8") if args.output.exists() else None
        if old == new:
            print(f"최신 — {len(sectors)}섹터 {total}항목")
            return 0
        print(f"어긋남 — 재생성 필요: {args.output}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(new, encoding="utf-8")
    print(f"생성: {args.output} ({len(sectors)}섹터 {total}항목)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
