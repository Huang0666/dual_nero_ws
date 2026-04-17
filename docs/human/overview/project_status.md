# 项目状态

## 当前结论

- P1 已完成。
- P2 已完成并通过现场验收（bridge 路线）。
- P3 主体已完成：
  - P3-A：故障恢复 SOP 已落地。
  - P3-B：MoveIt 主路径已完成现场验证。
  - P3-C：USB-CAN 固定命名保持暂缓。
- 当前项目处于 `P5-Sim 第一版实施阶段`。
- 真机成果保留，但后续开发主线已切到 `Gazebo Harmonic / gz sim` 仿真。
- 仿真后端已验证打通：
  - `controller_manager`
  - `joint_state_broadcaster`
  - 左右臂 `FollowJointTrajectory`
  - `/joint_states`
  - `run_dual_arm_task --task dual_prep_sync`

当前口径：

- `P4-A 仿真执行链`：已完成
- `P4-B 真机固定场景闭环`：延期，等待工位与模型对齐
- `P5-Sim`：第一版实施中

补充说明：

- 上面“仿真后端已验证打通”指的是 `P4` 基线仿真链已验证通过。
- 本轮 `P5` 新改动已引入：
  - 多 stage task schema
  - 静态 scene profile
  - `Planning Scene` 注入代码
  - `ign_ros2_control` 插件链切换
- 这些新增改动在 Linux 上仍待回归确认。用户最近一次验证时看到：
  - `Failed to load system plugin [libgz_ros2_control-system.so]`
  - `ros2 control list_controllers` 返回 `No controllers are currently loaded!`
- 因此当前不能把最新 `P5` 场景链和最新插件链视为“已验证通过”。

## 当前正式可交付路径

- 真机正式任务入口：`ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync`
- 仿真正式入口：`ros2 launch dual_nero_bringup simulation.launch.py`
- 仿真默认模式：server-only `gz sim`，优先保证控制器链和任务入口可用

说明：

- 当前原生 `ExecuteTrajectory` 不作为正式执行路径。
- 当前 bridge 正式合同仍然是“每个 goal 恰好 1 个 trajectory point”。
- 当前仿真继续复用 P1-P4 的任务入口、MoveIt group、controller 命名和 `FollowJointTrajectory` 合同。

## 已完成能力

### P1

- 双臂只读
- `/joint_states`
- 左右臂单点 action

### P2

- preflight 正式接入 action / topic 入口
- 统一错误码和 reject / abort 语义

### P3

- 恢复 SOP 已形成正式文档
- MoveIt 主路径已完成现场验证

### P4

- 正式任务入口 CLI 已落地
- `p4_tasks.yaml` 已固化
- `--target safe` 已支持
- 结果等待与 cleanup 的工程问题已修正
- 仿真后端已验证可用，`dual_prep_sync` 的 prep / return 已在仿真中执行成功

### P5-Sim

- 已具备启动前提，且当前已进入第一版实施：
  - P4 仿真执行链打通
  - MoveIt / controller / task 入口合同稳定
  - 已形成 [../phases/p5/README.md](../phases/p5/README.md) 作为实施边界文档
  - 已开始把 `run_dual_arm_task` 从 P4 固定结构升级到 P5 多 stage 结构
  - 已补上静态 scene profile 与 Planning Scene 注入代码骨架，待 Linux 仿真回归验证
  - 已尝试切换到 `ign_ros2_control` 插件链，待 Linux 回归验证 controller 是否恢复

## 当前阶段卡点

当前卡点不再是仿真后端能否启动，而是：

- P4-B 需要的真机工位与模型对齐被明确延期
- P4-B 需要的真机固定点位仍未完成
- P5-Real 的最终安全结论不能脱离真实工位

## 当前最高优先级

1. 先完成 `P5-Sim` 最新改动的 Linux 回归验证：controller 恢复、`dual_stage_demo` 跑通、scene 坐标贴合
2. 保留 `P4-B` 真机部分，等待工位与模型对齐恢复
3. 把后续能力按阶段挂到 `P6 / P7 / P8`，避免重新塞回 P5

## 当前风险

- Gazebo GUI 渲染链当前仍不稳定，默认只能保证 server-only 仿真后端
- 速度 / 加速度限位尚未替换为厂家真实值
- 当前双臂目标点位尚未与现场空间摆放完成对齐
- 双臂协调、避障、视觉、抓取仍未进入正式实现阶段
