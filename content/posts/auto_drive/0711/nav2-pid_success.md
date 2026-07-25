# Nav2 + PID 정밀 도킹 — 성공 기록 (시행착오·조치·최종 설정)

2026-07-11. 브랜치 `feat/overhead-pose-node`. 도메인 **50**. 맵 **wasab_map11**. 로봇 `.50`→(저배터리)→`.44`.

> **결과**: 콘솔 지휘용 Nav2 접근 → AprilTag PID **정면 15cm 정밀 도킹**을 4개 태그(7/8/9/10)에서 성립.
> tag8↔tag7↔tag9 이동 도킹 end-to-end DONE(물리 15cm 정지선 검증). 데모 촬영 성공.
> 관련 메모리: `precision-parking-status`, `robot-cpu-load-tuning`, `robot-camera-udp`.

---

## 0. 한 장 요약

| 항목 | 결론 |
|---|---|
| 서보 | **pose regulation**(ρ,α,β)로 diff-drive가 호를 그려 좌우 offset 제거 → 정면 15cm |
| yaw 안정화 | **YawFilter**(circular mean, window 6) — 평면 마커 ±flip 제거 |
| 정밀도 | ex ~6–12mm(15.x cm), ey <4mm, 4태그 물리 검증 |
| Nav2 flaky의 진범 | **저배터리** (6.9V/17% → controller 20→8Hz 기아 → ack timeout). .44 신선 배터리로 해결 |
| CPU 처방 | detector **NAV 구간 유휴**(153→26%) + **카메라 pre-warm**(cold-start 회피) |
| 데모 로봇 | **.44** 온보딩(.50 코드·태그·카메라값 그대로 배포, 재캘리브 불필요) |

---

## 1. 시행착오 → 조치 (시간순)

### 1.1 정면 15cm 서보 — 옛 P-제어의 구조적 한계
- **증상**: 옛 서보는 `|error_x|<tol_x`가 되면 `vx=0`. diff-drive는 제자리 회전만으론 **좌우 offset(error_y)을 병진으로 못 고침** → 좌우 3~5cm 잔차. (옛 메모의 "tol_y 0.04로 완화"는 이 한계 우회였음.)
- **오판정정**: "15cm에서 태그가 FOV에서 짤린다"를 **거리 한계로 오진** → 실제로는 **좌우 오차 탓**(비스듬히 접근해 태그가 화면 옆으로 이탈). 정면 접근하면 15cm에서도 태그 남음(사용자 지적이 옳았음).
- **조치**: `pid.py`를 **pose regulation**으로 교체. 목표 주차자세 `G = se2_compose(tag_base, inv(tag_goal))`를 극좌표로 추종:
  ```
  ρ = |G|,  heading = atan2(gy,gx),  reverse = |heading|>π/2
  α = heading(전진) 또는 normalize(heading-π)(후진),  β = normalize(gθ - α)
  v = k_rho·ρ (reverse면 -),  wz = k_alpha·α + k_beta·β,  clamp
  ρ<tol_x면 병진정지·최종 yaw 정렬만
  ```
  로봇이 **호를 그려 태그 법선 위로 올라타** ey→0, eyaw→0, ex→0(=15cm 정면).

### 1.2 eyaw 프레임마다 ±flip → wz 요동
- **증상**: dry-run에서 `eyaw +0.09/-0.09` 교대 → `wz -0.2/0` 요동. **평면 마커 pose ambiguity**(정면일수록 두 해가 비슷해 뒤집힘).
- **조치**: `pose_filter.py`에 **YawFilter**(최근 window개 yaw의 circular mean = atan2(Σsin,Σcos)) 추가. 노드 `_on_tag`에서 **x/y는 raw, yaw만 필터**. 대칭 flip이 ~0으로 수렴 → wz 안정.

