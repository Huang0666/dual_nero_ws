from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

try:
    from ament_index_python.packages import get_package_share_directory
except ImportError:  # pragma: no cover
    get_package_share_directory = None
    
from dual_nero_driver.safety import expected_joint_names


EXPECTED_LEFT_JOINTS = expected_joint_names("left")
EXPECTED_RIGHT_JOINTS = expected_joint_names("right")
EXPECTED_ALL_JOINTS = EXPECTED_LEFT_JOINTS + EXPECTED_RIGHT_JOINTS
EXPECTED_GROUPS = {"left_arm", "right_arm", "dual_arms"}
EXPECTED_CONTROLLERS = {
    "left_arm_controller",
    "right_arm_controller",
    "joint_state_broadcaster",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Static contract check for the dual_nero real execution bridge."
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional repository root. Defaults to the source-tree root if available.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = {
        "ros2_control": resolve_path(
            args.repo_root,
            package_name="dual_nero_moveit_config",
            relative_path=Path("config") / "dual_nero_description.ros2_control.xacro",
        ),
        "srdf": resolve_path(
            args.repo_root,
            package_name="dual_nero_moveit_config",
            relative_path=Path("config") / "dual_nero_description.srdf",
        ),
        "ros2_controllers": resolve_path(
            args.repo_root,
            package_name="dual_nero_moveit_config",
            relative_path=Path("config") / "ros2_controllers.yaml",
        ),
        "moveit_controllers": resolve_path(
            args.repo_root,
            package_name="dual_nero_moveit_config",
            relative_path=Path("config") / "moveit_controllers.yaml",
        ),
        "hardware_params": resolve_path(
            args.repo_root,
            package_name="dual_nero_bridge",
            relative_path=Path("config") / "hardware_params.yaml",
        ),
        "baseline": resolve_doc_path(args.repo_root, "project_baseline.md"),
        "contract": resolve_doc_path(args.repo_root, "driver_contract.md"),
    }
    errors: list[str] = []
    errors.extend(check_ros2_control(paths["ros2_control"]))
    errors.extend(check_srdf(paths["srdf"]))
    errors.extend(check_ros2_controllers(paths["ros2_controllers"]))
    errors.extend(check_moveit_controllers(paths["moveit_controllers"]))
    errors.extend(check_hardware_params(paths["hardware_params"]))
    errors.extend(check_tf_document_contract(paths["baseline"], paths["contract"]))

    if errors:
        print("dual_nero_bridge contract check: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("dual_nero_bridge contract check: PASS")
    return 0


def resolve_doc_path(explicit_root: str | None, name: str) -> Path:
    docs_root = resolve_path(explicit_root, package_name=None, relative_path=Path("docs"))
    matches = sorted(docs_root.rglob(name))
    if not matches:
        raise FileNotFoundError(f"Could not find document named '{name}' under {docs_root}.")
    if len(matches) > 1:
        raise FileNotFoundError(
            f"Found multiple documents named '{name}' under {docs_root}: {matches}"
        )
    return matches[0]


def resolve_path(
    explicit_root: str | None,
    *,
    package_name: str | None,
    relative_path: Path,
) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).resolve()
        if package_name is None:
            return repo_root / relative_path
        return repo_root / "src" / package_name / relative_path
    if package_name and get_package_share_directory is not None:
        return Path(get_package_share_directory(package_name)) / relative_path
    return Path(__file__).resolve().parents[4] / relative_path


def check_ros2_control(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    joints = [joint.attrib["name"] for joint in root.findall(".//joint")]
    if joints != EXPECTED_ALL_JOINTS:
        return [
            f"{path}: ros2_control joint list must equal {EXPECTED_ALL_JOINTS}, got {joints}."
        ]
    return []


def check_srdf(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    errors: list[str] = []
    groups = {group.attrib["name"] for group in root.findall(".//group")}
    if groups != EXPECTED_GROUPS:
        errors.append(
            f"{path}: SRDF groups must equal {sorted(EXPECTED_GROUPS)}, got {sorted(groups)}."
        )

    group_joint_map = {
        group.attrib["name"]: [joint.attrib["name"] for joint in group.findall("./joint")]
        for group in root.findall(".//group")
    }
    if group_joint_map.get("left_arm") != EXPECTED_LEFT_JOINTS:
        errors.append(f"{path}: left_arm joints must equal {EXPECTED_LEFT_JOINTS}.")
    if group_joint_map.get("right_arm") != EXPECTED_RIGHT_JOINTS:
        errors.append(f"{path}: right_arm joints must equal {EXPECTED_RIGHT_JOINTS}.")
    if group_joint_map.get("dual_arms") != EXPECTED_ALL_JOINTS:
        errors.append(f"{path}: dual_arms joints must equal {EXPECTED_ALL_JOINTS}.")

    virtual_joints = root.findall(".//virtual_joint")
    if len(virtual_joints) != 1:
        errors.append(
            f"{path}: expected exactly one virtual_joint, got {len(virtual_joints)}."
        )
    else:
        virtual_joint = virtual_joints[0]
        if (
            virtual_joint.attrib.get("name") != "world_joint"
            or virtual_joint.attrib.get("parent_frame") != "world"
            or virtual_joint.attrib.get("child_link") != "world"
        ):
            errors.append(
                f"{path}: virtual_joint must remain world_joint(parent_frame=world, child_link=world)."
            )
    return errors


def check_ros2_controllers(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}

    errors: list[str] = []
    controllers = set(
        (data.get("controller_manager", {}) or {})
        .get("ros__parameters", {})
        .keys()
    )
    controllers.discard("update_rate")
    if controllers != EXPECTED_CONTROLLERS:
        errors.append(
            f"{path}: controller_manager entries must equal {sorted(EXPECTED_CONTROLLERS)}, got {sorted(controllers)}."
        )

    left_joints = (
        ((data.get("left_arm_controller", {}) or {}).get("ros__parameters", {}) or {})
    ).get("joints", [])
    right_joints = (
        ((data.get("right_arm_controller", {}) or {}).get("ros__parameters", {}) or {})
    ).get("joints", [])
    if left_joints != EXPECTED_LEFT_JOINTS:
        errors.append(f"{path}: left_arm_controller joints must equal {EXPECTED_LEFT_JOINTS}.")
    if right_joints != EXPECTED_RIGHT_JOINTS:
        errors.append(f"{path}: right_arm_controller joints must equal {EXPECTED_RIGHT_JOINTS}.")
    return errors


def check_moveit_controllers(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}

    errors: list[str] = []
    manager = data.get("moveit_simple_controller_manager", {}) or {}
    controller_names = set(manager.get("controller_names", []))
    expected_moveit_names = {"left_arm_controller", "right_arm_controller"}
    if controller_names != expected_moveit_names:
        errors.append(
            f"{path}: MoveIt controller_names must equal {sorted(expected_moveit_names)}, got {sorted(controller_names)}."
        )
    left = manager.get("left_arm_controller", {}) or {}
    right = manager.get("right_arm_controller", {}) or {}
    if left.get("joints") != EXPECTED_LEFT_JOINTS:
        errors.append(f"{path}: MoveIt left_arm_controller joints must equal {EXPECTED_LEFT_JOINTS}.")
    if right.get("joints") != EXPECTED_RIGHT_JOINTS:
        errors.append(f"{path}: MoveIt right_arm_controller joints must equal {EXPECTED_RIGHT_JOINTS}.")
    if left.get("action_ns") != "follow_joint_trajectory":
        errors.append(f"{path}: left_arm_controller action_ns must remain follow_joint_trajectory.")
    if right.get("action_ns") != "follow_joint_trajectory":
        errors.append(f"{path}: right_arm_controller action_ns must remain follow_joint_trajectory.")
    return errors


def check_hardware_params(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}

    errors: list[str] = []
    if data.get("mode") != "real_hardware_execution":
        errors.append(f"{path}: mode must be real_hardware_execution.")
    left_joint_names = ((data.get("left_arm", {}) or {}).get("joint_names")) or []
    right_joint_names = ((data.get("right_arm", {}) or {}).get("joint_names")) or []
    if left_joint_names != EXPECTED_LEFT_JOINTS:
        errors.append(f"{path}: left_arm.joint_names must equal {EXPECTED_LEFT_JOINTS}.")
    if right_joint_names != EXPECTED_RIGHT_JOINTS:
        errors.append(f"{path}: right_arm.joint_names must equal {EXPECTED_RIGHT_JOINTS}.")
    if ((data.get("left_arm", {}) or {}).get("dry_run")) is not False:
        errors.append(
            f"{path}: left_arm.dry_run must default to false in real hardware mode."
        )
    if ((data.get("right_arm", {}) or {}).get("dry_run")) is not False:
        errors.append(
            f"{path}: right_arm.dry_run must default to false in real hardware mode."
        )
    return errors


def check_tf_document_contract(baseline_path: Path, contract_path: Path) -> list[str]:
    expected_trunk = "world -> dual_base_plate -> dual_column -> dual_crossbar"
    errors: list[str] = []
    baseline_text = baseline_path.read_text(encoding="utf-8")
    contract_text = contract_path.read_text(encoding="utf-8")
    if expected_trunk not in baseline_text:
        errors.append(f"{baseline_path}: missing TF trunk string '{expected_trunk}'.")
    if expected_trunk not in contract_text:
        errors.append(f"{contract_path}: missing TF trunk string '{expected_trunk}'.")
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
