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
- 当前阶段：P3 准备中

参考文档：

- [docs/p2_acceptance_report.md](docs/p2_acceptance_report.md)
- [docs/project_status.md](docs/project_status.md)
- [docs/next_actions.md](docs/next_actions.md)

## 真机入口

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py
```

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
python3 src/dual_nero_bridge/scripts/send_left_arm_goal.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --execute

python3 src/dual_nero_bridge/scripts/send_right_arm_goal.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --execute
```

## 注意事项

- `preflight_enabled=false` 仅关闭运行时 gate，不会关闭启动期检查。
- USB-CAN 有插拔或重启后，先确认映射再重启 launch。
