# dual_nero_ws

`dual_nero_ws` 是面向 NERO 双臂机器人的 ROS 2 工作区。

当前仓库固定为三层结构：

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

- P1 已完成并通过当前实机验证。
- 当前真实执行方案是 **bridge 方案**，不是 native C++ `ros2_control` hardware plugin。
- `pyAgxArm` 已确认可用于 Nero 实机。
- 当前推荐路线是继续沿 bridge 做稳定化和工程化，不建议立即切到 native plugin。

## P1 已完成项

- 左臂单臂 read-only 成功
- 右臂单臂 read-only 成功
- 双臂只读成功
- `/joint_states` 14 joints 正常
- 双臂最小动作成功
- 左臂单点 action 成功
- 右臂单点 action 成功
- 双臂动作一致

## 当前实机稳定配置

当前 `create_agx_arm_config(...)` 的稳定做法是最小参数集：

- `robot="nero"`
- `comm="can"`
- `channel`
- `interface`
- `bitrate`

当前实机验证下，不传：

- `enable_check_can`
- `auto_connect`
- `timeout`

运行时已确认的行为：

- `connect()` 后必须调用 `set_normal_mode()`
- `enable()` 需要轮询重试，不能按一次返回值判失败
- `enable_all()` 以 7 个关节全部 enabled 为成功标准

## 已确认现场问题

### 1. 右臂初始位姿超限

- 首次双臂最小动作失败的根因是右臂初始位姿超出当前限位。
- 当前处理方式是：
  - 先失能
  - 手动调回合法区间
  - 再重新执行测试

### 2. USB-CAN 映射错位

- `can0` / `can1` 与物理左右臂可能因 USB-CAN 枚举和插拔顺序发生错位。
- 现场曾出现“左命令驱右臂 / 右命令驱左臂”。
- 当前仍使用 `can0/can1` 临时方案。
- 后续建议是为左右臂准备固定命名，例如 `udev`。
- 如果中途拔插 USB-CAN，建议重新确认映射，并重启 `real_hardware.launch.py` 后再继续测试。

## 测试脚本当前行为

- `test_left_arm.py`、`test_right_arm.py`、`test_dual_arm.py` 默认都会安全收尾：
  - `stop`
  - `disable_all`
  - `close`
- 如果要连续执行 `test + action`，建议显式传 `--keep-enabled`
- `--keep-enabled` 模式下：
  - 仍执行 `stop`
  - 不自动 `disable_all`
  - 不主动切回失能

## 冻结命名合同

- joints：`left_joint1..7`、`right_joint1..7`
- groups：`left_arm`、`right_arm`、`dual_arms`
- controllers：`left_arm_controller`、`right_arm_controller`、`joint_state_broadcaster`
- TF trunk：`world -> dual_base_plate -> dual_column -> dual_crossbar -> {left/right}_base_link -> ...`

## 推荐验证顺序

1. 左臂 read-only
2. 右臂 read-only
3. 双臂 read-only
4. `/joint_states` 检查
5. 双臂最小动作
6. 左臂单点 action
7. 右臂单点 action

详细命令见 [docs/p1_smoke_test_report.md](docs/p1_smoke_test_report.md)。

## 当前阶段与下一步

- 当前阶段：`P1 Final Cleanup` 已完成，项目准备进入 `P2 稳定化与工程化`
- 当前最高优先级：
  - USB-CAN 固定命名
  - 正式入口的姿态/限位检查前置
  - bridge/action 日志和恢复策略增强

## 文档索引

- [docs/project_status.md](docs/project_status.md)
- [docs/known_issues.md](docs/known_issues.md)
- [docs/next_actions.md](docs/next_actions.md)
- [docs/migration_runbook.md](docs/migration_runbook.md)
- [docs/session_resume.md](docs/session_resume.md)
- [docs/project_baseline.md](docs/project_baseline.md)
- [docs/p1_driver_contract.md](docs/p1_driver_contract.md)
- [docs/p1_execution_report.md](docs/p1_execution_report.md)
- [docs/p1_smoke_test_report.md](docs/p1_smoke_test_report.md)
