# 신규 로봇 투입 체크리스트 (`.50` / `.44` → `.87` 과 동일 상태로)

작성 2026-07-10. 근거: `docs/worklog-2026-07-10-lidar-bias-and-preflight.md`, `-07-09-night-odom-calibration-and-remap.md`

**순서를 지킬 것.** 각 게이트는 앞 게이트가 통과해야 의미가 있다.
아래 순서는 2026-07-10 하루를 태운 순서를 거꾸로 뒤집은 것이다 — 그날 우리는
맵과 odom 을 의심하다가 **반나절 뒤에야 라이다가 휘어 있음**을 발견했다.

```
G0 네트워크·DDS  →  G1 라이다(자)  →  G2 휠(odom)  →  G3 파일·파라미터  →  G4 측위  →  G5 회전 품질
```

---

## G0. 네트워크 / DDS

```bash
# PC(.29) 에서
ping -c2 192.168.0.<ID>
ssh pinky@192.168.0.<ID> 'hostname -I; uptime'
```

### `ap0` 내리기 — 재부팅마다 부활한다
`ip link set ap0 down` **만으로는 부족하다.** `hostapd`·`dnsmasq` 가 되살린다.

```bash
# 로봇에서
sudo systemctl stop hostapd dnsmasq
sudo ip link set ap0 down
sudo ip addr flush dev ap0
ip -4 addr show ap0        # 빈 출력이면 성공
```

**왜**: `ap0`(192.168.4.1)가 살아 있으면 DDS 가 그 인터페이스의 locator 를 광고해
PC 가 로봇 노드를 못 본다. 로봇의 AP 핫스팟이 필요하면 대신 DDS 화이트리스트를 쓴다
(`docs/dds-discovery-multihoming-known-issue-2026-07-07.md`).

### 공통 헤더 (모든 로봇 터미널)
```bash
source /opt/ros/jazzy/setup.bash
source ~/pinky_pro/install/setup.bash      # bringup/Nav2 는 ~/wasab 을 source 하지 말 것
export ROS_DOMAIN_ID=50 ROS_STATIC_PEERS=192.168.0.29
```
PC 쪽: `export ROS_DOMAIN_ID=50 ROS_STATIC_PEERS=192.168.0.<ID>`

> ⚠ **두 로봇을 동시에 켜지 말 것.** 같은 도메인에서 `/scan`, `/odom` 을 같은 이름으로
> 발행한다. 새 로봇을 올리기 전에 이전 로봇의 노드가 0개인지 확인:
> `ros2 topic info /scan | grep "Publisher count"` → **1**

---

## G1. 라이다 검증 — ★ 가장 먼저, 반드시

**자를 먼저 재고 물건을 잰다.** 라이다가 휘어 있으면 맵·AMCL·태그 좌표가 전부 오염되고,
그 사실은 며칠 뒤에야 드러난다.

```bash
# 로봇에 bringup 만 띄우고 (아래 G3 의 launch), 아레나에 놓은 뒤 PC 에서:
python3 scripts/verify_lidar_scale.py            # 기본 축1=2.00 m, 축2=1.00 m
```

배치: **칸막이가 두 축 어느 쪽도 가리지 않는 자리.** 모퉁이도 괜찮다
(마주보는 두 빔의 합은 로봇이 축 위 어디에 있든 두 벽 사이 거리다 — pose 불변량).

| 출력 | 뜻 | 조치 |
|---|---|---|
| `LIDAR PASS` (exit 0) | 한쪽당 편향 ≤ 2 cm | G2 로 |
| `PLACEMENT FAIL` (exit 2) | 합이 실제보다 **짧다** = 빔이 막힘 | 자리를 옮겨 재실행 |
| `LIDAR FAIL` (exit 1) | 합이 실제보다 **길다** = 거리 과대보고 | **이 로봇 쓰지 말 것** |

기준값 (2026-07-10 실측, 같은 아레나·같은 코드):
```
.87   축1 2.0105 / 축2 1.0125   →  +0.6 cm/side    정상
.31   축1 2.1895 / 축2 1.1875   →  +9.4 cm/side    불량 (상수 +8.5 cm 가산)
```

`LIDAR FAIL` 이면 `scan_mode` 를 바꿔도 소용없다(`.31` 에서 `DenseBoost` ≡ `Standard` 확인).
장치 배너(`sllidar_node` 기동 로그의 S/N·Firmware·Hardware Rev)를 `.87` 과 대조하고 교체를 검토한다.

