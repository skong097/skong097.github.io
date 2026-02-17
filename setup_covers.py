#!/usr/bin/env python3
"""
Stephen's Robotics Lab - Cover Image Auto Setup
=================================================
이미지를 static/images/covers/에 복사하고,
각 콘텐츠 파일의 frontmatter에 cover 설정을 자동 삽입합니다.

사용법:
  1. covers/ 폴더를 ~/dev_ws/blog/ 루트에 복사
  2. 이 스크립트를 ~/dev_ws/blog/ 에서 실행
     python setup_covers.py
"""

import os
import shutil
import re
import yaml

BLOG_ROOT = os.path.expanduser("~/dev_ws/blog")
COVERS_SRC = os.path.join(BLOG_ROOT, "covers")  # 다운받은 covers 폴더
COVERS_DST = os.path.join(BLOG_ROOT, "static", "images", "covers")

# ── 이미지 → 콘텐츠 매핑 ────────────────────────────────────────
POST_COVER_MAP = {
    "content/posts/computer-vision/stgcn-finetuning-fall-detection.md": {
        "image": "images/covers/post-stgcn-finetuning.png",
        "alt": "ST-GCN Fine-tuning for Fall Detection",
    },
    "content/posts/computer-vision/rf-vs-stgcn-fall-detection.md": {
        "image": "images/covers/post-rf-vs-stgcn.png",
        "alt": "RF vs ST-GCN Model Comparison",
    },
    "content/posts/dev-tools/pyqt6-dark-theme-system.md": {
        "image": "images/covers/post-pyqt6-dark-theme.png",
        "alt": "PyQt6 Dark Theme System",
    },
    "content/posts/robotics/kevin-patrol-fleet-dashboard.md": {
        "image": "images/covers/post-kevin-patrol-fleet.png",
        "alt": "Kevin Patrol Fleet Dashboard",
    },
    "content/posts/ros2/ros2-guard-brain-fastapi.md": {
        "image": "images/covers/post-ros2-guard-brain.png",
        "alt": "ROS2 + FastAPI Guard Brain",
    },
    "content/about/index.md": {
        "image": "images/covers/about-cover.png",
        "alt": "About Stephen",
    },
    "content/projects/_index.md": {
        "image": "images/covers/projects-cover.png",
        "alt": "Projects",
    },
}

# hugo.yaml에 추가할 기본 커버 설정
HUGO_YAML_COVER = {
    "image": "images/covers/hero-banner.png",
    "alt": "Stephen's Robotics Lab",
    "hidden": False,
    "hiddenInList": False,
    "hiddenInSingle": False,
}


def step1_copy_images():
    """covers/ → static/images/covers/ 복사"""
    print("\n[Step 1] 이미지 파일 복사")
    print(f"  FROM: {COVERS_SRC}")
    print(f"  TO  : {COVERS_DST}")

    if not os.path.exists(COVERS_SRC):
        print(f"  [ERROR] {COVERS_SRC} 폴더가 없습니다.")
        print(f"  다운받은 covers 폴더를 {BLOG_ROOT}/ 에 넣어주세요.")
        return False

    os.makedirs(COVERS_DST, exist_ok=True)
    count = 0
    for f in os.listdir(COVERS_SRC):
        if f.endswith(".png"):
            src = os.path.join(COVERS_SRC, f)
            dst = os.path.join(COVERS_DST, f)
            shutil.copy2(src, dst)
            print(f"  [OK] {f}")
            count += 1

    print(f"  => {count}개 이미지 복사 완료")
    return True


def step2_update_frontmatter():
    """각 포스트/페이지 frontmatter에 cover 설정 삽입"""
    print("\n[Step 2] Frontmatter 업데이트")

    for rel_path, cover_data in POST_COVER_MAP.items():
        filepath = os.path.join(BLOG_ROOT, rel_path)
        if not os.path.exists(filepath):
            print(f"  [SKIP] {rel_path} (파일 없음)")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # YAML frontmatter 추출 (--- ... ---)
        match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
        if not match:
            print(f"  [SKIP] {rel_path} (frontmatter 없음)")
            continue

        fm_text = match.group(1)
        body = match.group(2)

        try:
            fm = yaml.safe_load(fm_text)
            if fm is None:
                fm = {}
        except yaml.YAMLError:
            print(f"  [SKIP] {rel_path} (YAML 파싱 실패)")
            continue

        # cover 설정이 이미 있으면 업데이트, 없으면 추가
        fm["cover"] = {
            "image": cover_data["image"],
            "alt": cover_data["alt"],
            "hidden": False,
        }

        # YAML 덤프 (한글 유지)
        new_fm = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
        new_content = f"---\n{new_fm}---\n{body}"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

        print(f"  [OK] {rel_path}")
        print(f"       cover: {cover_data['image']}")

    print("  => Frontmatter 업데이트 완료")


def step3_update_hugo_yaml():
    """hugo.yaml에 기본 커버 설정 추가"""
    print("\n[Step 3] hugo.yaml 업데이트")

    hugo_yaml_path = os.path.join(BLOG_ROOT, "hugo.yaml")
    if not os.path.exists(hugo_yaml_path):
        print(f"  [SKIP] hugo.yaml 없음")
        return

    with open(hugo_yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config is None:
        config = {}

    # params.cover 설정
    if "params" not in config:
        config["params"] = {}

    config["params"]["cover"] = HUGO_YAML_COVER

    with open(hugo_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"  [OK] params.cover 설정 추가")
    print(f"       image: {HUGO_YAML_COVER['image']}")


def step4_summary():
    """최종 결과 요약"""
    print("\n" + "=" * 55)
    print("  Setup 완료!")
    print("=" * 55)
    print(f"""
  적용된 이미지:
    - 홈페이지 히어로:  hero-banner.png
    - Dashboard 배너:   dashboard-banner.png
    - About 커버:       about-cover.png
    - Projects 커버:    projects-cover.png
    - 카테고리 4개:     cover-*.png
    - 포스트 5개:       post-*.png

  확인 방법:
    cd {BLOG_ROOT}
    hugo server -D
    → http://localhost:1313/

  Dashboard 배너는 수동 적용이 필요합니다:
    layouts/dashboard/single.html 상단에 추가:

    <div class="dashboard-hero">
      <img src="/images/covers/dashboard-banner.png"
           alt="Career Dashboard"
           style="width:100%; border-radius:12px; margin-bottom:24px;">
    </div>
""")


if __name__ == "__main__":
    print("=" * 55)
    print("  Stephen's Robotics Lab - Cover Image Setup")
    print("=" * 55)

    if step1_copy_images():
        step2_update_frontmatter()
        step3_update_hugo_yaml()
    step4_summary()
