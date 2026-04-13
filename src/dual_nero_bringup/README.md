# dual_nero_bringup

`dual_nero_bringup` 是操作员启动入口，当前同时承载真机与仿真主线。

## 阶段说明

- P2 已验收完成
- 当前进入 P3：
  - P3-A：故障恢复 SOP 标准化
  - P3-B：MoveIt 执行链系统化验证
  - P3-C：USB-CAN 固定命名（暂缓）

P3 当前正式文档：

- [../../docs/human/phases/p3/recovery_sop.md](../../docs/human/phases/p3/recovery_sop.md)
- [../../docs/human/phases/p3/moveit_validation_plan.md](../../docs/human/phases/p3/moveit_validation_plan.md)

## 启动入口

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py
```

```bash
ros2 launch dual_nero_bringup simulation.launch.py
```

## 职责边界

launch 层负责：

- 启动参数注入
- 启动期文件/路径检查
- 左右臂 channel 参数检查
- bridge 与 MoveIt 关节限位一致性检查
- 映射与安全状态日志输出

launch 层不负责：

- 运行时动作决策
- 运行时 reject/abort 语义判定

当前分工：

- `real_hardware.launch.py`：真机主线
- `simulation.launch.py`：gz sim 仿真主线

## 关键参数

- `allow_motion`
- `enable_on_start`
- `preflight_enabled`
- `preflight_config_path`
- `safety_mode`

## `preflight_enabled` 语义

- `true`：运行时 preflight gate 开启
- `false`：运行时 preflight gate 关闭
- 启动期检查始终执行，不受该参数影响

## 当前 P3-A 约束

- 现场恢复优先按 SOP 走，不在 bringup 文档里复制第二套故障处置步骤
- 继续保持 bridge 路线，不切 native plugin

## P3-B 当前使用方式

- `real_hardware.launch.py` 默认会带起 `move_group`
- 现场验证时优先使用：

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm
```
