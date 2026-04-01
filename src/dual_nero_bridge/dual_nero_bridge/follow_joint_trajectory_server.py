from __future__ import annotations

from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from trajectory_msgs.msg import JointTrajectoryPoint

from dual_nero_driver.safety import ensure_float_list, expected_joint_names

from .errors import (
    BridgeArmUnavailableError,
    BridgeMotionRejectedError,
    BridgeTrajectoryValidationError,
)
from .logging_utils import log_abort, log_reject
from .runtime import DualNeroBridgeRuntime


class SingleArmFollowJointTrajectoryServer:
    def __init__(
        self,
        node,
        runtime: DualNeroBridgeRuntime,
        *,
        side: str,
    ) -> None:
        self._node = node
        self._runtime = runtime
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
        try:
            self._validate_goal(goal_request)
        except (
            BridgeTrajectoryValidationError,
            BridgeMotionRejectedError,
            BridgeArmUnavailableError,
        ) as exc:
            log_reject(self._node.get_logger(), self._controller_name, str(exc))
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
        point = goal_handle.request.trajectory.points[0]
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

    def _validate_goal(self, goal_request: FollowJointTrajectory.Goal) -> None:
        trajectory = goal_request.trajectory
        self._validate_runtime_motion_prerequisites()

        if list(trajectory.joint_names) != self._joint_names:
            raise BridgeTrajectoryValidationError(
                f"joint_names must exactly match {self._joint_names}, "
                f"got {list(trajectory.joint_names)}."
            )
        if not trajectory.points:
            raise BridgeTrajectoryValidationError("trajectory must contain exactly one point.")
        if len(trajectory.points) != 1:
            raise BridgeTrajectoryValidationError(
                "this bridge currently supports exactly one trajectory point per goal; "
                f"received {len(trajectory.points)} points."
            )

        point = trajectory.points[0]
        ensure_float_list(
            point.positions,
            expected_len=len(self._joint_names),
            label=f"{self._controller_name} point.positions",
        )
        self._validate_optional_sequence(
            point.velocities,
            label=f"{self._controller_name} point.velocities",
        )
        self._validate_optional_sequence(
            point.accelerations,
            label=f"{self._controller_name} point.accelerations",
        )
        self._validate_optional_sequence(
            point.effort,
            label=f"{self._controller_name} point.effort",
        )
        self._validate_time_from_start(point)

    def _validate_runtime_motion_prerequisites(self) -> None:
        if self._side == "left":
            self._runtime.require_arm_ready_for_motion("left")
            return
        self._runtime.require_arm_ready_for_motion("right")

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

    def _validate_optional_sequence(self, values, *, label: str) -> None:
        if not values:
            return
        ensure_float_list(values, expected_len=len(self._joint_names), label=label)

    @staticmethod
    def _validate_time_from_start(point: JointTrajectoryPoint) -> None:
        sec = int(point.time_from_start.sec)
        nanosec = int(point.time_from_start.nanosec)
        if sec < 0 or nanosec < 0:
            raise BridgeTrajectoryValidationError(
                "time_from_start must be non-negative."
            )
        if nanosec >= 1_000_000_000:
            raise BridgeTrajectoryValidationError(
                "time_from_start.nanosec must be < 1_000_000_000."
            )

    @staticmethod
    def _result(*, error_code: int, error_string: str) -> FollowJointTrajectory.Result:
        result = FollowJointTrajectory.Result()
        result.error_code = error_code
        result.error_string = error_string
        return result
