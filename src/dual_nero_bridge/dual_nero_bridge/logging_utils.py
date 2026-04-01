from __future__ import annotations


def bridge_log_text(level: str, source: str, message: str) -> str:
    return f"[{level}][{source}] {message}"


def log_reject(logger, source: str, message: str) -> None:
    logger.warning(bridge_log_text("REJECT", source, message))


def log_abort(logger, source: str, message: str) -> None:
    logger.error(bridge_log_text("ABORT", source, message))


def log_degraded(logger, source: str, message: str) -> None:
    logger.error(bridge_log_text("DEGRADED", source, message))


def log_state(logger, source: str, message: str) -> None:
    logger.info(bridge_log_text("STATE", source, message))


def log_fatal(logger, source: str, message: str) -> None:
    logger.fatal(bridge_log_text("FATAL", source, message))
