---
title: "카메라 없이 도킹하기 — 2D 라이다로 V홈을 찾아 2 cm 까지"
date: 2026-08-08
slug: 카메라없이-2d라이다-v홈-도킹
tags: ["auto-drive", "lidar", "docking", "ros2", "laserscan", "line-fitting", "split-and-merge", "tf2", "qos", "precision-parking", "amcl", "wasab"]
categories: ["robotics"]
summary: "카메라가 고장 나 AprilTag 도킹을 못 쓰게 됐다. 라이다는 멀쩡했다. 벽에 붙은 끼인각 120° V홈을 2D 라이다로 찾아 도킹했고, 6회 전부 성공해 최종 간격 2 cm·횡편차 1 mm 이내가 나왔다. 핵심은 꼭짓점을 '모서리에 찍힌 점'이 아니라 두 변의 직선 피팅 교점으로 구한 것(σ 0.33 vs 2.3 mm), 그리고 기존 제어부가 카메라에서 받던 메시지를 그대로 흉내 내 제어 코드를 한 줄도 고치지 않은 것이다."
draft: false
ShowToc: true
TocOpen: true
---

로봇 도킹의 표준 해법은 시각 마커다. AprilTag 를 벽에 붙이고, 카메라로 찍고, `solvePnP` 로 자세를 풀면 된다. 우리도 그렇게 만들어 [정면 15 cm 정밀 주차](/posts/auto_drive/nav2-apriltag-pid-정밀주차/)까지 완성해 두었다.

그런데 카메라가 고장 났다.

```text
dmesg: ov5647 10-0036: ov5647_read: i2c read error, reg: 300a = -5
       ov5647: probe of 10-0036 failed with error -5
→ libcamera 인식 카메라 0개
```

센서 칩과 I2C 통신 자체가 끊긴 상태다. 리본 케이블을 다시 꽂기 전까지 이 로봇은 도킹을 못 한다. 그런데 **라이다는 멀쩡하다.** 그러면 라이다만으로 도킹할 수는 없을까?

결론부터 적으면, 됐다. **2D 라이다만으로 6회 도킹해 전부 성공했고, 최종 실물 간격 2 cm, 횡편차 1 mm 이내다.** 그리고 제어 코드는 한 줄도 고치지 않았다.

---

## 1. 무엇을 랜드마크로 삼을 것인가

### 1-1. 2D 라이다가 주는 것

2D 라이다는 한 평면을 훑어 **거리 배열 하나**를 준다. 우리 것은 720개 빔, 10 Hz 다.

```text
ranges[0..719],  angle_min = -π,  angle_increment = 0.0087 rad
```

각 빔을 극좌표에서 직교로 바꾸면 **점 구름**이 된다. 코드로는 이게 전부다.

```python
def scan_to_points(ranges, angle_min, angle_increment, range_min, range_max):
    """LaserScan.ranges → [(x, y, r, index)]. inf/nan/범위 밖 빔은 버린다."""
    pts = []
    for i, r in enumerate(ranges):
        if r is None:
            continue
        r = float(r)
        if not math.isfinite(r) or not (range_min < r < range_max):
            continue
        a = angle_min + i * angle_increment
        pts.append((r * math.cos(a), r * math.sin(a), r, i))
    return pts
```

`index` 를 함께 들고 다니는 게 뒤에서 쓸모가 있다. 빔 번호가 건너뛰었다는 것은 그 사이에 측정 실패가 있었다는 뜻이고, 그것도 물체가 끊긴 단서다.

색도, 질감도, ID 도 없다. 카메라가 "저건 8번 태그다"라고 말해 주는 것과 달리, 라이다는 "여기 뭔가 있다"만 말한다. 그래서 랜드마크로 쓰려면 **형상 자체가 식별자**가 되어야 한다.

### 1-2. V홈 — 각도가 곧 이름이다

우리가 고른 것은 끼인각 120°, 변 170 mm 의 **V홈**이다. 벽에 붙은 평범한 구조물이지만 라이다 입장에서는 훌륭한 표적이다. 이유는 세 가지다.