### 1.3 dry-run 먼저 (모션 전 방향 검증)
- `cmd_vel_enabled:=false`로 서보 기동 → docking_state의 **계산 vx/wz 부호**를 읽어 방향·안정성 확인 후 실주행. (CPU 이슈는 실제 nav 돌려야 나오므로 dry-run으론 재현 안 됨.)

### 1.4 Nav2 이동 도킹 — 반복 nav_failed (긴 삽질)
증상: 이동 도킹의 Nav2 접근이 `nav_failed`로 자주 실패. 층층이 원인을 벗겨냄:
1. **cold-start**: dock.launch 첫 시도는 detector **카메라 init 스파이크**로 planner가 굶어 `compute_path ack timeout`(~1s). → **warm 재시도로 통과**(성공 런은 전부 warm).
2. **detector CPU**: UDP 스트리밍(매 프레임 JPEG 인코딩+송신)이 detector CPU **+40~85%p(153%)**. → **NAV 구간 detector 유휴 게이트**(아래 2.2)로 153→26%.
3. **스테일 프로세스**: 5.5분 생존한 옛 `precision_parking`이 **카메라 점유**(새 detector "Device busy")+CPU로 반복 방해. → `kill -9` 철저히.
4. **Nav2 재기동 여파**: nav2 재시작 직후 **costmap 미준비**("no valid path") + **TF cache 드롭**("timestamp earlier than transform cache") + **goal response send timeout**. → **재기동 후 충분히 정착 대기**(compute_path 타진 SUCCEEDED로 확인) 필요.
5. **파라미터 오조준**: "acknowledge goal request timeout"은 `wait_for_service_timeout`(서버 발견 대기)이 아니라 `default_server_timeout`(200ms, ack 대기)이 지배. `wait_for_service_timeout 4000` 시도는 무효 → **1000 원복**(검증 config 그대로).
6. **★ 진범 = 저배터리**: 위 처방들로 개선됐으나 잔여 실패 지속. `.50` **6.9V/17%**에서 controller loop **20→8Hz** 굶음이 근본. **`.44` 신선 배터리로 교체하니 nav 안정 완주.** (성공했던 초반 런들은 배터리가 더 높았음.)

### 1.5 tag10 — Nav2 이동 불가(구조적)
- tag10 접근점(0.5m standoff)이 **교무실 내벽 박스**에 2cm로 붙어 costmap inflation상 도달 불가. 위쪽 standoff 0.30 접근점(1.687,0.53)은 도달 가능하나 **등록 yaw ±13° 오차** + 30cm 근접으로 서보가 정렬 중 태그를 놓침(tag_lost).
- **조치**: tag10은 **PID+물리배치**(정면 30cm 수동 배치, nav_enabled:=false)로 DONE(ex7.6/ey1.7). 이동 도킹은 tag7/8/9만.

### 1.6 .44 온보딩 (데모 로봇 교체)
- `.50` 저배터리로 `.44`(신선)로 교체. **.50의 working 상태를 통째로 백업 후 배포**:
  - `.50`에서 `wasab_docking`(소스)+`wasab_robot_agent`+`~/.wasab/tag_map_poses.yaml`를 tar → PC `backups/from-50/from50_deploy.tgz`.
  - `.44`에 추출 + `map12` 복사 + `colcon build`(2 pkg).
- **★ .50 카메라값(fx588.6/camera_to_base.x0.023)이 .44에서도 15cm 정확** → **재캘리브 불필요**(개체차 무시 가능).

### 1.7 콘솔 카메라 안 뜸
- **원인**: `robots.yaml`의 로봇44에 `camera` 항목 없음 → 콘솔 `_camera_ip`=None → "카메라 없음".
- **조치**: `44: {..., camera: {port: 8090}}` 추가(port는 미사용, 항목 존재만 필요). **콘솔 재시작** 후 로봇44 선택 시 UDP 스트림 표시.

### 1.8 촬영 playbook (cold-start 회피)
- dock.launch 첫 시도는 cold-start로 nav_failed(정상). 촬영 테이크가 실패하지 않게:
  **재측위(tag8, median<2cm) → 카메라 pre-warm(detector 잠깐 standalone 기동→kill, libs 캐시, 로봇 안 움직임) → 촬영 시작 → dock**. → 첫 테이크 완주.

