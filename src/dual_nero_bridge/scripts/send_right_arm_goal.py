#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import rclpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dual_nero_bridge.goal_client_utils import SingleArmGoalClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Minimal right-arm FollowJointTrajectory smoke-test client."
    )
    parser.add_argument("--config", required=True, help="Path to hardware YAML config.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually send the action goal. Without this flag the script only prints a preview.",
    )
    parser.add_argument(
        "--delta",
        type=float,
        default=0.03,
        help="Small offset applied to right_joint1 from the current /joint_states sample.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for /joint_states and action server/result waits.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rclpy.init()
    node = SingleArmGoalClient(
        side="right",
        config_path=args.config,
        delta=args.delta,
        timeout_sec=args.timeout,
    )
    try:
        preview = node.build_preview()
        print(preview.to_pretty_json())
        if not args.execute:
            print("No goal sent. Re-run with --execute to send this single-point goal.")
            return 0
        result = node.send_goal(preview)
        print(
            f"right_arm_controller result: error_code={result.error_code}, "
            f"error_string={result.error_string}"
        )
        return 0 if result.error_code == 0 else 1
    except Exception as exc:
        print(f"send_right_arm_goal failed: {exc}", file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
