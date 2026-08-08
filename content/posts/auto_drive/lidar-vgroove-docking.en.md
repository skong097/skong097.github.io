---
title: "Docking Without a Camera — Finding a V-Groove with 2D Lidar, Down to 2 cm"
date: 2026-08-08
tags: ["auto-drive", "lidar", "docking", "ros2", "laserscan", "line-fitting", "split-and-merge", "tf2", "qos", "precision-parking", "amcl", "wasab"]
categories: ["robotics"]
summary: "The camera died, taking AprilTag docking with it. The lidar was fine. So the robot docked by finding a 120° V-groove on the wall with nothing but a 2D lidar — six runs, six successes, a final gap of 2 cm and lateral error inside 1 mm. Two things made it work: deriving the apex from the intersection of two fitted lines rather than from a point sampled on the corner (σ 0.33 vs 2.3 mm), and imitating the exact message the existing controller already consumed, so not one line of control code changed."
draft: false
ShowToc: true
TocOpen: true
---

The standard answer for robot docking is a visual marker. Stick an AprilTag on the wall, look at it with a camera, solve the pose with `solvePnP`. We built exactly that, and it got us [precision parking to 15 cm head-on](/posts/auto_drive/nav2-apriltag-pid-정밀주차/) (Korean).

Then the camera died.

```text
dmesg: ov5647 10-0036: ov5647_read: i2c read error, reg: 300a = -5
       ov5647: probe of 10-0036 failed with error -5
→ libcamera sees 0 cameras
```

I2C communication with the sensor chip itself is gone. Until someone reseats the ribbon cable, this robot cannot dock. But **the lidar is fine.** So — could it dock on lidar alone?

Short answer: yes. **Six docking runs on 2D lidar only, six successes, a final physical gap of 2 cm and lateral error inside 1 mm.** And not one line of control code changed.

---

## 1. What do we use as a landmark?

### 1-1. What a 2D lidar gives you

A 2D lidar sweeps one plane and hands back **a single array of ranges**. Ours is 720 beams at 10 Hz.

```text
ranges[0..719],  angle_min = -π,  angle_increment = 0.0087 rad
```

Convert each beam from polar to Cartesian and you have a **point cloud**. In code that is the whole of it.

```python
def scan_to_points(ranges, angle_min, angle_increment, range_min, range_max):
    """LaserScan.ranges → [(x, y, r, index)]. Drop inf/nan/out-of-range beams."""
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

Carrying `index` along pays off later. A jump in beam number means measurements failed in between, and that is itself a hint that an object ended there.

No colour, no texture, no ID. Where a camera says "that is tag number 8," a lidar only says "there is something here." So to serve as a landmark, **the shape itself has to be the identifier.**

### 1-2. The V-groove — the angle is the name

We picked a **V-groove** with a 120° included angle and 170 mm sides. An unremarkable piece of wall furniture, but an excellent target from the lidar's point of view, for three reasons.

**1. Angle is independent of range.** Seen from 1 m or from 30 cm, 120° is 120°. Unlike size-based tests, no range compensation is needed.

**2. It is uncommon nearby.** Corners in a room are mostly 90°. A 120°±20° window filters wall corners out.

**3. Two sides meet, so a single point is defined.** A flat wall only tells you "somewhere along here," but a bend gives you **one point.** As we will see, that is the crux of the precision.

---

## 2. Pulling the V-groove out of the point cloud

### 2-1. Cut, straighten, pair

{{< figure src="/images/diagrams/autodrive-vgroove-pipeline-en.svg" alt="Four-stage pipeline turning a 2D lidar scan into a V-groove pose: cluster, split into lines, pair segments, then solve the pose and publish a PoseStamped" >}}

Stage 2, split-and-merge, is recursive. Fit a line to a bunch of points; if the residual of **the worst-offending point** exceeds tolerance (6 mm), cut the bunch in two at that point, then do the same to each piece.

```python
def _split(pts, tol, depth=0):
    """Cut at the worst point whenever max residual exceeds tol (split-and-merge)."""
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

