---
title: "micro-ROS ESP32 완벽 설치 가이드 (ROS 2 Jazzy + Ubuntu 24.04 Docker)"
date: 2026-03-21
draft: true
tags: ["ros2"]
categories: ["ros2"]
description: "- **호스트 OS:** Ubuntu 24.04 Desktop - **Docker 이미지:** `osrf/ros:jazzy-desktop-full` - **보드:** ESP32 (UART/Serial 연결)"
---

# micro-ROS ESP32 완벽 설치 가이드 (ROS 2 Jazzy + Ubuntu 24.04 Docker)

## 환경
- **호스트 OS:** Ubuntu 24.04 Desktop
- **Docker 이미지:** `osrf/ros:jazzy-desktop-full`
- **보드:** ESP32 (UART/Serial 연결)
- **ROS 2:** Jazzy Jalisco
- **Python:** 3.12 (Ubuntu 24.04 기본)

> ⚠️ Ubuntu 24.04(Python 3.12) + ESP-IDF 4.1 조합에서 발생하는 호환성 문제들을 모두 해결한 가이드입니다.

---

## 1단계: Docker 컨테이너 생성 및 기본 패키지 설치

```bash
# Docker 컨테이너 생성 (호스트 네트워크 + 디바이스 접근)
docker run -it --net=host -v /dev:/dev --privileged --name micro-ros osrf/ros:jazzy-desktop-full
```

```bash
# 컨테이너 내부에서 기본 패키지 설치
apt update
apt install -y python3-rosdep python3-colcon-common-extensions python3-pip nano
```

---

## 2단계: micro_ros_setup 빌드

```bash
mkdir ~/microros && cd ~/microros
git clone -b $ROS_DISTRO https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup

apt update && rosdep update
rosdep install --from-path src --ignore-src -y

colcon build
source install/local_setup.bash
```

---

## 3단계: ESP32 펌웨어 워크스페이스 생성

```bash
ros2 run micro_ros_setup create_firmware_ws.sh freertos esp32
```

> 이 명령은 ESP-IDF 툴체인 다운로드까지 포함하여 상당한 시간이 소요됩니다.
> 마지막에 `pkg_resources cannot be imported` 에러가 발생하지만, 툴체인 설치는 완료된 상태입니다.

---

## 4단계: Python 호환성 문제 해결 (핵심!)

Ubuntu 24.04의 Python 3.12와 ESP-IDF 4.1 사이의 호환성 문제를 해결합니다.

### 4-1. setuptools 호환 버전 설치

ESP-IDF 4.1은 `pkg_resources`가 필요하지만:
- `setuptools 82.x` (기본 설치됨) → `pkg_resources` 제거됨
- `setuptools 58.x` → Python 3.12와 비호환 (`pkgutil.ImpImporter` 제거됨)
- **`setuptools 69.5.1`** → 둘 다 호환!

```bash
~/microros/firmware/toolchain/espressif/python_env/idf4.1_py3.12_env/bin/pip install setuptools==69.5.1
```

### 4-2. 추가 Python 패키지 설치

```bash
# pyyaml (의존성 경고 해결)
~/microros/firmware/toolchain/espressif/python_env/idf4.1_py3.12_env/bin/pip install pyyaml

# catkin_pkg, lark, empy (빌드 시 필요)
~/microros/firmware/toolchain/espressif/python_env/idf4.1_py3.12_env/bin/pip install catkin_pkg lark empy==3.3.4
```

### 4-3. python 심볼릭 링크 생성

Ubuntu 24.04에는 `python` 명령이 없고 `python3`만 있습니다.

```bash
ln -s /usr/bin/python3 /usr/bin/python
```

### 4-4. NumPy 설치 (Agent 빌드용)

```bash
pip install numpy --break-system-packages
```

### 4-5. ESP-IDF 환경 확인

```bash
export IDF_TOOLS_PATH=/root/microros/firmware/toolchain/espressif
source ~/microros/firmware/toolchain/esp-idf/export.sh
```

아래 메시지가 출력되면 성공:
```
Python requirements from .../requirements.txt are satisfied.
Done! You can now compile ESP-IDF projects.
```

---

## 5단계: 불필요한 패키지 제거

`create_firmware_ws.sh`가 중간에 실패했기 때문에 `freertos_apps`를 수동 클론해야 하며,
크로스컴파일에 불필요한 패키지들을 제거해야 합니다.

### 5-1. freertos_apps 수동 클론 (경로가 없는 경우)

```bash
ls ~/microros/firmware/freertos_apps/ 2>/dev/null || \
  (cd ~/microros/firmware && git clone -b $ROS_DISTRO https://github.com/micro-ROS/freertos_apps.git)
```

### 5-2. 중복/불필요 패키지 제거

```bash
# rcl 중복 제거 (uros/rcl이 ros2/rcl을 대체)
rm -rf ~/microros/firmware/mcu_ws/ros2/rcl

# 트레이싱 패키지 제거 (ESP32에서 불필요)
rm -rf ~/microros/firmware/mcu_ws/ros2/ros2_tracing

# spdlog 로깅 제거 (ESP32는 rcl_logging_noop 사용)
rm -rf ~/microros/firmware/mcu_ws/ros2/rcl_logging/rcl_logging_spdlog

# rclc 예제 제거 (크로스컴파일 링크 에러 발생)
rm -rf ~/microros/firmware/mcu_ws/uros/rclc/rclc_examples
```

---

## 6단계: ping_pong 앱 코드 수정

### 6-1. Domain ID 설정 및 초기화 코드 수정

