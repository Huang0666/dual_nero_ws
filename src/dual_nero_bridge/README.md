# dual_nero_bridge

`dual_nero_bridge` 是 `dual_nero_ws` 当前的第一版真机执行桥。

## 作用

- 复用 `dual_nero_driver` 作为唯一 `pyAgxArm` 后端接入层
- 发布 14 关节固定顺序的真实 `/joint_states`
- 提供：
  - `/left_arm_controller/joint_command`
  - `/right_arm_controller/joint_command`
  - `/dual_arms/joint_command`
- 提供：
  - `/left_arm_controller/follow_joint_trajectory`
  - `/right_arm_controller/follow_joint_trajectory`

## P1.1 收口内容

- 修复 `FollowJointTrajectory` 语义，当前采用 **方案 A**
  - 每个 goal 仅支持 1 个 trajectory point
  - 多点 goal 在 `goal_callback` 阶段直接拒绝
  - joint names、point 维度、空 goal、可选字段维度、`time_from_start` 合法性都会显式检查
- 明确 bridge 失败语义
  - 两臂都不可用：节点启动失败并退出
  - 单臂不可用：节点进入 degraded mode
  - 单臂命令只允许打到可用臂
  - 双臂命令要求两臂都可用且都 enabled
  - `allow_motion=false`：所有动作和命令入口显式拒绝
  - `enable_on_start=false`：bridge 不做 lazy enable，执行命令显式拒绝
- 补充 action 客户端示例：
  - [scripts/send_left_arm_goal.py](scripts/send_left_arm_goal.py)
  - [scripts/send_right_arm_goal.py](scripts/send_right_arm_goal.py)

## 当前 `FollowJointTrajectory` 语义

- 支持程度：**单点 point-to-point goal**
- 不支持：多点 trajectory 的顺序执行
- 不支持：基于 `time_from_start` 的多点时间控制
- 对单点 goal：
  - `time_from_start` 仅做合法性检查
  - 真正执行仍由 `move_j(..., wait=True)` 完成

## 失败语义约定

- 日志前缀约定：
  - `[STATE][source] ...`
  - `[REJECT][source] ...`
  - `[ABORT][source] ...`
  - `[DEGRADED][source] ...`
  - `[FATAL][source] ...`
- `/joint_states`
  - 只有在两臂都可用时才发布完整 14-joint 合同
  - 单臂缺失时不发布“半截 joint_states”，而是进入 degraded 日志
- topic/action
  - 单臂不可用时，该臂命令拒绝
  - 双臂只要有一臂不可用，`dual_arms` 命令拒绝

## 运行前提

- `pyAgxArm` 必须安装
- CAN 设备必须先激活
- [config/hardware_params.yaml](config/hardware_params.yaml) 默认是 `dry_run: false`
- 真实动作需显式启动：
  - `allow_motion:=true`
  - `enable_on_start:=true`

## 常用命令

- 静态合同检查：
  - `ros2 run dual_nero_bridge contract_check`
- 仅启动 bridge：
  - `ros2 launch dual_nero_bridge real_hardware_bridge.launch.py`
- 左臂 action 预览：
  - `python src/dual_nero_bridge/scripts/send_left_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml`
- 右臂 action 预览：
  - `python src/dual_nero_bridge/scripts/send_right_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml`

## 当前限制

- 没有 native `ros2_control` hardware plugin
- 没有真正的 controller manager 真机链
- `FollowJointTrajectory` 仅支持单点 goal
- 不实现严格实时轨迹控制
- 不实现 lazy enable / 故障恢复 / 校准
