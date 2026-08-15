---
title: Projects
layout: single
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
  border-bottom: 1px solid var(--border);
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}
header.post-header h1 {
  font-size: 40px;
  text-align: center;
}
</style>

<p class="projects-intro">
  Projects in robotics, computer vision, and AI.
</p>

<div class="projects-grid">

  <div class="project-card" style="--card-accent: #F7A8B8;">
    <span class="project-card-status status-active">Active</span>
    <div class="project-card-title">MOCA — Cafe Service Robot</div>
    <div class="project-card-subtitle">Autonomous cafe robot for greeting, serving, and guidance</div>
    <div class="project-card-desc">
      A mobile-manipulator cafe robot combining a six-stage BehaviorTree greeting scenario with real-time customer facial-emotion analysis (Valence-Arousal). A priority-based orchestrator switches between and returns from five operating modes (serving, patrol, guidance, greeting, standby), while operators supervise remotely from a web dashboard.
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
      <a class="project-card-link" href="/posts/robotics/moca-감정인식-과민반응-방지-behaviortree-설계/">Emotion-aware BT →</a>
      <a class="project-card-link" href="/posts/robotics/moca-운영모드-오케스트레이터-우선순위-선점/">Operating modes →</a>
      <a class="project-card-link" href="/posts/robotics/moca-colcon-symlink-정적파일-404-해결/">colcon 404 →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #7FD8BE;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">ARASEO — Autonomous Taxi</div>
    <div class="project-card-subtitle">Mini-city autonomous taxi system</div>
    <div class="project-card-desc">
      A mini-city system that operates small autonomous robots (Pinky) like taxis. Hailing a destination from the PWA web app triggers automatic dispatch, autonomous driving, and payment end to end, while a control dashboard supervises multiple robots in real time. The focus is operational stability: lane detection and following, coordinate-frame alignment, and remote-startup responsiveness.
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
      <a class="project-card-link" href="/posts/robotics/araseo-관제대시보드-다수로봇-좌표계-일치시키기/">Frame alignment →</a>
      <a class="project-card-link" href="/posts/robotics/araseo-ssh-원격기동-12초-멈춤-0.5초-단축/">SSH 12s → 0.5s →</a>
      <a class="project-card-link" href="/posts/robotics/araseo-차선주행-스쿨존-hsv-색공간-구분/">HSV separation →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #8FD8E8;">
    <span class="project-card-status status-active">Active</span>
    <div class="project-card-title">Kevin Patrol Fleet Dashboard</div>
    <div class="project-card-subtitle">Multi-robot fleet monitoring system</div>
    <div class="project-card-desc">
      A PyQt6 dashboard for monitoring 5–10 autonomous patrol robots at once. The Fleet Overview minimap shows every robot's position, status, and detection events in real time.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">PyQt6</span>
      <span class="project-card-tag">ROS2</span>
      <span class="project-card-tag">SLAM</span>
      <span class="project-card-tag">Nav2</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/kevin-patrol-fleet/">Details →</a>
      <a class="project-card-link" href="https://github.com/skong097/kevin_patrol_fleet" target="_blank">GitHub →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #A9C7F0;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">Kevin Patrol Dashboard</div>
    <div class="project-card-subtitle">Autonomous patrol robot monitoring dashboard</div>
    <div class="project-card-desc">
      A real-time monitoring system for a single robot. It brings a SLAM 3D viewport, camera feed, sensor time-series plots, face and fall detection, and ROS2 topic monitoring together on one screen.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">PyQt6</span>
      <span class="project-card-tag">PyQtGraph</span>
      <span class="project-card-tag">ROS2</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/kevin-patrol-dashboard/">Details →</a>
      <a class="project-card-link" href="https://github.com/skong097/kevin_patrol" target="_blank">GitHub →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #C4B5FD;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">Home Safe Solution</div>
    <div class="project-card-subtitle">Vision-AI fall detection system</div>
    <div class="project-card-desc">
      Real-time fall detection combining YOLO, ST-GCN, and Random Forest. The GUI provides an integrated pipeline covering model switching, live inference, and database logging.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">YOLO</span>
      <span class="project-card-tag">ST-GCN</span>
      <span class="project-card-tag">Random Forest</span>
      <span class="project-card-tag">OpenCV</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/home-safe-solution/">Details →</a>
      <a class="project-card-link" href="https://github.com/skong097/vision_ai" target="_blank">GitHub →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #F7C948;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">EyeCon (Pinocchio) v3.5</div>
    <div class="project-card-subtitle">Real-time conversation analysis system</div>
    <div class="project-card-desc">
      Real-time analysis of 13 metrics and 7 emotions, built on Ollama EXAONE 7.8B. A four-panel dashboard with radar charts, LLM conversation strategies, and a 1.5-second response time.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">Ollama</span>
      <span class="project-card-tag">EXAONE</span>
      <span class="project-card-tag">PyQt6</span>
      <span class="project-card-tag">NLP</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/eyecon-pinocchio/">Details →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #A8DDB5;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">Home Guard Bot</div>
    <div class="project-card-subtitle">LLM + ROS2 integrated guard robot</div>
    <div class="project-card-desc">
      An intelligent security robot system that adds TTS and JSON capabilities to FastAPI v0.2 and fuses LLM output with sensor data in a `guard_brain` node on ROS2 Jazzy.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">ROS2 Jazzy</span>
      <span class="project-card-tag">FastAPI</span>
      <span class="project-card-tag">LLM</span>
      <span class="project-card-tag">TTS</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/home-guard-bot/">Details →</a>
    </div>
  </div>

  <div class="project-card" style="--card-accent: #F4A6A0;">
    <span class="project-card-status status-done">Done</span>
    <div class="project-card-title">ROS2 Commander</div>
    <div class="project-card-subtitle">Gamified ROS2 learning application</div>
    <div class="project-card-desc">
      An interactive application for learning ROS2 concepts through gameplay. Core concepts — topics, services, actions, and parameters — are picked up hands-on.
    </div>
    <div class="project-card-tags">
      <span class="project-card-tag">Python</span>
      <span class="project-card-tag">PyQt6</span>
      <span class="project-card-tag">ROS2</span>
    </div>
    <div class="project-card-links">
      <a class="project-card-link" href="/projects/ros2-commander/">Details →</a>
    </div>
  </div>

</div>
