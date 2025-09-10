"""
Device management utilities for tumor detection package.

Automatic device detection and configuration based on available hardware.
"""

import logging

import torch

logger = logging.getLogger(__name__)


def auto_device_resolve() -> str:
    """
    Automatically resolve the best available device for computation.

    Returns:
        String representing the best device ('cuda' or 'cpu')

    Example:
        >>> device = auto_device_resolve()
        >>> print(f"Using device: {device}")
        Using device: cuda
    """
    if torch.cuda.is_available():
        device = "cuda"
        gpu_count = torch.cuda.device_count()
        gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
        total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9

        logger.info(f"CUDA available: Using GPU {gpu_name} "
                   f"({total_memory:.1f}GB memory)")
    else:
        device = "cpu"
        logger.info("CUDA not available: Using CPU")

    return device


def get_device_info() -> dict:
    """
    Get detailed information about available devices.

    Returns:
        Dictionary containing device information
    """
    info = {
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "recommended_device": auto_device_resolve()
    }

    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            info[f"gpu_{i}"] = {
                "name": props.name,
                "total_memory_gb": props.total_memory / 1e9,
                "major": props.major,
                "minor": props.minor,
                "multi_processor_count": props.multi_processor_count
            }

    return info


def check_memory_requirements(model_name: str = "unetr") -> dict:
    """
    Check if current device meets memory requirements for specific models.

    Args:
        model_name: Name of the model to check requirements for

    Returns:
        Dictionary with memory check results
    """
    # Approximate memory requirements (in GB) for different models
    memory_requirements = {
        "unetr": {
            "minimum": 8.0,
            "recommended": 16.0,
            "optimal": 24.0
        },
        "unet": {
            "minimum": 4.0,
            "recommended": 8.0,
            "optimal": 12.0
        },
        "swin_unetr": {
            "minimum": 12.0,
            "recommended": 20.0,
            "optimal": 32.0
        }
    }

    requirements = memory_requirements.get(model_name.lower(),
                                          memory_requirements["unetr"])

    result = {
        "model": model_name,
        "requirements": requirements,
        "device": auto_device_resolve(),
        "meets_minimum": False,
        "meets_recommended": False,
        "meets_optimal": False
    }

    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        available_memory = props.total_memory / 1e9

        result["available_memory_gb"] = available_memory
        result["meets_minimum"] = available_memory >= requirements["minimum"]
        result["meets_recommended"] = available_memory >= requirements["recommended"]
        result["meets_optimal"] = available_memory >= requirements["optimal"]
    else:
        # CPU - assume sufficient memory but note performance implications
        result["available_memory_gb"] = "Unknown (CPU)"
        result["meets_minimum"] = True
        result["meets_recommended"] = True
        result["meets_optimal"] = False
        result["note"] = "CPU inference will be significantly slower"

    return result
    return result
