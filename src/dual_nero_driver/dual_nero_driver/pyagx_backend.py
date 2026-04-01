from __future__ import annotations

import time
from typing import Any

from .backend_base import ArmBackend
from .exceptions import (
    BackendCommandError,
    BackendConnectionError,
    BackendDependencyError,
    BackendTimeoutError,
)
from .safety import ensure_float_list
from .types import ArmConfig

try:
    from pyAgxArm import AgxArmFactory, create_agx_arm_config
except ImportError as import_error:  # pragma: no cover
    AgxArmFactory = None
    create_agx_arm_config = None
    _PYAGX_IMPORT_ERROR = import_error
else:  # pragma: no cover
    _PYAGX_IMPORT_ERROR = None


class PyAgxBackend(ArmBackend):
    def __init__(self, arm_config: ArmConfig) -> None:
        self._config = arm_config
        self._robot: Any | None = None
        self._connected = False
        self._enabled = False
        self._dry_run_joint_positions = [0.0] * len(self._config.joint_names)

    def connect(self) -> None:
        if self._connected:
            return

        if self._config.dry_run:
            self._connected = True
            return

        if create_agx_arm_config is None or AgxArmFactory is None:
            raise BackendDependencyError(
                "pyAgxArm is not installed. Install it or set dry_run=true."
            ) from _PYAGX_IMPORT_ERROR

        try:
            cfg_kwargs = {
                "robot": "nero",
                "comm": "can",
                "channel": self._config.can.channel,
                "interface": self._config.can.interface,
                "enable_check_can": self._config.pyagx.enable_check_can,
                "auto_connect": self._config.pyagx.auto_connect,
                "timeout": self._config.pyagx.timeout,
            }
            if self._config.can.bitrate is not None:
                cfg_kwargs["bitrate"] = self._config.can.bitrate

            backend_cfg = create_agx_arm_config(**cfg_kwargs)
            if backend_cfg is None:
                raise BackendConnectionError(
                    f"{self._config.name}: create_agx_arm_config returned None."
                )

            self._robot = AgxArmFactory.create_arm(backend_cfg)
            if self._robot is None:
                raise BackendConnectionError(
                    f"{self._config.name}: AgxArmFactory.create_arm returned None."
                )

            result = self._robot.connect()
            if result is False:
                raise BackendConnectionError(
                    f"{self._config.name}: pyAgxArm connect() returned False."
                )
            self._connected = True
        except BackendConnectionError:
            raise
        except Exception as exc:
            raise BackendConnectionError(
                f"{self._config.name}: failed to connect via pyAgxArm: {exc}"
            ) from exc

    def enable_all(self, timeout_sec: float = 5.0) -> None:
        self._require_connected()
        if self._config.dry_run:
            self._enabled = True
            return

        start = time.monotonic()
        result = self._invoke("enable")
        elapsed = time.monotonic() - start
        if elapsed > timeout_sec:
            raise BackendTimeoutError(
                f"{self._config.name}: enable() exceeded timeout {timeout_sec:.2f}s."
            )
        if result is False:
            raise BackendCommandError(f"{self._config.name}: enable() returned False.")
        self._wait_until_enabled(timeout_sec)
        self._enabled = True

    def disable_all(self) -> None:
        if not self._connected:
            return
        if self._config.dry_run:
            self._enabled = False
            return

        result = self._invoke("disable")
        if result is False:
            raise BackendCommandError(f"{self._config.name}: disable() returned False.")
        self._enabled = False

    def get_joint_positions(self) -> list[float]:
        self._require_connected()
        if self._config.dry_run:
            return list(self._dry_run_joint_positions)

        result = self._invoke("get_joint_angles")
        if result is None:
            raise BackendTimeoutError(
                f"{self._config.name}: get_joint_angles() returned None."
            )
        if hasattr(result, "msg"):
            result = result.msg
        return ensure_float_list(
            result,
            expected_len=len(self._config.joint_names),
            label=f"{self._config.name}.joint_positions",
        )

    def get_joint_velocities(self) -> list[float] | None:
        self._require_connected()
        if self._config.dry_run:
            return [0.0] * len(self._config.joint_names)

        robot = self._require_robot()
        method = getattr(robot, "get_joint_velocities", None)
        if method is None:
            return None
        try:
            result = method()
        except Exception as exc:
            raise BackendCommandError(
                f"{self._config.name}: get_joint_velocities() failed: {exc}"
            ) from exc
        if result is None:
            return None
        if hasattr(result, "msg"):
            result = result.msg
        return ensure_float_list(
            result,
            expected_len=len(self._config.joint_names),
            label=f"{self._config.name}.joint_velocities",
        )

    def get_tcp_pose(self) -> list[float] | None:
        self._require_connected()
        if self._config.dry_run:
            return None

        robot = self._require_robot()
        method = getattr(robot, "get_tcp_pose", None)
        if method is None:
            return None
        try:
            result = method()
        except Exception as exc:
            raise BackendCommandError(
                f"{self._config.name}: get_tcp_pose() failed: {exc}"
            ) from exc
        if result is None:
            return None
        if hasattr(result, "msg"):
            result = result.msg
        return ensure_float_list(
            result,
            expected_len=len(result),
            label=f"{self._config.name}.tcp_pose",
        )

    def move_j(
        self,
        target: list[float],
        speed: float | None = None,
        wait: bool = False,
    ) -> None:
        self._require_connected()
        if self._config.dry_run:
            self._dry_run_joint_positions = list(target)
            return

        if speed is not None:
            self._invoke("set_speed_percent", int(round(speed)))
        result = self._invoke("move_j", target)
        if result is False:
            raise BackendCommandError(f"{self._config.name}: move_j() returned False.")

    def stop(self) -> None:
        if not self._connected:
            return
        if self._config.dry_run:
            return

        result = self._invoke("stop")
        if result is False:
            raise BackendCommandError(f"{self._config.name}: stop() returned False.")

    def estop(self) -> None:
        if not self._connected:
            return
        if self._config.dry_run:
            self._enabled = False
            return

        result = self._invoke("electronic_emergency_stop")
        if result is False:
            raise BackendCommandError(
                f"{self._config.name}: electronic_emergency_stop() returned False."
            )
        self._enabled = False

    def close(self) -> None:
        if self._config.dry_run:
            self._connected = False
            self._enabled = False
            return

        if self._robot is not None:
            close_method = getattr(self._robot, "close", None)
            disconnect_method = getattr(self._robot, "disconnect", None)
            try:
                if callable(close_method):
                    close_method()
                elif callable(disconnect_method):
                    disconnect_method()
            except Exception as exc:
                raise BackendCommandError(
                    f"{self._config.name}: failed to close backend: {exc}"
                ) from exc
        self._robot = None
        self._connected = False
        self._enabled = False

    def _invoke(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        robot = self._require_robot()
        method = getattr(robot, method_name, None)
        if not callable(method):
            raise BackendCommandError(
                f"{self._config.name}: backend does not implement {method_name}()."
            )
        try:
            return method(*args, **kwargs)
        except Exception as exc:
            raise BackendCommandError(
                f"{self._config.name}: {method_name}() failed: {exc}"
            ) from exc

    def _require_robot(self) -> Any:
        if self._robot is None:
            raise BackendConnectionError(
                f"{self._config.name}: backend robot handle is not initialized."
            )
        return self._robot

    def _require_connected(self) -> None:
        if not self._connected:
            raise BackendConnectionError(
                f"{self._config.name}: backend is not connected yet."
            )

    def _wait_until_enabled(self, timeout_sec: float) -> None:
        robot = self._require_robot()
        status_method = getattr(robot, "get_joints_enable_status_list", None)
        if not callable(status_method):
            return

        deadline = time.monotonic() + timeout_sec
        while time.monotonic() < deadline:
            try:
                statuses = status_method()
            except Exception as exc:
                raise BackendCommandError(
                    f"{self._config.name}: get_joints_enable_status_list() failed: {exc}"
                ) from exc
            if hasattr(statuses, "msg"):
                statuses = statuses.msg
            if isinstance(statuses, list) and len(statuses) == len(self._config.joint_names):
                if all(bool(status) for status in statuses):
                    return
            time.sleep(0.05)

        raise BackendTimeoutError(
            f"{self._config.name}: joints were not all enabled within {timeout_sec:.2f}s."
        )
