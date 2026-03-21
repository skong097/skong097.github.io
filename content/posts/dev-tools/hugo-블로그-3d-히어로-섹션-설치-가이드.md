---
title: "Hugo 블로그 3D 히어로 섹션 설치 가이드"
date: 2026-03-21
draft: true
tags: ["dev-tools", "hugo"]
categories: ["dev-tools"]
description: "**작성일**: 2026-02-17 **대상**: ~/dev_ws/blog (Hugo + PaperMod 테마) ```bash"
---

# Hugo 블로그 3D 히어로 섹션 설치 가이드

**작성일**: 2026-02-17  
**대상**: ~/dev_ws/blog (Hugo + PaperMod 테마)

---

## 1. 파일 배치

```bash
# 1) 히어로 파셜 (3D 씬 + 스타일 + 스크립트)
mkdir -p ~/dev_ws/blog/layouts/partials
cp hero-3d.html ~/dev_ws/blog/layouts/partials/hero-3d.html

# 2) 홈페이지 레이아웃 오버라이드
cp blog-layouts-index.html ~/dev_ws/blog/layouts/index.html
```

## 2. 디렉토리 구조

```
~/dev_ws/blog/
├── layouts/
│   ├── index.html              ← 홈페이지 오버라이드 (hero + 포스트 리스트)
│   ├── partials/
│   │   └── hero-3d.html        ← 3D 히어로 파셜 (Three.js)
│   └── dashboard/
│       └── single.html         ← 기존 대시보드 레이아웃
├── content/
│   └── posts/
├── static/
├── hugo.toml
└── themes/
    └── PaperMod/
```

## 3. 동작 확인

```bash
cd ~/dev_ws/blog
hugo server -D
# http://localhost:1313 접속
```

## 4. 커스터마이징

### 4-1. 텍스트 수정

`hero-3d.html` 내 `.hero-content` 영역:

```html
<p class="hero-tag">Autonomous Robotics · Vision AI · ROS2</p>
<h1 class="hero-title">
  <span class="line1">Building</span>
  <span class="line2">Intelligent Robots</span>
</h1>
```

### 4-2. 색상 변경

주요 색상 값:
- 코어 색: `0x7c6aef` (퍼플)
- 보조 색: `0x60a5fa` (블루)
- 배경: `#050508` (다크)
- 버튼: `#7c6aef`

### 4-3. 3D 씬 조정

```javascript
// 코어 크기
new THREE.IcosahedronGeometry(1.8, 1)  // 1.8 = 반지름, 1 = 디테일

// 파티클 수
for (let i = 0; i < 400; i++)  // 400개

// 카메라 거리
camera.position.set(0, 1, 12);  // z=12 (가까이/멀리)

// 자동 회전 속도
Math.sin(t * 0.1) * 0.5  // 0.1 = 속도
```

### 4-4. CTA 버튼 링크

```html
<a href="/posts/" class="btn-primary">Explore Posts</a>
<a href="/dashboard/" class="btn-secondary">Dashboard</a>
```

## 5. 성능 참고

- Three.js r128 CDN 로드 (~150KB gzip)
- 스크롤 시 히어로가 뷰포트 밖이면 렌더링 자동 중지
- 모바일: `devicePixelRatio` 최대 2로 제한
- 파티클 400개 + 노드 50개 → 대부분 기기에서 60fps 유지

## 6. PaperMod 호환성

- `layouts/index.html`이 PaperMod의 기본 홈을 오버라이드
- 히어로 아래에 포스트 리스트가 자연스럽게 이어짐
- 다크 테마 전용 (PaperMod dark mode와 통일)
- 기존 PaperMod 스타일(포스트 카드, 네비게이션 등)은 그대로 유지
