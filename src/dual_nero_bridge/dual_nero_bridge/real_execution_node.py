from __future__ import annotations

import rclpy
import rclpy.logging
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from .follow_joint_trajectory_server import SingleArmFollowJointTrajectoryServer
from .joint_command_bridge import JointCommandBridge
from .joint_state_bridge import JointStateBridge
from .logging_utils import log_fatal, log_state
from .runtime import DualNeroBridgeRuntime


class RealExecutionNode(Node):
    def __init__(self) -> None:
        super().__init__("dual_nero_real_execution")
        self.declare_parameter("config_path", "")
        self.declare_parameter("publish_rate_hz", 50.0)
        self.declare_parameter("allow_motion", False)
        self.declare_parameter("enable_on_start", False)

        config_path = str(self.get_parameter("config_path").value)
        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        allow_motion = _coerce_bool(self.get_parameter("allow_motion").value)
        enable_on_start = _coerce_bool(self.get_parameter("enable_on_start").value)

        if not config_path:
            raise ValueError("config_path parameter must not be empty.")

        self.runtime = DualNeroBridgeRuntime(
            config_path=config_path,
            allow_motion=allow_motion,
            enable_on_start=enable_on_start,
        )
        self.runtime.connect()
        self.runtime.enable_if_requested()
        self.joint_state_bridge = JointStateBridge(
            self,
            self.runtime,
            publish_rate_hz=publish_rate_hz,
        )
        self.joint_command_bridge = JointCommandBridge(self, self.runtime)
        self.left_trajectory_server = SingleArmFollowJointTrajectoryServer(
            self,
            self.runtime,
            side="left",
        )
        self.right_trajectory_server = SingleArmFollowJointTrajectoryServer(
            self,
            self.runtime,
            side="right",
        )
        log_state(
            self.get_logger(),
            "startup",
            "real_hardware_execution bridge started; "
            f"allow_motion={allow_motion}, enable_on_start={enable_on_start}, "
            f"publish_rate_hz={publish_rate_hz}, {self.runtime.availability_summary()}",
        )
        if not (self.runtime.left_state.available and self.runtime.right_state.available):
            log_state(
                self.get_logger(),
                "startup",
                "bridge is running in degraded mode; only available arms accept arm-local commands, "
                "dual-arm commands and full /joint_states are rejected until both arms recover.",
            )

    def shutdown_runtime(self) -> None:
        try:
            self.runtime.disable_all()
        except Exception:
            pass
        try:
            self.runtime.close()
        except Exception:
            pass


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node: RealExecutionNode | None = None
    executor = MultiThreadedExecutor(num_threads=4)
    logger = rclpy.logging.get_logger("dual_nero_real_execution")
    exit_code = 0
    try:
        node = RealExecutionNode()
        executor.add_node(node)
        executor.spin()
    except Exception as exc:
        log_fatal(logger, "startup", str(exc))
        exit_code = 1
    finally:
        executor.shutdown()
        if node is not None:
            node.shutdown_runtime()
            node.destroy_node()
        rclpy.shutdown()
    if exit_code != 0:
        raise SystemExit(exit_code)


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
