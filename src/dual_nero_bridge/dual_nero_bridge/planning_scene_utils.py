from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from geometry_msgs.msg import Pose
from moveit_msgs.msg import CollisionObject, PlanningScene
from shape_msgs.msg import SolidPrimitive


@dataclass(slots=True)
class BoxObstacle:
    object_id: str
    frame_id: str
    size: tuple[float, float, float]
    position: tuple[float, float, float]
    orientation_xyzw: tuple[float, float, float, float]


@dataclass(slots=True)
class SceneProfile:
    profile_name: str
    obstacles: list[BoxObstacle]

    @property
    def object_ids(self) -> list[str]:
        return [obstacle.object_id for obstacle in self.obstacles]


def load_scene_profile(path: str | Path, profile_name: str) -> SceneProfile:
    yaml_path = Path(path)
    if not yaml_path.is_file():
        raise FileNotFoundError(f"Scene config file does not exist: {yaml_path}")

    with yaml_path.open("r", encoding="utf-8") as file_obj:
        data = yaml.safe_load(file_obj) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"Scene config must be a mapping: {yaml_path}")

    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        raise RuntimeError(f"Scene config must contain a 'profiles' mapping: {yaml_path}")

    profile_data = profiles.get(profile_name)
    if not isinstance(profile_data, dict):
        known = sorted(profiles)
        raise RuntimeError(
            f"Scene profile {profile_name!r} was not found in {yaml_path}. Known profiles: {known}"
        )

    frame_id = str(profile_data.get("frame_id", "world")).strip() or "world"
    obstacles_data = profile_data.get("obstacles", [])
    if not isinstance(obstacles_data, list):
        raise RuntimeError(f"{profile_name}.obstacles must be a list.")

    obstacles: list[BoxObstacle] = []
    seen_ids: set[str] = set()
    for index, obstacle_data in enumerate(obstacles_data, start=1):
        if not isinstance(obstacle_data, dict):
            raise RuntimeError(f"{profile_name}.obstacles[{index}] must be a mapping.")
        object_id = str(obstacle_data.get("id", "")).strip()
        if not object_id:
            raise RuntimeError(f"{profile_name}.obstacles[{index}] is missing id.")
        if object_id in seen_ids:
            raise RuntimeError(f"{profile_name} contains duplicate obstacle id {object_id!r}.")
        seen_ids.add(object_id)
        size = _load_float_tuple(
            obstacle_data.get("size"),
            label=f"{profile_name}.obstacles[{object_id}].size",
            expected_len=3,
        )
        position = _load_float_tuple(
            obstacle_data.get("position"),
            label=f"{profile_name}.obstacles[{object_id}].position",
            expected_len=3,
        )
        orientation = _load_float_tuple(
            obstacle_data.get("orientation_xyzw", [0.0, 0.0, 0.0, 1.0]),
            label=f"{profile_name}.obstacles[{object_id}].orientation_xyzw",
            expected_len=4,
        )
        obstacles.append(
            BoxObstacle(
                object_id=object_id,
                frame_id=str(obstacle_data.get("frame_id", frame_id)).strip() or frame_id,
                size=size,
                position=position,
                orientation_xyzw=orientation,
            )
        )

    return SceneProfile(profile_name=profile_name, obstacles=obstacles)


def build_scene_diff(
    *,
    profile: SceneProfile,
    previous_object_ids: set[str],
) -> PlanningScene:
    planning_scene = PlanningScene()
    planning_scene.is_diff = True

    for object_id in sorted(previous_object_ids - set(profile.object_ids)):
        remove_object = CollisionObject()
        remove_object.id = object_id
        remove_object.operation = CollisionObject.REMOVE
        planning_scene.world.collision_objects.append(remove_object)

    for obstacle in profile.obstacles:
        collision_object = CollisionObject()
        collision_object.id = obstacle.object_id
        collision_object.header.frame_id = obstacle.frame_id
        collision_object.operation = CollisionObject.ADD

        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = list(obstacle.size)
        collision_object.primitives.append(primitive)

        pose = Pose()
        pose.position.x = obstacle.position[0]
        pose.position.y = obstacle.position[1]
        pose.position.z = obstacle.position[2]
        pose.orientation.x = obstacle.orientation_xyzw[0]
        pose.orientation.y = obstacle.orientation_xyzw[1]
        pose.orientation.z = obstacle.orientation_xyzw[2]
        pose.orientation.w = obstacle.orientation_xyzw[3]
        collision_object.primitive_poses.append(pose)

        planning_scene.world.collision_objects.append(collision_object)

    return planning_scene


def build_remove_all_scene(object_ids: set[str]) -> PlanningScene:
    planning_scene = PlanningScene()
    planning_scene.is_diff = True
    for object_id in sorted(object_ids):
        remove_object = CollisionObject()
        remove_object.id = object_id
        remove_object.operation = CollisionObject.REMOVE
        planning_scene.world.collision_objects.append(remove_object)
    return planning_scene


def _load_float_tuple(value: Any, *, label: str, expected_len: int) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != expected_len:
        raise RuntimeError(f"{label} must be a list of {expected_len} numbers.")
    return tuple(float(item) for item in value)