---

## G2. 휠 캘리브레이션 — 로봇마다 반드시 실측

> **다른 로봇의 값을 복사하지 말 것.** `.87` 의 `wheel_separation = 0.0976` 은
> 그 로봇의 360° 회전 시험에서 역산한 값이다. `.31` 은 잰 적이 없다.
> 유효 구름반경 `r` 은 두 로봇에서 우연히 0.0273 으로 일치했지만, `B` 는 개체마다 다르다.

odom 은 상수가 **둘**(`r`, `B`)이므로 시험도 **둘**(직진, 회전) 필요하다.
직진만 재고 넘어가면 SLAM 이 전단(shear)된다 — 2026-07-09 에 겪었다.

### 도구 배포 (`.87` 에서 복사)
```bash
scp pinky@192.168.0.87:~/odom_trace.py pinky@192.168.0.87:~/yaw_trace.py /tmp/
scp /tmp/odom_trace.py /tmp/yaw_trace.py pinky@192.168.0.<ID>:~/
```

### 측정
```bash
# 1) 직진: 줄자로 정확히 1.000 m 텔레옵 주행 (손으로 밀지 말 것 — 모터가 바퀴를 잠가 odom 이 0)
python3 ~/odom_trace.py            # odom 직선거리 D 를 읽는다

# 2) 회전: 제자리 360° 텔레옵 (병진이 섞이면 무효)
python3 ~/yaw_trace.py             # 누적 회전각 A, 병진량을 읽는다
```

### 연립으로 푼다
odom 거리 ∝ `r`,  odom 각도 ∝ `r / B`. 현재 설정값을 `r_cfg`, `B_cfg` 라 하면:
```
r_true = r_cfg × (1.000 / D)
B_true = B_cfg × (A / 360) × (1.000 / D)      # = B_cfg × (A/360) ÷ (D/1.000) 의 역
```
2026-07-09 `.87` 실적:
```
직진 1.000 m → odom 1.0238 (+2.4 %)     회전 360° → odom 374.13° (+3.9 %)
r 0.028 → 0.0273     B 0.0961 → 0.0976
재검증: 직진 -0.15 %,  회전 -0.06 %
```
**기하학적 반경 ≠ 유효 구름반경.** 자로 잰 지름 56 mm(→ r=0.028)라도 하중받은 타이어는 눌린다.

### 적용 — 파일이 몇 곳인지부터 확인
로봇마다 다르다. **`.87` 은 6곳, `.31` 은 1곳**이다.
```bash
grep -rl "wheel_radius\|WHEEL_RAD" ~/pinky_pro | grep -v "/build/\|/log/"
```
- `declare_parameter` 방식(`.87`): `src`/`install` × (`bringup.py`, `launch.xml`, `params.yaml`) = 6곳.
  **우선순위**: 실행 인자 > launch `<arg default>` > `declare_parameter` 기본값.
  `bringup.py` 만 고치면 값이 안 바뀐다.
- 모듈 상수 방식(`.31`): `bringup.py` 의 `WHEEL_RAD`, `WHEEL_BASE` 한 곳.

수정 전 백업: `cp <file> ~/backups/<name>.pre-cal-$(date +%Y%m%d-%H%M%S)`

### 표에 기록
`scripts/preflight_robot.sh` 의 로봇별 표에 실측값을 넣는다. 넣기 전까지 `UNMEASURED` 로 두면
preflight 가 **자동으로 bringup 을 막는다**(의도된 동작).
```bash
case "$ROBOT" in
  87) EXP_R="0.0273"; EXP_B="0.0976" ;;
  50) EXP_R="?";      EXP_B="?" ;;      # ← 실측 후 채울 것
```

> ⚠ preflight 의 휠 점검은 `wheel_radius` 문자열을 찾는다. **모듈 상수(`WHEEL_RAD`) 방식
> 로봇은 못 읽는다.** 그런 로봇을 표에 넣을 때는 `extract()` 도 함께 고쳐야 한다.

---

## G3. 파일·파라미터 배포

