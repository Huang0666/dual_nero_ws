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
    parser = argparse.ArgumentParser(description="Minimal left-arm connectivity test.")
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
    parser.add_argument(
        "--keep-enabled",
        action="store_true",
        help="Keep the arm enabled after the test instead of auto-disabling in cleanup.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _configure_logging(verbose=args.verbose)
    cleanup_mode = "keep-enabled" if args.keep_enabled else "auto-disable"

    arm = build_single_arm_from_file(args.config, "left")
    left_config, _ = load_dual_arm_config(args.config)
    timeout_sec = left_config.pyagx.timeout
    backend = arm.backend

    if args.verbose:
        print(f"config_path: {Path(args.config).resolve()}")
        print(
            "arm_config: "
            f"name={left_config.name}, side={left_config.side}, "
            f"channel={left_config.can.channel}, interface={left_config.can.interface}, "
            f"bitrate={left_config.can.bitrate}, dry_run={left_config.dry_run}"
        )
        print(f"cleanup mode: {cleanup_mode}")

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
        print("Left arm snapshot:")
        print(dump_json(before))

        if args.execute:
            current_positions = before["joint_positions"]
            if args.target:
                target = parse_target_csv(args.target, label="left_arm target")
            else:
                target = build_small_offset_target(current_positions, delta=args.delta)
            arm.move_j(target, speed=args.speed, wait=args.wait)
            after = arm.get_joint_state_snapshot().as_dict()
            print("Left arm snapshot after move:")
            print(dump_json(after))

        return 0
    except Exception as exc:
        print(f"test_left_arm failed: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            arm.stop()
        except Exception:
            pass
        if not args.keep_enabled:
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
