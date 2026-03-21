---
title: "GHOST-5 작업 일지 | Phase 1 — M01 완료 ✅"
date: 2026-03-21
draft: true
tags: ["ros2", "slam", "zenoh"]
categories: ["ros2"]
description: "**날짜**: 2026-03-18 **현재 단계**: Phase 1 — M01 완료 / M02 진입 준비 **작업자**: gjkong@pc"
---

# GHOST-5 작업 일지 | Phase 1 — M01 완료 ✅
**날짜**: 2026-03-18  
**현재 단계**: Phase 1 — M01 완료 / M02 진입 준비  
**작업자**: gjkong@pc  
**프로젝트 홈**: `/home/gjkong/ghost5`

---

## 오늘 작업 요약

| 순서 | 작업 내용 | 상태 |
|------|-----------|------|
| 1 | `ghost5_bringup/config/qos_profiles.py` 작성 | ✅ 완료 |
| 2 | `ghost5_bringup/config/zenoh_config.json5` 작성 | ✅ 완료 |
| 3 | `tests/unit/test_m01_verify.py` 작성 | ✅ 완료 |
| 4 | M01 완료 조건 검증 **21/21 PASS** | ✅ 완료 |

---

## M01 최종 검증 결과

```
결과: 21/21 통과  |  실패: 0
✅ PASS  M01 완료 조건 모두 충족 🎉
→ M02 (SLAM 패키지 설정) 진행 가능
```

| 항목 | 결과 |
|------|------|
| qos_profiles.py 임포트 + 7개 QoSProfile | ✅ |
| TOPIC_QOS_MAP, get_qos() | ✅ |
| zenoh_config.json5 파싱 (mode/listen/scouting) | ✅ |
| RMW_IMPLEMENTATION=rmw_zenoh_cpp | ✅ |
| ROS_DOMAIN_ID=42 | ✅ |
| libzenohc.so ld 캐시 등록 | ✅ |
| rmw_zenoh_cpp, zenoh_cpp_vendor 패키지 | ✅ |

> 📌 pyjson5 미설치 상태 — fallback(정규화) 파싱으로 통과.  
> 필요 시: `source ~/ghost5/venv/bin/activate && pip install pyjson5`

---

## 확정된 파일 위치

```
ghost5_ws/src/ghost5_bringup/
└── config/
    ├── qos_profiles.py          ✅ v1.0
    └── zenoh_config.json5       ✅ v1.0

ghost5_ws/tests/unit/
└── test_m01_verify.py           ✅ v1.1 (pyjson5 fallback 포함)
```

---

## 다음 작업 — M02 (SLAM 패키지 설정)

- [ ] `ghost5_slam` ROS2 패키지 생성
- [ ] `slam_toolbox` 파라미터 설정 (`slam_params_robot_N.yaml`)
- [ ] 5대 로봇 개별 네임스페이스 `/robot_N/` SLAM 구성
- [ ] Multi-Robot 지도 병합 설계

---

## 참고 문서

| 문서 | 버전 | 위치 |
|------|------|------|
| GHOST5_plan_v2.md | v2.1 | `/home/gjkong/ghost5/` |
| GHOST5_구현단계_v2.md | v1.2 | `/home/gjkong/ghost5/` |
| 작업 일지 (전일) | 2026-03-17 | `GHOST5_작업일지_20260317_Phase1_M01.md` |

---

*다음 세션 시작 시 이 파일을 참고하여 M02부터 진행.*
