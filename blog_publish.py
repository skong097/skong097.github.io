#!/usr/bin/env python3
"""
blog_publish.py — 자료.md → Hugo 포스트 자동 생성 + 미리보기 후 선택 배포

사용법:
    python blog_publish.py              # references/ 처리 → 미리보기 → push 선택
    python blog_publish.py --dry-run    # 실제 변경 없이 미리보기
    python blog_publish.py --status     # 현재 포스트 현황
    python blog_publish.py --publish    # draft 포스트 공개 전환 (대화형 선택)

흐름:
    references/**/*.md 수집
        → 카테고리 자동 분류
        → Hugo frontmatter 생성 (draft: true)
        → content/posts/<category>/ 배치
        → hugo server -D 실행 (브라우저 확인)
        → Ctrl+C → push 여부 선택

작성일: 2026-03-21
"""

import os
import re
import sys
import json
import hashlib
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════
#  설정
# ═══════════════════════════════════════════════
HOME       = Path.home()
BLOG_ROOT  = HOME / "dev_ws" / "blog"
REFS_DIR   = BLOG_ROOT / "references"
POSTS_DIR  = BLOG_ROOT / "content" / "posts"
STATE_FILE = BLOG_ROOT / ".publish_state.json"

CATEGORY_MAP = {
    "ros2":           "ros2",
    "ai-ml":          "ai-ml",
    "vision-ai":      "vision-ai",
    "robotics":       "robotics",
    "mlops":          "mlops",
    "robot-network":  "robot-network",
    "robot-security": "robot-security",
    "big-data":       "big-data",
    "dev-tools":      "dev-tools",
    "project":        "dev-tools",
    "worklog":        "dev-tools",
    "smart-home":     "smart-home",
}

CATEGORY_KEYWORDS = {
    "ros2": {
        "high": ["ros2", "ros 2", "jazzy", "humble", "nav2", "gazebo",
                 "colcon", "ament", "launch", "rclpy", "topic", "service",
                 "action server", "action client", "guard_brain",
                 "slam_toolbox", "ghost-5", "ghost5", "swarm", "zenoh",
                 "rmw", "fastdds"],
        "medium": ["subscriber", "publisher", "tf2", "urdf", "xacro",
                   "rviz", "rosbag", "dds", "qos", "cmd_vel", "/scan"],
        "low": ["robot", "sensor", "lidar"],
    },
    "ai-ml": {
        "high": ["random forest", "st-gcn", "stgcn", "lstm", "transformer",
                 "fine-tuning", "fine_tuning", "pretrained", "pre-trained",
                 "epoch", "learning rate", "class_weight", "f1-score",
                 "confusion matrix", "hyperparameter", "randomforestclassifier",
                 "llm", "exaone", "ollama", "langchain", "langgraph"],
        "medium": ["accuracy", "precision", "recall", "auc", "roc",
                   "train", "validation", "test set", "overfitting",
                   "batch size", "optimizer", "cross-validation", "모델 학습"],
        "low": ["model", "feature", "predict", "classification"],
    },
    "vision-ai": {
        "high": ["yolo", "pose estimation", "keypoint", "키포인트",
                 "fall detection", "낙상", "skeleton", "bounding box",
                 "opencv", "mediapipe", "insightface", "arcface",
                 "낙상 감지", "home safe", "facial recognition", "얼굴 인식"],
        "medium": ["frame", "video", "camera", "inference", "webcam",
                   "detection", "tracking", "confidence"],
        "low": ["image", "pixel", "resolution"],
    },
    "robotics": {
        "high": ["kevin patrol", "kevin_patrol", "자율주행", "slam",
                 "a* ", "a-star", "astar", "경로 계획", "path planning",
                 "navigation", "waypoint", "occupancy grid",
                 "patrol", "fleet", "pinky", "quadruped"],
        "medium": ["robot", "collision", "충돌", "obstacle",
                   "autonomous", "multi-robot", "순찰"],
        "low": ["motor", "imu", "odometry"],
    },
    "mlops": {
        "high": ["pipeline", "파이프라인", "data augmentation", "데이터 증강",
                 "feature engineering", "auto labeling",
                 "모델 비교", "model comparison", "배포", "deploy"],
        "medium": ["preprocessing", "전처리", "normalization", "정규화",
                   "dataset", "데이터셋", "experiment"],
        "low": ["script", "automation", "batch", "csv", "pkl"],
    },
    "dev-tools": {
        "high": ["pyqt6", "pyqt", "dashboard", "대시보드", "dark theme",
                 "다크 테마", "fastapi", "gui", "widget", "qss",
                 "hugo", "github pages", "블로그", "rosforge"],
        "medium": ["layout", "sidebar", "panel", "chart", "plot",
                   "toast", "alert", "ui", "ux", "css"],
        "low": ["button", "window", "font", "style"],
    },
    "robot-network": {
        "high": ["robot network", "로봇 네트워크", "swarm", "mesh network",
                 "multi-robot communication", "zenoh", "redis"],
        "medium": ["protocol", "bandwidth", "latency", "네트워크", "sync"],
        "low": ["socket", "tcp", "udp", "mqtt", "wireless"],
    },
    "robot-security": {
        "high": ["robot security", "로봇 보안", "sros2", "jwt", "hmac",
                 "authentication", "인증", "encryption", "암호화",
                 "smartgate", "2fa", "liveness"],
        "medium": ["vulnerability", "취약점", "firewall", "certificate",
                   "tls", "ssl", "token", "permission", "권한"],
        "low": ["security", "보안", "threat", "attack"],
    },
    "smart-home": {
        "high": ["smart home", "스마트홈", "iot", "esp32", "voice iot",
                 "wake word", "porcupine", "whisper", "tts", "stt",
                 "음성 인식", "음성 제어", "스마트 게이트"],
        "medium": ["mqtt", "websocket", "servo", "pir", "sensor",
                   "자동화", "automation"],
        "low": ["wifi", "bluetooth", "relay", "led"],
    },
    "big-data": {
        "high": ["big data", "빅데이터", "kafka", "elasticsearch",
                 "data lake", "hadoop", "spark"],
        "medium": ["로그 분석", "log analysis", "데이터 수집", "mysql",
                   "mongodb", "시계열", "time series"],
        "low": ["data", "데이터", "db", "query", "sql"],
    },
}

