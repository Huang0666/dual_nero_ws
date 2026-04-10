# dual_nero_bridge

`dual_nero_bridge` 是双臂 NERO 的真机执行桥。

## 阶段说明

- P2 preflight 稳定化已验收完成
- 当前进入 P3（映射稳定化 + 正式执行验证）

## 主要职责

- 对接 `dual_nero_driver` 的运行时桥接
- 发布 `/joint_states`
- 提供 topic/action 正式执行入口

## 统一 preflight

`preflight.py` 是正式入口唯一运行时 gate。

当前检查项包括：

- `allow_motion`
- arm online/enabled
- 状态可读性与新鲜度
- 当前姿态越限/近限位
- 起点偏差
- joint set 与命令结构合法性

## 错误码

集中定义于：

- `dual_nero_bridge/preflight_codes.py`

action/topic 路径统一使用：

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
