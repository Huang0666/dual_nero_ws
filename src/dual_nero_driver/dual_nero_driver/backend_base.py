from __future__ import annotations

from abc import ABC, abstractmethod


class ArmBackend(ABC):
    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def enable_all(self, timeout_sec: float = 5.0) -> None:
        raise NotImplementedError

    @abstractmethod
    def disable_all(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_joint_positions(self) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    def get_joint_velocities(self) -> list[float] | None:
        raise NotImplementedError

    @abstractmethod
    def get_tcp_pose(self) -> list[float] | None:
        raise NotImplementedError

    @abstractmethod
    def move_j(
        self,
        target: list[float],
        speed: float | None = None,
        wait: bool = False,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def estop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError
