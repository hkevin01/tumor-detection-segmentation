"""
Configuration management for tumor detection package.

Utilities for loading and parsing recipe and dataset configurations.
"""

import json
from pathlib import Path
from typing import Any, Dict, Union


def load_recipe_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a recipe configuration file.

    Args:
        config_path: Path to recipe configuration JSON file

    Returns:
        Dictionary containing recipe configuration

    Example:
        >>> config = load_recipe_config("config/recipes/unetr_multimodal.json")
        >>> model_config = config['model']
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Recipe config not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config


def load_dataset_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a dataset configuration file.

    Args:
        config_path: Path to dataset configuration JSON file

    Returns:
        Dictionary containing dataset configuration

    Example:
        >>> config = load_dataset_config("config/datasets/msd_task01_brain.json")
        >>> data_dir = config['data_dir']
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Dataset config not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config


def get_default_config_dir() -> Path:
    """
    Get the default configuration directory.

    Returns:
        Path to default config directory
    """
    # Get package root (go up from src/tumor_detection)
    package_root = Path(__file__).parent.parent.parent.parent
    config_dir = package_root / "config"

    return config_dir


def list_available_recipes() -> Dict[str, Path]:
    """
    List all available recipe configurations.

    Returns:
        Dictionary mapping recipe names to their file paths
    """
    config_dir = get_default_config_dir()
    recipes_dir = config_dir / "recipes"

    if not recipes_dir.exists():
        return {}

    recipes = {}
    for recipe_file in recipes_dir.glob("*.json"):
        recipe_name = recipe_file.stem
        recipes[recipe_name] = recipe_file

    return recipes


def list_available_datasets() -> Dict[str, Path]:
    """
    List all available dataset configurations.

    Returns:
        Dictionary mapping dataset names to their file paths
    """
    config_dir = get_default_config_dir()
    datasets_dir = config_dir / "datasets"

    if not datasets_dir.exists():
        return {}

    datasets = {}
    for dataset_file in datasets_dir.glob("*.json"):
        dataset_name = dataset_file.stem
        datasets[dataset_name] = dataset_file

    return datasets
