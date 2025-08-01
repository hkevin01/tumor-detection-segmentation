"""
General utility functions for the tumor detection project.

This module provides common utility functions used throughout the project.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

try:
    import torch
    import numpy as np
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False


def setup_logging(log_dir: str = "./logs", log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_dir: Directory to save log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger instance
    """
    # Create log directory
    Path(log_dir).mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(Path(log_dir) / 'application.log'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in config file {config_path}: {e}")


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to JSON file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path where to save the configuration
    """
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, sort_keys=True)


def create_directory_structure(base_path: str, structure: Dict[str, Any]) -> None:
    """
    Create directory structure from a nested dictionary.
    
    Args:
        base_path: Base path where to create the structure
        structure: Dictionary describing the directory structure
    """
    base = Path(base_path)
    
    for name, content in structure.items():
        path = base / name
        
        if isinstance(content, dict):
            # It's a directory
            path.mkdir(exist_ok=True)
            create_directory_structure(str(path), content)
        else:
            # It's a file
            path.parent.mkdir(parents=True, exist_ok=True)
            if content is not None:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)


def get_device(prefer_gpu: bool = True) -> str:
    """
    Get the best available device for computation.
    
    Args:
        prefer_gpu: Whether to prefer GPU over CPU
        
    Returns:
        Device string ('cuda', 'mps', or 'cpu')
    """
    if not DEPENDENCIES_AVAILABLE:
        return 'cpu'
    
    if prefer_gpu:
        if torch.cuda.is_available():
            return 'cuda'
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return 'mps'
    
    return 'cpu'


def count_parameters(model) -> int:
    """
    Count the total number of parameters in a model.
    
    Args:
        model: PyTorch model
        
    Returns:
        Total number of parameters
    """
    if not DEPENDENCIES_AVAILABLE:
        raise ImportError("PyTorch not available")
    
    return sum(p.numel() for p in model.parameters())


def count_trainable_parameters(model) -> int:
    """
    Count the number of trainable parameters in a model.
    
    Args:
        model: PyTorch model
        
    Returns:
        Number of trainable parameters
    """
    if not DEPENDENCIES_AVAILABLE:
        raise ImportError("PyTorch not available")
    
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def set_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Random seed value
    """
    import random
    random.seed(seed)
    
    if DEPENDENCIES_AVAILABLE:
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
        # Ensure deterministic behavior
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory
        
    Returns:
        Path object for the directory
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes
    """
    return Path(file_path).stat().st_size


def format_bytes(size: int) -> str:
    """
    Format byte size into human readable format.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def validate_paths(paths: Dict[str, str]) -> Dict[str, bool]:
    """
    Validate that specified paths exist.
    
    Args:
        paths: Dictionary of path descriptions and paths
        
    Returns:
        Dictionary indicating which paths exist
    """
    results = {}
    for description, path in paths.items():
        results[description] = Path(path).exists()
    return results


def cleanup_empty_directories(root_path: str, exclude_dirs: Optional[List[str]] = None) -> int:
    """
    Remove empty directories recursively.
    
    Args:
        root_path: Root directory to start cleanup
        exclude_dirs: List of directory names to exclude from cleanup
        
    Returns:
        Number of directories removed
    """
    if exclude_dirs is None:
        exclude_dirs = ['.git', '__pycache__', '.pytest_cache']
    
    root = Path(root_path)
    removed_count = 0
    
    # Walk through directories bottom-up
    for dirpath in sorted(root.rglob('*'), key=lambda p: len(p.parts), reverse=True):
        if dirpath.is_dir() and dirpath.name not in exclude_dirs:
            try:
                # Try to remove if empty
                dirpath.rmdir()
                removed_count += 1
                print(f"Removed empty directory: {dirpath}")
            except OSError:
                # Directory not empty, skip
                continue
    
    return removed_count


def backup_file(file_path: str, backup_suffix: str = ".bak") -> str:
    """
    Create a backup of a file.
    
    Args:
        file_path: Path to the file to backup
        backup_suffix: Suffix for the backup file
        
    Returns:
        Path to the backup file
    """
    original = Path(file_path)
    backup_path = original.with_suffix(original.suffix + backup_suffix)
    
    if original.exists():
        import shutil
        shutil.copy2(original, backup_path)
        return str(backup_path)
    else:
        raise FileNotFoundError(f"Original file not found: {file_path}")


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries, with override taking precedence.
    
    Args:
        base_config: Base configuration
        override_config: Override configuration
        
    Returns:
        Merged configuration
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result
