from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare("dual_nero_description")

    xacro_file = PathJoinSubstitution(
        [pkg_share, "urdf", "dual_nero_description.xacro"]
    )

    robot_description = ParameterValue(
        Command(["xacro ", xacro_file]),
        value_type=str
    )

    rviz_config = PathJoinSubstitution(
        [pkg_share, "rviz", "dual_nero.rviz"]
    )

    joint_state_publisher_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        parameters=[{
            "zeros": {
                "left_joint1": 0.0,
                "left_joint2": 1.57079632679,
                "left_joint3": 0.0,
                "left_joint4": 0.0,
                "left_joint5": 0.0,
                "left_joint6": 0.0,
                "left_joint7": 0.0,
                "right_joint1": 0.0,
                "right_joint2": 1.57079632679,
                "right_joint3": 0.0,
                "right_joint4": 0.0,
                "right_joint5": 0.0,
                "right_joint6": 0.0,
                "right_joint7": 0.0
            }
        }]
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[{"robot_description": robot_description}]
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config],
        output="screen"
    )

    return LaunchDescription([
        joint_state_publisher_node,
        robot_state_publisher_node,
        rviz_node,
    ])
