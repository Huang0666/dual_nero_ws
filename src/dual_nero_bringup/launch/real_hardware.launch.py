from pathlib import Path

import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _load_defaults() -> dict:
    config_path = Path(__file__).resolve().parents[1] / "config" / "real_execution.yaml"
    with config_path.open("r", encoding="utf-8") as file_obj:
        return (yaml.safe_load(file_obj) or {}).get("real_execution", {})


def _startup_checks(context, *_args, **_kwargs):
    hardware_config = Path(LaunchConfiguration("hardware_config").perform(context))
    preflight_config = Path(LaunchConfiguration("preflight_config_path").perform(context))
    preflight_enabled = LaunchConfiguration("preflight_enabled").perform(context)
    safety_mode = LaunchConfiguration("safety_mode").perform(context)

    if not hardware_config.is_file():
        raise RuntimeError(f"hardware_config does not exist: {hardware_config}")
    if not preflight_config.is_file():
        raise RuntimeError(f"preflight_config_path does not exist: {preflight_config}")

    with hardware_config.open("r", encoding="utf-8") as file_obj:
        hardware_data = yaml.safe_load(file_obj) or {}
    with preflight_config.open("r", encoding="utf-8") as file_obj:
        preflight_data = yaml.safe_load(file_obj) or {}

    left_channel = (
        (((hardware_data.get("left_arm") or {}).get("can") or {}).get("channel"))
    )
    right_channel = (
        (((hardware_data.get("right_arm") or {}).get("can") or {}).get("channel"))
    )

    if not left_channel:
        raise RuntimeError("left_arm.can.channel is missing from hardware_config.")
    if not right_channel:
        raise RuntimeError("right_arm.can.channel is missing from hardware_config.")

    preflight_config_data = preflight_data.get("preflight", preflight_data)
    if not isinstance(preflight_config_data, dict):
        raise RuntimeError(f"preflight config section must be a mapping: {preflight_config}")

    moveit_joint_limits_path = _resolve_preflight_reference(
        preflight_config,
        preflight_config_data.get("moveit_joint_limits_path"),
    )
    if moveit_joint_limits_path is None:
        raise RuntimeError(
            "preflight.moveit_joint_limits_path is required for startup consistency checks."
        )
    if not moveit_joint_limits_path.is_file():
        raise RuntimeError(
            f"preflight.moveit_joint_limits_path does not exist: {moveit_joint_limits_path}"
        )

    _assert_joint_limit_consistency(
        hardware_config=hardware_config,
        hardware_data=hardware_data,
        moveit_joint_limits_path=moveit_joint_limits_path,
    )

    return [
        LogInfo(msg=f"[bringup] left_arm channel -> {left_channel}"),
        LogInfo(msg=f"[bringup] right_arm channel -> {right_channel}"),
        LogInfo(msg=f"[bringup] preflight_enabled -> {preflight_enabled}"),
        LogInfo(msg=f"[bringup] preflight_config_path -> {preflight_config}"),
        LogInfo(msg=f"[bringup] safety_mode -> {safety_mode}"),
        LogInfo(msg=f"[bringup] moveit_joint_limits_path -> {moveit_joint_limits_path}"),
        LogInfo(
            msg="[bringup] note -> current USB-CAN strategy still relies on can0/can1 ordering; "
            "reconfirm mapping after any unplug/replug and restart real_hardware.launch.py."
        ),
    ]


def _resolve_preflight_reference(preflight_config: Path, raw_path: object) -> Path | None:
    if raw_path in (None, ""):
        return None
    candidate = Path(str(raw_path))
    if candidate.is_absolute():
        return candidate
    return (preflight_config.parent / candidate).resolve()


def _assert_joint_limit_consistency(
    *,
    hardware_config: Path,
    hardware_data: dict,
    moveit_joint_limits_path: Path,
) -> None:
    hardware_limits = _load_bridge_joint_limits(hardware_data)
    moveit_limits = _load_moveit_joint_limits(moveit_joint_limits_path)
    missing = sorted(set(hardware_limits) ^ set(moveit_limits))
    if missing:
        raise RuntimeError(
            "Bridge and MoveIt joint limit sets differ. "
            f"hardware_config={hardware_config}, moveit_joint_limits_path={moveit_joint_limits_path}, "
            f"mismatched_joints={missing}"
        )

    for joint_name in sorted(hardware_limits):
        bridge_lower, bridge_upper = hardware_limits[joint_name]
        moveit_lower, moveit_upper = moveit_limits[joint_name]
        if bridge_lower != moveit_lower or bridge_upper != moveit_upper:
            raise RuntimeError(
                "Bridge and MoveIt joint limits differ for "
                f"{joint_name}: bridge=({bridge_lower}, {bridge_upper}) "
                f"moveit=({moveit_lower}, {moveit_upper}). "
                f"hardware_config={hardware_config}, moveit_joint_limits_path={moveit_joint_limits_path}"
            )