**① 각도는 거리와 무관하다.** 1 m 에서 보든 30 cm 에서 보든 120° 는 120° 다. 크기 기반 판정과 달리 거리 보정이 필요 없다.

**② 주변에 흔치 않다.** 방 안의 모서리는 대개 90° 다. 120°±20° 창을 두면 벽 모서리는 걸러진다.

**③ 두 변이 만나므로 점 하나를 특정할 수 있다.** 평평한 벽은 "어디쯤"만 알 수 있지만, 꺾인 곳은 **한 점**이 나온다. 뒤에 나오지만 이게 정밀도의 핵심이다.

---

## 2. 점 구름에서 V홈을 꺼내기

### 2-1. 끊고, 펴고, 짝짓는다

{{< figure src="/images/diagrams/autodrive-vgroove-pipeline.svg" alt="2D 라이다 스캔을 클러스터링·직선분해·쌍찾기·자세산출 네 단계로 처리해 V홈 자세를 PoseStamped 로 발행하는 파이프라인" >}}

②의 split-and-merge 는 재귀적이다. 점 뭉치에 직선을 맞추고, **가장 많이 벗어난 점**의 잔차가 허용치(6 mm)를 넘으면 그 점에서 둘로 쪼갠다. 쪼갠 조각에 같은 짓을 반복한다.

```python
def _split(pts, tol, depth=0):
    """최대 잔차가 tol 을 넘으면 그 점에서 쪼갠다 (split-and-merge)."""
    if len(pts) < 8 or depth > 6:
        return [pts]
    fl = fit_line(pts)
    if fl["maxres"] <= tol:
        return [pts]
    k = max(range(len(pts)),
            key=lambda i: abs((pts[i][0] - fl["mx"]) * fl["nv"][0]
                              + (pts[i][1] - fl["my"]) * fl["nv"][1]))
    if k < 4 or k > len(pts) - 4:
        return [pts]
    return _split(pts[:k + 1], tol, depth + 1) + _split(pts[k:], tol, depth + 1)
```

`depth > 6` 과 `k < 4` 가 안전장치다. 노이즈가 심하면 무한히 쪼개려 들기 때문에 깊이를 막고, 끝에서 4점 이내로는 자르지 않는다 — 조각이 너무 짧으면 직선 피팅 자체가 의미를 잃는다.

직선 피팅은 **전최소자승**(total least squares)이다. 일반 최소자승은 수직선을 못 맞추는데, 라이다 점은 어느 방향으로든 놓이므로 그러면 곤란하다.

```python
sxx = sum((p[0] - mx) ** 2 for p in pts)
syy = sum((p[1] - my) ** 2 for p in pts)
sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
th  = 0.5 * math.atan2(2 * sxy, sxx - syy)      # 주축 방향
d   = (math.cos(th), math.sin(th))              # 직선 방향
nv  = (-d[1], d[0])                             # 법선 → 잔차 계산용
```

클러스터링 임계는 고정값이면 안 된다. 라이다는 **먼 곳일수록 점 간격이 벌어지기** 때문이다.

```python
for a, b in zip(pts, pts[1:]):
    gap = math.hypot(b[0] - a[0], b[1] - a[1])
    # 거리에 비례한 적응 임계 — 먼 벽이 점 간격만으로 쪼개지지 않게
    thr = max(0.02, 3.0 * b[2] * angle_increment)
    if b[3] - a[3] > 2 or gap > thr:
        clusters.append(cur); cur = [b]
    else:
        cur.append(b)
```

3 m 벽의 점 간격은 26 mm 인데 고정 20 mm 임계를 쓰면 멀쩡한 벽이 산산조각 난다. `b[3] - a[3] > 2` 는 빔 번호가 건너뛴 경우 — 그 사이 빔이 아무것도 못 맞혔다는 뜻이라 물체가 끊긴 것으로 본다.

### 2-2. 꼭짓점은 점을 찍는 게 아니라 직선을 연장해 만든다

가장 중요한 설계 판단이 여기 있다. **V홈의 꼭짓점을 "모서리에 찍힌 점"에서 구하지 않았다.** 대신 **두 변의 직선을 각각 피팅한 뒤 그 교점**을 계산했다.

쌍을 고르는 조건부터 보면 이렇다.

