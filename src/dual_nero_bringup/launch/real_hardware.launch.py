from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from pathlib import Path

import yaml


def _load_defaults() -> dict:
    config_path = Path(__file__).resolve().parents[1] / "config" / "real_execution.yaml"
    with config_path.open("r", encoding="utf-8") as file_obj:
        return (yaml.safe_load(file_obj) or {}).get("real_execution", {})


def generate_launch_description():
    defaults = _load_defaults()
    bridge_config = PathJoinSubstitution(
        [FindPackageShare("dual_nero_bridge"), "config", "hardware_params.yaml"]
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
                "with_moveit",
                default_value=str(defaults.get("with_moveit", True)).lower(),
                description="Whether to start move_group for real hardware execution.",
            ),
            DeclareLaunchArgument(
                "with_rviz",
                default_value=str(defaults.get("with_rviz", False)).lower(),
                description="Whether to start the MoveIt RViz configuration.",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(bridge_launch),
                launch_arguments={
                    "config_path": LaunchConfiguration("hardware_config"),
                    "allow_motion": LaunchConfiguration("allow_motion"),
                    "enable_on_start": LaunchConfiguration("enable_on_start"),
                    "publish_rate_hz": LaunchConfiguration("publish_rate_hz"),
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
