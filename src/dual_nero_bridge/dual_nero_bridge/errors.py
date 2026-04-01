class DualNeroBridgeError(Exception):
    """Base exception for the dual_nero_bridge package."""


class BridgeStartupError(DualNeroBridgeError):
    """Raised when the bridge cannot reach a usable startup state."""


class BridgeDegradedError(DualNeroBridgeError):
    """Raised when a full-contract read cannot be served in degraded mode."""


class BridgeArmUnavailableError(DualNeroBridgeError):
    """Raised when a command targets an unavailable arm."""


class BridgeMotionRejectedError(DualNeroBridgeError):
    """Raised when motion is rejected by bridge policy or startup mode."""


class BridgeTrajectoryValidationError(DualNeroBridgeError):
    """Raised when a trajectory goal violates the current bridge contract."""