`depth > 6` and `k < 4` are the guard rails. Heavy noise makes it want to split forever, so depth is capped, and it never cuts within 4 points of an end — too short a piece makes line fitting meaningless.

The fit is **total least squares.** Ordinary least squares cannot fit a vertical line, and lidar points lie in every direction, so that would not do.

```python
sxx = sum((p[0] - mx) ** 2 for p in pts)
syy = sum((p[1] - my) ** 2 for p in pts)
sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
th  = 0.5 * math.atan2(2 * sxy, sxx - syy)      # principal axis
d   = (math.cos(th), math.sin(th))              # line direction
nv  = (-d[1], d[0])                             # normal → for residuals
```

The clustering threshold cannot be a constant, because **lidar points spread further apart with range.**

```python
for a, b in zip(pts, pts[1:]):
    gap = math.hypot(b[0] - a[0], b[1] - a[1])
    # adaptive threshold, proportional to range — so a distant wall
    # does not shatter on point spacing alone
    thr = max(0.02, 3.0 * b[2] * angle_increment)
    if b[3] - a[3] > 2 or gap > thr:
        clusters.append(cur); cur = [b]
    else:
        cur.append(b)
```

Point spacing on a wall 3 m away is 26 mm; a fixed 20 mm threshold shatters a perfectly good wall. `b[3] - a[3] > 2` catches skipped beam numbers — nothing was hit in between, so we treat the object as having ended.

### 2-2. The apex is not sampled, it is where two lines cross

The most important design decision is here. **We do not take the V-groove apex from a point sampled on the corner.** Instead we fit a line to each side and compute **their intersection.**

Here is how a pair is chosen.

```python
for i in range(len(segs)):
    for j in range(i + 1, len(segs)):
        a, b = segs[i], segs[j]
        if not (arm[0] <= a["length"] <= arm[1] and arm[0] <= b["length"] <= arm[1]):
            continue                                   # arm length 8–30 cm
        diff = abs(a["ang"] - b["ang"])
        inc = 180 - min(diff, 180 - diff)
        if abs(inc - nominal) > span:
            continue                                   # 120° ±20°
        d = min(math.hypot(pa[0] - pb[0], pa[1] - pb[1])
                for pa in (a["p0"], a["p1"]) for pb in (b["p0"], b["p1"]))
        if d > joint:
            continue                                   # endpoints must meet within 5 cm
        score = abs(inc - nominal) + d * 500            # angle first, joint gap secondary
        if best is None or score < best["score"]:
            best = dict(a=a, b=b, inc=inc, joint=d, score=score)
```

And the apex is solved as **the intersection of the two lines.**

```python
(x1, y1), (x2, y2) = a["p0"], a["p1"]
(x3, y3), (x4, y4) = b["p0"], b["p1"]
den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
if abs(den) < 1e-12:                                # parallel — no intersection
    return None
px = ((x1*y2 - y1*x2) * (x3-x4) - (x1-x2) * (x3*y4 - y3*x4)) / den
py = ((x1*y2 - y1*x2) * (y3-y4) - (y1-y2) * (x3*y4 - y3*x4)) / den
```

Heading comes from the **bisector** — the sum of the two arms' unit vectors.

```python
far = lambda s: max((s["p0"], s["p1"]), key=lambda p: math.hypot(p[0]-px, p[1]-py))
ta, tb = far(a), far(b)                             # the end farther from the apex is the tip
ua = ((ta[0]-px)/armA, (ta[1]-py)/armA)
ub = ((tb[0]-px)/armB, (tb[1]-py)/armB)
bx, by = ua[0] + ub[0], ua[1] + ub[1]               # sum of unit vectors = bisector
best["bisector"] = math.degrees(math.atan2(by/bn, bx/bn))
```

Why does this matter? Park the robot, capture 30 frames, and the spread answers it.

{{< figure src="/images/diagrams/autodrive-vgroove-apex-intersection-en.svg" alt="Deriving the apex as the intersection of two fitted lines gives a standard deviation of 0.33 mm against 2.3 mm for the arm endpoints — a sevenfold difference" >}}

**Arm length wobbles at σ 2.3 mm while the apex sits at 0.33 mm. Seven times tighter.**

