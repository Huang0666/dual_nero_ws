from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .exceptions import ConfigError, ValidationError
from .safety import ensure_float_list, validate_joint_names
from .types import ArmConfig, CANConfig, JointLimit, PyAgxOptions


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    yaml_path = Path(path)
    if not yaml_path.is_file():
        raise ConfigError(f"Configuration file does not exist: {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}

    if not isinstance(data, dict):
        raise ConfigError(f"Top-level YAML content must be a mapping: {yaml_path}")

    return data


def load_dual_arm_config(path: str | Path) -> tuple[ArmConfig, ArmConfig]:
    data = load_yaml_file(path)
    left_arm = build_arm_config(data, "left_arm")
    right_arm = build_arm_config(data, "right_arm")
    return left_arm, right_arm


def build_arm_config(data: dict[str, Any], arm_key: str) -> ArmConfig:
    arm_data = data.get(arm_key)
    if not isinstance(arm_data, dict):
        raise ConfigError(f"Missing or invalid '{arm_key}' mapping in configuration.")

    side = arm_data.get("side")
    if side not in ("left", "right"):
        raise ConfigError(f"{arm_key}.side must be 'left' or 'right', got {side!r}.")

    can_data = _require_mapping(arm_data.get("can"), f"{arm_key}.can")
    pyagx_data = _require_mapping(arm_data.get("pyagx"), f"{arm_key}.pyagx")

    joint_names = arm_data.get("joint_names")
    if not isinstance(joint_names, list):
        raise ConfigError(f"{arm_key}.joint_names must be a list.")
    validate_joint_names(side, [str(joint_name) for joint_name in joint_names])

    return ArmConfig(
        name=str(arm_data.get("name", arm_key)),
        side=side,
        can=CANConfig(
            channel=str(can_data.get("channel", "")),
            interface=str(can_data.get("interface", "can")),
            bitrate=_optional_int(can_data.get("bitrate")),
        ),
        pyagx=PyAgxOptions(
            enable_check_can=bool(pyagx_data.get("enable_check_can", True)),
            auto_connect=bool(pyagx_data.get("auto_connect", False)),
            timeout=_positive_float(
                pyagx_data.get("timeout", 5.0),
                f"{arm_key}.pyagx.timeout",
            ),
        ),
        joint_names=[str(joint_name) for joint_name in joint_names],
        max_speed_percent=_optional_positive_float(
            arm_data.get("max_speed_percent"),
            f"{arm_key}.max_speed_percent",
        ),
        dry_run=bool(arm_data.get("dry_run", False)),
        joint_position_limits=_load_joint_limits(
            arm_data.get("joint_position_limits"),
            arm_key,
        ),
    )


def parse_target_csv(target_csv: str, *, label: str) -> list[float]:
    parts = [part.strip() for part in target_csv.split(",") if part.strip()]
    return ensure_float_list(parts, expected_len=7, label=label)


def build_small_offset_target(
    current_positions: list[float],
    *,
    delta: float = 0.05,
    joint_index: int = 0,
) -> list[float]:
    if joint_index < 0 or joint_index >= len(current_positions):
        raise ValidationError(
            f"joint_index must be in [0, {len(current_positions) - 1}], got {joint_index}."
        )
    target = list(current_positions)
    target[joint_index] += float(delta)
    return target


def dump_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be a mapping.")
    return value


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _positive_float(value: Any, label: str) -> float:
    normalized = float(value)
    if normalized <= 0.0:
        raise ConfigError(f"{label} must be positive, got {normalized}.")
    return normalized


def _optional_positive_float(value: Any, label: str) -> float | None:
    if value is None:
        return None
    return _positive_float(value, label)


def _load_joint_limits(value: Any, arm_key: str) -> dict[str, JointLimit]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ConfigError(f"{arm_key}.joint_position_limits must be a mapping.")

    joint_limits: dict[str, JointLimit] = {}
    for joint_name, limit_data in value.items():
        if not isinstance(limit_data, dict):
            raise ConfigError(
                f"{arm_key}.joint_position_limits.{joint_name} must be a mapping."
            )
        lower = limit_data.get("lower")
        upper = limit_data.get("upper")
        joint_limits[str(joint_name)] = JointLimit(
            lower=float(lower) if lower is not None else None,
            upper=float(upper) if upper is not None else None,
        )
    return joint_limits
