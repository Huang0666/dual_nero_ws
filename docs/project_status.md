# Project Status

## 项目当前结论

- 当前项目已经完成 P1 真机最小执行链。
- 当前真实执行方案是 **bridge 方案**，不是 native C++ `ros2_control` hardware plugin。
- 当前推荐路线是继续沿 bridge 做稳定化与工程化，不建议立即切换到 native plugin。
- 当前项目三层结构已经固定：
  - `display`
  - `planning_demo`
  - `real_hardware_execution`

## 已完成事项

### P0 Baseline

- 仓库定位与三层结构已明确
- joints / groups / controllers 命名体系已冻结
- TF 主干口径已固定

### P1 真机最小执行链

- 左臂单臂 read-only 成功
- 右臂单臂 read-only 成功
- 双臂只读成功
- `/joint_states` 14 joints 正常
- 双臂最小动作成功
- 左臂单点 action 成功
- 右臂单点 action 成功
- 双臂动作一致

### P1 Final Cleanup

- `test_left_arm.py` / `test_right_arm.py` / `test_dual_arm.py` cleanup 行为已统一
- 三个 test 脚本都支持 `--keep-enabled`
- 当前最小成功参数集已固化到代码和文档
- USB-CAN 顺序错位问题已明确记录
- smoke / execution / README 已更新为 P1 最终状态

## 当前阶段

- 当前阶段：`P1 Final Cleanup` 已完成
- 下一活跃阶段：`P2 稳定化与工程化`

## 当前阻塞点

- USB-CAN 仍使用 `can0/can1` 临时方案，缺少固定命名
- 正式入口还缺少更强的姿态/限位前置校验
- bridge 的 fault / reconnect / recovery 仍较弱
- 现场复现能力还需要重复性 smoke test 支撑

## 下一步任务

- 先做 USB-CAN 固定命名，例如 `udev`
- 把当前姿态与限位检查前置到正式入口
- 增强 bridge/action 的日志、错误原因和恢复语义
- 做重复性 smoke test，形成更稳定的复现记录

## 阶段路线图

### P1 Final Cleanup

目标：

- 把已经打通的真机最小执行链收成稳定版本

已完成：

- 统一 test 脚本 cleanup 行为
- 增加 `--keep-enabled`
- 固化当前最小成功参数集
- 明确记录 USB-CAN 顺序错位问题
- 更新 smoke / execution / README 文档为最终 P1 状态

### P2 稳定化与工程化

目标：

- 从“能跑”变成“稳定可复现”

建议任务：

- USB-CAN 固定命名（udev）
- 当前姿态与限位检查前置到正式入口
- action / bridge 日志增强
- fault / reconnect / recovery 基础策略
- 做重复性 smoke test

### P3 更正式的规划执行验证

目标：

- 从单点动作与 bridge 测试，推进到更规范的 MoveIt 执行验证

建议任务：

- MoveIt 到 action 的真实执行验证
- 轨迹时间与容差核对
- bridge 方案边界整理
- 是否继续长期沿用 bridge 的评估

### P4 长期架构决策

目标：

- 判断是否继续走 bridge，还是进入 native hardware plugin 路线评估

当前推荐路线：

- 继续沿 bridge 做 P2 / P3，不建议立即切换 native plugin

当前不建议立即切换 native plugin 的理由：

- P1 已经在 bridge 路线上打通
- 当前主要问题是稳定化和工程化，不是架构打不通
- 现在切架构会打断现场验证连续性

## Context For Next Chat

可直接复制给新聊天框：

```text
当前仓库是 dual_nero_ws，P0 和 P1 已完成。项目当前真实执行方案是 bridge，不是 native ros2_control plugin。P1 已经通过实机验证：左臂 read-only、右臂 read-only、双臂只读、/joint_states 14 joints、双臂最小动作、左臂单点 action、右臂单点 action 都已成功。当前 create_agx_arm_config 的实机稳定做法是最小参数集：robot="nero", comm="can", channel, interface, bitrate；当前不要传 enable_check_can / auto_connect / timeout。connect() 后必须 set_normal_mode()，enable() 需要轮询重试。已知问题包括：右臂初始位姿曾超限，现已通过 limits 收口和执行前检查缓解；USB-CAN 枚举顺序可能导致 can0/can1 与物理左右臂错位，当前仍是临时方案，后续建议做 udev 固定命名；如果中途拔插 USB-CAN，需要重启 real_hardware.launch.py。当前 test_left_arm.py / test_right_arm.py / test_dual_arm.py 已统一支持 --keep-enabled，默认安全收尾，适合连续 test + action 时可保留使能。当前下一阶段是 P2 稳定化与工程化。
```
