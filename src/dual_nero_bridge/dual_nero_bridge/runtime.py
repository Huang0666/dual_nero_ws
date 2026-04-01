from __future__ import annotations

import threading
from pathlib import Path

from dual_nero_driver import build_dual_arm_manager_from_file
from dual_nero_driver.exceptions import SafetyError
from dual_nero_driver.safety import expected_joint_names
from dual_nero_driver.utils import load_dual_arm_config


class DualNeroBridgeRuntime:
    def __init__(
        self,
        config_path: str | Path,
        *,
        allow_motion: bool,
        enable_on_start: bool,
    ) -> None:
        self.config_path = Path(config_path)
        self.allow_motion = bool(allow_motion)
        self.enable_on_start = bool(enable_on_start)
        self.lock = threading.RLock()
        self.left_config, self.right_config = load_dual_arm_config(self.config_path)
        self.manager = build_dual_arm_manager_from_file(self.config_path)
        self.left_joint_names = expected_joint_names("left")
        self.right_joint_names = expected_joint_names("right")
        self.dual_joint_names = self.left_joint_names + self.right_joint_names
        self._connected = False
        self._enabled = False

    def connect(self) -> None:
        with self.lock:
            if self._connected:
                return
            self.manager.connect_all()
            self._connected = True

    def enable_if_requested(self) -> None:
        with self.lock:
            if not self.enable_on_start or self._enabled:
                return
            timeout_sec = max(
                self.left_config.pyagx.timeout,
                self.right_config.pyagx.timeout,
            )
            self.manager.enable_all(timeout_sec=timeout_sec)
            self._enabled = True

    def read_joint_state(self) -> tuple[list[str], list[float], list[float] | None]:
        with self.lock:
            states = self.manager.get_states()
            left_state = states["left_arm"]
            right_state = states["right_arm"]
            names = list(left_state["joint_names"]) + list(right_state["joint_names"])
            positions = list(left_state["joint_positions"]) + list(
                right_state["joint_positions"]
            )
            left_velocity = left_state["joint_velocities"]
            right_velocity = right_state["joint_velocities"]
            velocities = None
            if left_velocity is not None and right_velocity is not None:
                velocities = list(left_velocity) + list(right_velocity)
            return names, positions, velocities

    def move_left(
        self,
        target: list[float],
        *,
        speed: float | None = None,
        wait: bool = False,
    ) -> None:
        with self.lock:
            self._require_motion_allowed("left_arm_controller")
            self.manager.left_arm.move_j(target, speed=speed, wait=wait)

    def move_right(
        self,
        target: list[float],
        *,
        speed: float | None = None,
        wait: bool = False,
    ) -> None:
        with self.lock:
            self._require_motion_allowed("right_arm_controller")
            self.manager.right_arm.move_j(target, speed=speed, wait=wait)

    def move_both(
        self,
        left_target: list[float],
        right_target: list[float],
        *,
        speed: float | None = None,
        wait: bool = False,
    ) -> None:
        with self.lock:
            self._require_motion_allowed("dual_arms")
            self.manager.move_both_joints(
                left_target=left_target,
                right_target=right_target,
                speed=speed,
                wait=wait,
            )

    def stop_left(self) -> None:
        with self.lock:
            self.manager.left_arm.stop()

    def stop_right(self) -> None:
        with self.lock:
            self.manager.right_arm.stop()

    def stop_all(self) -> None:
        with self.lock:
            self.manager.stop_all()

    def estop_all(self) -> None:
        with self.lock:
            self.manager.estop_all()
            self._enabled = False

    def disable_all(self) -> None:
        with self.lock:
            self.manager.disable_all()
            self._enabled = False

    def close(self) -> None:
        with self.lock:
            try:
                self.manager.left_arm.backend.close()
            finally:
                self.manager.right_arm.backend.close()
            self._connected = False
            self._enabled = False

    def _require_motion_allowed(self, label: str) -> None:
        if not self.allow_motion:
            raise SafetyError(
                f"{label}: allow_motion is false; refusing to execute hardware motion."
            )
