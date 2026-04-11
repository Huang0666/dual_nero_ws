from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from dataclasses import asdict, dataclass

import rclpy
from moveit_msgs.action import ExecuteTrajectory
from moveit_msgs.msg import Constraints, JointConstraint, MoveItErrorCodes, RobotState
from moveit_msgs.srv import GetMotionPlan
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState

LEFT_ARM_JOINTS = [
    "left_joint1",
    "left_joint2",
    "left_joint3",
    "left_joint4",
    "left_joint5",
    "left_joint6",
    "left_joint7",
]
RIGHT_ARM_JOINTS = [
    "right_joint1",
    "right_joint2",
    "right_joint3",
    "right_joint4",
    "right_joint5",
    "right_joint6",
    "right_joint7",
]
GROUP_JOINTS = {
    "left_arm": LEFT_ARM_JOINTS,
    "right_arm": RIGHT_ARM_JOINTS,
    "dual_arms": LEFT_ARM_JOINTS + RIGHT_ARM_JOINTS,
}
GROUP_CONTROLLERS = {
    "left_arm": ["left_arm_controller"],
    "right_arm": ["right_arm_controller"],
    "dual_arms": ["left_arm_controller", "right_arm_controller"],
}


@dataclass(slots=True)
class MoveItValidationPreview:
    group_name: str
    joint_names: list[str]
    current_positions: list[float]
    target_positions: list[float]
    plan_service: str
    execute_action: str
    controller_names: list[str]

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


@dataclass(slots=True)
class MoveItPlanSummary:
    group_name: str
    error_code: int
    error_name: str
    message: str
    source: str
    planning_time: float
    trajectory_point_count: int

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


@dataclass(slots=True)
class MoveItExecutionSummary:
    group_name: str
    error_code: int
    error_name: str
    message: str
    source: str
    state: str

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