---

## 2. 조치 요약 (코드/설정 변경)

### 2.1 커밋됨 (9aaa79f, 2dddef2)
- `wasab_docking/wasab_docking/pid.py` — pose regulation `servo_cmd(errors, tag_goal, gains, limits, tols)` + 후진 재접근
- `wasab_docking/wasab_docking/pose_filter.py` — `YawFilter`(circular mean)
- `wasab_docking/wasab_docking/precision_parking_node.py` — YawFilter 배선(yaw만 필터, 전이 reset) + pose-reg gains
- `wasab_docking/wasab_docking/state_machine.py` — servo_cmd에 tag_goal 전달
- `wasab_docking/config/precision_parking.yaml` — tag_goal_x 0.15, k_rho/k_alpha/k_beta
- `wasab_gui/udp_camera_worker.py` + `console_app.py` — UDP JPEG 수신 워커(로봇 IP 필터) → front 패널

### 2.2 미커밋 (작업트리/로봇 배포됨)
- `wasab_docking/wasab_docking/apriltag_detector_node.py` — **UDP 컬러 송출** + **NAV 구간 유휴 게이트**(docking_state 구독, `state in {NAV_TO_APPROACH, NAV_CANCELING}`면 검출·인코딩·송신 skip, 프레임만 버림). picamera2 "RGB888"=실제 BGR라 변환 없이 imencode.
- `wasab_docking/launch/dock.launch.py` — `tag_goal_x` 기본 0.25→**0.15**(콘솔/agent 도킹 기본)
- `wasab_gui/map_view.py` — `MAP_ROT_CW` 90→**0**(map11 가로 긴축 표시) + `tests/test_map_view.py`(monkeypatch로 회전 90 고정 검증)
- `wasab_gui/config/robots.yaml` — 로봇44 `camera:{port:8090}`
- `nav2_params_0709.yaml` `wait_for_service_timeout` — 4000 시도했다 **1000 원복(순변경 없음)**

### 2.3 백업
- 로봇(.50) 소스 백업: `~/backups/wasab_docking.pre-posereg-*`, `~/backups/wasab_docking.pre-navidle-*`
- PC: `backups/wasab_gui.pre-udpcam-*`, `backups/from-50/from50_deploy.tgz`, `backups/from-50/tag_map_poses.yaml`

---

## 3. 최종 설정값 (확정 — 변경 금지)

### 3.1 `wasab_docking/config/precision_parking.yaml`
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
yaw_filter_window: 6         # (default) eyaw circular-mean
settle_time_s: 0.4 ; settle_min_frames: 5
overall_timeout_s: 45.0 ; tag_lost_timeout_s: 0.5 ; search_timeout_s: 10.0
control_rate_hz: 20.0
```

### 3.2 `nav2_params_0709.yaml` (AMCL/BT 핵심)
```yaml
amcl: alpha1~5: 0.2 ; recovery_alpha_fast/slow: 0.0 ; sigma_hit: 0.05   # ★주행중 밀림 해소
      laser_model_type: likelihood_field ; z_hit 0.5 ; z_rand 0.5
      min_particles 1000 ; max_particles 2500 ; update_min_d/a 0.05
bt_navigator: wait_for_service_timeout: 1000 ; default_server_timeout: 200
              transform_tolerance: 1.0 ; bt_loop_duration: 10
controller_server: controller_frequency: 20.0
# global_costmap inflation_radius 0.06 (inscribed 0.07보다 작다는 경고 있으나 좁은 아레나용 의도)
```

### 3.3 휠 캘리브 (bringup, 개체별)
```
.44 / .50 : wheel_radius 0.0279, wheel_separation 0.1000
.87       : 0.0273 / 0.0976
```

---

## 4. 운영 절차 (재현용)

### 4.1 스택 기동 (.44, 도메인 50)
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
# (콘솔 도킹 쓰려면 agent도: ~/wasab/scripts/start_agent.sh --console-domain 50)
```

