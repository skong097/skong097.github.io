---
title: "The ROS 2 Autonomous Navigation Stack, End to End — Nav2 · Planner/Controller · AMCL · TF"
date: 2026-08-06
tags: ["ros2", "nav2", "planner", "controller", "amcl", "tf2", "localization", "costmap", "dds", "qos", "navigation", "rep-105"]
categories: ["ros2"]
summary: "ROS 2 has so many layers that the hardest part is often working out which layer your symptom belongs to. This is a single reference covering the whole stack from DDS up to Nav2, how the Nav2 servers fit together, why the planner and the controller are deliberately kept apart, why AMCL publishes map→odom instead of map→base_link, and the TF concepts and bring-up order that hold all of it up. Concepts only — nothing tied to a particular robot."
draft: false
ShowToc: true
TocOpen: true
---

Work with ROS 2 navigation for a while and the hard part stops being any single algorithm. It becomes **figuring out which layer the symptom you're staring at actually belongs to.** When the robot wobbles in front of its goal, is that controller tuning, unstable localization, or a transform arriving too late?

This post draws that map. It builds bottom-up — TF, localization, costmaps, planner and controller, then the BT Navigator — covering what each layer owns and why the seams sit where they do. It's a concept reference, not tied to any particular robot or project.

---

## 1. The whole ROS 2 stack

### 1-1. Layers

{{< figure src="/images/diagrams/ros2-stack-layers-en.svg" alt="The ROS 2 layered stack. From the bottom up: OS and hardware, DDS, the RMW layer abstracting the DDS vendor, rcl as the language-neutral C core, the rclcpp and rclpy bindings, and application frameworks such as Nav2, MoveIt2 and ros2_control on top. QoS and distributed discovery come up from the DDS layer, which is why there is no master process." >}}

The important part is the **bottom two rows**. There is no master process — no `roscore` equivalent. DDS's distributed discovery takes over that job, so nodes find each other whatever order you start them in. The price is that QoS is now exposed directly to you.

| Layer | What it does | Typical implementation |
|---|---|---|
| Application frameworks | Domain stacks | Nav2, MoveIt2, ros2_control, SLAM Toolbox |
| Client Library | Language bindings | `rclcpp`, `rclpy`, `rclrs` |
| rcl | Language-neutral C core | `rcl`, `rcl_action`, `rcl_lifecycle` |
| RMW | DDS vendor abstraction | `rmw_fastrtps_cpp`, `rmw_cyclonedds_cpp` |
| DDS | The actual middleware | Fast DDS (default), Cyclone DDS, Connext |
| OS / HW | Execution environment | Ubuntu, RTOS, MCU (micro-ROS) |

### 1-2. The four communication primitives

| Kind | Pattern | Used for | Example |
|---|---|---|---|
| Topic | pub/sub · async · N:N | Streaming data | `/scan`, `/odom`, `/cmd_vel` |
| Service | req/res · sync · 1:1 | Queries needing an answer now | `/clear_entirely_global_costmap` |
| Action | goal/feedback/result · cancellable | Long-running work | `/navigate_to_pose` |
| Parameter | (services underneath) | Runtime configuration | `max_vel_x` |

An action looks like its own primitive but is really a composite of **three services plus two topics** (goal / cancel / result services, feedback / status topics). That's why `ros2 topic list --include-hidden-topics` shows several topics per action.

### 1-3. QoS — the biggest trap coming from ROS 1

DDS QoS is exposed directly, and **if a publisher and subscriber have incompatible QoS they never connect at all.** This is the number one cause of "the topic shows up in `ros2 topic list` but my callback never fires."

