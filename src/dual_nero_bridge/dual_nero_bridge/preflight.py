from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal, Sequence

import yaml

from dual_nero_driver.safety import (
    JointLimitStatus,
    ensure_float_list,
    find_joints_near_limits,
    find_joints_outside_limits,
)

from . import preflight_codes as codes
from .runtime import DualNeroBridgeRuntime, Side


CommandScope = Literal["left_arm", "right_arm", "dual_arms"]


@dataclass(slots=True)
class PreflightConfig:
    enabled: bool = True
    safety_mode: str = "strict"
    near_limit_margin: float = 0.05
    reject_on_near_limit: bool = True
    max_start_deviation: float = 0.35
    max_state_age_sec: float = 0.5
    require_online: bool = True
    require_enabled: bool = True
    require_dual_online: bool = True
    require_dual_enabled: bool = True
    scopes: dict[str, list[str]] = field(
        default_factory=lambda: {
            "left_arm": ["left"],
            "right_arm": ["right"],
            "dual_arms": ["left", "right"],
        }
    )


@dataclass(slots=True)
class PreflightResult:
    ok: bool
    stage: str
    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    severity: Literal["allow", "reject", "abort", "warn"] = "allow"

    @classmethod
    def allow(cls) -> "PreflightResult":
        return cls(
            ok=True,
            stage="preflight",
            code=codes.OK,
            message="preflight checks passed",
            severity="allow",
        )

    @classmethod
    def reject(
        cls,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
        severity: Literal["reject", "abort", "warn"] = "reject",
    ) -> "PreflightResult":
        return cls(
            ok=False,
            stage="preflight",
            code=code,
            message=message,
            details=details or {},
            severity=severity,
        )


