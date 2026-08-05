---
title: Gallery
layout: single
ShowToc: false
ShowReadingTime: false
hideMeta: true
summary: Demo videos verified on physical robots
---

<style>
header.post-header { text-align:center; width:100%; border-bottom:1px solid rgba(128,128,128,.2); padding-bottom:1rem; margin-bottom:1.2rem; }
header.post-header h1 { font-size:40px; text-align:center; }

</style>

<p class="gal-intro">
These are scenes verified directly on physical robots. They are real hardware results, not simulations,
and the design background and failure/correction process for each item are documented in the linked technical posts below.
</p>

<div class="gal-sec" id="wasab">
<h2>WaSaB — Multi-Robot Integrated Control <span class="tag">Advanced course · Solo</span></h2>
<p class="desc">Operates 4 mobile robots under a single control system in a school environment. I handled the full scope myself — from architecture design to the control console, autonomous driving/localization tuning, patrol traffic mediation, remote emergency stop, and hardware verification.</p>

<div class="gal-grid">

<div class="gal-item"><img src="/images/gallery/demo/wasab-traffic-control.gif" alt="Traffic mediation for 3 robots" loading="lazy">
<div class="gal-cap"><span class="n">TRAFFIC CONTROL</span><span class="t">Traffic mediation for 3 robots</span>
<div class="s">Occupancy counted by hop instead of coordinates · 14 grants in 51s · 0 collisions · 0 waits</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/wasab-patrol-3robots.gif" alt="Simultaneous patrol with 3 robots" loading="lazy">
<div class="gal-cap"><span class="n">FLEET PATROL</span><span class="t">Simultaneous patrol with 3 robots</span>
<div class="s">Domain isolation + a 2-Context bridge operate all 4 robots on a single screen</div></div></div>



<div class="gal-item"><img src="/images/gallery/demo/wasab-homedock.gif" alt="Return home docking" loading="lazy">
<div class="gal-cap"><span class="n">HOME RETURN</span><span class="t">Return home — AprilTag docking</span>
<div class="s">Automatic return after patrol ends · unattended through docking completion</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/wasab-patrol-cycle.gif" alt="Patrol full cycle" loading="lazy">
<div class="gal-cap"><span class="n">FULL CYCLE</span><span class="t">Patrol full cycle</span>
<div class="s">Infinite loop over a set route · on-site check when an event is detected</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/wasab-homedock-success.gif" alt="Successful home-return docking" loading="lazy">
<div class="gal-cap"><span class="n">DOCKING</span><span class="t">Successful home-return docking</span>
<div class="s">PID alignment after AprilTag global relocalization — 15cm from the tag</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/wasab-patrol-dock-parallel.gif" alt="Patrol and docking running in parallel" loading="lazy">
<div class="gal-cap"><span class="n">PARALLEL OPS</span><span class="t">Patrol and docking running in parallel</span>
<div class="s">While one robot docks, another keeps patrolling</div></div></div>

</div>

<p class="gal-sub">Full-resolution video <span>— the entire control screen, unedited</span></p>

<div class="gal-grid tall">
<div class="gal-item">
<video src="/images/gallery/demo/3대 충돌제어성공.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">TRAFFIC CONTROL</span><span class="t">Successful 3-robot traffic mediation — full 2:55</span>
<div class="s">The full process from patrol start as 3 robots (Pinky-44 · 50 · 87) avoid each other in a narrow corridor. Mediation counts occupancy by hop, not by coordinates · 0 collisions · 0 waits</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/홈복귀도킹성공.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">DOCKING</span><span class="t">Successful home-return docking — full process</span>
<div class="s">Return command → AprilTag global relocalization → PID alignment → docking complete · 1:22</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/긴급정지전체로봇정지.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">E-STOP</span><span class="t">Remote software emergency stop — all robots halt</span>
<div class="s">A single <code>Stop</code> on the control screen halts every moving robot at once · 1:19</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/순찰fullcycle.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">FULL CYCLE</span><span class="t">Patrol full cycle — full 3:36</span>
<div class="s">Departure → waypoint loop → event check → home return, performed without a single break</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/재측위성공.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">RELOCALIZE</span><span class="t">Successful AprilTag global relocalization</span>
<div class="s">A single tag observation corrects a drifted pose estimate · 30s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/복수재측위.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">RELOCALIZE ×N</span><span class="t">Simultaneous relocalization for multiple robots</span>
<div class="s">Relocalizes all 3 online robots at once from the control screen · 34s</div></div></div>
</div>

