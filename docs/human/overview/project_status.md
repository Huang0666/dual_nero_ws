# 项目状态

## 当前结论

- P1 已完成。
- P2 已完成并通过现场验收（bridge 路线）。
- P3 主体已完成：
  - P3-A：故障恢复 SOP 已落地。
  - P3-B：MoveIt 主路径已完成现场验证。
  - P3-C：USB-CAN 固定命名保持暂缓，作为后续待办。
- 当前架构仍为 bridge，未切到 native `ros2_control`。
- 项目当前进入 `P4 双臂固定场景任务闭环` 阶段。

参考：

- [../phases/p2/acceptance_report.md](../phases/p2/acceptance_report.md)
- [../phases/p3/moveit_validation_report.md](../phases/p3/moveit_validation_report.md)
- [roadmap.md](roadmap.md)

## 长期目标

- 双臂能够实现协调运动。
- 双臂能够在规划中考虑避障。
- 后续接入视觉。
- 最终完成简单抓取任务。

## 当前阶段

- 已完成：`P1 最小真实执行链`
- 已完成：`P2 preflight 稳定化与工程化`
- 已完成：`P3 恢复 SOP + MoveIt 主路径验证`
- 进行中：`P4 双臂固定场景任务闭环`

## 当前正式可交付路径

- 启动 `real_hardware.launch.py`
- 通过 MoveIt 完成单臂规划并以 `bridge-final-point` 执行
- P4 正式任务入口：`ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync`

说明：

- 当前原生 `ExecuteTrajectory` 不作为正式执行路径。
- 当前 bridge 正式合同仍然是“每个 goal 恰好 1 个 trajectory point”。

## 已完成能力

### P1

- 双臂只读
- `/joint_states`
- 双臂最小动作
- 左右臂单点 action

### P2

- 启动期映射/安全模式日志
- action/topic 正式入口统一 preflight gate
- 统一错误码与 reject/abort 语义
- dual_arms topic 路径验证通过

### P3-A

- 故障恢复 SOP 已形成正式文档
- 现场常见故障已有统一恢复步骤

### P3-B

- 左臂 MoveIt 规划通过
- 右臂 MoveIt 规划通过
- 左臂 `bridge-final-point` 执行通过
- 右臂 `bridge-final-point` 执行通过
- 只读模式负例通过，错误码为 `ALLOW_MOTION_DISABLED`
- `joint_limits.yaml` 已补保守的速度/加速度占位值，TOTG 默认警告已消失

### P4

- 双臂固定场景任务入口 CLI 已落地
- 任务配置已固化至 `p4_tasks.yaml`
- 已支持正式入口直接回固定安全位
- 已修正任务结果等待与 stop 清理的工程问题

## 当前阶段卡点

当前卡点不是底层链路，而是现场任务空间与点位定义。

具体是：

- 目标位在 MoveIt 与 bridge 合同层面可以表达
- 但当前预备位/返回位与现场双臂实际摆放空间存在冲突
- 继续盲试不会沉淀为正式任务，只会增加试错成本

当前处理入口：

- [../operations/hardware_alignment_checklist.md](../operations/hardware_alignment_checklist.md)

## 当前最高优先级

1. 先完成 P4 的初始位/安全位/预备位建模
2. 明确双臂在当前工位下的可活动安全空间
3. 再回到真机执行 `dual_prep_sync` 正式验收

## 总体路线入口

- [roadmap.md](roadmap.md)
- P4 阶段定义：[../phases/p4/README.md](../phases/p4/README.md)

## 当前风险

- `can0/can1` 重插或重启后仍存在人工确认成本。
- 速度/加速度限位尚未替换为厂家真实值。
- 当前双臂目标点位还未与现场空间摆放完成对齐。
- 双臂协调、避障、视觉、抓取仍未进入正式实现阶段。
