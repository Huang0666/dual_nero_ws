# P3-B MoveIt 执行链验证报告

## 当前状态

- 已具备最小验证 CLI
- 本轮已完成主路径现场验证
- 当前主验证路径为 `--bridge-final-point-execute`

## 验证环境

- 日期：2026-04-12
- 操作人：现场终端 `hrs`
- 工作区：`~/dual_nero_ws_project/dual_nero_ws`
- ROS 发行版：Humble
- 启动模式：
  - 动作模式：`allow_motion:=true enable_on_start:=true`
  - 只读负例：`allow_motion:=false enable_on_start:=false`
  - `with_moveit:=true`
  - `with_rviz:=false`

## 现场硬规则

1. `real_hardware.launch.py` 必须持续运行
2. 所有 `ros2 run dual_nero_bridge ...` 验证命令都要在另一个终端执行
3. 先确认 `/joint_states --once` 能返回，再做 P3-B 验证

## 执行命令

### 左臂规划

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm
```

结果：

- 是否通过：通过
- 关键输出：
  - `error_name=SUCCESS`
  - `trajectory_point_count=5`

### 右臂规划

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group right_arm
```

结果：

- 是否通过：通过
- 关键输出：
  - `error_name=SUCCESS`
  - `trajectory_point_count=5`

### 左臂执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm --execute
```

结果：

- 是否通过：不通过
- 关键输出：
  - MoveIt 规划成功：`error_name=SUCCESS`
  - 执行结果：`error_name=CONTROL_FAILED`
  - 原因结论：MoveIt 默认输出多点轨迹，当前 bridge 合同只接受单点 trajectory

### 右臂执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group right_arm --execute
```

结果：

- 是否通过：本轮未单独重复执行
- 关键输出：
  - 左臂原生执行已足以证明当前 `ExecuteTrajectory` 与 bridge 单点合同不兼容
  - 当前主验证路径已切到 `--bridge-final-point-execute`

### 左臂 bridge 末点执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm --bridge-final-point-execute
```

结果：

- 是否通过：通过
- 关键输出：
  - 规划结果：`error_name=SUCCESS`
  - bridge 执行结果：`error_name=SUCCESSFUL`
  - `error_string=left_arm_controller executed a single-point goal. This bridge currently supports exactly one trajectory point per goal.`

### 右臂 bridge 末点执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group right_arm --bridge-final-point-execute
```

结果：

- 是否通过：通过
- 关键输出：
  - 现场已验证通过
  - 详细 stdout 未单独归档，本轮结论以现场通过为准

### 只读负例

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm --bridge-final-point-execute
```

结果：

- 是否出现 `ALLOW_MOTION_DISABLED`：是
- MoveIt 执行是否按预期失败：是
- 关键输出：
  - MoveIt 规划成功：`error_name=SUCCESS`
  - bridge 拒绝日志：

```text
[STATE][left_arm_controller] received trajectory goal; source=trajectory, joint_names=['left_joint1', 'left_joint2', 'left_joint3', 'left_joint4', 'left_joint5', 'left_joint6', 'left_joint7'], point_count=1
[STATE][left_arm_controller] preflight result -> ok=False, code=ALLOW_MOTION_DISABLED, message=left_arm_controller rejected because allow_motion=false.
[REJECT][left_arm_controller] ALLOW_MOTION_DISABLED: left_arm_controller rejected because allow_motion=false.
```

### 双臂规划（可选）

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group dual_arms
```

结果：

- 是否通过：本轮未执行
- 关键输出：
  - 保留为可选增强项，不影响本轮主路径结论

## bridge 日志样例

### 成功样例

```text
[STATE][left_arm_controller] received trajectory goal; source=trajectory, joint_names=['left_joint1', ...], point_count=1
[STATE][left_arm_controller] preflight result -> ok=True, code=OK, message=preflight checks passed
```

### 失败样例

```text
[REJECT][left_arm_controller] ALLOW_MOTION_DISABLED: ...
```

## 额外观察

- MoveIt 日志出现：

```text
Joint velocity limits are not defined. Using the default 1 rad/s.
Joint acceleration limits are not defined. Using the default 1 rad/s^2.
```

- 当前 `joint_limits.yaml` 仍缺少速度/加速度限位定义
- 这不会阻断本轮主路径验证，但会影响时间参数化的可信度

## 配置修正记录

- 已在 `src/dual_nero_moveit_config/config/joint_limits.yaml` 中补入保守的速度/加速度限位占位值：
  - `has_velocity_limits: true`
  - `max_velocity: 1.0`
  - `has_acceleration_limits: true`
  - `max_acceleration: 1.0`
- 该值当前用于消除 TOTG 默认值警告，并不代表厂家真值
- 后续若拿到正式动力学参数，应统一替换本占位配置

## 结论

- MoveIt 规划是否稳定：稳定，左右臂规划均成功
- MoveIt 原生 `ExecuteTrajectory` 是否与 bridge 兼容：当前不兼容，默认多点轨迹会触发 `CONTROL_FAILED`
- bridge 末点执行是否稳定：稳定，左右臂均已通过现场验证
- bridge / preflight 语义是否清晰：清晰，只读模式下能稳定返回 `ALLOW_MOTION_DISABLED`
- 是否达到 P3-B 退出标准：已达到本轮主路径退出标准

## 当前阶段结论

本轮已经确认当前 bridge 路线下可交付的 MoveIt 执行方式是：

1. MoveIt 规划
2. 提取规划结果的末点
3. 以单点 `FollowJointTrajectory` 通过 bridge 执行

原生 `ExecuteTrajectory` 当前不作为正式执行路径。

## 下一步建议

- 将本报告结论同步回项目状态与下一步任务
- 后续若继续抬高质量，可补：
  - `dual_arms` 规划验证
  - 用厂家真值替换当前 MoveIt 速度/加速度占位限值
