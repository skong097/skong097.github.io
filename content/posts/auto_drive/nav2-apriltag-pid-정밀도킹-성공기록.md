---
title: "Nav2로 가까이, AprilTag PID로 정확히 — 정밀 도킹 성공 기록"
date: 2026-07-11
tags: ["auto-drive", "ros2", "nav2", "apriltag", "pid", "pose-regulation", "docking", "precision-parking", "wasab", "pinky"]
categories: ["robotics"]
summary: "map11과 sigma_hit 0.05 위에서, Nav2 접근 + AprilTag PID로 4개 태그(7/8/9/10)에서 정면 15cm 정밀 도킹을 성립시켰다. 옛 P-제어의 좌우 offset 한계를 pose regulation(ρ,α,β)으로, 평면 마커의 yaw ±flip을 YawFilter로 풀었고, 반복되던 Nav2 nav_failed의 진범이 저배터리였음을 짚는다. 시행착오와 최종 확정 설정값을 정리한다."
draft: false
ShowToc: true
TocOpen: true
---

앞선 글에서 `wasab_map11`을 만들고 AMCL `sigma_hit`을 `0.05`로 확정해 측위 신뢰를 확보했다
([맵을 만들기 전에 로봇을 먼저 검증해야 하는 이유](../로봇을-먼저-검증하라-라이다편향과-preflight-게이트/)).
이 글은 그 위에서 실제로 정밀 도킹을 성공시킨 기록이다.

콘솔 지휘용 Nav2 접근 → AprilTag PID **정면 15cm 정밀 도킹**을 4개 태그(7/8/9/10)에서 성립시켰고,
tag8↔tag7↔tag9 이동 도킹을 end-to-end로 완주했다(물리 15cm 정지선 검증). 데모 촬영도 성공했다.

{{< figure src="/images/auto_drive/nav2-pid-tag9-docking-demo.gif" alt="Pinky 로봇이 Nav2로 tag9 접근점까지 이동한 뒤 AprilTag를 보며 저속 PID로 정렬해 태그 정면 15cm에서 멈추는 정밀 도킹 데모" >}}

---

## 0. 한 장 요약

| 항목 | 결론 |
|---|---|
| 서보 | **pose regulation**(ρ,α,β)로 diff-drive가 호를 그려 좌우 offset 제거 → 정면 15cm |
| yaw 안정화 | **YawFilter**(circular mean, window 6) — 평면 마커 ±flip 제거 |
| 정밀도 | ex ~6–12mm(15.x cm), ey <4mm, 4태그 물리 검증 |
| Nav2 flaky의 진범 | **저배터리** (6.9V/17% → controller 20→8Hz 기아 → ack timeout). `.44` 신선 배터리로 해결 |
| CPU 처방 | detector **NAV 구간 유휴**(153→26%) + **카메라 pre-warm**(cold-start 회피) |
| 데모 로봇 | **`.44`** 온보딩(`.50` 코드·태그·카메라값 그대로 배포, 재캘리브 불필요) |

---

## 1. 정면 15cm 서보 — 옛 P-제어의 구조적 한계

**증상**: 옛 서보는 `|error_x| < tol_x`가 되면 `vx = 0`이었다. diff-drive는 제자리 회전만으로는
**좌우 offset(error_y)을 병진으로 못 고친다** → 좌우 3~5cm 잔차가 남았다. (옛 메모의
"tol_y 0.04로 완화"는 이 한계를 우회한 것이었다.)

**오판 정정**: "15cm에서 태그가 FOV에서 짤린다"를 **거리 한계로 오진**했었다. 실제로는
**좌우 오차 탓**이었다 — 비스듬히 접근해서 태그가 화면 옆으로 이탈한 것이다. 정면으로 접근하면
15cm에서도 태그가 남는다.

**조치**: `pid.py`를 **pose regulation**으로 교체했다. 목표 주차자세
`G = se2_compose(tag_base, inv(tag_goal))`를 극좌표로 추종한다.

