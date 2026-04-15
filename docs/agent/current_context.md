# 当前上下文

## 当前阶段

- P1：已完成
- P2：已完成并通过现场验收
- P3：主体已完成
- 当前阶段：`P4 / P5 过渡阶段`

## 最近已完成

- P4 正式任务入口已落地：`run_dual_arm_task --task dual_prep_sync`
- 已支持 `--target safe` 直接回固定安全位
- 已修正结果等待与 cleanup 的主要工程问题
- 仿真主线已切到 `Gazebo Harmonic / gz sim`
- 仿真后端已验证打通：
  - `controller_manager`
  - `/joint_states`
  - 左右臂 `FollowJointTrajectory`
  - `run_dual_arm_task --task dual_prep_sync`
- 当前阶段口径：
  - `P4-A 仿真执行链`：已完成
  - `P4-B 真机固定场景闭环`：延期
  - `P5-Sim`：可启动

## 当前正式路径

- 正式执行架构仍保持 bridge 合同，不切到另一套上层入口
- 仿真默认使用 server-only `gz sim`
- 当前仿真默认由 `gz_ros2_control / controller_manager` 自动加载 controller

## 当前问题判断

当前主开发环境已切到仿真层。真机成果保留，但当前主要问题不再是仿真能否跑起来，而是：

- P4-B 依赖的工位与模型对齐被延期
- P4-B 依赖的真机固定点位尚未完成
- P5-Real 的最终安全结论仍不能脱离真实工位

## 当前优先级

1. 启动 P5-Sim：双臂协同、约束、避障、场景建模
2. 保留 P4-B 真机部分，等待工位与模型对齐恢复
3. 等工位和模型对齐后，再恢复真机任务验收

## 当前应优先参考

- [../human/overview/project_status.md](../human/overview/project_status.md)
- [../human/overview/next_actions.md](../human/overview/next_actions.md)
- [../human/operations/simulation_runbook.md](../human/operations/simulation_runbook.md)
- [../human/phases/p4/README.md](../human/phases/p4/README.md)
