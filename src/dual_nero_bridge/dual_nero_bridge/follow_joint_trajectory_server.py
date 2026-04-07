from __future__ import annotations

from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from trajectory_msgs.msg import JointTrajectoryPoint

from dual_nero_driver.safety import ensure_float_list, expected_joint_names

from .errors import BridgeArmUnavailableError, BridgeMotionRejectedError
from .logging_utils import log_abort, log_reject
from .preflight import PreflightChecker, PreflightResult
from .runtime import DualNeroBridgeRuntime


class SingleArmFollowJointTrajectoryServer:
    def __init__(
        self,
        node,
        runtime: DualNeroBridgeRuntime,
        preflight: PreflightChecker,
        *,
        side: str,
    ) -> None:
        self._node = node
        self._runtime = runtime
        self._preflight = preflight
        self._side = side
        self._joint_names = expected_joint_names(side)
        self._controller_name = f"{side}_arm_controller"
        self._action_server = ActionServer(
            node,
            FollowJointTrajectory,
            f"/{self._controller_name}/follow_joint_trajectory",
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
        )

    def destroy(self) -> None:
        self._action_server.destroy()

    def goal_callback(self, goal_request: FollowJointTrajectory.Goal):
        trajectory = goal_request.trajectory
        self._log_received_goal(trajectory.joint_names, len(trajectory.points))
        result = self._preflight.check_trajectory_goal(
            side=self._side,
            controller_name=self._controller_name,
            joint_names=trajectory.joint_names,
            points=trajectory.points,
        )
        self._log_preflight_result(result)
        if not result.ok:
            log_reject(
                self._node.get_logger(),
                self._controller_name,
                self._format_preflight_message(result),
            )
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def cancel_callback(self, _goal_handle):
        log_reject(
            self._node.get_logger(),
            self._controller_name,
            "Cancel requested; stopping the arm.",
        )
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        trajectory = goal_handle.request.trajectory
        result = self._preflight.check_trajectory_goal(
            side=self._side,
            controller_name=self._controller_name,
            joint_names=trajectory.joint_names,
            points=trajectory.points,
        )
        self._log_preflight_result(result)
        if not result.ok:
            goal_handle.abort()
            log_abort(
                self._node.get_logger(),
                self._controller_name,
                self._format_preflight_message(result),
            )
            return self._result(
                error_code=FollowJointTrajectory.Result.INVALID_GOAL,
                error_string=self._format_preflight_message(result),
            )

        point = trajectory.points[0]
        try:
            target = ensure_float_list(
                point.positions,
                expected_len=len(self._joint_names),
                label=f"{self._controller_name} point.positions",
            )
            self._move_side(target, wait=True)
            goal_handle.publish_feedback(self._build_feedback(target, point))
            goal_handle.succeed()
            return self._result(
                error_code=FollowJointTrajectory.Result.SUCCESSFUL,
                error_string=(
                    f"{self._controller_name} executed a single-point goal. "
                    "This bridge currently supports exactly one trajectory point per goal."
                ),
            )
        except (BridgeMotionRejectedError, BridgeArmUnavailableError) as exc:
            self._stop_side()
            goal_handle.abort()
            log_abort(self._node.get_logger(), self._controller_name, str(exc))
            return self._result(
                error_code=FollowJointTrajectory.Result.INVALID_GOAL,
                error_string=str(exc),
            )
        except Exception as exc:
            self._stop_side()
            goal_handle.abort()
            message = f"{self._controller_name} execution failed: {exc}"
            log_abort(self._node.get_logger(), self._controller_name, message)
            return self._result(
                error_code=FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED,
                error_string=message,
            )

    def _move_side(self, target: list[float], *, wait: bool) -> None:
        if self._side == "left":
            self._runtime.move_left(target, wait=wait)
            return
        self._runtime.move_right(target, wait=wait)

    def _stop_side(self) -> None:
        if self._side == "left":
            self._runtime.stop_left()
            return
        self._runtime.stop_right()

    def _build_feedback(
        self,
        target: list[float],
        point: JointTrajectoryPoint,
    ) -> FollowJointTrajectory.Feedback:
        feedback = FollowJointTrajectory.Feedback()
        feedback.joint_names = list(self._joint_names)
        feedback.desired = point
        _, actual_positions, _ = self._runtime.read_arm_joint_state(self._side)
        feedback.actual.positions = list(actual_positions)
        feedback.error.positions = [
            desired - actual
            for desired, actual in zip(target, actual_positions, strict=True)
        ]
        return feedback

    def _log_received_goal(self, joint_names, point_count: int) -> None:
        self._node.get_logger().info(
            f"[STATE][{self._controller_name}] received trajectory goal; "
            f"source=trajectory, "
            f"joint_names={list(joint_names)}, point_count={point_count}"
        )

    def _log_preflight_result(self, result: PreflightResult) -> None:
        self._node.get_logger().info(
            f"[STATE][{self._controller_name}] preflight result -> "
            f"ok={result.ok}, code={result.code}, message={result.message}"
        )

    @staticmethod
    def _format_preflight_message(result: PreflightResult) -> str:
        return f"{result.code}: {result.message}"

    @staticmethod
    def _result(*, error_code: int, error_string: str) -> FollowJointTrajectory.Result:
        result = FollowJointTrajectory.Result()
        result.error_code = error_code
        result.error_string = error_string
        return result
