# 측위 근본원인 규명 + 함대 설정값 정리 (2026-07-10)

브랜치 `feat/overhead-pose-node`. 도메인 **50**. 맵 **`wasab_map11`**.
상세 경과는 `docs/worklog-2026-07-10-lidar-bias-and-preflight.md`.

---

## 0. 한 장 요약

오늘 **두 개의 근본원인**을 찾았다. 어제까지 "맵이 나쁘다"고 믿었던 두 현상의 정체다.

| 현상 | 어제까지의 진단 | **실제 원인** |
|---|---|---|
| 방향별 거리 오차 2~10 cm | `map5` 의 벽 위치가 틀렸다 | **`.31` 라이다가 모든 거리에 +8.5 cm 가산** (개체 불량) |
| 주행 중 AMCL 이 19 cm 밀림 | 맵 오차 / 회전이 AMCL 을 무너뜨림 | **`sigma_hit: 0.2`** (AMCL 이 19 cm 오차를 구분 못 함) |

두 원인 모두 **맵과 무관**했다. 어제 재-SLAM(`map11`)은 결과적으로 좋은 맵을 남겼지만,
그것을 하게 만든 진단은 **휘어 있는 자로 잰 값** 위에 서 있었다.

부수 성과: `.50`·`.44` 두 대를 라이다부터 검증해 함대에 투입(G0~G4).

---

## 1. ★★ 근본원인 1 — AMCL `sigma_hit`

### 1.1 증상
초기 pose 를 정확히 찍어도, **직진 주행만 하면 AMCL 이 한 축으로 ~19 cm 밀린다.**
정지 중에는 스스로 못 돌아오고, **제자리 회전을 하면 즉시 옳은 자리로 복귀**한다.

두 로봇에서 동일하게 재현됐다(같은 맵·같은 파라미터, 다른 휠 상수).
```
.87  2D Pose Estimate 직후  3.68 cm  →  20 cm 왕복 후  19.11 cm  →  좌 90° 회전 후  5.18 cm
.44  2D Pose Estimate 직후  3.19 cm  →  1.2 m 주행 후  27.07 cm  →  좌 90° 회전 후   3.61 cm
```
`.87` 은 왕복이라 **물리적으로 제자리 복귀**했고 odom 도 0.5 mm 였다. 그래도 AMCL 만 19 cm 어긋났다.

### 1.2 밀림 vs 편향을 가르는 법
주행 후 `.44` 의 방향별 오차(라이다 프레임):
```
0° +1.9    90° -18.3    180° -0.3    270° +20.1 cm
```
- **`90°` 와 `270°` 가 반대 부호** → pose 가 그 축으로 밀렸다
- 센서 편향이면 **네 방향 모두 같은 부호**로 부풀어야 한다 (`.31` 이 그랬다)

동시에 **마주보는 빔의 합(pose 불변량)** 으로 센서를 무죄 판정:
```
90°+270°   라이다 0.147 + 0.236 = 0.383 m      맵 0.330 + 0.035 = 0.365 m   → 1.8 cm
```
통로 폭은 맞다. **로봇만 그 안에서 밀려 있다고 AMCL 이 믿는다.**

### 1.3 원인
```yaml
laser_model_type: "likelihood_field"
sigma_hit: 0.2          # ← 20 cm
```
`likelihood_field` 모델은 각 빔 끝점이 **최근접 벽에서 벗어난 거리**를
표준편차 `sigma_hit` 의 가우시안으로 점수화한다.

> `sigma_hit = 0.2 m` = **"빔 끝점이 벽에서 20 cm 안이면 다 비슷하게 좋은 점수"**

관측된 오차가 **19 cm** — 정확히 그 허용폭 안이다.
AMCL 은 밀린 pose 와 옳은 pose 를 **구분할 수 없어서** odom 이 이끄는 대로 흘러갔다.

`update_min_d = 0.05` 이므로 1.2 m 주행 중 스캔 갱신은 20회 넘게 일어났다.
**갱신은 됐지만 가중치 차이가 없어 리샘플링이 아무것도 고르지 못했다.**

