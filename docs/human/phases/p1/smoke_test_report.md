# P1 Smoke Test Report

## 结论

P1 实机验证已通过。

已通过项：

- 左臂单臂 read-only 成功
- 右臂单臂 read-only 成功
- 双臂只读成功
- `/joint_states` 14 joints 正常
- 双臂最小动作成功
- 左臂单点 action 成功
- 右臂单点 action 成功

## 当前实机稳定参数

当前 Nero 实机连接采用最小 `create_agx_arm_config(...)` 参数集合：

- `robot="nero"`
- `comm="can"`
- `channel`
- `interface`
- `bitrate`

当前不传：

- `enable_check_can`
- `auto_connect`
- `timeout`

补充说明：

- `set_normal_mode()` 必须走
- `enable()` 需要轮询重试
- 扩展参数后续再逐项回归验证

## 已确认现场问题与处理

### 1. 右臂初始位姿超限

- 首次双臂最小动作失败，根因是右臂初始位姿超出当前配置限位。
- 处理方式：
  - 先失能
  - 手动调整到合法区间
  - 重新执行测试
- 复测后双臂最小动作成功。

### 2. USB-CAN 映射错位

- USB-CAN 枚举/插拔顺序可能导致 `can0` / `can1` 与物理左右臂不一致。
- 现场已确认出现过左右臂映射错位。
- 当前处理方式：
  - 先确认 `channel -> 物理手臂` 映射
  - 再执行 read-only、最小动作和 action 测试
- 后续建议：
  - 使用 `udev` 做固定命名
- 如果中途拔插 USB-CAN：
  - 重新确认映射
  - 重启 `real_hardware.launch.py`
  - 再继续测试

## 前置条件

- `pyAgxArm` 已安装
- CAN 设备已正确激活
- 硬件参数文件已准备：
  - `src/dual_nero_bridge/config/hardware_params.yaml`
- 操作者已确认机械臂周边环境安全

## 推荐测试顺序

### 1. 左臂 read-only

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_left_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 2. 右臂 read-only

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_right_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 3. 双臂 read-only

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_dual_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 4. `/joint_states` 检查

```bash
ros2 topic echo /joint_states
```

检查项：

- joint 数量为 14
- joint 顺序为 `left_joint1..7` + `right_joint1..7`

### 5. 双臂最小动作

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_dual_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --execute \
  --wait \
  --delta 0.03 \
  --verbose
```

连续测试建议：

- 如果后面紧接着要跑 action，建议这里加 `--keep-enabled`

### 6. 左臂 action

```bash
python src/dual_nero_bridge/scripts/send_left_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml --execute
```

### 7. 右臂 action

```bash
python src/dual_nero_bridge/scripts/send_right_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml --execute
```

## 收尾说明

- 三个 test 脚本默认执行安全收尾：
  - `stop`
  - `disable_all`
  - `close`
- 如果需要连续进行 `test + action`，推荐显式传 `--keep-enabled`
- `--keep-enabled` 模式下不会自动 `disable_all`
- verbose 下会打印：
  - `cleanup mode: auto-disable`
  - 或 `cleanup mode: keep-enabled`

## 已知限制

- 当前运行时 safety 仍以 `src/dual_nero_bridge/config/hardware_params.yaml` 为准
- bridge 当前只支持单点 `FollowJointTrajectory` goal
- bridge 不是 native `ros2_control` hardware plugin
- 当前仍依赖人工确认 USB-CAN 映射关系
