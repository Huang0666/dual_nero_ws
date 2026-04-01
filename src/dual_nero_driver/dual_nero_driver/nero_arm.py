from __future__ import annotations

import time
from typing import Literal

from .backend_base import ArmBackend
from .exceptions import BackendTimeoutError
from .safety import (
    clamp_speed_percent,
    ensure_float_list,
    targets_within_tolerance,
    validate_joint_names,
    validate_target_with_limits,
)
from .types import JointLimit, JointStateSnapshot


class NeroArm:
    def __init__(
        self,
        arm_name: str,
        side: Literal["left", "right"],
        backend: ArmBackend,
        joint_names: list[str],
        max_speed_percent: float | None,
        joint_position_limits: dict[str, JointLimit] | None = None,
    ) -> None:
        self.arm_name = arm_name
        self.side = side
        self.backend = backend
        self.joint_names = validate_joint_names(side, list(joint_names))
        self.max_speed_percent = max_speed_percent
        self.joint_position_limits = joint_position_limits or {}

    def connect(self) -> None:
        self.backend.connect()

    def enable_all(self, timeout_sec: float = 5.0) -> None:
        self.backend.enable_all(timeout_sec=timeout_sec)

    def disable_all(self) -> None:
        self.backend.disable_all()

    def get_joint_positions(self) -> list[float]:
        return ensure_float_list(
            self.backend.get_joint_positions(),
            expected_len=len(self.joint_names),
            label=f"{self.arm_name}.joint_positions",
        )

    def get_joint_state_snapshot(self) -> JointStateSnapshot:
        return JointStateSnapshot(
            arm_name=self.arm_name,
            side=self.side,
            joint_names=list(self.joint_names),
            joint_positions=self.get_joint_positions(),
            joint_velocities=self.backend.get_joint_velocities(),
            tcp_pose=self.backend.get_tcp_pose(),
        )

    def get_tcp_pose(self) -> list[float] | None:
        return self.backend.get_tcp_pose()

    def move_j(
        self,
        target: list[float],
        speed: float | None = None,
        wait: bool = False,
    ) -> None:
        normalized_target = ensure_float_list(
            target,
            expected_len=len(self.joint_names),
            label=f"{self.arm_name}.move_j target",
        )
        validate_target_with_limits(
            self.joint_names,
            normalized_target,
            self.joint_position_limits,
        )
        bounded_speed = clamp_speed_percent(speed, self.max_speed_percent)
        self.backend.move_j(normalized_target, speed=bounded_speed, wait=False)
        if wait:
            self._wait_for_target(normalized_target)

    def stop(self) -> None:
        self.backend.stop()

    def estop(self) -> None:
        self.backend.estop()

    def _wait_for_target(
        self,
        target: list[float],
        *,
        tolerance: float = 0.01,
        timeout_sec: float = 10.0,
        poll_sec: float = 0.1,
    ) -> None:
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            current = self.get_joint_positions()
            if targets_within_tolerance(current, target, tolerance=tolerance):
                return
            time.sleep(poll_sec)

        raise BackendTimeoutError(
            f"{self.arm_name}: timed out while waiting for target joints."
        )