회전을 하면 각도 오차가 빔 끝점을 훨씬 크게 움직여 점수 차가 벌어진다 → 그제야 파티클이 몰린다.
**이것이 "회전이 AMCL 을 고친다"의 정체다.**

`0.2` 는 Nav2 기본값이고 **수십 미터짜리 실내**를 전제로 한다.
우리 아레나는 **1 × 2 m**. 20 cm 는 짧은 축의 **20 %** 다.

### 1.4 단일 변수 실험
`z_rand`, `z_hit`, `alpha*` 는 **일부러 건드리지 않았다.** 두 개를 동시에 바꾸면 귀속이 불가능하다.

| | `sigma_hit = 0.2` | `sigma_hit = 0.05` |
|---|---|---|
| 2D Pose Estimate 직후 | 3.19 cm | 2.92 cm |
| **1 m 주행 후** | **27.07 cm** | **4.10 cm** |
| 주행 후 방향별 | `-18.3 / +20.1` (밀림) | `+3.2 / +2.9` (**등방**) |

정지 확인(6초간 x 변동 0.02 mm) 후 재측정해도 4.10 cm 로 동일.
**부호가 모두 같아졌다** = 위치가 밀리지 않는다.

남은 4 cm 의 내역(추정): 라이다 편향 `+0.05 cm` + 격자 반 셀 `1 cm` + `map11` 자체 오차 `2.4 cm`.

### 1.5 파급
- **Nav2 접근 docking 의 선결 조건이었다.** 목표 20 cm 앞에서 자기 위치를 19 cm 틀리게 알면 벽을 친다
  (2026-07-09 에 실제로 그랬다).
- 어제 이 현상을 "맵의 벽 위치 오차"로 진단해 **재-SLAM 까지 했다.** 실제로는 파라미터 한 줄이었다.
- 함대 전체가 같은 값을 쓰고 있었다.

---

## 2. ★ 근본원인 2 — `.31` 라이다 상수 편향

### 2.1 측정법 — pose 불변량
마주보는 두 빔의 합은 로봇이 그 축 위 **어디에 있든 두 벽 사이 거리**다.
→ pose·odom·AMCL·맵이 **하나도 들어가지 않는다.** 정지 상태 스캔 한 장이면 된다.

도구: `scripts/verify_lidar_scale.py`

### 2.2 결과 (같은 아레나, 같은 모퉁이, 같은 코드)
| 로봇 | 긴 축 (실제 2.00 m) | 짧은 축 (실제 1.00 m) | 한쪽당 편향 |
|---|---|---|---|
| `.44` | 2.0010 | 0.9975 | **+0.05 / -0.13 cm** |
| `.87` | 2.0105 / 2.0120 | 1.0125 / 1.0130 | +0.6 cm |
| `.50` | 2.0145 | 1.0180 | +0.8 cm |
| `.31` | **2.1895** | **1.1875** | **+9.4 cm** |

### 2.3 가산 vs 비례 — 줄자 4점
합만으로는 구분할 수 없다(둘 다 합을 똑같이 설명). **빔 하나의 참값**이 필요하다.

| 벽 | 참값 | `.31` 스캔 | 차이 |
|---|---|---|---|
| 1 m 벽 (가까움) | 0.145 | 0.2290 | +8.4 cm |
| 2 m 벽 (가까움) | 0.170 | 0.2550 | +8.5 cm |
| 2 m 벽 (맞은편) | 0.830 | 0.9325 | +10.3 cm |
| 1 m 벽 (맞은편) | 1.855 | 1.9605 | +10.6 cm |

최소제곱: **`스캔 = 1.013 × 참값 + 0.0846`** → **상수 +8.5 cm 지배.** 비례 기각.

### 2.4 기각된 원인
- **`scan_mode`** — `DenseBoost` ≡ `Standard` (차이 1~2 mm)
- **휠 미보정** — 휠 상수는 엔코더→`/odom` 변환에만 들어간다. 측정 경로에 odom 이 없다
- **장착 오프셋** — 라이다를 옮겨도 마주보는 두 빔의 **합은 불변**. 합이 +19 cm 늘었다는 게 배제 근거
- **펌웨어/모델** — `.31`·`.50`·`.44` 모두 `FW 1.02 / HW Rev 18`. 세 대 중 `.31` 하나만 15배 어긋난다

