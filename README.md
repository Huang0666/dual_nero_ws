# dual_nero_ws

`dual_nero_ws` 是面向 NERO 双臂机器人的 ROS 2 工作区。

当前仓库维持三层结构：

- `display`
  - 包：`src/dual_nero_description`
  - 入口：`ros2 launch dual_nero_description display_dual_urdf.launch.py`
- `planning_demo`
  - 包：`src/dual_nero_moveit_config`
  - 入口：`ros2 launch dual_nero_moveit_config demo.launch.py`
- `real_hardware_execution`
  - 包：`src/dual_nero_driver`、`src/dual_nero_bridge`、`src/dual_nero_bringup`
  - 入口：`ros2 launch dual_nero_bringup real_hardware.launch.py`

## 当前结论

- P1 已完成，并通过 bridge 路线的真机最小执行链验证。
- 当前正式执行架构仍然是 Python bridge，不切 native `ros2_control` hardware plugin。
- P2 当前聚焦稳定化与工程化：统一 preflight、启动期配置校验、日志收口、故障可诊断。

## P2 preflight 总览

当前正式执行入口统一接入 preflight：

- `/left_arm_controller/follow_joint_trajectory`
- `/right_arm_controller/follow_joint_trajectory`
- `/left_arm_controller/joint_command`
- `/right_arm_controller/joint_command`
- `/dual_arms/joint_command`

运行时 preflight 统一检查：

- `allow_motion`
- arm online
- arm enabled
- 当前状态可读
- 当前状态未过旧
- 当前姿态未越限
- 当前姿态未接近限位
- 当前状态到目标首点偏差未超阈值
- joint set 与命名合同匹配
- goal / joint command 结构合法

启动期校验独立于运行时 preflight gate，始终执行：

- `hardware_config` 文件存在
- `preflight_config_path` 文件存在
- 左右臂 channel 参数存在
- MoveIt joint limits 文件存在
- bridge 配置与 MoveIt 配置中的关节软限位完全一致

`preflight_enabled` 的准确语义：

- `true`：启用运行时 preflight gate
- `false`：仅跳过运行时 gate
- 无论取值如何，启动期校验都不会被关闭

## 当前已知现场问题

### 1. 右臂初始位姿可能超限

- 现场曾因右臂初始姿态超限导致双臂最小动作失败。
- 当前正式入口已把“当前姿态越限 / 接近限位”前置到 preflight。

### 2. USB-CAN 映射可能错位

- `can0` / `can1` 与物理左右臂可能因插拔顺序发生错位。
- 现场曾出现“左命令驱右臂 / 右命令驱左臂”。
- 当前仍使用 `can0/can1`，但启动时会明确打印：
  - `left_arm channel -> ...`
  - `right_arm channel -> ...`
- 中途插拔 USB-CAN 后，必须重新确认映射并重启 `real_hardware.launch.py`。

## 推荐启动方式

### Read-only

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=false enable_on_start:=false
```

### 动作测试

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=true enable_on_start:=true
```

### 显式关闭运行时 preflight gate

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py \
  allow_motion:=true \
  enable_on_start:=true \
  preflight_enabled:=false
```

注意：这不会关闭启动期配置/路径/限位一致性校验。

## 合法命令示例

### 左臂单点 action

```bash
ros2 run dual_nero_bridge send_left_arm_goal.py
```

### 右臂单点 action

```bash
ros2 run dual_nero_bridge send_right_arm_goal.py
```

## 会被 preflight 拒绝的示例

### `allow_motion=false`

在 read-only 模式下发送 action 或 topic 命令，预期会被拒绝，错误码为：

```text
ALLOW_MOTION_DISABLED
```

### 错误的 joint set

若向左臂 controller 发送非 `left_joint1..7` 的 joint_names，预期会被拒绝，错误码为：

```text
INVALID_JOINT_SET
```

## 预期日志示例

启动日志：

```text
[bringup] left_arm channel -> can0
[bringup] right_arm channel -> can1
[bringup] preflight_enabled -> true
[bringup] preflight_config_path -> .../preflight.yaml
[bringup] safety_mode -> strict
```

执行前日志：

```text
[STATE][left_arm_controller] received trajectory goal; source=trajectory, joint_names=[...], point_count=1
[STATE][left_arm_controller] preflight result -> ok=False, code=ALLOW_MOTION_DISABLED, message=left_arm_controller rejected because allow_motion=false.
```

## 冻结命名合同

- joints：`left_joint1..7`、`right_joint1..7`
- groups：`left_arm`、`right_arm`、`dual_arms`
- controllers：`left_arm_controller`、`right_arm_controller`、`joint_state_broadcaster`

## 当前限制

- 当前 bridge 不是 native `ros2_control` hardware plugin
- 当前 `FollowJointTrajectory` 只支持单点 goal
- 当前 USB-CAN 映射仍依赖现场确认

## 文档索引

- [docs/p2_preflight_design.md](docs/p2_preflight_design.md)
- [docs/p1_smoke_test_report.md](docs/p1_smoke_test_report.md)
- [docs/project_status.md](docs/project_status.md)
- [docs/known_issues.md](docs/known_issues.md)
