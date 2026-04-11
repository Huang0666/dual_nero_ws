# Agent 规则

## 总原则

1. 只保留一套项目事实
2. `human/` 是正文，`agent/` 是索引和规则
3. 先更新正文，再更新 agent 摘要

## 文档更新硬规则

1. 改代码后，必须判断是否影响文档
2. 改启动、执行、恢复命令后，必须更新 human 操作文档
3. 新问题先写回所属阶段文档，再决定是否进入 `issue_index.md`
4. 阶段状态变化后，必须更新：
   - `human/overview/project_status.md`
   - `human/overview/next_actions.md`
   - `agent/current_context.md`
5. 新增、移动、删除文档后，必须更新：
   - `docs/README.md`
   - 所属目录 `README.md`
   - `agent/doc_map.md`

## 禁止事项

1. 不在根目录新增项目级文档
2. 不写第二套独立的事实正文
3. 不把问题只写在 `issue_index.md`，不写来源阶段
4. 不把 P3-C 写成当前已落地能力

## 当前协作规则

- 默认尽量使用中文文档
- 人类文档强调背景、结论和操作
- agent 文档强调规则、结构、入口和当前状态
- 文档结构重构时，要同步修代码里的文档路径引用
