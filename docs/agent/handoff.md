# 交接摘要

## 当前项目状态

- P1 已完成
- P2 已完成并通过现场验收
- 当前进入 P3

## 当前优先级

1. P3-A：故障恢复 SOP 标准化
2. P3-B：MoveIt 执行链系统化验证
3. P3-C：USB-CAN 固定命名（暂缓）

## 当前推荐入口

- 项目状态：[../human/overview/project_status.md](../human/overview/project_status.md)
- 下一步任务：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- P3-A 恢复 SOP：[../human/phases/p3/recovery_sop.md](../human/phases/p3/recovery_sop.md)
- P3-B 计划：[../human/phases/p3/moveit_validation_plan.md](../human/phases/p3/moveit_validation_plan.md)
- 运维问题索引：[../human/operations/issue_index.md](../human/operations/issue_index.md)

## 当前最小恢复命令

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

## 当前注意事项

- 测试脚本和 bridge launch 不要并发占同一套硬件
- `gs_usb` 不要依赖 `restart-ms`
- P3-B 现在优先使用 `ros2 run dual_nero_bridge validate_moveit_pipeline`
- P3-C 当前不做
