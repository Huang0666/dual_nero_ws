# 交接摘要

## 当前项目状态

- P1 已完成
- P2 已完成并通过现场验收
- P3 主体已完成
- 当前进入 `P5-Sim 第一版收口验收阶段`

## 当前有效结论

- bridge 路线仍为正式上层合同
- P4 正式任务入口已落地：`run_dual_arm_task`
- 已支持 `--target safe` 回固定安全位
- P4-B 最小闭环验收入口已准备：`run_p4b_acceptance --task dual_prep_sync --cycles 3`，待工位与模型对齐恢复后执行
- 当前后续开发主线已切到 gz sim 仿真层
- 仿真后端已验证可用，`dual_prep_sync` 已在仿真中执行成功
- 当前阶段口径：
  - `P4-A` 已完成
  - `P4-B` 延期
  - `P5-Sim` 第一版实施完成，收口验收中

## 本轮新增并已完成 Linux 回归验证

- `run_dual_arm_task` 已升级到 P5 多 stage task schema，并保持 P4 配置兼容
- 已新增：
  - `src/dual_nero_bridge/config/p5_tasks.yaml`
  - `src/dual_nero_bridge/config/p5_scene_sim.yaml`
  - `src/dual_nero_bridge/config/p5_scene_real.yaml`
  - `src/dual_nero_bridge/dual_nero_bridge/planning_scene_utils.py`
- 已把 `sim_static_demo` 障碍物坐标重新收回到双臂基座附近
- 已统一仿真 ros2_control 默认插件链到 `gz_ros2_control`
- 已修正一处默认值残留：
  - `src/dual_nero_bringup/config/simulation.yaml`
  - `src/dual_nero_moveit_config/config/dual_nero_description.ros2_control.xacro`
  - `src/dual_nero_moveit_config/config/dual_nero_description.urdf.xacro`
  - 上述默认值已统一，不再出现 `gz/ign` 混用回落
- 已修正：
  - `controller_manager_name` 前导 `/` 导致的 `InvalidNodeNameError`
  - `move_group use_sim_time=false` 导致 Execute 失败的问题
- 最新 Linux 回归结果：
  - `controller_manager`、`joint_state_broadcaster`、左右臂 controller 均可激活
  - `/clock`、`/joint_states` 正常
  - `run_dual_arm_task --task dual_prep_sync` 成功
  - MoveIt RViz `Plan & Execute` 恢复可执行

## 当前暂停点

- 当前不再卡在仿真后端
- 当前剩余问题主要是真机部分延期，以及 P5-Sim 收口验收文档留档

## 下一步

- 先完成 `dual_stage_demo` 结果留档和 `sim_static_demo` 几何微调，形成 P5-Sim v1 收口记录
- 同时把 P6 进入条件固定在 `docs/human/phases/p6/README.md`
- 把动态障碍物 / 复杂调度 / 复杂真机验收挂到 `docs/human/phases/p7/README.md` 和 `docs/human/phases/p8/README.md`
- 再等工位与模型对齐恢复 P4-B 真机工作
- 工位恢复后使用 `run_p4b_acceptance --task dual_prep_sync --cycles 3` 留档 P4-B 最小闭环验收结果

## 执行块规则

- 后续任务按最低 `1 小时` 的执行块推进。
- 5 分钟心跳只检查状态；如果当前执行块仍在进行中，不启动下一块。
- 执行块结束时必须留下产物或阻塞结论。
- 当前 `P5-Sim-01 仿真基线复核` 已在 Windows shell 尝试启动，但 `ros2`、`colcon`、`gz` 不可用；WSL 仅有 stopped 的 `docker-desktop`，因此阻塞在运行环境。
- 在切换到可用 Linux ROS 2 / Gazebo 环境前，不启动 `P5-Sim-02`。
- 当前执行顺序：
  1. `P5-Sim-01 仿真基线复核`
  2. `P5-Sim-02 dual_stage_demo 全流程验收`
  3. `P5-Sim-03 sim_static_demo 几何贴合`
  4. `P5-Sim-04 收口文档固化`
  5. `P6-Plan-01 视觉与简单抓取进入条件`
  6. `P4B-Real-01 真机最小闭环验收`（等待现场恢复）
- 导航 / 建图暂不进入当前执行块；后续应单独建阶段承接移动底盘、SLAM、Nav2。

## 新窗口立即执行的最小验证

1. 重新编译并 source：

```bash
cd ~/dual_nero_ws_project/dual_nero_ws
colcon build --packages-select dual_nero_bridge dual_nero_bringup dual_nero_moveit_config
source install/setup.bash
```

2. 启动仿真：

```bash
ros2 launch dual_nero_bringup simulation.launch.py
```

3. 先看仿真日志里这几项：

- `sim_control_hardware_plugin`
- `sim_control_system_plugin`
- `sim_control_system_plugin_name`
- 不应出现 `Failed to load system plugin`

4. 新终端检查 controller 与时钟域：

```bash
source ~/dual_nero_ws_project/dual_nero_ws/install/setup.bash
ros2 control list_controllers
ros2 param get /move_group use_sim_time
```

目标是看到：

- `joint_state_broadcaster active`
- `left_arm_controller active`
- `right_arm_controller active`
- `/move_group use_sim_time` 为 `True`

5. 通过后再继续跑：

```bash
ros2 run dual_nero_bridge run_dual_arm_task \
  --task dual_stage_demo \
  --task-config ~/dual_nero_ws_project/dual_nero_ws/install/dual_nero_bridge/share/dual_nero_bridge/config/p5_tasks.yaml \
  --scene-config ~/dual_nero_ws_project/dual_nero_ws/install/dual_nero_bridge/share/dual_nero_bridge/config/p5_scene_sim.yaml
```

## 关键文档入口

- 仓库级规则：`/.codex/AGENTS.md`
- 项目状态：[../human/overview/project_status.md](../human/overview/project_status.md)
- 下一步任务：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- 仿真手册：[../human/operations/simulation_runbook.md](../human/operations/simulation_runbook.md)
- P4 定义：[../human/phases/p4/README.md](../human/phases/p4/README.md)
- P5 定义：[../human/phases/p5/README.md](../human/phases/p5/README.md)
