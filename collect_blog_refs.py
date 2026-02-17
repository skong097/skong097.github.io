#!/usr/bin/env python3
"""
collect_blog_refs.py — 블로그 레퍼런스 .md 파일 수집기

사용법:
    python collect_blog_refs.py --init       # 최초 1회: ~/dev_ws 전체 스캔
    python collect_blog_refs.py              # 일상: ~/Downloads 만 스캔
    python collect_blog_refs.py --status     # 수집 현황 출력
    python collect_blog_refs.py --dry-run    # 실제 복사 없이 미리보기

수집 대상: .md 파일
수집 위치: ~/dev_ws/blog/references/<프로젝트명>/
제외 대상: blog 디렉토리 자체, node_modules, .git, __pycache__

작성일: 2026-02-17
"""

import os
import sys
import shutil
import hashlib
import argparse
import json
from pathlib import Path
from datetime import datetime


# ═══════════════════════════════════════════════
#  설정
# ═══════════════════════════════════════════════
HOME = Path.home()
DEV_WS = HOME / "dev_ws"
BLOG_REFS = DEV_WS / "blog" / "references"
DOWNLOADS = HOME / "Downloads"
STATE_FILE = BLOG_REFS / ".collect_state.json"

# 제외할 디렉토리 (정확히 일치)
EXCLUDE_DIRS = {
    "blog", "node_modules", ".git", "__pycache__",
    "venv", ".venv", "env", ".env",
    "public", "resources", ".hugo_build.lock",
    "themes",  # Hugo 테마
}

# 제외할 디렉토리 접미사 패턴 (예: kevin_venv, yolo_venv, ...)
EXCLUDE_DIR_SUFFIXES = ("_venv",)

# 제외할 파일 패턴
EXCLUDE_FILES = {
    "README.md",
    "LICENSE.md",
    "CHANGELOG.md",
    "ICON_LICENSE.md",
    "Privacy.md",
    "AGENTS.md",
    "best_practices.md",        # pip 패키지 공통 문서
    "coreml_supported_mlprogram_ops.md",
    "coreml_supported_neuralnetwork_ops.md",
    "nnapi_supported_ops.md",
    "AUTHORS.md",
}


# ═══════════════════════════════════════════════
#  유틸리티
# ═══════════════════════════════════════════════
def file_hash(filepath: Path) -> str:
    """파일 MD5 해시 (중복/변경 감지용)"""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def guess_project_name(filepath: Path, scan_root: Path) -> str:
    """파일 경로에서 프로젝트명 추론

    ~/dev_ws/kevin_patrol/docs/log.md → kevin_patrol
    ~/dev_ws/home_safe_solution/notes.md → home_safe_solution
    ~/Downloads/some_log.md → downloads
    """
    try:
        rel = filepath.relative_to(scan_root)
        parts = rel.parts
        if len(parts) > 1:
            return parts[0]     # 첫 번째 하위 디렉토리 = 프로젝트명
        else:
            return scan_root.name   # 루트에 직접 있는 파일
    except ValueError:
        return "misc"


def should_exclude(filepath: Path) -> bool:
    """제외 대상인지 확인 (수집 시 사용 — 전체 경로 체크)"""
    # 파일명 제외
    if filepath.name in EXCLUDE_FILES:
        return True

    # 경로에 제외 디렉토리 포함 여부
    for part in filepath.parts:
        if part in EXCLUDE_DIRS:
            return True
        # 접미사 패턴 매칭 (예: kevin_venv, yolo_venv)
        for suffix in EXCLUDE_DIR_SUFFIXES:
            if part.endswith(suffix):
                return True

    return False


def _should_exclude_in_refs(filepath: Path) -> bool:
    """제외 대상인지 확인 (classify 시 사용 — references 기준 상대 경로만 체크)

    references/ 안에 이미 수집된 파일 중 분류 대상에서 제외할 것만 걸러냄.
    전체 절대경로가 아닌, BLOG_REFS 이후의 상대 경로 부분만 검사.
    """
    # 파일명 제외
    if filepath.name in EXCLUDE_FILES:
        return True

    # references 기준 상대 경로의 디렉토리명만 체크
    try:
        rel = filepath.relative_to(BLOG_REFS)
    except ValueError:
        return False

    for part in rel.parts[:-1]:  # 마지막은 파일명이므로 제외
        # 접미사 패턴 매칭 (예: yolo_venv, eyecon_venv)
        for suffix in EXCLUDE_DIR_SUFFIXES:
            if part.endswith(suffix):
                return True

    return False


def load_state() -> dict:
    """이전 수집 상태 로드"""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"collected": {}, "last_init": None, "last_daily": None}


