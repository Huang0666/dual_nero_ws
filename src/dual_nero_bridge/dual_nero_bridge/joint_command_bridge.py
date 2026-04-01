from __future__ import annotations

from trajectory_msgs.msg import JointTrajectory

from dual_nero_driver.safety import ensure_float_list, expected_joint_names

from .errors import BridgeArmUnavailableError, BridgeMotionRejectedError
from .logging_utils import log_reject
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
        self._handle_single_arm_command(
            msg,
            expected_names=self._left_joint_names,
            source="left_arm_controller",
            move_callback=self._runtime.move_left,
        )

    def _handle_right_command(self, msg: JointTrajectory) -> None:
        self._handle_single_arm_command(
            msg,
            expected_names=self._right_joint_names,
            source="right_arm_controller",
            move_callback=self._runtime.move_right,
        )

    def _handle_dual_command(self, msg: JointTrajectory) -> None:
        source = "dual_arms"
        try:
            self._runtime.require_dual_motion_ready()
            point = self._extract_single_point(
                msg,
                expected_names=self._dual_joint_names,
                label=f"{source}/joint_command",
            )
            target = ensure_float_list(
                point.positions,
                expected_len=len(self._dual_joint_names),
                label=f"{source} target",
            )
            left_count = len(self._left_joint_names)
            self._runtime.move_both(
                target[:left_count],
                target[left_count:],
                wait=False,
            )
        except (BridgeMotionRejectedError, BridgeArmUnavailableError, ValueError) as exc:
            log_reject(self._node.get_logger(), source, str(exc))
        except Exception as exc:
            log_reject(self._node.get_logger(), source, f"joint command failed: {exc}")

    def _handle_single_arm_command(
        self,
        msg: JointTrajectory,
        *,
        expected_names: list[str],
        source: str,
        move_callback,
    ) -> None:
        side = "left" if source == "left_arm_controller" else "right"
        try:
            self._runtime.require_arm_ready_for_motion(side)
            point = self._extract_single_point(
                msg,
                expected_names=expected_names,
                label=f"{source}/joint_command",
            )
            target = ensure_float_list(
                point.positions,
                expected_len=len(expected_names),
                label=f"{source} target",
            )
            move_callback(target, wait=False)
        except (BridgeMotionRejectedError, BridgeArmUnavailableError, ValueError) as exc:
            log_reject(self._node.get_logger(), source, str(exc))
        except Exception as exc:
            log_reject(self._node.get_logger(), source, f"joint command failed: {exc}")

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
