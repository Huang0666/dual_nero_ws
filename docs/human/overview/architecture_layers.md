# 当前架构分层

## 作用

说明当前项目哪些层必须在真机与仿真之间保持一致，哪些层允许分叉。

## 当前分层

### 1. 任务层

- `run_dual_arm_task`
- 后续 P5 任务入口
- 任务 YAML 结构

要求：

- 真机与仿真必须保持一致

### 2. 规划层

- MoveIt
- `left_arm`
- `right_arm`
- `dual_arms`

要求：

- 真机与仿真必须保持一致

### 3. 执行合同层

- `FollowJointTrajectory`
- `left_arm_controller`
- `right_arm_controller`
- joint/controller 命名合同

要求：

- 真机与仿真必须保持一致

### 4. 规则层

- preflight
- 任务前检查
- 目标结构校验

要求：

- 通用规则尽量复用
- 纯真机项允许在仿真中做等价策略或豁免

### 5. backend 层

- 真机：`bridge -> driver -> pyAgxArm -> hardware`
- 仿真：`gz sim -> ros2_control sim hardware -> joint_trajectory_controller`

要求：

- 这是唯一允许明确分叉的层

## 当前冻结原则

- 不允许为了仿真新造第二套任务入口
- 不允许为了仿真改动 joint/group/controller 命名合同
- 不允许把当前 P1-P4 的任务层成果丢掉重来
- 允许只替换最底层执行 backend
