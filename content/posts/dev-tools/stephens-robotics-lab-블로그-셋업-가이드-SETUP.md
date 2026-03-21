---
title: "Stephen's Robotics Lab — 블로그 셋업 가이드"
date: 2026-03-21
draft: true
tags: ["dev-tools", "hugo"]
categories: ["dev-tools"]
description: "```bash sudo snap install hugo --channel=extended cp -r blog/ ~/dev_ws/blog"
---

# Stephen's Robotics Lab — 블로그 셋업 가이드

## 빠른 시작

```bash
# 1. Hugo 설치
sudo snap install hugo --channel=extended

# 2. 이 프로젝트를 ~/dev_ws/blog 로 복사
cp -r blog/ ~/dev_ws/blog
cd ~/dev_ws/blog

# 3. Git 초기화 + PaperMod 테마 추가
git init
git submodule add https://github.com/adityatelange/hugo-PaperMod themes/PaperMod

# 4. 로컬 미리보기 (draft 포함)
hugo server -D
# → http://localhost:1313

# 5. draft 포스트 확인 후, 공개할 포스트의 draft: false 로 변경
```

## GitHub Pages 배포

```bash
# 1. GitHub에 저장소 생성 (private 가능)
#    Repository name: skong097.github.io

# 2. remote 추가 + push
git remote add origin https://github.com/skong097/skong097.github.io.git
git add .
git commit -m "Initial blog setup"
git push -u origin main

# 3. GitHub → Settings → Pages → Source: GitHub Actions
#    .github/workflows/deploy.yml 이 자동 인식됨

# 4. 비공개 → 공개 전환
#    Settings → Danger Zone → Change visibility → Public
```

## 포스트 작성 플로우

```bash
# 새 포스트 생성
hugo new posts/ros2/my-new-post.md

# 작성 후 미리보기
hugo server -D

# 공개 준비 완료 시
# frontmatter에서 draft: true → draft: false

# 배포
git add . && git commit -m "Publish: My New Post" && git push
```

## 디렉토리 구조

```
blog/
├── archetypes/default.md        ← 포스트 템플릿
├── content/
│   ├── posts/
│   │   ├── ros2/                ← ROS2 관련
│   │   ├── computer-vision/     ← CV/ML 관련
│   │   ├── robotics/            ← 로보틱스 프로젝트
│   │   ├── ai-ml/               ← LLM/AI 관련
│   │   └── dev-tools/           ← 개발 도구/팁
│   ├── projects/                ← 프로젝트 포트폴리오
│   ├── about/                   ← 자기소개
│   └── search.md                ← 검색 페이지
├── static/
│   ├── images/                  ← 포스트 이미지
│   └── screenshots/             ← 스크린샷
├── .github/workflows/deploy.yml ← CI/CD
├── hugo.toml                    ← Hugo 설정
└── .gitignore
```

## 비공개 → 공개 전략

1. Private repo에서 draft: true 포스트 10개 축적
2. 준비 완료 시 repo를 public으로 전환
3. 매주 5개씩 draft: false로 변경하여 push
4. 신규 5개를 draft: true로 작성 (예비)
