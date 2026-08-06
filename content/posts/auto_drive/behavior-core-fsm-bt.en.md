---
title: "We Designed the Behavior Core as Two Layers of FSM + BT, and Built Half of It"
date: 2026-08-06
tags: ["auto-drive", "behavior-core", "fsm", "behavior-tree", "state-machine", "nav2", "ros2", "apriltag", "pose-regulation", "estop", "yasmin", "wasab"]
categories: ["robotics"]
summary: "The robot's behavior skeleton was designed as two layers: a top-level FSM owning the mode, with a BT executing and recovering inside each state. The research conclusion was YASMIN + BehaviorTree.CPP v4. We used neither, and never built the coordination layer at all. What exists is two pure-Python FSMs (patrol and docking) plus an E-STOP latch at the last stage before the motors, with navigation replanning and recovery delegated to the Nav2 bt_navigator. This post records which field failures produced those decisions — and why the reasoning that overturned the research conclusion was never written down."
draft: false
ShowToc: true
TocOpen: true
---

We call the layer that decides "what the robot is doing right now" the **behavior core**.
It is not a single algorithm but a skeleton. The requirements came down to five lines.

| Requirement | Meaning |
|---|---|
| Mode / state selection | idle · patrol · teacher-assist |
| Automatic and manual transitions | accept both perception events and GUI commands |
| Per-state mission execution | what is performed and recovered in that state, and how |
| Emergency stop | immediate halt in any state, during any mission |
| Multi-robot supervision | keep state in sync with the console |

The conclusion first. **The design had two layers; only the lower one was built.**
The patrol FSM and the docking FSM exist and are field-verified. The layer above them that owns the mode
was never built. YASMIN and BehaviorTree.CPP v4 — the 2026-06-29 research conclusion — are **both absent from the repository.**

This post is about how that half got built, and why the other half is empty.

---

## 1. Why Two Layers

Doing everything with one FSM makes the transition table explode. Promote every combination of
"a goal aborted mid-patrol, the battery is low, a robot is ahead, and relocalization is needed"
into a state, and the state count grows multiplicatively.

Doing everything with one BT leaves **no clear owner for the system-level question of "which mode are we in?"**
A BT re-evaluates from the root every tick, so there is no natural place to hold a long-lived exclusive mode.

So we split the roles.

- **FSM** — "which state are we in, and when" (mode transitions, operator intervention, emergency stop)
- **BT** — "how is it performed and recovered in that state" (replanning, retries, fallback)

Four things informed this: FSM–BT comparison studies (BT maintainability wins as task complexity grows),
a BT survey (modularity and reusability), Flexible Behavior Trees (a hybrid where HFSM states load and run BTs),
and the largest example in the field — **Nav2 itself is built on BehaviorTree.CPP.**

That last item later renders half of this design moot. More on it below.

---

## 2. The Layer Map — How Far We Got

{{< figure src="/images/diagrams/autodrive-behavior-core-layers-en.svg" alt="Behavior core layer map. The top-level B0 FSM is not built; the agent only relays a mode string. Below it, only the patrol FSM and the docking FSM are implemented and verified. The traffic arbiter is a rule engine rather than an FSM, navigation is delegated to the Nav2 bt_navigator, and E-STOP latches the last stage before the motors from outside the FSM layers." >}}

| Layer | Role in the design | Status |
|---|---|---|
| **B0 top-level FSM** | owns mode transitions and operator intervention | **not built** — replaced by the agent's mode-string relay plus each node deciding on its own |
| **Lower execution state machines** | actually run patrol and docking, and handle their failures | **built and field-verified** — two pure FSMs |
| **B1 BT executor** | perform and recover the mission inside a state | **delegated to the Nav2 `bt_navigator`** (nothing custom) |
| **Global overlay** | a stop that wins in any state | built — outside the FSM, latched at the last stage before the motors |

The dashed line is not coordination but a **string relay**. The agent receives `/wasab/cmd_mode` and
republishes it into the local domain; what to do with that string is then decided separately by each node.
The two FSMs do not know about each other, and nothing arbitrates between them.
No unified behavior-core node was ever written.

---

## 3. "Holds State" Is Not "Is a State Machine"

The first thing we did while writing this up was draw that distinction. Several modules hold something
state-like, but only two have **explicit state labels and a transition table.**

