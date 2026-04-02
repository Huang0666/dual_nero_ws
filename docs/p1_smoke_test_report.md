# P1 Smoke Test Report

## 测试目标

本模板用于 P1.1 阶段的真机冒烟验证，目标是：

- 验证左臂 read-only 连接与状态回读
- 验证右臂 read-only 连接与状态回读
- 验证双臂 read-only 连接与状态回读
- 验证双臂最小动作测试流程
- 验证 bridge 的 action/topic 入口是否达到当前语义合同

## 前置条件

- `pyAgxArm` 已安装
- CAN 设备已激活
- 硬件参数文件已准备：
  - `src/dual_nero_bridge/config/hardware_params.yaml`
- 当前实机验证下，Nero 连接采用最小 `create_agx_arm_config(...)` 参数集合；扩展参数后续再逐项回归验证
- 操作者确认当前机械臂周围环境安全
- 最小动作测试前确认：
  - `allow_motion:=true`
  - `enable_on_start:=true`

## 启动命令

### Read-only bridge 启动

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=false enable_on_start:=false
```

### 动作测试 bridge 启动

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=true enable_on_start:=true
```

## Read-only 测试步骤

### 1. 左臂 read-only check

```bash
python src/dual_nero_driver/scripts/test_left_arm.py --config src/dual_nero_bridge/config/hardware_params.yaml
```

### 2. 右臂 read-only check

```bash
python src/dual_nero_driver/scripts/test_right_arm.py --config src/dual_nero_bridge/config/hardware_params.yaml
```

### 3. 双臂 read-only check

```bash
python src/dual_nero_driver/scripts/test_dual_arm.py --config src/dual_nero_bridge/config/hardware_params.yaml
```

### 4. bridge joint state check

```bash
ros2 topic echo /joint_states
```

检查项：

- `/joint_states` 是否包含 14 joints
- joint 顺序是否为 `left_joint1..7` + `right_joint1..7`
- velocity 若为空，是否有明确日志说明

## Motion 测试步骤

### 1. 双臂最小动作测试

```bash
python src/dual_nero_driver/scripts/test_dual_arm.py --config src/dual_nero_bridge/config/hardware_params.yaml --execute --wait --delta 0.03
```

### 2. 左臂 action 示例

预览：

```bash
python src/dual_nero_bridge/scripts/send_left_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml
```

执行：

```bash
python src/dual_nero_bridge/scripts/send_left_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml --execute
```

### 3. 右臂 action 示例

预览：

```bash
python src/dual_nero_bridge/scripts/send_right_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml
```

执行：

```bash
python src/dual_nero_bridge/scripts/send_right_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml --execute
```

## 安全提示

- 所有动作默认必须由显式 `--execute` 触发
- 不要在未知姿态下直接发送自定义大幅目标
- `allow_motion=false` 时收到动作拒绝属于预期行为
- `enable_on_start=false` 时动作拒绝属于预期行为
- 当前 bridge 不支持多点 trajectory；示例只发送单点 goal

## 结果记录模板

| 项目 | 命令 | 结果 | 备注 |
|---|---|---|---|
| 左臂 read-only | `test_left_arm.py` | 待填写 | |
| 右臂 read-only | `test_right_arm.py` | 待填写 | |
| 双臂 read-only | `test_dual_arm.py` | 待填写 | |
| `/joint_states` 合同检查 | `ros2 topic echo /joint_states` | 待填写 | |
| 双臂最小动作测试 | `test_dual_arm.py --execute` | 待填写 | |
| 左臂 action 测试 | `send_left_arm_goal.py --execute` | 待填写 | |
| 右臂 action 测试 | `send_right_arm_goal.py --execute` | 待填写 | |

## 已知限制

- 当前无法在文档中替代真实硬件验证结果，本模板需要现场实填
- bridge 当前只支持单点 `FollowJointTrajectory` goal
- `time_from_start` 当前只做合法性检查，不做多点时间控制
- bridge 不是 native `ros2_control` hardware plugin
