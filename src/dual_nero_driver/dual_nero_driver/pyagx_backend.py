from __future__ import annotations

import logging
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
        self._logger = logging.getLogger(f"dual_nero_driver.{self._config.name}")
        self._normal_mode_was_called = False
        self._last_enable_return: Any = None
        self._last_enable_statuses: list[bool] | None = None

    @property
    def normal_mode_was_called(self) -> bool:
        return self._normal_mode_was_called

    @property
    def last_enable_return(self) -> Any:
        return self._last_enable_return

    @property
    def last_enable_statuses(self) -> list[bool] | None:
        if self._last_enable_statuses is None:
            return None
        return list(self._last_enable_statuses)

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
            self._logger.debug("%s: connect() completed successfully", self._config.name)
            self._set_normal_mode_if_available()
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

        deadline = time.monotonic() + timeout_sec
        self._last_enable_return = None
        self._last_enable_statuses = None
        while time.monotonic() < deadline:
            self._last_enable_return = self._invoke("enable")
            self._last_enable_statuses = self._read_enable_statuses()
            self._logger.debug(
                "%s: enable() -> %r statuses -> %r",
                self._config.name,
                self._last_enable_return,
                self._last_enable_statuses,
            )
            if self._all_joints_enabled(self._last_enable_statuses):
                self._enabled = True
                return
            time.sleep(0.05)

        raise BackendTimeoutError(
            f"{self._config.name}: joints were not all enabled within {timeout_sec:.2f}s; "
            f"last_enable_return={self._last_enable_return!r}, "
            f"last_statuses={self._last_enable_statuses!r}."
        )

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

    def _set_normal_mode_if_available(self) -> None:
        robot = self._require_robot()
        set_normal_mode = getattr(robot, "set_normal_mode", None)
        if not callable(set_normal_mode):
            return
        try:
            self._logger.debug("%s: calling set_normal_mode()", self._config.name)
            result = set_normal_mode()
        except Exception as exc:
            raise BackendConnectionError(
                f"{self._config.name}: set_normal_mode() failed after connect: {exc}"
            ) from exc
        self._normal_mode_was_called = True
        if result is False:
            raise BackendConnectionError(
                f"{self._config.name}: set_normal_mode() returned False after connect."
            )
        self._logger.debug("%s: set_normal_mode() completed successfully", self._config.name)

    def _read_enable_statuses(self) -> list[bool] | None:
        robot = self._require_robot()
        status_method = getattr(robot, "get_joints_enable_status_list", None)
        if not callable(status_method):
            raise BackendCommandError(
                f"{self._config.name}: backend does not implement get_joints_enable_status_list()."
            )
        try:
            statuses = status_method()
        except Exception as exc:
            raise BackendCommandError(
                f"{self._config.name}: get_joints_enable_status_list() failed: {exc}"
            ) from exc
        if hasattr(statuses, "msg"):
            statuses = statuses.msg
        if statuses is None:
            return None
        if not isinstance(statuses, list):
            raise BackendCommandError(
                f"{self._config.name}: get_joints_enable_status_list() returned non-list {statuses!r}."
            )
        normalized_statuses = [bool(status) for status in statuses]
        if len(normalized_statuses) != len(self._config.joint_names):
            raise BackendCommandError(
                f"{self._config.name}: expected {len(self._config.joint_names)} enable statuses, "
                f"got {len(normalized_statuses)}."
            )
        return normalized_statuses

    def _all_joints_enabled(self, statuses: list[bool] | None) -> bool:
        return bool(statuses) and all(statuses)