<p class="desc" style="margin-top:1rem">
Related posts —
<a href="/posts/auto_drive/다중로봇-통행중재-홉기반-점유와-실측규칙/">Traffic mediation</a> ·
<a href="/posts/auto_drive/wasab-로봇함대-두-도메인을-잇는-agent와-cpu튜닝/">2-Context bridge · CPU tuning</a> ·
<a href="/posts/auto_drive/nav2-apriltag-pid-정밀도킹-성공기록/">Precision docking</a> ·
<a href="/posts/auto_drive/amcl-sigma-hit-작은-아레나에서-측위가-흘러내린-이유/">Localization parameters</a>
</p>
</div>

<div class="gal-sec" id="moca">
<h2>MOCA — Cafe Serving &amp; Greeting Robot <span class="tag">Team of 6 · Grand prize</span></h2>
<p class="desc">A single store owner and robots autonomously handle ordering, preparation, serving, and customer greeting in one store. I was responsible for overall motion control, the emotion-analysis pipeline, and command safety mediation.</p>

<div class="gal-grid wide">
<div class="gal-item"><img src="/images/gallery/demo/moca-group-approach.gif" alt="Group approach · greeting" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 01</span><span class="t">Group approach · greeting — multi-person tracking</span>
<div class="s">Recognizes and approaches groups via track_id · group_id. Stops immediately on detecting negative emotion</div></div></div>
</div>

<div class="gal-grid" style="margin-top:14px">
<div class="gal-item"><img src="/images/gallery/demo/moca-follow.gif" alt="Single-person following" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 02</span><span class="t">Single-person following</span>
<div class="s">Camera → LiDAR fallback · maintains a 1.5m target distance</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/moca-reaction.gif" alt="Real-time emotion-driven robot reaction" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 03</span><span class="t">Real-time emotion-driven robot reaction</span>
<div class="s">Selects a reaction from Valence-Arousal read off the face · the reaction changes as emotion changes</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/moca-handshake.gif" alt="Handshake · rapport" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 04</span><span class="t">Handshake · rapport HRI</span>
<div class="s">Proceeds after judging rapport via Valence-Arousal emotion analysis</div></div></div>
</div>

<p class="gal-sub">Greeting · group approach <span>— perception screen side by side with the real scene</span></p>

<div class="gal-grid wide">
<div class="gal-item">
<video src="/images/gallery/demo/그룹접근_합본.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">GROUP APPROACH</span><span class="t">Group approach — perception screen + on-site, combined</span>
<div class="s">Left is what the robot sees (<code>track_id</code> · <code>group_id</code>), right is the real scene at the same moment. A 2-person group and a solo person are grouped separately, and the approach target is chosen accordingly · 25s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/모객분석_고객화남_가로통합_1배속.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">ABORT ON ANGER</span><span class="t">Negative emotion detected → greeting aborted immediately</span>
<div class="s">If the customer's Valence turns negative during approach, the robot backs off instead of pushing the scenario through. 1x speed · 1:06</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/감정분석_표정분석_가로통합.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">FACE ANALYSIS</span><span class="t">Facial expression analysis — analysis screen + physical robot, combined</span>
<div class="s">How metrics extracted from the face feed into the dashboard in real time · 28s</div></div></div>
</div>

<p class="gal-sub">Control · emotion-analysis dashboard</p>

