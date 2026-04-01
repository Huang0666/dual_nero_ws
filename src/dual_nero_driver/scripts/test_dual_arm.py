#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dual_nero_driver.dual_arm_manager import DualArmManager
from dual_nero_driver.nero_arm import NeroArm
from dual_nero_driver.pyagx_backend import PyAgxBackend
from dual_nero_driver.utils import (
    build_small_offset_target,
    dump_json,
    load_dual_arm_config,
    parse_target_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Minimal dual-arm connectivity test.")
    parser.add_argument("--config", required=True, help="Path to arm YAML config.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Send small move_j commands after reading state.",
    )
    parser.add_argument(
        "--left-target",
        help="Optional comma-separated 7-joint target for the left arm.",
    )
    parser.add_argument(
        "--right-target",
        help="Optional comma-separated 7-joint target for the right arm.",
    )
    parser.add_argument(
        "--delta",
        type=float,
        default=0.05,
        help="Small default joint offset used when --execute is set without explicit targets.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=None,
        help="Requested speed percent. Clamped by per-arm max_speed_percent if configured.",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for both arms to reach target joints.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    left_config, right_config = load_dual_arm_config(args.config)
    left_backend = PyAgxBackend(left_config)
    right_backend = PyAgxBackend(right_config)

    left_arm = NeroArm(
        arm_name=left_config.name,
        side=left_config.side,
        backend=left_backend,
        joint_names=left_config.joint_names,
        max_speed_percent=left_config.max_speed_percent,
        joint_position_limits=left_config.joint_position_limits,
    )
    right_arm = NeroArm(
        arm_name=right_config.name,
        side=right_config.side,
        backend=right_backend,
        joint_names=right_config.joint_names,
        max_speed_percent=right_config.max_speed_percent,
        joint_position_limits=right_config.joint_position_limits,
    )
    manager = DualArmManager(left_arm=left_arm, right_arm=right_arm)

    try:
        manager.connect_all()
        manager.enable_all(
            timeout_sec=max(left_config.pyagx.timeout, right_config.pyagx.timeout)
        )

        before = manager.get_states()
        print("Dual arm snapshot:")
        print(dump_json(before))

        if args.execute:
            left_current = before["left_arm"]["joint_positions"]
            right_current = before["right_arm"]["joint_positions"]
            left_target = (
                parse_target_csv(args.left_target, label="left_arm target")
                if args.left_target
                else build_small_offset_target(left_current, delta=args.delta)
            )
            right_target = (
                parse_target_csv(args.right_target, label="right_arm target")
                if args.right_target
                else build_small_offset_target(right_current, delta=args.delta)
            )
            manager.move_both_joints(
                left_target=left_target,
                right_target=right_target,
                speed=args.speed,
                wait=args.wait,
            )
            after = manager.get_states()
            print("Dual arm snapshot after move:")
            print(dump_json(after))

        return 0
    except Exception as exc:
        print(f"test_dual_arm failed: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            manager.stop_all()
        except Exception:
            pass
        try:
            manager.disable_all()
        except Exception:
            pass
        try:
            left_backend.close()
        except Exception:
            pass
        try:
            right_backend.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
