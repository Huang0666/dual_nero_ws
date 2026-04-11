# dual_nero_ws 基线盘点

## 仓库定位

当前仓库已形成三层明确结构：

- `display`：已完成
- `planning_demo`：已完成
- `real_hardware_execution`：已完成（bridge v1，P1.1 已完成语义收口）

当前三层对应关系：

- `display`
  - 包：[../../../src/dual_nero_description](../../../src/dual_nero_description)
  - 作用：模型显示、TF 可视化、RViz 纯显示
- `planning_demo`
  - 包：[../../../src/dual_nero_moveit_config](../../../src/dual_nero_moveit_config)
  - 作用：MoveIt 规划 demo、fake `ros2_control`
- `real_hardware_execution`
  - 包：[../../../src/dual_nero_driver](../../../src/dual_nero_driver)、[../../../src/dual_nero_bridge](../../../src/dual_nero_bridge)、[../../../src/dual_nero_bringup](../../../src/dual_nero_bringup)
  - 作用：真实 joint state 回读、真实关节命令下发、MoveIt 可对接的最小真实执行入口

## 仓库结构图

```text
dual_nero_ws/
|-- README.md
|-- docs/
|   |-- README.md
|   |-- human/
|   `-- agent/
`-- src/
    |-- dual_nero_description/
    |-- dual_nero_moveit_config/
    |-- dual_nero_driver/
    |-- dual_nero_bridge/
    `-- dual_nero_bringup/
```

## 已完成 / 未完成

### 已完成

- 双臂 URDF/Xacro、mesh、RViz 显示链已完成
- MoveIt 的 SRDF、运动学、controllers 映射和 demo 启动链已完成
- `dual_nero_driver` 已完成第一版 non-invasive backend
- `dual_nero_bridge` 已完成第一版真实执行桥
- `dual_nero_bringup` 已完成第一版真机入口
- P1.1 已补充：
  - `FollowJointTrajectory` 单点语义收口
  - 最小 action 客户端示例
  - 冒烟验证模板
  - 统一失败语义和日志约定

### 未完成

- native `ros2_control` C++ hardware plugin
- 真正的 `controller_manager` / `joint_state_broadcaster` 真硬件链
- 严格实时轨迹执行与控制周期保证
- diagnostics / calibration / fault recovery
- 更完整的急停链、通信异常恢复与同步误差补偿

### 占位 / 仍保留的 demo 组件

- [../../../src/dual_nero_moveit_config/config/dual_nero_description.ros2_control.xacro](../../../src/dual_nero_moveit_config/config/dual_nero_description.ros2_control.xacro) 仍使用 `mock_components/GenericSystem`
- [../../../src/dual_nero_moveit_config/launch/demo.launch.py](../../../src/dual_nero_moveit_config/launch/demo.launch.py) 仍然只代表 `planning_demo`
- 当前 bridge 的 `FollowJointTrajectory` 是执行适配层，不是原生 `ros2_control` controller

## 命名规范

后续开发继续冻结以下命名，不再引入第二套语义等价名字。

### 关节命名

- `left_joint1` 到 `left_joint7`
- `right_joint1` 到 `right_joint7`

### 连杆命名

- `world`
- `dual_base_plate`
- `dual_column`
- `dual_crossbar`
- `left_base_link` / `right_base_link`
- `left_link1..7` / `right_link1..7`
- `left_end_effector` / `right_end_effector`

### 固定关节命名

- `left_mount_joint`
- `right_mount_joint`
- `left_end_effector_joint`
- `right_end_effector_joint`

### 规划组命名

- `left_arm`
- `right_arm`
- `dual_arms`

### 控制器命名

- `left_arm_controller`
- `right_arm_controller`
- `joint_state_broadcaster`

### TF 命名

- 权威主干：`world -> dual_base_plate -> dual_column -> dual_crossbar`
- 每条机械臂从 `{side}_base_link` 向下展开

### 禁止新增的别名

- `l_` / `r_`
- `arm_left` / `arm_right`
- `leftarm` / `rightarm`
- `both_arms`
- 任意与 `left_arm`、`right_arm`、`dual_arms` 等价的第二套 group / controller / topic / namespace 名字
