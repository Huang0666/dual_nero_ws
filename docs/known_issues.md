# Known Issues

## 1. `enable()` 不能按一次返回值判失败

- Nero 实机下，`enable()` 可能第一次返回 `False`，后续重试才成功。
- 当前正确做法：
  - 轮询调用 `enable()`
  - 每次读取 `get_joints_enable_status_list()`
  - 以 7 个关节全部 `True` 为成功标准

## 2. `set_normal_mode()` 必须走

- `connect()` 后必须显式调用 `set_normal_mode()`。
- 当前 backend 已按此路径实现。

## 3. 当前最小成功参数集

- 当前实机稳定的 `create_agx_arm_config(...)` 参数集合：
  - `robot="nero"`
  - `comm="can"`
  - `channel`
  - `interface`
  - `bitrate`
- 当前实机验证下，不传：
  - `enable_check_can`
  - `auto_connect`
  - `timeout`

## 4. USB-CAN 映射错位

- `can0` / `can1` 可能因 USB-CAN 枚举和插拔顺序与物理左右臂不一致。
- 现场已出现过“左命令驱右臂 / 右命令驱左臂”。
- 当前要求：
  - 测试前先确认 `channel -> 物理手臂` 映射
  - 中途拔插 USB-CAN 后，重新确认映射
  - 重启 `real_hardware.launch.py`
- 后续建议：
  - 用 `udev` 做固定命名

## 5. 右臂初始位姿超限

- 首次双臂最小动作曾因右臂初始位姿超限失败。
- 当前处理方式：
  - 先失能
  - 手动调整回合法区间
  - 再重新执行测试
- 当前代码已在 `test_dual_arm.py --execute` 前加入预检查。

## 6. test 结束自动失能

- 三个 test 脚本默认都会自动执行：
  - `stop`
  - `disable_all`
  - `close`
- 如果要连续跑 `test + action`：
  - 显式传 `--keep-enabled`

## 7. action 预览 / 执行流程

- 推荐先跑 read-only，再跑双臂最小动作，再跑左右单点 action。
- 如果 action 紧接在 test 后执行，建议测试脚本使用 `--keep-enabled`。

## 8. bridge 当前边界

- 当前 bridge 只支持单点 `FollowJointTrajectory` goal。
- 当前 bridge 不是 native `ros2_control` hardware plugin。
- 当前运行时 safety 仍以 `src/dual_nero_bridge/config/hardware_params.yaml` 为准。
- 当前正式入口已新增统一 preflight；即便绕过 test 脚本，action/topic 入口也会先做执行前检查。

## 9. 现场恢复注意事项

- 如果 USB-CAN 拔插过：
  - 不要直接继续沿用旧映射
  - 重新确认 `can0/can1`
  - 重启真机入口
- 如果当前姿态超限：
  - 不要强行执行动作
  - 先失能并人工调整回合法区间
