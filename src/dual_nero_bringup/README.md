# dual_nero_bringup

`dual_nero_bringup` 是 `real_hardware_execution` 的 operator-facing 入口。

## 入口

- `ros2 launch dual_nero_bringup real_hardware.launch.py`

## 默认行为

- 启动 `dual_nero_bridge`
- 启动 `robot_state_publisher`
- 可选启动 `move_group`
- 可选启动 MoveIt RViz
- 默认保持：
  - `allow_motion=false`
  - `enable_on_start=false`

这意味着默认是 **连接 + 读状态 + 空闲** 模式，不做动作。

## P1.1 收口说明

- `real_hardware.launch.py` 的语义不变，仍然是真机入口
- 文档明确了 bridge 当前只支持单点 `FollowJointTrajectory` goal
- 文档补充了 read-only check 和最小动作测试方式
- 文档补充了 `allow_motion` / `enable_on_start` 的前提关系

## 推荐启动方式

### Read-only

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=false enable_on_start:=false
```

### 最小动作测试

```bash
ros2 launch dual_nero_bringup real_hardware.launch.py allow_motion:=true enable_on_start:=true
```

## 当前限制

- `enable_on_start=false` 时，bridge 不会自动 enable
- 动作命令在该模式下会被显式拒绝
- bridge 仍然不是 native `ros2_control` plugin

详细步骤见：[../../docs/p1_smoke_test_report.md](../../docs/p1_smoke_test_report.md)
