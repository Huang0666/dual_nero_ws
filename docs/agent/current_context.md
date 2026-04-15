# 当前上下文

## 当前阶段

- P1：已完成
- P2：已完成并通过现场验收
- P3：主体已完成
- 当前阶段：`P4 双臂固定场景任务闭环`

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

## 当前正式路径

- 正式执行架构仍保持 bridge 合同，不切到另一套上层入口
- 仿真默认使用 server-only `gz sim`
- 当前仿真默认由 `gz_ros2_control / controller_manager` 自动加载 controller

## 当前问题判断

当前主开发环境已切到仿真层。真机成果保留，但当前主要问题不再是仿真能否跑起来，而是：

- 启动日志里 controller 重复配置噪声需要收口
- P4 点位与空间建模尚未完成
- 真机工位与模型对齐尚未完成

## 当前优先级

1. 固化 server-only 仿真可用主线，去掉重复 controller spawner 噪声
2. 继续做 P4 点位与空间建模
3. 等工位和模型对齐后，再恢复真机任务验收

## 当前应优先参考

- [../human/overview/project_status.md](../human/overview/project_status.md)
- [../human/overview/next_actions.md](../human/overview/next_actions.md)
- [../human/operations/simulation_runbook.md](../human/operations/simulation_runbook.md)
- [../human/phases/p4/README.md](../human/phases/p4/README.md)
