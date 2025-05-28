import sys
import subprocess

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

setup(
    name="tumor-detection-segmentation",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
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
    ],
)
