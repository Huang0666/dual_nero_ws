# 文档映射

## 目标

告诉 agent：改了哪类内容，必须同步更新哪些文档。

## 映射规则

### 1. 改阶段行为或阶段结论

必须更新：

- 对应 `human/phases/` 阶段文档
- [../human/overview/project_status.md](../human/overview/project_status.md)
- 如影响下一步，还要更新 [../human/overview/next_actions.md](../human/overview/next_actions.md)
- 如影响整体路线，还要更新 [../human/overview/roadmap.md](../human/overview/roadmap.md)
- [current_context.md](current_context.md)

### 2. 改启动、执行、恢复命令

必须更新：

- [../human/operations/migration_runbook.md](../human/operations/migration_runbook.md)
- 如属于仿真主线，还要更新 [../human/operations/simulation_runbook.md](../human/operations/simulation_runbook.md)
- [handoff.md](handoff.md)

### 3. 改项目摘要、交付边界、正式入口

必须更新：

- [../human/overview/project_status.md](../human/overview/project_status.md)
- [../human/overview/next_actions.md](../human/overview/next_actions.md)
- 如影响当前阶段结论，还要更新 [../human/phases/p4/README.md](../human/phases/p4/README.md)
- [current_context.md](current_context.md)

### 4. 改文档结构本身

必须更新：

- [../README.md](../README.md)
- 受影响目录的 `README.md`
- 本文档
- [rules.md](rules.md)
- 如涉及摆放规则，还要运行 `python tools/check_docs_layout.py`

### 5. 新增现场问题或故障处置经验

必须先更新：

- 来源阶段文档

如问题会长期重复出现，再更新：

- [../human/operations/issue_index.md](../human/operations/issue_index.md)

## 当前关键正文入口

- 状态：[../human/overview/project_status.md](../human/overview/project_status.md)
- 任务：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- 仿真：[../human/operations/simulation_runbook.md](../human/operations/simulation_runbook.md)
- P4：[../human/phases/p4/README.md](../human/phases/p4/README.md)
- P5：[../human/phases/p5/README.md](../human/phases/p5/README.md)
- P6：[../human/phases/p6/README.md](../human/phases/p6/README.md)
- P7：[../human/phases/p7/README.md](../human/phases/p7/README.md)
- P8：[../human/phases/p8/README.md](../human/phases/p8/README.md)
