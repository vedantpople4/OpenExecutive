"""Setup script for OpenExec."""

from pathlib import Path
from setuptools import setup, find_packages

this_dir = Path(__file__).resolve().parent


def get_readme():
    """Get README content for PyPI."""
    readme_file = this_dir / "README.md"
    return readme_file.read_text() if readme_file.exists() else ""


def get_requirements():
    """Get requirements list."""
    req_file = this_dir / "requirements.txt"
    return [line.strip() for line in req_file.read_text().splitlines() if line.strip() and not line.strip().startswith("#")]


setup(
    name="openexec",
    version="0.1.0",
    description="Executive Board Simulation System",
    long_description=get_readme(),
    long_description_content_type="text/markdown",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=get_requirements(),
    entry_points={
        "console_scripts": [
            "openexec=openexec.cli:main",
        ],
    },
)
