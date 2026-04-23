# 双臂公共安装结构参数

## 作用

这份参数表只描述双臂公共安装结构，不描述单臂本体关节链。

当前设计边界：

- 单臂本体：继续复用 `nero_single_arm_macro.xacro`
- 公共安装结构：由 `dual_nero_description.xacro` 参数化
- 工位物体：不进入 robot URDF

## 当前口径

- 坐标原点 `O`：方形升降柱中心线在地面的投影点
- `+X`：指向左臂
- `+Y`：指向机器人正前方
- `+Z`：向上
- 长度单位：`mm`（代码中已转换为 `m`）

## 当前结构拓扑

当前简化结构已经按照片语义改成下面这套：

- `dual_column`：中间方形立柱
- `front_support_plate`：前侧三角支撑板的外包络
- `rear_support_plate`：后侧三角支撑板的外包络
- `dual_crossbar`：顶部横向安装梁
- `center_top_bracket`：顶部中间小立式支架
- `left_mount_plate`：左机械臂安装过渡板
- `right_mount_plate`：右机械臂安装过渡板

这意味着当前模型不再把三角结构错误地建成一块中间厚板。

## 2026-04-23 第一轮测量落地值

这些值已经写入 [dual_nero_description.xacro](/F:/github/dual_nero_ws/src/dual_nero_description/urdf/dual_nero_description.xacro) 的默认参数。

### 前后支撑板外包络

- `enable_support_plates = true`
- `support_plate_size = 230 x 10 x 300`
- `front_support_plate_joint_xyz = 0, 35, 490`
- `rear_support_plate_joint_xyz = 0, -35, 490`

说明：

- 当前把真实三角板简化为前后一对薄板的外包络
- 这样前视会接近真实“中间镂空”，侧视也更接近实物有前后厚度的结构
- 仍然没有建孔和斜边细节，只是先把结构关系建对

### 顶部横梁

- `crossbar_size = 250 x 40 x 40`
- `crossbar_joint_xyz = 0, 0, 810`

说明：

- 横梁中心点实测高度为 `850`
- 因为 `dual_column` link 原点在柱底，且柱底相对地面偏移为 `40`，所以代码里用 `850 - 40 = 810`

### 顶部中间支架

- `center_top_bracket_size = 30 x 30 x 80`
- `center_top_bracket_xyz = 0, 0, 60`

说明：

- 这是按照片提取的最小占位，不是精确零件尺寸
- 目标只是让顶部结构关系接近实物

### 左右安装板

- 左安装板尺寸：`25 x 10 x 95`
- 右安装板尺寸：`25 x 10 x 95`
- 左安装板中心：`130, 0, 850`
- 右安装板中心：`-130, 0, 850`

说明：

- 当前用“安装板”代替之前错误的“安装盒”抽象
- 安装板位置在代码中是相对 `dual_crossbar` 中心表达
- 因此当前默认：
  - `left_mount_plate_xyz = 0.13 0 0`
  - `right_mount_plate_xyz = -0.13 0 0`

## 当前故意未写死的项

以下项在第一轮数据里仍不够可靠，当前没有直接固化到代码里：

- 左安装面中心相对左安装板中心的偏移
- 右安装面中心相对右安装板中心的偏移
- 左安装面精确 `roll/pitch/yaw`
- 右安装面精确 `roll/pitch/yaw`
- 机械臂底座面相对安装面的精确偏移

当前处理方式：

- `left_mount_xyz = 0 0 0`
- `right_mount_xyz = 0 0 0`
- 保留现有单臂安装朝向：
  - 左：`0 -1.5708 3.14159`
  - 右：`0 -1.5708 0`

## 为什么这样处理

原因很简单：

- 结构拓扑已经足够支撑公共安装结构重构
- 但精确安装面偏移和朝向目前仍不可靠
- 如果现在把错误值写死，后面调试成本会更高

所以当前策略是：

1. 先把公共安装结构的层级关系建对
2. 再通过 `RViz/现场照片` 微调 mount pose

## 下一步要补的最小数据

只要补下面这组数据，就可以把双臂挂载位进一步收紧：

- 左安装面中心相对左安装板中心：`dx dy dz`
- 右安装面中心相对右安装板中心：`dx dy dz`
- 左安装面 `roll pitch yaw`
- 右安装面 `roll pitch yaw`

## 对应代码参数

当前需要优先关注的参数：

- `support_plate_size`
- `front_support_plate_joint_xyz`
- `rear_support_plate_joint_xyz`
- `crossbar_size`
- `crossbar_joint_xyz`
- `center_top_bracket_size`
- `center_top_bracket_xyz`
- `left_mount_plate_size`
- `left_mount_plate_xyz`
- `right_mount_plate_size`
- `right_mount_plate_xyz`
- `left_mount_xyz`
- `left_mount_rpy`
- `right_mount_xyz`
- `right_mount_rpy`
