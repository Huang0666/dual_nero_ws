# P1 Execution Report

## 方案选择

- 最终采用：**B 方案，真实执行 bridge**
- 原因：
  - 当前仓库可确认可复用的是 Python SDK `pyAgxArm`
  - 当前仓库已有 Python backend 包 `dual_nero_driver`
  - 在缺少可确认可用的 NERO C++ SDK 的情况下，直接实现 C++ `ros2_control` `SystemInterface` 会落到不可维护的“C++ 嵌 Python SDK”方案

## 新增 / 修改文件树

```text
dual_nero_ws/
|-- .gitignore
|-- README.md
|-- docs/
|   |-- project_baseline.md
|   |-- p1_driver_contract.md
|   `-- p1_execution_report.md
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
    |   `-- dual_nero_bridge/
    |       |-- __init__.py
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

## 关键 diff 摘要

### 1. `dual_nero_driver`

- 新增 `factories.py`
  - `build_single_arm_from_file(config_path, side)`
  - `build_dual_arm_manager_from_file(config_path)`
- 最小测试脚本改为复用统一工厂接口，避免更高层包重复装配 backend

### 2. `dual_nero_bridge`

- `runtime.py`
  - 单进程共享 `DualArmManager`
  - 所有 `pyAgxArm` 访问经由统一运行时
- `joint_state_bridge.py`
  - 发布 14 joint 的真实 `/joint_states`
- `joint_command_bridge.py`
  - 提供左右臂和双臂的最小直接命令入口
- `follow_joint_trajectory_server.py`
  - 提供两个 `FollowJointTrajectory` action server
  - controller 名称与现有 MoveIt contract 对齐
- `contract_check.py`
  - 做 joint / group / controller / TF 口径静态检查

### 3. `dual_nero_bringup`

- 新增 `real_hardware.launch.py`
  - 明确区分真机执行入口与现有 demo
- 新增 `real_execution.yaml`
  - 保存 launch 默认参数，不把默认值全部硬编码进 launch

## 哪些已经进入真机执行链

已进入真机执行链的部分：

- 真实双臂 backend 复用链：`dual_nero_driver`
- 真实 `/joint_states` 发布链：`dual_nero_bridge`
- 左右臂 `FollowJointTrajectory` 真实执行入口：`dual_nero_bridge`
- 双臂直接命令入口：`/dual_arms/joint_command`
- operator-facing 真机入口：`dual_nero_bringup/real_hardware.launch.py`

## 哪些仍未完成

- native `ros2_control` C++ hardware plugin
- 真正的 `controller_manager` / `joint_state_broadcaster` 真机链
- 严格实时轨迹控制
- 更完整的 diagnostics / calibration / recovery
- 更强的同步误差补偿、急停闭环和通信恢复

## 风险与限制

- `FollowJointTrajectory` 当前是 point-to-point shim，不保证严格时间语义
- 速度、周期、延迟和同步误差仍取决于 `pyAgxArm` 与下位机行为
- velocity 回读是否可用仍依赖 `pyAgxArm` 当前环境
- 本轮默认 `allow_motion=false`，真实动作需要显式开启

## 建议的下一步

1. 在真实硬件上联调 `/joint_states`、左右臂 trajectory action、双臂直接命令入口
2. 固化 CAN 激活、enable、fault recovery 的操作规程
3. 评估是否具备进入 native `ros2_control` hardware plugin 的条件
