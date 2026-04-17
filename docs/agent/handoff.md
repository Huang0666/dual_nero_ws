# 交接摘要

## 当前项目状态

- P1 已完成
- P2 已完成并通过现场验收
- P3 主体已完成
- 当前进入 `P5-Sim 第一版实施阶段`

## 当前有效结论

- bridge 路线仍为正式上层合同
- P4 正式任务入口已落地：`run_dual_arm_task`
- 已支持 `--target safe` 回固定安全位
- 当前后续开发主线已切到 gz sim 仿真层
- 仿真后端已验证可用，`dual_prep_sync` 已在仿真中执行成功
- 当前阶段口径：
  - `P4-A` 已完成
  - `P4-B` 延期
  - `P5-Sim` 第一版实施中

## 本轮新增但尚未完成 Linux 回归验证

- `run_dual_arm_task` 已升级到 P5 多 stage task schema，并保持 P4 配置兼容
- 已新增：
  - `src/dual_nero_bridge/config/p5_tasks.yaml`
  - `src/dual_nero_bridge/config/p5_scene_sim.yaml`
  - `src/dual_nero_bridge/config/p5_scene_real.yaml`
  - `src/dual_nero_bridge/dual_nero_bridge/planning_scene_utils.py`
- 已把 `sim_static_demo` 障碍物坐标重新收回到双臂基座附近
- 已把仿真 ros2_control 插件链从 `gz_ros2_control` 切到更适配当前 `ROS 2 Humble + ign gazebo` 的 `ign_ros2_control`

当前还不能宣称这些新改动已验证通过。用户在 Linux 上最近一次观察到：

- `ros2 launch dual_nero_bringup simulation.launch.py` 日志出现：
  - `Failed to load system plugin [libgz_ros2_control-system.so]`
- `ros2 service list | grep controller_manager` 有服务
- `ros2 control list_controllers` 返回：
  - `No controllers are currently loaded!`

因此，新窗口要把这条链视为：

- `P4 基线已验证通过`
- `P5 场景 / 插件切换后的最新代码仍待 Linux 回归确认`

## 当前暂停点

- 当前不再卡在仿真后端
- 当前剩余问题主要是真机部分延期，以及 P5-v1 新改动的 Linux 仿真回归验证

## 下一步

- 先按 `docs/human/phases/p5/README.md` 做 P5-v1
- 同时把 P6 进入条件固定在 `docs/human/phases/p6/README.md`
- 把动态障碍物 / 复杂调度 / 复杂真机验收挂到 `docs/human/phases/p7/README.md` 和 `docs/human/phases/p8/README.md`
- 再等工位与模型对齐恢复 P4-B 真机工作

## 新窗口立即执行的最小验证

1. 重新编译并 source：

```bash
cd ~/wkw_ws/dual_nero_ws_test/dual_nero_ws
colcon build --packages-select dual_nero_bridge dual_nero_bringup dual_nero_moveit_config
source install/setup.bash
```

2. 启动仿真：

```bash
ros2 launch dual_nero_bringup simulation.launch.py
```

3. 先只看仿真日志里这几项：

- `sim_control_hardware_plugin`
- `sim_control_system_plugin`
- `sim_control_system_plugin_name`
- 不应再出现 `Failed to load system plugin`

4. 新终端检查 controller：

```bash
source ~/wkw_ws/dual_nero_ws_test/dual_nero_ws/install/setup.bash
ros2 control list_controllers
```

目标是重新看到：

- `joint_state_broadcaster active`
- `left_arm_controller active`
- `right_arm_controller active`

5. 只有 controller 恢复后，才继续跑：

```bash
ros2 run dual_nero_bridge run_dual_arm_task \
  --task dual_stage_demo \
  --task-config ~/wkw_ws/dual_nero_ws_test/dual_nero_ws/install/dual_nero_bridge/share/dual_nero_bridge/config/p5_tasks.yaml \
  --scene-config ~/wkw_ws/dual_nero_ws_test/dual_nero_ws/install/dual_nero_bridge/share/dual_nero_bridge/config/p5_scene_sim.yaml
```

## 关键文档入口

- 仓库级规则：`/.codex/AGENTS.md`
- 项目状态：[../human/overview/project_status.md](../human/overview/project_status.md)
- 下一步任务：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- 仿真手册：[../human/operations/simulation_runbook.md](../human/operations/simulation_runbook.md)
- P4 定义：[../human/phases/p4/README.md](../human/phases/p4/README.md)
- P5 定义：[../human/phases/p5/README.md](../human/phases/p5/README.md)