| Module | Explicit states / transitions | Classification |
|---|---|---|
| `patrol_planner.PatrolPlanner` | `PATROL` ↔ `YIELD`, returns `WAIT_EDGE` | **FSM** |
| `state_machine.py` (docking) | `IDLE` → `NAV_TO_APPROACH` → … → `DONE` / `FAILED` | **FSM** |
| `relocalize_logic.RelocalizeState` | an `_armed` boolean plus cooldown and travel-distance conditions | two-state **latch** |
| `traffic_rules.Arbiter` | no state labels. `GRANTED/QUEUED/REJECTED` is not the arbiter's state but **a response to a request** | **rule engine + occupancy table** |
| E-STOP | boolean latch (last stage before the motors) | overlay |
| Modes `idle`/`patrol`/`assist` | string relay, no transition logic | overlay |

The traffic arbiter matters most here. `GRANTED / QUEUED / REJECTED / REVOKED` is taken verbatim from
the VDA 5050 3.0.0 state model, but that model describes **a response to an individual request, not the arbiter's own state.**
The arbiter has no transition table; it recomputes the occupancy table from scratch every tick and only judges.
Structurally, it is a rule engine. The algorithm itself is written up separately in
[Dropping Coordinates and Counting Hops](/posts/auto_drive/다중로봇-통행중재-홉기반-점유와-실측규칙/) *(Korean)*.

---

## 4. The Patrol FSM — `PatrolPlanner`

A pure module with zero ROS dependencies. Three states.

| State | Meaning | Transition |
|---|---|---|
| `PATROL` | driving the waypoint loop | another robot inside `yield_radius` → `YIELD` |
| `YIELD` | hard stop + goal cancel | everyone outside `clear_radius` → `PATROL` (**hysteresis**) |
| `WAIT_EDGE` | waiting for a traffic grant | grant (`go`) → advance to the next node |

Three rules we held to.

- **The patrol robot has the lowest priority.** The arena is narrow, so it never drives around anything —
  it only stops. Generating an avoidance trajectory where there is no room to avoid drives you into a wall.
- **The `gate` only means anything on arrival at a node.** A blocked segment is never entered in the first place (fail-closed).
  Not entering is always cheaper than cancelling after entering.
- **The start node is the nearest node to the current pose.** Patrol can be triggered from anywhere and still join the ring.

The hysteresis is enforced in the constructor as `clear_radius ≥ yield_radius`. With equal radii the state
chatters at the boundary, and a chattering state machine issues `goal cancel` and `goal republish` several times a second.

---

## 5. The Docking FSM — `state_machine.py`

Eight states plus `ESTOP`. Also a pure module.

{{< figure src="/images/diagrams/autodrive-docking-fsm-states-en.svg" alt="The eight-state docking FSM flow and its control ownership. During NAV_TO_APPROACH and NAV_CANCELING, Nav2 owns cmd_vel and the precision parking node is forbidden from publishing; during TAG_SERVO_ALIGN and SETTLE the parking node owns control via pose regulation." >}}

| State | Meaning |
|---|---|
| `IDLE` | waiting for a goal |
| `NAV_TO_APPROACH` | Nav2 approach drive (including staging-waypoint routing) |
| `NAV_CANCELING` | waiting for the Nav2 goal cancel |
| `SEARCH_TAG` | searching for the target AprilTag (the detector subprocess starts here) |
| `TAG_SERVO_ALIGN` | PID alignment on tag-pose error |
| `SETTLE` | confirming the tolerance holds |
| `DONE` / `FAILED` | terminal states |
| `ESTOP` | E-STOP latch. **Set by `precision_parking_node`, not by the pure module** |

### Ownership Split

`NAV_TO_APPROACH` and `NAV_CANCELING` are the segments where Nav2 owns `/cmd_vel`,
so the precision parking node is **forbidden from publishing at all** during them (`_NO_PUBLISH`).
Two controllers writing to the same topic makes the robot oscillate. The state label *is* the ownership marker.

### `TAG_SERVO_ALIGN` Is Not P Control

Plain proportional control here would have spun the robot in place forever while laterally offset.
A diff-drive has no lateral velocity, so **turning in place cannot cancel a left-right offset.**
Hence **pose regulation** in polar coordinates (ρ, α, β): the robot arcs onto the tag normal and
converges in the order `ey` → 0, `eyaw` → 0, `ex` → 0.