```bash
# PC 에서
scp wasab_navigation/map/wasab_map11.{pgm,yaml} pinky@192.168.0.<ID>:~/wasab/wasab_navigation/map/
scp scripts/preflight_robot.sh scripts/verify_lidar_scale.py pinky@192.168.0.<ID>:~/wasab/scripts/
ssh pinky@192.168.0.<ID> 'chmod +x ~/wasab/scripts/preflight_robot.sh ~/wasab/scripts/verify_lidar_scale.py'
ssh pinky@192.168.0.<ID> 'md5sum ~/wasab/wasab_navigation/map/wasab_map11.*'   # PC 와 대조
```
`nav2_params_0709.yaml` 이 없으면 함께 복사 (`alpha1~5 = 0.2`, `recovery_alpha_* = 0.0`).

### preflight — bringup 직전 자동 점검

**검증만 하고 아무것도 고치지 않는다.** 하나라도 실패하면 `exit 1`.

```bash
ssh pinky@192.168.0.<ID> '~/wasab/scripts/preflight_robot.sh'
```

| 점검 | 무엇을 보는가 | 실패 시 근거 |
|---|---|---|
| `[ap0]` | `ap0` 에 IPv4 주소가 남았는가 | 재부팅마다 부활. DDS 가 잘못된 locator 를 광고 |
| `[wheel]` | 캘리브값이 **모든 파일에서** 일치하는가 | `.87` 은 `src`/`install` × 3파일 = 6곳 |
| `[map]` | 맵 파일이 있는가 | — |
| `[amcl]` | `alpha1~5 = 0.2`, `recovery_alpha_* = 0.0` | `alpha 0.4` + recovery 활성 → 1 m 직진 AMCL 추적 **−21.5 %** (2026-07-09) |

옵션:
```
--robot <id>          로봇 id. 기본: wlan0 IP 마지막 옥텟에서 자동 추출
--map <name>          기대 맵 이름(확장자 없이). 기본 wasab_map11
--params <path>       AMCL 파라미터 파일. 기본 nav2_params_0709.yaml
--allow-uncalibrated  휠 미측정을 실패 → 경고로 낮춘다
-h, --help
```

종료 코드: **0 = PASS(bringup 가능)**, **1 = FAIL(bringup 하지 말 것)**

출력 예 (`.87`, 2026-07-10 실기):
```
[ap0]
        DOWN / no inet                      OK
[wheel] robot=.87  expect r=0.0273 B=0.0976
        src/.../bringup.py                  0.0273/0.0976  OK
        ... (6곳 전부)
[map]
        wasab_map11.yaml                    OK
[amcl]  nav2_params_0709.yaml
        alpha1~5=0.2  recovery=0.0          OK
PREFLIGHT PASS — bringup 가능
```

미측정 로봇(`.31`, `.44`, `.50`)은 이렇게 **막힌다**:
```
[wheel] robot=.31  expect r=0.0273 B=UNMEASURED
        이 로봇의 휠 상수가 실측되지 않았다. 남의 로봇 값을 쓰지 말 것.
        먼저: ~/odom_trace.py (직진 1m → r), ~/yaw_trace.py (제자리 360° → B)
PREFLIGHT FAIL — bringup 하지 말 것
```

#### `--allow-uncalibrated` 는 언제 쓰나
**통제된 측정에서만.** 변수를 하나만 바꾸려고 일부러 캘리브레이션을 생략할 때다.
예: 2026-07-10 에 `.31` 의 휠을 미보정으로 둔 채 맵만 `map5 → map11` 로 바꿔
"차이 = 순수한 맵 효과" 를 보려 했다. 지금 캘리브레이션하면 odom·맵이 동시에 바뀌어
원인 분리가 불가능해진다.

플래그의 목적은 **의도를 코드에 남기는 것**이다. 규칙을 조용히 우회하는 대신
"이 판은 미보정으로 돌렸다" 가 출력과 로그에 남는다.

> **실전 운용에는 쓰지 말 것.** odom 오차가 그대로 주행에 실린다.

### 기동 (순서 중요 — 역순이면 `/odom` 부재로 amcl 이 죽는다)
```bash
# [T1] bringup
ros2 launch pinky_bringup bringup_robot.launch.xml

# [T2] localization
ros2 launch pinky_navigation localization_launch.xml \
  map:=$HOME/wasab/wasab_navigation/map/wasab_map11.yaml \
  params_file:=$HOME/wasab/wasab_navigation/wasab_nav2/params/nav2_params_0709.yaml
```

