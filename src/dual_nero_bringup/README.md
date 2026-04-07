# dual_nero_bringup

`dual_nero_bringup` 是 `real_hardware_execution` 的 operator-facing 启动入口。

## 入口

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py
```

## 启动职责

bringup / launch 层只负责：

- 解析并注入正式启动参数
- 校验配置文件和关键路径存在
- 校验左右臂 channel 参数存在
- 校验 bridge 与 MoveIt 的关节软限位完全一致
- 打印当前 channel 映射和 safety/preflight 状态

bringup / launch 层不负责：

- 运行时姿态判断
- 运行时动作拦截
- 最终 reject / abort 决策

## 正式启动参数

- `hardware_config`
- `allow_motion`
- `enable_on_start`
- `publish_rate_hz`
- `preflight_enabled`
- `preflight_config_path`
- `safety_mode`
- `with_moveit`
- `with_rviz`

## `preflight_enabled` 语义

- `true`：启用运行时 preflight gate
- `false`：仅关闭运行时 preflight gate

注意：

- `preflight_enabled` 不会关闭启动期校验
- 即使 `preflight_enabled:=false`，以下检查仍然必须通过：
  - 配置文件路径存在
  - 左右臂 `can.channel` 存在
  - 默认或 override 的 MoveIt joint limits 路径存在
  - bridge 与 MoveIt 关节限位一致

## 启动日志

启动成功后，日志必须至少出现：

```text
[bringup] left_arm channel -> can0
[bringup] right_arm channel -> can1
[bringup] preflight_enabled -> true
[bringup] preflight_config_path -> /.../preflight.yaml
[bringup] safety_mode -> strict
```

用法：

- 用 `left_arm channel` / `right_arm channel` 确认当前 USB-CAN 映射
- 用 `preflight_enabled` 确认运行时 gate 是否开启
- 用 `preflight_config_path` 确认当前使用的 preflight 配置
- 用 `safety_mode` 确认当前安全模式标签

## 常见启动失败语义

- `hardware_config does not exist`
  - `hardware_config` 路径错误
- `preflight_config_path does not exist`
  - `preflight_config_path` 路径错误
- `left_arm.can.channel is missing`
  - bridge 硬件配置缺少左臂 channel
- `right_arm.can.channel is missing`
  - bridge 硬件配置缺少右臂 channel
- `preflight.moveit_joint_limits_path does not exist`
  - preflight 配置中的 override 路径不存在，或默认的 `dual_nero_moveit_config/config/joint_limits.yaml` 不存在
- `Bridge and MoveIt joint limits differ`
  - bridge 配置与 MoveIt 配置中的软限位不一致，必须先修正再启动

## 推荐启动方式

### Read-only

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=false enable_on_start:=false
```

### 动作测试

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=true enable_on_start:=true
```

### 关闭运行时 preflight gate

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py \
  allow_motion:=true \
  enable_on_start:=true \
  preflight_enabled:=false
```

这不会绕过启动期校验。
