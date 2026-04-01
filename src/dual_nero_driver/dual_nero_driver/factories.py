from __future__ import annotations

from pathlib import Path
from typing import Literal

from .dual_arm_manager import DualArmManager
from .nero_arm import NeroArm
from .pyagx_backend import PyAgxBackend
from .utils import load_dual_arm_config


def build_arm_from_config_path(
    config_path: str | Path,
    side: Literal["left", "right"],
) -> NeroArm:
    left_config, right_config = load_dual_arm_config(config_path)
    arm_config = left_config if side == "left" else right_config
    backend = PyAgxBackend(arm_config)
    return NeroArm(
        arm_name=arm_config.name,
        side=arm_config.side,
        backend=backend,
        joint_names=arm_config.joint_names,
        max_speed_percent=arm_config.max_speed_percent,
        joint_position_limits=arm_config.joint_position_limits,
    )


def build_single_arm_from_file(
    config_path: str | Path,
    side: Literal["left", "right"],
) -> NeroArm:
    return build_arm_from_config_path(config_path, side)


def build_dual_arm_manager_from_file(config_path: str | Path) -> DualArmManager:
    left_arm = build_single_arm_from_file(config_path, "left")
    right_arm = build_single_arm_from_file(config_path, "right")
    return DualArmManager(left_arm=left_arm, right_arm=right_arm)
