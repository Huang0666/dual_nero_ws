# P1 Execution Report

## 结论

P1 已完成并通过当前实机验证。

已完成项：

- 左臂单臂 read-only 成功
- 右臂单臂 read-only 成功
- 双臂只读成功
- `/joint_states` 14 joints 正常
- 双臂最小动作成功
- 左臂单点 action 成功
- 右臂单点 action 成功
- 双臂动作一致

## 当前方案定位

- 当前采用：**B 方案，real-hardware bridge**
- 当前不是 native C++ `ros2_control` hardware plugin
- 当前推荐路线：
  - 沿 bridge 方案继续做稳定化和工程化
- 当前不建议立即切到 native plugin，原因是：
  - 现有 bridge 已完成 P1 真机最小执行链
  - 当前主要风险在稳定性、恢复、固定命名和日志，不在架构缺口
  - 现在切架构会打断验证连续性，性价比低

## 当前实机稳定配置

当前实机稳定的 `create_agx_arm_config(...)` 参数集为：

- `robot="nero"`
- `comm="can"`
- `channel`
- `interface`
- `bitrate`

当前暂不传：

- `enable_check_can`
- `auto_connect`
- `timeout`

已确认的运行时行为：

- `connect()` 后必须显式调用 `set_normal_mode()`
- `enable()` 需要轮询重试
- `enable_all()` 以 7 个关节全部 enabled 为成功标准

## 已确认问题与处理

### 1. 右臂初始位姿超限

- 首次双臂最小动作失败，根因是右臂初始位姿超出当前配置限位。
- 当前处理方式：
  - 先失能
  - 手动调回合法区间
  - 再重新执行测试
- 当前状态：
  - 已通过 limits 收口与执行前检查降低复发概率

### 2. USB-CAN 映射错位

- 现场已确认出现过左右臂映射错位。
- 根因是 USB-CAN 枚举/插拔顺序导致 `can0` / `can1` 与物理左右臂不一致。
- 当前处理方式：
  - 测试前先确认映射
  - 再运行 read-only、最小动作和 action
- 当前建议：
  - 后续为左右臂设备增加固定命名，例如 `udev`
- 额外要求：
  - 如果中途拔插 USB-CAN，需重启 `real_hardware.launch.py`

## P1 Final Cleanup 收口结果

### 1. 测试脚本 cleanup 行为统一

以下脚本已统一支持 `--keep-enabled`：

- `src/dual_nero_driver/scripts/test_left_arm.py`
- `src/dual_nero_driver/scripts/test_right_arm.py`
- `src/dual_nero_driver/scripts/test_dual_arm.py`

默认行为：

- `stop`
- `disable_all`
- `close`

`--keep-enabled` 行为：

- 仍执行 `stop`
- 不自动 `disable_all`
- 不主动把机械臂切回失能
- 适合连续执行 `test + action`

verbose 输出会明确打印：

- `cleanup mode: auto-disable`
- `cleanup mode: keep-enabled`

### 2. limits 与执行前检查已收口

- `hardware_params.yaml` 仍是运行时 safety 实际读取的 limits 来源
- `joint_limits.yaml` 已显式补齐 position limits
- `test_dual_arm.py --execute` 会在动作前检查当前姿态是否超限或接近限位

## 当前已完成项清单

- `dual_nero_driver` 已具备稳定的 Nero Python backend 第一版
- `dual_nero_bridge` 已具备真实 joint state、单点 action 和最小执行桥
- `dual_nero_bringup` 已具备真机启动入口
- P1 所需读状态、最小动作、左右单点 action 均已跑通
- 当前最小成功参数集、现场问题和 cleanup 行为已文档化

## 当前仍未完成

- native `ros2_control` C++ hardware plugin
- 真正的 `controller_manager` / `joint_state_broadcaster` 真机链
- 多点 trajectory 与严格时间控制
- diagnostics / calibration / fault recovery
- 固定 USB-CAN 命名与自动映射校验
- 更完整的急停闭环与通信异常恢复

## 下一阶段建议

1. 完成 USB-CAN 固定命名，例如 `udev`
2. 把当前姿态/限位检查前置到正式入口
3. 增强 bridge/action 日志、fault、reconnect 和 recovery 策略
4. 做重复性 smoke test，确认可复现性
