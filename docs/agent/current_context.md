# 当前上下文

## 当前阶段

- P1：已完成
- P2：已完成并通过现场验收
- 当前阶段：P3

## 当前优先级

1. P3-A：故障恢复 SOP 标准化
2. P3-B：MoveIt 执行链系统化验证
3. P3-C：USB-CAN 固定命名（暂缓）

## 当前架构边界

- 继续使用 bridge 路线
- 不切到 native `ros2_control`
- 冻结命名合同不改

## 最近已完成

- P2 preflight 已接入正式 action/topic 入口
- P2 已完成现场验收
- 文档结构已切换到 `human/` 与 `agent/` 双视图
- P3-B 最小 MoveIt 验证 CLI 已加入 `dual_nero_bridge`

## 当前应优先参考

- Human 状态入口：[../human/overview/project_status.md](../human/overview/project_status.md)
- Human 下一步入口：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- P3-A SOP：[../human/phases/p3/recovery_sop.md](../human/phases/p3/recovery_sop.md)
- P3-B 计划：[../human/phases/p3/moveit_validation_plan.md](../human/phases/p3/moveit_validation_plan.md)

## 当前不做

- 不做 P3-C 的固定命名实现
- 不切架构
- 不写第二套独立事实正文
