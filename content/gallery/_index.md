---
title: 갤러리
layout: single
url: /gallery/
ShowToc: false
ShowReadingTime: false
hideMeta: true
summary: 실물 로봇으로 검증한 데모 영상 모음
---

<style>
header.post-header { text-align:center; width:100%; border-bottom:1px solid rgba(128,128,128,.2); padding-bottom:1rem; margin-bottom:1.2rem; }
header.post-header h1 { font-size:40px; text-align:center; }

.gal-intro { text-align:center; color:var(--secondary); margin:0 auto 2.4rem; max-width:640px; line-height:1.7; }

.gal-sec { margin:0 0 3.2rem; }
.gal-sec h2 { font-size:22px; margin:0 0 .3rem; display:flex; align-items:center; gap:.5rem; }
.gal-sec h2 .tag { font-size:11px; font-weight:600; letter-spacing:.06em; padding:3px 9px; border-radius:99px;
  background:var(--code-bg); color:var(--secondary); text-transform:uppercase; }
.gal-sec .desc { color:var(--secondary); font-size:14px; margin:0 0 1.2rem; line-height:1.6; }

.gal-grid { display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); }
.gal-grid.wide { grid-template-columns:1fr; }

.gal-item { background:var(--entry); border-radius:10px; overflow:hidden; border:1px solid rgba(128,128,128,.18); }
.gal-item img { width:100%; height:auto; display:block; }
.gal-item video { width:100%; height:auto; display:block; background:#111; }
.gal-cap { padding:9px 12px 11px; }
.gal-cap .n { font-size:10px; font-weight:700; letter-spacing:.08em; color:#c8a24a; display:block; margin-bottom:2px; }
.gal-cap .t { font-size:13px; font-weight:600; line-height:1.4; }
.gal-cap .s { font-size:12px; color:var(--secondary); margin-top:3px; line-height:1.5; }

.gal-note { font-size:13px; color:var(--secondary); background:var(--code-bg); border-radius:8px;
  padding:14px 16px; margin:2.6rem 0 0; line-height:1.7; }
</style>

<p class="gal-intro">
실물 로봇으로 직접 검증한 장면입니다. 시뮬레이션이 아니라 실기 결과이며,
각 항목의 설계 배경과 실패·정정 과정은 아래 링크한 기술 글에 적어 두었습니다.
</p>

<div class="gal-sec">
<h2>WaSaB — 다중 로봇 통합관제 <span class="tag">심화과정 · 단독 수행</span></h2>
<p class="desc">학교 환경에서 모바일 로봇 4대를 하나의 관제 시스템으로 운용합니다. 아키텍처 설계부터 관제 콘솔, 자율주행·측위 튜닝, 순찰 통행 중재, 원격 긴급정지, 실기 검증까지 전 범위를 직접 수행하였습니다.</p>

<div class="gal-grid">

<div class="gal-item"><img src="/images/gallery/demo/wasab-traffic-control.gif" alt="로봇 3대 통행 중재" loading="lazy">
<div class="gal-cap"><span class="n">TRAFFIC CONTROL</span><span class="t">로봇 3대 통행 중재</span>
<div class="s">좌표를 버리고 홉으로 점유를 셈 · 51초 승인 14건 · 충돌 0 · 대기 0</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/wasab-patrol-3robots.gif" alt="3대 동시 순찰" loading="lazy">
<div class="gal-cap"><span class="n">FLEET PATROL</span><span class="t">로봇 3대 동시 순찰</span>
<div class="s">도메인 격리 + 2-Context 브리지로 4대를 한 화면에서 운용</div></div></div>



<div class="gal-item"><img src="/images/gallery/demo/wasab-homedock.gif" alt="홈 복귀 도킹" loading="lazy">
<div class="gal-cap"><span class="n">HOME RETURN</span><span class="t">홈 복귀 — AprilTag 도킹</span>
<div class="s">순찰 종료 후 자동 복귀 · 도킹 완료까지 무인 수행</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/wasab-patrol-cycle.gif" alt="순찰 full cycle" loading="lazy">
<div class="gal-cap"><span class="n">FULL CYCLE</span><span class="t">순찰 full cycle</span>
<div class="s">지정 경로 무한 순회 · 이벤트 감지 시 현장 확인</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/wasab-homedock-success.gif" alt="홈 복귀 도킹 성공" loading="lazy">
<div class="gal-cap"><span class="n">DOCKING</span><span class="t">홈 복귀 도킹 성공</span>
<div class="s">AprilTag 전역 재측위 후 PID 정렬 — 태그 기준 15cm</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/wasab-patrol-dock-parallel.gif" alt="순찰·도킹 동시 운용" loading="lazy">
<div class="gal-cap"><span class="n">PARALLEL OPS</span><span class="t">순찰 · 도킹 동시 운용</span>
<div class="s">한 로봇이 도킹하는 동안 다른 로봇은 순찰을 계속한다</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/wasab-console.png" alt="통합 관제 콘솔" loading="lazy">
<div class="gal-cap"><span class="n">CONSOLE</span><span class="t">통합 관제 — 실시간 위치·상태</span>
<div class="s">교사·안전관리자용 웹 관제 화면 · 기존 통신 계약 무변경</div></div></div>
</div>

<p class="desc" style="margin-top:1rem">
관련 글 —
<a href="/posts/auto_drive/다중로봇-통행중재-홉기반-점유와-실측규칙/">통행 중재</a> ·
<a href="/posts/auto_drive/wasab-로봇함대-두-도메인을-잇는-agent와-cpu튜닝/">2-Context 브리지 · CPU 튜닝</a> ·
<a href="/posts/auto_drive/nav2-apriltag-pid-정밀도킹-성공기록/">정밀 도킹</a> ·
<a href="/posts/auto_drive/amcl-sigma-hit-작은-아레나에서-측위가-흘러내린-이유/">측위 파라미터</a>
</p>
</div>

<div class="gal-sec">
<h2>MOCA — 카페 서빙·모객 로봇 <span class="tag">6인 팀 · 최우수상</span></h2>
<p class="desc">점주 한 명과 로봇들이 한 매장에서 주문·제조·서빙·모객을 자율로 수행합니다. 동작 제어 전반과 감정 분석 파이프라인, 명령 안전 중재를 담당하였습니다.</p>

<div class="gal-grid wide">
<div class="gal-item"><img src="/images/gallery/demo/moca-group-approach.gif" alt="그룹 접근 · 모객" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 01</span><span class="t">그룹 접근 · 모객 — 다중 사람 추적</span>
<div class="s">track_id · group_id 로 그룹을 인지하고 접근. 부정 감정 감지 시 즉시 중단</div></div></div>
</div>

<div class="gal-grid" style="margin-top:14px">
<div class="gal-item"><img src="/images/gallery/demo/moca-follow.gif" alt="1인 추종 주행" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 02</span><span class="t">1인 추종 주행</span>
<div class="s">카메라 → LiDAR 폴백 · 목표 거리 1.5m 유지</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/moca-minigame.gif" alt="미니게임" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 03</span><span class="t">미니게임 (닌자)</span>
<div class="s">BehaviorTree 모객 시나리오 4단계 중 하나</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/moca-handshake.gif" alt="악수 · 교감" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 04</span><span class="t">악수 · 교감 HRI</span>
<div class="s">Valence-Arousal 감정 분석으로 친밀도 판단 후 진행</div></div></div>
</div>

<p class="desc" style="margin-top:1rem">
관련 글 —
<a href="/posts/robotics/moca-감정인식-과민반응-방지-behaviortree-설계/">감정 인식 · ReactiveFallback</a> ·
<a href="/posts/robotics/moca-운영모드-오케스트레이터-우선순위-선점/">운영 모드 오케스트레이터</a> ·
<a href="/posts/robotics/moca-시스템-아키텍처-웹운영화면부터-ros2-로봇까지/">시스템 아키텍처</a>
</p>
</div>

<div class="gal-sec">
<h2>ARASEO / DALIMI — 자율주행 택시 <span class="tag">팀 프로젝트</span></h2>
<p class="desc">소형 자율주행 로봇을 택시처럼 운용합니다. 차선 인지·추종, 관제 대시보드, 사용자 PWA 웹앱을 담당하였습니다.</p>

<div class="gal-grid">
<div class="gal-item"><img src="/images/gallery/demo/araseo-curve.gif" alt="급커브 차선추종" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 01</span><span class="t">급커브 차선추종</span></div></div>

<div class="gal-item"><img src="/images/gallery/demo/araseo-schoolzone.gif" alt="스쿨존 감속" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 02</span><span class="t">스쿨존 감속 (SLOW)</span>
<div class="s">빨강·자홍이 HSV 에서 겹치던 오인식을 마스크 차집합으로 분리</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/araseo-intersection.gif" alt="십자 교차로" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 03</span><span class="t">십자 교차로 주행</span></div></div>

<div class="gal-item"><img src="/images/gallery/demo/araseo-dashboard.gif" alt="실시간 관제" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 04</span><span class="t">실시간 관제 대시보드</span>
<div class="s">다수 로봇 좌표계 정합 · 원격 기동 12초 → 0.5초</div></div></div>
</div>

<p class="desc" style="margin-top:1rem">
관련 글 —
<a href="/posts/robotics/araseo-차선주행-스쿨존-hsv-색공간-구분/">HSV 색공간 분리</a> ·
<a href="/posts/robotics/araseo-관제대시보드-다수로봇-좌표계-일치시키기/">좌표계 일치</a> ·
<a href="/posts/robotics/araseo-ssh-원격기동-12초-멈춤-0/">원격 기동 응답성</a>
</p>
</div>

<div class="gal-sec">
<h2>Home Care-Vision AI — 낙상 감지 <span class="tag">5인 팀</span></h2>
<p class="desc">가정 내 낙상·기절을 실시간 감지해 보호자에게 알립니다. AI 모델 학습과 데이터 파이프라인, 통합 모니터링 UI 를 담당하였습니다.</p>

<div class="gal-grid">
<div class="gal-item"><img src="/images/gallery/demo/homecare-pose.gif" alt="Pose 스켈레톤 추정" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 01</span><span class="t">Pose 스켈레톤 추정</span>
<div class="s">YOLO v11 Pose — 17 keypoint</div></div></div>
</div>

<div class="gal-grid wide" style="margin-top:14px">
<div class="gal-item">
<video src="/images/gallery/demo/homecare-fall-detection.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">SCENE 02</span><span class="t">낙상 실시간 감지 — 관제 화면 전체</span>
<div class="s">쓰러짐 발생 → ST-GCN 판정 <code>[FALL]</code> Confidence 100% → 이벤트 로그 적재 · 보호자 호출까지 한 화면. 56초<br>ST-GCN Fine-tuned 정확도 99.63% · Recall 99.40%</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/homecare-normal-activity.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">SCENE 03</span><span class="t">정상 활동 — 오탐 없음 구간</span>
<div class="s">앉기·눕기·보행 등 낙상과 혼동되기 쉬운 자세를 2분 11초 연속 판정. 전 구간 <code>Normal</code> 유지로 오탐(False Positive) 억제를 확인.</div></div></div>
</div>

<p class="desc" style="margin-top:1rem">
관련 글 —
<a href="/posts/computer-vision/rf-vs-stgcn-fall-detection/">Random Forest vs ST-GCN 비교</a> ·
<a href="/posts/computer-vision/stgcn-finetuning-fall-detection/">ST-GCN 전이학습</a>
</p>
</div>

<p class="gal-note">
모든 장면은 실물 로봇으로 수행한 결과입니다. 각 프로젝트에서 무엇이 어긋났고 어떻게 원인을 좁혔는지는
<a href="/posts/">포스트</a>에 기록해 두었으며, 제가 틀렸던 결론과 되돌린 판단도 지우지 않고 함께 남겼습니다.
</p>
