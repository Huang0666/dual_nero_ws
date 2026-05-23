from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any

import rclpy
from moveit_msgs.msg import MoveItErrorCodes

from .dual_arm_task_cli import (
    DualArmTaskClient,
    TaskStageDefinition,
    _default_task_config_path,
    _resolve_requested_stages,
    load_task_definition,
)


@dataclass(slots=True)
class CheckpointToleranceSummary:
    checkpoint: str
    tolerance_rad: float
    max_abs_error_rad: float
    worst_joint: str
    target_position_rad: float
    actual_position_rad: float
    passed: bool

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


@dataclass(slots=True)
class CycleAcceptanceSummary:
    task_name: str
    cycle: int
    executed_stages: list[str]
    overall_status: str
    failure_reason: str | None
    return_checkpoint: CheckpointToleranceSummary | None
    safe_checkpoint: CheckpointToleranceSummary | None

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


@dataclass(slots=True)
class P4BAcceptanceSummary:
    task_name: str
    cycles_requested: int
    cycles_completed: int
    point_tolerance_rad: float
    repeatability_tolerance_rad: float
    overall_status: str
    failed_cycle: int | None
    failed_reason: str | None
    safe_repeatability_passed: bool
    safe_repeatability_max_spread_rad: float
    safe_repeatability_by_joint_rad: dict[str, float]
    cycle_results: list[dict[str, Any]]

    def to_pretty_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2, sort_keys=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run P4-B minimal real-hardware acceptance: dual_prep_sync full cycle, "
            "safe return, and point stability checks."
        ),
    )
    parser.add_argument(
        "--task",
        default="dual_prep_sync",
        help="Task name defined in the task YAML.",
    )
    parser.add_argument(
        "--task-config",
        default=str(_default_task_config_path()),
        help="Path to the task YAML.",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=3,
        help="Number of repeated acceptance cycles.",
    )
    parser.add_argument(
        "--point-tolerance",
        type=float,
        default=0.03,
        help="Per-joint absolute position tolerance (rad) for return/safe checkpoints.",
    )
    parser.add_argument(
        "--repeatability-tolerance",
        type=float,
        default=None,
        help="Safe-point repeatability max spread tolerance (rad). Defaults to --point-tolerance.",
    )
    parser.add_argument(
        "--settle-sec",
        type=float,
        default=0.8,
        help="Seconds to wait for settling before sampling /joint_states at each checkpoint.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for /joint_states, service readiness, and action readiness.",
    )
    parser.add_argument(
        "--result-timeout",
        type=float,
        default=30.0,
        help="Minimum timeout in seconds when waiting for each arm action result.",
    )
    parser.add_argument(
        "--result-timeout-margin",
        type=float,
        default=15.0,
        help="Extra seconds added on top of planned trajectory duration for action result wait.",
    )
    parser.add_argument(
        "--planning-time",
        type=float,
        default=3.0,
        help="MoveIt allowed_planning_time in seconds.",
    )
    parser.add_argument(
        "--planning-attempts",
        type=int,
        default=1,
        help="MoveIt num_planning_attempts.",
    )
    parser.add_argument(
        "--goal-tolerance",
        type=float,
        default=0.001,
        help="Tolerance applied to each joint goal constraint.",
    )
    parser.add_argument(
        "--velocity-scaling",
        type=float,
        default=0.2,
        help="MoveIt max_velocity_scaling_factor.",
    )
    parser.add_argument(
        "--acceleration-scaling",
        type=float,
        default=0.2,
        help="MoveIt max_acceleration_scaling_factor.",
    )
    parser.add_argument(
        "--pipeline-id",
        default="",
        help="Optional MoveIt pipeline_id override.",
    )
    parser.add_argument(
        "--planner-id",
        default="",
        help="Optional MoveIt planner_id override.",
    )
    parser.add_argument(
        "--plan-service",
        default="/plan_kinematic_path",
        help="MoveIt planning service name.",
    )
    parser.add_argument(
        "--scene-config",
        default="",
        help="Optional planning-scene YAML path. Keep empty for P4-B unless scene_profile is configured.",
    )
    return parser


def _execute_stage(node: DualArmTaskClient, stage: TaskStageDefinition) -> tuple[bool, str | None]:
    response = node.plan_to_positions(
        stage=stage.name,
        target_positions=stage.as_dual_positions(),
        scene_profile=stage.scene_profile,
    )
    plan_summary = node.summarize_plan(stage=stage.name, response=response)
    print(plan_summary.to_pretty_json())
    if plan_summary.error_code != MoveItErrorCodes.SUCCESS:
        return False, f"{stage.name} planning failed ({plan_summary.error_name})"

    execution_summary = node.execute_dual_arm_stage(stage=stage, response=response)
    print(execution_summary.to_pretty_json())
    if execution_summary.overall_status != "success":
        return False, f"{stage.name} execution failed"
    return True, None


