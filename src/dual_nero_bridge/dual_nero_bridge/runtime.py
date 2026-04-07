from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dual_nero_driver import build_dual_arm_manager_from_file
from dual_nero_driver.exceptions import BackendError, SafetyError, ValidationError
from dual_nero_driver.safety import expected_joint_names
from dual_nero_driver.utils import load_dual_arm_config

from .errors import (
    BridgeArmUnavailableError,
    BridgeDegradedError,
    BridgeMotionRejectedError,
    BridgeStartupError,
)


Side = Literal["left", "right"]


@dataclass(slots=True)
class ArmRuntimeState:
    side: Side
    controller_name: str
    available: bool = False
    enabled: bool = False
    last_error: str | None = None


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
        self.left_state = ArmRuntimeState(side="left", controller_name="left_arm_controller")
        self.right_state = ArmRuntimeState(
            side="right",
            controller_name="right_arm_controller",
        )
        self._connected = False
        self._last_arm_snapshot: dict[Side, dict | None] = {"left": None, "right": None}
        self._last_arm_state_monotonic: dict[Side, float | None] = {
            "left": None,
            "right": None,
        }

    def connect(self) -> None:
        with self.lock:
            if self._connected:
                return

            self._connect_arm("left")
            self._connect_arm("right")
            self._connected = True

            if not (self.left_state.available or self.right_state.available):
                raise BridgeStartupError(
                    "No arm is available after bridge startup. Check CAN, pyAgxArm, and hardware power."
                )

    def enable_if_requested(self) -> None:
        with self.lock:
            if not self.enable_on_start:
                return

            self._enable_arm("left")
            self._enable_arm("right")
            if not (self.left_state.enabled or self.right_state.enabled):
                raise BridgeStartupError(
                    "enable_on_start=true but no available arm could be enabled."
                )

    def read_joint_state(self) -> tuple[list[str], list[float], list[float] | None]:
        with self.lock:
            if not (self.left_state.available and self.right_state.available):
                raise BridgeDegradedError(
                    "joint_states publishing requires both arms available; "
                    f"left_available={self.left_state.available}, "
                    f"right_available={self.right_state.available}."
                )

            left_state = self._read_arm_state("left")
            right_state = self._read_arm_state("right")
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

    def read_arm_joint_state(self, side: Side) -> tuple[list[str], list[float], list[float] | None]:
        with self.lock:
            state = self._state(side)
            if not state.available:
                detail = state.last_error or "arm is unavailable."
                raise BridgeArmUnavailableError(
                    f"{state.controller_name} state is unavailable: {detail}"
                )
            arm_state = self._read_arm_state(side)
            return (
                list(arm_state["joint_names"]),
                list(arm_state["joint_positions"]),
                arm_state["joint_velocities"],
            )

    def move_left(
        self,
        target: list[float],
        *,
        speed: float | None = None,
        wait: bool = False,
    ) -> None:
        with self.lock:
            self.require_arm_ready_for_motion("left")
            try:
                self.manager.left_arm.move_j(target, speed=speed, wait=wait)
            except (SafetyError, ValidationError) as exc:
                raise BridgeMotionRejectedError(str(exc)) from exc
            except BackendError as exc:
                self.left_state.last_error = str(exc)
                raise BridgeMotionRejectedError(
                    f"left_arm_controller backend command failed: {exc}"
                ) from exc

    def move_right(
        self,
        target: list[float],
        *,
        speed: float | None = None,
        wait: bool = False,
    ) -> None:
        with self.lock:
            self.require_arm_ready_for_motion("right")
            try:
                self.manager.right_arm.move_j(target, speed=speed, wait=wait)
            except (SafetyError, ValidationError) as exc:
                raise BridgeMotionRejectedError(str(exc)) from exc
            except BackendError as exc:
                self.right_state.last_error = str(exc)
                raise BridgeMotionRejectedError(
                    f"right_arm_controller backend command failed: {exc}"
                ) from exc

    def move_both(
        self,
        left_target: list[float],
        right_target: list[float],
        *,
        speed: float | None = None,
        wait: bool = False,
    ) -> None:
        with self.lock:
            self.require_dual_motion_ready()
            try:
                self.manager.move_both_joints(
                    left_target=left_target,
                    right_target=right_target,
                    speed=speed,
                    wait=wait,
                )
            except (SafetyError, ValidationError) as exc:
                raise BridgeMotionRejectedError(str(exc)) from exc
            except BackendError as exc:
                self.left_state.last_error = str(exc)
                self.right_state.last_error = str(exc)
                raise BridgeMotionRejectedError(
                    f"dual_arms backend command failed: {exc}"
                ) from exc

    def stop_left(self) -> None:
        with self.lock:
            if self.left_state.available:
                self.manager.left_arm.stop()

    def stop_right(self) -> None:
        with self.lock:
            if self.right_state.available:
                self.manager.right_arm.stop()

    def stop_all(self) -> None:
        with self.lock:
            if self.left_state.available:
                self.manager.left_arm.stop()
            if self.right_state.available:
                self.manager.right_arm.stop()

    def estop_all(self) -> None:
        with self.lock:
            if self.left_state.available:
                self.manager.left_arm.estop()
                self.left_state.enabled = False
            if self.right_state.available:
                self.manager.right_arm.estop()
                self.right_state.enabled = False

    def disable_all(self) -> None:
        with self.lock:
            if self.left_state.available:
                self.manager.left_arm.disable_all()
                self.left_state.enabled = False
            if self.right_state.available:
                self.manager.right_arm.disable_all()
                self.right_state.enabled = False

    def close(self) -> None:
        with self.lock:
            try:
                self.manager.left_arm.backend.close()
            finally:
                self.manager.right_arm.backend.close()
            self.left_state.enabled = False
            self.right_state.enabled = False
            self._connected = False

    def availability_summary(self) -> str:
        return (
            f"left_available={self.left_state.available}, "
            f"right_available={self.right_state.available}, "
            f"left_enabled={self.left_state.enabled}, "
            f"right_enabled={self.right_state.enabled}"
        )

    def channel_mapping(self) -> dict[str, str]:
        return {
            "left_arm": self.left_config.can.channel,
            "right_arm": self.right_config.can.channel,
        }

    def arm_channel(self, side: Side) -> str:
        return self._config(side).can.channel

    def arm_status(self, side: Side) -> ArmRuntimeState:
        with self.lock:
            state = self._state(side)
            return ArmRuntimeState(
                side=state.side,
                controller_name=state.controller_name,
                available=state.available,
                enabled=state.enabled,
                last_error=state.last_error,
            )

    def arm_joint_limits(self, side: Side):
        return self._config(side).joint_position_limits

    def arm_joint_names(self, side: Side) -> list[str]:
        return list(self.left_joint_names if side == "left" else self.right_joint_names)

    def latest_arm_state_age_sec(self, side: Side) -> float | None:
        with self.lock:
            timestamp = self._last_arm_state_monotonic[side]
            if timestamp is None:
                return None
            return max(time.monotonic() - timestamp, 0.0)

    def require_arm_ready_for_motion(self, side: Side) -> None:
        with self.lock:
            self._require_arm_ready_for_motion(side)

    def require_dual_motion_ready(self) -> None:
        with self.lock:
            self._require_dual_motion_ready()

    def _connect_arm(self, side: Side) -> None:
        arm = self._arm(side)
        state = self._state(side)
        try:
            arm.connect()
        except Exception as exc:
            state.available = False
            state.enabled = False
            state.last_error = str(exc)
            return
        state.available = True
        state.last_error = None

    def _enable_arm(self, side: Side) -> None:
        state = self._state(side)
        if not state.available:
            return
        arm = self._arm(side)
        timeout_sec = self._config(side).pyagx.timeout
        try:
            arm.enable_all(timeout_sec=timeout_sec)
        except Exception as exc:
            state.enabled = False
            state.last_error = str(exc)
            return
        state.enabled = True
        state.last_error = None

    def _read_arm_state(self, side: Side) -> dict:
        state = self._state(side)
        arm = self._arm(side)
        try:
            snapshot = arm.get_joint_state_snapshot().as_dict()
        except Exception as exc:
            state.available = False
            state.enabled = False
            state.last_error = str(exc)
            raise BridgeDegradedError(
                f"{state.controller_name} state read failed: {exc}"
            ) from exc
        state.last_error = None
        self._last_arm_snapshot[side] = snapshot
        self._last_arm_state_monotonic[side] = time.monotonic()
        return snapshot

    def _require_arm_ready_for_motion(self, side: Side) -> None:
        state = self._state(side)
        if not self.allow_motion:
            raise BridgeMotionRejectedError(
                f"{state.controller_name} rejected because allow_motion=false."
            )
        if not state.available:
            detail = state.last_error or "arm is unavailable."
            raise BridgeArmUnavailableError(
                f"{state.controller_name} rejected because the arm is unavailable: {detail}"
            )
        if not state.enabled:
            raise BridgeMotionRejectedError(
                f"{state.controller_name} rejected because the arm is not enabled. "
                "This bridge does not perform lazy enable; launch with enable_on_start:=true."
            )

    def _require_dual_motion_ready(self) -> None:
        if not self.allow_motion:
            raise BridgeMotionRejectedError(
                "dual_arms rejected because allow_motion=false."
            )
        if not self.left_state.available or not self.right_state.available:
            raise BridgeArmUnavailableError(
                "dual_arms rejected because both arms must be available for synchronized execution."
            )
        if not self.left_state.enabled or not self.right_state.enabled:
            raise BridgeMotionRejectedError(
                "dual_arms rejected because both arms must be enabled. "
                "This bridge does not perform lazy enable; launch with enable_on_start:=true."
            )

    def _arm(self, side: Side):
        return self.manager.left_arm if side == "left" else self.manager.right_arm

    def _state(self, side: Side) -> ArmRuntimeState:
        return self.left_state if side == "left" else self.right_state

    def _config(self, side: Side):
        return self.left_config if side == "left" else self.right_config
