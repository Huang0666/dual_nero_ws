# dual_nero_ws

`dual_nero_ws` 是 NERO 双臂机器人 ROS 2 工作区。

## 目录结构

- `src/dual_nero_description`：模型显示
- `src/dual_nero_moveit_config`：规划演示
- `src/dual_nero_driver` + `src/dual_nero_bridge` + `src/dual_nero_bringup`：真机执行

## 当前状态

- P1：已完成
- P2：已完成并通过现场验收
- 当前执行架构：bridge（未切 native `ros2_control`）
- 当前阶段：P4 双臂固定场景任务闭环
- 当前后续开发主线：Gazebo / gz sim 仿真

长期目标：

- 双臂协调运动
- 避障
- 视觉接入
- 简单抓取任务

当前阶段进展：

- P1：已完成
- P2：已完成并通过现场验收
- P3-A：已完成
- P3-B：主体已完成
- P3-C：暂缓
- P4：双臂固定场景任务入口已落地

当前路线入口：

- [docs/human/overview/roadmap.md](docs/human/overview/roadmap.md)

文档入口：

- 给人看：[docs/human/README.md](docs/human/README.md)
- 给 agent 看：[docs/agent/README.md](docs/agent/README.md)
- 文档总入口：[docs/README.md](docs/README.md)

## 真机入口

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py
```

## 仿真入口

```bash
ros2 launch dual_nero_bringup simulation.launch.py
```

## P4 双臂正式任务入口

```bash
ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync
```

任务配置：

- `src/dual_nero_bridge/config/p4_tasks.yaml`

## 推荐启动模式

只读模式：

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=false enable_on_start:=false
```

动作模式：

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=true enable_on_start:=true
```

## Action 示例

```bash
ros2 run dual_nero_bridge send_left_arm_goal \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --execute

ros2 run dual_nero_bridge send_right_arm_goal \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --execute
```

## P3-B MoveIt 验证示例

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm --bridge-final-point-execute
```

## 注意事项

- `preflight_enabled=false` 仅关闭运行时 gate，不会关闭启动期检查。
- USB-CAN 有插拔或重启后，先确认映射再重启 launch。
- 现场恢复优先按 [docs/human/phases/p3/recovery_sop.md](docs/human/phases/p3/recovery_sop.md) 执行，不要临场拼凑命令。