An arm tip depends on where the scan happened to stop, so it moves frame to frame. The intersection, by contrast, falls out of a fit over **dozens of points along the whole side**, so a few jittering endpoints barely shift it. A rough corner finish does not matter either.

**The value docking actually needs is the most accurate one.** That is not luck; it is why this shape was chosen.

---

## 3. How not to touch the controller

### 3-1. What existed and what didn't

Of the three pieces needed, two already existed.

| Piece | Status |
|---|---|
| Seeing the V-groove | ✅ verified with an offline tool |
| A node publishing pose in real time | ❌ **the only gap** |
| A servo that precision-parks on that pose | ✅ proven by AprilTag docking |

Only the middle box needed filling. The question was how to slot it in.

### 3-2. Imitate the contract exactly

The existing precision-parking node consumed **exactly one thing.**

```python
self.create_subscription(PoseStamped, "/wasab/tag_pose", self._on_tag, 10)
```

A `PoseStamped` — x, y, yaw in `base_footprint`. That is all. Which means **if the lidar detector emits the same shape, the controller never needs to know whether it is looking through a camera or a lidar.**

| Value from the lidar | Message field |
|---|---|
| V-groove apex (intersection of two lines) | `position.x`, `position.y` |
| Bisector + 180° | `orientation` (yaw) |

The publishing side is effectively identical to the camera detector's.

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

The subscribing side has one trap. QoS on `/scan` varies by driver, and **a BEST_EFFORT subscription is compatible with a RELIABLE publisher, but not the other way round.** So take the loose side.

```python
qos = QoSProfile(depth=5, history=HistoryPolicy.KEEP_LAST,
                 reliability=ReliabilityPolicy.BEST_EFFORT)
self.create_subscription(LaserScan, self.scan_topic, self._on_scan, qos)
```

With that matched, **control-code changes came to zero lines.** No new controller, no re-tuning of PID gains. The servo we had spent months refining on real hardware was reused as is.

### 3-3. Keeping two detectors from fighting

One problem remained. The precision-parking node **starts the camera detector itself** on launch, with no option to skip it. Left alone, `/wasab/tag_pose` would have two publishers pushing different values in alternation.

There was a way around it without editing code: **topic remapping.**

```bash
ros2 run wasab_docking precision_parking --ros-args \
  -p tag_goal_x:=0.07 -p cmd_vel_enabled:=true \
  -r /wasab/tag_pose:=/wasab/vgroove_pose    # ← listen only to the lidar side
```

The camera detector still comes up; nobody subscribes to its topic. This is precisely what ROS remapping is for.

Here is the live view. On top is the detector — a polar plot plus the numeric panel showing included angle, apex range and x/y/yaw. Below it, the fleet GUI and the arena cameras.

<video src="/images/auto_drive/lidar-vgroove-detector-screen.mp4" controls loop muted playsinline preload="metadata" style="max-width:420px;width:100%"></video>

---

## 4. Three bugs caught before the robot moved

Three of them, before any real run. All three would have turned into an accident had the robot been moving.

### 4-1. It could not tell 60° from 120°

The included angle was being derived from **the line angle of the segments.** But think it through: a 60° V-groove and a 120° V-groove **lie on exactly the same pair of lines.** The only difference is which way the arms extend.

{{< figure src="/images/diagrams/autodrive-vgroove-60-vs-120-en.svg" alt="The same two lines produce both a 60° wedge and a 120° wedge — segment line angle alone cannot separate them" >}}

By line angle alone, both read 120°. Any 60° corner in the room gets mistaken for the groove.

**The fix**: separately measure the angle between the two vectors running from the apex to each arm tip, and cross-check. Vectors have direction, so they distinguish 60° from 120°.

```python
def included_angle(apex, tip_a, tip_b):
    """True included angle (deg) between the apex-to-tip vectors.

    Unlike the value derived from segment line angles, this separates 60° from 120°.
    """
    ua = (tip_a[0] - apex[0], tip_a[1] - apex[1])
    ub = (tip_b[0] - apex[0], tip_b[1] - apex[1])
    na, nb = math.hypot(*ua), math.hypot(*ub)
    cos = (ua[0]*ub[0] + ua[1]*ub[1]) / (na * nb)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))
```

