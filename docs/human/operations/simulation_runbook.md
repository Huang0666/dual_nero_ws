# 仿真运行手册

## 作用

说明当前如何启动 Gazebo / gz sim 主线，并保持与 P1-P4 上层合同一致。

## 当前定位

- 真机成果保留，但真机暂不作为主开发环境
- 当前后续开发主线切到 `Gazebo Harmonic / gz sim`
- 当前默认采用 server-only 启动，优先保证 `controller_manager`、`/joint_states`、`FollowJointTrajectory` 和任务入口稳定可用
- `P4` 基线仿真链已验证通过；`P5` 的最新 scene / 插件链改动仍待 Linux 回归确认

## 当前正式入口

```bash
ros2 launch dual_nero_bringup simulation.launch.py
```

默认参数要点：

- `with_gz_gui:=false`
- `spawn_sim_controllers:=false`

## 当前启动内容

- gz sim 世界
- 双臂机器人模型
- `robot_state_publisher`
- `controller_manager`
- `joint_state_broadcaster`
- `left_arm_controller`
- `right_arm_controller`
- `move_group`
- MoveIt RViz（默认开启）

说明：

- `P4` 基线验证通过时，默认由 sim ros2_control/controller_manager 自己加载并激活 controller
- `simulation.launch.py` 中的手动 controller `spawner` 仅保留为回退开关，不再默认触发

当前新候选路径：

- 已把仿真控制插件链从 `gz_ros2_control` 切向 `ign_ros2_control`
- 目的：匹配当前 `ROS 2 Humble + ign gazebo` 组合
- 这条新路径尚未最终验收，必须先看 Linux 回归结果

如某些环境确实没有自动激活 controller，可显式打开回退路径：

```bash
ros2 launch dual_nero_bringup simulation.launch.py spawn_sim_controllers:=true
```

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

## 当前新窗口优先验证

先重新编译并 source：

```bash
cd ~/wkw_ws/dual_nero_ws_test/dual_nero_ws
colcon build --packages-select dual_nero_bridge dual_nero_bringup dual_nero_moveit_config
source install/setup.bash
```

然后启动：

```bash
ros2 launch dual_nero_bringup simulation.launch.py
```

重点看日志中：

- `sim_control_hardware_plugin`
- `sim_control_system_plugin`
- `sim_control_system_plugin_name`
- 不应再出现 `Failed to load system plugin`

再开新终端验证：

```bash
source ~/wkw_ws/dual_nero_ws_test/dual_nero_ws/install/setup.bash
ros2 control list_controllers
```

目标是看到：

- `joint_state_broadcaster active`
- `left_arm_controller active`
- `right_arm_controller active`

只有 controller 恢复后，才继续跑：

```bash
ros2 run dual_nero_bridge run_dual_arm_task \
  --task dual_stage_demo \
  --task-config ~/wkw_ws/dual_nero_ws_test/dual_nero_ws/install/dual_nero_bridge/share/dual_nero_bridge/config/p5_tasks.yaml \
  --scene-config ~/wkw_ws/dual_nero_ws_test/dual_nero_ws/install/dual_nero_bridge/share/dual_nero_bridge/config/p5_scene_sim.yaml
```

## 当前已验证通过

- `ros2 control list_controllers` 可见：
  - `joint_state_broadcaster active`
  - `left_arm_controller active`
  - `right_arm_controller active`
- `/joint_states` 已开始发布
- `ros2 action list | grep follow_joint_trajectory` 已返回左右臂 action
- `ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync` 已完成 prep / return 全流程

注意：

- 上面“已验证通过”针对的是 `P4` 基线仿真链。
- `dual_stage_demo`、`sim_static_demo` 以及最新 `ign_ros2_control` 插件链还不在这个“已验证通过”集合里。

## 复用边界

仿真中继续复用：

- `run_dual_arm_task`
- MoveIt group
- `FollowJointTrajectory`
- controller 命名
- 任务 YAML

仿真中替换的是：

- 真机 runtime / driver / pyAgxArm / CAN

## 当前已知噪声

- RViz 中 `Action server: /recognize_objects not available` 可忽略，当前未接视觉识别链
- MoveIt 中 `No 3D sensor plugin(s) defined for octomap updates` 可忽略，当前未接 3D 传感器
- Gazebo GUI 渲染链当前不稳定，因此默认不启 GUI，不作为当前阻塞项

## 当前限制

- 当前 URDF 仍在继续对齐真实工位
- 当前 world 只是起步世界，不代表最终工位
- 当前阶段不承诺高保真动力学
- 夹爪、视觉、障碍物场景后续再接入
