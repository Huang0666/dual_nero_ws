# 下一步任务

## 当前阶段

- 当前阶段：`P3 Formal Execution Validation`
- P2 已完成并验收通过

## 优先级 A：USB-CAN 映射稳定化

- 落地固定命名规则（udev 或等价方案）
- 将左右臂配置绑定到稳定接口标识
- 验证以下场景稳定性：
  - 重启
  - USB 重插
  - 设备重枚举

## 优先级 B：MoveIt 执行验证

- 验证 MoveIt 规划到 action 执行链路
- 核对容差与时间行为是否符合预期
- 固化可复现的通过/失败命令

## 优先级 C：恢复流程工程化

- 固化以下场景的恢复步骤：
  - BUS-OFF / STOPPED
  - degraded 模式（单臂不可用）
  - 重连后映射错位
- 每次恢复后增加一轮快速 smoke

## 本阶段不做

- 切换到 native `ros2_control` plugin
- 大规模架构重写
- 冻结合同外的命名/协议变更
