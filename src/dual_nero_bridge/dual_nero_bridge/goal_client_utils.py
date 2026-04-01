from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import rclpy
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from dual_nero_driver.safety import expected_joint_names
from dual_nero_driver.utils import load_dual_arm_config


@dataclass(slots=True)
class GoalPreview:
    controller_name: str
    joint_names: list[str]
    current_positions: list[float]
    target_positions: list[float]

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


class SingleArmGoalClient(Node):
    def __init__(
        self,
        *,
        side: str,
        config_path: str | Path,
        delta: float,
        timeout_sec: float,
    ) -> None:
        super().__init__(f"{side}_arm_goal_client")
        self.side = side
        self.timeout_sec = float(timeout_sec)
        self.joint_names = _load_joint_names(config_path, side)
        self._joint_state_msg: JointState | None = None
        self._joint_state_subscription = self.create_subscription(
            JointState,
            "/joint_states",
            self._joint_state_callback,
            10,
        )
        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            f"/{side}_arm_controller/follow_joint_trajectory",
        )
        self.delta = float(delta)

    def build_preview(self) -> GoalPreview:
        current = self._wait_for_current_positions()
        target = list(current)
        target[0] += self.delta
        return GoalPreview(
            controller_name=f"{self.side}_arm_controller",
            joint_names=list(self.joint_names),
            current_positions=current,
            target_positions=target,
        )

    def send_goal(self, preview: GoalPreview):
        if not self._action_client.wait_for_server(timeout_sec=self.timeout_sec):
            raise RuntimeError(
                f"{preview.controller_name} action server was not available within {self.timeout_sec:.1f}s."
            )

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory()
        goal.trajectory.joint_names = list(preview.joint_names)
        point = JointTrajectoryPoint()
        point.positions = list(preview.target_positions)
        point.time_from_start.sec = 1
        goal.trajectory.points = [point]

        send_goal_future = self._action_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_goal_future, timeout_sec=self.timeout_sec)
        goal_handle = send_goal_future.result()
        if goal_handle is None:
            raise RuntimeError(f"{preview.controller_name} goal request timed out.")
        if not goal_handle.accepted:
            raise RuntimeError(f"{preview.controller_name} goal was rejected by the bridge.")

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=self.timeout_sec)
        result_handle = result_future.result()
        if result_handle is None:
            raise RuntimeError(f"{preview.controller_name} result wait timed out.")
        return result_handle.result

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
                f"/joint_states is missing expected joints for {self.side}_arm_controller: {missing}"
            )
        return [float(name_to_position[joint_name]) for joint_name in self.joint_names]

    def _joint_state_callback(self, msg: JointState) -> None:
        self._joint_state_msg = msg


def _load_joint_names(config_path: str | Path, side: str) -> list[str]:
    left_config, right_config = load_dual_arm_config(config_path)
    joint_names = left_config.joint_names if side == "left" else right_config.joint_names
    expected = expected_joint_names(side)
    if list(joint_names) != expected:
        raise RuntimeError(
            f"{side}_arm joint_names must match {expected}, got {list(joint_names)}."
        )
    return expected
