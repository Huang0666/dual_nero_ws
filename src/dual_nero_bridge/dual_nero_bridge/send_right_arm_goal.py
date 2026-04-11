from __future__ import annotations

from dual_nero_bridge.single_arm_goal_cli import run_single_arm_goal


def main() -> int:
    return run_single_arm_goal(side="right")


if __name__ == "__main__":
    raise SystemExit(main())