```python
for i in range(len(segs)):
    for j in range(i + 1, len(segs)):
        a, b = segs[i], segs[j]
        if not (arm[0] <= a["length"] <= arm[1] and arm[0] <= b["length"] <= arm[1]):
            continue                                   # 팔 길이 8~30 cm
        diff = abs(a["ang"] - b["ang"])
        inc = 180 - min(diff, 180 - diff)
        if abs(inc - nominal) > span:
            continue                                   # 120° ±20°
        d = min(math.hypot(pa[0] - pb[0], pa[1] - pb[1])
                for pa in (a["p0"], a["p1"]) for pb in (b["p0"], b["p1"]))
        if d > joint:
            continue                                   # 두 끝점이 5 cm 이내로 만나야
        score = abs(inc - nominal) + d * 500            # 각도 우선, 접합 간격 보조
        if best is None or score < best["score"]:
            best = dict(a=a, b=b, inc=inc, joint=d, score=score)
```

그리고 꼭짓점은 **두 직선의 교점**으로 푼다.

```python
(x1, y1), (x2, y2) = a["p0"], a["p1"]
(x3, y3), (x4, y4) = b["p0"], b["p1"]
den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
if abs(den) < 1e-12:                                # 평행 — 교점 없음
    return None
px = ((x1*y2 - y1*x2) * (x3-x4) - (x1-x2) * (x3*y4 - y3*x4)) / den
py = ((x1*y2 - y1*x2) * (y3-y4) - (y1-y2) * (x3*y4 - y3*x4)) / den
```

방향(yaw)은 두 팔의 단위벡터를 더한 **이등분선**으로 구한다.

```python
far = lambda s: max((s["p0"], s["p1"]), key=lambda p: math.hypot(p[0]-px, p[1]-py))
ta, tb = far(a), far(b)                             # 꼭짓점에서 먼 쪽이 팔 끝
ua = ((ta[0]-px)/armA, (ta[1]-py)/armA)
ub = ((tb[0]-px)/armB, (tb[1]-py)/armB)
bx, by = ua[0] + ub[0], ua[1] + ub[1]               # 두 단위벡터의 합 = 이등분선
best["bisector"] = math.degrees(math.atan2(by/bn, bx/bn))
```

왜 이게 중요한가. 로봇을 세워 두고 30프레임을 뜬 실측 산포를 보면 답이 나온다.

{{< figure src="/images/diagrams/autodrive-vgroove-apex-intersection.svg" alt="꼭짓점을 두 직선의 교점으로 구하면 표준편차 0.33 mm 인데 팔 끝점은 2.3 mm 로 7배 차이가 난다는 비교" >}}

**팔 길이는 σ 2.3 mm 로 흔들리는데 꼭짓점은 0.33 mm 다. 7배 차이다.**

팔 끝은 "스캔 점이 어디서 끊겼나"에 달려 있어 프레임마다 달라진다. 반면 교점은 **변 전체 수십 개 점의 피팅**에서 나오므로 끝점 몇 개가 흔들려도 거의 안 움직인다. 모서리 마감이 거칠어도 상관없다.

**정작 도킹에 필요한 값이 가장 정확하다.** 운이 아니라 그렇게 되도록 고른 것이다.

---

## 3. 제어부를 고치지 않는 법

### 3-1. 이미 있는 것과 없는 것

정리해 보면 필요한 세 조각 중 두 개는 이미 있었다.

| 조각 | 상태 |
|---|---|
| V홈이 보인다 | ✅ 오프라인 도구로 검증됨 |
| 실시간으로 pose 를 내는 노드 | ❌ **이것만 없다** |
| 그 pose 로 정밀 주차하는 서보 | ✅ AprilTag 도킹에서 검증됨 |

가운데 한 칸만 채우면 된다. 그런데 어떻게 끼워 넣을 것인가.

### 3-2. 계약을 그대로 흉내 낸다

기존 정밀 주차 노드가 소비하는 것은 **딱 하나**였다.

```python
self.create_subscription(PoseStamped, "/wasab/tag_pose", self._on_tag, 10)
```

