# 下一步任务

## 当前阶段

- 当前阶段：`P5-Sim 第一版实施阶段`
- P1、P2、P3 主体已完成
- `P4-A` 已完成，`P4-B` 延期

## 优先级 A：启动 P5-Sim

- 先把 `run_dual_arm_task` 升级为 P5 多 stage task schema
- 接着收口最小 execution mode：`sync / serial_left_first / serial_right_first`
- 补最小失败策略：`abort / return_safe`
- 再接静态 Planning Scene 能力验证场景
- 全程维持当前任务入口和 controller 合同不变
- 当前最先要做的不是继续扩功能，而是回归确认最新改动：
  - `ign_ros2_control` 插件链是否真正恢复 controller
  - `sim_static_demo` 坐标是否贴合当前 URDF
  - `dual_stage_demo` 是否能完整跑通
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

## 优先级 D：把后续增强项挂到 P7 / P8

- P7：动态障碍物、更复杂调度、按需评估 MTC / BT
- P8：复杂真机验收、复杂抓取、更高强度现场安全结论
- 当前入口：[../phases/p7/README.md](../phases/p7/README.md)
- 当前入口：[../phases/p8/README.md](../phases/p8/README.md)

## 优先级 E：回到真机做阶段验收

- 在仿真里固化点位后，再回到真机执行 `dual_prep_sync`
- 用同一套任务入口做正式验收，不另起第二条链路

## 优先级 F：保留待办但当前不做

- USB-CAN 固定命名与批量映射稳定化
- `dual_arms` MoveIt 验证增强项
- MoveIt 厂家真实速度 / 加速度参数回填
