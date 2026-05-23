# ROS2 Commander — 앱 스토어 배포 로드맵

**작성일**: 2026-02-16  
**현재 상태**: Pygame 데스크톱 게임 (Python, 1216 lines, 단일 파일)  
**목표**: Google Play Store + Apple App Store 배포

---

## 현재 프로그램 분석

| 항목 | 현재 |
|------|------|
| 프레임워크 | Pygame (데스크톱 전용) |
| 언어 | Python |
| 해상도 | 1280×800 고정 |
| 입력 | 마우스 + 키보드 |
| 데이터 | 하드코딩 (MATCH_DATA, COMMAND_DATA, NODE_BUILDER_LEVELS) |
| 모드 | Memory Match, Command Rush, Node Builder (3개) |
| 저장 | 없음 (세션 종료 시 초기화) |

**핵심 강점**: ROS2 학습 특화 니치 콘텐츠 + Kevin 로봇 시나리오 기반 + 3가지 게임 모드 + 4단계 Tier 시스템

---

## Phase 0: 전략 결정 (1주)

### 어떤 프레임워크로 재작성할 것인가?

| 옵션 | 장점 | 단점 | 추천도 |
|------|------|------|--------|
| **A. Flutter (Dart)** | iOS+Android 동시, 고성능 렌더링, 애니메이션 강력, 단일 코드베이스 | Dart 학습 필요 | ★★★★★ |
| **B. React Native (JS)** | JS 생태계, 웹 확장 용이 | 게임류 UI에 약함 | ★★★☆☆ |
| **C. Buildozer (Python→APK)** | 기존 코드 재활용 | iOS 미지원, 성능 열악, 스토어 심사 리스크 | ★★☆☆☆ |
| **D. Web App (PWA)** | 스토어 없이 배포 가능, React/Vue | 네이티브 느낌 부족 | ★★★☆☆ |

**추천: Flutter**

이유: 카드 뒤집기 애니메이션, 드래그&드롭(Node Builder), 타이머 등 게임적 인터랙션이 많고, Flutter의 위젯/애니메이션 시스템이 이런 용도에 최적화되어 있습니다. iOS+Android를 한 번에 처리할 수 있고, Google의 장기 지원도 안정적입니다.

### 대안: Web App (빠른 배포 원할 경우)

React + Capacitor로 웹앱을 만들고 네이티브 래핑하는 방법도 있습니다. 기존 Python 로직을 JavaScript로 1:1 포팅하면 되고, PWA로 먼저 공개 후 스토어에도 올릴 수 있습니다. Flutter보다 학습 곡선이 낮을 수 있지만 게임 퍼포먼스에서는 Flutter가 우위입니다.

---

## Phase 1: 설계 & 리아키텍처 (1~2주)

### 1-1. 모바일 UX 재설계

| 데스크톱 (현재) | 모바일 (변경) |
|----------------|-------------|
| 1280×800 고정 | 반응형 (360~428dp 기준) |
| 마우스 클릭 | 터치 탭 + 스와이프 |
| 키보드 입력 (Command Rush) | 소프트 키보드 + 자동완성 힌트 |
| 큰 카드 그리드 | 스크롤 가능 그리드 or 축소 |
| Node Builder 드래그 | 터치 드래그 + 줌/팬 |

### 1-2. 데이터 분리

현재 하드코딩된 학습 데이터를 JSON 파일로 분리:

```
assets/
├── data/
│   ├── match_data.json       ← 카드 매칭 데이터 (Tier 1~4)
│   ├── command_data.json     ← CLI 명령어 데이터
│   └── node_builder.json     ← 아키텍처 퍼즐 레벨
├── fonts/
│   └── JetBrainsMono.ttf
└── images/
    ├── icons/
    └── cards/
```

이점: 콘텐츠 업데이트 시 코드 수정 불필요, 향후 서버에서 데이터 불러오기 가능

### 1-3. 상태 관리 & 저장

- **로컬 저장**: SharedPreferences (Flutter) 또는 AsyncStorage (RN)
  - 각 모드별 최고 점수, 별 획득 현황
  - Tier 잠금 해제 상태
  - 마지막 플레이 모드
- **진행도 시스템**: Tier 1 클리어 → Tier 2 잠금 해제 (현재는 모두 오픈)

---

## Phase 2: 개발 (3~5주)

### 2-1. 프로젝트 초기화 (Flutter 기준)

