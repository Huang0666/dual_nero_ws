# P3-A 故障恢复 SOP

## 范围

本文档是 P3-A 的正式交付物，用于规范真实执行链在现场出现异常时的诊断、恢复与最小回归流程。

适用场景：

- 重启电脑后重新接入双臂
- USB-CAN 重插后恢复
- `BUS-OFF / STOPPED`
- 单臂不可用导致 degraded
- `/joint_states --once` 阻塞
- 怀疑左右臂映射错位

## 操作硬规则

1. 不要并发运行测试脚本和 bridge launch 占用同一套硬件
2. 所有恢复动作先做单臂只读检查，再做 bridge 启动
3. 任何动作前先确认 `can0/can1` 状态和左右臂映射
4. `gs_usb` 设备不要依赖 `restart-ms`
5. 文档中的命令以当前工作区 `install` 配置为准

## 标准恢复顺序

1. 校验环境 overlay 是否指向当前工作区
2. 重建 `can0/can1`，确认状态为 `UP`
3. 分别执行左臂、右臂只读单测
4. 单测都 `rc=0` 后，再启动只读 bridge
5. 验证 `/joint_states --once`
6. 需要动作时，再切到 `allow_motion:=true enable_on_start:=true`

## 标准命令

### 1. 环境准备

```bash
source /opt/ros/humble/setup.bash
cd ~/wkw_ws/dual_nero_ws_test/dual_nero_ws
source install/setup.bash
```

### 2. CAN 重建

```bash
sudo ip link set can0 down || true
sudo ip link set can1 down || true
sudo ip link set can0 type can bitrate 1000000
sudo ip link set can1 type can bitrate 1000000
sudo ip link set can0 up
sudo ip link set can1 up

ip -details link show can0
ip -details link show can1
```

合格标准：

- `state UP`
- 非 `BUS-OFF`
- 非 `STOPPED`

### 3. 单臂只读检查

```bash
python3 src/dual_nero_driver/scripts/test_left_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose

python3 src/dual_nero_driver/scripts/test_right_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

合格标准：

- 左右臂最终都返回 `rc=0`
- 能看到 `connect: success`
- 能完成 `enable_all`

### 4. 只读启动

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=false enable_on_start:=false
```

启动后必须看到：

- `[bringup] left_arm channel -> ...`
- `[bringup] right_arm channel -> ...`
- `[bringup] preflight_enabled -> ...`
- `[bringup] preflight_config_path -> ...`
- `[bringup] safety_mode -> ...`

### 5. joint state 检查

```bash
ros2 topic echo /joint_states --once
```

合格标准：

- 能返回 14 个关节
- 不长时间阻塞

## 故障处理模板

每个故障都按下面 4 段处理：

1. 症状
2. 诊断命令
3. 恢复步骤
4. 恢复后 smoke 检查

---

## 故障 1：`can1 BUS-OFF / STOPPED`

### 症状

- `ip -details link show can1` 显示 `BUS-OFF` 或 `STOPPED`
- 右臂 `enable_all` 一直失败
- `test_right_arm.py` 返回 `rc=1`
- `/joint_states --once` 阻塞

### 诊断命令

```bash
ip -details link show can1

python3 src/dual_nero_driver/scripts/test_right_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 恢复步骤

1. 检查右臂物理线缆、供电、急停状态
2. 修复线缆或接触问题
3. 重新执行 CAN 重建命令
4. 重新跑右臂只读单测，直到 `rc=0`

### 恢复后 smoke

- `ip -details link show can1` 为 `UP`
- `test_right_arm.py` 为 `rc=0`
- 只读启动后 `/joint_states --once` 恢复

---

## 故障 2：单臂掉线导致 degraded

### 症状

- launch 日志出现 `degraded`
- `/joint_states --once` 阻塞
- 双臂 topic / dual 命令不可用

### 诊断命令

```bash
python3 src/dual_nero_driver/scripts/test_left_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose

python3 src/dual_nero_driver/scripts/test_right_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 恢复步骤

1. 找出 `rc!=0` 的那一侧
2. 优先恢复对应 CAN、线缆和供电
3. 等左右臂都 `rc=0` 后，再重启 bridge

### 恢复后 smoke

- `/joint_states --once` 可读
- launch 不再打印 degraded

---

## 故障 3：怀疑左右臂映射错位

### 症状

- 左命令驱右臂，或右命令驱左臂
- 单臂测试行为与物理臂不一致

### 诊断命令

```bash
python3 src/dual_nero_driver/scripts/test_left_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose

python3 src/dual_nero_driver/scripts/test_right_arm.py \
  --config install/dual_nero_bridge/share/dual_nero_bridge/config/hardware_params.yaml \
  --verbose
```

### 恢复步骤

1. 根据物理反应确认当前 `can0/can1` 与左右臂的实际对应
2. 修正 `hardware_params.yaml` 中左右臂 `channel`
3. 重新做左右臂只读单测
4. 重启 bridge，确认启动日志映射

### 恢复后 smoke

- 启动日志里的左右臂 channel 与现场一致
- 左右臂单臂命令不再串臂

---

## 故障 4：`gs_usb` 不支持 `restart-ms`

### 症状

- 执行带 `restart-ms` 的 `ip link set` 报错：
  - `Error: Device doesn't support restart from Bus Off.`

### 诊断命令

```bash
ip -details link show can0
ip -details link show can1
```

### 恢复步骤

1. 不再使用 `restart-ms`
2. 改为 `down -> type bitrate -> up`

### 恢复后 smoke

- `can0/can1` 正常 `UP`
- 单臂测试恢复可用

---

## 故障 5：只读模式下动作请求被拒绝

### 症状

- 日志出现 `ALLOW_MOTION_DISABLED`

### 诊断命令

查看 launch 参数：

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=false enable_on_start:=false
```

### 恢复步骤

1. 确认当前是否本来就在只读模式
2. 若需要正式动作，切换到：

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=true enable_on_start:=true
```

### 恢复后 smoke

- action / topic 正例返回 `code=OK`

---

## 故障 6：topic/action 被 `INVALID_JOINT_SET` 拒绝

### 症状

- 日志出现 `INVALID_JOINT_SET`

### 诊断命令

检查命令中的 `joint_names` 是否与 controller 完全一致：

- 左臂：`left_joint1..7`
- 右臂：`right_joint1..7`
- 双臂：左 7 个 + 右 7 个

### 恢复步骤

1. 修正 joint 名称集合
2. 不要把右臂 joint 发到左臂 controller

### 恢复后 smoke

- 同一条命令修正后可通过 preflight

## 恢复完成判定

以下 5 项同时满足，才视为现场恢复完成：

1. `can0/can1` 均 `UP`
2. 左右臂只读单测都 `rc=0`
3. 启动日志能看到映射和安全模式
4. `/joint_states --once` 可读取
5. 目标路径的最小正例能通过

## 与其他文档的职责边界

- [../../operations/migration_runbook.md](../../operations/migration_runbook.md)：偏环境部署与重启流程
- [../../operations/issue_index.md](../../operations/issue_index.md)：偏跨阶段问题索引
- 本文档：偏现场故障处置 SOP

## 下一步提示

- 下一项：P3-B MoveIt 执行链系统化验证
- 目标：把 MoveIt 规划 -> action -> 真机执行做成可重复验证流程
- 依赖：P3-A 的故障恢复 SOP 已经稳定可执行
