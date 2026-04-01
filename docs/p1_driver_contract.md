# dual_nero_ws P1 Driver Contract

## 目的

本文档记录 `dual_nero_ws` 完成 P1 后的驱动接入合同。

P1 已落地结果：

- 命名唯一性：PASS
- URDF / SRDF / controllers 一致性：PASS
- group 命名唯一性：PASS
- TF 主干口径唯一性：PASS
- P1 真机执行链方案：**B 方案，真实执行 bridge**

## 当前结论

P1 已完成的真实执行链不是 native `ros2_control` hardware plugin，而是：

- 以 [../src/dual_nero_driver](../src/dual_nero_driver) 作为唯一硬件后端
- 以 [../src/dual_nero_bridge](../src/dual_nero_bridge) 作为 ROS 2 真实执行桥
- 以 [../src/dual_nero_bringup](../src/dual_nero_bringup) 作为 operator-facing 入口

这一实现仍满足 P1 合同的核心要求：

- 不破坏现有 `display`
- 不破坏现有 `planning_demo`
- 为 MoveIt 执行层提供真实后端入口
- 不引入第二套 joint / group / controller / TF 命名

## 冻结名称

以下名称继续冻结：

- joints：`left_joint1..7`、`right_joint1..7`
- groups：`left_arm`、`right_arm`、`dual_arms`
- controllers：`left_arm_controller`、`right_arm_controller`、`joint_state_broadcaster`
- TF trunk：`world -> dual_base_plate -> dual_column -> dual_crossbar -> {left/right}_base_link -> ...`

P1 之后仍不允许：

- 把 `left_` / `right_` 改成其它前缀
- 新增 `both_arms`、`arm_left`、`arm_right`、`leftarm`、`rightarm`
- 通过改 group / controller 名称去适配驱动

## 执行接口合同

### ROS 2 真实执行桥

P1 新增的真实执行入口如下：

- `/joint_states`
- `/left_arm_controller/follow_joint_trajectory`
- `/right_arm_controller/follow_joint_trajectory`
- `/left_arm_controller/joint_command`
- `/right_arm_controller/joint_command`
- `/dual_arms/joint_command`

### joint state 合同

- joint 数量固定：14
- 顺序固定：`left_joint1..7` + `right_joint1..7`
- position 必须可读
- velocity 若后端可读则发布；若后端不可读，bridge 允许空 velocity，但必须明确说明

### trajectory 合同

- `left_arm_controller` 与 `right_arm_controller` 继续使用 `FollowJointTrajectory`
- action namespace 继续是 `follow_joint_trajectory`
- 这是 bridge/shim，不是严格实时控制器
- P1.1 当前明确只支持 **单点 trajectory goal**
- `dual_arms` 不新增第二套 controller name；双臂同步入口通过直接命令 topic 和上层已有双臂规划语义衔接

## 与现有包的边界

- [../src/dual_nero_description](../src/dual_nero_description)
  - 继续只负责 `display`
- [../src/dual_nero_moveit_config](../src/dual_nero_moveit_config)
  - 继续只负责 `planning_demo`
- [../src/dual_nero_driver](../src/dual_nero_driver)
  - 继续作为唯一 `pyAgxArm` 适配层
- [../src/dual_nero_bridge](../src/dual_nero_bridge)
  - 负责真实执行桥
- [../src/dual_nero_bringup](../src/dual_nero_bringup)
  - 负责真机入口和 operator 默认参数

## 限制与下一阶段

当前 P1 仍未完成：

- native `ros2_control` C++ hardware plugin
- 严格实时轨迹控制
- 真正的 `joint_state_broadcaster` / controller_manager 真机链
- diagnostics / calibration / recovery

下一阶段如果要进入 P2，应优先处理：

1. bridge 到 native hardware plugin 的演进路径
2. 轨迹时间参数与实时执行一致性
3. 通信异常、急停、恢复与同步误差控制
