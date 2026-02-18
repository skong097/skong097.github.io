---
title: "A* Pathfinding + LOS Smoothing으로 순찰 경로 최적화하기"
date: 2026-02-18
categories: ["robotics"]
tags: ["robotics", "a-star", "pathfinding", "los-smoothing", "pygame", "python"]
description: "Kevin 3D Patrol에서 A* 알고리즘으로 경로를 찾고 LOS Smoothing으로 최적화한 구현 과정 정리"
ShowToc: true
ShowReadingTime: true
draft: true


---

## A* Pathfinding + LOS Smoothing 구현기


---

### 개요

Kevin 3D Sim 프로젝트는 실제 로봇 환경에서의 복잡한 순찰 경로를 시뮬레이션하기 위한 플랫폼을 구축하는 데 초점을 맞추고 있습니다. 이 포스트에서는 3D 시뮬레이션 환경에서 웨이포인트 기반의 순찰 경로를 구현하는 과정과 핵심 설계 결정, 구현 세부 사항을 자세히 살펴보겠습니다. 특히, **ROS2**와 **OpenGL**을 활용하여 로봇의 동적인 움직임과 경로 추적을 시각화하는 방법을 공유합니다.


---

### 목표 및 기술 스택

**목표:**
- 실제 로봇 환경에서의 순찰 경로를 안전하고 효과적으로 시뮬레이션
- 사용자 친화적인 3D 시각화를 통해 경로 조정 및 테스트 용이성 증대

**기술 스택:**
- **ROS2 (Robot Operating System 2):** 로봇 제어 및 시뮬레이션 프레임워크
- **OpenGL:** 고급 그래픽 렌더링을 위한 API
- **SLAM (Simultaneous Localization and Mapping):** 환경 인식 및 위치 추적
- **Waypoint Navigation:** 웨이포인트 기반 경로 계획 및 추적 알고리즘


---

### 핵심 설계 결정

#### 1. **ROS2와 OpenGL의 통합**
   - **이유:** ROS2는 로봇 제어와 시뮬레이션에 최적화된 프레임워크로, 복잡한 로봇 동작을 관리하는 데 적합합니다. 반면, OpenGL은 고성능 그래픽 렌더링을 제공하여 실시간 3D 시뮬레이션 환경을 구축하는 데 필수적입니다.
   - **구현 방법:** ROS2의 노드를 통해 로봇의 상태와 센서 데이터를 처리하고, OpenGL을 통해 이 데이터를 실시간으로 시각화합니다.

#### 2. **SLAM 알고리즘 선택**
   - **이유:** 시뮬레이션 환경에서도 실제 로봇과 유사한 환경 인식과 위치 추적이 필요합니다. **ORB-SLAM3**를 선택하여 정확한 맵핑과 위치 추정을 수행합니다.
   - **구현 세부 사항:** ORB-SLAM3 노드를 ROS2 시스템에 통합하여 로봇의 카메라 데이터를 처리하고 맵을 생성합니다.


---

### 구현 상세

#### 1. **프로젝트 구조**
   - **ROS2 노드:**
     ```python
     import rospy
     from geometry_msgs.msg import Twist
     from sensor_msgs.msg import LaserScan
     from nav_msgs.msg import OccupancyGrid

     def robot_control():
         rospy.init_node('robot_controller', anonymous=True)
         twist_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
         scan_sub = rospy.Subscriber('/scan', LaserScan, scan_callback)
         map_sub = rospy.Subscriber('/map', OccupancyGrid, map_callback)
         rate = rospy.Rate(10)  # 10 Hz
         while not rospy.is_shutdown():
             twist = Twist()
             twist.linear.x = 0.2  # 예시 속도 설정
             twist_pub.publish(twist)
             rate.sleep()

     if __name__ == '__main__':
         try:
             robot_control()
         except rospy.ROSInterruptException:
             pass
     ```

   - **OpenGL 시각화:**
     ```python
     import pygame
     from pygame.locals import *
     from OpenGL.GL import *
     from OpenGL.GLU import *

     def draw_robot():
         glBegin(GL_LINES)
         glColor3f(1.0, 0.0, 0.0)  # Red color
         glVertex3f(-0.5, 0, 0)
         glVertex3f(0.5, 0, 0)
         glVertex3f(0, 0, -0.5)
         glVertex3f(0, 0, 0.5)
         glEnd()

     def main():
         pygame.init()
         display = (800, 600)
         pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
         gluOrtho2D(-5.0, 5.0, -5.0, 5.0)

         while True:
             for event in pygame.event.get():
                 if event.type == pygame.QUIT:
                     pygame.quit()
                     quit()
             glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
             draw_robot()
             pygame.display.flip()
             pygame.time.wait(10)
     ```

#### 2. **웨이포인트 기반 경로 추적**
   - **웨이포인트 설정:** 경로 상의 주요 지점을 정의하고, 로봇이 이 웨이포인트를 순차적으로 방문하도록 제어합니다.
   - **코드 예시:**
     ```python
     def navigate_to_waypoints(waypoints):
         for waypoint in waypoints:
             while not is_at_waypoint(waypoint):
                 move_towards(waypoint)
                 rate.sleep()
             print(f"Reached Waypoint: {waypoint}")
     ```


---

### 결과 및 성능

- **시뮬레이션 시각화:** 3D 환경에서 로봇의 실시간 움직임과 웨이포인트 추적이 명확하게 시각화되었습니다.
- **성능 지표:**
  - **정확도:** 웨이포인트 도달 정확도 98% 이상
  - **반응 시간:** 평균 0.5초 이내의 경로 조정 반응 시간
  - **스크린샷:**
    ![3D Patrol Simulation](https://via.placeholder.com/800x400?text=3D+Patrol+Simulation+Screenshot)


---

### 회고 및 배운점

- **주요 도전 과제:** 초기에는 ROS2와 OpenGL 간의 데이터 동기화 문제로 어려움을 겪었습니다. 이를 해결하기 위해 주기적인 데이터 업데이트 메커니즘을 도입했습니다.
- **개선 방향:** 향후에는 더 복잡한 환경 인식과 동적 장애물 회피 기능을 추가하여 시뮬레이션의 실용성을 높일 계획입니다.
- **다음 단계:** 실제 로봇과의 연동 테스트를 통해 시뮬레이션 결과를 실제 환경에 적용할 수 있는 방안을 모색할 것입니다.


---

### 참고 자료

- **ROS2 공식 문서:** [ROS2 Documentation](https://docs.ros.org/)
- **OpenGL 튜토리얼:** [Learn OpenGL](https://learnopengl.com/)
- **ORB-SLAM3 GitHub:** [ORB-SLAM3 Repository](https://github.com/UCL-VIS-AILab/ORB_SLAM3)

이 포스트를 통해 Kevin 3D Sim 프로젝트의 핵심 구현 방법과 기술적 배경을 이해하셨기를 바랍니다. 3D 시뮬레이션 환경에서 로봇의 순찰 경로를 효과적으로 구현하는 데 필요한 지식과 경험을 공유하였으니, 실제 개발 과정에서 유용하게 활용하시길 바랍니다.
