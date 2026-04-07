# P2 Preflight 设计说明

## 目标

把当前 P1 已打通的真机执行链推进到“正式入口统一受控、启动期配置可校验、执行前规则统一、日志可诊断”的状态。

## 范围

- 当前仍沿 bridge 路线实现
- 不切 native `ros2_control` hardware plugin
- 不实现 USB-CAN 固定命名
- 不做多点轨迹时间控制重构
- 不引入大型状态机框架

## 三层职责

### 1. bringup / launch 层

负责：

- 启动期配置和路径校验
- 左右臂 channel 参数存在性校验
- MoveIt-vs-bridge 关节限位一致性校验
- 打印当前映射和 `preflight_enabled` / `preflight_config_path` / `safety_mode`

不负责：

- 运行时姿态判断
- 运行时动作拦截
- 最终 reject / abort 判定

### 2. bridge 执行层

负责：

- 接收 action / topic 请求
- 在真正下发前调用统一 preflight
- 根据 preflight 结果决定 accept / reject / abort / execute
- 打印统一日志

### 3. preflight 模块

负责：

- 统一规则
- 统一结果结构
- 统一错误码
- 统一错误文案

## 运行时 preflight gate

统一检查顺序：

1. `enabled`
2. `allow_motion`
3. 目标结构合法性
4. arm online / enabled
5. 当前状态可读且未过旧
6. 当前姿态越限
7. 当前姿态接近限位
8. 当前状态到目标首点偏差过大

`enabled=false` 时，只跳过上述运行时 gate，不影响启动期校验。

## 启动期校验

启动期校验始终执行，不受 `preflight_enabled` 影响：

- `hardware_config` 文件存在
- `preflight_config_path` 文件存在
- 左右臂 `can.channel` 存在
- `preflight.moveit_joint_limits_path` 存在
- bridge `hardware_params.yaml` 与 MoveIt `joint_limits.yaml` 的关节软限位完全一致

说明：

- `preflight.moveit_joint_limits_path` 允许作为 override
- 若未配置，则 bringup 默认解析 `dual_nero_moveit_config/config/joint_limits.yaml`

## 正式执行入口

当前已接入统一 preflight 的正式执行入口：

- `/left_arm_controller/follow_joint_trajectory`
- `/right_arm_controller/follow_joint_trajectory`
- `/left_arm_controller/joint_command`
- `/right_arm_controller/joint_command`
- `/dual_arms/joint_command`

## 错误码

错误码集中定义在 `dual_nero_bridge/preflight_codes.py`。

当前统一错误码：

- `ALLOW_MOTION_DISABLED`
- `ARM_OFFLINE`
- `ARM_NOT_ENABLED`
- `CURRENT_POSE_OUT_OF_LIMIT`
- `CURRENT_POSE_NEAR_LIMIT`
- `INVALID_GOAL_STRUCTURE`
- `INVALID_JOINT_SET`
- `STATE_UNAVAILABLE`
- `STATE_TOO_OLD`
- `START_DEVIATION_TOO_LARGE`

action / topic 路径不得各自硬编码不同错误码字符串。

## 限位来源策略

- runtime 与运行时 preflight 继续使用 bridge 当前生效限位
- 不新增第三份 joint limits 真值
- MoveIt `joint_limits.yaml` 只作为启动前强一致检查来源

## operator 关注点

- 启动后先确认日志中的左右臂 channel 映射
- 中途拔插 USB-CAN 后重新确认映射，并重启 `real_hardware.launch.py`
- `preflight_enabled=false` 只表示关闭运行时 gate，不表示系统不再做启动期安全校验
