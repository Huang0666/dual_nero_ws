# P1 Smoke Test Report

## 测试目标

本模板用于 P1.3 阶段的真机冒烟验证，目标是：

- 验证左臂 read-only 连接与状态回读
- 验证右臂 read-only 连接与状态回读
- 验证双臂 read-only 连接与状态回读
- 验证双臂最小动作测试
- 验证执行前限位预检查是否能提前发现“当前真实姿态已超限”的问题

## 前置条件

- `pyAgxArm` 已安装
- CAN 设备已正确激活
- 硬件参数文件已准备：
  - `src/dual_nero_bridge/config/hardware_params.yaml`
- 当前实机验证下，Nero 连接采用最小 `create_agx_arm_config(...)` 参数集合：
  - `robot="nero"`
  - `comm="can"`
  - `channel`
  - `interface`
  - `bitrate`
- `enable_check_can`、`auto_connect`、`timeout` 暂不传入 `create_agx_arm_config(...)`
- 扩展参数后续再逐项回归验证
- 操作者已确认机械臂周边环境安全

## 已确认的实机结论

- 左臂 read-only 已成功
- 右臂 read-only 已进入可验证阶段
- 双臂最小动作测试已成功
- 首次双臂动作失败的原因已确认：
  - 右臂初始位姿超出当前配置限位
- 失能后手动将机械臂调整回合法区间，再次执行后：
  - 双臂最小动作成功
  - 机械臂发生微弱移动

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
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_left_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 2. 右臂 read-only check

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_right_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 3. 双臂 read-only check

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_dual_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml
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
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_dual_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --execute \
  --wait \
  --delta 0.03
```

执行前脚本会自动：

- 打印当前左右臂 joint positions
- 检查是否有 joint 已超限
- 检查是否有 joint 接近限位

如果发现当前姿态已超限，脚本会直接失败并提示：

- 哪个 joint 超限
- 当前值
- 下限
- 上限
- 先失能并手动调整回合法区间，再重新执行测试

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
- 如果执行前提示当前姿态超限：
  - 先失能
  - 手动调整到合法区间
  - 再重新执行最小动作测试

## 结果记录模板

| 项目 | 命令 | 结果 | 备注 |
|---|---|---|---|
| 左臂 read-only | `test_left_arm.py` | 已成功 | 最小参数集连接成功 |
| 右臂 read-only | `test_right_arm.py` | 待填写 | |
| 双臂 read-only | `test_dual_arm.py` | 待填写 | |
| `/joint_states` 合同检查 | `ros2 topic echo /joint_states` | 待填写 | |
| 双臂最小动作测试 | `test_dual_arm.py --execute` | 已成功 | 首次因 `right_joint2` 初始位姿超限失败，手动调整后复测成功 |
| 左臂 action 测试 | `send_left_arm_goal.py --execute` | 待填写 | |
| 右臂 action 测试 | `send_right_arm_goal.py --execute` | 待填写 | |

## 已知限制

- 当前 `test_dual_arm.py --execute` 的限位预检查读取的是 `src/dual_nero_bridge/config/hardware_params.yaml`
- `src/dual_nero_moveit_config/config/joint_limits.yaml` 已补齐为与 URDF/bridge 一致的显式 position limits，但运行时 safety 仍以 `hardware_params.yaml` 为准
- bridge 当前只支持单点 `FollowJointTrajectory` goal
- `time_from_start` 当前只做合法性检查，不做多点时间控制
- bridge 不是 native `ros2_control` hardware plugin
