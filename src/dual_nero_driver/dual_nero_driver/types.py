from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


Side = Literal["left", "right"]


@dataclass(slots=True)
class CANConfig:
    channel: str
    interface: str = "socketcan"
    bitrate: int | None = None


@dataclass(slots=True)
class PyAgxOptions:
    enable_check_can: bool = True
    auto_connect: bool = False
    timeout: float = 5.0


@dataclass(slots=True)
class JointLimit:
    lower: float | None = None
    upper: float | None = None


@dataclass(slots=True)
class ArmConfig:
    name: str
    side: Side
    can: CANConfig
    pyagx: PyAgxOptions
    joint_names: list[str]
    max_speed_percent: float | None = None
    dry_run: bool = False
    joint_position_limits: dict[str, JointLimit] = field(default_factory=dict)


@dataclass(slots=True)
class JointStateSnapshot:
    arm_name: str
    side: Side
    joint_names: list[str]
    joint_positions: list[float]
    joint_velocities: list[float] | None
    tcp_pose: list[float] | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
