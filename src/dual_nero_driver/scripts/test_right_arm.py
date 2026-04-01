#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dual_nero_driver.nero_arm import NeroArm
from dual_nero_driver.pyagx_backend import PyAgxBackend
from dual_nero_driver.utils import (
    build_small_offset_target,
    dump_json,
    load_dual_arm_config,
    parse_target_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal right-arm connectivity test.")
    parser.add_argument("--config", required=True, help="Path to arm YAML config.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Send a small move_j command after reading state.",
    )
    parser.add_argument(
        "--target",
        help="Optional comma-separated 7-joint target in driver units.",
    )
    parser.add_argument(
        "--delta",
        type=float,
        default=0.05,
        help="Small default joint offset used when --execute is set without --target.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=None,
        help="Requested speed percent. Clamped by max_speed_percent if configured.",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for motion completion after move_j.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _, right_config = load_dual_arm_config(args.config)
    backend = PyAgxBackend(right_config)
    arm = NeroArm(
        arm_name=right_config.name,
        side=right_config.side,
        backend=backend,
        joint_names=right_config.joint_names,
        max_speed_percent=right_config.max_speed_percent,
        joint_position_limits=right_config.joint_position_limits,
    )

    try:
        arm.connect()
        arm.enable_all(timeout_sec=right_config.pyagx.timeout)

        before = arm.get_joint_state_snapshot().as_dict()
        print("Right arm snapshot:")
        print(dump_json(before))

        if args.execute:
            current_positions = before["joint_positions"]
            if args.target:
                target = parse_target_csv(args.target, label="right_arm target")
            else:
                target = build_small_offset_target(current_positions, delta=args.delta)
            arm.move_j(target, speed=args.speed, wait=args.wait)
            after = arm.get_joint_state_snapshot().as_dict()
            print("Right arm snapshot after move:")
            print(dump_json(after))

        return 0
    except Exception as exc:
        print(f"test_right_arm failed: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            arm.stop()
        except Exception:
            pass
        try:
            arm.disable_all()
        except Exception:
            pass
        try:
            backend.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
