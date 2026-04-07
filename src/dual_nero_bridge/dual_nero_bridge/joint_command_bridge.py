from __future__ import annotations

from trajectory_msgs.msg import JointTrajectory

from dual_nero_driver.safety import ensure_float_list, expected_joint_names

from .errors import BridgeArmUnavailableError, BridgeMotionRejectedError
from .logging_utils import log_reject, log_state
from .preflight import PreflightChecker
from .runtime import DualNeroBridgeRuntime


class JointCommandBridge:
    def __init__(
        self,
        node,
        runtime: DualNeroBridgeRuntime,
        preflight: PreflightChecker,
    ) -> None:
        self._node = node
        self._runtime = runtime
        self._preflight = preflight
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
            scope="left_arm",
            move_callback=self._runtime.move_left,
        )

    def _handle_right_command(self, msg: JointTrajectory) -> None:
        self._handle_single_arm_command(
            msg,
            expected_names=self._right_joint_names,
            source="right_arm_controller",
            scope="right_arm",
            move_callback=self._runtime.move_right,
        )

    def _handle_dual_command(self, msg: JointTrajectory) -> None:
        source = "dual_arms"
        try:
            self._log_received_command(source, msg)
            result = self._preflight.check_joint_command(
                scope="dual_arms",
                source_name=source,
                joint_names=msg.joint_names,
                points=msg.points,
            )
            self._log_preflight_result(source, result)
            if not result.ok:
                raise ValueError(self._format_preflight_message(result))
            point = msg.points[0]
            target = ensure_float_list(point.positions, expected_len=len(self._dual_joint_names), label=f"{source} target")
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
        scope: str,
        move_callback,
    ) -> None:
        try:
            self._log_received_command(source, msg)
            result = self._preflight.check_joint_command(
                scope=scope,
                source_name=source,
                joint_names=msg.joint_names,
                points=msg.points,
            )
            self._log_preflight_result(source, result)
            if not result.ok:
                raise ValueError(self._format_preflight_message(result))
            point = msg.points[0]
            target = ensure_float_list(point.positions, expected_len=len(expected_names), label=f"{source} target")
            move_callback(target, wait=False)
        except (BridgeMotionRejectedError, BridgeArmUnavailableError, ValueError) as exc:
            log_reject(self._node.get_logger(), source, str(exc))
        except Exception as exc:
            log_reject(self._node.get_logger(), source, f"joint command failed: {exc}")

    def _log_received_command(self, source: str, msg: JointTrajectory) -> None:
        log_state(
            self._node.get_logger(),
            source,
            f"received topic joint command; source=topic, joint_names={list(msg.joint_names)}, point_count={len(msg.points)}",
        )

    def _log_preflight_result(self, source: str, result) -> None:
        log_state(
            self._node.get_logger(),
            source,
            f"preflight result -> ok={result.ok}, code={result.code}, message={result.message}",
        )

    @staticmethod
    def _format_preflight_message(result) -> str:
        return f"{result.code}: {result.message}"
