---
title: "Autonomous Driving · Robotics Technical Dictionary"
layout: single
summary: "A sector-by-sector dictionary of the algorithms, models, standards, and design patterns actually used in autonomous driving, AGVs, and multi-robot fleets. Each entry is summarized by one line: what breaks without it."
ShowToc: true
TocOpen: false
ShowReadingTime: false
hideMeta: true
---

<div class="algo-dict"></div>

Build robots long enough and you catch yourself **searching for the same algorithm three weeks later.**
Retracing "what exactly did this solve again?" every single time was a waste, so I cut the ones that
actually get used into sectors and made a dictionary.

Each entry is described not by its definition but by **"what stops working without it."** An algorithm
isn't an answer — it's someone's solution to a problem they hit. If you don't know the problem, you
don't know when to reach for it.

> **This page is an index.** The details per entry — how it works, the original paper, implementation
> code, what I ran into using it — get written up one at a time and linked below. An entry with no link
> yet is one I haven't written.

**Domain tags** — `AV` autonomous vehicles · `AGV` industrial AGV/AMR · `MR` multi-robot & fleet

Currently **10 sectors · 119 entries**.


## S0. Sensing · Preprocessing

| Name | Type | Problem it solves | Domain |
|---|:---:|---|:---:|
| Camera calibration (Zhang) | Algorithm | A lens is not a perfect pinhole — it distorts, and focal length differs per camera. Without measuring this up front, the conversion "this pixel on screen is N meters ahead" doesn't hold at all | AV AGV |
| IPM (inverse perspective mapping) | Math model | Shoot a road with a camera and perspective makes farther lane lines appear narrower, so you can't compute real curvature. This flattens the image as if seen from above | AV |
| DLT (Direct Linear Transform) | Algorithm | Converts pixel coordinates from a ceiling-mounted camera into the robot's real (x, y) coordinates on the floor | AGV MR |
| Scan deskew (motion compensation) | Algorithm | While the lidar completes one revolution the robot moves, so the start and end of the scan are captured from different poses and the point cloud comes out warped. This corrects that distortion by the robot's own motion | AV AGV |
| RANSAC plane fitting · Patchwork++ | Algorithm | If the floor is mistaken for an obstacle in a lidar point cloud, the robot concludes it can't go anywhere. This picks out just the plane that is the ground from among noisy points | AV |
| Voxel grid downsampling | Algorithm | A lidar frame can contain hundreds of thousands of points; processing all of them breaks real time. Divide space into small cells and keep one representative point per cell | AV |
| ApproximateTime synchronization | Algorithm | Fusing different sensors requires matching data from the same instant. If timestamps don't line up, you fuse wrong information and performance gets worse, not better | AV AGV |
| HSV threshold segmentation | Algorithm | Thresholds set on RGB values fall apart the moment lighting changes (shade, backlight). HSV separates hue, saturation, and value, making the threshold far more robust to lighting | AV |


## S1. Perception

| Name | Type | Problem it solves | Domain |
|---|:---:|---|:---:|
| Canny + Hough lane detection | Algorithm | The classical way to extract lane position using only edge detection and line detection, no deep learning | AV |
| Sliding window + polyfit | Algorithm | Dashed lane markings are broken up, but they have to be fit into a single continuous curve before they're usable for path computation | AV |
| CLRNet / UFLD / LaneNet | Learned model | Classical methods collapse when lighting is poor or lanes are worn or occluded. Deep learning extracts lanes even under those conditions | AV |
| YOLO-family 2D detection | Learned model | The standard way to find people, vehicles, and signs in a camera image in real time as boxes | AV AGV |
| PointPillars / CenterPoint | Learned model | Detects objects as 3D boxes from lidar point clouds in real time | AV |
| BEVFormer / BEVFusion | Learned model | Merges what several cameras each saw into one common top-down coordinate frame (BEV) and perceives there | AV |
| Occupancy Network | Learned model | Box detection only handles a fixed set of object classes. Irregular things — construction material, fallen debris — must be expressed as occupancy of space rather than as a box | AV |
| Freespace segmentation | Problem | Sometimes you don't need to know "what that is," only "whether I can drive there." This extracts drivable area per pixel without going through object recognition | AV AGV |
| SORT / DeepSORT / ByteTrack | Algorithm | Detecting objects fresh every frame leaves a separate job: deciding whether that object last frame and this object this frame are the same entity | AV MR |
| ArUco / AprilTag detection | Algorithm | When you need a positional reference indoors with no GPS and no infrastructure, the camera finds pre-placed markers to obtain an absolute coordinate reference | AGV MR |
| Traffic light · sign recognition | Problem | Points where the rules change — intersections, school zones — have to be judged in real time from the camera | AV |
| Vector map color classification + denoising | Problem | Converts a hand-drawn floor plan image (bitmap) into line-and-point vector data the robot can actually compute with | AV |
| Automatic waypoint extraction | Problem | In a large facility with hundreds of waypoints, no one can place them all by hand — they have to be extracted automatically | AV AGV |
| Pose estimation (skeleton) | Problem | Recognizes the joint positions of a person's limbs so that posture or gesture can be used as a command or event for the robot | MR |


