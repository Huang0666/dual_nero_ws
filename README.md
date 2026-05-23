# dual_nero_ws

`dual_nero_ws` 是 NERO 双臂机器人 ROS 2 工作区。

## 目录结构

- `src/dual_nero_description`：模型显示
- `src/dual_nero_moveit_config`：规划演示
- `src/dual_nero_driver` + `src/dual_nero_bridge` + `src/dual_nero_bringup`：真机执行
- `docs/`：项目级文档正文、规则、上下文

## 当前状态

- P1：已完成
- P2：已完成并通过现场验收
- 当前执行架构：bridge（未切 native `ros2_control` 上层合同）
- 当前阶段：P5-Sim 第一版收口验收阶段
- 当前后续开发主线：Gazebo / gz sim 仿真
- 当前仿真执行链：`controller_manager` / `/joint_states` / `FollowJointTrajectory` / `dual_prep_sync` / RViz `Plan & Execute` 已验证可用

## 文档入口

- 给人看：[docs/human/README.md](docs/human/README.md)
- 给 agent 看：[docs/agent/README.md](docs/agent/README.md)
- 文档总入口：[docs/README.md](docs/README.md)

## 文档布局规则

- 仓库根目录只保留本文件作为项目级 Markdown 入口
- 其余项目级文档统一放在 `docs/`
- 提交前可运行 `python tools/check_docs_layout.py` 做快速检查

## 真机入口

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py
```

## 仿真入口

```bash
ros2 launch dual_nero_bringup simulation.launch.py
```

## 标准任务入口（P4 基线任务）

```bash
ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync
```