### 4.2 재측위 (tag8 예, 도킹15cm pose)
```bash
ros2 topic pub -r 4 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
"{header:{frame_id: map}, pose:{pose:{position:{x: -0.031, y: 0.021}, \
 orientation:{z: -0.6755, w: 0.7373}}, covariance:[0.1,0,0,0,0,0, 0,0.1,0,0,0,0, \
 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0.05]}}"
# scan_vs_map.py로 median<2cm 확인 (PC scratchpad)
```

### 4.3 카메라 pre-warm (촬영 전, 로봇 안 움직임)
```bash
ros2 run wasab_docking apriltag_detector --ros-args \
  --params-file ~/wasab/install/wasab_docking/share/wasab_docking/config/precision_parking.yaml -p tag_id:=9
# "apriltag_detector: tag_id" 로그 뜨면(카메라 init OK) kill -9
```

### 4.4 CLI 이동 도킹
```bash
ros2 launch wasab_docking dock.launch.py tag_id:=N \
  approach_pose_x:=<AX> approach_pose_y:=<AY> approach_pose_yaw:=<AYAW> \
  nav_enabled:=true cmd_vel_enabled:=true tag_goal_x:=0.15
# 첫 시도 cold-start nav_failed 시 kill 후 즉시 재시도(warm)
```
**접근점(standoff 0.5m)·재측위 pose(15cm)**:
| tag | 접근점 (AX, AY, AYAW) | 재측위 pose(15cm) |
|---|---|---|
| 8 | (-0.062, 0.370, -1.4832=-85°) | (-0.031, 0.021, -85°) |
| 7 | (-0.046, 0.350, +1.4595=+83.6°) | (-0.007, 0.698, +83.6°) |
| 9 | (1.335, -0.051, +0.1083=+6.2°) | (1.683, -0.013, +6.2°) |
| 10 | (1.730, 0.527, +1.5708=+90° 벽법선) | — (등록yaw 81.9°는 15° 오차; PID+물리배치 권장) |

### 4.5 촬영 순서
재측위(median<2cm) → pre-warm → **촬영 시작** → dock.launch → NAV(카메라 OFF)→서보(콘솔 카메라 ON)→DONE.

---

## 5. 검증 결과 (물리 15cm 확인)

| 런 | 로봇 | done_error_x | done_error_y | 비고 |
|---|---|---|---|---|
| tag8 (Nav2+PID) | .50 | 2.4mm (15.24cm) | 3.4mm | |
| tag7 (Nav2+PID) | .50 | 12mm | 2.5mm | tag8→tag7 |
| tag9 (Nav2+PID) | .50 | 6.6mm | 0.4mm | tag7→tag9 (1.5m, 07-09 실패거리) |
| tag10 (PID+물리) | .50 | 7.6mm | 1.7mm | Nav2 이동 불가(박스) |
| tag9 (Nav2+PID) | .44 | ~15cm(물리확인) | — | 촬영 테이크 DONE |

**네 태그 모두 정면 15cm 서보 성립. 이동 도킹은 tag7/8/9 end-to-end DONE.**

---

## 6. 미해결/후속

- [ ] 미커밋 오후 변경분 커밋 (2.2 목록)
- [ ] cx/cy·왜곡 미보정 → 태그 좌우(y)·yaw 정밀도 한계(체스보드 필요)
- [ ] tag10 등록 yaw 재등록(비스듬히) 또는 벽법선 사용
- [ ] Pi5 CPU 근본 저감(선택): detector rate↓ / smoother 제거 등 (배터리 충분하면 불필요)
- [ ] 콘솔 버튼(agent) 경로 end-to-end 촬영 (지금까지 CLI로 검증)
- [ ] .87/.31에 tag_map_poses·docking 배포(필요 시), .50 충전
