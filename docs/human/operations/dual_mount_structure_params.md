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

## 2026-04-23 第一轮测量落地值

这些值已经写入 [dual_nero_description.xacro](/F:/github/dual_nero_ws/src/dual_nero_description/urdf/dual_nero_description.xacro) 的默认参数。

### 三角支撑框外包络

- `enable_support_frame = true`
- `support_frame_size = 230 x 10 x 300`
- `support_frame_joint_xyz = 0, 60, 490`

说明：

- 当前用一个近似包围盒代表三角支撑框，不建模中间镂空
- 这是为了先固定空间边界，不是为了外观还原

### 顶部横杆

- `crossbar_size = 250 x 40 x 40`
- `crossbar_joint_xyz = 0, 0, 810`

说明：

- 横杆中心点实测高度为 `850`
- 因为 `dual_column` link 原点在柱底，且柱底相对地面偏移为 `40`，所以代码中关节值为 `850 - 40 = 810`

### 左右安装盒

- 左安装盒尺寸：`70 x 20 x 95`
- 右安装盒尺寸：`70 x 20 x 95`
- 左安装盒中心：`130, 0, 850`
- 右安装盒中心：`-130, 0, 850`

说明：

- 安装盒位置在代码中是相对 `dual_crossbar` 中心表达
- 因此当前默认：
  - `left_mount_box_xyz = 0.13 0 0`
  - `right_mount_box_xyz = -0.13 0 0`

## 当前故意未写死的项

以下项在第一轮数据里不够自洽，当前没有直接固化到代码里：

- 左安装面中心相对左安装盒中心的偏移
- 右安装面中心相对右安装盒中心的偏移
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

- 结构尺寸已经足够支撑公共安装结构重构
- 但安装面偏移和朝向目前仍不可靠
- 如果现在把错误值写死，后面调试成本会更高

所以当前策略是：

1. 先固定公共安装结构
2. 再通过 `STEP + RViz/现场对照` 微调 mount pose

## 下一步要补的最小数据

只要补下面这组数据，就可以把双臂挂载位进一步收紧：

- 左安装面中心相对左安装盒中心：`dx dy dz`
- 右安装面中心相对右安装盒中心：`dx dy dz`
- 左安装面 `roll pitch yaw`
- 右安装面 `roll pitch yaw`

## 对应代码参数

当前需要优先关注的参数：

- `support_frame_size`
- `support_frame_joint_xyz`
- `crossbar_size`
- `crossbar_joint_xyz`
- `left_mount_box_size`
- `left_mount_box_xyz`
- `right_mount_box_size`
- `right_mount_box_xyz`
- `left_mount_xyz`
- `left_mount_rpy`
- `right_mount_xyz`
- `right_mount_rpy`
