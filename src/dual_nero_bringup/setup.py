from glob import glob
from setuptools import find_packages, setup


package_name = "dual_nero_bringup"


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml", "README.md"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
        (f"share/{package_name}/launch", glob("launch/*.py")),
        (f"share/{package_name}/worlds", glob("worlds/*.sdf")),
    ],
    install_requires=["setuptools", "PyYAML"],
    zip_safe=True,
    maintainer="yang-hrs",
    maintainer_email="15138756873@163.com",
    description="Bringup entry points for the dual-arm NERO real hardware execution flow.",
    license="Apache-2.0",
    python_requires=">=3.10",
)
