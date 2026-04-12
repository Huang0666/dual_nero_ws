# P3-B MoveIt 执行链验证计划

## 目标

验证当前 bridge 架构下的 MoveIt 执行链已经具备最小可重复验证入口：

1. MoveIt 能从当前 `/joint_states` 规划出合法轨迹
2. MoveIt 能通过 `/execute_trajectory` 把轨迹下发到控制器
3. bridge 的 preflight 与 action 执行日志语义保持清晰
4. 成功与失败边界可以用统一命令复现

## 当前状态

- P3-A 故障恢复 SOP 已完成，可作为 P3-B 的前置恢复流程
- 已新增正式 CLI：
  - `ros2 run dual_nero_bridge validate_moveit_pipeline`
- 已支持两条执行路径：
  - `--execute`：直接走 MoveIt `ExecuteTrajectory`
  - `--bridge-final-point-execute`：将 MoveIt 规划结果压成末点单点 goal，再走当前 bridge 合同
- 已将左右臂最小 action 客户端补成 `ros2 run` 正式入口：
  - `ros2 run dual_nero_bridge send_left_arm_goal`
  - `ros2 run dual_nero_bridge send_right_arm_goal`
- 现场执行结果尚未正式补入报告

## 前置条件

执行 P3-B 前，先满足以下条件：

1. 按 [recovery_sop.md](recovery_sop.md) 完成现场恢复
2. `can0/can1` 均为 `UP`
3. 左右臂单臂只读单测均 `rc=0`
4. `ros2 topic echo /joint_states --once` 可立即返回 14 个关节
5. `ros2 launch dual_nero_bringup real_hardware.launch.py` 能正常启动并看到 `[bringup]` 日志

## 启动方式

### 只做规划或失败语义验证

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=false enable_on_start:=false
```

### 做真实执行验证

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=true enable_on_start:=true
```

说明：

- `with_moveit` 默认已开启，不需要额外显式传参
- 需要 RViz 时可追加 `with_rviz:=true`

## 验证入口

### 1. 左臂 MoveIt 规划

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm
```

预期：

- 输出当前姿态与目标姿态预览 JSON
- 规划摘要 `error_name=SUCCESS`
- 不触发真实运动

### 2. 右臂 MoveIt 规划

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group right_arm
```

预期：

- 规划摘要 `error_name=SUCCESS`

### 3. 左臂 MoveIt 规划 + 执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm --execute
```

预期：

- 规划摘要 `error_name=SUCCESS`
- 若当前 MoveIt 输出多点轨迹，可能出现 `CONTROL_FAILED`
- 本命令当前主要用于观察“MoveIt 原生 execute 与 bridge 单点合同是否兼容”

### 4. 右臂 MoveIt 规划 + 执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group right_arm --execute
```

预期：

- 规划成功
- 若为多点轨迹，执行可能同样出现 `CONTROL_FAILED`

### 5. 左臂 MoveIt 规划 + bridge 末点执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm --bridge-final-point-execute
```

预期：

- 规划摘要 `error_name=SUCCESS`
- bridge 执行摘要 `error_name=SUCCESSFUL`
- `real_execution_node` 日志出现：
  - `source=trajectory`
  - `preflight result -> ok=True, code=OK`

### 6. 右臂 MoveIt 规划 + bridge 末点执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group right_arm --bridge-final-point-execute
```

预期：

- 规划成功
- bridge 单点执行成功

### 7. 双臂 MoveIt 规划（可选增强）

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group dual_arms
```

说明：

- 本项优先级低于左右单臂
- 通过标准是规划成功，不要求当前轮必须执行真实双臂轨迹

### 8. 只读模式负例

在 `allow_motion:=false` 下执行：

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm --bridge-final-point-execute
```

预期：

- MoveIt 规划仍可成功
- 执行阶段失败
- bridge 日志中明确出现 `ALLOW_MOTION_DISABLED`

## 验证矩阵

| 项目 | 命令 | 通过标准 |
| --- | --- | --- |
| 左臂规划 | `validate_moveit_pipeline --group left_arm` | `error_name=SUCCESS` |
| 右臂规划 | `validate_moveit_pipeline --group right_arm` | `error_name=SUCCESS` |
| 左臂原生执行 | `validate_moveit_pipeline --group left_arm --execute` | 用于观察原生 `ExecuteTrajectory` 兼容性 |
| 右臂原生执行 | `validate_moveit_pipeline --group right_arm --execute` | 用于观察原生 `ExecuteTrajectory` 兼容性 |
| 左臂末点执行 | `validate_moveit_pipeline --group left_arm --bridge-final-point-execute` | bridge 单点执行成功，日志 `code=OK` |
| 右臂末点执行 | `validate_moveit_pipeline --group right_arm --bridge-final-point-execute` | bridge 单点执行成功，日志 `code=OK` |
| 只读负例 | `allow_motion:=false` + `--bridge-final-point-execute` | 规划成功，执行失败，bridge 日志 `ALLOW_MOTION_DISABLED` |
| 双臂规划 | `validate_moveit_pipeline --group dual_arms` | 可选，规划成功即可 |

## 日志采集要求

P3-B 正式验收时至少保留以下日志：

- `validate_moveit_pipeline` 的 preview / plan / execute JSON
- `real_execution_node` 中对应 `source=trajectory` 的日志
- 负例时的 bridge reject 日志

## 当前结论边界

- MoveIt 默认会返回多点轨迹
- 当前 bridge 合同只接受单点 trajectory
- 因此 `--execute` 可能出现 `CONTROL_FAILED`
- P3-B 当前主验收路径应使用 `--bridge-final-point-execute`

## 预期交付

- 一套统一的 `ros2 run` 验证命令
- 一份正式验证报告
- 至少 1 组成功日志和 1 组失败日志
