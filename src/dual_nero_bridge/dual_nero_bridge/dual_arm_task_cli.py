from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from control_msgs.action import FollowJointTrajectory
from moveit_msgs.msg import Constraints, JointConstraint, MoveItErrorCodes, RobotState
from moveit_msgs.srv import GetMotionPlan
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from dual_nero_driver.safety import ensure_float_list

from .moveit_validation_cli import (
    GROUP_JOINTS,
    LEFT_ARM_JOINTS,
    RIGHT_ARM_JOINTS,
    _read_moveit_error_details,
    follow_joint_trajectory_error_name,
)


@dataclass(slots=True)
class DualArmPose:
    left_positions: list[float]
    right_positions: list[float]

    def as_dual_positions(self) -> list[float]:
        return list(self.left_positions) + list(self.right_positions)


@dataclass(slots=True)
class DualArmTaskDefinition:
    task_name: str
    group_name: str
    planning_mode: str
    execution_mode: str
    allow_return_to_safe: bool
    safe_positions: DualArmPose
    prep_positions: DualArmPose
    return_positions: DualArmPose


@dataclass(slots=True)
class DualArmTaskPreview:
    task_name: str
    group_name: str
    planning_mode: str
    execution_mode: str
    current_positions: list[float]
    safe_positions: list[float]
    prep_positions: list[float]
    return_positions: list[float]
    plan_service: str

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


@dataclass(slots=True)
class MoveItPlanSummary:
    task_name: str
    stage: str
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
class ArmGoalSummary:
    arm: str
    target_name: str
    accepted: bool
    error_code: int | None
    error_name: str
    error_string: str


@dataclass(slots=True)
class TaskExecutionSummary:
    task_name: str
    stage: str
    mode: str
    overall_status: str
    left_arm: ArmGoalSummary
    right_arm: ArmGoalSummary

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


@dataclass(slots=True)
class TaskFinalSummary:
    task_name: str
    overall_status: str
    target_mode: str
    primary_stage: str
    secondary_stage: str

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


