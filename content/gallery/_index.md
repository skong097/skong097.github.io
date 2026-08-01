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
.gal-grid.tall { grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); align-items:start; }

.gal-sub { font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase;
  color:var(--secondary); margin:2rem 0 .8rem; padding-top:1rem; border-top:1px dashed rgba(128,128,128,.25); }
.gal-sub span { font-weight:400; text-transform:none; letter-spacing:0; }

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

</div>

<p class="gal-sub">원본 화질 영상 <span>— 관제 화면 전체를 무편집으로 담았습니다</span></p>

<div class="gal-grid tall">
<div class="gal-item">
<video src="/images/gallery/demo/순찰fullcycle.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">FULL CYCLE</span><span class="t">순찰 full cycle — 전체 3분 36초</span>
<div class="s">출발 → 경유지 순회 → 이벤트 확인 → 홈 복귀까지 한 번도 끊지 않고 수행</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/긴급정지전체로봇정지.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">E-STOP</span><span class="t">원격 SW 긴급정지 — 전체 로봇 정지</span>
<div class="s">관제 화면 <code>정지</code> 한 번으로 주행 중인 전 로봇을 동시에 멈춘다 · 1분 19초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/홈복귀도킹성공.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">DOCKING</span><span class="t">홈 복귀 도킹 성공 — 전체 과정</span>
<div class="s">복귀 명령 → AprilTag 전역 재측위 → PID 정렬 → 도킹 완료 · 1분 22초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/재측위성공.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">RELOCALIZE</span><span class="t">AprilTag 전역 재측위 성공</span>
<div class="s">흘러내린 추정 위치를 태그 관측 한 번으로 되돌린다 · 30초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/복수재측위.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">RELOCALIZE ×N</span><span class="t">복수 로봇 동시 재측위</span>
<div class="s">온라인 로봇 3대를 관제 화면에서 한꺼번에 재측위 · 34초</div></div></div>
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

<p class="gal-sub">모객 · 그룹 접근 <span>— 인지 화면과 실제 현장을 나란히</span></p>

<div class="gal-grid wide">
<div class="gal-item">
<video src="/images/gallery/demo/그룹접근_합본.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">GROUP APPROACH</span><span class="t">그룹 접근 — 인지 화면 · 현장 합본</span>
<div class="s">왼쪽은 로봇이 보는 화면(<code>track_id</code> · <code>group_id</code>), 오른쪽은 같은 순간의 실제 현장. 2인 그룹과 1인을 각각 다른 그룹으로 묶어 접근 대상을 고른다 · 25초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/모객분석_고객화남_가로통합_1배속.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">ABORT ON ANGER</span><span class="t">부정 감정 감지 → 모객 즉시 중단</span>
<div class="s">접근 중 고객의 Valence 가 음(-)으로 꺾이면 시나리오를 끝까지 밀지 않고 물러난다. 1배속 · 1분 6초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/감정분석_표정분석_가로통합.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">FACE ANALYSIS</span><span class="t">표정 분석 — 분석 화면 · 실물 합본</span>
<div class="s">얼굴에서 뽑은 지표가 대시보드에 실시간으로 꽂히는 과정 · 28초</div></div></div>
</div>

<p class="gal-sub">관제 · 감정 분석 대시보드</p>

<div class="gal-grid" style="margin-top:14px">
<div class="gal-item">
<video src="/images/gallery/demo/전체.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">CONSOLE</span><span class="t">통합 관제 — 전체 흐름</span>
<div class="s">매장 평면도 위 로봇 위치 · 모드 전환 · 다음 순회까지 1분 27초 연속</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/이벤트.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">EVENT</span><span class="t">이벤트 처리 — 테이블 호출</span>
<div class="s">T01~T05 테이블에서 발생한 이벤트를 모드별로 배차 · 36초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/감정추이분석_ema.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">EMA</span><span class="t">감정 추이 — EMA 평활</span>
<div class="s">프레임 단위 감정값은 튄다. 지수이동평균으로 눌러야 판단이 흔들리지 않는다 · 30초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/모객분석_감정추이_라포스코어.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">RAPPORT</span><span class="t">라포 스코어 산출</span>
<div class="s">Valence-Arousal · 참여 이벤트 · 미니게임 결과를 합쳐 친밀도 점수로 · 45초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/표정분석_omx_reaction.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">REACTION</span><span class="t">표정 분석 → 로봇 반응 연동</span>
<div class="s">분석 결과가 로봇팔·표정 반응으로 이어지는 구간 · 28초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/rapport_minigame_가로통합.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">RAPPORT × GAME</span><span class="t">라포 분석 · 미니게임 합본</span>
<div class="s">게임 중 감정 궤적이 어떻게 움직이는지 분석 화면과 현장을 함께 · 24초</div></div></div>
</div>

