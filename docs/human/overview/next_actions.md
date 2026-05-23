# 下一步任务

## 当前阶段

- 当前阶段：`P5-Sim 第一版收口验收阶段`
- P1、P2、P3 主体已完成
- `P4-A` 已完成，`P4-B` 延期

## 执行节奏

- 后续任务按执行块推进，每个执行块最低预估 `1 小时`。
- 5 分钟心跳只检查状态；如果当前执行块仍在进行中，不启动下一个执行块。
- 每个执行块结束时必须留下明确产物：验收记录、配置差异、文档更新，或阻塞原因。
- 不把导航 / 建图提前塞入当前阶段；移动底盘、SLAM、Nav2 相关工作应在双臂 P5/P6/P7/P8 边界稳定后单独立阶段。

## 一小时执行块计划

当前执行块状态：

- `P5-Sim-01 仿真基线复核` 已尝试启动，但当前 Windows shell 缺少 `ros2`、`colcon`、`gz`。
- 本机 WSL 仅发现 `docker-desktop` 且处于 stopped 状态，未发现可用 Ubuntu / ROS 2 / Gazebo 环境。
- 因此该执行块当前阻塞在运行环境，不启动 `P5-Sim-02`。
- 恢复条件：切换到已安装 ROS 2 + Gazebo Harmonic / gz sim 的 Linux 环境，并按 handoff 中的最小验证步骤重新执行。

1. `P5-Sim-01 仿真基线复核`（最低 1 小时）
   - 目标：重新确认 `simulation.launch.py`、controller、`/clock`、`/joint_states`、`dual_prep_sync` 基线可用。
   - 产物：记录 controller 状态、`use_sim_time`、`dual_prep_sync` 结果；若失败，记录首个阻塞点。

2. `P5-Sim-02 dual_stage_demo 全流程验收`（最低 1 小时）
   - 目标：使用 `p5_tasks.yaml` 与 `p5_scene_sim.yaml` 跑通 `dual_stage_demo`。
   - 产物：保存各 stage 的 plan / execute JSON 摘要，并更新 P5 收口结论。

3. `P5-Sim-03 sim_static_demo 几何贴合`（最低 1 小时）
   - 目标：检查静态障碍物与当前 URDF / MoveIt frame 的贴合关系，只做几何微调。
   - 产物：如需修改，更新 `p5_scene_sim.yaml`；同步记录修改原因和验证结果。

4. `P5-Sim-04 收口文档固化`（最低 1 小时）
   - 目标：把 P5-Sim v1 的已验收项、剩余限制、不可替代真机结论写回权威文档。
   - 产物：更新 `p5/README.md`、`project_status.md`、`next_actions.md`、`agent/current_context.md`、`agent/handoff.md`。

5. `P6-Plan-01 视觉与简单抓取进入条件`（最低 1 小时）
   - 目标：在 P5-Sim 收口后，明确 P6 需要的相机、TF、标定、简单目标样例和不做事项。
   - 产物：更新 `p6/README.md`，不直接实现视觉代码。

6. `P4B-Real-01 真机最小闭环验收`（最低 1 小时，等待现场恢复）
   - 目标：工位与模型对齐恢复后，运行 `run_p4b_acceptance --task dual_prep_sync --cycles 3`。
   - 产物：记录 return/safe 偏差、safe 重复性和是否通过；未恢复现场前不启动。

## 优先级 A：收口 P5-Sim v1

- 保持当前任务入口和 controller 合同不变
- 固化本轮修复后的稳定启动路径（插件默认值、`use_sim_time`、controller 激活）
- 跑通并留档 `dual_stage_demo` 的完整回归记录
- 微调 `sim_static_demo` 坐标贴合当前 URDF（只做几何贴合，不扩展功能边界）
- 更新验收文档，形成“P5-Sim v1 已实施完成”的可追溯结论
- 当前边界入口：[architecture_layers.md](architecture_layers.md)
- 当前实施入口：[../phases/p5/README.md](../phases/p5/README.md)

## 优先级 B：保留 P4-B 真机部分

- 工位与模型对齐延后一周
- 固定位、预备位、任务位的真机确认暂缓
- 真机闭环验收暂缓
- 工位恢复后，用 `run_p4b_acceptance --task dual_prep_sync --cycles 3` 做最小闭环验收留档
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
