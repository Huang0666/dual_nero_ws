# Migration Runbook

## 适用场景

- 换新电脑继续工作
- 新环境从 0 恢复
- 新同事接手
- 现场隔天重建运行环境

## 当前项目阶段

- 当前项目已完成 P1 真机最小执行链
- 当前真实执行方案是 bridge
- 当前下一阶段是 P2 稳定化与工程化

## 环境依赖清单

- ROS 2 Humble
- Python 3
- `colcon`
- `pyAgxArm`
- Linux SocketCAN 环境
- NERO 双臂真机硬件
- USB-CAN 设备

## 仓库初始化步骤

1. 获取仓库并进入工作区根目录
2. 安装 Python 依赖与 `pyAgxArm`
3. 准备 ROS 2 环境
4. 确认 `src/dual_nero_bridge/config/hardware_params.yaml` 中的 `channel`、`interface`、`bitrate`
5. 构建工作区

参考：

```bash
cd dual_nero_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

## USB-CAN 与硬件准备说明

- 当前仓库仍使用 `can0/can1` 临时方案
- USB-CAN 枚举顺序可能导致左右臂映射错位
- 在开始任何动作前，先确认：
  - `can0` 当前对应哪一侧物理手臂
  - `can1` 当前对应哪一侧物理手臂
- 如果中途拔插 USB-CAN：
  - 重新确认映射
  - 重启 `real_hardware.launch.py`
- 当前 `real_hardware.launch.py` 启动后会打印：
  - 左右臂 channel 映射
  - `preflight_enabled`
  - `preflight_config_path`
  - `safety_mode`

## CAN 初始化命令

按当前 1 Mbps 配置准备：

```bash
sudo ip link set can0 down || true
sudo ip link set can1 down || true
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can1 type can bitrate 1000000
sudo ip link set can0 up
sudo ip link set can1 up
```

如果后续切到固定命名，需把命令中的设备名一并更新。

## 首次恢复后的验证顺序

### 1. 左臂单臂 read-only

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_left_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 2. 右臂单臂 read-only

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_right_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 3. 双臂只读

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_dual_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 4. 双臂最小动作

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_dual_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --execute \
  --wait \
  --delta 0.03 \
  --verbose
```

### 5. 左右 action

```bash
python src/dual_nero_bridge/scripts/send_left_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml --execute
python src/dual_nero_bridge/scripts/send_right_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml --execute
```

## 已知问题与注意事项

- `set_normal_mode()` 必须走
- `enable()` 需要轮询重试
- 当前实机稳定参数集是最小 `create_agx_arm_config(...)` 参数集合
- 右臂初始位姿曾超限，执行前要确认当前姿态处于合法区间
- 三个 test 脚本默认都会自动失能；若要连续执行 test + action，请加 `--keep-enabled`

## 迁移成功标准

- 左臂 read-only 成功
- 右臂 read-only 成功
- 双臂只读成功
- `/joint_states` 14 joints 正常
- 双臂最小动作成功
- 左右 action 都成功