Yaw needed one more layer. A planar marker's pose solution ±flips as you approach head-on,
so `eyaw` alternated between `+0.09` and `−0.09` and `wz` oscillated. A `YawFilter`
(circular mean of the last 6 yaw values) fixed it by filtering **yaw only, leaving x/y raw**.
Filtering the translational error too would just slow convergence.

**Result** — head-on stops at 15 cm on four tags (7 · 8 · 9 · 10), physically verified at
`ex` **6–12 mm** and `ey` **< 4 mm** (2026-07-11). The controller derivation and tuning are in
[Close with Nav2, Exact with AprilTag PID](/posts/auto_drive/nav2-apriltag-pid-정밀도킹-성공기록/) *(Korean)*.

---

## 6. The Global Overlay — E-STOP

Stopping was deliberately not made a state transition. It has to work from any state, which would mean
adding a stop transition to every state — the transition-table explosion again.
So it was pulled out into a path that **never touches the FSM layers.**

| Step | What happens |
|---|---|
| 1 | web app stop button → `POST /api/cmd/estop` |
| 2 | backend publishes `/wasab/estop` (console domain 50) |
| 3 | `estop_relay` — an **independent process** on the robot (systemd), republishes into the robot domain |
| 4 | `bringup` (base) latches the motors to zero and ignores `cmd_vel` from then on |

Step 4 is **the only place in this project where a robot file was modified**: a **4-line** latch in `bringup.py`
(subscribe to estop, plus a guard at the top of `twist_callback`). Only the last stage before the motors
can reliably stop the robot from any state, so this one exception was made — and since `bringup.py` differs
per robot, we inserted a snippet instead of overwriting the file.

Keeping the relay as a **process fully separate from the agent** was equally deliberate.
It was the only way to satisfy both constraints at once: don't touch the source of a stably running agent,
and keep the stop alive even if the agent dies.

The parsers were split too. `parse_estop` is **permissive** and stops on anything plausible;
`parse_estop_msg` is **strict** and returns `None` on a parse failure.
A stop should trigger even when the message is ambiguous; a release must never be triggered by a corrupted one.

---

## 7. What Went Wrong

### Case 1. A powered-off robot's ghost froze patrol forever

- **Problem** — after another robot was switched off, the patrol robot never left `YIELD`. Nothing was nearby.
- **Approach** — the `YIELD` condition is "another robot within the radius." If nothing is there and the
  condition is still true, **the data being read is stale.** The heartbeat cache still held the last pose of a terminated robot.
- **Fix** — a TTL on other-robot poses (`HEARTBEAT_TTL_S = 1.5`). Poses older than 1.5 s are excluded from the decision.

### Case 2. The robot yielded to itself

- **Problem** — with only one robot running, it dropped straight into `YIELD` and never moved.
- **Approach** — the code building the other-robot list excludes its own id from the heartbeats,
  but with `PATROL_ROBOT_ID` unset the id defaults to 0 and **its own heartbeat reads as another robot.**
  The distance to itself is 0, so the yield condition always holds.
- **Fix** — fail loudly at startup when `robot_id <= 0`.
  A missing setting silently turning into wrong behavior is the worst outcome.

### Case 3. Skipping blocked nodes caused a collision in the middle of the arena

- **Problem** — to raise throughput we added skipping of blocked nodes. The index advanced by 2,
  and the robot drove **diagonal edges that do not exist on the ring**, like `tag7→S` and `S→tag10`.
  The arbiter did not know those paths, nothing could block them, and a collision happened mid-arena.
- **Approach** — the starting clue was that the collision was not on the ring. The arbiter's occupancy model
  only knows **the ring graph's edges.** If a robot drives a path outside the graph, there is no way to represent its occupancy at all.
- **Fix** — skipping was removed. **A behavior that leaves the decidable state space cannot be made safe.**

### Case 4. Chasing throughput produced a rear-end collision

- **Problem** — letting a robot on an edge lock only its nearer endpoint cut occupancy from 1.79 to 1.00 nodes.
  The moment the lead robot crossed the middle of a long edge the rear node opened, the follower closed to
  **0.7 m** behind, and they collided near tag10.
- **Approach** — the optimization's premise ("past the middle of an edge, the node behind is clear") is physically false.
  A robot is not a point and the corridor is narrow.
- **Fix** — reverted. Throughput optimization is only valid when there is physical slack.

### Case 5. Only docking got stuck — same Nav2, and patrol passed through

