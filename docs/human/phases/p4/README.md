# P4 文档

## 作用

定义从“已验证执行链”进入“真实物理任务”的第一阶段目标，并记录当前 P4 的实际落地状态。

## 当前阶段定义

P4 当前正式定义为：

- 无视觉
- 低风险
- 固定工位
- 双臂固定场景任务闭环

## 当前已经完成的内容

- 已新增正式任务 CLI：`run_dual_arm_task`
- 已新增任务配置文件：`src/dual_nero_bridge/config/p4_tasks.yaml`
- 已建立 P4 正式执行路径：
  - 读取当前 `/joint_states`
  - 用 `dual_arms` 做统一规划
  - 提取统一轨迹末点
  - 分裂成左右臂单点 `FollowJointTrajectory` goal
  - 以任务级同步方式下发
- 已支持通过正式入口直接回固定安全位：
  - `ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync --target safe`
- 已修正执行等待与 cleanup 的主要工程问题
- 已验证仿真后端主线：
  - `simulation.launch.py` 可稳定启动 server-only `gz sim`
  - `controller_manager`、`joint_state_broadcaster`、左右臂 controller 可激活
  - `dual_prep_sync` 可在仿真中完整执行 prep / return

## 当前没有完成的内容

当前 P4 卡住的不是底层链路，而是现场任务空间与点位定义。

具体表现为：

- 仿真链路已经可用
- 但当前预备位 / 返回位与现场真实摆放空间仍存在冲突
- 继续盲试只会增加试错成本，不会沉淀为正式任务

## 当前阶段结论

P4 到目前为止，已经完成了两件关键事情：

- 正式任务入口已经建立
- 仿真后端已经跑通，不再卡在“控制器链是否可用”

所以当前下一步不是继续打底层，而是收口启动噪声并进入点位 / 空间建模。

阶段完成判断入口：

- [completion_checklist.md](completion_checklist.md)

## 当前正式任务入口

完整任务：

```bash
ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync
```

只回固定初始 / 安全位：

```bash
ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync --target safe
```

仿真主线入口：

- [../../operations/simulation_runbook.md](../../operations/simulation_runbook.md)
