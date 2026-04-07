# Next Actions

## 当前阶段

- 当前阶段：`P2 稳定化与工程化`
- 说明：P1 已完成，当前重点不是再开新架构，而是把 bridge 路线做稳定、可复现、可恢复。
- 当前已完成：正式入口 preflight 第一版

## 最高优先级任务

- 现场验证正式入口 preflight 的 reject / abort 行为
- 增强 bridge/action 日志，记录更清晰的 reject / abort / mapping 信息
- 增加 fault / reconnect / recovery 基础策略

## 次优先级任务

- 做重复性 smoke test，验证连续多轮测试的稳定性
- 整理 USB-CAN 映射确认步骤，减少现场误操作
- 继续评估正式入口保护还需要覆盖哪些路径

## 暂不做的事项

- 不回退去重做 P0 / P1 基线讨论
- 不在这一阶段切换到 native `ros2_control` hardware plugin 路线
- 不扩展复杂协同任务或抓取任务
- 不引入第二套 joints / groups / controllers 命名
- 当前不实现 USB-CAN 固定命名

## 当前阶段退出标准

- 正式入口 preflight 行为已稳定且日志可审查
- 正式入口能在动作前给出更清晰的姿态/限位保护
- 重复性 smoke test 至少完成多轮并保持稳定
- 日志足够支撑现场定位 mapping、连接和执行问题

## 未来 1~2 周建议执行顺序

1. 现场验证 preflight 第一版
2. 增强 bridge/action 日志
3. 做重复性 smoke test
4. 做故障恢复基础策略
5. 评估是否进入 P3 的 MoveIt 执行验证
