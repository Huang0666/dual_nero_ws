# OPENSPEC Feature Summary

## 作用

本文件用于记录“当前阶段的正式入口与核心能力摘要”。本仓库当前未启用 OpenSpec 流程，此文件作为统一摘要入口保留。

## 当前正式能力摘要

- P2：preflight 作为正式 gate 已接入 action/topic 入口
- P3：故障恢复 SOP 与 MoveIt 主路径验证已完成
- P4：双臂固定场景任务入口已落地
  - CLI：`ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync`
  - 配置：`src/dual_nero_bridge/config/p4_tasks.yaml`

## 下一步更新规则

- 阶段入口变化时：同步更新本文件与 `docs/human/overview/project_status.md`
- 新增正式执行入口时：同步更新 `docs/human/operations/migration_runbook.md`