def save_state(state: dict):
    """수집 상태 저장"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════
#  핵심 로직
# ═══════════════════════════════════════════════
def scan_directory(scan_root: Path) -> list[Path]:
    """디렉토리에서 .md 파일 검색 (제외 대상 필터링)"""
    md_files = []
    if not scan_root.exists():
        print(f"  ⚠  디렉토리 없음: {scan_root}")
        return md_files

    for filepath in scan_root.rglob("*.md"):
        if filepath.is_file() and not should_exclude(filepath):
            md_files.append(filepath)

    return sorted(md_files)


def collect_files(md_files: list[Path], scan_root: Path,
                  state: dict, dry_run: bool = False) -> dict:
    """파일 수집 (references 디렉토리로 복사)

    Returns:
        stats: {"new": int, "updated": int, "skipped": int}
    """
    stats = {"new": 0, "updated": 0, "skipped": 0}

    for src in md_files:
        # 프로젝트명 추론
        if scan_root == DOWNLOADS:
            project = "downloads"
        else:
            project = guess_project_name(src, scan_root)

        # 대상 경로 결정
        dest_dir = BLOG_REFS / project
        dest = dest_dir / src.name

        # 동일 파일명 충돌 처리 (다른 하위 경로에서 같은 이름)
        if dest.exists():
            src_hash = file_hash(src)
            dest_hash = file_hash(dest)
            if src_hash == dest_hash:
                stats["skipped"] += 1
                continue
            else:
                # 내용이 다르면 업데이트
                action = "updated"
                stats["updated"] += 1
        else:
            action = "new"
            stats["new"] += 1

        # 실제 복사
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

        # 상태 기록
        state["collected"][str(dest)] = {
            "source": str(src),
            "hash": file_hash(src) if not dry_run else "dry-run",
            "collected_at": datetime.now().isoformat(),
            "action": action,
        }

        flag = "🆕" if action == "new" else "🔄"
        print(f"  {flag} {project}/{src.name}")

    return stats


# ═══════════════════════════════════════════════
#  명령어
# ═══════════════════════════════════════════════
def cmd_init(dry_run: bool = False):
    """--init: ~/dev_ws 전체 스캔 (최초 1회)"""
    print("=" * 55)
    print("  📦 블로그 레퍼런스 수집 — 초기 스캔 (~/dev_ws)")
    print("=" * 55)

    if dry_run:
        print("  🔍 DRY-RUN 모드 (실제 복사 없음)\n")

    state = load_state()
    md_files = scan_directory(DEV_WS)

    # blog/references 자체 파일은 제외
    md_files = [f for f in md_files if BLOG_REFS not in f.parents]

    print(f"\n  검색 결과: {len(md_files)}개 .md 파일 발견\n")

    if not md_files:
        print("  수집할 파일이 없습니다.")
        return

    stats = collect_files(md_files, DEV_WS, state, dry_run)

    state["last_init"] = datetime.now().isoformat()
    if not dry_run:
        save_state(state)

    print(f"\n  ✅ 완료 — 🆕 {stats['new']}개 신규 | "
          f"🔄 {stats['updated']}개 업데이트 | "
          f"⏭ {stats['skipped']}개 건너뜀")
    print(f"  📁 저장 위치: {BLOG_REFS}")


def cmd_daily(dry_run: bool = False):
    """기본 모드: ~/Downloads 스캔 (일상 수집)"""
    print("=" * 55)
    print("  📦 블로그 레퍼런스 수집 — 일일 스캔 (~/Downloads)")
    print("=" * 55)

    if dry_run:
        print("  🔍 DRY-RUN 모드 (실제 복사 없음)\n")

    state = load_state()
    md_files = scan_directory(DOWNLOADS)

    print(f"\n  검색 결과: {len(md_files)}개 .md 파일 발견\n")

    if not md_files:
        print("  수집할 파일이 없습니다.")
        return

    stats = collect_files(md_files, DOWNLOADS, state, dry_run)

    state["last_daily"] = datetime.now().isoformat()
    if not dry_run:
        save_state(state)

    print(f"\n  ✅ 완료 — 🆕 {stats['new']}개 신규 | "
          f"🔄 {stats['updated']}개 업데이트 | "
          f"⏭ {stats['skipped']}개 건너뜀")
    print(f"  📁 저장 위치: {BLOG_REFS}")


def cmd_status():
    """--status: 현재 수집 현황"""
    print("=" * 55)
    print("  📊 블로그 레퍼런스 수집 현황")
    print("=" * 55)

    state = load_state()

    print(f"\n  마지막 초기 스캔: {state.get('last_init', '미실행')}")
    print(f"  마지막 일일 스캔: {state.get('last_daily', '미실행')}")

    # references 디렉토리 현황
    if not BLOG_REFS.exists():
        print(f"\n  📁 {BLOG_REFS} — 디렉토리 없음")
        return

    total = 0
    print(f"\n  📁 {BLOG_REFS}")
    for project_dir in sorted(BLOG_REFS.iterdir()):
        if project_dir.is_dir():
            md_count = len(list(project_dir.glob("*.md")))
            if md_count > 0:
                total += md_count
                print(f"     ├─ {project_dir.name:30s} {md_count:3d}개")

    # 루트의 .md 파일
    root_md = len([f for f in BLOG_REFS.glob("*.md")])
    if root_md > 0:
        total += root_md
        print(f"     ├─ {'(root)':30s} {root_md:3d}개")

    print(f"     └─ {'합계':30s} {total:3d}개")


# ═══════════════════════════════════════════════
#  분류 엔진 (--classify)
# ═══════════════════════════════════════════════
CATEGORY_INDEX_FILE = BLOG_REFS / ".category_index.json"

CATEGORY_KEYWORDS = {
    "ros2": {
        "high": ["ros2", "ros 2", "jazzy", "humble", "nav2", "gazebo",
                 "colcon", "ament", "launch", "rclpy", "topic", "service",
                 "action server", "action client", "ros2 node", "guard_brain",
                 "guard brain"],
        "medium": ["subscriber", "publisher", "tf2", "urdf", "xacro",
                   "rviz", "rosbag", "dds", "qos", "cmd_vel", "/scan"],
        "low": ["robot", "sensor", "lidar"],
    },
    "ai-ml": {
        "high": ["random forest", "st-gcn", "stgcn", "lstm", "transformer",
                 "fine-tuning", "fine_tuning", "pretrained", "pre-trained",
                 "epoch", "learning rate", "class_weight", "f1-score",
                 "confusion matrix", "hyperparameter", "randomforestclassifier"],
        "medium": ["accuracy", "precision", "recall", "auc", "roc",
                   "train", "validation", "test set", "overfitting",
                   "batch size", "optimizer", "cross-validation", "모델 학습"],
        "low": ["model", "feature", "predict", "classification"],
    },
    "vision-ai": {
        "high": ["yolo", "pose estimation", "keypoint", "키포인트",
                 "fall detection", "낙상", "skeleton", "bounding box",
                 "opencv", "mediapipe", "coco 17", "yolo11s-pose",
                 "낙상 감지", "home safe"],
        "medium": ["frame", "video", "camera", "inference", "webcam",
                   "detection", "tracking", "confidence"],
        "low": ["image", "pixel", "resolution"],
    },
    "robotics": {
        "high": ["kevin patrol", "kevin_patrol", "자율주행", "slam",
                 "a* ", "a-star", "astar", "경로 계획", "path planning",
                 "navigation", "waypoint", "occupancy grid",
                 "spatial hash", "patrol", "kevin multi"],
        "medium": ["robot", "3d sim", "collision", "충돌", "obstacle",
                   "autonomous", "mocksim", "fleet", "multi-robot",
                   "순찰", "벽 회피"],
        "low": ["motor", "imu", "odometry"],
    },
    "mlops": {
        "high": ["pipeline", "파이프라인", "data augmentation", "데이터 증강",
                 "feature engineering", "auto labeling", "자동 레이블링",
                 "모델 비교", "model comparison", "배포", "deploy"],
        "medium": ["preprocessing", "전처리", "normalization", "정규화",
                   "dataset", "데이터셋", "experiment", "undersample",
                   "smote", "class_weight"],
        "low": ["script", "automation", "batch", "csv", "pkl"],
    },
    "dev-tools": {
        "high": ["pyqt6", "pyqt", "dashboard", "대시보드", "dark theme",
                 "다크 테마", "fastapi", "gui", "widget", "qss",
                 "hugo", "github pages", "블로그"],
        "medium": ["layout", "sidebar", "panel", "chart", "plot",
                   "toast", "alert", "ui", "ux", "css", "paintEvent"],
        "low": ["button", "window", "font", "style"],
    },
    "robot-network": {
        "high": ["robot network", "로봇 네트워크", "로봇 통신", "fleet 통신",
                 "multi-robot communication", "멀티로봇 네트워크",
                 "robot-to-robot", "swarm", "mesh network"],
        "medium": ["dds", "protocol", "프로토콜", "bandwidth", "latency",
                   "네트워크", "network topology", "discovery",
                   "통신", "sync", "동기화"],
        "low": ["socket", "tcp", "udp", "mqtt", "wireless"],
    },
    "robot-security": {
        "high": ["robot security", "로봇 보안", "보안관", "침입 감지",
                 "intrusion detection", "authentication", "인증",
                 "encryption", "암호화", "access control", "접근 제어",
                 "security audit", "보안 감사", "보안 로봇", "guard bot",
                 "home guard", "경비", "순찰 보안", "llm 보안",
                 "security recommendation", "보안 권고"],
        "medium": ["vulnerability", "취약점", "firewall", "방화벽",
                   "certificate", "인증서", "tls", "ssl", "token",
                   "bcrypt", "hash", "permission", "권한",
                   "login", "password", "로그인"],
        "low": ["security", "보안", "threat", "위협", "attack"],
    },
    "big-data": {
        "high": ["big data", "빅데이터", "대용량 데이터", "데이터 레이크",
                 "data lake", "hadoop", "spark", "kafka",
                 "elasticsearch", "data warehouse"],
        "medium": ["로그 분석", "log analysis", "데이터 수집", "data collection",
                   "데이터 저장", "data storage", "mysql", "mongodb",
                   "통계", "statistics", "시계열", "time series",
                   "데이터베이스", "database"],
        "low": ["data", "데이터", "db", "query", "sql", "nosql"],
    },
    "project": {
        "high": ["계획서", "프로젝트 계획", "project plan", "roadmap",
                 "로드맵", "전략", "strategy", "phase", "milestone",
                 "개발계획서"],
        "medium": ["요구사항", "requirement", "architecture", "설계",
                   "목표", "objective", "scope"],
        "low": ["overview", "개요", "summary"],
    },
    "worklog": {
        "high": ["작업일지", "work_log", "work log", "작업 기록",
                 "dev_log", "dev log", "bugfix", "버그 수정",
                 "개발 일지", "작업일"],
        "medium": ["수정", "fix", "변경", "change", "이슈", "issue",
                   "해결", "resolved", "적용", "applied"],
        "low": ["완료", "done", "진행중"],
    },
}

# 카테고리 표시명 + 이모지
CATEGORY_DISPLAY = {
    "ros2":           "🔧 ROS2",
    "ai-ml":          "🧠 AI / ML / DL",
    "vision-ai":      "👁  Vision AI",
    "robotics":       "🤖 Robotics",
    "mlops":          "⚙  AIOps / MLOps",
    "robot-network":  "🌐 Robot Network",
    "robot-security": "🔒 Robot Security",
    "big-data":       "📦 Big Data",
    "dev-tools":      "🖥  Dev Tools / GUI",
    "project":        "📋 Project Planning",
    "worklog":        "📝 Work Log",
}

# 동점 시 우선순위 (낮을수록 우선)
CATEGORY_PRIORITY = {
    "vision-ai": 0, "ai-ml": 1, "robotics": 2, "ros2": 3,
    "mlops": 4, "robot-network": 5, "robot-security": 6, "big-data": 7,
    "dev-tools": 8, "project": 9, "worklog": 10,
}


def classify_file(filepath: Path) -> dict:
    """단일 md 파일을 카테고리로 분류

    Returns:
        {"primary": str, "secondary": str|None,
         "scores": dict, "top_keywords": list}
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return {"primary": "worklog", "secondary": None,
                "scores": {}, "top_keywords": []}

    # 파일명도 분류 힌트로 활용
    filename = filepath.stem.lower().replace("-", " ").replace("_", " ")

    # 제목 추출 (첫 번째 # 헤더)
    title = ""
    for line in content.split("\n")[:20]:
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("##"):
            title = stripped[2:].lower()
            break

    # 본문 앞 3000자
    body = content[:3000].lower()

    # 제목 영역 = 파일명 + 헤더 제목 (가중치 2배 적용 위해 별도)
    title_area = f"{filename} {title}"

    scores = {}
    matched_keywords = {}

    for cat, levels in CATEGORY_KEYWORDS.items():
        score = 0
        kw_hits = []

        for level, keywords in levels.items():
            weight = {"high": 3, "medium": 2, "low": 1}[level]

            for kw in keywords:
                kw_lower = kw.lower()
                # 제목 영역 매칭 (2배 가중치)
                title_count = title_area.count(kw_lower)
                if title_count > 0:
                    score += title_count * weight * 2
                    kw_hits.append(f"{kw}(title)")

                # 본문 매칭
                body_count = body.count(kw_lower)
                if body_count > 0:
                    score += body_count * weight
                    if f"{kw}(title)" not in kw_hits:
                        kw_hits.append(kw)

        scores[cat] = score
        matched_keywords[cat] = kw_hits

    # 1위/2위 결정
    sorted_cats = sorted(scores.items(),
                         key=lambda x: (-x[1], CATEGORY_PRIORITY.get(x[0], 99)))

    primary = sorted_cats[0][0] if sorted_cats[0][1] > 0 else "worklog"
    primary_score = sorted_cats[0][1]

    secondary = None
    if len(sorted_cats) > 1 and sorted_cats[1][1] > 0:
        second_score = sorted_cats[1][1]
        # 2위가 1위의 70% 이상이면 보조 카테고리
        if primary_score > 0 and (second_score / primary_score) >= 0.7:
            secondary = sorted_cats[1][0]

    top_kw = matched_keywords.get(primary, [])[:5]

    return {
        "primary": primary,
        "secondary": secondary,
        "scores": scores,
        "top_keywords": top_kw,
    }


