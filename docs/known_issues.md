# 已知问题

## 1）`enable()` 首次可能失败

- 真机下 `enable()` 可能第一次返回 `False`。
- 正确处理方式是重试并轮询状态，直到 7 个关节全部使能。

## 2）`set_normal_mode()` 必须调用

- `connect()` 后必须走 `set_normal_mode()`。

## 3）USB-CAN 映射漂移（`can0/can1`）

- USB 重插/重枚举后，左右臂可能与 `can0/can1` 对应错位。
- 动作前必须确认映射关系。

## 4）`can1 BUS-OFF/STOPPED` 会导致右臂不可用

已观察现象：

- 右臂 `enable_all` 一直失败
- 右臂单测 `rc=1`
- `/joint_states --once` 在 degraded 下阻塞

现场根因（已复现）：

- 右臂 CAN 物理线缆断开/接触异常

## 5）`gs_usb` 不支持 `restart-ms`

已观察报错：

- `Error: Device doesn't support restart from Bus Off.`

建议：

- 使用 `down/type/up` 显式重置，不依赖 `restart-ms`

## 6）测试脚本默认会自动失能

- `test_left_arm.py`、`test_right_arm.py`、`test_dual_arm.py` 默认会安全收尾。
- 连续 test + action 场景才使用 `--keep-enabled`。

## 7）当前 bridge 边界

- 仅支持单点 `FollowJointTrajectory`
- 仍是 bridge 方案，不是 native plugin
- action/topic 正式入口已经接入统一 preflight