→ **`.31` 개체의 거리 캘리브레이션 불량. 교체(또는 RMA).**
`health status: OK` 는 광학·모터 이상만 잡고 **거리 캘리브 오류는 못 잡는다.**

### 2.5 파급
어제 `map5` 를 "벽 위치가 방향마다 2~10 cm 어긋난다"고 판정한 것은 **`.31` 의 스캔으로** 내렸다.
그 자가 +8.5 cm 휘어 있었다. **그 판정은 재계산 대상이다.**
반면 `map11` 판정(평균 2.4 cm)은 `.87`(정상 라이다)로 쟀으므로 살아남는다.

---

## 3. 확정 설정값

### 3.1 AMCL (`nav2_params1.yaml` = 로봇의 `nav2_params_0709.yaml`)
```yaml
amcl:
  ros__parameters:
    alpha1: 0.2            # 2026-07-09 수정 (0.4 → 0.2). 1 m 직진 추적 -21.5% → -0.3%
    alpha2: 0.2
    alpha3: 0.2
    alpha4: 0.2
    alpha5: 0.2
    recovery_alpha_fast: 0.0   # 2026-07-09 수정 (0.1 → 0.0)
    recovery_alpha_slow: 0.0   # 2026-07-09 수정 (0.001 → 0.0)
    sigma_hit: 0.05        # ★ 2026-07-10 수정 (0.2 → 0.05). 주행 중 19 cm 밀림 해소
    laser_model_type: "likelihood_field"
    z_hit: 0.5             # 미변경
    z_rand: 0.5            # 미변경 (후보. 단일 변수 원칙으로 보류)
    laser_likelihood_max_dist: 2.0
    max_beams: 60
    min_particles: 1000
    max_particles: 2500
    update_min_d: 0.05
    update_min_a: 0.05
    base_frame_id: "base_footprint"
    odom_frame_id: "odom"
    global_frame_id: "map"
```

### 3.2 맵
```yaml
# wasab_map11.yaml   ← 채택본
image: wasab_map11.pgm
resolution: 0.020
origin: [-0.191, -0.207, 0]
occupied_thresh: 0.65
free_thresh: 0.196
mode: trinary
negate: 0
```
- 크기 105 × 62 px @ 0.02 m/cell
- 벽 bbox `x -0.191 ~ +1.889` (2.08 m), `y -0.207 ~ +1.013` (1.22 m)
- **긴 축 = x.** `map5`(긴 축 = y)와 **좌표계가 90° 다르다** → 옛 태그 좌표·웨이포인트·초기 pose 전부 무효
- 아레나 실측: 벽 안쪽 **1.00 m × 2.00 m**

### 3.3 휠 상수 (로봇별 — **복사 금지**)
| 로봇 | `wheel_radius` | `wheel_separation` | `B/r` | 검증 |
|---|---|---|---|---|
| `.87` | 0.0273 | 0.0976 | 3.575 | 직진 −0.15%, 회전 360° −0.06% |
| `.50` | 0.0279 | 0.1000 | 3.584 | 직진 +0.32%, 회전 720° −0.22% |
| `.44` | 0.0279 | 0.1000 | 3.584 | 직진 −0.35%, 회전 720° +0.08% |
| `.31` | 미측정 | 미측정 | — | 라이다 불량으로 보류 |