def cmd_classify():
    """--classify: references 디렉토리 전체 분류"""
    print("=" * 60)
    print("  📊 블로그 레퍼런스 자동 분류")
    print("=" * 60)

    if not BLOG_REFS.exists():
        print(f"\n  ⚠  {BLOG_REFS} 디렉토리가 없습니다.")
        print("     먼저 --init 으로 수집해 주세요.")
        return

    # 모든 .md 파일 수집 (venv 등 제외)
    all_md = sorted(BLOG_REFS.rglob("*.md"))
    all_md = [f for f in all_md
              if f.is_file()
              and f.name != ".category_index.json"
              and not _should_exclude_in_refs(f)]

    if not all_md:
        print("\n  수집된 .md 파일이 없습니다.")
        return

    print(f"\n  대상: {len(all_md)}개 파일 분류 중...\n")

    # 분류 실행
    results = {}      # {filepath: classify result}
    by_category = {}   # {category: [files]}

    for md_file in all_md:
        result = classify_file(md_file)
        rel_path = str(md_file.relative_to(BLOG_REFS))
        results[rel_path] = result

        cat = result["primary"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append((rel_path, result))

    # 리포트 출력
    for cat in CATEGORY_PRIORITY:
        if cat not in by_category:
            continue
        files = by_category[cat]
        display = CATEGORY_DISPLAY.get(cat, cat)
        print(f"  {display} ({len(files)}개)")

        for rel_path, result in sorted(files, key=lambda x: x[0]):
            sub = f"  [+{result['secondary']}]" if result["secondary"] else ""
            # 파일명만 표시 (디렉토리 제외하면 너무 길어질 수 있음)
            fname = Path(rel_path).name
            src_dir = Path(rel_path).parent
            print(f"     {fname:55s} {sub:15s} ← {src_dir}")

        print()

    # 통계
    total = len(all_md)
    classified = sum(len(v) for v in by_category.values())
    print(f"  ─────────────────────────────────────")
    print(f"  합계: {total}개 파일 → {len(by_category)}개 카테고리로 분류")

    # 인덱스 저장
    index = {}
    for cat, files in by_category.items():
        index[cat] = [
            {
                "file": rel_path,
                "score": result["scores"].get(cat, 0),
                "sub": result["secondary"],
                "keywords": result["top_keywords"],
            }
            for rel_path, result in sorted(files, key=lambda x: x[0])
        ]

    with open(CATEGORY_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n  💾 인덱스 저장: {CATEGORY_INDEX_FILE}")


# ═══════════════════════════════════════════════
#  메인
# ═══════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="블로그 레퍼런스 .md 파일 수집기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python collect_blog_refs.py --init       # 최초: ~/dev_ws 전체 스캔
  python collect_blog_refs.py              # 일상: ~/Downloads 스캔
  python collect_blog_refs.py --classify   # 카테고리 자동 분류
  python collect_blog_refs.py --status     # 현황 확인
  python collect_blog_refs.py --dry-run    # 미리보기
  python collect_blog_refs.py --init --dry-run  # 초기 스캔 미리보기
        """,
    )
    parser.add_argument("--init", action="store_true",
                        help="~/dev_ws 전체 스캔 (최초 1회)")
    parser.add_argument("--classify", action="store_true",
                        help="references 자동 분류")
    parser.add_argument("--status", action="store_true",
                        help="수집 현황 출력")
    parser.add_argument("--dry-run", action="store_true",
                        help="실제 복사 없이 미리보기")

    args = parser.parse_args()

    if args.classify:
        cmd_classify()
    elif args.status:
        cmd_status()
    elif args.init:
        cmd_init(dry_run=args.dry_run)
    else:
        cmd_daily(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
