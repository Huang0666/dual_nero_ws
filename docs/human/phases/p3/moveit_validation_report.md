# P3-B MoveIt 执行链验证报告

## 当前状态

- 已具备最小验证 CLI
- 现场正式结果待补

## 验证环境

- 日期：
- 操作人：
- 工作区：
- ROS 发行版：
- 启动模式：
  - `allow_motion`
  - `enable_on_start`
  - `with_moveit`
  - `with_rviz`

## 执行命令

### 左臂规划

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm
```

结果：

- 是否通过：
- 关键输出：

### 右臂规划

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group right_arm
```

结果：

- 是否通过：
- 关键输出：

### 左臂执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm --execute
```

结果：

- 是否通过：
- 关键输出：

### 右臂执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group right_arm --execute
```

结果：

- 是否通过：
- 关键输出：

### 左臂 bridge 末点执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm --bridge-final-point-execute
```

结果：

- 是否通过：
- 关键输出：

### 右臂 bridge 末点执行

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group right_arm --bridge-final-point-execute
```

结果：

- 是否通过：
- 关键输出：

### 只读负例

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group left_arm --bridge-final-point-execute
```

结果：

- 是否出现 `ALLOW_MOTION_DISABLED`：
- MoveIt 执行是否按预期失败：
- 关键输出：

### 双臂规划（可选）

```bash
ros2 run dual_nero_bridge validate_moveit_pipeline --group dual_arms
```

结果：

- 是否通过：
- 关键输出：

## bridge 日志样例

### 成功样例

```text
[STATE][left_arm_controller] received trajectory goal; source=trajectory, ...
[STATE][left_arm_controller] preflight result -> ok=True, code=OK, message=preflight checks passed
```

### 失败样例

```text
[REJECT][left_arm_controller] ALLOW_MOTION_DISABLED: ...
```

## 结论

- MoveIt 规划是否稳定：
- MoveIt 原生 `ExecuteTrajectory` 是否与 bridge 兼容：
- bridge 末点执行是否稳定：
- bridge / preflight 语义是否清晰：
- 是否达到 P3-B 退出标准：

## 下一步建议

- 
