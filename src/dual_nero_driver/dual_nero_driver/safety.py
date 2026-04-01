from __future__ import annotations

from typing import Iterable

from .exceptions import SafetyError, ValidationError
from .types import JointLimit, Side


EXPECTED_JOINT_COUNT = 7


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
