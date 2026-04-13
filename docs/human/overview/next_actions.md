# 下一步任务

## 当前阶段

- 当前阶段：`P4 目标定义`
- P1、P2、P3 主体已完成

## 当前总目标

- 双臂协调运动
- 避障
- 视觉接入
- 简单抓取任务

## 优先级 A：定义 P4 的任务目标

- 不再继续把阶段定义成零散验证项。
- 先把 P4 明确定义成“从已验证执行链走向真实物理任务”的第一阶段。
- 需要回答清楚：
  - P4 的第一个双臂任务样例具体是什么
  - P4 是否先做无视觉任务
  - P4 的验收是“能规划执行”还是“能完成一个真实动作目标”
- 当前阶段定义入口：
  - [../phases/p4/README.md](../phases/p4/README.md)

## 优先级 B：给出 P4-P6 的整体路线

- 需要把后续阶段和最终目标对齐，而不是继续沿用早期临时编号。
- 当前建议的规划方向是：
  - P4：真实物理动作任务闭环
  - P5：双臂协调运动与避障
  - P6：视觉接入与简单抓取
- 该路线还需要正式冻结到文档。
- 总路线文档：
  - [roadmap.md](roadmap.md)

## 优先级 C：保留待办但当前不做

- USB-CAN 固定命名与批量映射稳定化
- `dual_arms` MoveIt 验证增强项
- MoveIt 厂家真值速度/加速度参数回填

## 本阶段不做

- 切换到 native `ros2_control` plugin
- 大规模架构重写
- 在未定义任务目标前继续扩散验证范围

## 当前建议入口

- 项目状态：
  - [project_status.md](project_status.md)
- P3 验证报告：
  - [../phases/p3/moveit_validation_report.md](../phases/p3/moveit_validation_report.md)
- P3 恢复 SOP：
  - [../phases/p3/recovery_sop.md](../phases/p3/recovery_sop.md)
