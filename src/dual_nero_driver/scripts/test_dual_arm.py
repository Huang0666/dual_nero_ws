#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dual_nero_driver.factories import build_dual_arm_manager_from_file
from dual_nero_driver.safety import find_joints_near_limits, find_joints_outside_limits
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
    parser.add_argument(
        "--near-limit-margin",
        type=float,
        default=0.05,
        help="Warn when a joint is within this distance of its configured limit.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print config and cleanup details for the dual-arm test flow.",
    )
    parser.add_argument(
        "--keep-enabled",
        action="store_true",
        help="Keep both arms enabled after the test instead of auto-disabling in cleanup.",
    )
    return parser.parse_args()


def _print_joint_positions(arm_label: str, joint_names: list[str], positions: list[float]) -> None:
    print(f"{arm_label} current joint positions:")
    for joint_name, joint_value in zip(joint_names, positions, strict=True):
        print(f"  {joint_name}: {joint_value:.6f}")


def _print_limit_warnings(arm_label: str, warnings: list) -> None:
    if not warnings:
        return

    print(
        f"{arm_label} joints close to configured limits "
        f"(still legal, but motion margin is small):"
    )
    for warning in warnings:
        assert warning.distance is not None
        relation = "lower" if warning.relation == "near_lower" else "upper"
        print(
            "  "
            f"{warning.joint_name}: current={warning.current:.6f}, "
            f"lower={warning.lower}, upper={warning.upper}, "
            f"near_{relation}_distance={warning.distance:.6f}"
        )


def _raise_precheck_failure(violations: list) -> None:
    details = [
        (
            f"{violation.joint_name}: current={violation.current:.6f}, "
            f"lower={violation.lower}, upper={violation.upper}"
        )
        for violation in violations
    ]
    detail_text = "\n".join(details)
    raise RuntimeError(
        "Current real joint positions are outside configured limits.\n"
        f"{detail_text}\n"
        "Please disable the robot, manually move the affected joints back into the "
        "legal range, and then rerun test_dual_arm.py --execute."
    )


def main() -> int:
    args = parse_args()
    cleanup_mode = "keep-enabled" if args.keep_enabled else "auto-disable"
    manager = build_dual_arm_manager_from_file(args.config)
    left_config, right_config = load_dual_arm_config(args.config)

    if args.verbose:
        print(f"config_path: {Path(args.config).resolve()}")
        print(
            "left_arm_config: "
            f"name={left_config.name}, side={left_config.side}, "
            f"channel={left_config.can.channel}, interface={left_config.can.interface}, "
            f"bitrate={left_config.can.bitrate}, dry_run={left_config.dry_run}"
        )
        print(
            "right_arm_config: "
            f"name={right_config.name}, side={right_config.side}, "
            f"channel={right_config.can.channel}, interface={right_config.can.interface}, "
            f"bitrate={right_config.can.bitrate}, dry_run={right_config.dry_run}"
        )
        print(f"cleanup mode: {cleanup_mode}")

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
            _print_joint_positions(
                "left_arm",
                left_config.joint_names,
                left_current,
            )
            _print_joint_positions(
                "right_arm",
                right_config.joint_names,
                right_current,
            )

            left_violations = find_joints_outside_limits(
                left_config.joint_names,
                left_current,
                left_config.joint_position_limits,
            )
            right_violations = find_joints_outside_limits(
                right_config.joint_names,
                right_current,
                right_config.joint_position_limits,
            )
            _print_limit_warnings(
                "left_arm",
                find_joints_near_limits(
                    left_config.joint_names,
                    left_current,
                    left_config.joint_position_limits,
                    margin=args.near_limit_margin,
                ),
            )
            _print_limit_warnings(
                "right_arm",
                find_joints_near_limits(
                    right_config.joint_names,
                    right_current,
                    right_config.joint_position_limits,
                    margin=args.near_limit_margin,
                ),
            )

            if left_violations or right_violations:
                _raise_precheck_failure(left_violations + right_violations)

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
        if not args.keep_enabled:
            try:
                manager.disable_all()
            except Exception:
                pass
        try:
            manager.left_arm.backend.close()
        except Exception:
            pass
        try:
            manager.right_arm.backend.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