CATEGORY_PRIORITY = {
    "vision-ai": 0, "ai-ml": 1, "robotics": 2, "ros2": 3,
    "smart-home": 4, "mlops": 5, "robot-network": 6,
    "robot-security": 7, "big-data": 8, "dev-tools": 9,
}


# ═══════════════════════════════════════════════
#  분류 엔진
# ═══════════════════════════════════════════════
def classify_file(filepath: Path) -> str:
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return "dev-tools"

    filename   = filepath.stem.lower().replace("-", " ").replace("_", " ")
    title      = ""
    for line in content.split("\n")[:20]:
        s = line.strip()
        if s.startswith("# ") and not s.startswith("##"):
            title = s[2:].lower()
            break

    title_area = f"{filename} {title}"
    body       = content[:3000].lower()
    scores     = {}

    for cat, levels in CATEGORY_KEYWORDS.items():
        score = 0
        for level, keywords in levels.items():
            weight = {"high": 3, "medium": 2, "low": 1}[level]
            for kw in keywords:
                kw_l = kw.lower()
                score += title_area.count(kw_l) * weight * 2
                score += body.count(kw_l) * weight
        scores[cat] = score

    sorted_cats = sorted(
        scores.items(),
        key=lambda x: (-x[1], CATEGORY_PRIORITY.get(x[0], 99))
    )
    return sorted_cats[0][0] if sorted_cats[0][1] > 0 else "dev-tools"


# ═══════════════════════════════════════════════
#  frontmatter 처리
# ═══════════════════════════════════════════════
def has_frontmatter(content: str) -> bool:
    return content.strip().startswith("---")