`PoseStamped`, `base_footprint` 기준 x·y·yaw. 그게 전부다. 그렇다면 **라이다 검출기가 같은 모양으로 내면 제어부는 자기가 카메라를 보는지 라이다를 보는지 알 필요가 없다.**

| 라이다에서 구한 값 | 메시지 필드 |
|---|---|
| V홈 꼭짓점 (두 직선의 교점) | `position.x`, `position.y` |
| 이등분선 + 180° | `orientation` (yaw) |

발행부는 기존 카메라 검출기의 것과 사실상 같다.

```python
def _publish(self, x, y, yaw):
    m = PoseStamped()
    m.header.stamp = self.get_clock().now().to_msg()
    m.header.frame_id = self.base_frame          # base_footprint
    m.pose.position.x = x
    m.pose.position.y = y
    qx, qy, qz, qw = g.quat_from_yaw(yaw)
    m.pose.orientation.x = qx; m.pose.orientation.y = qy
    m.pose.orientation.z = qz; m.pose.orientation.w = qw
    self.pub_pose.publish(m)
```

구독 쪽에는 함정이 하나 있다. `/scan` 의 QoS 는 개체마다 다른데, **BEST_EFFORT 구독은 RELIABLE 발행자와도 호환되지만 그 반대는 안 된다.** 그래서 느슨한 쪽으로 잡는다.

```python
qos = QoSProfile(depth=5, history=HistoryPolicy.KEEP_LAST,
                 reliability=ReliabilityPolicy.BEST_EFFORT)
self.create_subscription(LaserScan, self.scan_topic, self._on_scan, qos)
```

이렇게 맞추니 **제어 코드 수정이 0줄**이 됐다. 새 제어기를 쓰지 않았고, PID 게인을 다시 잡지도 않았다. 몇 달에 걸쳐 실기로 다듬은 서보를 그대로 재사용했다.

### 3-3. 두 검출기가 싸우지 않게

문제가 하나 있었다. 정밀 주차 노드는 시작할 때 **카메라 검출기를 스스로 띄운다.** 끄는 옵션이 없다. 그대로 두면 `/wasab/tag_pose` 발행자가 둘이 되어 서로 다른 값을 번갈아 밀어 넣는다.

코드를 고치지 않고 피하는 방법이 있었다. **토픽 리매핑**이다.

```bash
ros2 run wasab_docking precision_parking --ros-args \
  -p tag_goal_x:=0.07 -p cmd_vel_enabled:=true \
  -r /wasab/tag_pose:=/wasab/vgroove_pose    # ← 라이다 쪽만 보게
```

카메라 검출기는 여전히 뜨지만 아무도 그 토픽을 안 듣는다. ROS 의 리매핑은 이럴 때 쓰라고 있는 기능이다.

실시간 화면은 이렇게 돈다. 위쪽이 검출기(극좌표 플롯 + 끼인각·꼭짓점 거리·x/y/yaw 수치), 아래쪽이 관제 GUI 와 아레나 카메라다.

<video src="/images/auto_drive/lidar-vgroove-detector-screen.mp4" controls loop muted playsinline preload="metadata" style="max-width:420px;width:100%"></video>

---

## 4. 로봇을 움직이기 전에 잡은 버그 셋

실기 전에 세 개를 잡았다. 셋 다 **로봇이 움직였으면 사고로 이어질** 것들이었다.

### 4-1. 60° 와 120° 를 구분하지 못한다

끼인각을 **선분의 직선 각도**로 구하고 있었다. 그런데 생각해 보면 60° V홈과 120° V홈은 **두 직선이 완전히 동일하다.** 다른 것은 팔이 어느 쪽으로 뻗었는가뿐이다.

{{< figure src="/images/diagrams/autodrive-vgroove-60-vs-120.svg" alt="같은 두 직선이 만드는 60도 쐐기와 120도 쐐기 비교 — 직선 각도만으로는 구분되지 않는다" >}}

직선 각도만 보면 둘 다 120° 로 나온다. 방 안에 60° 모서리가 있으면 V홈으로 착각한다.

**해법**: 꼭짓점에서 팔 끝으로 가는 두 벡터의 사잇각을 따로 재서 교차 검증한다. 벡터는 방향이 있으므로 60° 와 120° 를 구분한다.

