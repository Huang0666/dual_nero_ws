# P5 文档

## 作用

定义 `P5-Sim / P5-Real` 阶段要做什么、不做什么、优先怎么做，以及第一版要落到哪些代码与配置位置。

## 当前阶段定位

P5 不是重写 MoveIt，也不是另造一套仿真任务系统。  
P5 的定位是：

- 在当前 P4 已打通的任务入口基础上
- 继续复用 `run_dual_arm_task`
- 在 MoveIt 之上增加双臂协同、约束、避障和场景能力

当前阶段拆分为：

- `P5-Sim`：先在仿真 backend 上落地
- `P5-Real`：后续在真实工位上验证

## 与 P4 的边界

P4 解决的是：

- 固定场景任务入口是否建立
- 执行链是否打通
- 最小闭环是否可跑

P5 解决的是：

- 双臂如何在同一任务中协同
- 障碍物和约束如何进入规划链
- 任务如何从“单一固定动作”升级为“多阶段任务”

## 第一版目标

P5 第一版只做最小协同闭环，不追复杂框架和视觉。

目标包括：

1. 定义 `P5` 的 task schema
2. 支持多 stage task
3. 支持静态场景障碍物
4. 支持最小协同执行语义
5. 支持最小失败回退策略
6. 在仿真里形成一个可重复的最小协同样例

## 第一版建议落点

### 共用代码层

- `src/dual_nero_bridge/dual_nero_bridge/dual_arm_task_cli.py`
- 新增可拆分模块：
  - `task_schema.py`
  - `task_engine.py`
  - `planning_scene_utils.py`

### 配置层

- 新增 `src/dual_nero_bridge/config/p5_tasks.yaml`
- 新增 `src/dual_nero_bridge/config/p5_scene_sim.yaml`
- 新增 `src/dual_nero_bridge/config/p5_scene_real.yaml`

### backend 层

继续复用，不在 P5 里重写：

- 仿真：`dual_nero_bringup/launch/simulation.launch.py`
- 真机：`dual_nero_bringup/launch/real_hardware.launch.py`

## 第一版最小实施顺序

### Step 1：任务 schema 升级

把当前 `safe / prep / return` 结构升级为多 stage 结构。

最小字段建议：

- `task_name`
- `group_name`
- `stages`
- `execution_mode`
- `failure_policy`
- `scene_profile`

### Step 2：环境 profile

把环境差异从任务逻辑里拆出来。

最小 profile 建议：

- `sim`
- `real`

差异承载内容：

- scene
- safety / preflight 策略
- 是否允许某些阶段执行

### Step 3：Planning Scene 接入

把静态障碍物纳入 MoveIt Planning Scene。

第一版只做：

- 固定障碍物
- 固定工位对象
- 静态 CollisionObject

### Step 4：协同执行语义

第一版只支持：

- `sync`
- `serial_left_first`
- `serial_right_first`

### Step 5：最小失败策略

第一版只支持：

- `abort`
- `return_safe`

## 第一版验收标准

P5-Sim 第一版完成时，至少要满足：

1. 能跑一个多 stage 的双臂任务
2. 任务能使用静态场景障碍物
3. 能切换至少 2 种 execution mode
4. 失败时能按配置中止或回安全位
5. 不改现有 joint / group / controller / action 合同

## 当前明确不做

- 不引入 MTC 作为第一版前提
- 不引入 BehaviorTree 作为第一版前提
- 不做动态障碍物
- 不接视觉
- 不同时展开真机复杂验收

## 当前需要后续确认的关键问题

1. P5 第一版是否只做 `P5-Sim`
2. 是否继续沿用 `run_dual_arm_task` 作为正式入口
3. P5 配置文件是否独立成 `p5_tasks.yaml`
4. 第一版 execution mode 是否只做 `sync / serial_left_first / serial_right_first`
5. 第一版 failure policy 是否只做 `abort / return_safe`
6. 第一版 scene 是否只做静态 YAML
