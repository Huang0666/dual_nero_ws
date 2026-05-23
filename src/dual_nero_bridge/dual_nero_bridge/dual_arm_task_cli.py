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
from moveit_msgs.srv import ApplyPlanningScene, GetMotionPlan
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
from .planning_scene_utils import build_remove_all_scene, build_scene_diff, load_scene_profile


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
    default_execution_mode: str
    default_failure_policy: str
    scene_profile: str | None
    safe_positions: DualArmPose


@dataclass(slots=True)
class TaskStageDefinition:
    name: str
    execution_mode: str
    failure_policy: str
    scene_profile: str | None
    target_positions: DualArmPose

    def as_dual_positions(self) -> list[float]:
        return self.target_positions.as_dual_positions()


@dataclass(slots=True)
class LoadedDualArmTask:
    definition: DualArmTaskDefinition
    stages: list[TaskStageDefinition]


@dataclass(slots=True)
class DualArmTaskPreview:
    task_name: str
    group_name: str
    planning_mode: str
    default_execution_mode: str
    default_failure_policy: str
    current_positions: list[float]
    safe_positions: list[float]
    scene_profile: str | None
    stages: list[dict[str, Any]]
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
    completed_stages: list[str]
    failed_stage: str | None
    safe_return_status: str

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


class DualArmTaskClient(Node):
    def __init__(
        self,
        *,
        task: LoadedDualArmTask,
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
        scene_config_path: str | None,
    ) -> None:
        super().__init__(f"{task.definition.task_name}_task_client")
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
        self.scene_config_path = scene_config_path
        self.joint_names = list(GROUP_JOINTS[task.definition.group_name])
        self._joint_state_msg: JointState | None = None
        self._active_scene_profile: str | None = None
        self._managed_scene_object_ids: set[str] = set()

        self.create_subscription(JointState, "/joint_states", self._joint_state_callback, 10)
        self._plan_client = self.create_client(GetMotionPlan, self.plan_service_name)
        self._apply_scene_client = self.create_client(ApplyPlanningScene, "/apply_planning_scene")
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
            task_name=self.task.definition.task_name,
            group_name=self.task.definition.group_name,
            planning_mode=self.task.definition.planning_mode,
            default_execution_mode=self.task.definition.default_execution_mode,
            default_failure_policy=self.task.definition.default_failure_policy,
            current_positions=current_positions,
            safe_positions=self.task.definition.safe_positions.as_dual_positions(),
            scene_profile=self.task.definition.scene_profile,
            stages=[
                {
                    "name": stage.name,
                    "execution_mode": stage.execution_mode,
                    "failure_policy": stage.failure_policy,
                    "scene_profile": stage.scene_profile,
                    "target_positions": stage.as_dual_positions(),
                }
                for stage in self.task.stages
            ],
            plan_service=self.plan_service_name,
        )

    def read_current_positions(self) -> list[float]:
        """Return current group joint positions in task joint order."""
        return self._wait_for_current_positions()

    def plan_to_positions(
        self,
        *,
        stage: str,
        target_positions: list[float],
        scene_profile: str | None,
    ) -> GetMotionPlan.Response:
        self._ensure_scene_profile(scene_profile)
        if not self._plan_client.wait_for_service(timeout_sec=self.timeout_sec):
            raise RuntimeError(
                f"MoveIt plan service {self.plan_service_name} was not available within "
                f"{self.timeout_sec:.1f}s."
            )

        request = GetMotionPlan.Request()
        motion_plan_request = request.motion_plan_request
        motion_plan_request.group_name = self.task.definition.group_name
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
            task_name=self.task.definition.task_name,
            stage=stage,
            group_name=self.task.definition.group_name,
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
        stage: TaskStageDefinition,
        response: GetMotionPlan.Response,
    ) -> TaskExecutionSummary:
        trajectory = response.motion_plan_response.trajectory.joint_trajectory
        if not trajectory.points:
            raise RuntimeError(f"{stage.name} trajectory is empty.")

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

        result_timeout = self._result_wait_timeout_sec(trajectory)
        goal_map = {"left": left_goal, "right": right_goal}
        target_map = {"left": left_target, "right": right_target}
        if stage.execution_mode == "sync":
            left_summary, right_summary = self._execute_sync_goals(
                stage_name=stage.name,
                goals=goal_map,
                targets=target_map,
                result_timeout=result_timeout,
            )
        elif stage.execution_mode == "serial_left_first":
            left_summary, right_summary = self._execute_serial_goals(
                stage_name=stage.name,
                goals=goal_map,
                targets=target_map,
                result_timeout=result_timeout,
                first_arm="left",
            )
        else:
            left_summary, right_summary = self._execute_serial_goals(
                stage_name=stage.name,
                goals=goal_map,
                targets=target_map,
                result_timeout=result_timeout,
                first_arm="right",
            )

        overall_status = (
            "success"
            if left_summary.error_code == FollowJointTrajectory.Result.SUCCESSFUL
            and right_summary.error_code == FollowJointTrajectory.Result.SUCCESSFUL
            else "failed"
        )
        return TaskExecutionSummary(
            task_name=self.task.definition.task_name,
            stage=stage.name,
            mode=stage.execution_mode,
            overall_status=overall_status,
            left_arm=left_summary,
            right_arm=right_summary,
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
                f"/joint_states is missing expected joints for {self.task.definition.group_name}: {missing}"
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
        constraints.name = f"{self.task.definition.task_name}_{stage}_goal"
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

    def _execute_sync_goals(
        self,
        *,
        stage_name: str,
        goals: dict[str, FollowJointTrajectory.Goal],
        targets: dict[str, str],
        result_timeout: float,
    ) -> tuple[ArmGoalSummary, ArmGoalSummary]:
        left_future = self._arm_action_clients["left"].send_goal_async(goals["left"])
        right_future = self._arm_action_clients["right"].send_goal_async(goals["right"])
        left_handle = self._wait_for_future(left_future, f"{stage_name} left-arm goal request")
        right_handle = self._wait_for_future(right_future, f"{stage_name} right-arm goal request")

        left_accepted = bool(left_handle and left_handle.accepted)
        right_accepted = bool(right_handle and right_handle.accepted)
        if not left_accepted or not right_accepted:
            self._cancel_if_possible(left_handle)
            self._cancel_if_possible(right_handle)
            return (
                self._goal_rejected_summary("left", targets["left"]) if not left_accepted
                else self._goal_cancelled_summary("left", targets["left"]),
                self._goal_rejected_summary("right", targets["right"]) if not right_accepted
                else self._goal_cancelled_summary("right", targets["right"]),
            )

        left_result = self._wait_for_future(
            left_handle.get_result_async(),
            f"{stage_name} left-arm result",
            timeout_sec=result_timeout,
        ).result
        right_result = self._wait_for_future(
            right_handle.get_result_async(),
            f"{stage_name} right-arm result",
            timeout_sec=result_timeout,
        ).result
        return (
            self._result_summary("left", targets["left"], left_result),
            self._result_summary("right", targets["right"], right_result),
        )

    def _execute_serial_goals(
        self,
        *,
        stage_name: str,
        goals: dict[str, FollowJointTrajectory.Goal],
        targets: dict[str, str],
        result_timeout: float,
        first_arm: str,
    ) -> tuple[ArmGoalSummary, ArmGoalSummary]:
        second_arm = "right" if first_arm == "left" else "left"
        first_summary = self._execute_single_goal(
            arm=first_arm,
            stage_name=stage_name,
            goal=goals[first_arm],
            target_name=targets[first_arm],
            result_timeout=result_timeout,
        )
        if first_summary.error_code != FollowJointTrajectory.Result.SUCCESSFUL:
            second_summary = self._not_executed_summary(
                second_arm,
                targets[second_arm],
                reason=f"{first_arm} arm failed before serial handoff.",
            )
        else:
            second_summary = self._execute_single_goal(
                arm=second_arm,
                stage_name=stage_name,
                goal=goals[second_arm],
                target_name=targets[second_arm],
                result_timeout=result_timeout,
            )

        if first_arm == "left":
            return first_summary, second_summary
        return second_summary, first_summary

    def _execute_single_goal(
        self,
        *,
        arm: str,
        stage_name: str,
        goal: FollowJointTrajectory.Goal,
        target_name: str,
        result_timeout: float,
    ) -> ArmGoalSummary:
        goal_future = self._arm_action_clients[arm].send_goal_async(goal)
        goal_handle = self._wait_for_future(goal_future, f"{stage_name} {arm}-arm goal request")
        if not goal_handle or not goal_handle.accepted:
            return self._goal_rejected_summary(arm, target_name)

        result = self._wait_for_future(
            goal_handle.get_result_async(),
            f"{stage_name} {arm}-arm result",
            timeout_sec=result_timeout,
        ).result
        return self._result_summary(arm, target_name, result)

    def _goal_rejected_summary(self, arm: str, target_name: str) -> ArmGoalSummary:
        return ArmGoalSummary(
            arm=arm,
            target_name=target_name,
            accepted=False,
            error_code=None,
            error_name="REJECTED",
            error_string=f"{target_name} rejected the goal.",
        )

    def _goal_cancelled_summary(self, arm: str, target_name: str) -> ArmGoalSummary:
        return ArmGoalSummary(
            arm=arm,
            target_name=target_name,
            accepted=True,
            error_code=None,
            error_name="CANCELLED",
            error_string="Goal was cancelled because the paired arm was rejected.",
        )

    def _not_executed_summary(self, arm: str, target_name: str, *, reason: str) -> ArmGoalSummary:
        return ArmGoalSummary(
            arm=arm,
            target_name=target_name,
            accepted=False,
            error_code=None,
            error_name="NOT_EXECUTED",
            error_string=reason,
        )

    def _result_summary(self, arm: str, target_name: str, result) -> ArmGoalSummary:
        result_code = int(result.error_code)
        return ArmGoalSummary(
            arm=arm,
            target_name=target_name,
            accepted=True,
            error_code=result_code,
            error_name=follow_joint_trajectory_error_name(result_code),
            error_string=str(result.error_string),
        )

    def _ensure_scene_profile(self, scene_profile: str | None) -> None:
        if scene_profile == self._active_scene_profile:
            return
        if scene_profile is None:
            if self._managed_scene_object_ids:
                self._apply_planning_scene(build_remove_all_scene(self._managed_scene_object_ids))
                self._managed_scene_object_ids = set()
            self._active_scene_profile = None
            return
        if not self.scene_config_path:
            raise RuntimeError(
                f"Scene profile {scene_profile!r} was requested but no --scene-config was provided."
            )
        profile = load_scene_profile(self.scene_config_path, scene_profile)
        planning_scene = build_scene_diff(
            profile=profile,
            previous_object_ids=self._managed_scene_object_ids,
        )
        self._apply_planning_scene(planning_scene)
        self._managed_scene_object_ids = set(profile.object_ids)
        self._active_scene_profile = scene_profile

    def _apply_planning_scene(self, planning_scene) -> None:
        if not self._apply_scene_client.wait_for_service(timeout_sec=self.timeout_sec):
            raise RuntimeError(
                f"MoveIt apply_planning_scene service was not available within {self.timeout_sec:.1f}s."
            )
        request = ApplyPlanningScene.Request()
        request.scene = planning_scene
        future = self._apply_scene_client.call_async(request)
        response = self._wait_for_future(future, "apply planning scene")
        if not response.success:
            raise RuntimeError("MoveIt rejected the planning scene update.")

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
        description="Run a dual-arm task through MoveIt dual_arms planning and bridge execution.",
    )
    parser.add_argument(
        "--task",
        default="dual_prep_sync",
        help="Task name defined in the task YAML.",
    )
    parser.add_argument(
        "--task-config",
        default=str(_default_task_config_path()),
        help="Path to the task YAML.",
    )
    parser.add_argument(
        "--target",
        default="full",
        help=(
            "Execution target. 'full' runs the task stage list in order. Any explicit stage name "
            "runs only that stage. 'safe' always moves directly to safe_positions."
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
    parser.add_argument(
        "--scene-config",
        default=str(_default_scene_config_path()),
        help="Path to the planning-scene YAML. Only used when a task or stage declares scene_profile.",
    )
    return parser


def load_task_definition(path: str | Path, task_name: str) -> LoadedDualArmTask:
    yaml_path = Path(path)
    if not yaml_path.is_file():
        raise FileNotFoundError(f"Task config file does not exist: {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"Task config must be a mapping: {yaml_path}")

    tasks = data.get("tasks")
    if not isinstance(tasks, dict):
        raise RuntimeError(f"Task config must contain a 'tasks' mapping: {yaml_path}")

    task_data = tasks.get(task_name)
    if not isinstance(task_data, dict):
        known = sorted(tasks)
        raise RuntimeError(f"Task {task_name!r} was not found. Known tasks: {known}")

    normalized_task_name = str(task_data.get("task_name", task_name))
    group_name = str(task_data.get("group_name", ""))
    planning_mode = str(task_data.get("planning_mode", ""))
    default_execution_mode = _normalize_execution_mode(
        task_data.get("execution_mode", "sync"),
        label=f"{normalized_task_name}.execution_mode",
    )
    default_failure_policy = _normalize_failure_policy(
        task_data.get("failure_policy", "abort"),
        label=f"{normalized_task_name}.failure_policy",
    )
    scene_profile = _normalize_optional_string(task_data.get("scene_profile"))
    if group_name != "dual_arms":
        raise RuntimeError(f"{normalized_task_name} must use group_name=dual_arms, got {group_name!r}.")
    if planning_mode != "dual_arms":
        raise RuntimeError(
            f"{normalized_task_name} must use planning_mode=dual_arms, got {planning_mode!r}."
        )

    safe_positions = _load_dual_arm_pose(task_data, field_name="safe_positions")
    stages_data = task_data.get("stages")
    if isinstance(stages_data, list):
        stages = _load_stage_definitions(
            stages_data,
            task_name=normalized_task_name,
            default_execution_mode=default_execution_mode,
            default_failure_policy=default_failure_policy,
            default_scene_profile=scene_profile,
        )
    else:
        stages = _load_legacy_stage_definitions(
            task_data,
            task_name=normalized_task_name,
            default_execution_mode=default_execution_mode,
            default_failure_policy=default_failure_policy,
            default_scene_profile=scene_profile,
            safe_positions=safe_positions,
        )

    return LoadedDualArmTask(
        definition=DualArmTaskDefinition(
            task_name=normalized_task_name,
            group_name=group_name,
            planning_mode=planning_mode,
            default_execution_mode=default_execution_mode,
            default_failure_policy=default_failure_policy,
            scene_profile=scene_profile,
            safe_positions=safe_positions,
        ),
        stages=stages,
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


def _load_stage_definitions(
    stages_data: list[Any],
    *,
    task_name: str,
    default_execution_mode: str,
    default_failure_policy: str,
    default_scene_profile: str | None,
) -> list[TaskStageDefinition]:
    if not stages_data:
        raise RuntimeError(f"{task_name} must define at least one stage.")

    stages: list[TaskStageDefinition] = []
    seen_names: set[str] = set()
    for index, stage_data in enumerate(stages_data, start=1):
        if not isinstance(stage_data, dict):
            raise RuntimeError(f"{task_name}.stages[{index}] must be a mapping.")
        stage_name = str(stage_data.get("name", "")).strip()
        if not stage_name:
            raise RuntimeError(f"{task_name}.stages[{index}] is missing name.")
        if stage_name in seen_names:
            raise RuntimeError(f"{task_name} has duplicate stage name {stage_name!r}.")
        seen_names.add(stage_name)
        positions = _load_dual_arm_pose(stage_data, field_name="positions")
        stages.append(
            TaskStageDefinition(
                name=stage_name,
                execution_mode=_normalize_execution_mode(
                    stage_data.get("execution_mode", default_execution_mode),
                    label=f"{task_name}.stages[{stage_name}].execution_mode",
                ),
                failure_policy=_normalize_failure_policy(
                    stage_data.get("failure_policy", default_failure_policy),
                    label=f"{task_name}.stages[{stage_name}].failure_policy",
                ),
                scene_profile=_normalize_optional_string(stage_data.get("scene_profile", default_scene_profile)),
                target_positions=positions,
            )
        )
    return stages


def _load_legacy_stage_definitions(
    task_data: dict[str, Any],
    *,
    task_name: str,
    default_execution_mode: str,
    default_failure_policy: str,
    default_scene_profile: str | None,
    safe_positions: DualArmPose,
) -> list[TaskStageDefinition]:
    prep_positions = _load_dual_arm_pose(task_data, field_name="prep_positions")
    allow_return_to_safe = bool(task_data.get("allow_return_to_safe", True))
    return_positions = _load_dual_arm_pose(task_data, field_name="return_positions", default=safe_positions)
    stages = [
        TaskStageDefinition(
            name="prep",
            execution_mode=default_execution_mode,
            failure_policy=default_failure_policy,
            scene_profile=default_scene_profile,
            target_positions=prep_positions,
        )
    ]
    if allow_return_to_safe:
        stages.append(
            TaskStageDefinition(
                name="return",
                execution_mode=default_execution_mode,
                failure_policy="abort",
                scene_profile=default_scene_profile,
                target_positions=return_positions,
            )
        )
    return stages


def _normalize_execution_mode(value: Any, *, label: str) -> str:
    normalized = str(value).strip()
    allowed = {"sync", "serial_left_first", "serial_right_first"}
    if normalized not in allowed:
        raise RuntimeError(f"{label} must be one of {sorted(allowed)}, got {normalized!r}.")
    return normalized


def _normalize_failure_policy(value: Any, *, label: str) -> str:
    normalized = str(value).strip()
    allowed = {"abort", "return_safe"}
    if normalized not in allowed:
        raise RuntimeError(f"{label} must be one of {sorted(allowed)}, got {normalized!r}.")
    return normalized


def _normalize_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _default_task_config_path() -> Path:
    return Path(get_package_share_directory("dual_nero_bridge")) / "config" / "p4_tasks.yaml"


def _default_scene_config_path() -> Path:
    return Path(get_package_share_directory("dual_nero_bridge")) / "config" / "p5_scene_sim.yaml"


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
        scene_config_path=args.scene_config,
    )

    try:
        preview = node.build_preview()
        print(preview.to_pretty_json())

        selected_stages = _resolve_requested_stages(
            task_definition=task_definition,
            target=args.target,
        )
        completed_stages: list[str] = []
        safe_return_status = "not_requested"
        for stage in selected_stages:
            stage_response = node.plan_to_positions(
                stage=stage.name,
                target_positions=stage.as_dual_positions(),
                scene_profile=stage.scene_profile,
            )
            stage_plan_summary = node.summarize_plan(stage=stage.name, response=stage_response)
            print(stage_plan_summary.to_pretty_json())
            if stage_plan_summary.error_code != MoveItErrorCodes.SUCCESS:
                safe_return_status = _attempt_safe_return(node=node, task_definition=task_definition, failed_stage=stage)
                print(
                    TaskFinalSummary(
                        task_name=task_definition.definition.task_name,
                        overall_status="failed",
                        target_mode=args.target,
                        completed_stages=completed_stages,
                        failed_stage=stage.name,
                        safe_return_status=safe_return_status,
                    ).to_pretty_json()
                )
                return 1

            stage_execution_summary = node.execute_dual_arm_stage(
                stage=stage,
                response=stage_response,
            )
            print(stage_execution_summary.to_pretty_json())
            if stage_execution_summary.overall_status != "success":
                safe_return_status = _attempt_safe_return(node=node, task_definition=task_definition, failed_stage=stage)
                print(
                    TaskFinalSummary(
                        task_name=task_definition.definition.task_name,
                        overall_status="failed",
                        target_mode=args.target,
                        completed_stages=completed_stages,
                        failed_stage=stage.name,
                        safe_return_status=safe_return_status,
                    ).to_pretty_json()
                )
                return 1
            completed_stages.append(stage.name)

        print(
            TaskFinalSummary(
                task_name=task_definition.definition.task_name,
                overall_status="success",
                target_mode=args.target,
                completed_stages=completed_stages,
                failed_stage=None,
                safe_return_status=safe_return_status,
            ).to_pretty_json()
        )
        return 0
    except Exception as exc:
        print(f"run_dual_arm_task failed: {exc}", file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


def _resolve_requested_stages(
    *,
    task_definition: LoadedDualArmTask,
    target: str,
) -> list[TaskStageDefinition]:
    if target == "safe":
        return [
            TaskStageDefinition(
                name="safe",
                execution_mode=task_definition.definition.default_execution_mode,
                failure_policy="abort",
                scene_profile=task_definition.definition.scene_profile,
                target_positions=task_definition.definition.safe_positions,
            )
        ]
    if target == "full":
        return list(task_definition.stages)

    for stage in task_definition.stages:
        if stage.name == target:
            return [stage]

    known_targets = ["full", "safe", *[stage.name for stage in task_definition.stages]]
    raise RuntimeError(f"Unknown target {target!r}. Known targets: {known_targets}")


def _attempt_safe_return(
    *,
    node: DualArmTaskClient,
    task_definition: LoadedDualArmTask,
    failed_stage: TaskStageDefinition,
) -> str:
    if failed_stage.failure_policy != "return_safe":
        return "not_requested"
    if failed_stage.name == "safe":
        return "skipped"

    safe_stage = TaskStageDefinition(
        name="safe",
        execution_mode=task_definition.definition.default_execution_mode,
        failure_policy="abort",
        scene_profile=task_definition.definition.scene_profile,
        target_positions=task_definition.definition.safe_positions,
    )
    safe_response = node.plan_to_positions(
        stage=safe_stage.name,
        target_positions=safe_stage.as_dual_positions(),
        scene_profile=safe_stage.scene_profile,
    )
    safe_plan_summary = node.summarize_plan(stage=safe_stage.name, response=safe_response)
    print(safe_plan_summary.to_pretty_json())
    if safe_plan_summary.error_code != MoveItErrorCodes.SUCCESS:
        return "plan_failed"
    safe_execution_summary = node.execute_dual_arm_stage(stage=safe_stage, response=safe_response)
    print(safe_execution_summary.to_pretty_json())
    if safe_execution_summary.overall_status != "success":
        return "execute_failed"
    return "success"


if __name__ == "__main__":
    raise SystemExit(main())