### PC 에서 확인
```bash
ros2 topic info /scan | grep "Publisher count"     # 1
ros2 topic hz /odom                                # ~30 Hz
ros2 topic hz /scan                                # ~10 Hz
ros2 param get /pinky_bringup wheel_radius         # 실측값. "Parameter not set" 이면 모듈 상수 방식
ros2 topic echo /battery/voltage --once            # 7.0 V 이상 권장
```

---

## G4. 측위 — 초기 pose 와 검증

`map11` 은 `map5` 와 **좌표축이 90° 다르다**(긴 축이 x). 옛 태그 좌표·웨이포인트·초기 pose 는 무효다.

> **agent 를 띄우지 말 것.** 태그 자동 재측위가 옛 `map5` 좌표로 AMCL 을 덮어써서
> 측정을 오염시킨다(`auto_relocalize_enabled`).

```bash
# PC — 설정 파일 없이. nav2_view.rviz 는 Nav2 미기동 시 세그폴트한다
rviz2
#   Fixed Frame = map,  Map(/map, Durability=Transient Local) + LaserScan(/scan) + TF 수동 추가
#   2D Pose Estimate 로 로봇의 실제 위치·방향을 찍는다
```

검증 (scratchpad 도구, 미커밋):
```bash
python3 scan_vs_map.py      # AMCL pose 에서 맵 raycast vs /scan
```
| 평균 \|오차\| | 판정 |
|---|---|
| < 4 cm | 통과. G5 로 |
| 4~10 cm | 덜 수렴. 살짝 주행 후 재확인 |
| > 10 cm | pose 가 틀렸거나 **라이다 편향**(G1 을 건너뛰지 않았는지 확인) |

**주의**: `2D Pose Estimate` 를 찍은 뒤 측정 중에 **다시 찍지 말 것.**
정지 중 AMCL 이 움직였다면 그건 결함이 아니라 사람이 다시 찍은 것이다(2026-07-10 에 착각했다).

---

## G5. 회전 품질 (선택 — 맵 검증이 목적일 때)

```bash
python3 rotation_drift.py     # 정지 2초 → 기준점 자동 확정
# 제자리 좌 90° → 우 90° → 정지
```
유효 조건: **`odom 병진 ≈ 0`** (바퀴가 안 미끄러졌다). 순 회전각 0 은 어제 절차와의 비교용일 뿐이다.

기준값:
```
.87 + map11, pose 수렴 상태   AMCL 병진 1.86 cm     ← 정상
.31 + map5,  편향 라이다      AMCL 병진 11~12 cm    ← 자가 휘어 있었다
```

---

## 부록 A. 배터리

- **전원을 끄고 충전할 것.** 켠 채로는 RPi5 + 라이다 + bringup 이 1.5~2 A 를 먹어
  충전기 전류를 넘어서면 **순 방전**이 된다(2026-07-10: 한 시간에 +0.08 V).
- 측정 시작 전 **7.0 V 이상**. 6.4 V 아래로 내려가면 중단.
- `/battery/percent` 는 셀 구성·컷오프 가정을 확인하지 않았다. **전압을 믿을 것.**

## 부록 B. 안전

- **pinky base 에 `cmd_vel` 워치독이 없다.** Dynamixel 속도모드가 마지막 RPM 을 유지하므로
  **발행자를 죽여도 로봇은 안 선다.** 정지 경로를 확보하기 전에는 고장주입 테스트 금지.
- 손으로 옮기면 odom 이 0 이다(모터가 속도 0 토크로 바퀴를 잠근다). 측정·태그등록은 **텔레옵 주행**으로.

## 부록 C. 게이트별 근거 (왜 이 순서인가)

| 게이트 | 건너뛰면 | 실제 사례 |
|---|---|---|
| G1 라이다 | 맵·odom·AMCL·태그 좌표가 전부 오염. 원인 추적에 반나절+ | 2026-07-10 `.31` (+8.5 cm) |
| G2 휠 | SLAM 전단·이중 벽. 회전 시험 무효 | 2026-07-09 `.87` (회전 +3.9 %) |
| G3 파일 | 옛 맵·옛 파라미터로 기동. `alpha 0.4` → 직진 추적 −21.5 % | 2026-07-09 `.31` |
| G4 측위 | 회전 시험이 "클릭 정확도" 를 재게 됨 | 2026-07-10 |
