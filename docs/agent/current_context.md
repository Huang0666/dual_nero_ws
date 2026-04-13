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
- MoveIt 速度/加速度限位已补保守占位值，TOTG 默认警告已消失
- P4 双臂正式任务入口已落地：`run_dual_arm_task --task dual_prep_sync`

## 当前正式路径

- bridge 架构继续保留
- 不切到 native `ros2_control`
- MoveIt 正式执行路径：规划 -> 取末点 -> 单点 `FollowJointTrajectory` 走 bridge
- P4 正式任务入口：双臂 `dual_arms` 规划 -> 分裂左右臂单点 goal -> 同步下发

## 当前优先级

1. 现场验收 P4 双臂任务闭环
2. 固化任务配置与执行约束
3. 不推进 P3-C 的固定命名实现

## 当前对 P4 的约束

- P4 从双臂任务开始，不退回单臂优先
- P4 先做固定场景、固定工位、无视觉、低风险双臂任务
- P5 再正式引入双臂协调约束和避障

## 当前不做

- 不做 P3-C 的固定命名实现
- 不切架构
- 不把原生 `ExecuteTrajectory` 写成当前正式执行路径
- 不在未定义任务目标前继续扩散验证范围

## 当前应优先参考

- Human 状态入口：[../human/overview/project_status.md](../human/overview/project_status.md)
- Human 任务入口：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- Human 路线入口：[../human/overview/roadmap.md](../human/overview/roadmap.md)
- P4 阶段定义入口：[../human/phases/p4/README.md](../human/phases/p4/README.md)
- P3 验证报告入口：[../human/phases/p3/moveit_validation_report.md](../human/phases/p3/moveit_validation_report.md)