def extract_frontmatter_field(content: str, field: str) -> str:
    m = re.search(rf'^{field}:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
    return m.group(1).strip() if m else ""


def extract_md_title(content: str) -> str:
    for line in content.split("\n")[:30]:
        s = line.strip()
        if s.startswith("# ") and not s.startswith("##"):
            return s[2:].strip()
    return ""


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s가-힣-]", "", text)
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text[:60] if text else "untitled"


def extract_tags(content: str, category: str) -> list[str]:
    tags = [category]
    body = content[:2000].lower()
    tag_hints = {
        "ros2":           ["nav2", "slam", "gazebo", "rclpy", "zenoh"],
        "ai-ml":          ["llm", "pytorch", "tensorflow", "fine-tuning", "exaone"],
        "vision-ai":      ["yolo", "opencv", "mediapipe", "insightface"],
        "robotics":       ["slam", "navigation", "fleet", "patrol"],
        "smart-home":     ["esp32", "fastapi", "whisper", "porcupine"],
        "dev-tools":      ["pyqt6", "fastapi", "hugo", "rosforge"],
        "robot-security": ["jwt", "sros2", "hmac", "2fa"],
    }
    for kw in tag_hints.get(category, []):
        if kw in body and kw not in tags:
            tags.append(kw)
    return tags[:5]


def make_description(content: str) -> str:
    lines = [l.strip() for l in content.split("\n")
             if l.strip() and not l.strip().startswith("#")
             and not l.strip().startswith("---")]
    return " ".join(lines[:3])[:120].replace('"', "'")


def build_frontmatter(title: str, category: str,
                      tags: list[str], desc: str, date_str: str) -> str:
    tags_yaml = ", ".join(f'"{t}"' for t in tags)
    return (
        f'---\n'
        f'title: "{title}"\n'
        f'date: {date_str}\n'
        f'draft: true\n'
        f'tags: [{tags_yaml}]\n'
        f'categories: ["{category}"]\n'
        f'description: "{desc}"\n'
        f'---\n\n'
    )


# ═══════════════════════════════════════════════
#  상태 관리
# ═══════════════════════════════════════════════
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"generated": {}}


def save_state(state: dict):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def file_hash(filepath: Path) -> str:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ═══════════════════════════════════════════════
#  파일 처리
# ═══════════════════════════════════════════════
def process_file(src: Path, state: dict, dry_run: bool = False) -> dict | None:
    """단일 .md → content/posts/ 변환 (draft: true)"""
    content   = src.read_text(encoding="utf-8", errors="replace")
    src_hash  = file_hash(src)
    state_key = str(src)

    # 변경 없는 파일 스킵
    if state_key in state["generated"]:
        if state["generated"][state_key].get("hash") == src_hash:
            return None

    category    = classify_file(src)
    dest_subdir = CATEGORY_MAP.get(category, "dev-tools")

    if has_frontmatter(content):
        title = extract_frontmatter_field(content, "title")
        # draft 값을 true로 보정
        if "draft:" in content:
            new_content = re.sub(
                r'^draft:\s*(true|false)', 'draft: true',
                content, flags=re.MULTILINE
            )
        else:
            new_content = content.replace("---\n", "---\ndraft: true\n", 1)
    else:
        title       = (extract_md_title(content)
                       or src.stem.replace("-", " ").replace("_", " ").title())
        tags        = extract_tags(content, category)
        desc        = make_description(content)
        date_str    = datetime.now().strftime("%Y-%m-%d")
        new_content = build_frontmatter(title, category, tags, desc, date_str) + content

    slug      = slugify(title) if title else slugify(src.stem)
    dest_dir  = POSTS_DIR / dest_subdir
    dest_path = dest_dir / f"{slug}.md"

    # slug 충돌 방지
    if dest_path.exists() and state_key not in state["generated"]:
        dest_path = dest_dir / f"{slug}-{src.stem[:10]}.md"

    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(new_content, encoding="utf-8")

    return {
        "src":          str(src),
        "dest":         str(dest_path),
        "category":     category,
        "title":        title,
        "hash":         src_hash,
        "generated_at": datetime.now().isoformat(),
    }