It was bolted on as **an extra gate behind the existing test**, leaving the original decision untouched. Plug the hole without disturbing code that already works.

```python
inc_true = included_angle(v["apex"], v["tipA"], v["tipB"])
if abs(inc_true - nominal) > span:
    return None                      # reject 60° corners and the like
```

**A test caught this bug.** With one helper that synthesises a scan,

```python
def synth_scan(apex=(0.55, 0.0), inc_deg=120.0, arm=0.17, bisector_deg=180.0, n=720, ...):
    """Build a synthetic LaserScan.ranges containing exactly one V-groove."""
    half = math.radians(inc_deg) / 2.0
    b = math.radians(bisector_deg)
    dirs = [(math.cos(b + half), math.sin(b + half)),      # directions of the two sides
            (math.cos(b - half), math.sin(b - half))]
    ...
```

the test asserting "60° must not be detected" went red.

```python
def test_out_of_span_angle_rejected():
    """Anything outside the design ±span (e.g. 60°) is not a V-groove."""
    ranges, amin, ainc, rmin, rmax = synth_scan(inc_deg=60.0)
    assert vg.detect(ranges, amin, ainc, rmin, rmax, EXT0) is None
```

Caught with no hardware, without even powering the robot on. **Being able to synthesise scans is itself a lidar advantage** — writing this test against a camera would be far harder.

### 4-2. The lidar was mounted upside down

After bringing the live view up, the user pointed it out: "left and right look swapped. The real groove is on the right, but the screen shows it on the left."

Dumping TF answered it immediately.

```text
base_footprint → rplidar_link
  Translation: [-0.017, 0.000, 0.125]
  RPY(degree): [0, 0, 180.000]          ← 180° rotation
```

**The lidar was mounted flipped, and that fact was already written in the URDF.** AMCL and Nav2 both read it through TF and were working fine. Only my node was using raw lidar coordinates.

A judgement call was needed here. The request was "mirror it left-to-right," and **that would have been wrong.**

| Approach | Target dead ahead | Target off to one side |
|---|---|---|
| Mirror | looks right | **ends up on the wrong side** |
| 180° rotation | right | right |

A mirror flips the handedness of the frame. The groove happened to be only 18 mm off centre at the time, so the difference was invisible — but approach at an angle and the robot **docks on the opposite side laterally.** What was needed was a 180° rotation that flips x and y together.

And rather than hard-coding the value, the node **reads it from TF.** Keep the URDF as the single source and the code follows any remount.

```python
def _resolve_ext(self, lidar_frame):
    """Read base_frame ← lidar_frame from TF once and cache it."""
    if self._ext_from_tf or not self.use_tf:
        return
    try:
        tr = self._tf_buf.lookup_transform(self.base_frame, lidar_frame, rclpy.time.Time())
    except Exception:
        return                              # TF not populated yet — retry next scan
    t = tr.transform.translation
    yaw = g.yaw_from_quat(tr.transform.rotation.x, ..., tr.transform.rotation.w)
    self.ext = {"x": t.x, "y": t.y, "yaw": yaw}
    self._ext_from_tf = True
```

Applying it is an ordinary SE(2) transform.

```python
def lidar_to_base(x, y, yaw_deg, ext):
    c, s = math.cos(ext["yaw"]), math.sin(ext["yaw"])
    yaw = math.radians(yaw_deg) + ext["yaw"]
    return (ext["x"] + c * x - s * y,
            ext["y"] + s * x + c * y,
            math.atan2(math.sin(yaw), math.cos(yaw)))    # normalise to ±π
```

A start-up log line makes it verifiable.

```text
mount transform from TF: base_footprint←rplidar_link x=-0.017 y=0.000 yaw=180.0°
```

### 4-3. The yaw convention was exactly 180° out

The controller's error term looks like this.

```python
"yaw": normalize_angle(tyaw - tag_goal["yaw"])     # tag_goal_yaw = 0.0
```

