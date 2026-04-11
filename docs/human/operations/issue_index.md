# 运维问题索引

## 作用

本文档不是问题正文仓库，而是跨阶段运维问题索引。

规则：

- 新问题先写入所属阶段文档
- 只有会跨阶段重复出现、需要长期运维关注的问题，才进入本索引
- 每条问题必须给出来源阶段和当前处理入口

## 当前问题

| 问题 | 简述 | 来源阶段 | 当前处理入口 |
|---|---|---|---|
| `enable()` 首次可能失败 | 真机下第一次 `enable()` 可能返回 `False`，需要轮询重试 | [P1 执行报告](../phases/p1/execution_report.md) / [P1 冒烟报告](../phases/p1/smoke_test_report.md) | [P3-A 恢复 SOP](../phases/p3/recovery_sop.md) |
| `set_normal_mode()` 必须调用 | `connect()` 后必须显式进入 normal mode | [P1 执行报告](../phases/p1/execution_report.md) / [P1 冒烟报告](../phases/p1/smoke_test_report.md) | [迁移与启动手册](migration_runbook.md) |
| USB-CAN 映射漂移 | `can0/can1` 与物理左右臂可能错位 | [P1 执行报告](../phases/p1/execution_report.md) / [P1 冒烟报告](../phases/p1/smoke_test_report.md) | [P3-A 恢复 SOP](../phases/p3/recovery_sop.md) |
| `can1 BUS-OFF/STOPPED` | 右臂不可用，`/joint_states --once` 可能阻塞 | [P2 验收报告](../phases/p2/acceptance_report.md) | [P3-A 恢复 SOP](../phases/p3/recovery_sop.md) |
| `gs_usb` 不支持 `restart-ms` | 带 `restart-ms` 的恢复命令会报错 | [P2 验收报告](../phases/p2/acceptance_report.md) | [P3-A 恢复 SOP](../phases/p3/recovery_sop.md) |
| 测试脚本默认自动失能 | 连续 `test + action` 场景容易误以为硬件异常 | [P1 执行报告](../phases/p1/execution_report.md) / [P1 冒烟报告](../phases/p1/smoke_test_report.md) | [迁移与启动手册](migration_runbook.md) |
| bridge 仅支持单点 trajectory | 当前不是 native plugin，`FollowJointTrajectory` 仅支持单点目标 | [P1 驱动合同](../phases/p1/driver_contract.md) / [P2 设计说明](../phases/p2/preflight_design.md) | [P2 设计说明](../phases/p2/preflight_design.md) |
