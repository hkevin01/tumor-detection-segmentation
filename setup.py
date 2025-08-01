"""
Setup script for tumor detection and segmentation package.

This script handles package installation and dependency management.
"""

import sys
import subprocess
from pathlib import Path

try:
    import setuptools
except ImportError:
    print("setuptools not found. Attempting to install...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools"])
    try:
        import setuptools
    except ImportError as e:
        print(f"Import failed: {e}")
        sys.exit(1)

from setuptools import setup, find_packages

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Tumor Detection and Segmentation using MONAI"

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = [
        "monai",
        "torch",
        "torchvision",
        "numpy",
        "matplotlib",
        "pandas",
        "scikit-learn",
        "scipy",
        "tqdm",
        "jupyter"
    ]

setup(
    name="tumor-detection-segmentation",
    version="0.1.0",
    author="Tumor Detection Team",
    author_email="",
    description="Deep learning pipeline for tumor detection and segmentation in medical images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest",
            "black",
            "flake8",
            "mypy",
            "pre-commit",
        ],
        "docs": [
            "sphinx",
            "sphinx-rtd-theme",
            "sphinxcontrib-napoleon",
        ],
    },
    entry_points={
        "console_scripts": [
            "tumor-train=training.train:main",
            "tumor-infer=inference.inference:main",
            "tumor-eval=evaluation.evaluate:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
