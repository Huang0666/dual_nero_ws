# Session Resume

## 当前阶段

- P1 已完成
- 当前正在进入 `P2 稳定化与工程化`
- 当前真实执行方案仍是 bridge，不是 native plugin

## 已完成内容摘要

- P0 基线已完成，三层结构和命名体系已冻结
- P1 真机最小执行链已打通
- 左右臂 read-only、双臂只读、`/joint_states`、双臂最小动作、左右单点 action 都已通过
- 当前最小成功参数集已确认
- `--keep-enabled` 已加入三个 test 脚本

## 当前阻塞点

- USB-CAN 仍可能因枚举顺序导致左右臂映射错位
- 正式入口还缺少更强的自动映射和恢复能力
- 仍缺少固定命名和更强日志

## 今日开始前检查项

- 确认 `can0/can1` 与物理左右臂映射
- 确认 CAN 已初始化
- 确认 `src/dual_nero_bridge/config/hardware_params.yaml` 未被误改
- 如果昨天中途拔插过 USB-CAN，先重启 `real_hardware.launch.py`

## Quick Resume Checklist

1. 进入仓库根目录
2. source ROS 2 环境
3. 确认 CAN 设备已 up
4. 确认 `channel -> 物理手臂` 映射
5. 先跑左右 read-only
6. 再跑双臂 read-only 和最小动作
7. 最后跑左右 action

## 恢复执行顺序

1. `test_left_arm.py`
2. `test_right_arm.py`
3. `test_dual_arm.py`
4. `/joint_states` 检查
5. `test_dual_arm.py --execute`
6. `send_left_arm_goal.py --execute`
7. `send_right_arm_goal.py --execute`

## 常用命令集合

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash

sudo ip link set can0 down || true
sudo ip link set can1 down || true
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can1 type can bitrate 1000000
sudo ip link set can0 up
sudo ip link set can1 up

PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_left_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --verbose

PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_right_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --verbose

PYTHONPATH=$PWD/src/dual_nero_driver:$PWD/src/dual_nero_bridge \
python3 src/dual_nero_driver/scripts/test_dual_arm.py \
  --config src/dual_nero_bridge/config/hardware_params.yaml \
  --execute \
  --wait \
  --delta 0.03 \
  --verbose \
  --keep-enabled
```

## 当前下一步任务

- 做 USB-CAN 固定命名
- 前置姿态/限位检查到正式入口
- 增强 bridge/action 日志和恢复策略

## 给新聊天框使用的简短上下文模板

```text
当前仓库是 dual_nero_ws。P0 和 P1 已完成，当前真实执行方案是 bridge，不是 native ros2_control plugin。P1 已通过实机验证：左右单臂 read-only、双臂只读、/joint_states 14 joints、双臂最小动作、左右单点 action 都已成功。当前 create_agx_arm_config 的实机稳定做法是最小参数集：robot="nero", comm="can", channel, interface, bitrate；当前不要传 enable_check_can / auto_connect / timeout。connect() 后必须 set_normal_mode()，enable() 需要轮询重试。USB-CAN 枚举顺序可能导致 can0/can1 与物理左右臂错位；如果中途拔插 USB-CAN，需要重新确认映射并重启 real_hardware.launch.py。三个 test 脚本都已支持 --keep-enabled，适合连续 test + action。当前下一阶段是 P2：先做 USB-CAN 固定命名、入口级姿态/限位检查和 bridge 日志/恢复增强。
```
