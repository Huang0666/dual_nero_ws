# P2 Preflight 设计（已实现并验收）

## 目标

在当前 bridge 架构下，将正式执行入口统一到一套 preflight gate，确保启动可校验、执行可拒绝、故障可读。

## 设计原则

- action/topic 共享同一 preflight 源
- launch 层负责启动期检查与可见性
- 执行层负责运行时 gate/reject/abort
- 错误码和消息结构化、可读、可对齐

## 已实现范围

- 启动日志输出：
  - 左右臂 channel 映射
  - `preflight_enabled`
  - `preflight_config_path`
  - `safety_mode`
- 启动期检查：
  - 配置/路径存在
  - 映射参数存在
  - bridge 与 MoveIt 限位一致性
- 运行时 preflight 检查：
  - `allow_motion`
  - arm online/enabled
  - 状态可读/新鲜度
  - 当前姿态越限/近限位
  - 起点偏差阈值
  - joint set 与结构合法性

## 统一错误码

在 `dual_nero_bridge/preflight_codes.py` 中集中定义，action/topic 统一复用。

核心错误码：

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

## 验收状态

- 已实现并完成现场验收
- 详见 [acceptance_report.md](acceptance_report.md)

## 下一阶段

P3 当前拆分：

- P3-A：故障恢复 SOP 标准化
- P3-B：MoveIt 执行链系统化验证
- P3-C：USB-CAN 固定命名（暂缓）

说明：

- P3-C 已保留为待办，不在当前周期落地
- 当前优先推进 P3-A，再进入 P3-B