def scan_references() -> list[Path]:
    if not REFS_DIR.exists():
        return []
    exclude = {".collect_state.json", ".category_index.json"}
    return sorted(
        md for md in REFS_DIR.rglob("*.md")
        if md.is_file() and md.name not in exclude
    )


# ═══════════════════════════════════════════════
#  Hugo 미리보기 + Git push
# ═══════════════════════════════════════════════
def run_hugo_preview():
    """hugo server -D 실행 → Ctrl+C 대기"""
    print("\n  🌐 Hugo 로컬 서버 시작 중...")
    print("  📌 브라우저: http://localhost:1313/posts/")
    print("  ⏹  확인 완료 후 Ctrl+C 를 누르세요\n")
    proc = subprocess.Popen(["hugo", "server", "-D"], cwd=BLOG_ROOT)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()
        print("\n  서버 종료됨")


def git_push_posts(titles: list[str], action: str = "post") -> bool:
    os.chdir(BLOG_ROOT)
    if action == "publish":
        msg = f"publish: {len(titles)}개 포스트 공개"
    elif len(titles) == 1:
        msg = f"post: {titles[0]} (draft)"
    else:
        msg = f"post: {len(titles)}개 draft 포스트 추가\n\n" + \
              "\n".join(f"- {t}" for t in titles)

    for cmd in [
        ["git", "add", "content/posts/"],
        ["git", "commit", "-m", msg],
        ["git", "push"],
    ]:
        print(f"  $ {' '.join(cmd)}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ❌ {r.stderr.strip()}")
            return False
        if r.stdout.strip():
            print(f"     {r.stdout.strip()}")
    return True


def ask_and_push(titles: list[str], action: str = "post"):
    """미리보기 → push 여부 확인"""
    run_hugo_preview()

    print("\n  GitHub에 push 하시겠습니까?")
    print("  [y] push   [n] 취소")
    ans = input("  >>> ").strip().lower()

    if ans == "y":
        success = git_push_posts(titles, action)
        if success:
            print(f"\n  ✅ 배포 완료! 1-2분 후 확인:")
            print(f"     https://skong097.github.io/posts/")
    else:
        print("\n  push 생략. 준비되면 수동으로:")
        print("  git add content/posts/ && git commit -m 'post: ...' && git push")


# ═══════════════════════════════════════════════
#  명령: --publish (draft → 공개 전환)
# ═══════════════════════════════════════════════
def cmd_publish_drafts():
    """draft 포스트 목록 출력 → 번호 선택 → 공개 전환 → 미리보기 → push"""
    draft_files = []
    for f in sorted(POSTS_DIR.rglob("*.md")):
        content = f.read_text(encoding="utf-8", errors="replace")
        if "draft: true" in content:
            draft_files.append(f)

    if not draft_files:
        print("\n  ℹ️  공개 대기 중인 draft 포스트 없음")
        return

    print(f"\n  📝 Draft 포스트 ({len(draft_files)}개)\n")
    for i, f in enumerate(draft_files, 1):
        content = f.read_text(encoding="utf-8", errors="replace")
        title   = extract_frontmatter_field(content, "title") or f.stem
        rel     = f.relative_to(POSTS_DIR)
        print(f"  [{i:2d}] {title}")
        print(f"       {rel}\n")

    print("  공개할 번호 입력 (예: 1 3 5  /  all = 전체  /  q = 취소)")
    choice = input("  >>> ").strip().lower()

    if not choice or choice == "q":
        print("  취소됨")
        return

    if choice == "all":
        targets = draft_files
    else:
        try:
            indices = [int(x) - 1 for x in choice.split()]
            targets = [draft_files[i] for i in indices
                       if 0 <= i < len(draft_files)]
        except ValueError:
            print("  ❌ 잘못된 입력")
            return

    titles = []
    for f in targets:
        content     = f.read_text(encoding="utf-8", errors="replace")
        new_content = re.sub(r'^draft:\s*true', 'draft: false',
                             content, flags=re.MULTILINE)
        f.write_text(new_content, encoding="utf-8")
        title = extract_frontmatter_field(new_content, "title") or f.stem
        titles.append(title)
        print(f"  ✅ 공개 전환: {title}")

    ask_and_push(titles, action="publish")