def _load_bridge_joint_limits(hardware_data: dict) -> dict[str, tuple[float | None, float | None]]:
    limits: dict[str, tuple[float | None, float | None]] = {}
    for arm_key in ("left_arm", "right_arm"):
        arm_data = hardware_data.get(arm_key)
        if not isinstance(arm_data, dict):
            raise RuntimeError(f"Missing or invalid '{arm_key}' mapping in hardware_config.")
        arm_limits = arm_data.get("joint_position_limits")
        if not isinstance(arm_limits, dict):
            raise RuntimeError(f"{arm_key}.joint_position_limits must be a mapping.")
        for joint_name, limit_data in arm_limits.items():
            if not isinstance(limit_data, dict):
                raise RuntimeError(f"{arm_key}.joint_position_limits.{joint_name} must be a mapping.")
            limits[str(joint_name)] = (
                _optional_float(limit_data.get("lower")),
                _optional_float(limit_data.get("upper")),
            )
    return limits


def _load_moveit_joint_limits(path: Path) -> dict[str, tuple[float | None, float | None]]:
    with path.open("r", encoding="utf-8") as file_obj:
        moveit_data = yaml.safe_load(file_obj) or {}
    moveit_limits_data = moveit_data.get("joint_limits")
    if not isinstance(moveit_limits_data, dict):
        raise RuntimeError(f"joint_limits mapping is missing from MoveIt config: {path}")

    limits: dict[str, tuple[float | None, float | None]] = {}
    for joint_name, limit_data in moveit_limits_data.items():
        if not isinstance(limit_data, dict):
            raise RuntimeError(f"joint_limits.{joint_name} must be a mapping in {path}")
        has_position_limits = bool(limit_data.get("has_position_limits", False))
        limits[str(joint_name)] = (
            _optional_float(limit_data.get("min_position")) if has_position_limits else None,
            _optional_float(limit_data.get("max_position")) if has_position_limits else None,
        )
    return limits


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def generate_launch_description():
    defaults = _load_defaults()
    bridge_config = PathJoinSubstitution(
        [FindPackageShare("dual_nero_bridge"), "config", "hardware_params.yaml"]
    )
    preflight_config = PathJoinSubstitution(
        [FindPackageShare("dual_nero_bridge"), "config", "preflight.yaml"]
    )
    bridge_launch = PathJoinSubstitution(
        [FindPackageShare("dual_nero_bridge"), "launch", "real_hardware_bridge.launch.py"]
    )
    rsp_launch = PathJoinSubstitution(
        [FindPackageShare("dual_nero_moveit_config"), "launch", "rsp.launch.py"]
    )
    move_group_launch = PathJoinSubstitution(
        [FindPackageShare("dual_nero_moveit_config"), "launch", "move_group.launch.py"]
    )
    rviz_launch = PathJoinSubstitution(
        [FindPackageShare("dual_nero_moveit_config"), "launch", "moveit_rviz.launch.py"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "hardware_config",
                default_value=defaults.get("hardware_config") or bridge_config,
                description="Path to the real hardware execution config.",
            ),
            DeclareLaunchArgument(
                "allow_motion",
                default_value=str(defaults.get("allow_motion", False)).lower(),
                description="Whether the real hardware bridge may execute motion commands.",
            ),
            DeclareLaunchArgument(
                "enable_on_start",
                default_value=str(defaults.get("enable_on_start", False)).lower(),
                description="Whether both arms should be enabled on startup.",
            ),
            DeclareLaunchArgument(
                "publish_rate_hz",
                default_value=str(defaults.get("publish_rate_hz", 50.0)),
                description="Real joint state publish rate.",
            ),
            DeclareLaunchArgument(
                "preflight_enabled",
                default_value=str(defaults.get("preflight_enabled", True)).lower(),
                description="Whether runtime preflight checks are enabled.",
            ),
            DeclareLaunchArgument(
                "preflight_config_path",
                default_value=defaults.get("preflight_config_path") or preflight_config,
                description="Path to the runtime preflight config file.",
            ),
            DeclareLaunchArgument(
                "safety_mode",
                default_value=str(defaults.get("safety_mode", "strict")),
                description="Safety mode label exposed to the runtime preflight checker.",
            ),
            DeclareLaunchArgument(
                "with_moveit",
                default_value=str(defaults.get("with_moveit", True)).lower(),
                description="Whether to start move_group for real hardware execution.",
            ),
            DeclareLaunchArgument(
                "with_rviz",
                default_value=str(defaults.get("with_rviz", False)).lower(),
                description="Whether to start the MoveIt RViz configuration.",
            ),
            OpaqueFunction(function=_startup_checks),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(bridge_launch),
                launch_arguments={
                    "config_path": LaunchConfiguration("hardware_config"),
                    "allow_motion": LaunchConfiguration("allow_motion"),
                    "enable_on_start": LaunchConfiguration("enable_on_start"),
                    "publish_rate_hz": LaunchConfiguration("publish_rate_hz"),
                    "preflight_enabled": LaunchConfiguration("preflight_enabled"),
                    "preflight_config_path": LaunchConfiguration("preflight_config_path"),
                    "safety_mode": LaunchConfiguration("safety_mode"),
                }.items(),
            ),
            IncludeLaunchDescription(PythonLaunchDescriptionSource(rsp_launch)),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(move_group_launch),
                condition=IfCondition(LaunchConfiguration("with_moveit")),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(rviz_launch),
                condition=IfCondition(LaunchConfiguration("with_rviz")),
            ),
        ]
    )