## S2. Localization & State Estimation

| Name | Type | Problem it solves | Domain |
|---|:---:|---|:---:|
| Kalman Filter | Algorithm | Sensor readings always carry noise; this is the basic filter that estimates the true value optimally while accounting for that noise | All |
| **EKF** | Algorithm | A robot turning while it moves has nonlinear equations of motion, but the plain Kalman filter only holds for linear systems. This approximates the nonlinearity as locally linear | All |
| UKF / ESKF | Algorithm | The EKF's linear approximation accumulates large error under heavy rotation or when handling attitude (quaternions). These versions refine how the approximation is done | AV |
| Staged sensor-fusion validation | Pattern | Fuse every sensor at once and, when the result is wrong, you can't tell which sensor caused it. Add them one at a time, validating at each step | AGV MR |
| **MCL / AMCL (particle filter)** | Algorithm | You have a map but no idea where on it the robot is. Scatter many pose hypotheses and narrow them down by matching against sensor observations | AGV |
| ICP / GICP | Algorithm | Overlays point clouds from two moments (or two sensors) to recover the change in position and orientation between them | AV AGV |
| NDT | Algorithm | Instead of corresponding point to point as ICP does, it represents the cloud as a probability distribution, registering faster and more robustly | AV |
| Graph SLAM / Pose graph | Algorithm | Position error accumulates as the robot travels; this optimizes it as a graph so the error is corrected all at once when the robot revisits a place it has been (loop closure) | AGV |
| gmapping (RBPF) | Algorithm | Since position is uncertain, each particle (pose hypothesis) builds its own separate map while doing SLAM | AGV |
| Cartographer / slam_toolbox | Implementation | Software stacks that run in real time yet still perform one more optimization pass afterwards | AGV |
| LOAM / LIO-SAM / FAST-LIO2 | Algorithm | Recovers precise odometry using only lidar and IMU in environments without GPS | AV |
| ORB-SLAM3 / VINS-Fusion | Implementation | Implementations that do localization and mapping simultaneously using cameras alone, without lidar | AV |
| Wheel odometry calibration (UMBmark) | Algorithm | If wheel diameter or wheelbase differs even slightly from the design value, error keeps accumulating in proportion to distance traveled. This corrects it from measurement | AGV |
| Ceiling markers / external infrastructure positioning | Problem | In wide-open spaces without walls, matching surrounding geometry to fix your position doesn't work even in principle, so an external reference is required | AGV MR |
| UWB TWR/TDOA · beacon fingerprinting | Algorithm | Where cameras and lidar have no clear line of sight indoors, position is derived from radio round-trip time or time difference of arrival | AGV |


## S3. Mapping & Representation

| Name | Type | Problem it solves | Domain |
|---|:---:|---|:---:|
| Occupancy grid (log-odds) | Representation | A map representation that keeps accumulating sensor observations, updating per cell the probability that something is there | AGV MR |
| Costmap 2D + inflation layer | Representation | The robot has physical size, so planning flush against a wall means hitting it. Instead of modeling the robot as a point, inflate the obstacles by the robot's size | AGV |
| STVL / 3D voxel layer | Implementation | A 2D grid assumes the floor is flat and therefore misses obstacles suspended in the air above it. This represents space in 3D | AGV |
| 2.5D elevation map | Representation | Terrain with height differences — ramps, thresholds — is separated into its own layer and reflected in traversal cost | AGV MR |
| Octomap / TSDF / ESDF | Representation | Stores an entire 3D space in memory efficiently and also rapidly yields the distance from any point to the nearest obstacle (distance field) | AV |
| **Topological graph / waypoint map** | Representation | In environments where the traversable routes are fixed in advance, like roads, representing every cell as a grid is wasteful. Represent it with nodes and edges only | AV AGV |
| Lanelet2 / OpenDRIVE / HD map | Standard | The map data itself has to carry the traffic rules — which direction each lane runs, what it connects to, who has right of way | AV |
| Map merging (delta merging) | Algorithm | What's needed when maps built separately by several robots have to be combined into one | MR |
| Umeyama / Kabsch registration | Algorithm | When robots use different coordinate frames, they refer to the same spot by different numbers. This recovers the transform that aligns the two frames | MR |


