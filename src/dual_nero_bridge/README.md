# dual_nero_bridge

`dual_nero_bridge` is the first real hardware execution bridge for `dual_nero_ws`.

Current scope:

- Reuses `dual_nero_driver` as the only backend that talks to `pyAgxArm`.
- Publishes real `/joint_states` for all 14 joints in a fixed repository contract order.
- Exposes direct joint command topics for left arm, right arm, and `dual_arms`.
- Exposes `FollowJointTrajectory` action servers at:
  - `/left_arm_controller/follow_joint_trajectory`
  - `/right_arm_controller/follow_joint_trajectory`

Why this package exists:

- The current repository has a Python hardware SDK (`pyAgxArm`) and a reusable Python backend in `dual_nero_driver`.
- This round does not add a native C++ `ros2_control` hardware plugin.
- Instead, P1 uses a real execution bridge so the repository can execute on hardware without breaking existing display and planning-demo semantics.

Important constraints:

- This package does not rename joints, groups, controllers, or the TF trunk.
- This package does not replace `dual_nero_moveit_config/demo.launch.py`.
- This package does not add a real `controller_manager`; the `FollowJointTrajectory` endpoints are a bridge/shim.
- The trajectory bridge is best-effort point-to-point execution, not a strict real-time controller.

Safety defaults:

- `allow_motion` defaults to `false`.
- `enable_on_start` defaults to `false`.
- All motion requests are validated for joint names, joint count, numeric payload shape, and configured joint limits.
- Direct command topics reject multi-point trajectories.

Runtime prerequisites:

- `pyAgxArm` must be installed.
- CAN interfaces must already be configured and activated.
- The hardware config should use `dry_run: false` for real execution mode.

Useful commands:

- Static contract check:
  - `ros2 run dual_nero_bridge contract_check`
- Real execution bridge only:
  - `ros2 launch dual_nero_bridge real_hardware_bridge.launch.py`