def _sample_positions(node: DualArmTaskClient, *, settle_sec: float) -> list[float]:
    settle_sec = max(0.0, float(settle_sec))
    if settle_sec > 0.0:
        deadline = time.monotonic() + settle_sec
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)
    return node.read_current_positions()


def _evaluate_checkpoint(
    *,
    checkpoint: str,
    joint_names: list[str],
    target_positions: list[float],
    actual_positions: list[float],
    tolerance: float,
) -> CheckpointToleranceSummary:
    errors = [abs(actual - target) for actual, target in zip(actual_positions, target_positions, strict=True)]
    worst_index = max(range(len(errors)), key=lambda index: errors[index])
    max_abs_error = float(errors[worst_index])
    return CheckpointToleranceSummary(
        checkpoint=checkpoint,
        tolerance_rad=float(tolerance),
        max_abs_error_rad=max_abs_error,
        worst_joint=joint_names[worst_index],
        target_position_rad=float(target_positions[worst_index]),
        actual_position_rad=float(actual_positions[worst_index]),
        passed=max_abs_error <= float(tolerance),
    )


def _compute_repeatability(
    *,
    joint_names: list[str],
    safe_samples: list[list[float]],
    tolerance: float,
) -> tuple[bool, float, dict[str, float]]:
    spread_by_joint: dict[str, float] = {joint_name: 0.0 for joint_name in joint_names}
    if len(safe_samples) < 2:
        return True, 0.0, spread_by_joint

    max_spread = 0.0
    for index, joint_name in enumerate(joint_names):
        values = [sample[index] for sample in safe_samples]
        spread = float(max(values) - min(values))
        spread_by_joint[joint_name] = spread
        max_spread = max(max_spread, spread)
    return max_spread <= float(tolerance), max_spread, spread_by_joint


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cycles < 1:
        print("run_p4b_acceptance failed: --cycles must be >= 1.", file=sys.stderr)
        return 2

    repeatability_tolerance = (
        float(args.repeatability_tolerance)
        if args.repeatability_tolerance is not None
        else float(args.point_tolerance)
    )

    try:
        task_definition = load_task_definition(args.task_config, args.task)
    except Exception as exc:
        print(f"run_p4b_acceptance failed: {exc}", file=sys.stderr)
        return 2

    if task_definition.definition.group_name != "dual_arms":
        print(
            "run_p4b_acceptance failed: task must use group_name=dual_arms.",
            file=sys.stderr,
        )
        return 2

    rclpy.init()
    node = DualArmTaskClient(
        task=task_definition,
        timeout_sec=args.timeout,
        result_timeout_sec=args.result_timeout,
        result_timeout_margin_sec=args.result_timeout_margin,
        plan_service_name=args.plan_service,
        planning_time_sec=args.planning_time,
        planning_attempts=args.planning_attempts,
        goal_tolerance=args.goal_tolerance,
        velocity_scaling=args.velocity_scaling,
        acceleration_scaling=args.acceleration_scaling,
        pipeline_id=args.pipeline_id,
        planner_id=args.planner_id,
        scene_config_path=(args.scene_config or None),
    )

    try:
        preview = node.build_preview()
        print(preview.to_pretty_json())

        full_stages = _resolve_requested_stages(task_definition=task_definition, target="full")
        if not full_stages:
            raise RuntimeError("Task target 'full' resolved to zero stages.")
        return_stage = next((stage for stage in full_stages if stage.name == "return"), full_stages[-1])
        safe_stage = TaskStageDefinition(
            name="safe",
            execution_mode=task_definition.definition.default_execution_mode,
            failure_policy="abort",
            scene_profile=task_definition.definition.scene_profile,
            target_positions=task_definition.definition.safe_positions,
        )

        safe_target = task_definition.definition.safe_positions.as_dual_positions()
        safe_samples: list[list[float]] = []
        cycle_reports: list[CycleAcceptanceSummary] = []

        failed_cycle: int | None = None
        failed_reason: str | None = None

        for cycle in range(1, int(args.cycles) + 1):
            executed_stages: list[str] = []
            cycle_failure: str | None = None
            return_check: CheckpointToleranceSummary | None = None
            safe_check: CheckpointToleranceSummary | None = None

            for stage in full_stages:
                executed_stages.append(stage.name)
                ok, reason = _execute_stage(node, stage)
                if not ok:
                    cycle_failure = reason
                    break

            if cycle_failure is None:
                return_actual = _sample_positions(node, settle_sec=args.settle_sec)
                return_check = _evaluate_checkpoint(
                    checkpoint=f"cycle_{cycle}.return",
                    joint_names=node.joint_names,
                    target_positions=return_stage.as_dual_positions(),
                    actual_positions=return_actual,
                    tolerance=float(args.point_tolerance),
                )
                print(return_check.to_pretty_json())
                if not return_check.passed:
                    cycle_failure = (
                        f"{return_check.checkpoint} exceeded tolerance "
                        f"({return_check.max_abs_error_rad:.6f} rad > {args.point_tolerance:.6f} rad)."
                    )

            if cycle_failure is None:
                executed_stages.append(safe_stage.name)
                ok, reason = _execute_stage(node, safe_stage)
                if not ok:
                    cycle_failure = reason

            if cycle_failure is None:
                safe_actual = _sample_positions(node, settle_sec=args.settle_sec)
                safe_samples.append(safe_actual)
                safe_check = _evaluate_checkpoint(
                    checkpoint=f"cycle_{cycle}.safe",
                    joint_names=node.joint_names,
                    target_positions=safe_target,
                    actual_positions=safe_actual,
                    tolerance=float(args.point_tolerance),
                )
                print(safe_check.to_pretty_json())
                if not safe_check.passed:
                    cycle_failure = (
                        f"{safe_check.checkpoint} exceeded tolerance "
                        f"({safe_check.max_abs_error_rad:.6f} rad > {args.point_tolerance:.6f} rad)."
                    )
            else:
                executed_stages.append(f"{safe_stage.name}_recovery")
                recovery_ok, recovery_reason = _execute_stage(node, safe_stage)
                if not recovery_ok:
                    cycle_failure = f"{cycle_failure} | safe recovery failed ({recovery_reason})"
                else:
                    safe_actual = _sample_positions(node, settle_sec=args.settle_sec)
                    safe_check = _evaluate_checkpoint(
                        checkpoint=f"cycle_{cycle}.safe_recovery",
                        joint_names=node.joint_names,
                        target_positions=safe_target,
                        actual_positions=safe_actual,
                        tolerance=float(args.point_tolerance),
                    )
                    print(safe_check.to_pretty_json())
                    if not safe_check.passed:
                        cycle_failure = (
                            f"{cycle_failure} | {safe_check.checkpoint} exceeded tolerance "
                            f"({safe_check.max_abs_error_rad:.6f} rad > {args.point_tolerance:.6f} rad)."
                        )

            overall_status = "success" if cycle_failure is None else "failed"
            cycle_report = CycleAcceptanceSummary(
                task_name=task_definition.definition.task_name,
                cycle=cycle,
                executed_stages=executed_stages,
                overall_status=overall_status,
                failure_reason=cycle_failure,
                return_checkpoint=return_check,
                safe_checkpoint=safe_check,
            )
            print(cycle_report.to_pretty_json())
            cycle_reports.append(cycle_report)

            if cycle_failure is not None:
                failed_cycle = cycle
                failed_reason = cycle_failure
                break

        repeatability_passed, max_spread, spread_by_joint = _compute_repeatability(
            joint_names=node.joint_names,
            safe_samples=safe_samples,
            tolerance=repeatability_tolerance,
        )
        if failed_reason is None and not repeatability_passed:
            failed_reason = (
                "safe repeatability exceeded tolerance "
                f"({max_spread:.6f} rad > {repeatability_tolerance:.6f} rad)."
            )

        cycles_completed = len(cycle_reports)
        full_cycles_completed = (
            cycles_completed == int(args.cycles)
            and all(report.overall_status == "success" for report in cycle_reports)
        )
        overall_success = full_cycles_completed and repeatability_passed

        summary = P4BAcceptanceSummary(
            task_name=task_definition.definition.task_name,
            cycles_requested=int(args.cycles),
            cycles_completed=cycles_completed,
            point_tolerance_rad=float(args.point_tolerance),
            repeatability_tolerance_rad=repeatability_tolerance,
            overall_status="success" if overall_success else "failed",
            failed_cycle=failed_cycle,
            failed_reason=failed_reason,
            safe_repeatability_passed=repeatability_passed,
            safe_repeatability_max_spread_rad=max_spread,
            safe_repeatability_by_joint_rad=spread_by_joint,
            cycle_results=[asdict(report) for report in cycle_reports],
        )
        print(summary.to_pretty_json())
        return 0 if overall_success else 1
    except Exception as exc:
        print(f"run_p4b_acceptance failed: {exc}", file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