## S4. Global Planning

| Name | Type | Problem it solves | Domain |
|---|:---:|---|:---:|
| Dijkstra | Algorithm | Finds "the shortest route from here to there" on a graph with a guarantee of optimality. It ignores the goal direction, so it searches outward in every direction | All |
| **A\*** | Algorithm | Dijkstra doesn't know where the goal lies and searches all directions equally, which wastes effort. A\* estimates roughly how far remains to the goal and narrows the search toward it | All |
| Weighted A\* / Theta\* | Algorithm | Running A\* on a grid restricts motion to 8 directions, turning routes that could be straight lines into staircase zigzags. These relax that | AGV |
| Jump Point Search | Algorithm | On a uniform grid, A\* is slow because it expands neighboring cells of identical value one by one. This skips the obvious stretches to gain speed | AGV |
| D\* / D\* Lite | Algorithm | When an obstacle appears that wasn't in the original plan, A\* has to recompute from scratch. D\* recomputes only the changed portion, making replanning fast | AV AGV |
| **Hybrid A\*** | Algorithm | Grid A\* assumes the robot can teleport into any cell, but a car cannot rotate in place. This considers only trajectories the vehicle can actually execute | AV AGV |
| Reeds-Shepp / Dubins shortest curves | Algorithm | For a vehicle with a minimum turning radius, this gives the shortest curve from A to B (heading included) directly by formula, with no search | AV AGV |
| State lattice | Algorithm | Splicing arbitrary curves together can produce a trajectory the robot cannot actually follow. Precompute a library of executable trajectory segments and connect those | AV |
| RRT / RRT-Connect | Algorithm | When the search space has very high dimension, sweeping it with a grid explodes computationally. Scatter random points, grow a tree, and quickly find one route that works | MR |
| RRT\* / Informed RRT\* / BIT\* | Algorithm | RRT is fast but offers no guarantee that the first route found is optimal (shortest). These keep improving, converging toward the optimum | MR |
| PRM | Algorithm | If you'll plan many times on the same map, don't search anew each time — lay down a roadmap of traversable routes once, then search quickly on top of it | AGV |
| NavFn / Smac Planner (Nav2) | Implementation | The above theory implemented so it can be used directly in real robot middleware (ROS 2 Nav2) | AGV |
| Waypoint routing (waypoint following) | Pattern | Handles operational requirements — warehouse aisles and the like — where the robot must follow a prescribed order and route rather than the shortest path | AGV MR |


## S5. Local Planning & Trajectory

| Name | Type | Problem it solves | Domain |
|---|:---:|---|:---:|
| **DWA / DWB** | Algorithm | The path drawn by the global planner knows nothing about the velocity and acceleration the robot can actually produce right now. This picks the next single step from only the velocity candidates reachable within current dynamic limits | AGV |
| TEB (Timed Elastic Band) | Algorithm | Optimizes the path including the time axis, not just space, deforming it like a rubber band pushed by obstacles | AGV |
| **MPPI** | Algorithm | Cost functions that split cleanly into feasible/infeasible, such as collision, aren't differentiable and can't be solved by classical MPC. This works around it by randomly sampling many trajectories and averaging | AGV AV |
| **MPC / NMPC** | Algorithm | Optimizes the next N steps of the future all at once while respecting constraints such as velocity and steering limits and collision avoidance | AV AGV |
| Frenet trajectory generation (Werling) | Algorithm | On curved roads it is far easier to work in "how far along the lane you've traveled (s)" and "how far laterally you've deviated (d)" than in xy coordinates | AV |
| Polynomial trajectories (quintic · jerk-optimal) | Algorithm | Ride comfort is determined not by acceleration but by its rate of change (jerk). This builds trajectories as polynomials that are smooth down to jerk | AV |
| VO / RVO / **ORCA** | Algorithm | When several agents each take their own avoidance action, they can't predict the other's avoidance and end up oscillating back and forth. These are reciprocal avoidance algorithms that prevent it | MR |
| Potential field (APF) | Algorithm | Decides the next motion immediately from the sum of forces — the goal attracts, obstacles repel. Cheap to compute, but it can get trapped where the forces cancel (local minima) | MR |
| Elastic Band | Algorithm | Treats the global path itself as a rubber band pushed by obstacles and deforms it in real time | AGV |
| S-T graph / velocity profile | Representation | Which route to take and at what speed to pass along it are separate problems, so they're computed separately | AV |
| Bezier / Clothoid / Spline smoothing | Math model | A path made by connecting sharp corners directly makes steering jerk violently when followed. This smooths it into gentle curves | AV AGV |
| Virtual obstacle injection | Pattern | Sometimes you need to create the constraint "you can't go here" artificially in software even though no real obstacle is present | AGV MR |


