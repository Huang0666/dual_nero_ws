# 交接摘要

## 当前项目状态

- P1 已完成
- P2 已完成并通过现场验收
- P3 主体已完成
- 当前进入 `P4 双臂固定场景任务闭环`

## 当前总目标

- 双臂协调运动
- 避障
- 视觉接入
- 简单抓取任务

## 当前正式入口

- 启动：`ros2 launch dual_nero_bringup real_hardware.launch.py`
- P4 任务入口：`ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync`

## 当前有效结论

- bridge 路线仍为主路径
- 任务执行以 `bridge-final-point` 为正式合同
- P3-C 固定命名暂缓，不阻塞 P4
- P4 任务入口已落地，但需要现场验收固化

## 当前注意事项

- 测试脚本和 bridge launch 不要并发占同一套硬件
- `real_hardware.launch.py` 运行时，验证命令必须从另一个终端执行
- 速度/加速度限位当前为保守占位值，不是厂家真值

## 关键文档入口

- 项目状态：[../human/overview/project_status.md](../human/overview/project_status.md)
- 下一步任务：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- 总体路线：[../human/overview/roadmap.md](../human/overview/roadmap.md)
- P4 阶段定义：[../human/phases/p4/README.md](../human/phases/p4/README.md)
- P3 恢复 SOP：[../human/phases/p3/recovery_sop.md](../human/phases/p3/recovery_sop.md)
- P3 验证报告：[../human/phases/p3/moveit_validation_report.md](../human/phases/p3/moveit_validation_report.md)