<div class="gal-grid" style="margin-top:14px">
<div class="gal-item">
<video src="/images/gallery/demo/전체.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">CONSOLE</span><span class="t">Integrated control — full flow</span>
<div class="s">Robot position on the store floor plan · mode switching · continuous for 1:27 through the next round</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/이벤트.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">EVENT</span><span class="t">Event handling — table call</span>
<div class="s">Events from tables T01–T05 dispatched by mode · 36s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/감정추이분석_ema.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">EMA</span><span class="t">Emotion trend — EMA smoothing</span>
<div class="s">Frame-level emotion values are noisy. An exponential moving average keeps the judgment from wobbling · 30s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/모객분석_감정추이_라포스코어.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">RAPPORT</span><span class="t">Rapport score computation</span>
<div class="s">Valence-Arousal, participation events, and minigame results combine into a rapport score · 45s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/표정분석_omx_reaction.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">REACTION</span><span class="t">Facial expression analysis → robot reaction link</span>
<div class="s">The segment where analysis results carry through to arm and facial-expression reactions · 28s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/rapport_minigame_가로통합.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">RAPPORT × GAME</span><span class="t">Rapport analysis + minigame, combined</span>
<div class="s">How the emotion trajectory moves during the game, analysis screen and on-site together · 24s</div></div></div>
</div>

<p class="gal-sub">Minigame · rapport</p>

<div class="gal-grid" style="margin-top:14px">
<div class="gal-item">
<video src="/images/gallery/demo/카페닌자.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">MINIGAME</span><span class="t">Cafe Ninja — game screen</span>
<div class="s">Slice menu items with the index finger and dodge bombs. 3 difficulty levels · 15s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/moca_ninja_demo_trim.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">MINIGAME</span><span class="t">Cafe Ninja — hand-gesture recognition play</span>
<div class="s">MediaPipe hand tracking turns the index fingertip coordinate into a blade · 13s</div></div></div>
</div>

<div class="gal-grid tall" style="margin-top:14px">
<div class="gal-item">
<video src="/images/gallery/demo/고객접근_매장홍보.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">APPROACH</span><span class="t">Customer approach · store promotion</span>
<div class="s">Finds a person in the corridor, approaches, and speaks to them · 30s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/minigame_best.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">MINIGAME</span><span class="t">Minigame on hardware — full process</span>
<div class="s">From approach to game end and reaction · 25s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/사용자인터렉션1.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">HRI</span><span class="t">User interaction #1</span>
<div class="s">Communicates status to the person via the facial-expression display · 9s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/사용자인터렉션2.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">HRI</span><span class="t">User interaction #2</span>
<div class="s">Expression transition on a negative reaction · 6s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/omx_reaction2.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">ARM REACTION</span><span class="t">Robot-arm reaction #1</span>
<div class="s">OpenMANIPULATOR motion driven by the emotion judgment result · 7s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/omx_reation_best.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">ARM REACTION</span><span class="t">Robot-arm reaction #2</span>
<div class="s">The best-performing reaction segment · 4s</div></div></div>
</div>

<p class="desc" style="margin-top:1rem">
Related posts —
<a href="/posts/robotics/moca-감정인식-과민반응-방지-behaviortree-설계/">Emotion recognition · ReactiveFallback</a> ·
<a href="/posts/robotics/moca-운영모드-오케스트레이터-우선순위-선점/">Operating-mode orchestrator</a> ·
<a href="/posts/robotics/moca-시스템-아키텍처-웹운영화면부터-ros2-로봇까지/">System architecture</a>
</p>
</div>

<div class="gal-sec" id="araseo">
<h2>ARASEO / DALIMI — Autonomous Taxi <span class="tag">Team project</span></h2>
<p class="desc">Operates small autonomous robots as taxis. I was responsible for lane perception/following, the control dashboard, and the user-facing PWA web app.</p>

<div class="gal-grid">
<div class="gal-item"><img src="/images/gallery/demo/araseo-curve.gif" alt="Sharp-curve lane following" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 01</span><span class="t">Sharp-curve lane following</span></div></div>

<div class="gal-item"><img src="/images/gallery/demo/araseo-schoolzone.gif" alt="School-zone deceleration" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 02</span><span class="t">School-zone deceleration (SLOW)</span>
<div class="s">Separates red/magenta misdetections that overlapped in HSV using a mask set-difference</div></div></div>

<div class="gal-item"><img src="/images/gallery/demo/araseo-intersection.gif" alt="4-way intersection" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 03</span><span class="t">4-way intersection driving</span></div></div>

</div>

<p class="gal-sub">On-track runs <span>— actual driving on the track</span></p>