```python
def included_angle(apex, tip_a, tip_b):
    """꼭짓점에서 두 팔 끝을 향하는 벡터 사이의 실제 끼인각(도).

    선분의 직선 각도로 구한 값과 달리 60° 와 120° 를 구분한다.
    """
    ua = (tip_a[0] - apex[0], tip_a[1] - apex[1])
    ub = (tip_b[0] - apex[0], tip_b[1] - apex[1])
    na, nb = math.hypot(*ua), math.hypot(*ub)
    cos = (ua[0]*ub[0] + ua[1]*ub[1]) / (na * nb)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))
```

기존 판정은 그대로 두고 **뒤에 관문을 하나 더 세우는 방식**으로 붙였다. 검증된 코드를 건드리지 않으면서 구멍만 막는다.

```python
inc_true = included_angle(v["apex"], v["tipA"], v["tipB"])
if abs(inc_true - nominal) > span:
    return None                      # 60° 모서리 등 오인 차단
```

이 버그는 **테스트가 잡았다.** 합성 스캔을 만드는 헬퍼를 하나 두고,

```python
def synth_scan(apex=(0.55, 0.0), inc_deg=120.0, arm=0.17, bisector_deg=180.0, n=720, ...):
    """V홈 하나만 있는 합성 LaserScan.ranges 를 만든다."""
    half = math.radians(inc_deg) / 2.0
    b = math.radians(bisector_deg)
    dirs = [(math.cos(b + half), math.sin(b + half)),      # 두 변의 방향
            (math.cos(b - half), math.sin(b - half))]
    ...
```

"60° 는 검출되면 안 된다"고 단언한 테스트가 빨갛게 떴다.

```python
def test_out_of_span_angle_rejected():
    """설계 ±span 밖(예: 60°)은 V홈으로 보지 않는다."""
    ranges, amin, ainc, rmin, rmax = synth_scan(inc_deg=60.0)
    assert vg.detect(ranges, amin, ainc, rmin, rmax, EXT0) is None
```

실물 없이, 로봇을 켜지도 않고 잡은 버그다. **합성 스캔을 만들 수 있다는 게 라이다의 장점**이기도 하다 — 카메라라면 이런 테스트를 쓰기가 훨씬 어렵다.

### 4-2. 라이다가 거꾸로 달려 있었다

화면을 띄우고 나서 사용자가 지적했다. "좌우가 바뀐 것 같다. 실제 V홈은 오른쪽인데 화면은 왼쪽이다."

TF 를 떠 보니 답이 바로 나왔다.

```text
base_footprint → rplidar_link
  Translation: [-0.017, 0.000, 0.125]
  RPY(degree): [0, 0, 180.000]          ← 180° 회전
```

**라이다가 뒤집혀 달려 있었고, 그 사실은 URDF 에 이미 적혀 있었다.** AMCL 도 Nav2 도 TF 로 그 값을 읽어 정상 동작하고 있었다. 내 노드만 라이다 좌표를 그대로 썼던 것이다.

여기서 판단이 하나 필요했다. 요청은 "좌우 대칭으로 뒤집어 그려 달라"였는데 **그렇게 하면 안 된다.**

| 방식 | 정면 목표 | 좌우로 벗어난 목표 |
|---|---|---|
| 거울 대칭 | 맞아 보임 | **좌우가 반대로 나옴** |
| 180° 회전 | 맞음 | 맞음 |

거울은 좌표계의 손대칭(handedness)을 뒤집는다. 당시 V홈이 정면에서 18 mm 밖에 안 벗어나 있어 차이가 안 보였을 뿐, 비스듬히 접근하면 **횡방향으로 반대편에 붙는다.** 필요한 것은 x·y 를 함께 뒤집는 180° 회전이었다.

그리고 값을 코드에 적어 넣는 대신 **TF 에서 읽도록** 했다. URDF 를 단일 출처로 두면 장착이 바뀌어도 따라간다.

