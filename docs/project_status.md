# 项目状态

## 当前结论

- P1 已完成。
- P2 已完成并通过现场验收（bridge 路线）。
- 当前架构仍为 bridge（未切 native `ros2_control`）。
- 项目进入 P3 阶段。

参考：

- [p2_acceptance_report.md](p2_acceptance_report.md)

## 当前阶段

- 已完成：`P1 Final Cleanup`
- 已完成：`P2 Stabilization and Engineering`
- 进行中：`P3 Formal Execution Validation`

## P2 已完成内容

- 启动期检查与映射/安全日志可见
- action/topic 正式入口统一 preflight gate
- 错误码与失败语义统一且可读
- dual_arms topic 路径验证通过（`code=OK`）
- 负例验证通过（`ALLOW_MOTION_DISABLED` / `INVALID_JOINT_SET` / `START_DEVIATION_TOO_LARGE`）

## 当前最高优先级

1. P3-A：故障恢复 SOP 标准化
2. P3-B：MoveIt -> action 真机执行验证
3. P3-C：USB-CAN 固定命名与映射稳定化（待办）

## 主要风险

- `can0/can1` 人工映射在重插/重启后仍存在操作风险。

## P3 退出标准

- 故障恢复 SOP 在现场可执行且可复现
- MoveIt 执行链验证完成并有复现证据
- P3-C 的固定命名任务明确列入待办并保留实施入口
