# dual_nero_ws

`dual_nero_ws` 是一个面向 NERO 双臂机器人的 ROS 2 工作区。

当前仓库包含两个核心包：

- `dual_nero_description`：双臂 URDF/Xacro、模型网格、RViz 显示启动文件。
- `dual_nero_moveit_config`：MoveIt demo 配置、fake ros2_control、控制器映射。

当前仓库定位：

- 已支持 RViz 模型显示。
- 已支持 RViz/MoveIt 规划 demo。
- 尚不支持真机执行。

快速入口：

- 仅显示模型：`ros2 launch dual_nero_description display_dual_urdf.launch.py`
- MoveIt demo：`ros2 launch dual_nero_moveit_config demo.launch.py`

基线盘点与命名规范：

- [docs/project_baseline.md](docs/project_baseline.md)

核心命名约定：

- 关节：`left_joint1..7`、`right_joint1..7`
- 连杆：`left_base_link`、`left_link1..7`、`left_end_effector`，以及镜像的 `right_*`
- 控制器：`left_arm_controller`、`right_arm_controller`、`joint_state_broadcaster`
- TF 主干：`world -> dual_base_plate -> dual_column -> dual_crossbar -> {left/right}_base_link -> ...`

当前阶段未覆盖：

- 真机硬件接口插件
- 总线/驱动通信链路
- bringup、标定、诊断、执行类包
