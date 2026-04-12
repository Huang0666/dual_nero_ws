# 交接摘要

## 当前项目状态

- P1 已完成
- P2 已完成并通过现场验收
- P3 主体已完成
- 当前进入 `P4 目标定义`

## 当前总目标

- 双臂协调运动
- 避障
- 视觉接入
- 简单抓取任务

## 当前推荐入口

- 项目状态：[../human/overview/project_status.md](../human/overview/project_status.md)
- 下一步任务：[../human/overview/next_actions.md](../human/overview/next_actions.md)
- P3 恢复 SOP：[../human/phases/p3/recovery_sop.md](../human/phases/p3/recovery_sop.md)
- P3 验证报告：[../human/phases/p3/moveit_validation_report.md](../human/phases/p3/moveit_validation_report.md)
- 运维问题索引：[../human/operations/issue_index.md](../human/operations/issue_index.md)

## 当前有效结论

- 当前 bridge 路线已具备单臂 MoveIt 主路径执行能力。
- 当前正式路径不是原生 `ExecuteTrajectory`，而是 `bridge-final-point`。
- P3-C 固定命名保持暂缓，不阻塞当前路线。
- 下一步不是继续零散验证，而是先定义 P4。

## 当前注意事项

- 测试脚本和 bridge launch 不要并发占同一套硬件
- `real_hardware.launch.py` 运行时，验证命令必须从另一个终端执行
- 速度/加速度限位当前是保守占位值，不是厂家真值
