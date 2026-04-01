# dual_nero_ws P1 Driver Contract

## 目的

本文档是 `dual_nero_ws` 进入 P1 驱动开发前的静态退出检查结果与驱动接入合约。

P1 的目标不是改模型、不是真机功能全量交付，而是：

- 在不破坏现有 `display` / `planning_demo` 能力的前提下，
- 为后续真机驱动接入建立一套不可再变的命名、控制器、规划组、TF 主干和 `ros2_control` 对接约束。

## 静态退出检查结论

结论：**PASS，允许进入 P1 驱动开发。**

本次检查范围：

- 命名唯一性
- URDF / SRDF / controllers 一致性
- group 命名唯一性
- TF 主干口径唯一性

本次检查不包含：

- ROS 2 运行时验证
- RViz / MoveIt 启动验证
- 真机通信验证
- 时序、带宽、控制周期、丢包与安全停机验证

## 检查结果

### 1. 命名唯一性

结果：**PASS**

静态结论：

- 关节命名只存在一套：`left_joint1..7`、`right_joint1..7`
- 控制器命名只存在一套：`left_arm_controller`、`right_arm_controller`、`joint_state_broadcaster`
- 规划组命名只存在一套：`left_arm`、`right_arm`、`dual_arms`
- 未在源码配置文件中发现 `l_`、`r_`、`arm_left`、`arm_right`、`leftarm`、`rightarm` 这类第二套别名

### 2. URDF / SRDF / controllers 一致性

结果：**PASS**

检查到的权威关节集合：

- 左臂：`left_joint1` 到 `left_joint7`
- 右臂：`right_joint1` 到 `right_joint7`

一致性结论：

- URDF 单臂宏定义了 `joint1..7`，通过 `left_` / `right_` 前缀实例化后形成完整双臂 14 关节集合
- `dual_nero_description.ros2_control.xacro` 中的 joint 集合与上述 14 关节完全一致
- `ros2_controllers.yaml` 中左右控制器的 joints 列表与上述 14 关节完全一致
- `moveit_controllers.yaml` 中左右控制器的 joints 列表与上述 14 关节完全一致
- `dual_nero_description.srdf` 中 `left_arm`、`right_arm`、`dual_arms` 的 joint 集合与 URDF 一致

当前一对一映射如下：

| 层级 | 左臂 | 右臂 |
|---|---|---|
| URDF revolute joints | `left_joint1..7` | `right_joint1..7` |
| ros2_control joints | `left_joint1..7` | `right_joint1..7` |
| ros2 controller name | `left_arm_controller` | `right_arm_controller` |
| MoveIt controller name | `left_arm_controller` | `right_arm_controller` |
| SRDF group | `left_arm` | `right_arm` |

### 3. Group 命名唯一性

结果：**PASS**

当前 SRDF 中仅存在以下 group 定义：

- `left_arm`
- `right_arm`
- `dual_arms`

约束解释：

- `left_arm` 和 `right_arm` 是单臂控制与规划的最小稳定标识
- `dual_arms` 是双臂联合规划的稳定标识
- P1 期间不得新增与其等价的第二套 group 名，例如 `left_manipulator`、`right_manipulator`、`both_arms`

### 4. TF 主干口径唯一性

结果：**PASS**

当前静态定义出的唯一主干是：

`world -> dual_base_plate -> dual_column -> dual_crossbar -> {left/right}_base_link -> ...`

静态证据：

- URDF 中存在且仅存在以下三段结构固定关节：
  - `world_to_dual_base_plate`
  - `dual_base_plate_to_column`
  - `dual_column_to_crossbar`
- SRDF 中存在且仅存在一个 virtual joint：
  - `world_joint`，`parent_frame="world"`，`child_link="world"`
- 在源码配置文件中未发现 `map`、`odom`、`base_footprint` 等第二套机器人根参考系

说明：

- 当前 SRDF 的 `world_joint` 是 MoveIt 对“外部固定参考系”的语义声明。
- 当前 URDF 中的 `world` link 与 `world_to_dual_base_plate` 是描述包中的主干起点。
- 对本仓库而言，这两者当前口径一致，不构成第二套 TF 主干。

## P1 驱动接入合约

P1 开发必须遵守以下合约，除非先修改本文档和 baseline，并完成重新审计。

### 1. 不允许改名

