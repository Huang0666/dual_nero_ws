# 项目状态

## 当前结论

- P1 已完成。
- P2 已完成并通过现场验收（bridge 路线）。
- P3 主体已完成：
  - P3-A：故障恢复 SOP 已落地。
  - P3-B：MoveIt 主路径已完成现场验证。
  - P3-C：USB-CAN 固定命名保持暂缓。
- 当前项目处于 `P4 双臂固定场景任务闭环` 阶段。
- 真机成果保留，但后续开发主线已切到 `Gazebo Harmonic / gz sim` 仿真。
- 仿真后端已验证打通：
  - `controller_manager`
  - `joint_state_broadcaster`
  - 左右臂 `FollowJointTrajectory`
  - `/joint_states`
  - `run_dual_arm_task --task dual_prep_sync`

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

## 当前阶段卡点

当前卡点不再是仿真后端能否启动，而是：

- 启动日志里仍有 controller 重复配置噪声需要收口
- P4 任务点位与空间建模仍未完成
- 真机工位与模型对齐仍未完成

## 当前最高优先级

1. 固化 server-only 仿真主线，收口启动噪声
2. 继续完成 P4 的初始位 / 安全位 / 预备位建模
3. 等工位和模型对齐后，再回到真机执行 `dual_prep_sync` 正式验收

## 当前风险

- Gazebo GUI 渲染链当前仍不稳定，默认只能保证 server-only 仿真后端
- 速度 / 加速度限位尚未替换为厂家真实值
- 当前双臂目标点位还未与现场空间摆放完成对齐
- 双臂协调、避障、视觉、抓取仍未进入正式实现阶段
