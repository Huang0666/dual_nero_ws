# 下一步任务

## 当前阶段

- 当前阶段：`P4 双臂固定场景任务闭环`
- P1、P2、P3 主体已完成

## 当前总目标

- 双臂协调运动
- 避障
- 视觉接入
- 简单抓取任务

## 优先级 A：先做 P4 点位与空间建模

- 固定一组可重复回位的初始/安全位
- 明确左右臂在当前工位下的安全活动空间
- 再在该空间内定义预备位和任务位
- 当前阶段定义入口：[../phases/p4/README.md](../phases/p4/README.md)
- 对齐清单入口：[../operations/hardware_alignment_checklist.md](../operations/hardware_alignment_checklist.md)

## 优先级 B：暂停盲试，保留正式入口

- 暂停继续盲目增大动作幅度试错
- 保留 `run_dual_arm_task` 作为正式任务入口
- 等点位建模完成后，再恢复真机验收

## 优先级 C：保留待办但当前不做

- USB-CAN 固定命名与批量映射稳定化
- `dual_arms` MoveIt 验证增强项
- MoveIt 厂家真实速度/加速度参数回填

## 本阶段不做

- 切换到 native `ros2_control` plugin
- 大规模架构重写
- 在空间关系未定义清楚前继续扩散真机验证范围

## 当前建议入口

- 项目状态入口：[project_status.md](project_status.md)
- P4 阶段定义入口：[../phases/p4/README.md](../phases/p4/README.md)
- P3 恢复 SOP 入口：[../phases/p3/recovery_sop.md](../phases/p3/recovery_sop.md)
