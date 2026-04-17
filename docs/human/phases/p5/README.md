# P5 文档

## 作用

定义 `P5-Sim / P5-Real` 阶段要做什么、不做什么、优先怎么做，以及第一版要落到哪些代码与配置位置。

## 当前阶段定位

P5 不是重写 MoveIt，也不是另造一套仿真任务系统。  
P5 的定位是：

- 在当前 P4 已打通的任务入口基础上继续复用 `run_dual_arm_task`
- 在 MoveIt 之上增加双臂协同、约束、避障和场景能力
- 保持 joint / group / controller / action 合同不变

当前阶段拆分为：

- `P5-Sim`：先在仿真 backend 上落地
- `P5-Real`：后续在真实工位上复用同一套任务逻辑验证

## 与 P4 的边界

P4 解决的是：

- 固定场景任务入口是否建立
- 执行链是否打通
- 最小闭环是否可跑

P5 解决的是：

- 双臂如何在同一任务中协同
- 障碍物和约束如何进入规划链
- 任务如何从“单一固定动作”升级为“多阶段任务”

## P5-v1 当前范围

P5 第一版只做最小协同闭环，不追复杂框架和视觉。

目标包括：

1. 定义 `P5` 的 task schema
2. 支持多 stage task
3. 支持最小协同执行语义
4. 支持最小失败回退策略
5. 支持能力验证用的静态 Planning Scene
6. 在仿真里形成一个可重复的最小协同样例

当前不要求：

- 动态障碍物
- 视觉输入
- 复杂真机验收
- MTC / BehaviorTree 作为前提

## 当前代码落点

### 已开始改动

- `src/dual_nero_bridge/dual_nero_bridge/dual_arm_task_cli.py`
- `src/dual_nero_bridge/config/p5_tasks.yaml`
- `src/dual_nero_bridge/config/p5_scene_sim.yaml`
- `src/dual_nero_bridge/config/p5_scene_real.yaml`

### 后续继续扩展的位置

- `src/dual_nero_bridge/config/p5_scene_sim.yaml`
- `src/dual_nero_bridge/config/p5_scene_real.yaml`
- 如后续复杂度上升，再考虑拆出：
  - `task_schema.py`
  - `task_engine.py`
  - `planning_scene_utils.py`

### backend 层

继续复用，不在 P5 里重写：

- 仿真：`dual_nero_bringup/launch/simulation.launch.py`
- 真机：`dual_nero_bringup/launch/real_hardware.launch.py`

## P5-v1 实施顺序

### Step 1：任务 schema 升级

把当前 `safe / prep / return` 结构升级为多 stage 结构。

最小字段建议：

- `task_name`
- `group_name`
- `stages`
- `execution_mode`
- `failure_policy`
- `scene_profile`

### Step 2：协同执行语义

第一版只支持：

- `sync`
- `serial_left_first`
- `serial_right_first`

### Step 3：最小失败策略

第一版只支持：

- `abort`
- `return_safe`

### Step 4：Planning Scene 接入

把静态障碍物纳入 MoveIt Planning Scene。

第一版只做：

- 固定障碍物
- 固定工位对象
- 静态 `CollisionObject`

说明：

- 这里的 `sim_static_demo` 只是 `P5-Sim` 的能力验证场景
- 它不是现场真实工位
- 它的作用是验证多 stage、sync/serial、return_safe 在受限空间下仍可工作

### Step 5：最小样例

在仿真里跑通一个多 stage 的双臂协同任务。

## P5-v1 验收标准

P5-Sim 第一版完成时，至少要满足：

1. 能跑一个多 stage 的双臂任务
2. 能切换至少 2 种 execution mode
3. 失败时能按配置中止或回安全位
4. 不改现有 joint / group / controller / action 合同
5. 静态场景只作为能力验证场景，不作为真机安全结论来源

## 当前未完成的回归确认

本轮代码已新增：

- 多 stage task schema
- `p5_tasks.yaml`
- `sim_static_demo` 场景
- `Planning Scene` 注入
- 仿真 ros2_control 插件链切到 `ign_ros2_control`

但这些仍未形成 Linux 侧最终通过结论。最近一次用户验证显示：

- `ros2 launch dual_nero_bringup simulation.launch.py` 日志出现 `Failed to load system plugin [libgz_ros2_control-system.so]`
- `ros2 control list_controllers` 返回 `No controllers are currently loaded!`
- 因此 `dual_stage_demo` 还不能算已验收通过

新窗口继续工作时，优先级应是：

1. 先恢复 controller
2. 再验证 `dual_stage_demo`
3. 最后再继续扩大 P5 功能面

## 本阶段明确后移的内容

### 移到 P6

- 视觉接入
- 感知结果进任务链
- 简单抓取 / 操作闭环

### 移到 P7

- 动态障碍物
- 更复杂的调度 / 分支
- 如确有必要，再评估 MTC / BehaviorTree

### 移到 P8

- 复杂真机验收
- 更复杂抓取与现场任务闭环
- 更高强度的真实工位安全结论

## 当前需要后续确认的关键问题

1. P5 第一版是否只做 `P5-Sim`
2. 是否继续沿用 `run_dual_arm_task` 作为正式入口
3. P5 配置文件是否独立成 `p5_tasks.yaml`
4. 第一版 scene 是否只先做静态 YAML