## S6. Control

| Name | Type | Problem it solves | Domain |
|---|:---:|---|:---:|
| PID | Algorithm | The most basic feedback control: look at the gap between target and current value (the error) and decide how much motor command to turn it into | All |
| **Pure Pursuit** | Algorithm | Rather than considering the whole path, look only at a single point ahead and compute the steering angle geometrically (by drawing a circle) to head toward it | AV AGV |
| **Regulated Pure Pursuit (RPP)** | Algorithm | Pure Pursuit doesn't slow down for sharp curves or nearby obstacles. This augments it to regulate speed for those situations | AGV |
| Stanley controller | Algorithm | Puts lateral deviation from the path and heading error into a single expression, measured at the front axle, to compute steering | AV |
| Kinematic bicycle model | Math model | Computing all four wheels of a car separately makes the equations messy, so each axle is collapsed into a single wheel and simplified into a bicycle | AV |
| Differential drive inverse kinematics | Math model | Converts the command "go forward at this speed while turning this much (v, ω)" into the actual rotational speed of each of the left and right wheels | AGV MR |
| Mecanum / omni inverse kinematics | Math model | Unlike differential drive, these wheel arrangements can also move sideways, so the inverse kinematics equations themselves differ | AGV |
| LQR / iLQR·DDP | Algorithm | Instead of tuning gains by feel as with PID, this derives the control input mathematically by minimizing a cost (error plus energy, etc.) | AV |
| Visual servoing | Algorithm | When the target is an object visible in the camera frame rather than a coordinate on a map, control is driven directly from that image information | AGV |
| Final alignment / RotationShim | Implementation | Arriving at the goal coordinate with the wrong heading means docking or loading fails, so a separate final stage fixes the orientation | AGV |
| S-curve acceleration profile | Algorithm | A trapezoidal velocity profile makes the rate of change of acceleration (jerk) momentarily infinite, shocking the machine. A smooth S-curve keeps jerk finite | AGV |


## S7. Multi-Robot & Fleet

| Name | Type | Problem it solves | Domain |
|---|:---:|---|:---:|
| **CBS / ECBS** | Algorithm | Plan each robot's path independently and conflicting paths are inevitable. This finds the conflicts and solves for all robots together, adding constraints one at a time | MR AGV |
| Prioritized planning (PBS) | Algorithm | CBS explodes computationally as the robot count grows. Assigning priorities and solving them one by one in order buys speed | MR |
| PIBT / LNS2 / RHCR | Algorithm | Settings like logistics floors, where new tasks arrive continuously, cannot be handled by planning everything once and being done (one-shot MAPF) | AGV |
| Intersection reservation | Algorithm | Prevents collisions by cutting shared crossing segments into time slots that robots claim in advance | AV AGV |
| Deadlock detection (resource allocation graph) | Algorithm | If everyone just waits for everyone else to yield, no one ever moves. This detects that state as a graph | AGV MR |
| **Auction / market-based task allocation (CBBA)** | Algorithm | As workload grows it becomes hard for one central node to compute who gets which job. The robots divide the work among themselves by bidding | MR |
| Hungarian algorithm | Algorithm | Solves the optimal 1:1 matching of N tasks to M robots exactly, in polynomial time | MR |
| Leader-follower formation | Algorithm | The problem of several robots traveling together while holding a formation | MR |
| Consensus / Flocking (Reynolds) | Algorithm | Produces collective behavior like flocks of birds or schools of fish using only each agent's neighbor information, with no central control | MR |
| Coverage (BCD · Spanning Tree) | Algorithm | The problem of sweeping an entire area exhaustively, as a cleaning robot does, rather than traveling to a single point | MR AGV |
| **Heartbeat / liveness detection** | Pattern | Believing a dead robot is alive and continuing to assign it work turns it into a black hole where those tasks are never processed | MR |
| Domain isolation / 2-context bridge | Pattern | As robot count grows, the discovery traffic of the communication middleware (DDS) alone can saturate the network, so communication domains are separated | MR |
| Stale data correction | Pattern | Old state from another robot, delayed in transit, must not be mistaken for its current state and acted upon | MR |
| **VDA 5050 / OpenRMF** | Standard | A common standard interface for tying AGVs from different manufacturers into a single fleet management system | AGV MR |


