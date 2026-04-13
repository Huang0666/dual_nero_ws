# 下一步任务

## 当前阶段

- 当前阶段：`P4 双臂固定场景任务闭环`
- P1、P2、P3 主体已完成

## 当前总目标

- 双臂协调运动
- 避障
- 视觉接入
- 简单抓取任务

## 优先级 A：完成 P4 双臂任务闭环验收

- 在动作模式下执行 `dual_prep_sync`，完成多次重复验证
- 固化任务安全位/预备位/返回位配置
- 失败时按 P3-A SOP 处理，不做临时指令拼凑
- 当前阶段定义入口：[../phases/p4/README.md](../phases/p4/README.md)

## 优先级 B：保持 P4-P6 路线冻结

- 路线入口：[roadmap.md](roadmap.md)

## 优先级 C：保留待办但当前不做

- USB-CAN 固定命名与批量映射稳定化
- `dual_arms` MoveIt 验证增强项
- MoveIt 厂家真实速度/加速度参数回填

## 本阶段不做

- 切换到 native `ros2_control` plugin
- 大规模架构重写
- 在未定义任务目标前继续扩散验证范围

## 当前建议入口

- 项目状态入口：[project_status.md](project_status.md)
- P3 验证报告入口：[../phases/p3/moveit_validation_report.md](../phases/p3/moveit_validation_report.md)
- P3 恢复 SOP 入口：[../phases/p3/recovery_sop.md](../phases/p3/recovery_sop.md)