```bash
flutter create ros2_commander
cd ros2_commander
flutter pub add shared_preferences  # 로컬 저장
flutter pub add audioplayers        # 효과음
flutter pub add lottie              # 애니메이션 (선택)
flutter pub add google_fonts        # 폰트
```

### 2-2. 핵심 화면 구조

```
lib/
├── main.dart
├── models/
│   ├── match_card.dart
│   ├── command_question.dart
│   └── node_level.dart
├── screens/
│   ├── main_menu_screen.dart
│   ├── mode_select_screen.dart
│   ├── match_game_screen.dart       ← Memory Match
│   ├── command_game_screen.dart     ← Command Rush
│   ├── node_builder_screen.dart     ← Node Builder
│   └── result_screen.dart
├── widgets/
│   ├── flip_card.dart              ← 카드 뒤집기 애니메이션
│   ├── timer_bar.dart              ← 타임어택 바
│   ├── node_graph.dart             ← 노드 연결 캔버스
│   ├── star_rating.dart            ← 결과 별점
│   └── tier_badge.dart             ← Tier 표시
├── data/
│   └── ros2_data.dart              ← JSON 파싱
├── theme/
│   └── app_theme.dart              ← 색상/폰트 정의
└── utils/
    └── score_manager.dart          ← 점수 저장/불러오기
```

### 2-3. Python → Dart 포팅 핵심 매핑

| Python (Pygame) | Dart (Flutter) |
|-----------------|---------------|
| `pygame.display.set_mode()` | `MaterialApp` + `Scaffold` |
| `pygame.draw.rect()` | `Container` + `BoxDecoration` |
| `draw_rounded_rect()` | `Container(decoration: BoxDecoration(borderRadius: ...))` |
| `pygame.font.render()` | `Text` 위젯 |
| `pygame.event.get()` | `GestureDetector`, `InkWell` |
| `Button` 클래스 | `ElevatedButton` or 커스텀 위젯 |
| `GameState` Enum | State Management (Provider/Riverpod) |
| `time.time()` 기반 타이머 | `Timer`, `AnimationController` |
| `ease_out_back()` 이징 | `Curves.easeOutBack` (내장) |
| `random.shuffle()` | `list.shuffle()` (Dart 내장) |

### 2-4. 게임 모드별 구현 포인트

**Memory Match**:
- `AnimatedBuilder` + `Transform` 으로 3D 카드 뒤집기
- 카드 매칭 성공 시 `ScaleTransition` 효과
- 6×2 그리드 → 모바일에서 3×4 또는 스크롤

**Command Rush**:
- `TextField` + 자동완성 드롭다운
- 모바일 키보드 최적화: `ros2 ` 접두사 자동 입력 버튼
- 타이머바: `LinearProgressIndicator` + `AnimationController`

**Node Builder**:
- `CustomPainter`로 노드/연결선 드로잉
- `GestureDetector` + `Draggable`로 터치 드래그
- 핀치 줌: `InteractiveViewer` 위젯 활용

---

## Phase 3: 테스트 & 폴리싱 (1~2주)

### 3-1. 테스트 체크리스트

- [ ] 다양한 화면 크기 (5인치 ~ 12인치 태블릿)
- [ ] 세로/가로 모드 대응 (또는 세로 고정)
- [ ] 소프트 키보드 올라올 때 레이아웃 깨짐 확인
- [ ] 저사양 기기 성능 테스트
- [ ] 데이터 저장/복원 (앱 종료 후 재실행)
- [ ] 다크/라이트 모드 (시스템 설정 연동)

### 3-2. 모바일 전용 개선

- 효과음 추가 (카드 뒤집기, 정답, 오답, 타임업)
- 햅틱 피드백 (진동)
- 온보딩 튜토리얼 (첫 실행 시)
- 앱 아이콘 + 스플래시 스크린 디자인

---

## Phase 4: 스토어 배포 준비 (1주)

### 4-1. 스토어 등록 비용

| 스토어 | 비용 | 비고 |
|--------|------|------|
| Google Play | $25 (1회) | 평생 유효, 앱 무제한 등록 |
| Apple App Store | $99/년 | 매년 갱신 필요 |

**무료 앱이면 수수료 없음.** 유료 또는 인앱결제 시 15~30% 수수료.

### 4-2. 스토어 필수 자산

