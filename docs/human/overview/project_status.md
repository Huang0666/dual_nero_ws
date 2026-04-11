# 项目状态

## 当前结论

- P1 已完成。
- P2 已完成并通过现场验收（bridge 路线）。
- 当前架构仍为 bridge（未切 native `ros2_control`）。
- 项目进入 P3 阶段。

参考：

- [../phases/p2/acceptance_report.md](../phases/p2/acceptance_report.md)

## 当前阶段

- 已完成：`P1 最小真实执行链`
- 已完成：`P2 preflight 稳定化与工程化`
- 进行中：`P3 正式执行验证`

## P3 当前进展

- P3-A：恢复 SOP 已形成正式文档并可用于现场恢复
- P3-B：最小验证 CLI 已落地，待现场补正式执行结果
- P3-C：保持暂缓，不在当前周期实施

## P2 已完成内容

- 启动期检查与映射/安全日志可见
- action/topic 正式入口统一 preflight gate
- 错误码与失败语义统一且可读
- dual_arms topic 路径验证通过（`code=OK`）
- 负例验证通过（`ALLOW_MOTION_DISABLED` / `INVALID_JOINT_SET` / `START_DEVIATION_TOO_LARGE`）

## 当前最高优先级

1. P3-A：故障恢复 SOP 标准化
2. P3-B：MoveIt 执行链系统化验证
3. P3-C：USB-CAN 固定命名与映射稳定化（待办）

## P3-A 当前交付物

- 正式 SOP：
  - [../phases/p3/recovery_sop.md](../phases/p3/recovery_sop.md)
- P3-B 验证计划：
  - [../phases/p3/moveit_validation_plan.md](../phases/p3/moveit_validation_plan.md)
- P3-B 验证报告：
  - [../phases/p3/moveit_validation_report.md](../phases/p3/moveit_validation_report.md)
- 迁移/重启手册：
  - [../operations/migration_runbook.md](../operations/migration_runbook.md)
- 运维问题索引：
  - [../operations/issue_index.md](../operations/issue_index.md)

## 主要风险

- `can0/can1` 人工映射在重插/重启后仍存在操作风险。

## P3 退出标准

- 故障恢复 SOP 在现场可执行且可复现
- MoveIt 执行链验证完成并有复现证据
- P3-C 的固定命名任务明确列入待办并保留实施入口
