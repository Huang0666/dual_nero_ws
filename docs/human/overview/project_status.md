# 项目状态

## 当前结论

- P1 已完成。
- P2 已完成并通过现场验收（bridge 路线）。
- P3 主体已完成：
  - P3-A：故障恢复 SOP 已落地。
  - P3-B：MoveIt 主路径已完成现场验证。
  - P3-C：USB-CAN 固定命名保持暂缓，作为后续待办。
- 当前架构仍为 bridge，未切到 native `ros2_control`。
- 项目当前进入 `P4 目标定义` 阶段。

参考：

- [../phases/p2/acceptance_report.md](../phases/p2/acceptance_report.md)
- [../phases/p3/moveit_validation_report.md](../phases/p3/moveit_validation_report.md)

## 长期目标

- 双臂能够实现协调运动。
- 双臂能够在规划中考虑避障。
- 后续接入视觉。
- 最终完成简单抓取任务。

## 当前阶段

- 已完成：`P1 最小真实执行链`
- 已完成：`P2 preflight 稳定化与工程化`
- 已完成：`P3 恢复 SOP + MoveIt 主路径验证`
- 进行中：`P4 目标定义与路线拆分`

## 当前正式可交付路径

- 启动 `real_hardware.launch.py`
- 通过 MoveIt 完成单臂规划
- 取规划末点
- 以单点 `FollowJointTrajectory` 经 bridge 执行

说明：

- 当前原生 `ExecuteTrajectory` 不作为正式执行路径。
- 当前 bridge 正式合同仍然是“每个 goal 恰好 1 个 trajectory point”。

## 已完成能力

### P1

- 双臂只读
- `/joint_states`
- 双臂最小动作
- 左右臂单点 action

### P2

- 启动期映射/安全模式日志
- action/topic 正式入口统一 preflight gate
- 统一错误码与 reject/abort 语义
- dual_arms topic 路径验证通过

### P3-A

- 故障恢复 SOP 已形成正式文档
- 现场常见故障已有统一恢复步骤

### P3-B

- 左臂 MoveIt 规划通过
- 右臂 MoveIt 规划通过
- 左臂 `bridge-final-point` 执行通过
- 右臂 `bridge-final-point` 执行通过
- 只读模式负例通过，错误码为 `ALLOW_MOTION_DISABLED`
- `joint_limits.yaml` 已补保守的速度/加速度占位值，TOTG 默认警告已消失

## 当前未完成但已明确的边界

- `dual_arms` 的 MoveIt 验证还未作为正式阶段目标推进，后续可补。
- USB-CAN 固定命名尚未实施，当前仍依赖人工映射确认。
- MoveIt 速度/加速度限位当前是保守占位值，不是厂家真值。
- 原生 `ExecuteTrajectory` 与 bridge 单点合同当前不兼容。

## 当前最高优先级

1. 定义 P4 的任务目标、范围和验收标准
2. 将 P4 与最终“协调运动/避障/视觉/抓取”目标建立清晰映射
3. 保持 P3-C 作为待办入口，不在当前周期实施

## 当前风险

- `can0/can1` 重插或重启后仍存在人工确认成本。
- 速度/加速度限位尚未替换为厂家真值。
- 双臂协调、避障、视觉、抓取仍未进入正式实现阶段。
