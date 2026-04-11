from __future__ import annotations

import argparse
import sys

import rclpy

from dual_nero_bridge.goal_client_utils import SingleArmGoalClient


def build_parser(*, side: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Minimal {side}-arm FollowJointTrajectory smoke-test client."
    )
    parser.add_argument("--config", required=True, help="Path to hardware YAML config.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually send the action goal. Without this flag the command only prints a preview.",
    )
    parser.add_argument(
        "--delta",
        type=float,
        default=0.03,
        help=f"Small offset applied to {side}_joint1 from the current /joint_states sample.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for /joint_states and action server/result waits.",
    )
    return parser


def run_single_arm_goal(*, side: str, argv: list[str] | None = None) -> int:
    args = build_parser(side=side).parse_args(argv)
    rclpy.init()
    node = SingleArmGoalClient(
        side=side,
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
            f"{side}_arm_controller result: error_code={result.error_code}, "
            f"error_string={result.error_string}"
        )
        return 0 if result.error_code == 0 else 1
    except Exception as exc:
        print(f"send_{side}_arm_goal failed: {exc}", file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()
