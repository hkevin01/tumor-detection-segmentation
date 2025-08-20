"""
Enhanced Data Augmentation for Medical Image Segmentation

This module provides medical-specific data augmentation transforms optimized
for 3D medical image segmentation tasks. It includes transforms for addressing
common challenges in medical imaging while preserving anatomical constraints.

Components:
- MedicalTransforms: Core medical-specific augmentations
- IntensityAugmentation: MRI/CT intensity variations
- SpatialAugmentation: Geometric and elastic deformations
- NoiseAugmentation: Realistic noise injection
- ComposedAugmentation: Pipeline composition and optimization
- AugmentationConfig: Configuration and hyperparameter management
"""

__version__ = "1.0.0"
__author__ = "Medical AI Team"

from .augmentation_config import (AugmentationConfig,
                                  create_augmentation_from_config,
                                  get_domain_config)
from .composed_augmentation import (AdaptiveAugmentation,
                                    CurriculumAugmentation,
                                    MedicalAugmentationPipeline,
                                    create_augmentation_pipeline)
from .intensity_augmentation import (BiasFieldCorrection, ContrastAdjustment,
                                     GammaCorrection, IntensityShift,
                                     create_intensity_transform)
from .medical_transforms import (AnatomicalConstraints, ElasticDeformation,
                                 MedicalNormalization,
                                 create_medical_transform)
from .noise_augmentation import (GaussianNoise, GibbsRinging, MotionArtifact,
                                 RicianNoise, create_noise_transform)
from .spatial_augmentation import (AffineTransform, AnisotropicScaling,
                                   ElasticTransform, NonLinearDeformation,
                                   create_spatial_transform)

__all__ = [
    # Medical Transforms
    "ElasticDeformation",
    "AnatomicalConstraints",
    "MedicalNormalization",
    "create_medical_transform",

    # Intensity Augmentation
    "GammaCorrection",
    "BiasFieldCorrection",
    "ContrastAdjustment",
    "IntensityShift",
    "create_intensity_transform",

    # Spatial Augmentation
    "ElasticTransform",
    "AffineTransform",
    "NonLinearDeformation",
    "AnisotropicScaling",
    "create_spatial_transform",

    # Noise Augmentation
    "GaussianNoise",
    "RicianNoise",
    "MotionArtifact",
    "GibbsRinging",
    "create_noise_transform",

    # Composed Augmentation
    "MedicalAugmentationPipeline",
    "AdaptiveAugmentation",
    "CurriculumAugmentation",
    "create_augmentation_pipeline",

    # Configuration
    "AugmentationConfig",
    "get_domain_config",
    "create_augmentation_from_config",
]
