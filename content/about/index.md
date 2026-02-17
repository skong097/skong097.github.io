---
title: About
layout: single
url: /about/
ShowToc: false
ShowBreadCrumbs: false
cover:
  image: images/covers/about-cover.png
  alt: About Stephen
  hidden: false
---

<style>
/* ── About Page - Container 확장 ──────────────────────── */
.post-single .post-content {
  max-width: 1200px !important;
  width: 100% !important;
  margin: 0 auto;
}
.post-single .main,
.post-single main.main {
  max-width: 1200px !important;
  width: 92% !important;
}

/* ── Hero ──────────────────────────────────────────────── */
.about-hero {
  text-align: center;
  padding: 2.5rem 0 1.5rem;
}
.about-hero h2 {
  font-size: 2.4rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin-bottom: 0.6rem;
}
.about-hero p {
  font-size: 1.08rem;
  opacity: 0.75;
  max-width: 620px;
  margin: 0 auto;
  line-height: 1.75;
}

/* ── Section Title ────────────────────────────────────── */
.about-section-title {
  font-size: 1.3rem;
  font-weight: 700;
  margin: 2.5rem 0 1.2rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(0,200,220,0.2);
  letter-spacing: -0.02em;
}
[data-theme="light"] .about-section-title {
  border-bottom-color: rgba(60,130,246,0.2);
}

/* ── Tech Stack Grid ──────────────────────────────────── */
.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
  margin-bottom: 1rem;
}
.tech-card {
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  padding: 1.2rem 1.3rem;
  background: rgba(255,255,255,0.02);
  transition: 0.3s ease;
}
.tech-card:hover {
  border-color: rgba(0,200,220,0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.2);
}
[data-theme="light"] .tech-card {
  border-color: rgba(0,0,0,0.08);
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
[data-theme="light"] .tech-card:hover {
  border-color: rgba(60,130,246,0.3);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}
.tech-card-title {
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.7rem;
  opacity: 0.5;
}
.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}
.tech-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 500;
  background: rgba(0,200,220,0.08);
  border: 1px solid rgba(0,200,220,0.15);
  transition: 0.2s ease;
}
.tech-tag:hover {
  background: rgba(0,200,220,0.15);
}
[data-theme="light"] .tech-tag {
  background: rgba(60,130,246,0.06);
  border-color: rgba(60,130,246,0.12);
}

/* ── Project List Grid ────────────────────────────────── */
.project-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.8rem;
  margin-bottom: 1rem;
}
.project-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  padding: 0.9rem 1.2rem;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  text-decoration: none;
  color: inherit;
  transition: 0.3s ease;
}
.project-link:hover {
  border-color: rgba(0,200,220,0.3);
  background: rgba(0,200,220,0.04);
  transform: translateX(4px);
}
[data-theme="light"] .project-link {
  border-color: rgba(0,0,0,0.08);
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
[data-theme="light"] .project-link:hover {
  border-color: rgba(60,130,246,0.3);
  background: rgba(60,130,246,0.03);
}
.project-link-arrow {
  font-size: 1.2rem;
  opacity: 0.3;
  transition: 0.2s;
  flex-shrink: 0;
}
.project-link:hover .project-link-arrow {
  opacity: 0.8;
  transform: translateX(3px);
}
.project-link-title {
  font-weight: 600;
  font-size: 0.95rem;
}
.project-link-desc {
  font-size: 0.8rem;
  opacity: 0.55;
  margin-top: 2px;
}

/* ── Contact ──────────────────────────────────────────── */
.contact-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1rem;
}
.contact-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.7rem 1.4rem;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.03);
  color: inherit;
  text-decoration: none;
  font-size: 0.92rem;
  font-weight: 500;
  transition: 0.3s ease;
}
.contact-btn:hover {
  border-color: rgba(0,200,220,0.4);
  background: rgba(0,200,220,0.08);
  transform: translateY(-2px);
}
[data-theme="light"] .contact-btn {
  border-color: rgba(0,0,0,0.1);
  background: #fff;
}
[data-theme="light"] .contact-btn:hover {
  border-color: rgba(60,130,246,0.4);
  background: rgba(60,130,246,0.05);
}

