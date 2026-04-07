from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config_path = PathJoinSubstitution(
        [FindPackageShare("dual_nero_bridge"), "config", "hardware_params.yaml"]
    )
    preflight_config_path = PathJoinSubstitution(
        [FindPackageShare("dual_nero_bridge"), "config", "preflight.yaml"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config_path",
                default_value=config_path,
                description="Path to the real hardware bridge config file.",
            ),
            DeclareLaunchArgument(
                "allow_motion",
                default_value="false",
                description="Whether the bridge may execute motion commands.",
            ),
            DeclareLaunchArgument(
                "enable_on_start",
                default_value="false",
                description="Whether to enable both arms during startup.",
            ),
            DeclareLaunchArgument(
                "publish_rate_hz",
                default_value="50.0",
                description="Joint state publish rate.",
            ),
            DeclareLaunchArgument(
                "preflight_enabled",
                default_value="true",
                description="Whether runtime preflight checks are enabled.",
            ),
            DeclareLaunchArgument(
                "preflight_config_path",
                default_value=preflight_config_path,
                description="Path to the bridge preflight config file.",
            ),
            DeclareLaunchArgument(
                "safety_mode",
                default_value="strict",
                description="Safety mode label exposed to the bridge runtime.",
            ),
            Node(
                package="dual_nero_bridge",
                executable="real_execution_node",
                name="dual_nero_real_execution",
                output="screen",
                parameters=[
                    {
                        "config_path": LaunchConfiguration("config_path"),
                        "allow_motion": LaunchConfiguration("allow_motion"),
                        "enable_on_start": LaunchConfiguration("enable_on_start"),
                        "publish_rate_hz": LaunchConfiguration("publish_rate_hz"),
                        "preflight_enabled": LaunchConfiguration("preflight_enabled"),
                        "preflight_config_path": LaunchConfiguration("preflight_config_path"),
                        "safety_mode": LaunchConfiguration("safety_mode"),
                    }
                ],
            ),
        ]
    )