{{< figure src="/images/diagrams/autodrive-pose-regulation.svg" alt="AprilTag PID 정밀 도킹의 pose regulation 기하. 로봇이 목표 주차자세 G를 극좌표 ρ·α·β로 추종한다. ρ는 목표까지 거리, α는 로봇 진행방향과 목표를 잇는 선의 각도, β는 목표에서의 최종 방위 오차다. 로봇은 직선이 아니라 호를 그려 태그 법선 위로 올라타므로 좌우 offset과 yaw가 함께 0으로 수렴해 태그 정면 15cm에서 멈춘다." >}}

```text
ρ = |G|,  heading = atan2(gy,gx),  reverse = |heading|>π/2
α = heading(전진) 또는 normalize(heading-π)(후진),  β = normalize(gθ - α)
v = k_rho·ρ (reverse면 -),  wz = k_alpha·α + k_beta·β,  clamp
ρ<tol_x면 병진정지·최종 yaw 정렬만
```

로봇이 **호를 그려 태그 법선 위로 올라타** ey→0, eyaw→0, ex→0(=15cm 정면)이 함께 수렴한다.

## 2. eyaw 프레임마다 ±flip → wz 요동

**증상**: dry-run에서 `eyaw +0.09/-0.09`가 교대로 나왔고 `wz -0.2/0`이 요동쳤다.
**평면 마커의 pose ambiguity** 때문이다 — 정면일수록 두 해가 비슷해 뒤집힌다.

**조치**: `pose_filter.py`에 **YawFilter**를 추가했다. 최근 window개 yaw의 circular mean
(`atan2(Σsin, Σcos)`)을 쓴다. 노드 `_on_tag`에서 **x/y는 raw, yaw만 필터**한다.
대칭 flip이 ~0으로 수렴하면서 wz가 안정됐다.

## 3. dry-run 먼저 — 모션 전 방향 검증

`cmd_vel_enabled:=false`로 서보를 기동해 docking_state의 **계산 vx/wz 부호**를 읽어
방향과 안정성을 확인한 뒤 실주행했다. (CPU 이슈는 실제 nav을 돌려야 나오므로 dry-run으로는
재현되지 않는다.)

## 4. Nav2 이동 도킹 — 반복 nav_failed의 진범

이동 도킹의 Nav2 접근이 `nav_failed`로 자주 실패했다. 층층이 원인을 벗겨냈다.

1. **cold-start**: `dock.launch` 첫 시도는 detector **카메라 init 스파이크**로 planner가 굶어
   `compute_path ack timeout`(~1s). → **warm 재시도로 통과**(성공 런은 전부 warm).
2. **detector CPU**: UDP 스트리밍(매 프레임 JPEG 인코딩+송신)이 detector CPU를
   **+40~85%p(153%)** 올렸다. → **NAV 구간 detector 유휴 게이트**로 153→26%.
3. **스테일 프로세스**: 5.5분 생존한 옛 `precision_parking`이 **카메라를 점유**(새 detector
   "Device busy")하고 CPU로 반복 방해. → `kill -9` 철저히.
4. **Nav2 재기동 여파**: 재시작 직후 **costmap 미준비**("no valid path") + **TF cache 드롭** +
   **goal response send timeout**. → **재기동 후 충분히 정착 대기**가 필요.
5. **파라미터 오조준**: "acknowledge goal request timeout"은 `wait_for_service_timeout`가
   아니라 `default_server_timeout`(200ms, ack 대기)이 지배한다. `wait_for_service_timeout 4000`
   시도는 무효 → **1000 원복**.
6. **★ 진범 = 저배터리**: 위 처방들로 개선됐으나 잔여 실패가 지속됐다. `.50`의
   **6.9V/17%**에서 controller loop이 **20→8Hz**로 굶은 것이 근본 원인이었다.
   **`.44` 신선 배터리로 교체하니 nav이 안정 완주**했다. (성공했던 초반 런들은 배터리가 더 높았다.)

## 5. tag10 — Nav2 이동 불가(구조적)

tag10 접근점(0.5m standoff)이 **내벽 박스**에 2cm로 붙어 costmap inflation상 도달 불가였다.
위쪽 standoff 0.30 접근점은 도달 가능하나 **등록 yaw ±13° 오차** + 30cm 근접으로 서보가
정렬 중 태그를 놓쳤다(tag_lost).

