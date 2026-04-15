from pathlib import Path

import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, LogInfo, OpaqueFunction, RegisterEventHandler, SetEnvironmentVariable, TimerAction
from launch.conditions import IfCondition, UnlessCondition
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
    with_gz_gui = LaunchConfiguration("with_gz_gui").perform(context)
    spawn_sim_controllers = LaunchConfiguration("spawn_sim_controllers").perform(context)
    sim_control_hardware_plugin = LaunchConfiguration("sim_control_hardware_plugin").perform(context)
    sim_control_system_plugin = LaunchConfiguration("sim_control_system_plugin").perform(context)
    sim_control_system_plugin_name = LaunchConfiguration("sim_control_system_plugin_name").perform(context)
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)
    gz_resource_path = EnvironmentVariable("GZ_SIM_RESOURCE_PATH", default_value="").perform(context)
    ign_system_plugin_path = EnvironmentVariable("IGN_GAZEBO_SYSTEM_PLUGIN_PATH", default_value="").perform(context)
    return [
        LogInfo(msg=f"[sim] backend -> {backend}"),
        LogInfo(msg=f"[sim] world_file -> {world_file}"),
        LogInfo(msg=f"[sim] with_moveit -> {with_moveit}"),
        LogInfo(msg=f"[sim] with_rviz -> {with_rviz}"),
        LogInfo(msg=f"[sim] with_gz_gui -> {with_gz_gui}"),
        LogInfo(msg=f"[sim] spawn_sim_controllers -> {spawn_sim_controllers}"),
        LogInfo(msg=f"[sim] sim_control_hardware_plugin -> {sim_control_hardware_plugin}"),
        LogInfo(msg=f"[sim] sim_control_system_plugin -> {sim_control_system_plugin}"),
        LogInfo(msg=f"[sim] sim_control_system_plugin_name -> {sim_control_system_plugin_name}"),
        LogInfo(msg=f"[sim] use_sim_time -> {use_sim_time}"),
        LogInfo(msg=f"[sim] GZ_SIM_RESOURCE_PATH -> {gz_resource_path}"),
        LogInfo(msg=f"[sim] IGN_GAZEBO_SYSTEM_PLUGIN_PATH -> {ign_system_plugin_path}"),
        LogInfo(
            msg="[sim] contract -> task entry, MoveIt groups, controller names, "
            "and FollowJointTrajectory remain aligned with P1-P4."
        ),
    ]


def _controller_spawner_nodes():
    return [
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
            output="screen",
        ),
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["left_arm_controller", "--controller-manager", "/controller_manager"],
            output="screen",
        ),
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["right_arm_controller", "--controller-manager", "/controller_manager"],
            output="screen",
        ),
    ]


def _maybe_spawn_controllers(context, spawn_robot, *_args, **_kwargs):
    if LaunchConfiguration("spawn_sim_controllers").perform(context).lower() != "true":
        return [
            LogInfo(
                msg="[sim] controller spawning -> disabled; "
                "expect ign_ros2_control/controller_manager to load and activate controllers."
            )
        ]

    return [
        LogInfo(msg="[sim] controller spawning -> enabled fallback path via controller_manager spawners."),
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_robot,
                on_exit=[
                    TimerAction(
                        period=3.0,
                        actions=_controller_spawner_nodes(),
                    )
                ],
            )
        ),
    ]


def generate_launch_description():
    defaults = _load_defaults()
    description_pkg = FindPackageShare("dual_nero_description")
    moveit_pkg = FindPackageShare("dual_nero_moveit_config")
    bringup_pkg = FindPackageShare("dual_nero_bringup")
    ign_control_pkg = FindPackageShare("ign_ros2_control")
    description_model_root = PathJoinSubstitution([description_pkg, ".."])
    bringup_model_root = PathJoinSubstitution([bringup_pkg, ".."])
    ign_control_lib_path = PathJoinSubstitution([ign_control_pkg, "..", "..", "lib"])

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
            "hardware_plugin:=",
            LaunchConfiguration("sim_control_hardware_plugin"),
            " ",
            "sim_system_plugin_filename:=",
            LaunchConfiguration("sim_control_system_plugin"),
            " ",
            "sim_system_plugin_name:=",
            LaunchConfiguration("sim_control_system_plugin_name"),
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

    gz_sim_server = ExecuteProcess(
        cmd=[
            "ign",
            "gazebo",
            "-r",
            LaunchConfiguration("world_file"),
            "-s",
        ],
        condition=UnlessCondition(LaunchConfiguration("with_gz_gui")),
        output="screen",
    )

    gz_sim_gui = ExecuteProcess(
        cmd=[
            "ign",
            "gazebo",
            "-r",
            LaunchConfiguration("world_file"),
            "-g",
        ],
        condition=IfCondition(LaunchConfiguration("with_gz_gui")),
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
            DeclareLaunchArgument(
                "with_gz_gui",
                default_value=str(defaults.get("with_gz_gui", False)).lower(),
                description="Whether to start Gazebo GUI. Default false to avoid Ogre2 GUI crashes on current assets.",
            ),
            DeclareLaunchArgument(
                "spawn_sim_controllers",
                default_value=str(defaults.get("spawn_sim_controllers", False)).lower(),
                description="Whether to manually spawn sim controllers after model creation. Default false because gz_ros2_control already activates them in the current sim path.",
            ),
            DeclareLaunchArgument(
                "sim_control_hardware_plugin",
                default_value=str(defaults.get("sim_control_hardware_plugin", "ign_ros2_control/IgnitionSystem")),
                description="ros2_control hardware plugin used by the sim robot description.",
            ),
            DeclareLaunchArgument(
                "sim_control_system_plugin",
                default_value=str(defaults.get("sim_control_system_plugin", "libign_ros2_control-system.so")),
                description="Gazebo system plugin library used to host ros2_control in ign gazebo.",
            ),
            DeclareLaunchArgument(
                "sim_control_system_plugin_name",
                default_value=str(defaults.get("sim_control_system_plugin_name", "ign_ros2_control::IgnitionROS2ControlPlugin")),
                description="Gazebo system plugin class name used to host ros2_control in ign gazebo.",
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
            SetEnvironmentVariable(
                name="IGN_GAZEBO_SYSTEM_PLUGIN_PATH",
                value=[
                    ign_control_lib_path,
                    ":",
                    EnvironmentVariable("IGN_GAZEBO_SYSTEM_PLUGIN_PATH", default_value=""),
                ],
            ),
            SetEnvironmentVariable(
                name="GZ_SIM_SYSTEM_PLUGIN_PATH",
                value=[
                    ign_control_lib_path,
                    ":",
                    EnvironmentVariable("GZ_SIM_SYSTEM_PLUGIN_PATH", default_value=""),
                ],
            ),
            OpaqueFunction(function=_startup_logs),
            gz_sim_server,
            gz_sim_gui,
            clock_bridge,
            robot_state_publisher,
            spawn_robot,
            OpaqueFunction(function=_maybe_spawn_controllers, args=[spawn_robot]),
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