# ═══════════════════════════════════════════════
#  명령: 기본 (generate)
# ═══════════════════════════════════════════════
def cmd_generate(dry_run: bool = False):
    print("=" * 60)
    print("  📝 블로그 포스트 자동 생성 (draft: true)")
    if dry_run:
        print("  🔍 DRY-RUN 모드")
    print("=" * 60)

    state    = load_state()
    md_files = scan_references()

    if not md_files:
        print(f"\n  ⚠️  {REFS_DIR} 에 .md 파일이 없습니다.")
        print(f"     collect_blog_refs.py --init 을 먼저 실행하세요.")
        return

    print(f"\n  📂 대상: {len(md_files)}개 파일\n")

    changed = []
    skipped = 0

    for src in md_files:
        result = process_file(src, state, dry_run)
        if result is None:
            skipped += 1
            continue

        is_update = str(src) in state["generated"]
        flag      = "🔄" if is_update else "🆕"
        print(f"  {flag} [{result['category']:15s}] {result['title'] or Path(result['dest']).stem}")
        print(f"       → {Path(result['dest']).relative_to(BLOG_ROOT)}")
        changed.append(result)

        if not dry_run:
            state["generated"][result["src"]] = result

    print(f"\n  ─────────────────────────────────────────")
    print(f"  생성: {len(changed)}개  스킵: {skipped}개")

    if dry_run:
        print("\n  ✅ DRY-RUN 완료 (실제 변경 없음)")
        return

    if not changed:
        print("\n  ℹ️  새로 생성된 포스트 없음")
        return

    save_state(state)

    titles = [r["title"] or Path(r["dest"]).stem for r in changed]
    ask_and_push(titles, action="post")


# ═══════════════════════════════════════════════
#  명령: --status
# ═══════════════════════════════════════════════
def cmd_status():
    print("=" * 60)
    print("  📊 포스트 현황")
    print("=" * 60)

    draft_count = published_count = 0
    by_cat: dict[str, list] = {}

    for md in sorted(POSTS_DIR.rglob("*.md")):
        content  = md.read_text(encoding="utf-8", errors="replace")
        title    = extract_frontmatter_field(content, "title") or md.stem
        cat      = extract_frontmatter_field(content, "categories").strip('[]"\'') or "기타"
        is_draft = "draft: true" in content
        draft_count     += is_draft
        published_count += not is_draft
        by_cat.setdefault(cat, []).append((title, is_draft))

    for cat, items in sorted(by_cat.items()):
        print(f"\n  [{cat}] {len(items)}개")
        for title, is_draft in items:
            flag = "📝 draft  " if is_draft else "✅ 공개   "
            print(f"    {flag} {title}")

    print(f"\n  {'─'*45}")
    print(f"  ✅ 공개: {published_count}개  📝 Draft: {draft_count}개  합계: {published_count+draft_count}개")

    # 미처리 references
    state = load_state()
    unpub = [f for f in scan_references() if str(f) not in state["generated"]]
    if unpub:
        print(f"\n  📥 references 미처리: {len(unpub)}개")
        for f in unpub[:5]:
            print(f"    - {f.name}")
        if len(unpub) > 5:
            print(f"    ... 외 {len(unpub)-5}개")


# ═══════════════════════════════════════════════
#  메인
# ═══════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="references/ → Hugo draft 포스트 생성 + 미리보기 + 선택 배포",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python blog_publish.py              # 포스트 생성 → 미리보기 → push 선택
  python blog_publish.py --dry-run    # 미리보기만 (변경 없음)
  python blog_publish.py --publish    # draft → 공개 전환 (번호 선택)
  python blog_publish.py --status     # 전체 포스트 현황
        """,
    )
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 미리보기")
    parser.add_argument("--publish", action="store_true", help="draft 포스트 공개 전환")
    parser.add_argument("--status",  action="store_true", help="포스트 현황 출력")
    args = parser.parse_args()

    if args.status:
        cmd_status()
    elif args.publish:
        cmd_publish_drafts()
    else:
        cmd_generate(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
