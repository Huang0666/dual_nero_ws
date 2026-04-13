# 当前上下文

## 当前阶段

- P1：已完成
- P2：已完成并通过现场验收
- P3：主体已完成
- 当前阶段：`P4 双臂固定场景任务闭环`

## 最终目标

- 双臂协调运动
- 避障
- 视觉接入
- 简单抓取任务

## 最近已完成

- P2 preflight 已接入 action/topic 正式入口
- P3-A 恢复 SOP 已落地
- P3-B MoveIt 主路径已现场验证通过
- P4 双臂正式任务入口已落地：`run_dual_arm_task --task dual_prep_sync`
- P4 已支持通过正式入口直接回固定安全位：`--target safe`
- P4 已修正结果等待与 stop cleanup 的工程问题

## 当前正式路径

- bridge 架构继续保留
- 不切到 native `ros2_control`
- MoveIt 正式执行路径：规划 -> 取末点 -> 单点 `FollowJointTrajectory` 走 bridge
- P4 正式任务入口：双臂 `dual_arms` 规划 -> 分裂左右臂单点 goal -> 任务级同步下发

## 当前问题判断

当前 P4 的主要问题不是底层链路，而是现场任务空间与点位定义。

具体表现：

- CLI、MoveIt、bridge、preflight 都已经接上
- 当前预备位/返回位与现场双臂摆放空间存在冲突
- 继续盲试不会形成正式任务定义

## 当前优先级

1. 固定初始位/安全位
2. 做 P4 点位与空间建模
3. 再恢复真机任务验收

## 当前不做

- 不做 P3-C 的固定命名实现
- 不切架构
- 不在空间关系未定义清楚前继续扩大动作试错

## 当前应优先参考

- Human 状态入口：[../human/overview/project_status.md](../human/overview/project_status.md)
- Human 任务入口：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- P4 阶段定义入口：[../human/phases/p4/README.md](../human/phases/p4/README.md)
- 工位对齐清单入口：[../human/operations/hardware_alignment_checklist.md](../human/operations/hardware_alignment_checklist.md)
- P3 恢复 SOP 入口：[../human/phases/p3/recovery_sop.md](../human/phases/p3/recovery_sop.md)
