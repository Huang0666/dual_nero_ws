# dual_nero_ws

`dual_nero_ws` 是一个面向 NERO 双臂机器人的 ROS 2 工作区。

当前仓库明确分成三层：

- `display`
  - 包：[src/dual_nero_description](F:\github\dual_nero_ws\src\dual_nero_description)
  - 入口：`ros2 launch dual_nero_description display_dual_urdf.launch.py`
- `planning_demo`
  - 包：[src/dual_nero_moveit_config](F:\github\dual_nero_ws\src\dual_nero_moveit_config)
  - 入口：`ros2 launch dual_nero_moveit_config demo.launch.py`
- `real_hardware_execution`
  - 包：[src/dual_nero_driver](F:\github\dual_nero_ws\src\dual_nero_driver)、[src/dual_nero_bridge](F:\github\dual_nero_ws\src\dual_nero_bridge)、[src/dual_nero_bringup](F:\github\dual_nero_ws\src\dual_nero_bringup)
  - 入口：`ros2 launch dual_nero_bringup real_hardware.launch.py`

本轮实现说明：

- 仓库已新增第一版 `real_hardware_execution`。
- 当前采用 **B 方案 bridge**，不是 native C++ `ros2_control` hardware plugin。
- `pyAgxArm` 仍然只通过 `dual_nero_driver` 使用，不在其它包里散落调用。
- MoveIt 真实执行入口通过以下 action 名称暴露：
  - `/left_arm_controller/follow_joint_trajectory`
  - `/right_arm_controller/follow_joint_trajectory`
- 这是一层真实执行桥，`FollowJointTrajectory` 为 best-effort point-to-point shim，不承诺严格实时轨迹控制。

冻结命名合同：

- joints：`left_joint1..7`、`right_joint1..7`
- groups：`left_arm`、`right_arm`、`dual_arms`
- controllers：`left_arm_controller`、`right_arm_controller`、`joint_state_broadcaster`
- TF trunk：`world -> dual_base_plate -> dual_column -> dual_crossbar -> {left/right}_base_link -> ...`

当前未完成：

- native `ros2_control` C++ hardware plugin
- 严格时间参数轨迹控制
- diagnostics / calibration / fault recovery
- 更完整的急停闭环和通信异常恢复

相关文档：

- [docs/project_baseline.md](F:\github\dual_nero_ws\docs\project_baseline.md)
- [docs/p1_driver_contract.md](F:\github\dual_nero_ws\docs\p1_driver_contract.md)
- [docs/p1_execution_report.md](F:\github\dual_nero_ws\docs\p1_execution_report.md)