In other words, **the target's yaw must be 0 when the robot is facing it head-on.** An AprilTag satisfies that, its normal pointing into the wall. But the V-groove bisector points from the apex **toward the robot.** Dead ahead, it read 178°.

Wired up as is, the controller would have tried to drive 178° to zero and **spun the robot half a turn.** Adding 180° to the bisector fixed it.

```python
def target_yaw_deg(bisector_deg):
    """Docking target yaw = bisector + 180°.

    precision_parking computes error against `tag_goal_yaw: 0.0`, i.e. the target's
    yaw must be 0 when the robot faces it head-on. An AprilTag satisfies this with
    its normal pointing into the wall, but the V-groove bisector points from the apex
    back at the robot — used raw it is exactly 180° out and the controller spins the
    robot half a turn.
    """
    return _norm180(bisector_deg + 180.0)
```

A regression test went in alongside.

```python
def test_detect_yaw_is_zero_when_facing_groove():
    """A synthetic groove seen head-on must publish yaw near 0 (guards the 180° flip)."""
    ranges, amin, ainc, rmin, rmax = synth_scan(bisector_deg=180.0)
    x, y, yaw, _info = vg.detect(ranges, amin, ainc, rmin, rmax, EXT0)
    assert abs(math.degrees(yaw)) < 3.0, math.degrees(yaw)
```

There is a footnote here. After the fix the value read `358.48°` and I judged it still broken — but 358.48° is the same angle as −1.52°. The quaternion is identical and the controller reads it correctly. **The value was right; the human misread it.** I changed it to normalise to ±180°. That fix was for the reader, not the machine.

---

## 5. On the robot

### 5-1. The safety default tripped first

The first run failed after 45 seconds. The log made the reason obvious.

```text
precision_parking start: ... cmd_vel_enabled=False
TAG_SERVO_ALIGN → FAILED (fail=overall_timeout)
error_x = 0.3954
```

A comment in the config explained it: *"safe default: first real run is a dry run (publish zeros); set true after confirming direction."* Velocity output had been blocked the whole time.

**Which turned out to be a good thing.** With the robot standing still, the entire path — detection → pose → remap → state machine → error computation — got verified. `error_x = 0.3954` was exactly 545 − 150 = 395 mm. Only then did I open up velocity.

### 5-2. Six runs, six successes

<video src="/images/auto_drive/lidar-vgroove-docking-demo.mp4" controls loop muted playsinline preload="metadata" style="max-width:420px;width:100%"></video>

The robot approaches the orange V-groove on the floor and stops in front of the apex. The camera is dead; all it is looking at is lidar scans.

| # | Start | Goal | Final | Error | y | yaw |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 545 | 150 | 161 | 11.8 | +4.5 | +1.3° |
| 2 | 161 | 100 | 112 | 11.8 | +2.2 | +0.7° |
| 3 | 112 | 70 | 82.4 | 12.6 | +0.1 | −0.6° |
| 4 | 624 | 150 | 162 | 12.4 | +6.8 | +2.1° |
| 5 | 162 | 70 | 81.3 | 10.4 | 0.0 | −1.1° |
| 6 | 645 | 70 | 82.1 | 12.1 | −0.9 | −1.4° |

(millimetres; detection rate 100%)

The three runs targeting 70 mm landed at **82.4 / 81.3 / 82.1 mm** — a spread of 1.1 mm. Starting from 112 mm or from 645 mm, it stops in the same place.

### 5-3. Alignment improves as it gets closer

There is a clear trend. Lateral error falls **4.5 → 2.2 → 0.1 mm**, angle **1.3° → 0.6°**.

That is straightforward physics. The lidar's angular resolution is fixed at 0.5°, but **the lateral uncertainty it produces scales with range.** At 1 m, 0.5° is 8.7 mm; at 10 cm it is 0.9 mm. The closer it gets, the smaller the distance error that the same angular error maps to.

**So the approach gets more precise as it proceeds** — a convenient property for docking.

### 5-4. The 12 mm is a characteristic, not an error

All six runs stopped **11–13 mm short** of the goal. That is not coincidence.