class DualArmTaskClient(Node):
    def __init__(
        self,
        *,
        task: DualArmTaskDefinition,
        timeout_sec: float,
        result_timeout_sec: float,
        result_timeout_margin_sec: float,
        plan_service_name: str,
        planning_time_sec: float,
        planning_attempts: int,
        goal_tolerance: float,
        velocity_scaling: float,
        acceleration_scaling: float,
        pipeline_id: str,
        planner_id: str,
    ) -> None:
        super().__init__(f"{task.task_name}_task_client")
        self.task = task
        self.timeout_sec = float(timeout_sec)
        self.result_timeout_sec = float(result_timeout_sec)
        self.result_timeout_margin_sec = float(result_timeout_margin_sec)
        self.plan_service_name = plan_service_name
        self.planning_time_sec = float(planning_time_sec)
        self.planning_attempts = int(planning_attempts)
        self.goal_tolerance = float(goal_tolerance)
        self.velocity_scaling = float(velocity_scaling)
        self.acceleration_scaling = float(acceleration_scaling)
        self.pipeline_id = pipeline_id
        self.planner_id = planner_id
        self.joint_names = list(GROUP_JOINTS[task.group_name])
        self._joint_state_msg: JointState | None = None

        self.create_subscription(JointState, "/joint_states", self._joint_state_callback, 10)
        self._plan_client = self.create_client(GetMotionPlan, self.plan_service_name)
        self._arm_action_clients = {
            "left": ActionClient(
                self,
                FollowJointTrajectory,
                "/left_arm_controller/follow_joint_trajectory",
            ),
            "right": ActionClient(
                self,
                FollowJointTrajectory,
                "/right_arm_controller/follow_joint_trajectory",
            ),
        }

    def build_preview(self) -> DualArmTaskPreview:
        current_positions = self._wait_for_current_positions()
        return DualArmTaskPreview(
            task_name=self.task.task_name,
            group_name=self.task.group_name,
            planning_mode=self.task.planning_mode,
            execution_mode=self.task.execution_mode,
            current_positions=current_positions,
            safe_positions=self.task.safe_positions.as_dual_positions(),
            prep_positions=self.task.prep_positions.as_dual_positions(),
            return_positions=self.task.return_positions.as_dual_positions(),
            plan_service=self.plan_service_name,
        )

    def plan_to_positions(self, *, stage: str, target_positions: list[float]) -> GetMotionPlan.Response:
        if not self._plan_client.wait_for_service(timeout_sec=self.timeout_sec):
            raise RuntimeError(
                f"MoveIt plan service {self.plan_service_name} was not available within "
                f"{self.timeout_sec:.1f}s."
            )

        request = GetMotionPlan.Request()
        motion_plan_request = request.motion_plan_request
        motion_plan_request.group_name = self.task.group_name
        motion_plan_request.num_planning_attempts = self.planning_attempts
        motion_plan_request.allowed_planning_time = self.planning_time_sec
        motion_plan_request.max_velocity_scaling_factor = self.velocity_scaling
        motion_plan_request.max_acceleration_scaling_factor = self.acceleration_scaling
        motion_plan_request.pipeline_id = self.pipeline_id
        motion_plan_request.planner_id = self.planner_id
        motion_plan_request.start_state = self._build_start_state()
        motion_plan_request.goal_constraints = [
            self._build_goal_constraints(
                stage=stage,
                target_positions=target_positions,
            )
        ]

        future = self._plan_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=self.timeout_sec)
        response = future.result()
        if response is None:
            raise RuntimeError(
                f"MoveIt plan request to {self.plan_service_name} timed out or returned no response."
            )
        return response

    def summarize_plan(self, *, stage: str, response: GetMotionPlan.Response) -> MoveItPlanSummary:
        motion_plan_response = response.motion_plan_response
        error_details = _read_moveit_error_details(motion_plan_response.error_code)
        return MoveItPlanSummary(
            task_name=self.task.task_name,
            stage=stage,
            group_name=self.task.group_name,
            error_code=int(error_details["code"]),
            error_name=str(error_details["name"]),
            message=str(error_details["message"]),
            source=str(error_details["source"]),
            planning_time=float(motion_plan_response.planning_time),
            trajectory_point_count=len(motion_plan_response.trajectory.joint_trajectory.points),
        )

    def execute_dual_arm_stage(
        self,
        *,
        stage: str,
        response: GetMotionPlan.Response,
    ) -> TaskExecutionSummary:
        trajectory = response.motion_plan_response.trajectory.joint_trajectory
        if not trajectory.points:
            raise RuntimeError(f"{stage} trajectory is empty.")

        left_goal, right_goal = self._split_dual_final_point(trajectory)
        left_target = "/left_arm_controller/follow_joint_trajectory"
        right_target = "/right_arm_controller/follow_joint_trajectory"

        if not self._arm_action_clients["left"].wait_for_server(timeout_sec=self.timeout_sec):
            raise RuntimeError(
                f"Bridge action server {left_target} was not available within {self.timeout_sec:.1f}s."
            )
        if not self._arm_action_clients["right"].wait_for_server(timeout_sec=self.timeout_sec):
            raise RuntimeError(
                f"Bridge action server {right_target} was not available within {self.timeout_sec:.1f}s."
            )

        left_future = self._arm_action_clients["left"].send_goal_async(left_goal)
        right_future = self._arm_action_clients["right"].send_goal_async(right_goal)
        left_handle = self._wait_for_future(left_future, f"{stage} left-arm goal request")
        right_handle = self._wait_for_future(right_future, f"{stage} right-arm goal request")

        left_accepted = bool(left_handle and left_handle.accepted)
        right_accepted = bool(right_handle and right_handle.accepted)
        if not left_accepted or not right_accepted:
            self._cancel_if_possible(left_handle)
            self._cancel_if_possible(right_handle)
            return TaskExecutionSummary(
                task_name=self.task.task_name,
                stage=stage,
                mode=self.task.execution_mode,
                overall_status="failed",
                left_arm=ArmGoalSummary(
                    arm="left",
                    target_name=left_target,
                    accepted=left_accepted,
                    error_code=None,
                    error_name="REJECTED" if not left_accepted else "CANCELLED",
                    error_string="" if left_accepted else f"{left_target} rejected the goal.",
                ),
                right_arm=ArmGoalSummary(
                    arm="right",
                    target_name=right_target,
                    accepted=right_accepted,
                    error_code=None,
                    error_name="REJECTED" if not right_accepted else "CANCELLED",
                    error_string="" if right_accepted else f"{right_target} rejected the goal.",
                ),
            )

        left_result_future = left_handle.get_result_async()
        right_result_future = right_handle.get_result_async()
        result_timeout = self._result_wait_timeout_sec(trajectory)
        left_result_handle = self._wait_for_future(
            left_result_future,
            f"{stage} left-arm result",
            timeout_sec=result_timeout,
        )
        right_result_handle = self._wait_for_future(
            right_result_future,
            f"{stage} right-arm result",
            timeout_sec=result_timeout,
        )
        left_result = left_result_handle.result
        right_result = right_result_handle.result
        left_code = int(left_result.error_code)
        right_code = int(right_result.error_code)

        overall_status = (
            "success"
            if left_code == FollowJointTrajectory.Result.SUCCESSFUL
            and right_code == FollowJointTrajectory.Result.SUCCESSFUL
            else "failed"
        )
        return TaskExecutionSummary(
            task_name=self.task.task_name,
            stage=stage,
            mode=self.task.execution_mode,
            overall_status=overall_status,
            left_arm=ArmGoalSummary(
                arm="left",
                target_name=left_target,
                accepted=True,
                error_code=left_code,
                error_name=follow_joint_trajectory_error_name(left_code),
                error_string=str(left_result.error_string),
            ),
            right_arm=ArmGoalSummary(
                arm="right",
                target_name=right_target,
                accepted=True,
                error_code=right_code,
                error_name=follow_joint_trajectory_error_name(right_code),
                error_string=str(right_result.error_string),
            ),
        )

    def _wait_for_current_positions(self) -> list[float]:
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
                f"/joint_states is missing expected joints for {self.task.group_name}: {missing}"
            )
        return [float(name_to_position[joint_name]) for joint_name in self.joint_names]

    def _build_start_state(self) -> RobotState:
        if self._joint_state_msg is None:
            raise RuntimeError("Cannot build MoveIt start_state without /joint_states.")
        robot_state = RobotState()
        robot_state.joint_state = deepcopy(self._joint_state_msg)
        robot_state.is_diff = False
        return robot_state

    def _build_goal_constraints(self, *, stage: str, target_positions: list[float]) -> Constraints:
        constraints = Constraints()
        constraints.name = f"{self.task.task_name}_{stage}_goal"
        constraints.joint_constraints = [
            self._build_joint_constraint(joint_name, target_position)
            for joint_name, target_position in zip(self.joint_names, target_positions, strict=True)
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

    def _split_dual_final_point(
        self,
        trajectory: JointTrajectory,
    ) -> tuple[FollowJointTrajectory.Goal, FollowJointTrajectory.Goal]:
        final_point = trajectory.points[-1]
        point_data = {
            joint_name: index
            for index, joint_name in enumerate(trajectory.joint_names)
        }
        missing = [
            joint_name
            for joint_name in (LEFT_ARM_JOINTS + RIGHT_ARM_JOINTS)
            if joint_name not in point_data
        ]
        if missing:
            raise RuntimeError(f"dual_arms final point is missing joints: {missing}")

        left_goal = FollowJointTrajectory.Goal()
        left_goal.trajectory = JointTrajectory()
        left_goal.trajectory.joint_names = list(LEFT_ARM_JOINTS)
        left_goal.trajectory.points = [self._build_arm_point(final_point, point_data, LEFT_ARM_JOINTS)]

        right_goal = FollowJointTrajectory.Goal()
        right_goal.trajectory = JointTrajectory()
        right_goal.trajectory.joint_names = list(RIGHT_ARM_JOINTS)
        right_goal.trajectory.points = [self._build_arm_point(final_point, point_data, RIGHT_ARM_JOINTS)]
        return left_goal, right_goal

    def _build_arm_point(
        self,
        final_point: JointTrajectoryPoint,
        point_data: dict[str, int],
        joint_names: list[str],
    ) -> JointTrajectoryPoint:
        point = JointTrajectoryPoint()
        point.positions = [float(final_point.positions[point_data[joint_name]]) for joint_name in joint_names]
        if final_point.velocities:
            point.velocities = [
                float(final_point.velocities[point_data[joint_name]]) for joint_name in joint_names
            ]
        if final_point.accelerations:
            point.accelerations = [
                float(final_point.accelerations[point_data[joint_name]]) for joint_name in joint_names
            ]
        if final_point.effort:
            point.effort = [float(final_point.effort[point_data[joint_name]]) for joint_name in joint_names]
        point.time_from_start = final_point.time_from_start
        return point

    def _wait_for_future(self, future, label: str, *, timeout_sec: float | None = None):
        wait_timeout_sec = self.timeout_sec if timeout_sec is None else float(timeout_sec)
        rclpy.spin_until_future_complete(self, future, timeout_sec=wait_timeout_sec)
        result = future.result()
        if result is None:
            raise RuntimeError(f"{label} timed out after {wait_timeout_sec:.1f}s.")
        return result

    def _result_wait_timeout_sec(self, trajectory: JointTrajectory) -> float:
        if not trajectory.points:
            return self.result_timeout_sec
        final_point = trajectory.points[-1]
        planned_duration_sec = float(final_point.time_from_start.sec) + (
            float(final_point.time_from_start.nanosec) / 1e9
        )
        return max(self.result_timeout_sec, planned_duration_sec + self.result_timeout_margin_sec)

    def _cancel_if_possible(self, goal_handle) -> None:
        if goal_handle is None or not getattr(goal_handle, "accepted", False):
            return
        cancel_future = goal_handle.cancel_goal_async()
        rclpy.spin_until_future_complete(self, cancel_future, timeout_sec=1.0)

    def _joint_state_callback(self, msg: JointState) -> None:
        self._joint_state_msg = msg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a formal P4 dual-arm task through MoveIt dual_arms planning and bridge single-point execution.",
    )
    parser.add_argument(
        "--task",
        default="dual_prep_sync",
        help="Task name defined in the P4 task YAML.",
    )
    parser.add_argument(
        "--task-config",
        default=str(_default_task_config_path()),
        help="Path to the P4 task YAML.",
    )
    parser.add_argument(
        "--target",
        choices=["full", "prep", "safe", "return"],
        default="full",
        help=(
            "Execution target. 'full' means move to prep_positions and then optionally "
            "return_positions. 'safe' moves directly to safe_positions."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for /joint_states, service readiness, and action readiness.",
    )
    parser.add_argument(
        "--result-timeout",
        type=float,
        default=30.0,
        help="Minimum timeout in seconds when waiting for each arm action result.",
    )
    parser.add_argument(
        "--result-timeout-margin",
        type=float,
        default=15.0,
        help="Extra seconds added on top of the planned trajectory duration when waiting for action results.",
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
    return parser


def load_task_definition(path: str | Path, task_name: str) -> DualArmTaskDefinition:
    yaml_path = Path(path)
    if not yaml_path.is_file():
        raise FileNotFoundError(f"P4 task config file does not exist: {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"P4 task config must be a mapping: {yaml_path}")

    tasks = data.get("tasks")
    if not isinstance(tasks, dict):
        raise RuntimeError(f"P4 task config must contain a 'tasks' mapping: {yaml_path}")

    task_data = tasks.get(task_name)
    if not isinstance(task_data, dict):
        known = sorted(tasks)
        raise RuntimeError(f"P4 task {task_name!r} was not found. Known tasks: {known}")

    normalized_task_name = str(task_data.get("task_name", task_name))
    group_name = str(task_data.get("group_name", ""))
    planning_mode = str(task_data.get("planning_mode", ""))
    execution_mode = str(task_data.get("execution_mode", ""))
    allow_return_to_safe = bool(task_data.get("allow_return_to_safe", True))
    if group_name != "dual_arms":
        raise RuntimeError(f"{normalized_task_name} must use group_name=dual_arms, got {group_name!r}.")
    if planning_mode != "dual_arms":
        raise RuntimeError(
            f"{normalized_task_name} must use planning_mode=dual_arms, got {planning_mode!r}."
        )
    if execution_mode != "sync":
        raise RuntimeError(
            f"{normalized_task_name} must use execution_mode=sync, got {execution_mode!r}."
        )

    safe_positions = _load_dual_arm_pose(task_data, field_name="safe_positions")
    prep_positions = _load_dual_arm_pose(task_data, field_name="prep_positions")
    return_positions = _load_dual_arm_pose(task_data, field_name="return_positions", default=safe_positions)
    return DualArmTaskDefinition(
        task_name=normalized_task_name,
        group_name=group_name,
        planning_mode=planning_mode,
        execution_mode=execution_mode,
        allow_return_to_safe=allow_return_to_safe,
        safe_positions=safe_positions,
        prep_positions=prep_positions,
        return_positions=return_positions,
    )


def _load_dual_arm_pose(
    task_data: dict[str, Any],
    *,
    field_name: str,
    default: DualArmPose | None = None,
) -> DualArmPose:
    if field_name not in task_data:
        if default is not None:
            return default
        raise RuntimeError(f"Task config is missing {field_name}.")
    value = task_data[field_name]
    if not isinstance(value, dict):
        raise RuntimeError(f"{field_name} must be a mapping with left/right lists.")

    left_positions = ensure_float_list(
        value.get("left", []),
        expected_len=len(LEFT_ARM_JOINTS),
        label=f"{field_name}.left",
    )
    right_positions = ensure_float_list(
        value.get("right", []),
        expected_len=len(RIGHT_ARM_JOINTS),
        label=f"{field_name}.right",
    )
    return DualArmPose(left_positions=left_positions, right_positions=right_positions)


def _default_task_config_path() -> Path:
    return Path(get_package_share_directory("dual_nero_bridge")) / "config" / "p4_tasks.yaml"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        task_definition = load_task_definition(args.task_config, args.task)
    except Exception as exc:
        print(f"run_dual_arm_task failed: {exc}", file=sys.stderr)
        return 2

    rclpy.init()
    node = DualArmTaskClient(
        task=task_definition,
        timeout_sec=args.timeout,
        result_timeout_sec=args.result_timeout,
        result_timeout_margin_sec=args.result_timeout_margin,
        plan_service_name=args.plan_service,
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

        primary_stage_name, primary_target_positions = _resolve_primary_stage(
            task_definition=task_definition,
            target=args.target,
        )
        primary_response = node.plan_to_positions(
            stage=primary_stage_name,
            target_positions=primary_target_positions,
        )
        primary_plan_summary = node.summarize_plan(stage=primary_stage_name, response=primary_response)
        print(primary_plan_summary.to_pretty_json())
        if primary_plan_summary.error_code != MoveItErrorCodes.SUCCESS:
            return 1

        primary_execution_summary = node.execute_dual_arm_stage(
            stage=primary_stage_name,
            response=primary_response,
        )
        print(primary_execution_summary.to_pretty_json())
        if primary_execution_summary.overall_status != "success":
            return 1

        secondary_stage_status = "skipped"
        if args.target == "full" and task_definition.allow_return_to_safe:
            return_response = node.plan_to_positions(
                stage="return",
                target_positions=task_definition.return_positions.as_dual_positions(),
            )
            return_plan_summary = node.summarize_plan(stage="return", response=return_response)
            print(return_plan_summary.to_pretty_json())
            if return_plan_summary.error_code != MoveItErrorCodes.SUCCESS:
                return 1

            return_execution_summary = node.execute_dual_arm_stage(stage="return", response=return_response)
            print(return_execution_summary.to_pretty_json())
            if return_execution_summary.overall_status != "success":
                return 1
            secondary_stage_status = "success"

        print(
            TaskFinalSummary(
                task_name=task_definition.task_name,
                overall_status="success",
                target_mode=args.target,
                primary_stage="success",
                secondary_stage=secondary_stage_status,
            ).to_pretty_json()
        )
        return 0
    except Exception as exc:
        print(f"run_dual_arm_task failed: {exc}", file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


def _resolve_primary_stage(
    *,
    task_definition: DualArmTaskDefinition,
    target: str,
) -> tuple[str, list[float]]:
    if target == "prep":
        return "prep", task_definition.prep_positions.as_dual_positions()
    if target == "safe":
        return "safe", task_definition.safe_positions.as_dual_positions()
    if target == "return":
        return "return", task_definition.return_positions.as_dual_positions()
    return "prep", task_definition.prep_positions.as_dual_positions()


if __name__ == "__main__":
    raise SystemExit(main())
