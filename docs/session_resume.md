# 恢复卡片

## 当前上下文

- 阶段：P2 已验收完成，进入 P3
- 执行架构：bridge

## 快速启动

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

## 开始前检查

1. 确认 overlay 指向当前工作区
2. 确认 CAN 接口状态为 UP
3. 若有重插，先确认左右臂映射
4. 先跑单臂只读测试

## 单臂只读命令

```bash
python3 src/dual_nero_driver/scripts/test_left_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose

python3 src/dual_nero_driver/scripts/test_right_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

## Bridge 只读启动

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=false enable_on_start:=false
```

## 现场规则

- 不要并发运行测试脚本和 bridge launch 占用同一硬件
- 测试脚本默认收尾会失能，连续 test + action 需要 `--keep-enabled`
- USB-CAN 重插后必须先确认映射再重启 launch
- `gs_usb` 设备不要依赖 `restart-ms`

## 参考

- [known_issues.md](known_issues.md)
- [project_status.md](project_status.md)
- [migration_runbook.md](migration_runbook.md)
- [p2_acceptance_report.md](p2_acceptance_report.md)
