# 文档映射

## 目标

告诉 agent：改了哪类内容，必须同步更新哪些文档。

## 映射规则

### 1. 改阶段行为或阶段结论

必须更新：

- 对应 `human/phases/` 阶段文档
- [../human/overview/project_status.md](../human/overview/project_status.md)
- 如影响下一步，还要更新 [../human/overview/next_actions.md](../human/overview/next_actions.md)
- 如影响整体阶段路线，还要更新 [../human/overview/roadmap.md](../human/overview/roadmap.md)
- [current_context.md](current_context.md)

### 2. 改启动、执行、恢复命令

必须更新：

- [../human/operations/migration_runbook.md](../human/operations/migration_runbook.md)
- 如属于恢复流程，还要更新 [../human/phases/p3/recovery_sop.md](../human/phases/p3/recovery_sop.md)
- [handoff.md](handoff.md) 中的最小操作摘要

### 3. 新增现场问题或故障处置经验

必须先更新：

- 来源阶段文档

如该问题会长期重复出现，再更新：

- [../human/operations/issue_index.md](../human/operations/issue_index.md)

### 4. 改 preflight、错误码、启动校验

通常要更新：

- [../human/phases/p2/preflight_design.md](../human/phases/p2/preflight_design.md)
- [../human/phases/p2/acceptance_report.md](../human/phases/p2/acceptance_report.md)（若影响验收结论）
- [../human/overview/project_status.md](../human/overview/project_status.md)

### 5. 改 MoveIt 验证脚本、MoveIt 命令、P3-B 验证流程

必须更新：

- [../human/phases/p3/moveit_validation_plan.md](../human/phases/p3/moveit_validation_plan.md)
- [../human/phases/p3/moveit_validation_report.md](../human/phases/p3/moveit_validation_report.md)（若有真实结果）
- [../human/overview/project_status.md](../human/overview/project_status.md)
- [../human/overview/next_actions.md](../human/overview/next_actions.md)
- [current_context.md](current_context.md)

### 6. 改文档结构本身

必须更新：

- [../README.md](../README.md)
- 所有受影响目录的 `README.md`
- 本文档
- [rules.md](rules.md)（若规则有变化）

## 当前关键正文入口

- 状态：[../human/overview/project_status.md](../human/overview/project_status.md)
- 任务：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- 路线：[../human/overview/roadmap.md](../human/overview/roadmap.md)
- P4：[../human/phases/p4/README.md](../human/phases/p4/README.md)
- P2：[../human/phases/p2/acceptance_report.md](../human/phases/p2/acceptance_report.md)
- P3-A：[../human/phases/p3/recovery_sop.md](../human/phases/p3/recovery_sop.md)
- P3-B：[../human/phases/p3/moveit_validation_plan.md](../human/phases/p3/moveit_validation_plan.md)
