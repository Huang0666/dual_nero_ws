# P1 Execution Report

## 方案选择

- 最终采用：**B 方案，真实执行 bridge**
- 原因：
  - 当前仓库可确认可复用的是 Python SDK `pyAgxArm`
  - 当前仓库已存在 Python backend 包 `dual_nero_driver`
  - 在缺少可确认可用的 NERO C++ SDK 的情况下，直接实现 C++ `ros2_control` `SystemInterface` 会落到不可维护的“C++ 嵌 Python SDK”方案

## 当前仓库分层

- `display`
  - `src/dual_nero_description/launch/display_dual_urdf.launch.py`
- `planning_demo`
  - `src/dual_nero_moveit_config/launch/demo.launch.py`
- `real_hardware_execution`
  - `src/dual_nero_bringup/launch/real_hardware.launch.py`

## P1.1 收口结果

- `FollowJointTrajectory` 当前明确采用单点 goal 语义
- 多点 goal 会在接收阶段被显式拒绝
- bridge 的 degraded / reject / abort 语义已收口
- 新增最小 action 客户端示例：
  - `src/dual_nero_bridge/scripts/send_left_arm_goal.py`
  - `src/dual_nero_bridge/scripts/send_right_arm_goal.py`
- 新增冒烟验证模板：
  - `docs/p1_smoke_test_report.md`

## P1.2 实机收口结果

- 左臂 read-only 已成功
- `pyAgxArm` 当前按实机稳定最小参数集接入：
  - `robot="nero"`
  - `comm="can"`
  - `channel`
  - `interface`
  - `bitrate`
- `connect()` 后显式调用 `set_normal_mode()`
- `enable_all()` 改为循环轮询 `enable()` + `get_joints_enable_status_list()`，直到 7 个关节全部 enabled 才算成功

## P1.3 收口结果

- 双臂最小动作测试已成功
- 首次执行失败的原因已确认：
  - 右臂初始位姿超出当前配置限位
- 处理方式：
  - 机械臂失能
  - 手动调整到合法位置
  - 再次执行双臂最小动作测试
- 复测结果：
  - 双臂最小动作成功
  - 机械臂发生微弱移动

### 本轮新增修复

- `src/dual_nero_moveit_config/config/joint_limits.yaml`
  - 显式补齐 14 个 joint 的 `has_position_limits` / `min_position` / `max_position`
  - 当前 position limits 与 URDF、bridge 配置保持一致
- `src/dual_nero_driver/scripts/test_dual_arm.py`
  - 在 `--execute` 前打印当前左右臂 joint positions
  - 执行前检查当前姿态是否超限
  - 执行前检查哪些 joint 接近限位
  - 如果当前姿态超限，报错信息会明确包含：
    - joint 名称
    - 当前值
    - 下限
    - 上限
    - “先失能并手动调整到合法区间，再重新执行测试”的操作提示
- `src/dual_nero_driver/dual_nero_driver/safety.py`
  - 新增当前姿态越界检查
  - 新增接近限位告警检查

## 哪些已进入真机执行链

- 真实双臂 backend 复用链：`dual_nero_driver`
- 真实 `/joint_states` 发布链：`dual_nero_bridge`
- 左右臂 `FollowJointTrajectory` 真实执行入口：`dual_nero_bridge`
- 双臂直接命令入口：`/dual_arms/joint_command`
- operator-facing 真机入口：`dual_nero_bringup/real_hardware.launch.py`
- 真机最小动作测试链：`src/dual_nero_driver/scripts/test_dual_arm.py --execute`

## 当前 limits 收口口径

- URDF/xacro 是机械结构 limits 的原始定义
- `src/dual_nero_bridge/config/hardware_params.yaml`
  - 是当前 driver/runtime safety 实际读取的 limits 来源
- `src/dual_nero_moveit_config/config/joint_limits.yaml`
  - 已补齐为和 URDF/bridge 一致的显式 position limits
- 当前运行时 safety 不直接读取 URDF 或 MoveIt YAML，仍以 `hardware_params.yaml` 为准

## 当前限制

- bridge 仍不是 native `ros2_control` hardware plugin
- 当前 `FollowJointTrajectory` 仅支持单点 goal
- 不实现多点时间控制
- 不实现 lazy enable
- 不实现完整 diagnostics / calibration / recovery
- 当前双臂最小动作测试依赖人工确认机械臂起始姿态处于合法区间

## 建议的下一步

1. 完成右臂 read-only 与双臂 read-only 的现场记录补齐
2. 在现场再跑一轮 `test_dual_arm.py --execute`，验证新的执行前限位预检查文案是否足够清晰
3. 评估是否要把 `hardware_params.yaml` 继续作为唯一运行时 limits 源，并增加自动从 URDF 导出/比对的校验工具
4. 如果后续继续保留 bridge，优先补故障恢复、enable 检测和更细化的同步控制
