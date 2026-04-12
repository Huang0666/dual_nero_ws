# 当前上下文

## 当前阶段

- P1：已完成
- P2：已完成并通过现场验收
- P3：主体已完成
- 当前阶段：`P4 目标定义`

## 最终目标

- 双臂协调运动
- 避障
- 视觉接入
- 简单抓取任务

## 最近已完成

- P2 preflight 已接入正式 action/topic 入口
- P2 已完成现场验收
- 文档结构已切换到 `human/` 与 `agent/` 双视图
- P3-A 恢复 SOP 已落地
- P3-B 主路径已现场验证通过：
  - 左右臂规划
  - 左右臂 `bridge-final-point` 执行
  - 只读负例
- MoveIt 速度/加速度限位已补保守占位值，TOTG 默认警告已消失

## 当前正式路径

- bridge 架构继续保留
- 不切到 native `ros2_control`
- 当前正式 MoveIt 执行路径是：
  - 规划
  - 提取末点
  - 通过单点 `FollowJointTrajectory` 走 bridge

## 当前优先级

1. 定义 P4 的目标和验收标准
2. 把 P4-P6 路线与最终目标对齐
3. 不推进 P3-C 的固定命名实现

## 当前不做

- 不做 P3-C 的固定命名实现
- 不切架构
- 不把原生 `ExecuteTrajectory` 写成当前正式执行路径
- 不在未定义任务目标前继续扩散验证范围

## 当前应优先参考

- Human 状态入口：[../human/overview/project_status.md](../human/overview/project_status.md)
- Human 下一步入口：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- P3 验证报告：[../human/phases/p3/moveit_validation_report.md](../human/phases/p3/moveit_validation_report.md)
