#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dual_nero_driver.factories import build_single_arm_from_file
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
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print backend alignment/debug output for connect() and enable_all().",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _configure_logging(verbose=args.verbose)

    arm = build_single_arm_from_file(args.config, "right")
    _, right_config = load_dual_arm_config(args.config)
    timeout_sec = right_config.pyagx.timeout
    backend = arm.backend

    if args.verbose:
        print(f"config_path: {Path(args.config).resolve()}")
        print(
            "arm_config: "
            f"name={right_config.name}, side={right_config.side}, "
            f"channel={right_config.can.channel}, interface={right_config.can.interface}, "
            f"bitrate={right_config.can.bitrate}, dry_run={right_config.dry_run}"
        )

    try:
        if args.verbose:
            print("connect: start")
        arm.connect()
        if args.verbose:
            print("connect: success")
            if isinstance(backend, PyAgxBackend):
                print(f"set_normal_mode_executed: {backend.normal_mode_was_called}")

        if args.verbose:
            print(f"enable_all: start timeout_sec={timeout_sec:.2f}")
        arm.enable_all(timeout_sec=timeout_sec)
        if args.verbose and isinstance(backend, PyAgxBackend):
            print(
                "enable_all: final "
                f"ret={backend.last_enable_return!r} "
                f"statuses={backend.last_enable_statuses!r}"
            )

        before = arm.get_joint_state_snapshot().as_dict()
        print(f"joint_positions: {before['joint_positions']}")
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
            arm.backend.close()
        except Exception:
            pass


def _configure_logging(*, verbose: bool) -> None:
    if not verbose:
        return
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s:%(name)s:%(message)s",
    )


if __name__ == "__main__":
    raise SystemExit(main())