**조치**: tag10은 **PID + 물리 배치**(정면 30cm 수동 배치, `nav_enabled:=false`)로 DONE
(ex 7.6 / ey 1.7). 이동 도킹은 tag7/8/9만으로 한다.

## 6. `.44` 온보딩 — 데모 로봇 교체

`.50` 저배터리로 `.44`(신선)로 교체했다. **`.50`의 working 상태를 통째로 백업 후 배포**했다:
`wasab_docking`(소스) + `wasab_robot_agent` + `~/.wasab/tag_map_poses.yaml`를 tar로 묶어
`.44`에 추출하고 `map12`를 복사한 뒤 `colcon build`(2 pkg).

**★ `.50` 카메라값(fx 588.6 / camera_to_base.x 0.023)이 `.44`에서도 15cm 정확** →
**재캘리브 불필요**(개체차 무시 가능).

---

## 7. 최종 설정값 (확정)

### 7.1 `precision_parking.yaml`

```yaml
tag_id: 8                    # 파킹 대상별 launch 오버라이드
tag_size_m: 0.06             # 실측
# 카메라 (⚠ .50 실측값, .44도 그대로 15cm OK — 개체차 무시가능)
camera.fx: 588.6             # = 635/1.0788 (2점 적합, fy=fx 가정)
camera.fy: 588.6
camera.cx: 320.0 ; camera.cy: 240.0   # 근사(미보정 — 좌우/yaw 정확도는 개선 안 됨)
camera_to_base.x: 0.023      # 실측(바퀴축→렌즈면 23mm)
camera_to_base.z: 0.10 ; camera_to_base.yaw: 0.0
swap_rb: false               # picamera2 RGB888 = 실제 BGR
flip_vertical: true ; flip_horizontal: true   # 카메라 상하반전 실장 → rot180
# 서보 (pose regulation)
tag_goal_x: 0.15             # 정면 15cm 밀착
tag_goal_y: 0.0 ; tag_goal_yaw: 0.0
k_rho: 0.5                   # 전진(거리)
k_alpha: 1.2                 # G 방향 조향 (>k_rho, 안정조건)
k_beta: -0.4                 # 최종 방위 (<0, 안정조건)
kyaw: 0.9                    # ρ 도달 후 최종 yaw 정렬
max_vx: 0.02 ; max_vx_back: 0.01 ; max_wz: 0.20
tol_x: 0.015 ; tol_y: 0.010 ; tol_yaw: 0.04   # ★tol_y 0.010 (옛 0.04로 되돌리지 말 것)
yaw_filter_window: 6         # eyaw circular-mean
settle_time_s: 0.4 ; settle_min_frames: 5
overall_timeout_s: 45.0 ; tag_lost_timeout_s: 0.5 ; search_timeout_s: 10.0
control_rate_hz: 20.0
```

### 7.2 `nav2_params_0709.yaml` (AMCL/BT 핵심)

```yaml
amcl: alpha1~5: 0.2 ; recovery_alpha_fast/slow: 0.0 ; sigma_hit: 0.05   # ★주행중 밀림 해소
      laser_model_type: likelihood_field ; z_hit 0.5 ; z_rand 0.5
      min_particles 1000 ; max_particles 2500 ; update_min_d/a 0.05
bt_navigator: wait_for_service_timeout: 1000 ; default_server_timeout: 200
              transform_tolerance: 1.0 ; bt_loop_duration: 10
controller_server: controller_frequency: 20.0
```

`sigma_hit: 0.05`가 왜 이 도킹의 선결 조건이었는지는
[sigma_hit 딥다이브](../amcl-sigma-hit-작은-아레나에서-측위가-흘러내린-이유/)에서 다뤘다.
목표 20cm 앞에서 자기 위치를 19cm 틀리게 알면 접근 자체가 벽을 친다.

### 7.3 휠 캘리브 (bringup, 개체별)

```text
.44 / .50 : wheel_radius 0.0279, wheel_separation 0.1000
.87       : 0.0273 / 0.0976
```

---

## 8. 운영 절차 (재현용)

