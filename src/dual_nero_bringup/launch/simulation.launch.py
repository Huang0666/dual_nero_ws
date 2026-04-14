from pathlib import Path

import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, LogInfo, OpaqueFunction, RegisterEventHandler, SetEnvironmentVariable, TimerAction
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import FindExecutable


def _load_defaults() -> dict:
    config_path = Path(__file__).resolve().parents[1] / "config" / "simulation.yaml"
    with config_path.open("r", encoding="utf-8") as file_obj:
        return (yaml.safe_load(file_obj) or {}).get("simulation", {})


def _startup_logs(context, *_args, **_kwargs):
    backend = LaunchConfiguration("backend").perform(context)
    world_file = LaunchConfiguration("world_file").perform(context)
    with_moveit = LaunchConfiguration("with_moveit").perform(context)
    with_rviz = LaunchConfiguration("with_rviz").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)
    gz_resource_path = EnvironmentVariable("GZ_SIM_RESOURCE_PATH", default_value="").perform(context)
    return [
        LogInfo(msg=f"[sim] backend -> {backend}"),
        LogInfo(msg=f"[sim] world_file -> {world_file}"),
        LogInfo(msg=f"[sim] with_moveit -> {with_moveit}"),
        LogInfo(msg=f"[sim] with_rviz -> {with_rviz}"),
        LogInfo(msg=f"[sim] use_sim_time -> {use_sim_time}"),
        LogInfo(msg=f"[sim] GZ_SIM_RESOURCE_PATH -> {gz_resource_path}"),
        LogInfo(
            msg="[sim] contract -> task entry, MoveIt groups, controller names, "
            "and FollowJointTrajectory remain aligned with P1-P4."
        ),
    ]


def generate_launch_description():
    defaults = _load_defaults()
    description_pkg = FindPackageShare("dual_nero_description")
    moveit_pkg = FindPackageShare("dual_nero_moveit_config")
    bringup_pkg = FindPackageShare("dual_nero_bringup")
    description_model_root = PathJoinSubstitution([description_pkg, ".."])
    bringup_model_root = PathJoinSubstitution([bringup_pkg, ".."])

    default_world = PathJoinSubstitution([bringup_pkg, "worlds", "dual_nero_empty.sdf"])
    controllers_file = PathJoinSubstitution([moveit_pkg, "config", "ros2_controllers.yaml"])
    initial_positions_file = PathJoinSubstitution([moveit_pkg, "config", "initial_positions.yaml"])
    xacro_file = PathJoinSubstitution([moveit_pkg, "config", "dual_nero_description.urdf.xacro"])
    move_group_launch = PathJoinSubstitution([moveit_pkg, "launch", "move_group.launch.py"])
    rviz_launch = PathJoinSubstitution([moveit_pkg, "launch", "moveit_rviz.launch.py"])

    robot_description = Command(
        [
            FindExecutable(name="xacro"),
            " ",
            xacro_file,
            " ",
            "initial_positions_file:=",
            initial_positions_file,
            " ",
            "hardware_plugin:=gz_ros2_control/GazeboSimSystem",
            " ",
            "use_gz_sim:=true",
            " ",
            "controllers_file:=",
            controllers_file,
        ]
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": LaunchConfiguration("use_sim_time"),
            }
        ],
    )

    gz_sim = ExecuteProcess(
        cmd=[
            "ign",
            "gazebo",
            "-r",
            LaunchConfiguration("world_file"),
        ],
        output="screen",
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            LaunchConfiguration("robot_name"),
            "-allow_renaming",
            "false",
            "-z",
            LaunchConfiguration("z_offset"),
        ],
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        output="screen",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )
    left_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["left_arm_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )
    right_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["right_arm_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    spawn_controllers = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_robot,
            on_exit=[
                TimerAction(
                    period=3.0,
                    actions=[
                        joint_state_broadcaster,
                        left_controller,
                        right_controller,
                    ],
                )
            ],
        )
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "backend",
                default_value=str(defaults.get("backend", "sim_gz")),
                description="Simulation backend label for operator-facing logs.",
            ),
            DeclareLaunchArgument(
                "world_file",
                default_value=defaults.get("world_file") or default_world,
                description="SDF world file used by gz sim.",
            ),
            DeclareLaunchArgument(
                "robot_name",
                default_value=str(defaults.get("robot_name", "dual_nero")),
                description="Model name inside gz sim.",
            ),
            DeclareLaunchArgument(
                "z_offset",
                default_value=str(defaults.get("z_offset", 0.0)),
                description="Spawn Z offset in meters.",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value=str(defaults.get("use_sim_time", True)).lower(),
                description="Whether to use Gazebo /clock.",
            ),
            DeclareLaunchArgument(
                "with_moveit",
                default_value=str(defaults.get("with_moveit", True)).lower(),
                description="Whether to start move_group for simulation.",
            ),
            DeclareLaunchArgument(
                "with_rviz",
                default_value=str(defaults.get("with_rviz", True)).lower(),
                description="Whether to start MoveIt RViz.",
            ),
            SetEnvironmentVariable(
                name="GZ_SIM_RESOURCE_PATH",
                value=[
                    description_model_root,
                    ":",
                    bringup_model_root,
                    ":",
                    EnvironmentVariable("GZ_SIM_RESOURCE_PATH", default_value=""),
                ],
            ),
            OpaqueFunction(function=_startup_logs),
            gz_sim,
            clock_bridge,
            robot_state_publisher,
            spawn_robot,
            spawn_controllers,
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