- **Problem** — the robot repeatedly wedged on the `tag9→tag7` docking approach.

  ```text
  collision ahead                                        100+ times
  Controller patience exceeded → follow_path Aborting     13 times
  costmap clear · spin · backup · wait                    every recovery failed
  → infinite abort loop, error_code 104
  ```

  And yet **patrol passed the same segment fine.**
- **Approach** — we first treated it as dynamic-obstacle avoidance, then redefined it after a user remark:
  *"that segment has always been a chronic wedge point, boxes or no boxes."*

  Both paths use **the same `navigate_to_pose`** — same planner, same controller, same goal checker.
  So it was not a Nav2 parameter difference. The difference was **routing.**

  | | Patrol (passes) | Docking (wedges) |
  |---|---|---|
  | goal publishing | sequential waypoints tag9 → **tag10 (northernmost)** → tag7 | **single direct goal** → tag7 approach |
  | progression | `reach_tol 0.15` **pass-through** (never settles onto a tight pose) | **waits for exact arrival** at the approach pose |

  And the approach pose was not arbitrary. It is a constrained spot that has to satisfy
  **tag visibility plus straight-line entry** for the PID precision parking, so it could not be replaced
  by brushing past it the way patrol does.
- **Fix** — without changing a single robot file, we published sequential goals from the PC to prove out the staging route first.

  | leg | segment | result |
  |---|---|---|
  | 1 | tag9 → staging tag10 | SUCCEEDED |
  | 2 | staging → north of tag7 | SUCCEEDED (**this is where the direct goal aborted**) |
  | 3 | north of tag7 → actual approach | SUCCEEDED, `error_code 0`, patience · abort · spin/backup all **0** |

  Only then was it implemented minimally as `pre_waypoints`. **Not one FSM state changed** —
  `NAV_TO_APPROACH` simply hands over goals in sequence.
- **Takeaway** — when the same stack clears one path and cannot clear another,
  look at **the shape of the goal you are giving it** before you look at stack parameters.

### Case 6. Agent CPU was blocking docking — and "TF is expensive" was the wrong hypothesis

- **Problem** — docking from the console button failed with the agent on and succeeded with it off.
  The agent process was eating nearly 30% CPU and starving the Nav2 planner.
- **Approach** — the hypothesis was "TF math is expensive." Instead of guessing we **isolated a single variable and measured.**
  On a freshly booted spare robot we ran bringup only (leaving `/tf` as the sole subscribed topic with a publisher)
  and added exactly one agent on top. Then `top -H` for per-thread and `py-spy` for per-function profiles.

  | Function | Share |
  |---|---|
  | `_wait_for_ready_callbacks` (rclpy executor) | **≈ 85 %** |
  | `lookup_transform` / `can_transform` (the actual TF math) | **≈ 0 %** |

  The hypothesis was wrong. TF math was free. The real cost was **the rclpy executor rebuilding the wait-set
  in Python on every `spin_once`**, and what woke it 35 times a second was the **35 Hz `/tf`**.
  Getting `map→base` via TF forces you to consume `odom→base`, which bringup publishes at 35 Hz.
- **Fix** — we checked what the pose was actually **for**. It only feeds the console marker (consumed at 2 Hz)
  and **is not used by docking control at all.** So the pose source moved from TF to a `/amcl_pose` subscription,
  dropping the wake rate from 35 Hz to the AMCL publish rate.

  **robot_ctx CPU 30% → 8%**, verified by completing a console-button dock from tag7 to tag9.
- **Takeaway** — "looks expensive" and "is expensive" are different things. Do not optimize without a profile.
  The full story is in [The Agent Bridging Two ROS Domains, and CPU Tuning](/posts/auto_drive/wasab-로봇함대-두-도메인을-잇는-agent와-cpu튜닝/) *(Korean)*.

### Case 7. Relocalization timed out quietly — with a different cause each time

- **Problem** — AprilTag relocalization kept timing out, the cause differed every time, and every time we suspected the code.
- **Approach and fix** — none of the three were the code.

  | Round | Symptom | Actual cause | How it was identified |
  |---|---|---|---|
  | ① | relocalization timeout | `localization` launched with `use_composition:=True` | when composed, the `/initialpose`→AMCL path fails. `False` is required |
  | ② | timeout (IP, config and sources all correct, matching md5) | **the tag was too large for the detector's 640×480 crop FOV and its top was cut off** | confirmed when 1280 decodes but the 640 preview does not. Move the robot back |
  | ③ | timeout even though the detector decoded `tag_id` fine | `map_name` in `relocalizer.yaml` did not match the current map | the log says "map mismatch, skipping" outright |

