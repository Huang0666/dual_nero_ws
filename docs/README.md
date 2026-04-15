# 文档总入口

## 目的

`docs/` 采用双视图结构：

- `human/`：给人看，强调背景、结论、操作
- `agent/`：给 agent 看，强调规则、映射、当前上下文

事实正文只保留一套，不允许在仓库里平行维护第二套项目结论。

## 先看哪里

### 如果你是人

先看：

- [human/README.md](human/README.md)

常用入口：

- 当前状态：[human/overview/project_status.md](human/overview/project_status.md)
- 下一步：[human/overview/next_actions.md](human/overview/next_actions.md)
- 架构边界：[human/overview/architecture_layers.md](human/overview/architecture_layers.md)
- 仿真手册：[human/operations/simulation_runbook.md](human/operations/simulation_runbook.md)
- 工位对齐：[human/operations/hardware_alignment_checklist.md](human/operations/hardware_alignment_checklist.md)
- P4 定义：[human/phases/p4/README.md](human/phases/p4/README.md)

### 如果你是 agent

先看：

- [agent/README.md](agent/README.md)

常用入口：

- 当前上下文：[agent/current_context.md](agent/current_context.md)
- 文档规则：[agent/rules.md](agent/rules.md)
- 文档映射：[agent/doc_map.md](agent/doc_map.md)
- 仓库结构：[agent/repo_map.md](agent/repo_map.md)

## 硬规则

1. 项目级文档默认只放在 `docs/` 下。
2. 仓库根目录只保留 [README.md](../README.md) 作为项目级 Markdown 入口。
3. 新增事实内容时，优先更新 `human/` 正文，再同步 `agent/` 摘要。
4. `agent/` 只做规则、导航、上下文和映射，不重写第二套事实正文。
5. 新问题必须先写回所属阶段文档，再决定是否进入 `human/operations/issue_index.md`。
6. 新增、移动、合并、删除文档后，必须同步更新本文件、所属目录 `README.md`、[agent/doc_map.md](agent/doc_map.md) 和相关交叉引用。
7. 文档默认尽量使用中文，必要术语、命令、协议名、错误码保留英文。
8. 涉及文档摆放规则的改动，提交前必须运行 `python tools/check_docs_layout.py`。

## 当前规范化入口

- 项目状态、正式能力摘要、交付边界统一以 [human/overview/project_status.md](human/overview/project_status.md) 为准。
- 仿真主线启动、验证、已知限制统一以 [human/operations/simulation_runbook.md](human/operations/simulation_runbook.md) 为准。
- 根目录不再保留 `DOC_CHECKLIST.md`、`OPENSPEC_FEATURE_SUMMARY.md`、`PROJECT_DELIVERY.md` 这类项目级副本文档。

## 提交前自检

- [ ] 没有在仓库根目录新增 `README.md` 之外的项目级 Markdown
- [ ] 运行过 `python tools/check_docs_layout.py`
- [ ] 状态变化已同步 `human/overview/project_status.md`
- [ ] 下一步变化已同步 `human/overview/next_actions.md`
- [ ] 仿真/启动命令变化已同步 `human/operations/simulation_runbook.md`
- [ ] `agent/current_context.md`、`agent/handoff.md`、`agent/doc_map.md` 已同步

## 当前目录

- [human/README.md](human/README.md)
- [agent/README.md](agent/README.md)