## S8. Learning & Prediction

| Name | Type | Problem it solves | Domain |
|---|:---:|---|:---:|
| Behavior Cloning | Algorithm | Driving too complex to write out as hand-authored rules is learned by imitating human driving data directly | AV |
| **PilotNet (end-to-end IL)** | Learned model | Rather than splitting perception→planning→control into separate modules, a single CNN outputs steering directly from camera input | AV |
| DAgger | Algorithm | Behavior Cloning learns only from data a human produced, so situations the policy itself drifts into by mistake never appear in the training data and can't be handled. This relabels those off-distribution states to fill the gap | AV |
| DQN / PPO / SAC | Algorithm | Reinforcement learning: give reward rather than the correct action, and let the robot find its policy through trial and error | AV MR |
| Sim-to-real | Problem | The gap where a policy learned in simulation doesn't transfer well to the real robot | AV MR |
| Social Force Model | Math model | People don't sit still like obstacles — natural avoidance requires treating them as entities with their own destination and intent | MR |
| Social LSTM / Trajectron++ | Learned model | Predicts where surrounding people and vehicles will be seconds from now as a probability distribution rather than a single value | AV |
| VectorNet / TNT / MTR | Learned model | Feeds HD map information and surrounding agents' trajectories into the network in vector form to push prediction accuracy up | AV |
| UniAD / VAD | Learned model | Rather than training perception, prediction, and planning separately, handles them together in one connected, end-to-end trainable network | AV |
| World model (Wayve GAIA, etc.) | Learned model | Instead of a human hand-building a simulator, learns from data how the world evolves and generates it | AV |
| Diffusion policy | Learned model | When several plausible actions exist (multimodality), represents the distribution as it is instead of collapsing it into one average | MR |
| VLA (RT-2 · π0) | Learned model | Converts a language instruction like "pick up that cup" straight into robot joint motion with no intermediate stage | MR |


## S9. Safety & Validation

| Name | Type | Problem it solves | Domain |
|---|:---:|---|:---:|
| **RSS (Mobileye)** | Math model | Safety has to be defined as a formula, not a verbal claim like "we kept sufficient distance," before a regulator can verify and certify it | AV |
| TTC / time headway | Math model | How many seconds until collision if the current speed holds — the simplest safety metric to compute | AV AGV |
| Safety Shield / SP Aggregator | Pattern | Perception, planning, and control can each emit a different speed and direction; something has to take responsibility for merging them into one safe final command | AV AGV |
| Soft E-STOP latch | Pattern | Sending a stop command once isn't enough if another module overwrites cmd_vel on the next control cycle — the robot won't stop. This latches the stop state | AGV MR |
| Collision monitor / safety zones | Implementation | The last line of defense that stops the robot from a single sensor at the final stage, even if all the upstream planning and perception are wrong | AGV |
| Watchdog / bond | Pattern | Trusting a dead software node as if it were alive makes the system fail silently, with no error shown. This checks liveness periodically | MR |
| MRM (minimal risk maneuver) | Problem | The procedure defining where and how to come to a safe stop when the autonomous system can no longer judge for itself | AV |
| ISO 26262 / SOTIF (21448) | Standard | The standards covering cases where danger arises from performance limitations (e.g. perception failure) even when no component has failed | AV |
| **ISO 3691-4 / ANSI B56.5** | Standard | The minimum bar for legal safety requirements on AGVs and AMRs on industrial sites | AGV |
| ODD definition (ISO 34503) | Standard | Unless the operational scope — "how far this autonomous system is accountable" — is pinned down in a document, there's no way to decide what needs validating | AV AGV |
| Scenario-based validation (OpenSCENARIO) | Standard | Safety has to be demonstrated by which hazardous situations have been experienced (scenario coverage), not simply by how many kilometers were driven without an accident | AV |


---

## How to use this dictionary

**It isn't for counting entries.** It's a table built so you can find the problem you're facing right
now in the "Problem it solves" column and start digging into the algorithm on that row.

One gap, stated up front — the **patent landscape** per entry and **recent deployments (CES and the
like)** haven't been researched yet. I'll fill those in per entry as the detail articles get written.