| 자산 | Google Play | App Store |
|------|-------------|-----------|
| 앱 아이콘 | 512×512 PNG | 1024×1024 PNG |
| 스크린샷 | 최소 2장 (폰) | 6.7" + 5.5" 각 최소 1장 |
| 기능 그래픽 | 1024×500 | - |
| 앱 설명 | 짧은(80자) + 긴 설명 | 설명 + 키워드 |
| 개인정보 처리방침 | 필수 (URL) | 필수 (URL) |
| 콘텐츠 등급 | IARC 설문 작성 | 연령 등급 선택 |

### 4-3. 앱 설명 (안)

**제목**: ROS2 Commander — ROS2 학습 게임

**짧은 설명**: 카드 매칭, CLI 타임어택, 아키텍처 퍼즐로 ROS2를 마스터하세요!

**긴 설명**:
```
ROS2를 재미있게 배우는 가장 빠른 방법!

3가지 게임 모드로 ROS2의 핵심 개념부터 Nav2/SLAM까지 단계별로 학습합니다.

🃏 Memory Match — ROS2 개념 카드 매칭
⌨️ Command Rush — CLI 명령어 타임어택
🔧 Node Builder — 로봇 아키텍처 연결 퍼즐

4단계 Tier 시스템:
  Tier 1: 기본 개념 (Node, Topic, Publisher...)
  Tier 2: 시스템 구조 (Launch, TF2, DDS...)
  Tier 3: Nav2/SLAM (Costmap, Planner, LiDAR...)
  Tier 4: 하드웨어 (micro-ROS, Gazebo, ros2_control...)

실제 자율순찰 로봇 프로젝트(Kevin) 시나리오 기반으로,
현업에서 바로 쓸 수 있는 실전 ROS2 지식을 게임으로 익힙니다.
```

### 4-4. 배포 프로세스

**Google Play**:
```bash
# 릴리스 빌드
flutter build appbundle --release

# 출력: build/app/outputs/bundle/release/app-release.aab
# → Google Play Console에 업로드
```
- 신규 계정은 12명 테스터 × 14일 클로즈드 테스트 필수
- 심사: 수시간 ~ 7일

**Apple App Store**:
```bash
# iOS 빌드 (macOS 필요)
flutter build ipa --release

# → Xcode 또는 Transporter로 App Store Connect 업로드
```
- TestFlight 베타 테스트 → 심사 제출
- 심사: 1~3일 (복잡한 경우 더 걸릴 수 있음)

---

## Phase 5: 출시 후 운영

### 5-1. 수익화 전략 (선택)

| 모델 | 설명 |
|------|------|
| 무료 + 광고 | Tier 1~2 무료, 광고 배너 (AdMob) |
| 프리미엄 | Tier 1 무료, Tier 3~4 인앱결제로 잠금 해제 |
| 완전 유료 | $2.99~$4.99 일괄 판매 |
| 무료 배포 | 포트폴리오/커뮤니티 기여 목적 |

ROS2 학습자 니치 시장 특성상, **무료 배포 + GitHub 오픈소스**로 커뮤니티 평판을 쌓는 것도 좋은 전략입니다.

### 5-2. 콘텐츠 확장 아이디어

- Tier 5: ROS2 Security / DDS QoS 심화
- 일일 챌린지 (Daily Challenge)
- 리더보드 (Firebase 연동)
- 다국어 지원 (영어/한국어/일본어)
- ROS2 Humble/Jazzy/Rolling 버전별 명령어 분기

---

## 전체 타임라인 요약

| Phase | 기간 | 핵심 산출물 |
|-------|------|-----------|
| Phase 0: 전략 결정 | 1주 | 프레임워크 선정, UX 와이어프레임 |
| Phase 1: 설계 | 1~2주 | 데이터 JSON 분리, 화면 설계, 상태 관리 |
| Phase 2: 개발 | 3~5주 | Flutter 앱 완성 (3모드 + 4Tier) |
| Phase 3: 테스트 | 1~2주 | 다기기 테스트, 폴리싱, 효과음 |
| Phase 4: 배포 준비 | 1주 | 스토어 자산, 빌드, 심사 제출 |
| Phase 5: 운영 | 지속 | 콘텐츠 업데이트, 피드백 반영 |

**예상 총 기간: 7~11주** (풀타임 기준)

---

## 즉시 시작할 수 있는 액션

1. **Flutter 설치** 및 샘플 앱 빌드 확인
2. **학습 데이터를 JSON으로 분리** (Python 스크립트로 자동 변환)
3. **카드 뒤집기 프로토타입** — Flutter AnimatedBuilder로 핵심 인터랙션 검증
4. **Google Play 개발자 계정 등록** ($25, 승인 최대 48시간)
