from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .exceptions import SafetyError, ValidationError
from .types import JointLimit, Side


EXPECTED_JOINT_COUNT = 7


@dataclass(slots=True)
class JointLimitStatus:
    joint_name: str
    current: float
    lower: float | None
    upper: float | None
    relation: str
    distance: float | None = None


def expected_joint_names(side: Side) -> list[str]:
    return [f"{side}_joint{index}" for index in range(1, EXPECTED_JOINT_COUNT + 1)]


def validate_joint_names(side: Side, joint_names: list[str]) -> list[str]:
    expected = expected_joint_names(side)
    if joint_names != expected:
        raise ValidationError(
            f"{side}_arm joint_names must exactly match {expected}, got {joint_names}."
        )
    return joint_names


def ensure_float_list(
    values: Iterable[float | int],
    *,
    expected_len: int,
    label: str,
) -> list[float]:
    try:
        normalized = [float(value) for value in values]
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{label} must be a numeric sequence.") from exc

    if len(normalized) != expected_len:
        raise ValidationError(
            f"{label} must contain exactly {expected_len} values, got {len(normalized)}."
        )

    return normalized


def clamp_speed_percent(
    requested_speed: float | None,
    max_speed_percent: float | None,
) -> float | None:
    if requested_speed is None:
        return max_speed_percent

    speed = float(requested_speed)
    if speed <= 0.0:
        raise SafetyError(f"speed must be positive, got {speed}.")
    if speed > 100.0:
        raise SafetyError(f"speed must be <= 100.0 percent, got {speed}.")

    if max_speed_percent is not None:
        max_speed = float(max_speed_percent)
        if max_speed <= 0.0:
            raise SafetyError(
                f"Configured max_speed_percent must be positive, got {max_speed}."
            )
        return min(speed, max_speed)

    return speed


def validate_target_with_limits(
    joint_names: list[str],
    target: list[float],
    joint_limits: dict[str, JointLimit] | None,
) -> list[float]:
    if not joint_limits:
        return target

    for joint_name, joint_value in zip(joint_names, target, strict=True):
        joint_limit = joint_limits.get(joint_name)
        if joint_limit is None:
            continue
        if joint_limit.lower is not None and joint_value < joint_limit.lower:
            raise SafetyError(
                f"Target for {joint_name}={joint_value} is below lower limit {joint_limit.lower}."
            )
        if joint_limit.upper is not None and joint_value > joint_limit.upper:
            raise SafetyError(
                f"Target for {joint_name}={joint_value} is above upper limit {joint_limit.upper}."
            )

    return target


def find_joints_outside_limits(
    joint_names: list[str],
    positions: list[float],
    joint_limits: dict[str, JointLimit] | None,
) -> list[JointLimitStatus]:
    if not joint_limits:
        return []

    violations: list[JointLimitStatus] = []
    for joint_name, joint_value in zip(joint_names, positions, strict=True):
        joint_limit = joint_limits.get(joint_name)
        if joint_limit is None:
            continue
        if joint_limit.lower is not None and joint_value < joint_limit.lower:
            violations.append(
                JointLimitStatus(
                    joint_name=joint_name,
                    current=joint_value,
                    lower=joint_limit.lower,
                    upper=joint_limit.upper,
                    relation="below_lower",
                    distance=joint_limit.lower - joint_value,
                )
            )
        elif joint_limit.upper is not None and joint_value > joint_limit.upper:
            violations.append(
                JointLimitStatus(
                    joint_name=joint_name,
                    current=joint_value,
                    lower=joint_limit.lower,
                    upper=joint_limit.upper,
                    relation="above_upper",
                    distance=joint_value - joint_limit.upper,
                )
            )

    return violations


def find_joints_near_limits(
    joint_names: list[str],
    positions: list[float],
    joint_limits: dict[str, JointLimit] | None,
    *,
    margin: float = 0.05,
) -> list[JointLimitStatus]:
    if not joint_limits:
        return []
    if margin <= 0.0:
        raise ValidationError(f"near-limit margin must be positive, got {margin}.")

    warnings: list[JointLimitStatus] = []
    for joint_name, joint_value in zip(joint_names, positions, strict=True):
        joint_limit = joint_limits.get(joint_name)
        if joint_limit is None:
            continue

        if joint_limit.lower is not None:
            distance_to_lower = joint_value - joint_limit.lower
            if 0.0 <= distance_to_lower <= margin:
                warnings.append(
                    JointLimitStatus(
                        joint_name=joint_name,
                        current=joint_value,
                        lower=joint_limit.lower,
                        upper=joint_limit.upper,
                        relation="near_lower",
                        distance=distance_to_lower,
                    )
                )
                continue

        if joint_limit.upper is not None:
            distance_to_upper = joint_limit.upper - joint_value
            if 0.0 <= distance_to_upper <= margin:
                warnings.append(
                    JointLimitStatus(
                        joint_name=joint_name,
                        current=joint_value,
                        lower=joint_limit.lower,
                        upper=joint_limit.upper,
                        relation="near_upper",
                        distance=distance_to_upper,
                    )
                )

    return warnings


def targets_within_tolerance(
    current: list[float],
    target: list[float],
    *,
    tolerance: float = 0.01,
) -> bool:
    if len(current) != len(target):
        return False
    return all(
        abs(current_value - target_value) <= tolerance
        for current_value, target_value in zip(current, target, strict=True)
    )
