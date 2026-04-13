# 迁移与恢复手册

## 适用场景

- 新电脑部署
- 环境重建
- 同事交接
- 重启后的标准启动

说明：

- 现场故障处置以 [../phases/p3/recovery_sop.md](../phases/p3/recovery_sop.md) 为准
- 本文档偏环境准备、标准启动和迁移交接

## 当前阶段

- P1：完成
- P2：完成并验收
- 当前阶段：P3 入口

参考：

- [../phases/p2/acceptance_report.md](../phases/p2/acceptance_report.md)

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

## 标准启动顺序

1. 左臂只读
2. 右臂只读
3. 双臂只读
4. 启动只读并检查 `/joint_states --once`
5. gate 负例（`ALLOW_MOTION_DISABLED`）
6. 动作模式 action/topic 正例与负例

## 故障恢复入口

如遇以下问题，不要继续在本文档里临时排障，直接跳到 SOP：

- `BUS-OFF / STOPPED`
- `/joint_states --once` 阻塞
- 单臂掉线导致 degraded
- 左右臂映射疑似错位

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

说明：

- launch 启动后要保持运行
- 后续 `ros2 run dual_nero_bridge ...` 命令必须从另一个终端执行

## action 脚本命令

```bash
ros2 run dual_nero_bridge send_left_arm_goal \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --execute

ros2 run dual_nero_bridge send_right_arm_goal \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --execute
```

## P4 双臂任务入口

```bash
ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync
```

说明：

- 需要在动作模式下执行
- 任务配置文件在 `src/dual_nero_bridge/config/p4_tasks.yaml`

如果要直接回固定初始/安全位：

```bash
ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync --target safe
```

## 成功标准

- 左右臂单测均 `rc=0`
- 启动日志能看到映射与安全状态
- 双臂健康时 `/joint_states` 可读取
- action/topic 的通过与拒绝语义符合预期