<div class="gal-grid" style="margin-top:14px">
<div class="gal-item">
<video src="/images/gallery/demo/차선 주행 다중 교차.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">LANE FOLLOW</span><span class="t">Lane following — multi-crossing section</span>
<div class="s">Passes crossing sections consecutively on a city-street track. Holds its own lane even where lanes split and overlap · 57s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/장애물 감지.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">OBSTACLE</span><span class="t">Obstacle detection — stops for a lead vehicle</span>
<div class="s">Detects the vehicle ahead and stops before collision, then resumes once the way is clear · 1:25</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/십자 교차로 주행.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">INTERSECTION</span><span class="t">4-way intersection — 2 vehicles crossing</span>
<div class="s">Two vehicles enter from different directions at a dotted-line intersection and pass through · 14s</div></div></div>
</div>

<p class="gal-sub">Full-resolution video <span>— the full DALIMI CONTROL screen</span></p>

<div class="gal-grid wide">
<div class="gal-item">
<video src="/images/gallery/demo/실시간위치맵4.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">FLEET MAP</span><span class="t">Real-time position map — operating 6 vehicles</span>
<div class="s">Displays every vehicle's coordinates, driving state, and next destination simultaneously on an 1880×1410mm measured map. Loops through 4 stops — mart, office, park, school · 49s</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/실시간위치맵2.webm" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">FLEET MAP</span><span class="t">Position map linked with the vehicle status table</span>
<div class="s">Each vehicle's X/Y coordinates and TARGET·HINT (STRAIGHT / LEFT / U-TURN) update on the same cycle as the map · 17s</div></div></div>
</div>

<p class="desc" style="margin-top:1rem">
Related posts —
<a href="/posts/robotics/araseo-차선주행-스쿨존-hsv-색공간-구분/">HSV color-space separation</a> ·
<a href="/posts/robotics/araseo-관제대시보드-다수로봇-좌표계-일치시키기/">Coordinate-frame alignment</a> ·
<a href="/posts/robotics/araseo-ssh-원격기동-12초-멈춤-0/">Remote-start responsiveness</a>
</p>
</div>

<div class="gal-sec" id="homecare">
<h2>Home Care-Vision AI — Fall Detection <span class="tag">Team of 5</span></h2>
<p class="desc">Detects falls and fainting at home in real time and alerts the caregiver. I was responsible for AI model training, the data pipeline, and the integrated monitoring UI.</p>

<div class="gal-grid">
<div class="gal-item"><img src="/images/gallery/demo/homecare-pose.gif" alt="Pose skeleton estimation" loading="lazy">
<div class="gal-cap"><span class="n">SCENE 01</span><span class="t">Pose skeleton estimation</span>
<div class="s">YOLO v11 Pose — 17 keypoint</div></div></div>
</div>

<div class="gal-grid wide" style="margin-top:14px">
<div class="gal-item">
<video src="/images/gallery/demo/정상활동.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">SCENE 02</span><span class="t">Normal activity → fall — unedited 2:11</span>
<div class="s">The first minute keeps standing/walking/sitting classified as <code>[OK] Normal</code> to show no false positives, then transitions to <code>[DANGER] Fallen</code> at the actual fall at the 62-second mark. Captured in one continuous take, with no cuts.</div></div></div>

<div class="gal-item">
<video src="/images/gallery/demo/낙상탐지.mp4" controls loop muted playsinline preload="metadata"></video>
<div class="gal-cap"><span class="n">SCENE 03</span><span class="t">Moment of the fall — [FALL] detected</span>
<div class="s">Fall occurs → ST-GCN judgment <code>[FALL]</code> Confidence 100% → event logged · caregiver call, all in one screen. 56s<br>ST-GCN fine-tuned accuracy 99.63% · Recall 99.40%</div></div></div>
</div>

<p class="desc" style="margin-top:1rem">
Related posts —
<a href="/posts/computer-vision/rf-vs-stgcn-fall-detection/">Random Forest vs ST-GCN comparison</a> ·
<a href="/posts/computer-vision/stgcn-finetuning-fall-detection/">ST-GCN transfer learning</a>
</p>
</div>

<p class="gal-note">
Every scene is a result performed on a physical robot. What went wrong in each project and how the cause was narrowed down
is recorded in the <a href="/posts/">posts</a>, including the conclusions I got wrong and later reversed, left in rather than erased.
</p>