class MoveItValidationClient(Node):
    def __init__(
        self,
        *,
        group_name: str,
        delta: float,
        timeout_sec: float,
        plan_service_name: str,
        execute_action_name: str,
        planning_time_sec: float,
        planning_attempts: int,
        goal_tolerance: float,
        velocity_scaling: float,
        acceleration_scaling: float,
        pipeline_id: str,
        planner_id: str,
    ) -> None:
        super().__init__(f"{group_name}_moveit_validation_client")
        self.group_name = group_name
        self.delta = float(delta)
        self.timeout_sec = float(timeout_sec)
        self.plan_service_name = plan_service_name
        self.execute_action_name = execute_action_name
        self.planning_time_sec = float(planning_time_sec)
        self.planning_attempts = int(planning_attempts)
        self.goal_tolerance = float(goal_tolerance)
        self.velocity_scaling = float(velocity_scaling)
        self.acceleration_scaling = float(acceleration_scaling)
        self.pipeline_id = pipeline_id
        self.planner_id = planner_id
        self.joint_names = list(GROUP_JOINTS[group_name])
        self.controller_names = list(GROUP_CONTROLLERS[group_name])
        self._joint_state_msg: JointState | None = None

        self.create_subscription(JointState, "/joint_states", self._joint_state_callback, 10)
        self._plan_client = self.create_client(GetMotionPlan, self.plan_service_name)
        self._execute_client = ActionClient(
            self,
            ExecuteTrajectory,
            self.execute_action_name,
        )

    def build_preview(self) -> MoveItValidationPreview:
        current = self._wait_for_group_positions()
        target = list(current)
        if self.group_name == "dual_arms":
            target[0] += self.delta
            target[len(LEFT_ARM_JOINTS)] -= self.delta
        else:
            target[0] += self.delta
        return MoveItValidationPreview(
            group_name=self.group_name,
            joint_names=list(self.joint_names),
            current_positions=current,
            target_positions=target,
            plan_service=self.plan_service_name,
            execute_action=self.execute_action_name,
            controller_names=list(self.controller_names),
        )

    def plan(self, preview: MoveItValidationPreview) -> GetMotionPlan.Response:
        if not self._plan_client.wait_for_service(timeout_sec=self.timeout_sec):
            raise RuntimeError(
                f"MoveIt plan service {self.plan_service_name} was not available within "
                f"{self.timeout_sec:.1f}s."
            )

        request = GetMotionPlan.Request()
        motion_plan_request = request.motion_plan_request
        motion_plan_request.group_name = preview.group_name
        motion_plan_request.num_planning_attempts = self.planning_attempts
        motion_plan_request.allowed_planning_time = self.planning_time_sec
        motion_plan_request.max_velocity_scaling_factor = self.velocity_scaling
        motion_plan_request.max_acceleration_scaling_factor = self.acceleration_scaling
        motion_plan_request.pipeline_id = self.pipeline_id
        motion_plan_request.planner_id = self.planner_id
        motion_plan_request.start_state = self._build_start_state()
        motion_plan_request.goal_constraints = [self._build_goal_constraints(preview)]

        future = self._plan_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=self.timeout_sec)
        response = future.result()
        if response is None:
            raise RuntimeError(
                f"MoveIt plan request to {self.plan_service_name} timed out or returned no response."
            )
        return response

    def summarize_plan(self, response: GetMotionPlan.Response) -> MoveItPlanSummary:
        motion_plan_response = response.motion_plan_response
        error_code = motion_plan_response.error_code
        return MoveItPlanSummary(
            group_name=self.group_name,
            error_code=int(error_code.val),
            error_name=moveit_error_name(int(error_code.val)),
            message=error_code.message,
            source=error_code.source,
            planning_time=float(motion_plan_response.planning_time),
            trajectory_point_count=len(motion_plan_response.trajectory.joint_trajectory.points),
        )

    def execute(self, response: GetMotionPlan.Response) -> MoveItExecutionSummary:
        if not self._execute_client.wait_for_server(timeout_sec=self.timeout_sec):
            raise RuntimeError(
                f"MoveIt execute action {self.execute_action_name} was not available within "
                f"{self.timeout_sec:.1f}s."
            )

        goal = ExecuteTrajectory.Goal()
        goal.trajectory = response.motion_plan_response.trajectory
        goal.controller_names = list(self.controller_names)

        send_goal_future = self._execute_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_goal_future, timeout_sec=self.timeout_sec)
        goal_handle = send_goal_future.result()
        if goal_handle is None:
            raise RuntimeError(f"ExecuteTrajectory goal request to {self.execute_action_name} timed out.")
        if not goal_handle.accepted:
            raise RuntimeError(f"ExecuteTrajectory goal was rejected by {self.execute_action_name}.")

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=self.timeout_sec)
        result_handle = result_future.result()
        if result_handle is None:
            raise RuntimeError(f"ExecuteTrajectory result wait on {self.execute_action_name} timed out.")

        result = result_handle.result
        error_code = result.error_code
        return MoveItExecutionSummary(
            group_name=self.group_name,
            error_code=int(error_code.val),
            error_name=moveit_error_name(int(error_code.val)),
            message=error_code.message,
            source=error_code.source,
            state=result.state,
        )

    def _build_start_state(self) -> RobotState:
        if self._joint_state_msg is None:
            raise RuntimeError("Cannot build MoveIt start_state without /joint_states.")
        robot_state = RobotState()
        robot_state.joint_state = deepcopy(self._joint_state_msg)
        robot_state.is_diff = False
        return robot_state

    def _build_goal_constraints(self, preview: MoveItValidationPreview) -> Constraints:
        constraints = Constraints()
        constraints.name = f"{preview.group_name}_validation_goal"
        constraints.joint_constraints = [
            self._build_joint_constraint(joint_name, target_position)
            for joint_name, target_position in zip(
                preview.joint_names,
                preview.target_positions,
                strict=True,
            )
        ]
        return constraints

    def _build_joint_constraint(self, joint_name: str, target_position: float) -> JointConstraint:
        constraint = JointConstraint()
        constraint.joint_name = joint_name
        constraint.position = float(target_position)
        constraint.tolerance_above = self.goal_tolerance
        constraint.tolerance_below = self.goal_tolerance
        constraint.weight = 1.0
        return constraint

    def _wait_for_group_positions(self) -> list[float]:
        deadline = self.get_clock().now().nanoseconds + int(self.timeout_sec * 1e9)
        while self._joint_state_msg is None and self.get_clock().now().nanoseconds < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
        if self._joint_state_msg is None:
            raise RuntimeError(
                "Did not receive /joint_states in time. Start real_hardware.launch.py first."
            )

        name_to_position = {
            name: position
            for name, position in zip(
                self._joint_state_msg.name,
                self._joint_state_msg.position,
                strict=True,
            )
        }
        missing = [joint_name for joint_name in self.joint_names if joint_name not in name_to_position]
        if missing:
            raise RuntimeError(
                f"/joint_states is missing expected joints for {self.group_name}: {missing}"
            )
        return [float(name_to_position[joint_name]) for joint_name in self.joint_names]

    def _joint_state_callback(self, msg: JointState) -> None:
        self._joint_state_msg = msg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Plan and optionally execute a minimal MoveIt trajectory against the real bridge.",
    )
    parser.add_argument(
        "--group",
        choices=sorted(GROUP_JOINTS),
        default="left_arm",
        help="MoveIt group to validate.",
    )
    parser.add_argument(
        "--delta",
        type=float,
        default=0.03,
        help="Small joint offset used to derive the target from the current /joint_states sample.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for /joint_states, service readiness, action readiness, and results.",
    )
    parser.add_argument(
        "--planning-time",
        type=float,
        default=3.0,
        help="MoveIt allowed_planning_time in seconds.",
    )
    parser.add_argument(
        "--planning-attempts",
        type=int,
        default=1,
        help="MoveIt num_planning_attempts.",
    )
    parser.add_argument(
        "--goal-tolerance",
        type=float,
        default=0.001,
        help="Tolerance applied to each joint goal constraint.",
    )
    parser.add_argument(
        "--velocity-scaling",
        type=float,
        default=0.2,
        help="MoveIt max_velocity_scaling_factor.",
    )
    parser.add_argument(
        "--acceleration-scaling",
        type=float,
        default=0.2,
        help="MoveIt max_acceleration_scaling_factor.",
    )
    parser.add_argument(
        "--pipeline-id",
        default="",
        help="Optional MoveIt pipeline_id override.",
    )
    parser.add_argument(
        "--planner-id",
        default="",
        help="Optional MoveIt planner_id override.",
    )
    parser.add_argument(
        "--plan-service",
        default="/plan_kinematic_path",
        help="MoveIt planning service name.",
    )
    parser.add_argument(
        "--execute-action",
        default="/execute_trajectory",
        help="MoveIt execute trajectory action name.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually send ExecuteTrajectory after the plan succeeds.",
    )
    return parser