- `.50`·`.44` 는 같은 개체군, `.87` 만 2% 작다. **`B/r` 는 3.575~3.584 로 일치** → 형상은 같고 스케일만 다르다
- **`B` 는 개체별이다.** `r` 이 우연히 일치해도 복사하면 안 된다
- 값이 **6곳**에 흩어져 있다(`.31` 만 모듈 상수 1곳):
  ```
  src/pinky_pro/pinky_bringup/pinky_bringup/bringup.py           declare_parameter 기본값
  src/pinky_pro/pinky_bringup/launch/bringup_robot.launch.xml    <arg default>
  src/pinky_pro/pinky_bringup/config/pinky_params.yaml
  install/.../site-packages/pinky_bringup/bringup.py
  install/.../share/pinky_bringup/launch/bringup_robot.launch.xml
  install/.../share/pinky_bringup/config/pinky_params.yaml
  ```
  **우선순위**: 실행 인자 > launch `<arg default>` > `declare_parameter` 기본값.
  고친 뒤 반드시 `ros2 param get /pinky_bringup wheel_radius` 로 **로드된 값**을 확인.

### 3.4 라이다
```
모델      sllidar C1   (launch: sllidar_c1_launch.py)
포트      /dev/ttyAMA0   460800
scan_mode DenseBoost   (Standard 와 거리 동일 — 1~2 mm 차)
frame_id  rplidar_link,  angle_compensate: true
배너      FW 1.02 / HW Rev 18   (.31 / .50 / .44 동일)
```

### 3.5 네트워크 / DDS
```bash
# 로봇 (부팅마다 반복 — hostapd/dnsmasq 가 ap0 를 되살린다)
sudo systemctl stop hostapd dnsmasq
sudo ip link set ap0 down
sudo ip addr flush dev ap0

# 공통 헤더 (bringup/Nav2 는 ~/pinky_pro 만 source. ~/wasab 소싱 금지)
source /opt/ros/jazzy/setup.bash
source ~/pinky_pro/install/setup.bash
export ROS_DOMAIN_ID=50 ROS_STATIC_PEERS=192.168.0.29
```
- `.bashrc` 가 로봇 고유 도메인을 export 한다(`.44`=53, `.87`=52 …).
  **텔레옵 터미널도 `export ROS_DOMAIN_ID=50` 을 먼저** 해야 `/cmd_vel` 이 닿는다
- **두 로봇을 동시에 켜지 말 것.** `ros2 topic info /scan | grep "Publisher count"` → **1**

---

## 4. 절차

### 4.1 기동 순서
```bash
# [T1] bringup  (역순이면 /odom 부재로 amcl 이 죽는다)
ros2 launch pinky_bringup bringup_robot.launch.xml

# [T2] localization
ros2 launch pinky_navigation localization_launch.xml \
  map:=$HOME/wasab/wasab_navigation/map/wasab_map11.yaml \
  params_file:=$HOME/wasab/wasab_navigation/wasab_nav2/params/nav2_params_0709.yaml
```
**agent 는 띄우지 말 것** — 태그 자동 재측위가 옛 `map5` 좌표로 AMCL 을 덮어쓴다.

### 4.2 RViz
설정 파일 없이 `rviz2` 로 띄운다 (`nav2_view.rviz` 는 Nav2 미기동 시 세그폴트).
- Fixed Frame = `map`
- **Map** → `/map` → **Durability = `Transient Local`** (latched 이므로 기본 Volatile 로는 안 보인다)
- **LaserScan** → `/scan` (Best Effort), **TF**

### 4.3 검증 도구 (PC 에서 실행)
| 도구 | 용도 | 판정 |
|---|---|---|
| `scripts/verify_lidar_scale.py` | 라이다 거리 편향 (pose 불변량) | PASS ≤ 2 cm/side |
| `scripts/preflight_robot.sh` | bringup 전 ap0/휠 6곳/맵/AMCL | exit 0 |
| `scan_vs_map.py` (scratchpad) | AMCL pose 에서 맵 raycast vs `/scan` | 평균 \|오차\| < 4 cm |
| `rotation_drift.py` (scratchpad) | 제자리 회전 시 AMCL 병진 | odom 병진 ≈ 0 이 유효 조건 |

### 4.4 측정 규율 (오늘 값비싸게 배운 것)
1. **직진은 기록기를 쓰지 마라.** odom 위치는 절대값 → `정지 상태 읽기 → 주행 → 정지 상태 읽기`.
   연속 기록은 **회전에만** 필요(360° 돌면 시작·끝 yaw 가 같으므로 증분을 언랩해 적산해야 한다).
