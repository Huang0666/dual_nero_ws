# dual_nero_driver

`dual_nero_driver` is the first non-invasive backend package for the dual-arm NERO robot.

Current scope:

- Adds a reusable driver backend abstraction for left and right arms.
- Adds a `pyAgxArm` backend wrapper with explicit error handling.
- Adds single-arm and dual-arm management classes.
- Adds an example parameter file and minimal test scripts.

This package does not do the following in this round:

- It does not add a real `ros2_control` hardware plugin.
- It does not replace `mock_components/GenericSystem`.
- It does not modify the existing MoveIt demo package.
- It does not change existing joint, controller, group, or TF naming.

Prerequisites:

- `pyAgxArm` must be installed for real hardware use.
- The CAN device must already be configured and activated before connecting.
- For Linux CAN, the upstream `pyAgxArm` documentation uses `comm="can"` and `interface="socketcan"`.
- If `dry_run: true` is used, the backend runs without `pyAgxArm` and only simulates local state updates.

Key contracts inherited from the repository baseline:

- Left arm joints: `left_joint1..7`
- Right arm joints: `right_joint1..7`
- Stable controller names: `left_arm_controller`, `right_arm_controller`, `joint_state_broadcaster`
- Stable groups: `left_arm`, `right_arm`, `dual_arms`
- Stable TF trunk: `world -> dual_base_plate -> dual_column -> dual_crossbar -> {left/right}_base_link -> ...`

Usage examples:

- Left arm read-only check:
  - `python src/dual_nero_driver/scripts/test_left_arm.py --config src/dual_nero_driver/config/arm_params.example.yaml`
- Right arm read-only check:
  - `python src/dual_nero_driver/scripts/test_right_arm.py --config src/dual_nero_driver/config/arm_params.example.yaml`
- Dual arm read-only check:
  - `python src/dual_nero_driver/scripts/test_dual_arm.py --config src/dual_nero_driver/config/arm_params.example.yaml`

Motion safety defaults:

- The scripts default to connect + enable + read state only.
- No motion command is sent unless `--execute` is provided.
- If `--execute` is used without a custom target, the script only generates a small offset motion from the current pose.