<p class="gal-sub">미니게임 · 교감</p>

<div class="gal-grid" style="margin-top:14px">
<div class="gal-item">
<video src="/images/gallery/demo/카페닌자.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">MINIGAME</span><span class="t">카페 닌자 — 게임 화면</span>
<div class="s">검지로 메뉴를 베고 폭탄을 피한다. 난이도 3단 · 15초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/moca_ninja_demo_trim.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">MINIGAME</span><span class="t">카페 닌자 — 손동작 인식 플레이</span>
<div class="s">MediaPipe 손 추적으로 검지 끝 좌표를 칼날로 · 13초</div></div></div>
</div>

<div class="gal-grid tall" style="margin-top:14px">
<div class="gal-item">
<video src="/images/gallery/demo/고객접근_매장홍보.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">APPROACH</span><span class="t">고객 접근 · 매장 홍보</span>
<div class="s">복도에서 사람을 찾아 다가가 말을 건다 · 30초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/minigame_best.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">MINIGAME</span><span class="t">미니게임 실기 — 전 과정</span>
<div class="s">접근부터 게임 종료·반응까지 · 25초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/사용자인터렉션1.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">HRI</span><span class="t">사용자 인터랙션 ①</span>
<div class="s">표정 디스플레이로 상태를 사람에게 알린다 · 9초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/사용자인터렉션2.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">HRI</span><span class="t">사용자 인터랙션 ②</span>
<div class="s">부정 반응일 때의 표정 전환 · 6초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/omx_reaction2.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">ARM REACTION</span><span class="t">로봇팔 반응 ①</span>
<div class="s">감정 판정 결과에 따른 OpenMANIPULATOR 동작 · 7초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/omx_reation_best.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">ARM REACTION</span><span class="t">로봇팔 반응 ②</span>
<div class="s">가장 잘 나온 반응 구간 · 4초</div></div></div>
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

<p class="gal-sub">원본 화질 영상 <span>— DALIMI CONTROL 관제 화면 전체</span></p>

<div class="gal-grid wide">
<div class="gal-item">
<video src="/images/gallery/demo/실시간위치맵4.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">FLEET MAP</span><span class="t">실시간 위치 맵 — 차량 6대 운용</span>
<div class="s">1880×1410mm 실측 맵 위에 전 차량의 좌표·주행 상태·다음 목적지를 동시에 표시. 마트·회사·공원·학교 4개 정류장 순회 · 49초</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/실시간위치맵2.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">FLEET MAP</span><span class="t">위치 맵 · 차량 상태 테이블 연동</span>
<div class="s">각 차량의 X·Y 좌표와 TARGET·HINT(STRAIGHT / LEFT / U-TURN)가 맵과 같은 주기로 갱신된다 · 17초</div></div></div>
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
<video src="/images/gallery/demo/정상활동.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">SCENE 02</span><span class="t">정상 활동 — [OK] Normal</span>
<div class="s">앉기·눕기·보행 등 낙상과 혼동되기 쉬운 자세를 2분 11초 연속 판정. 전 구간 <code>Normal</code> 유지로 오탐(False Positive) 억제를 확인.</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/낙상탐지.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">SCENE 03</span><span class="t">낙상 순간 — [FALL] 감지</span>
<div class="s">쓰러짐 발생 → ST-GCN 판정 <code>[FALL]</code> Confidence 100% → 이벤트 로그 적재 · 보호자 호출까지 한 화면. 56초<br>ST-GCN Fine-tuned 정확도 99.63% · Recall 99.40%</div></div></div>
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
