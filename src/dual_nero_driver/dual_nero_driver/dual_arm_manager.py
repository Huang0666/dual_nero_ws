from __future__ import annotations

import time

from .exceptions import BackendTimeoutError
from .nero_arm import NeroArm
from .safety import ensure_float_list, targets_within_tolerance


class DualArmManager:
    def __init__(self, left_arm: NeroArm, right_arm: NeroArm) -> None:
        if left_arm.side != "left":
            raise ValueError("left_arm.side must be 'left'.")
        if right_arm.side != "right":
            raise ValueError("right_arm.side must be 'right'.")
        self.left_arm = left_arm
        self.right_arm = right_arm

    def connect_all(self) -> None:
        self.left_arm.connect()
        self.right_arm.connect()

    def enable_all(self, timeout_sec: float = 5.0) -> None:
        self.left_arm.enable_all(timeout_sec=timeout_sec)
        self.right_arm.enable_all(timeout_sec=timeout_sec)

    def disable_all(self) -> None:
        self.left_arm.disable_all()
        self.right_arm.disable_all()

    def get_states(self) -> dict[str, dict]:
        return {
            "left_arm": self.left_arm.get_joint_state_snapshot().as_dict(),
            "right_arm": self.right_arm.get_joint_state_snapshot().as_dict(),
        }

    def move_both_joints(
        self,
        left_target: list[float],
        right_target: list[float],
        speed: float | None = None,
        wait: bool = False,
    ) -> None:
        normalized_left = ensure_float_list(
            left_target,
            expected_len=len(self.left_arm.joint_names),
            label="left_arm target",
        )
        normalized_right = ensure_float_list(
            right_target,
            expected_len=len(self.right_arm.joint_names),
            label="right_arm target",
        )

        self.left_arm.move_j(normalized_left, speed=speed, wait=False)
        self.right_arm.move_j(normalized_right, speed=speed, wait=False)

        if wait:
            self._wait_for_targets(normalized_left, normalized_right)

    def stop_all(self) -> None:
        self.left_arm.stop()
        self.right_arm.stop()

    def estop_all(self) -> None:
        self.left_arm.estop()
        self.right_arm.estop()

    def _wait_for_targets(
        self,
        left_target: list[float],
        right_target: list[float],
        *,
        tolerance: float = 0.01,
        timeout_sec: float = 10.0,
        poll_sec: float = 0.1,
    ) -> None:
        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            left_current = self.left_arm.get_joint_positions()
            right_current = self.right_arm.get_joint_positions()
            if targets_within_tolerance(left_current, left_target, tolerance=tolerance) and targets_within_tolerance(
                right_current,
                right_target,
                tolerance=tolerance,
            ):
                return
            time.sleep(poll_sec)

        raise BackendTimeoutError(
            "Timed out while waiting for both arms to reach target joints."
        )
