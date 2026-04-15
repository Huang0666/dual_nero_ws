# 下一步任务

## 当前阶段

- 当前阶段：`P5-Sim 规划启动阶段`
- P1、P2、P3 主体已完成
- `P4-A` 已完成，`P4-B` 延期

## 优先级 A：启动 P5-Sim

- 在现有 MoveIt 基础上继续做双臂协同能力
- 引入场景障碍物、Planning Scene 和约束
- 定义双臂同步 / 串行执行策略
- 维持当前任务入口和 controller 合同不变
- 当前边界入口：[architecture_layers.md](architecture_layers.md)
- 当前实施入口：[../phases/p5/README.md](../phases/p5/README.md)

## 优先级 B：保留 P4-B 真机部分

- 工位与模型对齐延后一周
- 固定位、预备位、任务位的真机确认暂缓
- 真机闭环验收暂缓
- 当前入口：[../operations/hardware_alignment_checklist.md](../operations/hardware_alignment_checklist.md)

## 优先级 C：规划 P6 进入条件

- 明确 P6 依赖哪些 P5 成果
- 明确视觉坐标链路和简单抓取边界
- 当前入口：[../phases/p6/README.md](../phases/p6/README.md)

## 优先级 D：回到真机做阶段验收

- 在仿真里固化点位后，再回到真机执行 `dual_prep_sync`
- 用同一套任务入口做正式验收，不另起第二条链路

## 优先级 E：保留待办但当前不做

- USB-CAN 固定命名与批量映射稳定化
- `dual_arms` MoveIt 验证增强项
- MoveIt 厂家真实速度 / 加速度参数回填
