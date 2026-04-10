# dual_nero_bringup

`dual_nero_bringup` 是真机执行的操作员启动入口。

## 阶段说明

- P2 已验收完成
- 当前进入 P3 准备阶段

## 启动入口

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py
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
