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
</style>

<p class="projects-intro">
  로보틱스, 컴퓨터 비전, AI 분야에서 진행한 프로젝트들입니다.
</p>

<div class="projects-grid">

  <div class="project-card" style="--card-accent: #ec4899;">
    <span class="project-card-status status-active">Active</span>
    <div class="project-card-title">MOCA — Cafe Service Robot</div>
    <div class="project-card-subtitle">카페 모객·서빙·안내 자율 로봇</div>
    <div class="project-card-desc">
      BehaviorTree 기반 6단계 모객 시나리오와 손님 표정 감정(Valence-Arousal) 실시간 분석을 결합한 모바일 매니퓰레이터 카페 로봇. 5가지 운영 모드(서빙·순회·안내·모객·대기)를 우선순위 기반 오케스트레이터가 자동 전환·복귀시키며, 운영자는 웹 대시보드에서 원격 관제합니다.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">ROS2 Jazzy</span>
      <span class="project-card-tag">C++</span>
      <span class="project-card-tag">BehaviorTree.CPP 4.8</span>
      <span class="project-card-tag">Nav2</span>
      <span class="project-card-tag">MediaPipe</span>
      <span class="project-card-tag">YOLOv8n</span>
      <span class="project-card-tag">FastAPI · WebSocket</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/posts/robotics/moca-감정인식-과민반응-방지-behaviortree-설계/">감정 인식 BT →</a>
      <a class="project-card-link" href="/posts/robotics/moca-운영모드-오케스트레이터-우선순위-선점/">운영 모드 →</a>
      <a class="project-card-link" href="/posts/robotics/moca-colcon-symlink-정적파일-404-해결/">colcon 404 →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #14b8a6;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">ARASEO — Autonomous Taxi</div>
    <div class="project-card-subtitle">미니시티 자율주행 택시 시스템</div>
    <div class="project-card-desc">
      소형 자율주행 로봇(Pinky)을 택시처럼 운용하는 미니시티 시스템. PWA 웹앱으로 목적지를 호출하면 자동 배차·자율주행·결제까지 이어지고, 관제 대시보드에서 다수 로봇 운행을 실시간으로 관제합니다. 차선 인지·추종, 좌표계 정합, 원격 기동 응답성 등 운영 안정성에 초점.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">ROS2 Jazzy</span>
      <span class="project-card-tag">FastAPI · WebSocket</span>
      <span class="project-card-tag">OpenCV (HSV)</span>
      <span class="project-card-tag">Vanilla JS · PWA</span>
      <span class="project-card-tag">SQLite</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/posts/robotics/araseo-관제대시보드-다수로봇-좌표계-일치시키기/">좌표계 일치 →</a>
      <a class="project-card-link" href="/posts/robotics/araseo-ssh-원격기동-12초-멈춤-0.5초-단축/">SSH 12→0.5초 →</a>
      <a class="project-card-link" href="/posts/robotics/araseo-차선주행-스쿨존-hsv-색공간-구분/">HSV 분리 →</a>
    </div>
  </div>

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