```python
def _resolve_ext(self, lidar_frame):
    """base_frame ← lidar_frame 변환을 TF 에서 한 번만 읽어 캐시한다."""
    if self._ext_from_tf or not self.use_tf:
        return
    try:
        tr = self._tf_buf.lookup_transform(self.base_frame, lidar_frame, rclpy.time.Time())
    except Exception:
        return                              # 아직 TF 가 안 찼다 — 다음 스캔에 재시도
    t = tr.transform.translation
    yaw = g.yaw_from_quat(tr.transform.rotation.x, ..., tr.transform.rotation.w)
    self.ext = {"x": t.x, "y": t.y, "yaw": yaw}
    self._ext_from_tf = True
```

적용은 평범한 SE(2) 변환이다.

```python
def lidar_to_base(x, y, yaw_deg, ext):
    c, s = math.cos(ext["yaw"]), math.sin(ext["yaw"])
    yaw = math.radians(yaw_deg) + ext["yaw"]
    return (ext["x"] + c * x - s * y,
            ext["y"] + s * x + c * y,
            math.atan2(math.sin(yaw), math.cos(yaw)))    # ±π 정규화
```

기동 로그로 적용 여부를 확인할 수 있게 해 두었다.

```text
장착 변환 TF 적용: base_footprint←rplidar_link x=-0.017 y=0.000 yaw=180.0°
```

### 4-3. yaw 규약이 정확히 180° 반대

제어기의 오차 계산은 이렇게 생겼다.

```python
"yaw": normalize_angle(tyaw - tag_goal["yaw"])     # tag_goal_yaw = 0.0
```

즉 **로봇이 정면으로 마주봤을 때 목표물의 yaw 가 0 이어야 한다.** AprilTag 는 법선이 벽 안쪽을 향해 그 조건을 만족한다. 그런데 V홈 이등분선은 꼭짓점에서 **로봇 쪽**을 향한다. 정면인데도 178° 가 나왔다.

그대로 물렸으면 제어기가 178° 를 0 으로 만들려고 **로봇을 반 바퀴 돌렸을 것이다.** 이등분선에 180° 를 더해 해결했다.

```python
def target_yaw_deg(bisector_deg):
    """도킹 타깃 yaw = 이등분선 + 180°.

    precision_parking 은 `tag_goal_yaw: 0.0` 을 목표로 오차를 계산한다.
    즉 로봇이 정면으로 마주봤을 때 목표물 yaw 가 0 이어야 한다. AprilTag 는 법선이
    벽 안쪽을 향해 그 조건을 만족하는데, V홈 이등분선은 꼭짓점에서 로봇 쪽을 향하므로
    그대로 쓰면 정확히 180° 어긋나 컨트롤러가 로봇을 반 바퀴 돌린다.
    """
    return _norm180(bisector_deg + 180.0)
```

회귀를 막는 테스트도 함께 넣었다.

```python
def test_detect_yaw_is_zero_when_facing_groove():
    """정면에서 본 합성 V홈이면 발행 yaw 가 0 근처여야 한다(180° 뒤집힘 회귀 방지)."""
    ranges, amin, ainc, rmin, rmax = synth_scan(bisector_deg=180.0)
    x, y, yaw, _info = vg.detect(ranges, amin, ainc, rmin, rmax, EXT0)
    assert abs(math.degrees(yaw)) < 3.0, math.degrees(yaw)
```

여기 곁가지가 하나 더 있다. 고친 뒤 값이 `358.48°` 로 나와서 "아직도 틀렸다"고 판단했는데, 358.48° 는 −1.52° 와 같은 각이다. 쿼터니언으로는 동일하고 제어기도 정상 해석한다. **값은 맞는데 사람이 오판한 것이다.** ±180° 로 정규화하도록 고쳤다. 기계가 아니라 읽는 사람을 위한 수정이다.

---

## 5. 실기

### 5-1. 안전장치가 먼저 걸렸다

첫 실행은 45초 만에 실패했다. 로그를 보니 이유가 명확했다.

```text
precision_parking 시작: ... cmd_vel_enabled=False
TAG_SERVO_ALIGN → FAILED (fail=overall_timeout)
error_x = 0.3954
```

설정 파일에 주석이 달려 있었다. *"안전 기본값: 첫 실기는 dry-run(zero 발행), 방향 확인 후 true"*. 속도 출력이 막힌 채로 돌아간 것이다.

