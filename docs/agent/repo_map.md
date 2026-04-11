# 仓库结构图

## 根目录

- [README.md](../../README.md)：项目总入口
- [docs/README.md](../README.md)：文档总入口
- `src/`：代码与包

## 关键包

- `src/dual_nero_description`
  - 模型显示、TF 可视化、RViz 纯显示
- `src/dual_nero_moveit_config`
  - MoveIt 规划 demo、controllers 映射、fake `ros2_control`
- `src/dual_nero_driver`
  - `pyAgxArm` 适配层与单臂测试脚本
- `src/dual_nero_bridge`
  - 真实执行桥、joint state、action/topic 执行、preflight
- `src/dual_nero_bringup`
  - 真机启动入口和操作员默认参数

## 当前关键代码入口

- `src/dual_nero_bringup/launch/real_hardware.launch.py`
- `src/dual_nero_bridge/dual_nero_bridge/preflight.py`
- `src/dual_nero_bridge/dual_nero_bridge/preflight_codes.py`
- `src/dual_nero_bridge/dual_nero_bridge/follow_joint_trajectory_server.py`
- `src/dual_nero_bridge/dual_nero_bridge/joint_command_bridge.py`
- `src/dual_nero_bridge/dual_nero_bridge/real_execution_node.py`

## 当前关键脚本入口

- `src/dual_nero_driver/scripts/test_left_arm.py`
- `src/dual_nero_driver/scripts/test_right_arm.py`
- `src/dual_nero_driver/scripts/test_dual_arm.py`
- `src/dual_nero_bridge/scripts/send_left_arm_goal.py`
- `src/dual_nero_bridge/scripts/send_right_arm_goal.py`
- `src/dual_nero_bridge/scripts/validate_moveit_pipeline.py`

## 当前关键 console_scripts 入口

- `ros2 run dual_nero_bridge send_left_arm_goal`
- `ros2 run dual_nero_bridge send_right_arm_goal`
- `ros2 run dual_nero_bridge validate_moveit_pipeline`