| Policy | Values | Meaning |
|---|---|---|
| Reliability | `RELIABLE` / `BEST_EFFORT` | Retransmit or not. High-rate sensors are usually best_effort |
| Durability | `VOLATILE` / `TRANSIENT_LOCAL` | Whether late subscribers get past messages (= ROS 1's latched) |
| History | `KEEP_LAST(depth)` / `KEEP_ALL` | Queue policy |
| Deadline / Liveliness / Lifespan | — | Real-time and health checking |

By convention, sensor streams like `/scan` use `SensorDataQoS` (best_effort, depth 5), while `/map` and `/tf_static` use `transient_local`. Subscribe to those last two with default QoS and you will silently receive nothing.

### 1-4. Execution model

- **Node** — the unit that holds callbacks. Not one-to-one with a process.
- **Executor** — the loop that pulls callbacks and runs them. `SingleThreadedExecutor` (default, serialises callbacks) and `MultiThreadedExecutor`.
- **Callback Group** — `MutuallyExclusive` (serial within the group) or `Reentrant` (parallel). **Calling a service synchronously from inside another service callback deadlocks**, and splitting them into a Reentrant group is the standard fix.
- **Lifecycle Node** — a managed node with an `unconfigured → inactive → active → finalized` state machine. Every Nav2 server is one.
- **Composition** — load several nodes into one process and intra-process communication passes pointers instead of serialising. The difference is very visible with cameras and point clouds.

### 1-5. Build and tooling

```bash
colcon build --symlink-install
source install/setup.bash

ros2 node list
ros2 topic echo /scan
ros2 param get /controller_server max_vel_x
ros2 interface show nav_msgs/msg/Path
ros2 launch nav2_bringup navigation_launch.py
ros2 bag record -a
```

For diagnosis, `rqt_graph`, `rviz2`, `ros2 doctor` and the `tf2_tools` covered later are effectively always-on tools.

---

## 2. The Nav2 navigation stack

### 2-1. Nav2 is not one node

Nav2 is a set of **lifecycle nodes (servers)** with **plugins** loaded into them. It isn't a monolithic library, so when something breaks the first question is always "which server failed?"

| Server | Role | Typical plugins |
|---|---|---|
| **BT Navigator** | Top-level orchestrator; drives everything from a behavior tree | `navigate_to_pose.xml`, `navigate_through_poses.xml` |
| **Planner Server** | Global path generation | NavFn (A*/Dijkstra), Smac 2D · Hybrid-A* · State Lattice, Theta* |
| **Controller Server** | Path following + local avoidance | DWB, RPP (Regulated Pure Pursuit), MPPI, TEB, Graceful |
| **Smoother Server** | Post-processing the path | Simple, Savitzky-Golay, Constrained |
| **Behavior Server** | Recovery behaviours | Spin, BackUp, Wait, DriveOnHeading, AssistedTeleop |
| **Velocity Smoother** | Acceleration and jerk limits on `cmd_vel` | — |
| **Collision Monitor** | Last safety net; slows or stops on proximity | polygon / circle zones |
| **Waypoint Follower** | Multi-point tours with per-point tasks | WaitAtWaypoint, PhotoAtWaypoint |
| **Map Server** | Loading and saving the static map | — |
| **Lifecycle Manager** | Configure/activate ordering and supervision | — |

The Planner Server and Controller Server each load a plugin implementing `nav2_core::GlobalPlanner` and `nav2_core::Controller`. When the robot's kinematics change, you swap the plugin, not the server.

### 2-2. Data flow

{{< figure src="/images/diagrams/ros2-nav2-dataflow-en.svg" alt="Nav2 data flow. The BT Navigator receives a goal and calls the Planner Server, which produces a path from the global costmap; the Controller Server turns that path into cmd_vel while watching the local costmap. cmd_vel passes through the Velocity Smoother and Collision Monitor into ros2_control. Wheel encoders produce odometry, and AMCL compares the scan against the map to publish the map to odom transform." >}}

The easy thing to miss is the dashed line running from bottom-right back to top-left. **Without TF, the costmaps cannot place sensor data onto the map.** Break TF and the whole of Nav2 stops — §5 comes back to this.

### 2-3. Costmap 2D

The shared input for both planner and controller. Two separate instances run at once.

{{< figure src="/images/diagrams/ros2-costmap-layers-en.svg" alt="The Costmap 2D layer structure. The static map, laser scan, point cloud and filter masks feed into static_layer, obstacle_layer, inflation_layer and costmap_filter, baked in order to produce the final cost grid with values from 0 to 255." >}}

Layers are stacked bottom-up to produce the final cost.

```yaml
global_costmap:
  global_costmap:
    ros__parameters:
      plugins: ["static_layer", "obstacle_layer", "inflation_layer"]
      inflation_layer:
        plugin: "nav2_costmap_2d::InflationLayer"
        inflation_radius: 0.55
        cost_scaling_factor: 3.0
```

| Layer | What it does |
|---|---|
| Static | Bakes `/map` straight into the grid |
| Obstacle / Voxel | Marking from LaserScan and PointCloud, clearing by raytracing |
| Inflation | Exponentially decaying cost around obstacles — inflating by the robot radius so the **robot can be treated as a point** |
| Range | Ultrasonic and infrared |
| Denoise | Removes speckle cells |
| Costmap Filter | Keepout masks and per-zone speed limits |

Cost values follow a convention: `0` free, `1–252` has cost, `253` inscribed (collision with the robot's inscribed circle), `254` lethal, `255` unknown. The planner and controller see nothing but these numbers.

`inflation_radius` is less a tuning knob than a **declaration of how big the robot is**. Set it below the robot radius and paths hug walls; set it too high and the robot can't fit through doorways.

### 2-4. The behavior tree — Nav2's coordination layer

The XML the BT Navigator runs *is* Nav2's control flow. Stripped to its skeleton, the default tree (`navigate_to_pose_w_replanning_and_recovery.xml`) looks like this:

```xml
<RecoveryNode number_of_retries="6">
  <PipelineSequence>
    <RateController hz="1.0">
      <ComputePathToPose goal="{goal}" path="{path}"/>
    </RateController>
    <FollowPath path="{path}"/>
  </PipelineSequence>

  <SequenceStar>
    <ClearEntireCostmap/>
    <Spin spin_dist="1.57"/>
    <BackUp backup_dist="0.15"/>
    <Wait wait_duration="5"/>
  </SequenceStar>
</RecoveryNode>
```

The point of the next section is already visible here. `ComputePathToPose` (the planner) is wrapped in `RateController hz="1.0"` and only re-runs at **1 Hz**, while `FollowPath` (the controller) runs **continuously** in between.

---

## 3. Planner and controller

### 3-1. What each one is

{{< figure src="/images/diagrams/ros2-planner-controller-split-en.svg" alt="A six-axis comparison of the Planner Server and the Controller Server. The planner answers which way to go, sees the whole map, runs at 1 Hz and emits a Path. The controller answers what velocity to command now, sees a few metres, runs at 20 to 50 Hz and emits a Twist." >}}

**Planner (global planner)**

- Question: "**Which route** gets me from here to the goal?"
- Input: global costmap, current pose, goal pose
- Output: `nav_msgs/Path` — a sequence of coordinates
- Rate: once per goal, or replanning around 1 Hz
- Algorithms: grid and graph **search** — Dijkstra, A*, Hybrid-A*, State Lattice
- Cares about: completeness (find a path if one exists), optimality, avoiding global dead ends

**Controller (local planner)**

- Question: "**What velocity right now** keeps me on that path?"
- Input: local costmap, current pose and velocity, the path from the planner
- Output: `geometry_msgs/Twist` — one linear and one angular velocity
- Rate: 20–50 Hz
- Algorithms: trajectory sampling and **optimisation** — DWA, Pure Pursuit, MPC (MPPI)
- Cares about: kinematic and dynamic limits, obstacles that just appeared, smoothness

### 3-2. Why they are split

Six independent reasons.

**① Compute cost and required rate pull in opposite directions — the decisive one**

An A* search over a 100 m × 100 m grid takes tens to hundreds of milliseconds. You cannot run that at 50 Hz (a 20 ms budget). Conversely, a velocity command has to land within 20 ms to stop in front of something that just appeared. **No single algorithm satisfies both**, so the problem was cut into a slow-but-wide layer and a fast-but-narrow one.

**② The state spaces have different dimensions**

The planner works in `(x, y)` or `(x, y, θ)` — geometry. The controller adds `(v, ω, a)` — physics. Fold the dynamics into a global search and the dimensionality explodes.

**③ The information differs in freshness and in reach**

The global map is static information built days ago; the local costmap is sensor data from milliseconds ago. Deciding an emergency swerve from stale data is wrong, and planning a global route from live sensors alone means not knowing what's behind the wall and driving into dead ends. The split **lets each kind of information be used in the layer it suits.**

**④ Failure modes and recoveries differ**

- Planner failure = "there is no path at all" → clear the costmap, relax the goal
- Controller failure = "there is a path but I can't follow it" → request a replan, spin in place, back up

The behavior tree can respond differently to each precisely because they were separated in the first place.

**⑤ Freedom to mix plugins**

| Robot | Planner | Controller |
|---|---|---|
| Indoor differential drive | NavFn or Smac 2D | RPP or MPPI |
| Ackermann (car-like) | Smac Hybrid-A* | RPP with turning-radius limits |
| Omnidirectional | Smac 2D | MPPI (Omni) |

**⑥ Theoretical background**

This is a **hierarchical deliberative/reactive** architecture — the compromise between classical Sense-Plan-Act (smart but slow) and reactive architectures (fast but short-sighted). Robotics converged on it over decades; it isn't a Nav2 invention.

### 3-3. What the split costs

Separation isn't free. It creates **mismatch**. The planner emits a grid path that says "turn 90° in place, then go straight" — and an Ackermann robot cannot do that. Three mechanisms close the gap:

- **Kinematically feasible planners** — Smac Hybrid-A* only produces paths that respect the robot's minimum turning radius.
- **Smoother Server** — rounds the staircase of a grid path into curves.
- **MPPI** — treats the path as a **reference in a cost function** rather than points that must be hit, absorbing sections the robot can't follow exactly.

If the robot zigzags along its path, check whether **the path the planner produced was ever a shape this robot could follow** before reaching for controller gains.

---

## 4. AMCL — Adaptive Monte Carlo Localization

### 4-1. What it is

A particle filter that estimates **where the robot is on a map that already exists.** It does not build the map — that's SLAM's job.

- **Monte Carlo Localization** — scatter thousands of **particles** as pose hypotheses and let only the ones consistent with the sensor survive.
- **Adaptive** — **KLD-sampling**. When particles converge (confidence up) the count shrinks; when they spread (uncertainty up) it grows. This is the key CPU saver.

| Direction | Items |
|---|---|
| Input | `/scan` (LaserScan), `/map` (OccupancyGrid), the `odom→base_link` transform, `/initialpose` |
| Output | **the `map→odom` transform**, `/amcl_pose` (PoseWithCovarianceStamped), `/particle_cloud` |

### 4-2. Why `map→odom` and not `map→base_link`

{{< figure src="/images/diagrams/ros2-amcl-cycle-en.svg" alt="The two essentials of AMCL. The top panel shows transform ownership: AMCL publishes map to odom as a drift correction while wheel odometry publishes odom to base_link continuously, and because a frame has one parent AMCL cannot publish map to base_link directly. The bottom panel shows one particle filter cycle of Predict, Update and Resample." >}}

This is the crux of understanding AMCL.

In a TF tree **a frame has exactly one parent.** `odom→base_link` is already published by wheel odometry — high rate, continuous, and accumulating drift. If AMCL also published `map→base_link`, `base_link` would have two parents and the tree would break.

So AMCL publishes only the correction — **"how far wrong odometry has drifted"** — as `map→odom`.

`map→base_link` then falls out automatically as the composition of the two. The design buys odometry's **continuity** (which control needs) and global **accuracy** (which navigation needs) at the same time.

### 4-3. The cycle

1. **Predict (motion update)** — move every particle by the odometry delta, spreading them with `alpha1`–`alpha5` noise.
   - `alpha1` rotation→rotation, `alpha2` translation→rotation, `alpha3` translation→translation, `alpha4` rotation→translation
2. **Update (measurement update)** — for each particle, compute the probability of observing this scan from that pose and weight accordingly.
   - `likelihood_field` — precomputed distance field to map obstacles. Fast, and the **recommended default**
   - `beam` — a per-ray physical model (hit/short/max/rand). More accurate but slower and prone to local minima
3. **Resample** — redraw proportional to weight, with KLD deciding the count. Not every step — every `resample_interval`.

**The trigger matters.** A cycle only runs after the robot has moved more than `update_min_d` (e.g. 0.25 m) or `update_min_a` (e.g. 0.2 rad). Standing still, nothing updates — this prevents particles from artificially converging while stationary.

### 4-4. Key parameters

```yaml
amcl:
  ros__parameters:
    min_particles: 500
    max_particles: 2000

    update_min_d: 0.25            # move this far before the filter updates
    update_min_a: 0.2
    resample_interval: 1

    laser_model_type: "likelihood_field"
    laser_likelihood_max_dist: 2.0
    laser_max_range: 12.0
    max_beams: 60                 # downsample rather than use every ray

    z_hit: 0.5                    # measurement model mix (z_hit + z_rand ≈ 1)
    z_rand: 0.5
    sigma_hit: 0.2

    robot_model_type: "nav2_amcl::DifferentialMotionModel"
    alpha1: 0.2
    alpha2: 0.2
    alpha3: 0.2
    alpha4: 0.2

    transform_tolerance: 1.0      # how far into the future to post-date the transform
    set_initial_pose: true
    tf_broadcast: true            # false stops it publishing map→odom
```

`tf_broadcast: false` is for when something else owns `map→odom` — an external positioning system, say — and you want AMCL kept around only for its pose estimate.

### 4-5. Services

```bash
# Global reinitialisation — scatter particles across the whole map again
ros2 service call /reinitialize_global_localization std_srvs/srv/Empty

# Force one update while stationary
ros2 service call /request_nomotion_update std_srvs/srv/Empty
```

### 4-6. Limits

- **Kidnapped robot** — pick the robot up and move it, and the already-converged particle cloud cannot recover on its own. Reinitialise manually with the service above.
- **Featureless environments** — long corridors, large halls. Scans look the same everywhere, so position along the corridor is unobservable.
- **Map/reality mismatch** — rearranged furniture, crowds. The weighting falls apart.
- **Dynamic obstacles** — AMCL has no special handling for them.

Alternatives and complements:

- `slam_toolbox` in localization mode — scan-matching based, and able to update the map.
- `robot_localization`'s EKF/UKF — **not a replacement** for AMCL. It fuses IMU, wheels and GPS to produce a **better `odom` for the layer below**. Different level of the stack.

---

## 5. TF (tf2)

### 5-1. The problem it solves

A robot has dozens of coordinate frames — map, body, lidar, camera, every joint. Multiplying "the point the lidar saw, into map coordinates" by hand every time is unmanageable. Worse, **transforms change over time as joints move**, and every sensor carries a different timestamp.

tf2 solves this with **distributed publishing, a time buffer, and automatic interpolation.**

### 5-2. Concepts

{{< figure src="/images/diagrams/ros2-tf-bringup-en.svg" alt="The TF frame chain and bring-up order. AMCL or SLAM publishes map to odom, the base driver publishes odom to base_link, and URDF with robot_state_publisher publishes the sensor frames over tf_static. Below, the five bring-up steps with the command that verifies each." >}}

**① Tree structure** — one parent per frame, no cycles. Different nodes may own different edges, and tf2 assembles them globally.

**② REP-105 frame conventions**

| Frame | Character |
|---|---|
| `map` | Globally fixed. **No drift, but may jump discontinuously** (the moment AMCL corrects) |
| `odom` | **Continuous** and smooth. **But accumulates drift over time** |
| `base_link` | The robot body reference point |
| `base_footprint` | Ground projection (optional) |

The reason `map` and `odom` are separate frames is contained entirely in that table. Control needs continuity — a pose that jumps makes controllers convulse — and navigation needs global accuracy. Splitting them into two frames lets each consumer take what it needs.

**③ REP-103 units and axes** — SI units, right-handed frames, **x forward, y left, z up**. Angles in radians.

**④ Two kinds of transform**

| | Topic | QoS | Used for |
|---|---|---|---|
| Dynamic | `/tf` | volatile · high rate | Joints, odometry, localization |
| Static | `/tf_static` | **transient_local (latched)** | Sensors bolted in place |

Static transforms are published once, and late-starting nodes still receive them thanks to `transient_local`. Get the subscriber QoS wrong and you receive nothing.

**⑤ Interpolation and extrapolation** — pass a timestamp to `lookupTransform` and tf2 interpolates between buffered samples. Ask outside the buffer and you get an `ExtrapolationException`. Passing `TimePointZero` means "the latest available".

### 5-3. Code

Publishing (dynamic):

```cpp
tf2_ros::TransformBroadcaster br(this);

geometry_msgs::msg::TransformStamped t;
t.header.stamp    = now();
t.header.frame_id = "odom";       // parent
t.child_frame_id  = "base_link";  // child
t.transform.translation.x = x;
t.transform.rotation = tf2::toMsg(q);
br.sendTransform(t);
```

Looking up:

```cpp
tf2_ros::Buffer buffer(get_clock());
tf2_ros::TransformListener listener(buffer);

// (target, source, time, timeout)
auto tf = buffer.lookupTransform("map", "base_link",
                                 tf2::TimePointZero, 100ms);

geometry_msgs::msg::PointStamped out;
buffer.transform(in_point, out, "map", 100ms);
```

`lookupTransform("map", "base_link", ...)` gives you **the transform that takes base_link coordinates into map coordinates**. The `(target, source)` argument order stays confusing forever; it's worth a comment at every call site.

**Automatic publishing from URDF** — `robot_state_publisher` reads the URDF, subscribes to `/joint_states`, and publishes every link transform for you. Fixed joints go out on `/tf_static`, revolute and prismatic joints on `/tf`. Put sensor mount positions in the URDF rather than broadcasting them by hand.

### 5-4. Bring-up procedure

Bring it up in order, **verifying each step**. A problem at a later step is usually a problem from an earlier one.

**Step 1 — URDF and static TF**

```bash
ros2 launch <robot>_description rsp.launch.py   # robot_state_publisher
ros2 run tf2_tools view_frames                  # writes frames.pdf
```

Verify: every sensor frame such as `base_link → laser_link` appears, and it is **one connected tree**. Several disconnected fragments means a missing URDF joint.

**Step 2 — base driver (`odom→base_link`)**

```bash
ros2 launch <robot>_bringup base.launch.py
ros2 run tf2_ros tf2_echo odom base_link
```

Verify: push the robot by hand or drive it with teleop, watch the values follow, and confirm the **directions match REP-103** (x increases when driving forward). A sign flip here corrupts everything downstream.

**Step 3 — sensor drivers**

```bash
ros2 topic echo /scan --field header.frame_id
```

Verify: the `frame_id` matches the URDF link name exactly. Watch for typos and for a leading `/` (ROS 2 does not use one).

**Step 4 — localization (`map→odom`)**

```bash
ros2 launch nav2_bringup localization_launch.py map:=my_map.yaml
ros2 run tf2_ros tf2_echo map odom
```

Verify: set the initial pose with RViz's 2D Pose Estimate, drive the robot, and watch `/particle_cloud` converge.

**Step 5 — Nav2**

```bash
ros2 launch nav2_bringup navigation_launch.py
```

Verify: `map → odom → base_link → laser_link` connected without a break, checked in the RViz TF display.

**Always-on diagnostics**

```bash
ros2 run tf2_tools view_frames                 # whole tree as PDF, with rates and publishers
ros2 run tf2_ros tf2_echo <parent> <child>     # live values
ros2 run tf2_ros tf2_monitor <parent> <child>  # delay and rate statistics
ros2 topic hz /tf
```

### 5-5. Five common failures

| Symptom | Cause | Fix |
|---|---|---|
| `Lookup would require extrapolation into the future` | Clocks disagree between nodes, or the stamp is too old | In simulation set `use_sim_time:=true` **on every node**. On real hardware, sync with chrony/NTP |
| `"X" passed to lookupTransform does not exist` | frame_id typo, URDF not loaded, or a leading `/` | Check the real names with `view_frames` |
| TF jumps or oscillates | **Two nodes publishing the same child frame** (e.g. odometry and an EKF both publishing `odom→base_link`) | Keep one. `view_frames` output names the publisher |
| Static transforms never arrive | QoS durability mismatch | Subscribe with `transient_local` |
| Robot wobbles near the goal | `transform_tolerance` too small, TF rate too low | Raise the rate — odometry wants 30–50 Hz minimum |

---

## 6. Tying it together

{{< figure src="/images/diagrams/ros2-stack-overview-en.svg" alt="A map tying the whole article together. The vertical pillar on the left is the ROS 2 core providing nodes, topics, actions, QoS and lifecycle. To its right the stack builds bottom-up: TF, AMCL localization, the costmap, planner and controller side by side, and the BT Navigator on top." >}}

- **TF** underpins everything. The base driver publishes `odom→base_link` (continuous, drifting); AMCL publishes `map→odom` (corrective, may jump).
- On top of that, the **costmap** uses TF to project sensor data into map coordinates and bake a cost grid.
- The **planner** reads that grid slowly and widely to answer "which route"; the **controller** reads it fast and narrowly to answer "what velocity".
- The **BT Navigator** coordinates the two and calls recovery behaviours when they fail.
- All of it runs on the **ROS 2 core** — nodes, topics, actions, QoS, lifecycle.

The most practically useful conclusion is that **debugging follows the same order as the diagram.** Symptoms appear high in the stack; causes usually sit low. Before touching controller gains because the robot trembles in front of its goal, work up from the bottom:

1. Is the TF tree connected, and published fast enough?
2. Is `map→odom` stable — has `/particle_cloud` converged?
3. Does `inflation_radius` match the actual robot?
4. Is the planner's path a shape this robot can physically follow?
5. *Then* tune the controller.
