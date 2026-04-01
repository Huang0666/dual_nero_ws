from __future__ import annotations

from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from trajectory_msgs.msg import JointTrajectoryPoint

from dual_nero_driver.safety import ensure_float_list, expected_joint_names

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
        if not self._runtime.allow_motion:
            self._node.get_logger().warning(
                f"Rejected {self._controller_name} goal because allow_motion=false."
            )
            return GoalResponse.REJECT
        try:
            self._validate_goal(goal_request)
        except Exception as exc:
            self._node.get_logger().error(
                f"Rejected {self._controller_name} goal: {exc}"
            )
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    @staticmethod
    def cancel_callback(_goal_handle):
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        trajectory = goal_handle.request.trajectory
        try:
            for point in trajectory.points:
                if goal_handle.is_cancel_requested:
                    self._stop_side()
                    goal_handle.canceled()
                    return self._result(
                        error_code=FollowJointTrajectory.Result.SUCCESSFUL,
                        error_string=f"{self._controller_name} goal canceled.",
                    )

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
                error_string=f"{self._controller_name} trajectory executed.",
            )
        except Exception as exc:
            self._stop_side()
            goal_handle.abort()
            return self._result(
                error_code=FollowJointTrajectory.Result.PATH_TOLERANCE_VIOLATED,
                error_string=str(exc),
            )

    def _validate_goal(self, goal_request: FollowJointTrajectory.Goal) -> None:
        trajectory = goal_request.trajectory
        if list(trajectory.joint_names) != self._joint_names:
            raise ValueError(
                f"{self._controller_name} joint_names must exactly match "
                f"{self._joint_names}, got {list(trajectory.joint_names)}."
            )
        if not trajectory.points:
            raise ValueError(f"{self._controller_name} trajectory must contain points.")
        for index, point in enumerate(trajectory.points):
            ensure_float_list(
                point.positions,
                expected_len=len(self._joint_names),
                label=f"{self._controller_name} point[{index}].positions",
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
        _, positions, _ = self._runtime.read_joint_state()
        joint_count = len(self._joint_names)
        if self._side == "left":
            actual_positions = positions[:joint_count]
        else:
            actual_positions = positions[joint_count:]
        feedback.actual.positions = list(actual_positions)
        feedback.error.positions = [
            desired - actual
            for desired, actual in zip(target, actual_positions, strict=True)
        ]
        return feedback

    @staticmethod
    def _result(*, error_code: int, error_string: str) -> FollowJointTrajectory.Result:
        result = FollowJointTrajectory.Result()
        result.error_code = error_code
        result.error_string = error_string
        return result
