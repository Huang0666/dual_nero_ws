# 迁移与恢复手册

## 适用场景

- 新电脑部署
- 环境重建
- 同事交接
- 重启/重插后的现场恢复

## 当前阶段

- P1：完成
- P2：完成并验收
- 当前阶段：P3 入口

参考：

- [p2_acceptance_report.md](p2_acceptance_report.md)

## 依赖前提

- ROS 2 Humble
- Python 3
- `colcon`
- `pyAgxArm`
- Linux SocketCAN
- NERO 双臂与 USB-CAN 设备

## 基础环境

```bash
cd dual_nero_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash
```

## CAN 初始化（1 Mbps）

```bash
sudo ip link set can0 down || true
sudo ip link set can1 down || true
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can1 type can bitrate 1000000
sudo ip link set can0 up
sudo ip link set can1 up
```

说明：

- 动作前必须确认左右臂映射
- USB 重插后先重确认映射再重启 launch
- `gs_usb` 不要依赖 `restart-ms`

## 验证顺序

1. 左臂只读
2. 右臂只读
3. 双臂只读
4. 启动只读并检查 `/joint_states --once`
5. gate 负例（`ALLOW_MOTION_DISABLED`）
6. 动作模式 action/topic 正例与负例

## 单臂测试命令

```bash
python3 src/dual_nero_driver/scripts/test_left_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose

python3 src/dual_nero_driver/scripts/test_right_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

## bridge 启动命令

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=false enable_on_start:=false
```

## action 脚本命令

```bash
python3 src/dual_nero_bridge/scripts/send_left_arm_goal.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --execute

python3 src/dual_nero_bridge/scripts/send_right_arm_goal.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --execute
```

## 成功标准

- 左右臂单测均 `rc=0`
- 启动日志能看到映射与安全状态
- 双臂健康时 `/joint_states` 可读取
- action/topic 的通过与拒绝语义符合预期
