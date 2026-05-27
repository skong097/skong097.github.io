---
title: "colcon symlink 빌드 환경에서 웹 대시보드 정적 파일이 404로 사라지던 이유"
date: 2026-05-23
draft: false
tags: ["robotics", "ros2", "colcon", "fastapi", "static-files", "symlink"]
categories: ["robotics"]
summary: "MOCA 카페 로봇의 관제 웹 대시보드를 ROS 빌드 환경(colcon symlink 설치)에서 띄우면 HTML·JS·CSS가 404로 사라지던 문제를, 정적 파일 prefix 분리와 symlink 추적 허용으로 해결한 기록"
cover:
  alt: "colcon symlink 정적 파일 경로"
  hidden: true
ShowToc: true
TocOpen: true
---

## 증상

MOCA 카페 로봇의 관제용 웹 대시보드는 FastAPI 위에 정적 HTML·JS·CSS를 얹은 단일 페이지 형태입니다. 개발 단계에서는 그냥 `uvicorn`으로 띄워도 멀쩡히 동작했는데, ROS 빌드 환경(`colcon build --symlink-install`)으로 패키지를 설치한 뒤 같은 코드를 실행하면 **모든 정적 파일이 404**로 떨어졌습니다.

브라우저 콘솔에는 다음과 비슷한 줄이 줄줄이 떴습니다.

```
GET /static/dashboard.css  404 (Not Found)
GET /static/app.js         404 (Not Found)
GET /static/icons/...      404 (Not Found)
```

API 엔드포인트(`/api/...`)는 정상이었습니다. 즉 서버는 살아 있고, **정적 파일 경로만 보지 못하는 상태**였습니다.

## 추적

### 1) 경로는 맞다 — 그런데 못 본다

가장 먼저 의심한 것은 "정적 파일 디렉터리 경로가 잘못 잡혔다"였습니다. 그러나 서버 로그에 찍힌 정적 디렉터리 절대경로를 따라가 보면, 거기에 파일이 실제로 존재했습니다. 손으로 `ls` 해도 멀쩡히 나오고, `cat`도 됩니다.

### 2) colcon symlink가 만들어낸 사슬

차이는 **경로의 종류**였습니다. `colcon build --symlink-install`은 빌드 결과를 복사하지 않고 **심볼릭 링크로 install 폴더에 연결**합니다. 그것도 한 번이 아니라 여러 단계로:

```
install/<pkg>/share/<pkg>/static/  →  src/<pkg>/static/    (심볼릭)
src/<pkg>/static/                    →  실제 정적 파일들
```

워크스페이스 구성에 따라 중간에 또 한 단계가 더 끼기도 합니다. 즉 정적 파일 요청 하나를 처리하려면 서버가 **심볼릭 링크를 여러 번 따라가야** 했습니다.

FastAPI의 정적 파일 핸들러(`StaticFiles`)는 기본적으로 **심볼릭을 따라가지 않거나**, 따라가더라도 **경로가 등록된 루트를 벗어나지 않는지 보안 검사**를 합니다. 위처럼 여러 단계의 symlink가 install/share 밖의 src/ 폴더를 가리키면, 보안 검사 로직이 "이건 등록된 루트 밖이다"라고 판단하여 요청을 거부할 수 있었습니다. 결과는 404였습니다.

### 3) 결정적인 단서

같은 빌드 환경에서 `--symlink-install` 대신 일반 빌드(파일 복사)로 설치해 보았더니, 정적 파일이 정상적으로 떴습니다. 즉 문제는 정확히 **symlink 사슬을 따라가는 단계에서 보안 검사가 잘라낸 것**이었습니다.

## 접근

해결 방향은 두 가지였습니다.

### 1) 정적 파일 경로를 명시적 prefix로 분리해 등록

기존에는 정적 파일이 라우터들과 같은 루트 아래에 묶여 있었습니다. 이를 별도의 prefix(`/static`)와 별도의 실제 디렉터리로 **명확하게 분리해 등록**하였습니다.

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# 정적 디렉터리의 절대경로 (symlink가 어디로 가든 최종 실제 경로 사용)
STATIC_DIR = Path(__file__).parent.joinpath("static").resolve()

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR), follow_symlink=True),
    name="static",
)
```

핵심은 두 가지입니다.

- `Path(...).resolve()`로 **심볼릭 사슬을 미리 풀어 실제 경로를 마운트**합니다. 런타임에 따라갈 사슬이 없으므로 보안 검사가 트리거되지 않습니다.
- `follow_symlink=True` 옵션을 켜서, 그 안에 또 다른 symlink가 섞여 있을 때도 따라가도록 허용하였습니다.

### 2) 빌드·실행 환경에서 절대경로가 같은 곳을 가리키는지 검증

배포할 때 환경별로 정적 디렉터리가 어디를 가리키는지 자동 출력하는 진단 라인을 한 줄 추가하였습니다.

```python
app.on_event("startup")
def _log_static_root():
    print(f"[static] mount path = {STATIC_DIR}")
    print(f"[static] exists = {STATIC_DIR.exists()}")
```

기동 직후 로그만 보면 "정적 디렉터리가 어디로 풀려 있는지"를 즉시 알 수 있어, 같은 종류의 문제가 재발했을 때 원인을 1분 안에 좁힐 수 있게 되었습니다.

## 결과

| 환경 | 변경 전 | 변경 후 |
|---|---|---|
| `uvicorn` 직접 실행(개발) | 정상 | 정상 |
| `colcon build` (복사 설치) | 정상 | 정상 |
| `colcon build --symlink-install` | **정적 파일 404** | 정상 |

빌드 방식에 따라 동작 여부가 갈리던 사각지대가 사라졌습니다. 빌드 환경을 모드별로 의식하지 않고 동일하게 다룰 수 있게 된 것이 가장 큰 이득이었습니다.

## 배운 점

- **개발 환경에서 멀쩡하다고 빌드 환경에서도 멀쩡할 것이라 단정하지 않는다.** 같은 코드도 빌드·설치 방식에 따라 경로의 종류(실경로 / 심볼릭)가 달라지고, 그 차이가 보안 검사·캐시 같은 곳에서 엇갈린 동작을 만듭니다.
- **경로를 마운트할 때는 `resolve()`로 풀어두는 편이 안전**합니다. 런타임에 따라갈 심볼릭을 줄이면, 보안 검사로 인한 사고도 같이 줄어듭니다.
- ROS 생태계에서 `--symlink-install`은 개발 편의(소스 수정 → 재빌드 없이 반영) 때문에 자주 쓰지만, **정적 파일을 다루는 패키지에서는 마운트 방식을 한 번 점검**할 가치가 있습니다. 같은 케이스를 미래의 다른 패키지에서 또 만나게 될 가능성이 높습니다.