以下名称在 P1 期间视为冻结：

- 关节：`left_joint1..7`、`right_joint1..7`
- 连杆：`world`、`dual_base_plate`、`dual_column`、`dual_crossbar`、`left_base_link`、`right_base_link`、`left_link1..7`、`right_link1..7`、`left_end_effector`、`right_end_effector`
- 固定关节：`left_mount_joint`、`right_mount_joint`、`left_end_effector_joint`、`right_end_effector_joint`
- 规划组：`left_arm`、`right_arm`、`dual_arms`
- 控制器：`left_arm_controller`、`right_arm_controller`、`joint_state_broadcaster`

P1 禁止：

- 把 `left_` / `right_` 改成别的前缀
- 为同一条手臂再引入一套 alias
- 修改 group 名来适配驱动
- 修改 controller 名来适配驱动

驱动必须适配现有名字，不是让现有模型去适配驱动名字。

### 2. ros2_control 接口合约

P1 驱动实现应继承当前 fake system 的对外接口，不得私改 joint 集合与接口类型。

P1 需要保持：

- joint 数量：14
- joint 名称：`left_joint1..7` + `right_joint1..7`
- command interface：`position`
- state interface：至少 `position`、`velocity`

P1 不允许：

- 把部分 joint 改成其他名字
- 为单条控制链只暴露 7 个 joint 却要求 MoveIt 使用 14 个
- 把现有 position 控制链静默改成另一套 controller contract

### 3. Controller 合约

P1 驱动接入后，以下 controller 命名与职责保持不变：

- `left_arm_controller`
- `right_arm_controller`
- `joint_state_broadcaster`

MoveIt 对接合约保持不变：

- controller type：`FollowJointTrajectory`
- action namespace：`follow_joint_trajectory`

如果后续驱动实现需要额外的底层控制节点或桥接节点：

- 可以新增节点
- 不能替换这三个对上层暴露的稳定名字

### 4. TF 合约

P1 驱动不能引入新的机器人根主干。

允许：

- 在 `{side}_end_effector` 下新增工具、夹爪、相机等末端 frame
- 在 `dual_base_plate` 或 `dual_crossbar` 下新增传感器 frame

不允许：

- 再引入 `map -> odom -> base_*` 作为同一机器人主干，除非架构层面正式升级并重审 MoveIt / TF 设计
- 用新的根 frame 替换 `world`
- 把驱动内部 frame 命名泄漏为第二套公开 frame 体系

### 5. Group 合约

P1 不得新增新的等价规划组来规避现有命名。

允许：

- 在后续阶段新增真正具备新语义的 group，例如单臂末端工具组、夹爪组、维护组

不允许：

- 新增 `left_manipulator` 作为 `left_arm` 的同义替代
- 新增 `both_arms` 作为 `dual_arms` 的同义替代

## P1 实施边界

P1 可以做：

- 新增硬件接口包
- 将 `mock_components/GenericSystem` 替换为真实硬件插件
- 接入总线、驱动、报文解析、状态回读
- 保持现有 MoveIt demo 上层接口不变

P1 不应该做：

- 重命名模型或控制器
- 重构 SRDF group 语义
- 重构 TF 主干
- 将仓库从“规划 demo + 驱动接入”直接扩展成“大一统真机系统”

## 进入 P1 的退出门槛

从当前静态检查角度看，进入 P1 的前置门槛已经满足。

P1 完成后，下一轮验收至少应新增：

- 真机 `ros2_control` 插件存在且可加载
- `left_arm_controller` / `right_arm_controller` 能接到真实硬件
- joint state 回读与命名保持完全一致
- 不破坏现有 `display_dual_urdf.launch.py` 与 `demo.launch.py` 的语义定位

## 相关文件

- [project_baseline.md](project_baseline.md)
- [dual_nero_description.xacro](../src/dual_nero_description/urdf/dual_nero_description.xacro)
- [nero_single_arm_macro.xacro](../src/dual_nero_description/urdf/nero_single_arm_macro.xacro)
- [dual_nero_description.srdf](../src/dual_nero_moveit_config/config/dual_nero_description.srdf)
- [ros2_controllers.yaml](../src/dual_nero_moveit_config/config/ros2_controllers.yaml)
- [moveit_controllers.yaml](../src/dual_nero_moveit_config/config/moveit_controllers.yaml)
