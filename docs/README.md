# 文档总入口

## 目的

`docs/` 采用双视图结构：

- `human/`：给人看，强调背景、流程、结论、操作
- `agent/`：给 agent 看，强调结构、规则、映射、当前状态

两边描述方式可以不同，但项目事实只保留一套，不允许写成两套互相独立的正文。

## 先看哪里

### 如果你是人

先看：

- [human/README.md](human/README.md)

常用入口：

- 当前状态：[human/overview/project_status.md](human/overview/project_status.md)
- 下一步任务：[human/overview/next_actions.md](human/overview/next_actions.md)
- 总体路线：[human/overview/roadmap.md](human/overview/roadmap.md)
- P4 阶段定义：[human/phases/p4/README.md](human/phases/p4/README.md)
- P3-A 故障恢复 SOP：[human/phases/p3/recovery_sop.md](human/phases/p3/recovery_sop.md)
- P3-B 验证计划：[human/phases/p3/moveit_validation_plan.md](human/phases/p3/moveit_validation_plan.md)
- 迁移与标准启动：[human/operations/migration_runbook.md](human/operations/migration_runbook.md)

### 如果你是 agent

先看：

- [agent/README.md](agent/README.md)

常用入口：

- 当前上下文：[agent/current_context.md](agent/current_context.md)
- 文档更新规则：[agent/rules.md](agent/rules.md)
- 文档映射：[agent/doc_map.md](agent/doc_map.md)
- 仓库结构：[agent/repo_map.md](agent/repo_map.md)

## 硬规则

1. 项目级文档默认只放在 `docs/` 下
2. 根目录默认只保留 [README.md](../README.md) 作为总入口
3. 新增事实类内容，优先更新 `human/` 正文文档
4. `agent/` 文档只做摘要、导航、规则和上下文，不重写一套完整正文
5. 新问题必须先写回所属阶段文档，再决定是否进入 `human/operations/issue_index.md`
6. 新增、移动、合并、删除文档后，必须同步更新：
   - 本文档
   - 所属目录的 `README.md`
   - [agent/doc_map.md](agent/doc_map.md)
   - 受影响文档中的相互引用
7. 文档默认尽量使用中文，只有必要术语、代码标识、协议名、命令、错误码保留英文

## 当前目录

- [human/README.md](human/README.md)
- [agent/README.md](agent/README.md)