- **Takeaway** — when the verified things (sources, md5) are identical, go look for **the thing that differs.**
  Suspecting the source first burns time. And **a "quiet skip" must always log** — ③ was caught instantly because it did.

### Case 8. After an emergency stop, patrol never worked again

- **Problem** — restarting patrol after an emergency stop did nothing. Nav2 was healthy and `/cmd_vel` carried values.
- **Approach** — commands going out while the wheels do not turn points at **the last stage.**
  E-STOP is a **latch** where base ignores `cmd_vel`. It was working exactly as designed; nobody had sent the release.
- **Fix** — an explicit **release** button in the frontend that publishes `active:false`,
  and a line in the operations doc: "patrol stays dead until you release the stop."
  A latch **looks like a bug whenever there is no release UI**, even when it behaves exactly as designed.

### Case 9. When Nav2 rejected or aborted a goal, the state machine froze

- **Problem** — if Nav2 rejected or aborted a goal, the patrol node stalled instead of doing anything next.
- **Approach** — the state machine published a goal and then **never tracked the result as state.** It assumed success.
- **Fix** — track goal state and **retry after a 2 s backoff** on reject/abort (`GOAL_RETRY_BACKOFF_S = 2.0`).
  Immediate retries repeat the same failure and only burn CPU.
  If Nav2 gives no response at all for 20 s, it raises `goal_pending_stuck` as a **pause plus an operator alert**.
  Calling a human beats spinning quietly on infinite retries.

### Case 10. The state machine was fine — only the robot would not move

- **Problem** — all of Nav2 was healthy, `/cmd_vel_nav` carried values, and the robot did not move.
- **Approach** — `/cmd_vel_nav` had values and `/cmd_vel` was empty. What sits between those two topics is the `velocity_smoother`.
- **Fix** — the `velocity_smoother` lifecycle was `inactive`. Activating it fixed it (no reboot needed).
- **Takeaway** — "Nav2 is running but the robot won't go" → **check the `velocity_smoother` lifecycle first.**

---

## 8. We Did Not Use the Research Conclusion

The 2026-06-29 research conclusion was **"a YASMIN-based top-level FSM (B0) plus per-state BT executors on
BehaviorTree.CPP v4 (B1),"** complete with a plan to gate it behind a two-state YASMIN PoC.
The actual implementation uses **neither.**

| Item | Research conclusion (2026-06-29) | Actual implementation |
|---|---|---|
| B0 top-level FSM | **YASMIN** (ROS 2 native FSM, web viewer) | in-house pure Python FSMs (`patrol_planner.py`, `state_machine.py`) |
| B1 BT executor | **BehaviorTree.CPP v4** + ROS 2 action wrapper leaves | not built. Navigation delegated to the Nav2 `bt_navigator` |
| Unified behavior-core node | top-level FSM loads / halts a BT per state | none. Per-feature state machines, distributed |

The repository has **no dependency at all** on `yasmin`, `behaviortree`, or `py_trees` (exhaustive grep, 0 hits).

> **The table below is a reconstruction after the fact.** The reasoning that overturned the research
> conclusion was never written down — there is no worklog and no spec in the repository recording *why* it went unused.
> What follows was reverse-engineered from the current code and measurements, and is **not a record of the decision as it was made.**

| Reason, reconstructed | Detail |
|---|---|
| **Nav2 is already a BT** | Navigation replanning and recovery (`navigate_to_pose_w_replanning_and_recovery`) already run in a proven BT. Layering our own BT on top puts recovery logic in **two places** |
| **There are few states** | Patrol has 3, docking has 8 (+`ESTOP`). That is not a transition table on the verge of exploding. The scale where BT's advantage — modularizing complex missions — pays off is not here yet |
| **CPU budget** | On the RPi 4, 20% idle headroom was the threshold for completing a run. There was no room for another executor |
| **Verification cost** | The PoC gate was validating BehaviorTree.ROS2 build and deployment stability on Jazzy. That time went into **field-critical features** like traffic arbitration and emergency stop instead |

