# 项目状态总控台账

## 当前结论

- 当前项目已完成 `P1`
- 当前真实执行方案是 **bridge**
- 当前不是 native C++ `ros2_control` hardware plugin
- 当前推荐路线：继续沿 bridge 做 `P2 稳定化与工程化`

## 当前阶段

- 已完成：`P1 Final Cleanup`
- 正在进入：`P2 稳定化与工程化`
- P2 当前已完成第一步：正式入口 preflight 已接入

## 当前最高优先级

1. 现场验证正式入口 preflight
2. bridge / action 日志与恢复能力增强
3. 重复性 smoke test
4. USB-CAN 当前流程文档化与风险控制

## 当前阻塞点

- `can0/can1` 仍是临时方案，左右臂映射可能错位
- 正式入口缺少更强的自动保护和恢复
- 现场复现能力还不够稳定

## P0 / P1 已完成

### P0

- 三层结构已固定：
  - `display`
  - `planning_demo`
  - `real_hardware_execution`
- 命名体系已冻结：
  - joints：`left_joint1..7`、`right_joint1..7`
  - groups：`left_arm`、`right_arm`、`dual_arms`
  - controllers：`left_arm_controller`、`right_arm_controller`、`joint_state_broadcaster`

### P1

- 左臂单臂 read-only 成功
- 右臂单臂 read-only 成功
- 双臂只读成功
- `/joint_states` 14 joints 正常
- 双臂最小动作成功
- 左臂单点 action 成功
- 右臂单点 action 成功
- 双臂动作一致

## 当前已确认技术结论

- `pyAgxArm` 对 Nero 实机可用
- `set_normal_mode()` 必须走
- `enable()` 需要轮询重试
- 当前实机稳定做法是最小 `create_agx_arm_config(...)` 参数集：
  - `robot="nero"`
  - `comm="can"`
  - `channel`
  - `interface`
  - `bitrate`
- 当前不要传：
  - `enable_check_can`
  - `auto_connect`
  - `timeout`
- 如果中途拔插 USB-CAN：
  - 重新确认映射
  - 重启 `real_hardware.launch.py`

## 当前已确认现场问题

### 右臂初始位姿超限

- 首次双臂最小动作失败
- 当前已通过 limit 收口和执行前检查缓解

### USB-CAN 映射错位

- 现场已出现“左命令驱右臂 / 右命令驱左臂”
- 根因是 USB-CAN 枚举/插拔顺序
- 当前仍需人工确认 `channel -> 物理手臂`

## 阶段路线图

### P1 Final Cleanup

- 目标：把最小真机执行链收成稳定版本
- 当前状态：已完成

### P2 稳定化与工程化

- 目标：从“能跑”变成“稳定可复现”
- 当前重点：
  - 正式入口 preflight 的现场验证
  - 前置姿态/限位检查
  - bridge/action 日志增强
  - fault / reconnect / recovery
  - 重复性 smoke test

### P3 更正式的规划执行验证

- 目标：推进到更规范的 MoveIt 执行验证
- 当前待做：
  - MoveIt 到 action 的真实执行验证
  - 轨迹时间与容差核对
  - bridge 边界整理

### P4 长期架构决策

- 目标：评估是否长期保留 bridge
- 当前建议：
  - 不要立即切 native plugin
- 理由：
  - 当前主要问题是稳定化与工程化，不是架构打不通

## 本周只做什么

- 先验证正式入口 preflight 的现场行为
- 再做 bridge/action 日志和恢复增强
- 保持当前 `can0/can1` 临时策略，不在这一轮实现固定命名
- 暂不切换硬件架构路线

## 下一聊天框直接复制

```text
当前仓库是 dual_nero_ws。P0 和 P1 已完成，当前真实执行方案是 bridge，不是 native ros2_control plugin。P1 已通过实机验证：左右单臂 read-only、双臂只读、/joint_states 14 joints、双臂最小动作、左右单点 action 都已成功。当前 create_agx_arm_config 的实机稳定做法是最小参数集：robot="nero", comm="can", channel, interface, bitrate；当前不要传 enable_check_can / auto_connect / timeout。connect() 后必须 set_normal_mode()，enable() 需要轮询重试。当前 P2 已落地第一版正式入口 preflight：real_hardware.launch.py 会打印左右臂 channel 映射、preflight_enabled、preflight_config_path、safety_mode，action 和 topic 命令在真正执行前都会经过统一 preflight。USB-CAN 枚举顺序可能导致 can0/can1 与物理左右臂错位；如果中途拔插 USB-CAN，需要重新确认映射并重启 real_hardware.launch.py。三个 test 脚本都已支持 --keep-enabled，适合连续 test + action。当前下一阶段是 P2：先现场验证 preflight 行为，再做 bridge 日志/恢复增强和重复性 smoke test。
```
