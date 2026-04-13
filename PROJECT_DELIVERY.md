# Project Delivery

## 作用

本文件用于记录“当前阶段的交付入口、交付边界与交付确认方式”。

## 当前交付入口

- P2：preflight 已进入 action/topic 正式入口
- P3：恢复 SOP 与 MoveIt 主路径验证已完成
- P4：双臂固定场景任务入口

## P4 交付边界

- 任务：`dual_prep_sync`
- 入口：`ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync`
- 规划：`dual_arms` 统一规划
- 执行：分裂为左右臂单点 goal，通过 bridge action 下发
- 同步语义：任务级同步（同一时间下发，统一结果判定）

## 当前不交付

- 双臂协同约束与避障能力（P5）
- 视觉接入与抓取（P6）
- USB-CAN 固定命名（P3-C 暂缓）

## 验收方式（摘要）

- 能稳定多次执行 `dual_prep_sync`
- 失败时由 preflight gate 拦截并返回可读错误码
- 失败后的恢复流程按 P3-A SOP 执行
