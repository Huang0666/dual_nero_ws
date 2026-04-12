# 下一步任务

## 当前阶段

- 当前阶段：`P3 正式执行验证`
- P2 已完成并验收通过

## 优先级 A：故障恢复 SOP 标准化

- 本项已进入落地阶段，正式文档见：
  - [../phases/p3/recovery_sop.md](../phases/p3/recovery_sop.md)
- 统一以下故障的现场处置步骤：
  - BUS-OFF / STOPPED
  - degraded 模式（单臂不可用）
  - 重连后映射错位
- 明确每种故障的：
  - 触发条件
  - 诊断命令
  - 恢复步骤
  - 恢复后 smoke 检查
- 要求非原开发者按文档可独立恢复

## 优先级 B：MoveIt 执行验证

- 最小验证 CLI 已落地：
  - `ros2 run dual_nero_bridge validate_moveit_pipeline`
- 当前主验证路径切换为：
  - `--bridge-final-point-execute`
- `--execute` 保留用于观察 MoveIt 原生 `ExecuteTrajectory` 与 bridge 单点合同的兼容性
- 当前已完成：
  - 左臂规划
  - 右臂规划
  - 左臂末点执行
  - 右臂末点执行
  - 只读负例
- 当前剩余收尾项：
  - 补 `dual_arms` 规划（可选增强）
  - 用厂家真值替换 MoveIt 当前保守速度/加速度占位限值
  - 持续完善报告中的原始输出归档
- 正式计划文档：
  - [../phases/p3/moveit_validation_plan.md](../phases/p3/moveit_validation_plan.md)
- 正式结果要回填到：
  - [../phases/p3/moveit_validation_report.md](../phases/p3/moveit_validation_report.md)

## 优先级 C：USB-CAN 固定命名（暂缓）

- 该项暂缓，等待批量策略成熟后再实施
- 先保留任务入口与验收目标，不在当前周期落地

## 本阶段不做

- 切换到 native `ros2_control` plugin
- 大规模架构重写
- 冻结合同外的命名/协议变更
