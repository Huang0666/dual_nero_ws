# dual_nero_bringup

`dual_nero_bringup` is the operator-facing entry point for `real_hardware_execution`.

This package keeps the repository layers explicit:

- `dual_nero_description`: display
- `dual_nero_moveit_config`: planning-demo
- `dual_nero_bridge`: real hardware execution bridge
- `dual_nero_bringup`: launch and operator defaults for real hardware execution

Main entry point:

- `ros2 launch dual_nero_bringup real_hardware.launch.py`

Default behavior:

- Starts the real execution bridge.
- Starts `robot_state_publisher`.
- Can optionally start MoveIt `move_group`.
- Can optionally start the MoveIt RViz configuration.
- Keeps `allow_motion=false` by default so bringup starts in a safe idle mode.

This package does not change the existing display launch or planning-demo launch.
