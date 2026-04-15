# 下一步任务

## 当前阶段

- 当前阶段：`P4 双臂固定场景任务闭环`
- P1、P2、P3 主体已完成

## 优先级 A：固化仿真可用主线

- 保持默认 `with_gz_gui:=false` 的 server-only 路径
- 默认不再重复 `spawner` 已由 `gz_ros2_control` 激活的 controller
- 收口启动日志中的重复配置噪声
- 当前入口：[../operations/simulation_runbook.md](../operations/simulation_runbook.md)

## 优先级 B：继续做点位与空间建模

- 固定一组可重复回位的初始 / 安全位
- 明确左右臂在当前工位下的安全活动空间
- 再在该空间内定义预备位和任务位
- 当前入口：[../operations/hardware_alignment_checklist.md](../operations/hardware_alignment_checklist.md)

## 优先级 C：回到真机做阶段验收

- 在仿真里固化点位后，再回到真机执行 `dual_prep_sync`
- 用同一套任务入口做正式验收，不另起第二条链路

## 优先级 D：保留待办但当前不做

- USB-CAN 固定命名与批量映射稳定化
- `dual_arms` MoveIt 验证增强项
- MoveIt 厂家真实速度 / 加速度参数回填
