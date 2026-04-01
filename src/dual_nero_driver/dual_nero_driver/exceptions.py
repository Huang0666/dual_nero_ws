class DualNeroDriverError(Exception):
    """Base exception for the dual_nero_driver package."""


class ConfigError(DualNeroDriverError):
    """Raised when driver configuration is missing or invalid."""


class ValidationError(DualNeroDriverError):
    """Raised when user input or API payloads fail validation."""


class SafetyError(ValidationError):
    """Raised when a motion request violates a safety guard."""


class BackendError(DualNeroDriverError):
    """Base exception for backend failures."""


class BackendDependencyError(BackendError):
    """Raised when an optional backend dependency is not available."""


class BackendConnectionError(BackendError):
    """Raised when the backend cannot connect to hardware."""


class BackendTimeoutError(BackendError):
    """Raised when a backend operation times out or returns no data."""


class BackendCommandError(BackendError):
    """Raised when the backend rejects or fails a command."""