**결과적으로 좋은 일이었다.** 로봇이 가만히 선 채로 검출 → pose → 리매핑 → 상태기계 → 오차계산까지 전 경로가 검증됐다. `error_x = 0.3954` 는 545 − 150 = 395 mm 로 정확했다. 그 다음에 속도를 열었다.

### 5-2. 6회 전부 성공

<video src="/images/auto_drive/lidar-vgroove-docking-demo.mp4" controls loop muted playsinline preload="metadata" style="max-width:420px;width:100%"></video>

바닥의 주황색 V홈으로 접근해 꼭짓점 앞에 정지한다. 카메라는 꺼져 있고, 로봇이 보고 있는 것은 라이다 스캔뿐이다.

| # | 출발 | 목표 | 최종 | 오차 | y | yaw |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 545 | 150 | 161 | 11.8 | +4.5 | +1.3° |
| 2 | 161 | 100 | 112 | 11.8 | +2.2 | +0.7° |
| 3 | 112 | 70 | 82.4 | 12.6 | +0.1 | −0.6° |
| 4 | 624 | 150 | 162 | 12.4 | +6.8 | +2.1° |
| 5 | 162 | 70 | 81.3 | 10.4 | 0.0 | −1.1° |
| 6 | 645 | 70 | 82.1 | 12.1 | −0.9 | −1.4° |

(mm 단위, 검출률 100%)

70 mm 목표 3회가 **82.4 / 81.3 / 82.1 mm** 로 편차 1.1 mm 다. 출발이 112 mm 든 645 mm 든 같은 곳에 선다.

### 5-3. 가까울수록 정렬이 좋아진다

눈에 띄는 경향이 있다. 횡편차가 **4.5 → 2.2 → 0.1 mm**, 각도가 **1.3° → 0.6°** 로 줄어든다.

당연한 물리다. 라이다의 각도 분해능은 0.5° 로 고정인데, 그게 만드는 **횡방향 불확실성은 거리에 비례**한다. 1 m 에서 0.5° 는 8.7 mm 지만 10 cm 에서는 0.9 mm 다. 가까워질수록 같은 각도 오차가 작은 거리 오차로 환산된다.

**즉 접근할수록 정밀해지는 구조**다. 도킹에 유리한 성질이다.

### 5-4. 12 mm 는 오차가 아니라 특성이다

여섯 번 모두 목표보다 **11~13 mm 앞에** 섰다. 우연이 아니다.

정착 판정 허용치가 `tol_x: 15 mm` 다. 오차가 그 안에 들어오는 순간 멈추는데, 접근 방향이 항상 같으니 늘 비슷한 지점에서 걸린다. **예측 가능한 계통 오차**이므로 목표값을 12 mm 앞당기거나 허용치를 조이면 없앨 수 있다. 랜덤 오차였다면 훨씬 나쁜 소식이었다.

---

## 6. 한계 — 너무 가까우면 형상이 무너진다

이 방식에는 명확한 하한이 있다. 꼭짓점까지 100 mm 인데 팔은 170 mm 다. 팔의 바깥쪽 절반이 라이다 시야 뒤로 넘어간다.

실제로 접근하면서 끼인각이 이렇게 변했다.

```text
123° → 121° → 117° → 113°     (거리 645 → 82 mm)
```

남은 짧은 조각으로 직선을 맞추니 각도가 흔들린다. 82 mm 에서는 **간헐적 미검출**까지 나왔다. 앞의 검출기 화면에서 접근 후반에 끼인각 표시가 흔들리는 것이 이 현상이다.

다만 **위치는 여전히 정확하다.** 같은 구간에서 꼭짓점 σ 는 0.11 mm 였다. 2장에서 본 성질이 여기서도 유효하다 — 끝점이 잘려도 교점은 버틴다.

그래서 이렇게 정리된다.

| 거리 | 위치 | 각도·형상 |
|---|---|---|
| 30 cm 이상 | 정확 | 정확 |
| 10 cm 내외 | 정확 | 흔들림 |
| 5 cm 이하 | 미검증 | 검출 실패 예상 |

