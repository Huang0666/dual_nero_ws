from glob import glob
from setuptools import find_packages, setup


package_name = "dual_nero_bridge"


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml", "README.md"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/launch", glob("launch/*.py")),
        (f"lib/{package_name}", glob("scripts/*.py")),
    ],
    install_requires=["setuptools", "PyYAML"],
    zip_safe=True,
    maintainer="yang-hrs",
    maintainer_email="15138756873@163.com",
    description="Real hardware execution bridge package for the dual-arm NERO robot.",
    license="Apache-2.0",
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "real_execution_node = dual_nero_bridge.real_execution_node:main",
            "contract_check = dual_nero_bridge.contract_check:main",
            "send_left_arm_goal = dual_nero_bridge.send_left_arm_goal:main",
            "send_right_arm_goal = dual_nero_bridge.send_right_arm_goal:main",
            "validate_moveit_pipeline = dual_nero_bridge.moveit_validation_cli:main",
            "run_dual_arm_task = dual_nero_bridge.dual_arm_task_cli:main",
        ]
    },
)
