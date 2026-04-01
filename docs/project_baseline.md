# dual_nero_ws 基线盘点

## 仓库定位

当前仓库是一个“双臂模型 + MoveIt demo”工作区，不是真机执行工作区。

当前能力分层：

- `display`：已完成
- `planning_demo`：已完成
- `real_hardware_execution`：未完成

## 仓库结构图

```text
dual_nero_ws/
|-- README.md
`-- src/
    |-- dual_nero_description/
    |   |-- launch/
    |   |   `-- display_dual_urdf.launch.py
    |   |-- meshes/
    |   |   |-- *.STL / *.dae
    |   |-- rviz/
    |   |   `-- dual_nero.rviz
    |   |-- urdf/
    |   |   |-- dual_nero_description.xacro
    |   |   `-- nero_single_arm_macro.xacro
    |   |-- frames_*.gv / frames_*.pdf
    |   |-- CMakeLists.txt
    |   `-- package.xml
    `-- dual_nero_moveit_config/
        |-- config/
        |   |-- dual_nero_description.srdf
        |   |-- dual_nero_description.urdf.xacro
        |   |-- dual_nero_description.ros2_control.xacro
        |   |-- initial_positions.yaml
        |   |-- joint_limits.yaml
        |   |-- kinematics.yaml
        |   |-- moveit.rviz
        |   |-- moveit_controllers.yaml
        |   |-- ros2_controllers.yaml
        |   `-- sensors_3d.yaml
        |-- launch/
        |   |-- demo.launch.py
        |   |-- move_group.launch.py
        |   |-- moveit_rviz.launch.py
        |   |-- rsp.launch.py
        |   |-- spawn_controllers.launch.py
        |   `-- other generated MoveIt launch files
        |-- .setup_assistant
        |-- CMakeLists.txt
        `-- package.xml
```

## 已完成 / 未完成

### 已完成

- 双臂 URDF/Xacro 已存在，左右臂统一使用 `left_` / `right_` 前缀。
- RViz 纯显示启动链已存在，可直接查看模型。
- MoveIt 的 SRDF、运动学、控制器映射、demo launch 已存在。
- fake `ros2_control` 已接入，足以支撑规划 demo 和控制器连线。
- 描述包中的 TF 主干已经采用 `world -> dual_base_plate -> dual_column -> dual_crossbar -> ...`。

### 未完成

- 还没有真机硬件包。
- 还没有自定义 `hardware_interface::SystemInterface` 实现。
- 还没有现场总线、串口、EtherCAT、CAN 或厂商驱动接入。
- 还没有 bringup、标定、诊断、执行类包。
- 还没有有效的 TF 运行验证产物；`frames_*.gv` 不能作为当前可运行证据。

### 占位 / 模板内容

- `dual_nero_moveit_config/config/dual_nero_description.ros2_control.xacro` 仍使用 `mock_components/GenericSystem`。
- `dual_nero_moveit_config/config/sensors_3d.yaml` 目前明确保持为空，等待真实 3D 传感器接入。
- `dual_nero_moveit_config` 仍然保留了 MoveIt Setup Assistant 生成包的结构，只是仓库定位已在此文档中明确。

## 命名规范

后续开发默认冻结以下命名，不再引入第二套同义命名。

### 关节命名

- 左臂：`left_joint1` 到 `left_joint7`
- 右臂：`right_joint1` 到 `right_joint7`

### 连杆命名

- 根与结构件：`world`、`dual_base_plate`、`dual_column`、`dual_crossbar`
- 左臂连杆：`left_base_link`、`left_link1` 到 `left_link7`、`left_end_effector`
- 右臂连杆：`right_base_link`、`right_link1` 到 `right_link7`、`right_end_effector`

### 固定关节命名

- 安装固定关节：`left_mount_joint`、`right_mount_joint`
- 末端固定关节：`left_end_effector_joint`、`right_end_effector_joint`

### 规划组命名

- `left_arm`
- `right_arm`
- `dual_arms`

### 控制器命名

- `left_arm_controller`
- `right_arm_controller`
- `joint_state_broadcaster`

### TF 命名

- 权威 TF 主干：`world -> dual_base_plate -> dual_column -> dual_crossbar`
- 每条手臂从 `{side}_base_link` 继续向下展开
- 新增 frame 时必须继续沿用同一前缀体系，禁止再引入别名根节点

### 禁止引入的别名

禁止新增：

- `l_` / `r_`
- `arm_left` / `arm_right`
- `leftarm` / `rightarm`
- 同一条手臂、关节、控制器、topic、namespace 的第二套命名体系

### 后续真机阶段的 namespace 规则

未来新增的硬件侧 topic、action、service、namespace 继续统一使用：

- `left_arm_*`
- `right_arm_*`

## 验证规则

- 新功能提交时，必须声明自己属于 `display`、`planning_demo`、`real_hardware_execution` 中的哪一层。
- URDF 关节名、SRDF 规划组、控制器 YAML 必须保持一一对应。
- 未来的真机支持必须进入新的 bringup/hardware 包，而不是悄悄覆盖当前 fake demo 配置。
