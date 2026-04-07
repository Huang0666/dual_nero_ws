# dual_nero_bridge

`dual_nero_bridge` 是当前 `dual_nero_ws` 的真实执行桥。

## 当前职责

- 复用 `dual_nero_driver` 作为唯一 `pyAgxArm` 后端
- 发布 14 关节固定顺序的真实 `/joint_states`
- 提供 topic 入口：
  - `/left_arm_controller/joint_command`
  - `/right_arm_controller/joint_command`
  - `/dual_arms/joint_command`
- 提供 action 入口：
  - `/left_arm_controller/follow_joint_trajectory`
  - `/right_arm_controller/follow_joint_trajectory`

## 统一 preflight

`preflight.py` 是 bridge 的唯一运行时 preflight gate。

它负责：

- 统一检查规则
- 统一结果结构
- 统一错误码
- 统一错误文案

它不负责：

- 生成 USB-CAN 映射
- 替代底层 driver 的运动保护
- 重构当前 bridge 为多点轨迹执行器

## 当前正式执行入口

以下入口都必须在真正下发硬件命令前调用同一套 preflight：

- `/left_arm_controller/follow_joint_trajectory`
- `/right_arm_controller/follow_joint_trajectory`
- `/left_arm_controller/joint_command`
- `/right_arm_controller/joint_command`
- `/dual_arms/joint_command`

## 当前 preflight 检查项

- `allow_motion`
- arm online
- arm enabled
- 当前状态是否可读
- 当前状态是否过旧
- 当前姿态是否越限
- 当前姿态是否接近限位
- 当前状态到目标首点偏差是否过大
- joint set 是否匹配冻结命名合同
- goal / joint command 结构是否合法

## 集中错误码

所有 preflight 错误码集中定义在：

```text
dual_nero_bridge/preflight_codes.py
```

当前统一使用：

- `ALLOW_MOTION_DISABLED`
- `ARM_OFFLINE`
- `ARM_NOT_ENABLED`
- `CURRENT_POSE_OUT_OF_LIMIT`
- `CURRENT_POSE_NEAR_LIMIT`
- `INVALID_GOAL_STRUCTURE`
- `INVALID_JOINT_SET`
- `STATE_UNAVAILABLE`
- `STATE_TOO_OLD`
- `START_DEVIATION_TOO_LARGE`

action 和 topic 路径必须复用同一组错误码，不能各自定义不同字符串。

## preflight 配置

配置文件：

```text
config/preflight.yaml
```

运行时参数：

- `preflight_enabled`
- `preflight_config_path`
- `safety_mode`

当前配置项包括：

- `enabled`
- `safety_mode`
- `near_limit_margin`
- `max_start_deviation`
- `max_state_age_sec`
- `require_online`
- `require_enabled`
- `require_dual_online`
- `require_dual_enabled`
- `moveit_joint_limits_path`
- `scopes`

## `preflight_enabled` 语义

- `true`：启用运行时 preflight gate
- `false`：仅跳过运行时 gate

注意：

- 它不会关闭 bringup 启动期校验
- 配置路径、映射存在性、MoveIt-vs-bridge 限位一致性校验仍然必须通过

## 限位来源与一致性策略

- runtime 和 preflight 运行时检查，继续使用 bridge 当前生效的关节限位
- 不再复制出第三份 preflight 限位真值
- MoveIt `joint_limits.yaml` 作为启动期强一致校验来源
- 如果 bridge `hardware_params.yaml` 与 MoveIt `joint_limits.yaml` 中任一关节限位不一致，启动立即失败

## 当前 `FollowJointTrajectory` 语义

- 当前 bridge 只支持单点 goal
- 多点 goal 会被 `INVALID_GOAL_STRUCTURE` 拒绝
- `time_from_start` 仅做结构合法性检查，不做多点时间控制

## 当前 USB-CAN 策略

- 本轮不实现固定命名
- 当前仍使用 `can0/can1`
- preflight 不硬编码 `can0/can1` 逻辑
- operator 必须通过启动日志确认：
  - `left_arm channel -> ...`
  - `right_arm channel -> ...`