/* ── Responsive ───────────────────────────────────────── */
@media (min-width: 1100px) {
  .tech-grid {
    grid-template-columns: repeat(5, 1fr);
  }
  .project-list {
    grid-template-columns: repeat(3, 1fr);
  }
}
@media (min-width: 768px) and (max-width: 1099px) {
  .tech-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .project-list {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 767px) {
  .post-single .main,
  .post-single main.main {
    width: 95% !important;
  }
  .about-hero h2 {
    font-size: 1.8rem;
  }
  .about-hero p {
    font-size: 0.95rem;
  }
  .tech-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.8rem;
  }
  .project-list {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 400px) {
  .tech-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<div class="about-hero">
  <h2>Stephen Kong</h2>
  <p>로보틱스 소프트웨어 개발자. 자율 순찰 로봇, 컴퓨터 비전, ROS2 기반 시스템을 개발하고 있습니다.</p>
</div>

<div class="about-section-title">기술 스택</div>

<div class="tech-grid">
  <div class="tech-card">
    <div class="tech-card-title">Robotics & ROS2</div>
    <div class="tech-tags">
      <span class="tech-tag">ROS2 Jazzy</span>
      <span class="tech-tag">Nav2</span>
      <span class="tech-tag">SLAM Toolbox</span>
      <span class="tech-tag">Gazebo</span>
      <span class="tech-tag">micro-ROS</span>
    </div>
  </div>
  <div class="tech-card">
    <div class="tech-card-title">AI / ML / DL</div>
    <div class="tech-tags">
      <span class="tech-tag">YOLO</span>
      <span class="tech-tag">ST-GCN</span>
      <span class="tech-tag">Random Forest</span>
      <span class="tech-tag">Ollama</span>
      <span class="tech-tag">TensorFlow</span>
      <span class="tech-tag">PyTorch</span>
    </div>
  </div>
  <div class="tech-card">
    <div class="tech-card-title">Computer Vision</div>
    <div class="tech-tags">
      <span class="tech-tag">OpenCV</span>
      <span class="tech-tag">MediaPipe</span>
      <span class="tech-tag">실시간 감지</span>
    </div>
  </div>
  <div class="tech-card">
    <div class="tech-card-title">Application</div>
    <div class="tech-tags">
      <span class="tech-tag">Python</span>
      <span class="tech-tag">PyQt6</span>
      <span class="tech-tag">FastAPI</span>
      <span class="tech-tag">PyQtGraph</span>
    </div>
  </div>
  <div class="tech-card">
    <div class="tech-card-title">DevOps</div>
    <div class="tech-tags">
      <span class="tech-tag">Git</span>
      <span class="tech-tag">GitHub Actions</span>
      <span class="tech-tag">Docker</span>
      <span class="tech-tag">VS Code</span>
      <span class="tech-tag">Jupyter</span>
    </div>
  </div>
</div>

<div class="about-section-title">주요 프로젝트</div>

<div class="project-list">
  <a class="project-link" href="/projects/kevin-patrol-fleet/">
    <div>
      <div class="project-link-title">Kevin Patrol Fleet</div>
      <div class="project-link-desc">다중 로봇 플릿 모니터링 시스템</div>
    </div>
    <span class="project-link-arrow">→</span>
  </a>
  <a class="project-link" href="/projects/kevin-patrol-dashboard/">
    <div>
      <div class="project-link-title">Kevin Patrol Dashboard</div>
      <div class="project-link-desc">자율 순찰 로봇 실시간 모니터링</div>
    </div>
    <span class="project-link-arrow">→</span>
  </a>
  <a class="project-link" href="/projects/home-safe-solution/">
    <div>
      <div class="project-link-title">Home Safe Solution</div>
      <div class="project-link-desc">Vision AI 기반 낙상 감지 시스템</div>
    </div>
    <span class="project-link-arrow">→</span>
  </a>
  <a class="project-link" href="/projects/eyecon-pinocchio/">
    <div>
      <div class="project-link-title">EyeCon (피노키오)</div>
      <div class="project-link-desc">실시간 대화 분석 시스템</div>
    </div>
    <span class="project-link-arrow">→</span>
  </a>
  <a class="project-link" href="/projects/home-guard-bot/">
    <div>
      <div class="project-link-title">Home Guard Bot</div>
      <div class="project-link-desc">LLM + ROS2 통합 가드 로봇</div>
    </div>
    <span class="project-link-arrow">→</span>
  </a>
  <a class="project-link" href="/projects/ros2-commander/">
    <div>
      <div class="project-link-title">ROS2 Commander</div>
      <div class="project-link-desc">게임형 ROS2 학습 애플리케이션</div>
    </div>
    <span class="project-link-arrow">→</span>
  </a>
</div>

<div class="about-section-title">연락처</div>

<div class="contact-row">
  <a class="contact-btn" href="https://github.com/skong097" target="_blank">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
    GitHub
  </a>
  <a class="contact-btn" href="https://linkedin.com/in/skong097" target="_blank">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
    LinkedIn
  </a>
</div>
