# P4 文档

## 作用

定义从“已验证执行链”进入“真实物理任务”的第一阶段目标，并记录当前 P4 的实际落地状态。

## 当前阶段定义

P4 不是继续做零散验证，而是开始做一个真正可重复的双臂固定场景任务闭环。

当前将 P4 正式定义为：

- `无视觉`
- `低风险`
- `固定工位`
- `双臂固定场景任务闭环`

## 当前已经完成的内容

- 已新增正式任务 CLI：`run_dual_arm_task`
- 已新增任务配置文件：`src/dual_nero_bridge/config/p4_tasks.yaml`
- 已建立 P4 正式执行路径：
  - 读取当前 `/joint_states`
  - 用 `dual_arms` 做统一规划
  - 提取统一轨迹末点
  - 分裂成左右臂单点 `FollowJointTrajectory` goal
  - 以任务级同步方式下发
- 已支持通过正式入口直接回固定安全位：
  - `ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync --target safe`
- 已修正真机执行中的两个工程问题：
  - 结果等待时间从通用 `timeout` 中拆分，不再轻易误判动作超时
  - `stop()` 不支持时只记告警，不再把 cleanup 异常放大成整条执行链崩溃

## 当前没有完成的内容

P4 现在卡住的不是底层链路，而是现场任务空间与点位定义。

具体表现为：

- MoveIt 可以规划
- preflight 也可能通过
- 但当前配置里的预备位/返回位与现场真实摆放空间存在冲突
- 继续盲试只会反复试错，不会沉淀成可复用任务

这说明当前问题已经从“链路是否打通”转向“任务空间是否定义正确”。

## 当前阶段结论

P4 到目前为止，已经完成了两件关键事情：

- 正式任务入口已经建立
- 当前主要缺口已经明确为“空间与点位建模”，而不是 bridge / preflight / MoveIt 主路径本身

所以当前暂停真机试验是正确动作。

阶段完成判断入口：

- [completion_checklist.md](completion_checklist.md)

## 当前正式任务入口

完整任务：

```bash
ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync
```

只回固定初始/安全位：

```bash
ros2 run dual_nero_bridge run_dual_arm_task --task dual_prep_sync --target safe
```

任务配置文件：

- `src/dual_nero_bridge/config/p4_tasks.yaml`

## 下一步不再怎么做

- 不再继续盲目放大动作幅度试错
- 不再在空间关系不清楚时直接定义预备位
- 不把当前空间冲突误判成底层链路失败

## 下一步要怎么做

下一步先转成“P4 点位与空间建模”：

- 固定一组可重复回位的初始/安全位
- 明确左右臂各自的可活动安全空间
- 再在该空间内定义预备位和任务位
- 最后回到真机做正式验收

## 与后续阶段的关系

- P4 解决“能不能稳定完成一个双臂固定场景任务”
- P5 再解决“双臂协调运动与避障”
- P6 再解决“视觉接入与简单抓取”