The first row is the thread left hanging at the end of §1. **The conclusion "use a BT" was already half-realized.**
The moment we called Nav2 as an action, we were running on top of somebody else's BT,
and adding our own executor above it was not a new capability — it was **a duplicate layer.**

None of which proves what was actually decided at the time. Two facts remain: there was a research conclusion,
and it is not in the code. Nothing in between was written down.
**It is more accurate not to say "we implemented it as designed."**

---

## 9. What Survived as Design Principles

The layering changed, but the rules we reached for repeatedly while building the two FSMs did not.

| Principle | Where | Why |
|---|---|---|
| **Pure-function logic split out** | FSMs = `patrol_planner.py` · `state_machine.py`, rule engine = `traffic_rules.py`, parsers = `estop.py` · `commands.py` | test every transition table and decision rule without ROS or a robot. Field time is expensive, so logic errors get caught on the ground |
| **Hysteresis** | enter YIELD on `yield_radius`, leave on `clear_radius` (the larger one) | stops the state chattering at the boundary. `clear ≥ yield` is enforced in the constructor |
| **fail-closed vs. fail-open, deliberately** | patrol = no grant, no motion / docking = proceeds even without the arbiter | a stopped patrol is safe; an interrupted precision park is not |
| **Timeout → pause + alert** | `YIELD_TIMEOUT_S`, `EDGE_WAIT_TIMEOUT_S`, 20 s of goal silence | hand it to a human instead of waiting forever. **A silent stall is the worst failure mode** |
| **Retry backoff** | `GOAL_RETRY_BACKOFF_S = 2.0` on Nav2 goal reject/abort | immediate retries repeat the same failure and only burn CPU |
| **Split strict and permissive parsers** | `parse_estop` (permissive, stops) / `parse_estop_msg` (strict, `None` on failure) | accept a stop broadly; never release on a corrupted message |
| **Watchdog on yourself** | `OWN_HB_TIMEOUT_S = 8.0` | a robot the supervisor cannot see does not drive itself |

That last watchdog pairs with the traffic arbiter. The arbiter erases a robot's occupancy after 15 s of silence,
and if the robot keeps driving after that erasure, **a robot invisible to the arbiter is occupying the corridor.**
So the patrol node subscribes to its own heartbeat and stops first, at **8 s**.
The whole trick is setting the threshold below 15.

---

## 10. Limits

| Item | Detail |
|---|---|
| **B0 top-level FSM not built** | The lower execution state machines are built and verified, but there is no coordination layer above them owning mode transitions. Modes are covered by the agent's string relay plus each node deciding on its own. **This layer becomes the first thing you need once robots or modes multiply** |
| **No in-house BT executor** | see §8 |
| **Assist-task integration** | the `assist` mode wire value exists, but state integration with the K1/K2/K3 tasks is incomplete |
| **Deadlock recovery** | only a design draft exists (Nav2 `BackUp`, limited to 2 attempts) for freeing a wedged robot by reversing the follower. Not built |

---

## Code Map

| Area | File |
|---|---|
| Patrol FSM (pure) | `wasab_navigation/wasab_patrol/wasab_patrol/patrol_planner.py` |
| Patrol node | `wasab_navigation/wasab_patrol/wasab_patrol/patrol_node.py` |
| Docking FSM (pure) | `wasab_navigation/wasab_docking/wasab_docking/state_machine.py` |
| Precision parking node | `wasab_navigation/wasab_docking/wasab_docking/precision_parking_node.py` |
| E-STOP parser (pure) | `wasab_navigation/wasab_docking/wasab_docking/estop.py` |
| E-STOP relay | `scripts/estop_relay.py` |
| Traffic decision logic (pure) | `wasab_navigation/wasab_patrol/wasab_patrol/traffic_rules.py` |

**Tests** — **115** unit tests for patrol/arbitration pure logic, **138** for the web app adapter.
Only the ones that run without ROS are counted. State machines are verified entirely on the ground;
only the communication contracts get checked on real hardware.

---

Related posts *(Korean)*: [Dropping Coordinates and Counting Hops](/posts/auto_drive/다중로봇-통행중재-홉기반-점유와-실측규칙/) ·
[The Agent Bridging Two ROS Domains, and CPU Tuning](/posts/auto_drive/wasab-로봇함대-두-도메인을-잇는-agent와-cpu튜닝/) ·
[AprilTag PID Precision Docking](/posts/auto_drive/nav2-apriltag-pid-정밀도킹-성공기록/)
