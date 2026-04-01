from __future__ import annotations

from trajectory_msgs.msg import JointTrajectory

from dual_nero_driver.safety import ensure_float_list, expected_joint_names

from .runtime import DualNeroBridgeRuntime


class JointCommandBridge:
    def __init__(self, node, runtime: DualNeroBridgeRuntime) -> None:
        self._node = node
        self._runtime = runtime
        self._left_joint_names = expected_joint_names("left")
        self._right_joint_names = expected_joint_names("right")
        self._dual_joint_names = self._left_joint_names + self._right_joint_names
        self._left_subscription = node.create_subscription(
            JointTrajectory,
            "/left_arm_controller/joint_command",
            self._handle_left_command,
            10,
        )
        self._right_subscription = node.create_subscription(
            JointTrajectory,
            "/right_arm_controller/joint_command",
            self._handle_right_command,
            10,
        )
        self._dual_subscription = node.create_subscription(
            JointTrajectory,
            "/dual_arms/joint_command",
            self._handle_dual_command,
            10,
        )

    def _handle_left_command(self, msg: JointTrajectory) -> None:
        try:
            point = self._extract_single_point(
                msg,
                expected_names=self._left_joint_names,
                label="left_arm_controller/joint_command",
            )
            target = ensure_float_list(
                point.positions,
                expected_len=len(self._left_joint_names),
                label="left_arm_controller target",
            )
            self._runtime.move_left(target, wait=False)
        except Exception as exc:
            self._node.get_logger().error(f"Rejected left arm command: {exc}")

    def _handle_right_command(self, msg: JointTrajectory) -> None:
        try:
            point = self._extract_single_point(
                msg,
                expected_names=self._right_joint_names,
                label="right_arm_controller/joint_command",
            )
            target = ensure_float_list(
                point.positions,
                expected_len=len(self._right_joint_names),
                label="right_arm_controller target",
            )
            self._runtime.move_right(target, wait=False)
        except Exception as exc:
            self._node.get_logger().error(f"Rejected right arm command: {exc}")

    def _handle_dual_command(self, msg: JointTrajectory) -> None:
        try:
            point = self._extract_single_point(
                msg,
                expected_names=self._dual_joint_names,
                label="dual_arms/joint_command",
            )
            target = ensure_float_list(
                point.positions,
                expected_len=len(self._dual_joint_names),
                label="dual_arms target",
            )
            left_count = len(self._left_joint_names)
            self._runtime.move_both(
                target[:left_count],
                target[left_count:],
                wait=False,
            )
        except Exception as exc:
            self._node.get_logger().error(f"Rejected dual arm command: {exc}")

    @staticmethod
    def _extract_single_point(
        msg: JointTrajectory,
        *,
        expected_names: list[str],
        label: str,
    ):
        if list(msg.joint_names) != expected_names:
            raise ValueError(
                f"{label} joint_names must exactly match {expected_names}, "
                f"got {list(msg.joint_names)}."
            )
        if len(msg.points) != 1:
            raise ValueError(
                f"{label} must contain exactly one trajectory point, got {len(msg.points)}."
            )
        return msg.points[0]
