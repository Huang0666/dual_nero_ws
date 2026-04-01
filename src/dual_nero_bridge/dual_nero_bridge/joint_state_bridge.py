from __future__ import annotations

from sensor_msgs.msg import JointState

from .runtime import DualNeroBridgeRuntime


class JointStateBridge:
    def __init__(
        self,
        node,
        runtime: DualNeroBridgeRuntime,
        *,
        publish_rate_hz: float,
    ) -> None:
        self._node = node
        self._runtime = runtime
        self._publisher = node.create_publisher(JointState, "/joint_states", 10)
        self._velocity_warning_emitted = False
        self._last_error: str | None = None
        period_sec = 1.0 / max(float(publish_rate_hz), 1.0)
        self._timer = node.create_timer(period_sec, self.publish_once)

    def publish_once(self) -> None:
        try:
            names, positions, velocities = self._runtime.read_joint_state()
            msg = JointState()
            msg.header.stamp = self._node.get_clock().now().to_msg()
            msg.name = names
            msg.position = positions
            if velocities is not None:
                msg.velocity = velocities
            elif not self._velocity_warning_emitted:
                self._node.get_logger().info(
                    "dual_nero_bridge: backend does not provide joint velocities; "
                    "publishing /joint_states without velocity values."
                )
                self._velocity_warning_emitted = True
            self._publisher.publish(msg)
            self._last_error = None
        except Exception as exc:
            error_text = str(exc)
            if error_text != self._last_error:
                self._node.get_logger().error(
                    f"Failed to publish /joint_states from real hardware: {error_text}"
                )
                self._last_error = error_text