```bash
nano ~/microros/firmware/freertos_apps/apps/ping_pong/app.c
```

`appMain` 함수에서 `rclc_support_init`이 두 번 호출되는 것을 수정합니다.

**수정 전 (잘못된 코드):**
```c
void appMain(void *argument)
{
    rcl_allocator_t allocator = rcl_get_default_allocator();
    rclc_support_t support;

    init_ops = rcl_get_zero_initialized_init_options();
    RCCHECK(rcl_init_options_init(&init_ops, allocator));
    RCCHECK(rcl_init_options_set_domain_id(&init_ops, domain_id));
    RCCHECK(rclc_support_init_with_options(&support, 0, NULL, &init_ops, &allocator));

    // 이 줄이 위의 domain_id 설정을 덮어씀!
    RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));

    rcl_node_t node;
```

**수정 후 (올바른 코드):**
```c
void appMain(void *argument)
{
    rcl_allocator_t allocator = rcl_get_default_allocator();
    rclc_support_t support;

    init_ops = rcl_get_zero_initialized_init_options();
    RCCHECK(rcl_init_options_init(&init_ops, allocator));
    RCCHECK(rcl_init_options_set_domain_id(&init_ops, domain_id));
    RCCHECK(rclc_support_init_with_options(&support, 0, NULL, &init_ops, &allocator));

    // rclc_support_init 중복 호출 삭제!

    rcl_node_t node;
```

### 6-2. Domain ID 값 확인

파일 상단에서 domain_id 변수를 원하는 값으로 설정:
```c
size_t domain_id = 31;  // 원하는 Domain ID
```

---

## 7단계: 펌웨어 Configure, Build, Flash

```bash
cd ~/microros
source install/local_setup.bash
export IDF_TOOLS_PATH=/root/microros/firmware/toolchain/espressif

# Serial 모드로 Configure
ros2 run micro_ros_setup configure_firmware.sh ping_pong --transport serial

# Build (시간 소요)
ros2 run micro_ros_setup build_firmware.sh

# ESP32 USB 연결 후 권한 설정 & Flash
sudo chmod a+rw /dev/ttyUSB0
ros2 run micro_ros_setup flash_firmware.sh
```

---

## 8단계: micro-ROS Agent 빌드 및 실행

```bash
cd ~/microros
source install/local_setup.bash

# Agent 워크스페이스 생성 & 빌드
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh

# Agent 실행 (Domain ID를 펌웨어와 일치시킴)
source install/local_setup.bash
export ROS_DOMAIN_ID=31
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 -v6
```

ESP32 보드의 **RST/EN 버튼**을 눌러 리셋합니다.

Agent 로그에 `session established` 메시지가 나오면 연결 성공!

---

## 9단계: ping_pong 테스트

**새 터미널을 열고 컨테이너에 접속:**
```bash
docker exec -it micro-ros bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=31
```

### 토픽 확인
```bash
ros2 topic list
```
출력:
```
/microROS/ping
/microROS/pong
/parameter_events
/rosout
```

### ping 메시지 모니터링
```bash
ros2 topic echo /microROS/ping
```

### pong 응답 테스트

**또 다른 터미널에서:**
```bash
docker exec -it micro-ros bash
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=31

# pong 모니터링
ros2 topic echo /microROS/pong
```

**ping 전송:**
```bash
ros2 topic pub --once /microROS/ping std_msgs/msg/Header '{frame_id: "fake_ping"}'
```

pong 터미널에서 응답이 출력되면 **완료!** 🎉

---

## 문제 해결 요약

| 문제 | 원인 | 해결 |
|------|------|------|
| `pkg_resources cannot be imported` | setuptools 82.x에서 pkg_resources 제거됨 | `setuptools==69.5.1` 설치 |
| `pkgutil has no attribute ImpImporter` | setuptools 58.x가 Python 3.12 미지원 | `setuptools==69.5.1` 설치 |
| `/usr/bin/env: 'python': No such file or directory` | Ubuntu 24.04에 python 명령 없음 | `ln -s /usr/bin/python3 /usr/bin/python` |
| `tool xtensa-esp32-elf has no installed versions` | IDF_TOOLS_PATH 미설정 | `export IDF_TOOLS_PATH=.../espressif` |
| `No module named 'catkin_pkg'` | ESP-IDF 가상환경에 미설치 | pip install catkin_pkg lark empy |
| `Duplicate package names: rcl` | ros2/rcl과 uros/rcl 중복 | `rm -rf mcu_ws/ros2/rcl` |
| `Findpybind11_vendor.cmake not found` (lttngpy) | ESP32에서 불필요한 트레이싱 | `rm -rf mcu_ws/ros2/ros2_tracing` |
| `Findspdlog_vendor.cmake not found` | ESP32에서 불필요한 spdlog 로깅 | `rm -rf rcl_logging_spdlog` |
| `cannot find -latomic` (rclc_examples) | 크로스컴파일 링크 에러 | `rm -rf rclc/rclc_examples` |
| `missing: NumPy` (Agent 빌드) | numpy 미설치 | `pip install numpy` |
| 토픽이 안 보임 | ROS_DOMAIN_ID 불일치 또는 init 중복 호출 | domain_id 일치 + 코드 수정 |

---

## 컨테이너 재시작 시 필요한 명령어

```bash
docker start micro-ros
docker exec -it micro-ros bash

cd ~/microros
source install/local_setup.bash
export IDF_TOOLS_PATH=/root/microros/firmware/toolchain/espressif
export ROS_DOMAIN_ID=31
```
