# Doc Checklist

## 作用

记录当前文档结构的硬规则与自检清单，用于约束新增/修改文档时的更新范围。

## 硬规则

1. 项目级文档默认只放在 `docs/` 下，根目录仅保留 `README.md` 作为总入口。
2. `docs/` 采用 `human/` 与 `agent/` 双视图结构，事实内容只保留一套。
3. 新增事实类内容必须先更新 `docs/human/` 的阶段或操作文档，再同步 `docs/agent/` 摘要。
4. 修改阶段目标或阶段结论时必须同步更新：
   - `docs/human/overview/project_status.md`
   - `docs/human/overview/next_actions.md`
   - `docs/human/overview/roadmap.md`（如影响路线）
   - `docs/agent/current_context.md`
5. 新增/修改操作命令时必须同步更新：
   - `docs/human/operations/migration_runbook.md`
   - `docs/agent/handoff.md`
6. 新增/移动/合并文档后必须更新：
   - `docs/README.md`
   - 对应目录的 `README.md`
   - `docs/agent/doc_map.md`

## 自检清单（提交前）

- [ ] 新增/修改文档已同步 `docs/README.md`
- [ ] 阶段变化已同步 `project_status.md`
- [ ] 下一步任务已同步 `next_actions.md`
- [ ] 关键入口命令已同步 `migration_runbook.md`
- [ ] agent 侧 `current_context.md`/`handoff.md`/`doc_map.md` 已同步
