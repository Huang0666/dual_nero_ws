# dual_nero_ws

`dual_nero_ws` 是一个面向 NERO 双臂机器人的 ROS 2 工作区。

当前仓库明确分成三层：

- `display`
  - 包：[src/dual_nero_description](src/dual_nero_description)
  - 入口：`ros2 launch dual_nero_description display_dual_urdf.launch.py`
- `planning_demo`
  - 包：[src/dual_nero_moveit_config](src/dual_nero_moveit_config)
  - 入口：`ros2 launch dual_nero_moveit_config demo.launch.py`
- `real_hardware_execution`
  - 包：[src/dual_nero_driver](src/dual_nero_driver)、[src/dual_nero_bridge](src/dual_nero_bridge)、[src/dual_nero_bringup](src/dual_nero_bringup)
  - 入口：`ros2 launch dual_nero_bringup real_hardware.launch.py`

## 当前状态

- 仓库已完成第一版 `real_hardware_execution`。
- 当前采用 **B 方案 real-hardware bridge**，不是 native C++ `ros2_control` hardware plugin。
- `pyAgxArm` 只通过 `dual_nero_driver` 使用，不在其它包中散落调用。
- MoveIt 真实执行入口通过以下 action 暴露：
  - `/left_arm_controller/follow_joint_trajectory`
  - `/right_arm_controller/follow_joint_trajectory`

## P1.1 收口结果

- `FollowJointTrajectory` 当前采用 **方案 A**：
  - 每个 goal 只支持 **1 个 trajectory point**
  - 如果 `trajectory.points` 数量大于 1，会在 goal 校验阶段显式拒绝
  - `time_from_start` 会做非负检查，但当前不实现多点时间语义
- bridge 的失败语义已明确：
  - 两臂都不可用时，节点启动失败并退出
  - 单臂不可用时，进入 degraded mode
  - 单臂命令只允许打到可用臂
  - 双臂命令和完整 `/joint_states` 在单臂缺失时会被拒绝或停止发布
  - `allow_motion=false` 时，topic/action 命令都会显式拒绝
  - `enable_on_start=false` 时，bridge 不做 lazy enable，动作命令会显式拒绝

## 冻结命名合同

- joints：`left_joint1..7`、`right_joint1..7`
- groups：`left_arm`、`right_arm`、`dual_arms`
- controllers：`left_arm_controller`、`right_arm_controller`、`joint_state_broadcaster`
- TF trunk：`world -> dual_base_plate -> dual_column -> dual_crossbar -> {left/right}_base_link -> ...`

## 冒烟验证入口

- 左臂 read-only：
  - `python src/dual_nero_driver/scripts/test_left_arm.py --config src/dual_nero_bridge/config/hardware_params.yaml`
- 右臂 read-only：
  - `python src/dual_nero_driver/scripts/test_right_arm.py --config src/dual_nero_bridge/config/hardware_params.yaml`
- 双臂 read-only：
  - `python src/dual_nero_driver/scripts/test_dual_arm.py --config src/dual_nero_bridge/config/hardware_params.yaml`
- 左臂 action 预览：
  - `python src/dual_nero_bridge/scripts/send_left_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml`
- 右臂 action 预览：
  - `python src/dual_nero_bridge/scripts/send_right_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml`

完整冒烟模板见：[docs/p1_smoke_test_report.md](docs/p1_smoke_test_report.md)

## 当前未完成

- native `ros2_control` C++ hardware plugin
- 真正的 `controller_manager` / `joint_state_broadcaster` 真机链
- 严格时间参数轨迹控制
- diagnostics / calibration / fault recovery
- 更完整的急停闭环和通信异常恢复

## 相关文档

- [docs/project_baseline.md](docs/project_baseline.md)
- [docs/p1_driver_contract.md](docs/p1_driver_contract.md)
- [docs/p1_execution_report.md](docs/p1_execution_report.md)
- [docs/p1_smoke_test_report.md](docs/p1_smoke_test_report.md)
