# P2 验收报告

## 范围

本报告记录在当前 bridge 架构下完成的 P2 稳定化验收结果：

- 不切换到 native `ros2_control` hardware plugin
- 不更换当前总体架构
- action/topic 正式入口统一 preflight gate
- 启动期映射/安全/配置检查可见且可失败

## 验收结论

### 1. 启动验收：通过

已确认启动日志包含：

- `[bringup] left_arm channel -> ...`
- `[bringup] right_arm channel -> ...`
- `[bringup] preflight_enabled -> ...`
- `[bringup] preflight_config_path -> ...`
- `[bringup] safety_mode -> ...`

### 2. Action 路径验收：通过

- 左右臂单点合法 goal：`preflight ok=True, code=OK`
- 只读模式（`allow_motion=false`）：被拒绝且报 `ALLOW_MOTION_DISABLED`

### 3. Topic 路径验收：通过

- 左/右/双臂合法 topic 命令：`preflight ok=True, code=OK`
- 错误 joint set：被拒绝且报 `INVALID_JOINT_SET`
- 起点偏差过大：被拒绝且报 `START_DEVIATION_TOO_LARGE`

### 4. 一致性验收：通过

action/topic 对同类故障使用一致的错误码与消息语义。

## 现场故障记录

### 故障 A：`can1 BUS-OFF/STOPPED`

现象：

- 右臂 `enable_all` 一直全 `False`
- 右臂单测 `rc=1`
- `/joint_states --once` 在 degraded 状态下阻塞

处置：

- 修复右臂 CAN 物理线缆
- 重新初始化 CAN 接口
- 重新执行单臂测试直到左右臂均 `rc=0`

### 故障 B：`gs_usb` 不支持 `restart-ms`

现象：

- `Error: Device doesn't support restart from Bus Off.`

处置：

- 不依赖 `restart-ms`
- 使用 `down/type/up` 显式重置流程

## 最终判定

P2 验收完成，可进入 P3。

## P3 第一优先级

- USB-CAN 固定命名（udev 或等价方案）
- 映射在重启/重插后保持可预测、可复现
