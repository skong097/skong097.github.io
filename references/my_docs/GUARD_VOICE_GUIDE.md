# guard_voice 노드 — 설치 및 테스트 가이드

> **작성일:** 2026-02-13
> **기능:** `/guard/tts_command`, `/guard/report` 구독 → gTTS 한국어 변환 → sounddevice 스피커 재생
> **재생 정책:** 우선순위 큐 하이브리드 (위험/경고 → 즉시 중단 재생, 정상/주의 → 큐 순서)

---

## 1. 패키지 설치

```bash
# venv 활성화
source ~/dev_ws/ros2_venv/bin/activate

# 필수 패키지 설치
pip install gtts pydub soundfile

# ffmpeg (pydub 백엔드 — MP3 디코딩)
sudo apt install -y ffmpeg

# 확인
python3 -c "from gtts import gTTS; print('gTTS OK')"
python3 -c "import sounddevice; print('sounddevice OK')"
python3 -c "from pydub import AudioSegment; print('pydub OK')"
```

## 2. 패키지 배치

```bash
# guard_voice 패키지를 ROS2 워크스페이스에 배치
cp -r guard_voice/ ~/dev_ws/ironman/home_guard_ws/src/guard_voice/
```

디렉토리 구조:
```
home_guard_ws/src/guard_voice/
├── guard_voice/
│   ├── __init__.py
│   └── tts_node.py          # TTS 노드
├── resource/
│   └── guard_voice           # ament 마커
├── package.xml
├── setup.cfg
└── setup.py
```

## 3. 빌드

```bash
cd ~/dev_ws/ironman
./scripts/build.sh guard_voice
```

`✅ guard_voice/tts_node` 패치 메시지가 나와야 합니다.

## 4. 단독 테스트

### 터미널 1: tts_node 실행
```bash
./scripts/run.sh guard_voice tts_node
```

### 터미널 2: 텍스트 발행 테스트
```bash
source ~/dev_ws/ros2_venv/bin/activate
source /opt/ros/jazzy/setup.bash

# 정상 등급 대사
ros2 topic pub --once /guard/tts_command std_msgs/String "data: '순찰 이상 없습니다.'"

# 위험 등급 보고서 (JSON — level 포함)
ros2 topic pub --once /guard/report std_msgs/String "data: '{\"level\":\"위험\",\"tts_voice\":\"위험! 낙상이 감지되었습니다!\"}'"
```

## 5. brain_node 통합 테스트

### 터미널 1: brain_node
```bash
./scripts/run.sh brain_node
```

### 터미널 2: tts_node
```bash
./scripts/run.sh guard_voice tts_node
```

### 터미널 3: sensor_sim
```bash
./scripts/run.sh sensor_sim_node
```

기대 결과:
- sensor_sim이 센서 데이터 발행
- brain_node가 LLM 판단 후 `/guard/report` + `/guard/tts_command` 발행
- tts_node가 수신 → gTTS 변환 → 스피커 재생

## 6. 파라미터

```bash
# 볼륨 조절 (0.0 ~ 1.0)
./scripts/run.sh guard_voice tts_node --ros-args -p volume:=0.5

# 캐시 끄기
./scripts/run.sh guard_voice tts_node --ros-args -p cache:=false
```

## 7. 트러블슈팅

### 소리가 안 나는 경우
```bash
# 오디오 디바이스 확인
python3 -c "import sounddevice; print(sounddevice.query_devices())"

# ALSA 에러 시
sudo apt install -y pulseaudio alsa-utils
pulseaudio --start
```

### gTTS 네트워크 에러
```bash
# 인터넷 연결 확인
python3 -c "from gtts import gTTS; gTTS('테스트', lang='ko').save('/tmp/test.mp3'); print('OK')"
```

### ffmpeg 없음 에러
```bash
sudo apt install -y ffmpeg
```
