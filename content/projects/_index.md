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
---

<style>
/* ── Projects Page Custom Styles ──────────────────────── */
header.post-header {
  text-align: center;
  width: 100%;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}
header.post-header h1 {
  font-size: 40px;
  text-align: center;
}
[data-theme="light"] header.post-header {
  text-align: center;
  width: 100%;
  border-bottom-color: rgba(0,0,0,0.1);
}
.projects-intro {
  font-size: 1.05rem;
  opacity: 0.75;
  margin-bottom: 2rem;
  line-height: 1.7;
}
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1.4rem;
}
.project-card {
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 1.6rem;
  background: rgba(255,255,255,0.02);
  transition: 0.3s cubic-bezier(0.4,0,0.2,1);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}
.project-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--card-accent, #00c8dc), transparent);
  opacity: 0;
  transition: opacity 0.3s;
}
.project-card:hover::before {
  opacity: 1;
}
.project-card:hover {
  border-color: rgba(0,200,220,0.3);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.25),
              0 0 0 1px rgba(0,200,220,0.08);
}
[data-theme="light"] .project-card {
  border-color: rgba(0,0,0,0.08);
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
[data-theme="light"] .project-card:hover {
  border-color: rgba(60,130,246,0.3);
  box-shadow: 0 12px 40px rgba(0,0,0,0.08),
              0 0 0 1px rgba(60,130,246,0.08);
}
.project-card-status {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 3px 10px;
  border-radius: 20px;
  margin-bottom: 0.8rem;
  width: fit-content;
}
.status-active {
  background: rgba(16,185,129,0.12);
  color: #10b981;
  border: 1px solid rgba(16,185,129,0.25);
}
.status-done {
  background: rgba(0,200,220,0.1);
  color: #00c8dc;
  border: 1px solid rgba(0,200,220,0.2);
}
.project-card-title {
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 0.3rem;
}
.project-card-subtitle {
  font-size: 0.88rem;
  opacity: 0.55;
  font-weight: 500;
  margin-bottom: 0.8rem;
}
.project-card-desc {
  font-size: 0.88rem;
  line-height: 1.65;
  opacity: 0.7;
  flex-grow: 1;
  margin-bottom: 1rem;
}
.project-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-bottom: 1.2rem;
}
.project-card-tag {
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 500;
  background: rgba(0,200,220,0.07);
  border: 1px solid rgba(0,200,220,0.12);
}
[data-theme="light"] .project-card-tag {
  background: rgba(60,130,246,0.05);
  border-color: rgba(60,130,246,0.1);
}
.project-card-links {
  display: flex;
  gap: 0.8rem;
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid rgba(255,255,255,0.06);
}
[data-theme="light"] .project-card-links {
  border-top-color: rgba(0,0,0,0.06);
}
.project-card-link {
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: none;
  color: #00c8dc;
  transition: 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}
.project-card-link:hover {
  opacity: 0.8;
  transform: translateX(2px);
}
[data-theme="light"] .project-card-link {
  color: #3c82f6;
}

@media (max-width: 500px) {
  .projects-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<p class="projects-intro">
  로보틱스, 컴퓨터 비전, AI 분야에서 진행한 프로젝트들입니다.
</p>

<div class="projects-grid">

  <div class="project-card" style="--card-accent: #00c8dc;">
    <span class="project-card-status status-active">Active</span>
    <div class="project-card-title">Kevin Patrol Fleet Dashboard</div>
    <div class="project-card-subtitle">다중 로봇 플릿 모니터링 시스템</div>
    <div class="project-card-desc">
      5~10대 자율 순찰 로봇을 동시에 모니터링하는 PyQt6 대시보드. Fleet Overview 미니맵에서 전체 로봇 위치, 상태, 감지 이벤트를 실시간으로 파악할 수 있습니다.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">PyQt6</span>
      <span class="project-card-tag">ROS2</span>
      <span class="project-card-tag">SLAM</span>
      <span class="project-card-tag">Nav2</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/kevin-patrol-fleet/">상세 보기 →</a>
      <a class="project-card-link" href="https://github.com/skong097/kevin_patrol_fleet" target="_blank">GitHub →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #3c82f6;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">Kevin Patrol Dashboard</div>
    <div class="project-card-subtitle">자율 순찰 로봇 모니터링 대시보드</div>
    <div class="project-card-desc">
      단일 로봇 실시간 모니터링 시스템. SLAM 3D 뷰포트, 카메라 피드, 센서 시계열 그래프, 얼굴/낙상 감지, ROS2 토픽 모니터링을 하나의 화면에 통합합니다.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">PyQt6</span>
      <span class="project-card-tag">PyQtGraph</span>
      <span class="project-card-tag">ROS2</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/kevin-patrol-dashboard/">상세 보기 →</a>
      <a class="project-card-link" href="https://github.com/skong097/kevin_patrol" target="_blank">GitHub →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #8b5cf6;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">Home Safe Solution</div>
    <div class="project-card-subtitle">Vision AI 기반 낙상 감지 시스템</div>
    <div class="project-card-desc">
      YOLO + ST-GCN + Random Forest를 결합한 실시간 낙상 감지. GUI에서 모델 전환, 실시간 추론, 데이터베이스 기록까지 통합 파이프라인을 제공합니다.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">YOLO</span>
      <span class="project-card-tag">ST-GCN</span>
      <span class="project-card-tag">Random Forest</span>
      <span class="project-card-tag">OpenCV</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/home-safe-solution/">상세 보기 →</a>
      <a class="project-card-link" href="https://github.com/skong097/vision_ai" target="_blank">GitHub →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #f59e0b;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">EyeCon (피노키오) v3.5</div>
    <div class="project-card-subtitle">실시간 대화 분석 시스템</div>
    <div class="project-card-desc">
      Ollama EXAONE 7.8B 기반으로 13개 메트릭 + 7개 감정을 실시간 분석. 레이더 차트, LLM 대화 전략, 1.5초 응답 시간을 달성한 4-패널 대시보드입니다.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">Ollama</span>
      <span class="project-card-tag">EXAONE</span>
      <span class="project-card-tag">PyQt6</span>
      <span class="project-card-tag">NLP</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/eyecon-pinocchio/">상세 보기 →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #10b981;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">Home Guard Bot</div>
    <div class="project-card-subtitle">LLM + ROS2 통합 가드 로봇</div>
    <div class="project-card-desc">
      FastAPI v0.2에 TTS+JSON 기능을 결합하고, ROS2 Jazzy의 guard_brain 노드에서 LLM과 센서 데이터를 융합하는 지능형 경비 로봇 시스템입니다.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">ROS2 Jazzy</span>
      <span class="project-card-tag">FastAPI</span>
      <span class="project-card-tag">LLM</span>
      <span class="project-card-tag">TTS</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/home-guard-bot/">상세 보기 →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #f43f5e;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">ROS2 Commander</div>
    <div class="project-card-subtitle">게임형 ROS2 학습 애플리케이션</div>
    <div class="project-card-desc">
      ROS2 개념을 게임으로 학습하는 인터랙티브 애플리케이션. 토픽, 서비스, 액션, 파라미터 등 ROS2 핵심 개념을 실습하며 익힐 수 있습니다.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">PyQt6</span>
      <span class="project-card-tag">ROS2</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/ros2-commander/">상세 보기 →</a>
    </div>
  </div>

</div>
