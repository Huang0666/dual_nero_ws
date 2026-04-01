# P1 Execution Report

## 方案选择

- 最终采用：**B 方案，真实执行 bridge**
- 原因：
  - 当前仓库可确认可复用的是 Python SDK `pyAgxArm`
  - 当前仓库已有 Python backend 包 `dual_nero_driver`
  - 在缺少可确认可用的 NERO C++ SDK 的情况下，直接实现 C++ `ros2_control` `SystemInterface` 会落到不可维护的“C++ 嵌 Python SDK”方案

## P1.1 收口更新

- 修复 `FollowJointTrajectory` 语义：
  - 当前明确采用 **方案 A**
  - 每个 goal 只支持一个 trajectory point
  - 多点 goal 会在接收阶段被显式拒绝，不再允许静默降级
- 明确 bridge 失败语义：
  - 两臂都不可用：启动失败退出
  - 单臂不可用：进入 degraded mode
  - `dual_arms` 命令要求两臂都可用且都 enabled
  - `allow_motion=false` / `enable_on_start=false` 的拒绝语义已收口
- 新增最小 action 客户端示例：
  - [../src/dual_nero_bridge/scripts/send_left_arm_goal.py](../src/dual_nero_bridge/scripts/send_left_arm_goal.py)
  - [../src/dual_nero_bridge/scripts/send_right_arm_goal.py](../src/dual_nero_bridge/scripts/send_right_arm_goal.py)
- 新增冒烟验证模板：
  - [p1_smoke_test_report.md](p1_smoke_test_report.md)

## 新增 / 修改文件树

```text
dual_nero_ws/
|-- .gitignore
|-- README.md
|-- docs/
|   |-- project_baseline.md
|   |-- p1_driver_contract.md
|   |-- p1_execution_report.md
|   `-- p1_smoke_test_report.md
`-- src/
    |-- dual_nero_driver/
    |   |-- README.md
    |   |-- dual_nero_driver/
    |   |   |-- __init__.py
    |   |   `-- factories.py
    |   `-- scripts/
    |       |-- test_left_arm.py
    |       |-- test_right_arm.py
    |       `-- test_dual_arm.py
    |-- dual_nero_bridge/
    |   |-- package.xml
    |   |-- setup.py
    |   |-- setup.cfg
    |   |-- README.md
    |   |-- config/hardware_params.yaml
    |   |-- launch/real_hardware_bridge.launch.py
    |   |-- scripts/
    |   |   |-- send_left_arm_goal.py
    |   |   `-- send_right_arm_goal.py
    |   `-- dual_nero_bridge/
    |       |-- __init__.py
    |       |-- errors.py
    |       |-- logging_utils.py
    |       |-- goal_client_utils.py
    |       |-- runtime.py
    |       |-- joint_state_bridge.py
    |       |-- joint_command_bridge.py
    |       |-- follow_joint_trajectory_server.py
    |       |-- real_execution_node.py
    |       `-- contract_check.py
    `-- dual_nero_bringup/
        |-- package.xml
        |-- setup.py
        |-- setup.cfg
        |-- README.md
        |-- config/real_execution.yaml
        |-- launch/real_hardware.launch.py
        `-- dual_nero_bringup/__init__.py
```

## 哪些已进入真机执行链

- 真实双臂 backend 复用链：`dual_nero_driver`
- 真实 `/joint_states` 发布链：`dual_nero_bridge`
- 左右臂 `FollowJointTrajectory` 真实执行入口：`dual_nero_bridge`
- 双臂直接命令入口：`/dual_arms/joint_command`
- operator-facing 真机入口：`dual_nero_bringup/real_hardware.launch.py`

## 当前限制

- bridge 仍不是 native `ros2_control` hardware plugin
- 当前 `FollowJointTrajectory` 仅支持单点 goal
- 不实现多点时间控制
- 不实现 lazy enable
- 不实现完整的 diagnostics / calibration / recovery

## 建议的下一步

1. 在真实硬件上执行 [p1_smoke_test_report.md](p1_smoke_test_report.md) 中的命令和记录模板
2. 评估是否需要进入 native `ros2_control` hardware plugin 路线
3. 如果继续保留 bridge，优先补故障恢复、enable 检测和更细化的同步控制