def moveit_error_name(code: int) -> str:
    for name, value in vars(MoveItErrorCodes).items():
        if name.isupper() and isinstance(value, int) and value == code:
            return name
    return f"UNKNOWN_{code}"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rclpy.init()
    node = MoveItValidationClient(
        group_name=args.group,
        delta=args.delta,
        timeout_sec=args.timeout,
        plan_service_name=args.plan_service,
        execute_action_name=args.execute_action,
        planning_time_sec=args.planning_time,
        planning_attempts=args.planning_attempts,
        goal_tolerance=args.goal_tolerance,
        velocity_scaling=args.velocity_scaling,
        acceleration_scaling=args.acceleration_scaling,
        pipeline_id=args.pipeline_id,
        planner_id=args.planner_id,
    )

    try:
        preview = node.build_preview()
        print(preview.to_pretty_json())

        plan_response = node.plan(preview)
        plan_summary = node.summarize_plan(plan_response)
        print(plan_summary.to_pretty_json())
        if plan_summary.error_code != MoveItErrorCodes.SUCCESS:
            return 1

        if not args.execute:
            print(
                "Plan computed successfully. Re-run with --execute to send ExecuteTrajectory."
            )
            return 0

        execute_summary = node.execute(plan_response)
        print(execute_summary.to_pretty_json())
        return 0 if execute_summary.error_code == MoveItErrorCodes.SUCCESS else 1
    except Exception as exc:
        print(f"validate_moveit_pipeline failed: {exc}", file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