### 8.1 스택 기동 (`.44`, 도메인 50)

```bash
# 공통 헤더
source /opt/ros/jazzy/setup.bash ; source ~/pinky_pro/install/setup.bash
export ROS_DOMAIN_ID=50 ROS_STATIC_PEERS=192.168.0.29
# ap0 정리 (부팅마다 부활)
sudo systemctl stop hostapd dnsmasq ; sudo ip link set ap0 down ; sudo ip addr flush dev ap0
# ① bringup ② localization ③ nav2
ros2 launch pinky_bringup bringup_robot.launch.xml
ros2 launch pinky_navigation localization_launch.xml \
  map:=$HOME/wasab/wasab_navigation/map/wasab_map11.yaml \
  params_file:=$HOME/wasab/wasab_navigation/wasab_nav2/params/nav2_params_0709.yaml use_composition:=False
ros2 launch pinky_navigation navigation_launch.xml \
  params_file:=$HOME/wasab/wasab_navigation/wasab_nav2/params/nav2_params_0709.yaml
```

### 8.2 CLI 이동 도킹

```bash
ros2 launch wasab_docking dock.launch.py tag_id:=N \
  approach_pose_x:=<AX> approach_pose_y:=<AY> approach_pose_yaw:=<AYAW> \
  nav_enabled:=true cmd_vel_enabled:=true tag_goal_x:=0.15
# 첫 시도 cold-start nav_failed 시 kill 후 즉시 재시도(warm)
```

접근점(standoff 0.5m)과 재측위 pose(15cm):

| tag | 접근점 (AX, AY, AYAW) | 재측위 pose(15cm) |
|---|---|---|
| 8 | (-0.062, 0.370, -85°) | (-0.031, 0.021, -85°) |
| 7 | (-0.046, 0.350, +83.6°) | (-0.007, 0.698, +83.6°) |
| 9 | (1.335, -0.051, +6.2°) | (1.683, -0.013, +6.2°) |
| 10 | (1.730, 0.527, +90° 벽법선) | — (등록yaw 오차 15°; PID+물리배치 권장) |

### 8.3 촬영 순서 (cold-start 회피)

`dock.launch` 첫 시도는 cold-start로 nav_failed가 나므로(정상), 촬영 테이크가 실패하지 않게:
**재측위(tag8, median<2cm) → 카메라 pre-warm(detector 잠깐 standalone 기동→kill) → 촬영 시작
→ dock**. 이렇게 하면 첫 테이크가 완주한다.

---

## 9. 검증 결과 (물리 15cm 확인)

| 런 | 로봇 | done_error_x | done_error_y | 비고 |
|---|---|---|---|---|
| tag8 (Nav2+PID) | .50 | 2.4mm (15.24cm) | 3.4mm | |
| tag7 (Nav2+PID) | .50 | 12mm | 2.5mm | tag8→tag7 |
| tag9 (Nav2+PID) | .50 | 6.6mm | 0.4mm | tag7→tag9 (1.5m, 07-09 실패거리) |
| tag10 (PID+물리) | .50 | 7.6mm | 1.7mm | Nav2 이동 불가(박스) |
| tag9 (Nav2+PID) | .44 | ~15cm(물리확인) | — | 촬영 테이크 DONE |

**네 태그 모두 정면 15cm 서보 성립. 이동 도킹은 tag7/8/9 end-to-end DONE.**

---

## 10. 미해결 / 후속

- cx/cy·왜곡 미보정 → 태그 좌우(y)·yaw 정밀도 한계(체스보드 필요)
- tag10 등록 yaw 재등록(비스듬히) 또는 벽법선 사용
- Pi5 CPU 근본 저감(선택): detector rate↓ / smoother 제거 등 (배터리 충분하면 불필요)
- 콘솔 버튼(agent) 경로 end-to-end 촬영 (지금까지 CLI로 검증)

이 도킹 구조를 처음 두 단계(Nav2 접근 + AprilTag 저속 PID)로 나눈 배경과 초기 설계는
[Nav2로 가까이 가고, AprilTag PID로 정확히 멈추기](../nav2-apriltag-pid-정밀주차/)에 정리해 두었다.
