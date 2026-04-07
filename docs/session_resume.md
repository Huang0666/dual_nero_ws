# 今日恢复卡片

## 先看这三条

- 当前阶段：`P2 稳定化与工程化`
- 当前真实执行方案：**bridge**
- 如果中途拔插过 USB-CAN：先重启 `real_hardware.launch.py`
- 当前正式入口已接入 preflight

## 今日开始前检查

1. 确认 `can0/can1` 与物理左右臂映射
2. 确认 CAN 已初始化
3. 确认 `src/dual_nero_bridge/config/hardware_params.yaml` 没被误改
4. 确认当前机械臂姿态处于合法区间

## Quick Resume Checklist

1. 进入仓库根目录
2. source ROS 2 环境
3. 初始化 CAN
4. 确认 USB-CAN 映射
5. 跑左臂 read-only
6. 跑右臂 read-only
7. 跑双臂 read-only
8. 看 `/joint_states`
9. 跑双臂最小动作
10. 跑左右单点 action

## 恢复执行顺序

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

### 5. 双臂最小动作

```bash
PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_dual_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --execute \
  --wait \
  --delta 0.03 \
  --verbose \
  --keep-enabled
```

### 6. 左右单点 action

```bash
python src/dual_nero_bridge/scripts/send_left_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml --execute
python src/dual_nero_bridge/scripts/send_right_arm_goal.py --config src/dual_nero_bridge/config/hardware_params.yaml --execute
```

## 常用命令

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash

sudo ip link set can0 down || true
sudo ip link set can1 down || true
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can1 type can bitrate 1000000
sudo ip link set can0 up
sudo ip link set can1 up
```

## 今天如果出问题先看哪里

- 映射问题：看 [known_issues.md](known_issues.md)
- 当前阶段和优先级：看 [project_status.md](project_status.md)
- 迁移或换环境：看 [migration_runbook.md](migration_runbook.md)

## 当前下一步任务

- USB-CAN 固定命名
- 正式入口前置姿态/限位检查
- bridge/action 日志和恢复增强

## 今天结束前至少更新

1. [project_status.md](project_status.md)
2. [next_actions.md](next_actions.md)
3. [session_resume.md](session_resume.md)

## 新聊天框直接复制

```text
当前仓库是 dual_nero_ws。P0 和 P1 已完成，当前真实执行方案是 bridge，不是 native ros2_control plugin。P1 已通过实机验证：左右单臂 read-only、双臂只读、/joint_states 14 joints、双臂最小动作、左右单点 action 都已成功。当前 create_agx_arm_config 的实机稳定做法是最小参数集：robot="nero", comm="can", channel, interface, bitrate；当前不要传 enable_check_can / auto_connect / timeout。connect() 后必须 set_normal_mode()，enable() 需要轮询重试。当前 P2 已落地第一版正式入口 preflight：real_hardware.launch.py 会打印左右臂 channel 映射、preflight_enabled、preflight_config_path、safety_mode，action 和 topic 命令在真正执行前都会经过统一 preflight。USB-CAN 枚举顺序可能导致 can0/can1 与物理左右臂错位；如果中途拔插 USB-CAN，需要重新确认映射并重启 real_hardware.launch.py。三个 test 脚本都已支持 --keep-enabled，适合连续 test + action。当前下一阶段是 P2：先现场验证 preflight 行为，再做 bridge 日志/恢复增强和重复性 smoke test。
```
