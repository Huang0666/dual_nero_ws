# 仿真运行手册

## 作用

说明当前如何启动 Gazebo/gz sim 主线，并保持与 P1-P4 上层合同一致。

## 当前定位

- 真机成果保留
- 真机暂不作为主开发环境
- 当前后续开发主线切到 `Gazebo Harmonic / gz sim`
- 当前仿真目标是先跑通空间关系、控制器合同和任务入口，不追一步到位的高保真动力学

## 当前正式入口

```bash
ros2 launch dual_nero_bringup simulation.launch.py
```

## 当前启动内容

- gz sim 世界
- 双臂机器人模型
- `robot_state_publisher`
- `joint_state_broadcaster`
- `left_arm_controller`
- `right_arm_controller`
- `move_group`
- MoveIt RViz（默认开启）

## 当前推荐验证

1. 确认 `/joint_states` 可读
2. 确认 `left_arm_controller` / `right_arm_controller` action 存在
3. 执行：

```bash
ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync
```

4. 执行：

```bash
ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync --target safe
```

## 复用边界

仿真中继续复用：

- `run_dual_arm_task`
- MoveIt group
- `FollowJointTrajectory`
- controller 命名
- 任务 YAML

仿真中替换的是：

- 真机 runtime / driver / pyAgxArm / CAN

## 当前规则边界

- 任务层入口继续复用当前 P4
- `FollowJointTrajectory` 合同继续复用
- 纯真机项例如 CAN、enable、offline、BUS-OFF 不在当前仿真主线里伪造
- 当前仿真重点是空间关系、碰撞关系、任务入口和控制器合同

## 当前限制

- 当前 URDF 仍在继续对齐真实工位
- 当前 world 只是起步世界，不代表最终工位
- 当前阶段不承诺高保真动力学
- 夹爪、视觉、障碍物场景后续再接入
