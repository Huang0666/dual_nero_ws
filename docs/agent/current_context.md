# 当前上下文

## 当前阶段

- P1：已完成
- P2：已完成并通过现场验收
- P3：主体已完成
- 当前阶段：`P5-Sim 第一版收口验收阶段`

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
  - `P5-Sim`：第一版实施中
- 本轮已落地并回归通过的改动：
  - `run_dual_arm_task` 升级为多 stage task schema
  - 新增 `p5_tasks.yaml`
  - 新增静态场景 profile 与 `Planning Scene` 注入代码
  - 修正仿真插件默认值并统一到 `gz_ros2_control`
  - 修正 `controller_manager_name` 前导 `/` 问题
  - 在 bringup 层对 `move_group` / `rviz` 强制注入 `use_sim_time`
- 本轮 Linux 回归结论：controller 可激活，`/joint_states` 正常，`dual_prep_sync` 与 RViz `Plan & Execute` 可执行

## 当前正式路径

- 正式执行架构仍保持 bridge 合同，不切到另一套上层入口
- 仿真默认使用 server-only `gz sim`
- P4 基线验证通过时，controller 可自动加载
- 当前默认路径为 `gz_ros2_control / controller_manager`，已完成 Linux 侧验证

## 当前问题判断

当前主开发环境已切到仿真层。真机成果保留，但当前主要问题不再是仿真能否跑起来，而是：

- P4-B 依赖的工位与模型对齐被延期
- P4-B 依赖的真机固定点位尚未完成
- P5-Real 的最终安全结论仍不能脱离真实工位

## 当前优先级

1. 按 [../human/phases/p5/README.md](../human/phases/p5/README.md) 继续做 P5-v1：多 stage task、最小协同语义、最小失败策略、能力验证场景
2. 保留 P4-B 真机部分，等待工位与模型对齐恢复
3. 完成 `dual_stage_demo` 的验收留档与 `sim_static_demo` 几何微调
4. 按 [../human/phases/p6/README.md](../human/phases/p6/README.md) 规划 P6 进入条件
5. 把动态障碍物 / 复杂调度 / 复杂真机验收挂到 P7 / P8，而不是塞回 P5

## 当前应优先参考

- 仓库级规则：`/.codex/AGENTS.md`
- [../human/overview/project_status.md](../human/overview/project_status.md)
- [../human/overview/next_actions.md](../human/overview/next_actions.md)
- [../human/operations/simulation_runbook.md](../human/operations/simulation_runbook.md)
- [../human/phases/p4/README.md](../human/phases/p4/README.md)
- [../human/phases/p5/README.md](../human/phases/p5/README.md)