The settle tolerance is `tol_x: 15 mm`. It halts the moment error falls inside that band, and since the approach direction is always the same, it always catches at a similar point. Being a **predictable systematic offset**, it can be removed by moving the goal 12 mm nearer or tightening the tolerance. A random error would have been much worse news.

---

## 6. The limit — get too close and the shape collapses

This method has a hard floor. At 100 mm from the apex, the arms are 170 mm long: the outer half of each arm falls behind the lidar's field of view.

Measured during an actual approach, the included angle drifted like this.

```text
123° → 121° → 117° → 113°     (range 645 → 82 mm)
```

Fitting a line to the short remaining piece makes the angle wobble. At 82 mm there were even **intermittent detection dropouts.** The wobble in the included-angle readout late in the detector video above is exactly this.

But **position stays accurate.** Over the same stretch, apex σ was 0.11 mm. The property from section 2 holds here too: clip the endpoints and the intersection survives.

Which gives this summary.

| Range | Position | Angle / shape |
|---|---|---|
| Beyond 30 cm | accurate | accurate |
| Around 10 cm | accurate | wobbly |
| Under 5 cm | untested | detection likely fails |

**Docking itself is fine** — reach the goal and stop, and the positional accuracy at that moment holds. What breaks is any use that needs to keep monitoring the shape at that range. That is why 5 cm was never attempted.

---

## 7. Relative versus absolute coordinates

Once docking worked, a natural question followed: "so can we also tell where this groove sits on the map?"

Yes. Compose the groove's relative position onto the robot's map pose.

```text
groove(map) = map→base_footprint  ⊙  groove(relative to base)
```

Measured three times, though, it came out like this.

| Measured from | x | y | yaw |
|---|---:|---:|---:|
| 62 cm away | 0.827 | −0.141 | −89.8° |
| 8 cm away | 0.823 | −0.170 | −90.8° |
| 66 cm | 0.826 | −0.123 | −93.8° |
| **Spread** | **4 mm** | **47 mm** | **4°** |

**x lands inside 4 mm while y scatters over 47 mm.** When the lidar's relative measurement is at the σ 0.1 mm level and the result scatters at the centimetre level, that error did not come from the lidar. **It is all [AMCL](/posts/auto_drive/amcl-yaw-측위오차-추적기-가설반박부터-환경개선까지/)** (Korean).

x holds up because that direction is the robot's fore-aft axis, so lidar range feeds straight into it; y and yaw inherit the localisation's lateral and angular error wholesale.

The lesson there is also this post's conclusion.

> **Docking does not need absolute coordinates.** Knowing the relative position of the target is enough to dock, and that relative measurement is millimetre-grade regardless of localisation error.

That is why our docking succeeded even with AMCL off by 53 cm. Conversely, the map coordinate should be used only as **a rough figure for registration** — which is what the live view says on screen.

---

## Wrapping up

**To dock with a 2D lidar**

1. **Use shape as the landmark.** Angle is range-independent; pick a value that is uncommon nearby.
2. **Use the intersection, not a point.** The crossing of two fitted lines is insensitive to endpoint jitter (σ 0.33 vs 2.3 mm).
3. **Imitate the existing controller's contract.** Emit the same message and the control code needs no edits.
4. **Read the mount transform from TF.** Copy a value that already lives in the URDF into code and it will drift apart eventually.
5. **Verify coordinate conventions in code.** Whether "facing it" means 0 or 180 is not something to guess — read the error expression.
6. **Run the first real test with velocity blocked.** The whole path can be verified with the robot standing still.

**When this approach is good**

- Environments where a camera cannot be used (failure, lighting, dust)
- Targets you cannot attach a marker to
- Shaky localisation — a relative measurement is unaffected

**When it is bad**

- Several targets that must be **told apart** (a lidar cannot read an ID)
- Very small targets, or ones you must get very close to (the shape leaves the field of view)
- Surroundings full of structures at similar angles

Cameras and lidars are not substitutes; they **cover each other's failure modes.** A tag gives you an ID; a shape gives you millimetres without any light. Make both emit the same contract and you can swap between them as the situation demands. That is the most practical thing this exercise produced.