class PreflightChecker:
    def __init__(
        self,
        runtime: DualNeroBridgeRuntime,
        *,
        config_path: str | Path,
        enabled: bool,
        safety_mode: str,
    ) -> None:
        self._runtime = runtime
        self.config_path = Path(config_path)
        self.config = self._load_config(
            self.config_path,
            enabled=enabled,
            safety_mode=safety_mode,
        )

    def summary(self) -> str:
        return (
            f"enabled={self.config.enabled}, "
            f"safety_mode={self.config.safety_mode}, "
            f"near_limit_margin={self.config.near_limit_margin}, "
            f"max_start_deviation={self.config.max_start_deviation}, "
            f"max_state_age_sec={self.config.max_state_age_sec}"
        )

    def check_trajectory_goal(
        self,
        *,
        side: Side,
        controller_name: str,
        joint_names: Sequence[str],
        points: Sequence[Any],
    ) -> PreflightResult:
        scope = "left_arm" if side == "left" else "right_arm"
        structure = self._validate_structure(
            scope=scope,
            source="trajectory",
            source_name=controller_name,
            joint_names=joint_names,
            points=points,
            expected_joint_names=self._runtime.arm_joint_names(side),
        )
        if not structure.ok:
            return structure

        point = points[0]
        optional_check = self._validate_optional_trajectory_fields(
            source_name=controller_name,
            point=point,
            expected_len=len(self._runtime.arm_joint_names(side)),
        )
        if not optional_check.ok:
            return optional_check

        target = ensure_float_list(
            point.positions,
            expected_len=len(self._runtime.arm_joint_names(side)),
            label=f"{controller_name} point.positions",
        )
        return self._run_motion_preflight(
            scope=scope,
            source="trajectory",
            source_name=controller_name,
            target_by_side={side: target},
        )

    def check_joint_command(
        self,
        *,
        scope: CommandScope,
        source_name: str,
        joint_names: Sequence[str],
        points: Sequence[Any],
    ) -> PreflightResult:
        expected_joint_names = self._expected_joint_names_for_scope(scope)
        structure = self._validate_structure(
            scope=scope,
            source="topic",
            source_name=source_name,
            joint_names=joint_names,
            points=points,
            expected_joint_names=expected_joint_names,
        )
        if not structure.ok:
            return structure

        point = points[0]
        target = ensure_float_list(
            point.positions,
            expected_len=len(expected_joint_names),
            label=f"{source_name} point.positions",
        )
        if scope == "dual_arms":
            left_count = len(self._runtime.arm_joint_names("left"))
            return self._run_motion_preflight(
                scope=scope,
                source="topic",
                source_name=source_name,
                target_by_side={
                    "left": target[:left_count],
                    "right": target[left_count:],
                },
            )

        side: Side = "left" if scope == "left_arm" else "right"
        return self._run_motion_preflight(
            scope=scope,
            source="topic",
            source_name=source_name,
            target_by_side={side: target},
        )

    def _run_motion_preflight(
        self,
        *,
        scope: CommandScope,
        source: str,
        source_name: str,
        target_by_side: dict[Side, list[float]],
    ) -> PreflightResult:
        if not self.config.enabled:
            return PreflightResult.allow()
        if not self._runtime.allow_motion:
            return PreflightResult.reject(
                codes.ALLOW_MOTION_DISABLED,
                f"{source_name} rejected because allow_motion=false.",
                details={"scope": scope, "source": source},
            )

        for side, target in target_by_side.items():
            availability = self._check_arm_availability(side=side, scope=scope)
            if not availability.ok:
                return availability

            state_result, current_positions = self._load_current_positions(side)
            if not state_result.ok:
                return state_result

            limit_result = self._check_pose_limits(
                side=side,
                current_positions=current_positions,
            )
            if not limit_result.ok:
                return limit_result

            start_result = self._check_start_deviation(
                side=side,
                current_positions=current_positions,
                target_positions=target,
                source_name=source_name,
            )
            if not start_result.ok:
                return start_result

        return PreflightResult.allow()

    def _validate_structure(
        self,
        *,
        scope: CommandScope,
        source: str,
        source_name: str,
        joint_names: Sequence[str],
        points: Sequence[Any],
        expected_joint_names: list[str],
    ) -> PreflightResult:
        if list(joint_names) != expected_joint_names:
            return PreflightResult.reject(
                codes.INVALID_JOINT_SET,
                f"{source_name} joint_names must exactly match {expected_joint_names}.",
                details={
                    "scope": scope,
                    "source": source,
                    "joint_names": list(joint_names),
                },
            )
        if not points:
            return PreflightResult.reject(
                codes.INVALID_GOAL_STRUCTURE,
                f"{source_name} must contain exactly one trajectory point; received 0.",
                details={"scope": scope, "source": source},
            )
        if len(points) != 1:
            return PreflightResult.reject(
                codes.INVALID_GOAL_STRUCTURE,
                f"{source_name} currently supports exactly one trajectory point; received {len(points)}.",
                details={"scope": scope, "source": source, "point_count": len(points)},
            )

        point = points[0]
        try:
            ensure_float_list(
                point.positions,
                expected_len=len(expected_joint_names),
                label=f"{source_name} point.positions",
            )
        except Exception as exc:
            return PreflightResult.reject(
                codes.INVALID_GOAL_STRUCTURE,
                str(exc),
                details={"scope": scope, "source": source},
            )
        return PreflightResult.allow()

    def _validate_optional_trajectory_fields(
        self,
        *,
        source_name: str,
        point: Any,
        expected_len: int,
    ) -> PreflightResult:
        for values, label in (
            (point.velocities, f"{source_name} point.velocities"),
            (point.accelerations, f"{source_name} point.accelerations"),
            (point.effort, f"{source_name} point.effort"),
        ):
            if values:
                try:
                    ensure_float_list(values, expected_len=expected_len, label=label)
                except Exception as exc:
                    return PreflightResult.reject(
                        codes.INVALID_GOAL_STRUCTURE,
                        str(exc),
                        details={"source_name": source_name},
                    )

        sec = int(point.time_from_start.sec)
        nanosec = int(point.time_from_start.nanosec)
        if sec < 0 or nanosec < 0 or nanosec >= 1_000_000_000:
            return PreflightResult.reject(
                codes.INVALID_GOAL_STRUCTURE,
                f"{source_name} time_from_start must be non-negative and nanosec < 1_000_000_000.",
                details={"sec": sec, "nanosec": nanosec},
            )
        return PreflightResult.allow()

    def _check_arm_availability(self, *, side: Side, scope: CommandScope) -> PreflightResult:
        state = self._runtime.arm_status(side)
        require_online = (
            self.config.require_dual_online if scope == "dual_arms" else self.config.require_online
        )
        require_enabled = (
            self.config.require_dual_enabled if scope == "dual_arms" else self.config.require_enabled
        )
        if require_online and not state.available:
            return PreflightResult.reject(
                codes.ARM_OFFLINE,
                f"{scope} rejected because {side}_arm is offline.",
                details={"arm": side, "last_error": state.last_error},
            )
        if require_enabled and not state.enabled:
            return PreflightResult.reject(
                codes.ARM_NOT_ENABLED,
                f"{scope} rejected because {side}_arm is not enabled.",
                details={"arm": side},
            )
        return PreflightResult.allow()

    def _load_current_positions(
        self,
        side: Side,
    ) -> tuple[PreflightResult, list[float] | None]:
        try:
            _, current_positions, _ = self._runtime.read_arm_joint_state(side)
        except Exception as exc:
            return (
                PreflightResult.reject(
                    codes.STATE_UNAVAILABLE,
                    f"{side}_arm current state is unavailable: {exc}",
                    details={"arm": side},
                ),
                None,
            )

        age_sec = self._runtime.latest_arm_state_age_sec(side)
        if age_sec is None:
            return (
                PreflightResult.reject(
                    codes.STATE_UNAVAILABLE,
                    f"{side}_arm current state timestamp is unavailable.",
                    details={"arm": side},
                ),
                None,
            )
        if age_sec > self.config.max_state_age_sec:
            return (
                PreflightResult.reject(
                    codes.STATE_TOO_OLD,
                    f"{side}_arm current state is stale: age={age_sec:.3f}s exceeds max_state_age_sec={self.config.max_state_age_sec:.3f}s.",
                    details={"arm": side, "age_sec": age_sec},
                ),
                None,
            )
        return PreflightResult.allow(), current_positions

    def _check_pose_limits(
        self,
        *,
        side: Side,
        current_positions: list[float],
    ) -> PreflightResult:
        joint_names = self._runtime.arm_joint_names(side)
        joint_limits = self._runtime.arm_joint_limits(side)

        violations = find_joints_outside_limits(joint_names, current_positions, joint_limits)
        if violations:
            violation = violations[0]
            return self._limit_status_result(
                code=codes.CURRENT_POSE_OUT_OF_LIMIT,
                message=f"{side}_arm current pose is outside limits: {self._format_limit_status(violation)}",
                status=violation,
                arm=side,
            )

        near_limit = find_joints_near_limits(
            joint_names,
            current_positions,
            joint_limits,
            margin=self.config.near_limit_margin,
        )
        if near_limit and self.config.reject_on_near_limit:
            warning = near_limit[0]
            return self._limit_status_result(
                code=codes.CURRENT_POSE_NEAR_LIMIT,
                message=f"{side}_arm current pose is near a limit: {self._format_limit_status(warning)}",
                status=warning,
                arm=side,
            )

        return PreflightResult.allow()

    def _check_start_deviation(
        self,
        *,
        side: Side,
        current_positions: list[float],
        target_positions: Sequence[float],
        source_name: str,
    ) -> PreflightResult:
        deltas = [
            abs(float(target) - float(current))
            for target, current in zip(target_positions, current_positions, strict=True)
        ]
        max_delta = max(deltas, default=0.0)
        if max_delta > self.config.max_start_deviation:
            joint_index = deltas.index(max_delta) + 1
            joint_name = self._runtime.arm_joint_names(side)[joint_index - 1]
            return PreflightResult.reject(
                codes.START_DEVIATION_TOO_LARGE,
                f"{source_name} rejected because {joint_name} start deviation {max_delta:.6f} exceeds max_start_deviation={self.config.max_start_deviation:.6f}.",
                details={
                    "arm": side,
                    "joint": joint_name,
                    "max_delta": max_delta,
                },
            )
        return PreflightResult.allow()

    def _expected_joint_names_for_scope(self, scope: CommandScope) -> list[str]:
        if scope == "left_arm":
            return self._runtime.arm_joint_names("left")
        if scope == "right_arm":
            return self._runtime.arm_joint_names("right")
        return self._runtime.arm_joint_names("left") + self._runtime.arm_joint_names("right")

    @staticmethod
    def _format_limit_status(status: JointLimitStatus) -> str:
        return (
            f"{status.joint_name} current={status.current:.6f}, "
            f"lower={status.lower}, upper={status.upper}"
        )

    @staticmethod
    def _limit_status_result(
        *,
        code: str,
        message: str,
        status: JointLimitStatus,
        arm: Side,
    ) -> PreflightResult:
        return PreflightResult.reject(
            code,
            message,
            details={
                "arm": arm,
                "joint": status.joint_name,
                "value": status.current,
                "lower": status.lower,
                "upper": status.upper,
                "relation": status.relation,
                "distance": status.distance,
            },
        )

    @staticmethod
    def _load_config(
        path: Path,
        *,
        enabled: bool,
        safety_mode: str,
    ) -> PreflightConfig:
        if not path.is_file():
            raise FileNotFoundError(f"preflight config file does not exist: {path}")

        with path.open("r", encoding="utf-8") as file_obj:
            data = yaml.safe_load(file_obj) or {}

        if not isinstance(data, dict):
            raise ValueError(f"preflight config must be a mapping: {path}")

        config_data = data.get("preflight", data)
        if not isinstance(config_data, dict):
            raise ValueError(f"preflight config section must be a mapping: {path}")

        scopes = config_data.get("scopes") or {
            "left_arm": ["left"],
            "right_arm": ["right"],
            "dual_arms": ["left", "right"],
        }

        return PreflightConfig(
            enabled=bool(enabled) and bool(config_data.get("enabled", True)),
            safety_mode=str(safety_mode or config_data.get("safety_mode", "strict")),
            near_limit_margin=float(config_data.get("near_limit_margin", 0.05)),
            reject_on_near_limit=bool(config_data.get("reject_on_near_limit", True)),
            max_start_deviation=float(config_data.get("max_start_deviation", 0.35)),
            max_state_age_sec=float(config_data.get("max_state_age_sec", 0.5)),
            require_online=bool(config_data.get("require_online", True)),
            require_enabled=bool(config_data.get("require_enabled", True)),
            require_dual_online=bool(config_data.get("require_dual_online", True)),
            require_dual_enabled=bool(config_data.get("require_dual_enabled", True)),
            scopes={
                str(key): [str(item) for item in _as_list(value)]
                for key, value in scopes.items()
            },
        )


def _as_list(value: Any) -> Iterable[Any]:
    if isinstance(value, list):
        return value
    return [value]
