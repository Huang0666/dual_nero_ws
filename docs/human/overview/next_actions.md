# 下一步任务

## 当前阶段

- 当前阶段：`P4 双臂固定场景任务闭环`
- P1、P2、P3 主体已完成

## 当前总目标

- 双臂协调运动
- 避障
- 视觉接入
- 简单抓取任务

## 优先级 A：切到仿真主线继续推进

- 启动 `simulation.launch.py`
- 先在 gz sim 中验证 `run_dual_arm_task`
- 保持 P1-P4 任务入口、MoveIt group、controller 合同不变
- 当前入口：[../operations/simulation_runbook.md](../operations/simulation_runbook.md)

## 优先级 B：继续做点位与空间建模

- 固定一组可重复回位的初始/安全位
- 明确左右臂在当前工位下的安全活动空间
- 再在该空间内定义预备位和任务位
- 当前入口：[../operations/hardware_alignment_checklist.md](../operations/hardware_alignment_checklist.md)

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
