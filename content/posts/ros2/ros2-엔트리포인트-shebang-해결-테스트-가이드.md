---
title: "ROS2 엔트리포인트 Shebang 해결 — 테스트 가이드"
date: 2026-03-21
draft: true
tags: ["ros2"]
categories: ["ros2"]
description: "> **작성일:** 2026-02-13 > **문제:** `colcon build` 시 shebang이 시스템 Python(`#!/usr/bin/python3`)으로 고정되어 venv 패키지(ollama 등)를 못 "
---

# ROS2 엔트리포인트 Shebang 해결 — 테스트 가이드

> **작성일:** 2026-02-13
> **문제:** `colcon build` 시 shebang이 시스템 Python(`#!/usr/bin/python3`)으로 고정되어 venv 패키지(ollama 등)를 못 찾음
> **해결:** venv 활성화 상태에서 `colcon build` → shebang이 venv Python 경로로 생성

---

## 파일 배치

```
/home/gjkong/dev_ws/ironman/
├── scripts/
│   ├── build.sh          ← 빌드 자동화 (NEW)
│   └── run.sh            ← 실행 자동화 (NEW)
└── home_guard_ws/
    └── src/
        └── guard_bringup/
            └── launch/
                └── guard_brain.launch.py  ← 표준 launch (NEW)
```

## 테스트 순서

### Step 1: 파일 복사

```bash
# 스크립트 복사
cp scripts/build.sh /home/gjkong/dev_ws/ironman/scripts/
cp scripts/run.sh /home/gjkong/dev_ws/ironman/scripts/
chmod +x /home/gjkong/dev_ws/ironman/scripts/*.sh

# launch 파일 복사
mkdir -p /home/gjkong/dev_ws/ironman/home_guard_ws/src/guard_bringup/launch/
cp guard_brain.launch.py /home/gjkong/dev_ws/ironman/home_guard_ws/src/guard_bringup/launch/
```

### Step 2: 클린 빌드

```bash
cd /home/gjkong/dev_ws/ironman

# 기존 빌드 삭제
rm -rf home_guard_ws/build/ home_guard_ws/install/ home_guard_ws/log/

# 빌드 스크립트로 빌드
./scripts/build.sh guard_brain
```

### Step 3: shebang 확인

```bash
# 엔트리포인트 shebang 확인 — venv Python이어야 함
head -1 home_guard_ws/install/guard_brain/lib/guard_brain/brain_node
# 기대 결과: #!/home/gjkong/dev_ws/ros2_venv/bin/python3
#
# ❌ 만약 #!/usr/bin/python3 이면 venv가 activate 안 된 상태에서 빌드한 것
```

### Step 4: ros2 run 테스트

```bash
# 방법 A: run.sh 사용 (권장)
./scripts/run.sh brain_node

# 방법 B: 수동 환경 설정 후 ros2 run
source /home/gjkong/dev_ws/ros2_venv/bin/activate
source /opt/ros/jazzy/setup.bash
source home_guard_ws/install/setup.bash
ros2 run guard_brain brain_node
```

### Step 5: ros2 launch 테스트

```bash
# guard_bringup 패키지도 빌드 필요
./scripts/build.sh guard_bringup guard_brain

# launch 실행
source /home/gjkong/dev_ws/ros2_venv/bin/activate
source /opt/ros/jazzy/setup.bash
source home_guard_ws/install/setup.bash
ros2 launch guard_bringup guard_brain.launch.py
```

### Step 6: 통합 테스트

터미널 1 (brain_node):
```bash
./scripts/run.sh brain_node
```

터미널 2 (sensor_sim):
```bash
./scripts/run.sh sensor_sim_node
```

기대 결과:
- brain_node가 `ros2 run`으로 정상 시작
- sensor_sim이 데이터 발행
- brain_node가 LLM 호출 후 보고서 + TTS 발행

---

## 트러블슈팅

### shebang이 여전히 시스템 Python인 경우

```bash
# 1. venv 활성화 확인
which python3
# → /home/gjkong/dev_ws/ros2_venv/bin/python3 이어야 함

# 2. 클린 빌드
rm -rf home_guard_ws/build/ home_guard_ws/install/
./scripts/build.sh guard_brain

# 3. 다시 확인
head -1 home_guard_ws/install/guard_brain/lib/guard_brain/brain_node
```

### import 에러 (ollama 등)

```bash
# venv에 패키지 설치 확인
source /home/gjkong/dev_ws/ros2_venv/bin/activate
pip list | grep ollama

# 없으면 설치
pip install ollama
```

### guard_bringup launch 파일을 못 찾는 경우

guard_bringup이 아직 ROS2 패키지로 설정되지 않았다면, 우선 launch 파일 없이 `ros2 run`으로 테스트합니다. guard_bringup 패키지 구성은 별도 작업으로 진행합니다.