**도킹 자체는 문제없다** — 목표 지점에 도달하면 멈추면 되고, 그 시점의 위치 정확도는 유지된다. 문제가 되는 것은 이 거리에서 형상을 계속 감시해야 하는 용도다. 그래서 5 cm 는 시도하지 않았다.

---

## 7. 상대 좌표와 절대 좌표

도킹이 성공한 뒤 자연스러운 질문이 나온다. "그럼 이 V홈이 지도상 어디 있는지도 알 수 있나?"

알 수 있다. 로봇의 맵 좌표에 V홈의 상대 위치를 합성하면 된다.

```text
V홈(map) = map→base_footprint  ⊙  V홈(base 기준)
```

그런데 실제로 세 번 재 보니 이렇게 나왔다.

| 측정 위치 | x | y | yaw |
|---|---:|---:|---:|
| 62 cm 떨어져서 | 0.827 | −0.141 | −89.8° |
| 8 cm 붙어서 | 0.823 | −0.170 | −90.8° |
| 66 cm | 0.826 | −0.123 | −93.8° |
| **산포** | **4 mm** | **47 mm** | **4°** |

**x 는 4 mm 안에 모이는데 y 는 47 mm 흩어진다.** 라이다 상대 측정이 σ 0.1 mm 급인데 결과가 cm 급으로 흩어진다면, 그 오차는 라이다에서 온 게 아니다. **전부 [AMCL](/posts/auto_drive/amcl-yaw-측위오차-추적기-가설반박부터-환경개선까지/) 이다.**

x 가 잘 맞는 것은 그 방향이 로봇의 전후축이라 라이다 거리가 직접 반영되기 때문이고, y 와 yaw 는 측위의 횡방향·각도 오차를 그대로 물려받는다.

여기서 얻는 교훈이 이 글의 결론이기도 하다.

> **도킹은 절대 좌표를 몰라도 된다.** 목표물까지의 상대 위치만 알면 붙을 수 있고, 그 상대 측정은 측위 오차와 무관하게 mm 급이다.

우리 도킹이 AMCL 이 53 cm 나 틀어져 있던 상태에서도 성공한 이유가 이것이다. 반대로 맵 좌표는 **등록용 대략치**로만 써야 한다. 그래서 실시간 화면에도 그렇게 명시해 두었다.

---

## 정리

**2D 라이다로 도킹하려면**

1. **형상을 랜드마크로 삼는다.** 각도는 거리와 무관하고, 주변에 흔치 않은 값을 고른다.
2. **점이 아니라 교점을 쓴다.** 직선 피팅의 교점은 끝점 흔들림에 둔감하다 (σ 0.33 vs 2.3 mm).
3. **기존 제어부의 계약을 흉내 낸다.** 같은 메시지를 내면 제어 코드를 안 고쳐도 된다.
4. **장착 변환은 TF 에서 읽는다.** URDF 에 이미 있는 값을 코드에 복사하면 언젠가 어긋난다.
5. **좌표 규약을 코드로 확인한다.** "정면일 때 0" 인지 "정면일 때 180" 인지는 추측하지 말고 오차 계산식을 읽는다.
6. **첫 실기는 속도를 막고 돌린다.** 로봇이 안 움직이는 채로 전 경로를 검증할 수 있다.

**이 방식이 좋은 경우**

- 카메라를 못 쓰는 환경 (고장·조명·먼지)
- 마커를 붙일 수 없는 대상
- 측위가 불안정한 상황 — 상대 측정이라 영향받지 않는다

**이 방식이 나쁜 경우**

- 대상이 여럿이고 **구분**해야 할 때 (라이다는 ID 를 못 읽는다)
- 목표물이 아주 작거나, 아주 가까이 붙어야 할 때 (형상이 시야에서 잘린다)
- 주변에 비슷한 각도의 구조물이 많을 때

카메라와 라이다는 대체재가 아니라 **서로의 실패 모드를 메우는 관계**다. 태그는 ID 를 주고, 형상은 조명 없이도 mm 를 준다. 둘 다 같은 계약으로 내도록 만들어 두면, 상황에 따라 갈아 끼울 수 있다. 이번에 얻은 가장 실용적인 성과는 그것이다.