2. **"완료" 신호와 실제 정지는 다르다.** 이 기종은 **`cmd_vel` 워치독이 없어** 키를 떼도 계속 간다.
   읽기 전에 **정지를 데이터로 확인**하라(최근 1초 이동 < 0.5 mm 가 3회 연속).
3. **기록기를 PC 에서 돌리지 마라.** 무선 DDS 구간에서 유실된다(로봇 4822샘플 vs PC 128샘플).
4. **사용자가 측정 중이면 기록기를 끄지 마라. 읽기만 하라.**
5. **캘리브레이션 정밀도는 자의 정밀도를 못 넘는다.** 각도는 **2바퀴(720°)** 로 재라(정렬 오차 1/2 희석).
6. **원격에서 `pkill -f`/`pgrep -f` 금지.** 패턴이 `ssh 'bash -c ...'` 명령줄에 들어가 **자기 자신을 죽인다.**
   `ps -eo pid,cmd | grep <pat> | grep -v "bash -c" | grep -v grep` → PID 로 `kill`.
7. **관측자의 개입을 데이터로 착각하지 마라.** 측정 중 `2D Pose Estimate` 를 다시 찍지 말 것.

---

## 5. 남은 것

```
[ ] sigma_hit 0.05 를 .87 / .50 에도 배포 후 재검증
[ ] .87 + map5 로 회전 드리프트 한 판  → 맵 탓 vs 라이다 탓 분리
    (오늘 증명한 것은 ".87+map11 조합이 건강하다" 이지 "map11 > map5" 가 아니다)
[ ] 태그 detector +9 cm 편향 재검토 — .31 라이다 편향(+8.5 cm)과 크기가 거의 같다.
    태그 등록은 AMCL pose 기반이고 AMCL 은 편향된 스캔에 맞춰 밀려 앉았을 것
    → "카메라 intrinsic 이 먼저" 라는 어제 계획의 전제가 흔들린다
[ ] .31 라이다 교체. 그 전까지 측위·거리 실험 금지
[ ] .50 / .44 의 G5(회전 품질)
[ ] (선택) z_rand 0.5 → 0.2 단일 변수 실험
---- 여기까지가 측위 신뢰 확보 ----
[ ] map11 기준 태그 7/8/9/10 재등록 (auto_relocalize_enabled:=false 필수)
[ ] 웨이포인트 재작성 (map11 은 map5 와 축이 90° 다르다)
[ ] 콘솔 배경 맵 경로를 map11 로 갱신
[ ] Task 9 시나리오 1' (Nav2 접근 docking) 재시도
```

---

## 6. 오늘의 교훈

1. **자를 먼저 재고 물건을 재라.** 어제 "맵이 틀렸다"는 진단은 휘어 있는 라이다로 내린 것이었다.
2. **pose 불변량을 써라.** 마주보는 두 빔의 합은 pose 와 무관하다 → 센서 단독으로 유죄가 갈린다.
   방향별 오차표는 "pose 가 틀렸나 / 센서가 틀렸나"를 섞는다.
3. **부호를 읽어라.** 네 방향 같은 부호 = 센서 편향(등방). 마주보는 방향 반대 부호 = pose 밀림.
4. **잣대를 섞지 마라.** "끝점→최근접 벽" 은 벽을 관통한 빔을 벌하지 않는다. raycast 가 옳은 잣대다.
5. **단일 변수만 바꿔라.** `sigma_hit` 하나로 27 → 4 cm. 함께 바꿨으면 무엇이 효과인지 몰랐다.
6. **기본값은 그 도메인의 전제를 함께 가져온다.** Nav2 의 `sigma_hit: 0.2` 는 수십 m 실내용이다.
   우리 아레나는 1 × 2 m. **파라미터의 물리적 의미를 스케일에 대입해 보라.**
7. **사용자의 반론을 근거로 반박하라.** "휠 미보정 탓 아닌가"에 대해 "측정 경로에 odom 이 없다"를 보였다.
