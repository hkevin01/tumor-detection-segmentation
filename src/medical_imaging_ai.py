#!/usr/bin/env python3
"""
Medical Imaging AI Backend for Tumor Detection and Segmentation
Using MONAI framework with advanced deep learning models
"""

import os
import logging
from datetime import datetime
from typing import Dict, List

import torch
import numpy as np
import nibabel as nib

# MONAI imports for medical imaging
try:
    from monai.networks.nets import UNet, SegResNet, SwinUNETR
    from monai.networks.layers import Norm
    from monai.metrics import (DiceMetric, HausdorffDistanceMetric,
                               SurfaceDistanceMetric)
    from monai.inferers import sliding_window_inference
    from monai.transforms import (
        Compose, LoadImaged, EnsureChannelFirstd, Orientationd, Spacingd,
        ScaleIntensityRanged, CropForegroundd, RandCropByPosNegLabeld,
        RandFlipd, RandRotate90d, RandScaleIntensityd, RandShiftIntensityd,
        EnsureTyped, AsDiscreted, KeepLargestConnectedComponentd
    )
    MONAI_AVAILABLE = True
except ImportError:
    MONAI_AVAILABLE = False
    print("MONAI not available. Please install with: pip install monai")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MedicalImagingAI:
    """
    Comprehensive medical imaging AI backend for tumor detection
    and segmentation
    """
    
    class MedicalImagingAI:
    """
    Comprehensive medical imaging AI backend for tumor detection
    and segmentation using MONAI framework
    """
    
    def __init__(self, config: Dict = None):
        """Initialize the medical imaging AI system"""
        if not MONAI_AVAILABLE:
            raise ImportError("MONAI is required but not available")
            
        self.config = config or self._default_config()
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device_str)
        self.models = {}
        self.metrics = self._setup_metrics()
        self.transforms = self._setup_transforms()
        
        logger.info("Medical Imaging AI initialized on device: %s",
                    self.device)
        
    def _default_config(self) -> Dict:
        """Default configuration for medical imaging AI"""
        return {
            "models": {
                "unet": {
                    "spatial_dims": 3,
                    "in_channels": 1,
                    "out_channels": 2,  # background + tumor
                    "channels": (16, 32, 64, 128, 256),
                    "strides": (2, 2, 2, 2),
                    "num_res_units": 2,
                    "norm": Norm.BATCH,
                    "dropout": 0.1
                },
                "segresnet": {
                    "spatial_dims": 3,
                    "init_filters": 32,
                    "in_channels": 1,
                    "out_channels": 2,
                    "dropout_prob": 0.2,
                    "norm_name": "batch",
                    "num_groups": 8
                },
                "swinunetr": {
                    "img_size": (96, 96, 96),
                    "in_channels": 1,
                    "out_channels": 2,
                    "feature_size": 48,
                    "use_checkpoint": True,
                    "spatial_dims": 3
                }
            },
            "inference": {
                "roi_size": (96, 96, 96),
                "sw_batch_size": 4,
                "overlap": 0.5,
                "mode": "gaussian",
                "sigma_scale": 0.125
            },
            "preprocessing": {
                "spacing": [1.0, 1.0, 1.0],
                "intensity_range": [-200, 200],
                "intensity_scale": [0, 1],
                "crop_foreground": True
            },
            "postprocessing": {
                "keep_largest_component": True,
                "threshold": 0.5
            }
        }
    
    def _setup_metrics(self) -> Dict:
        """Setup evaluation metrics"""
        return {
            "dice": DiceMetric(include_background=False, reduction="mean"),
            "hausdorff": HausdorffDistanceMetric(include_background=False,
                                                 reduction="mean"),
            "surface_distance": SurfaceDistanceMetric(
                include_background=False, reduction="mean")
        }
    
    def _setup_transforms(self) -> Dict:
        """Setup data transforms for preprocessing and augmentation"""
        transforms = {}
        
        # Preprocessing configuration
        spacing = self.config["preprocessing"]["spacing"]
        intensity_range = self.config["preprocessing"]["intensity_range"]
        intensity_scale = self.config["preprocessing"]["intensity_scale"]
        roi_size = self.config["inference"]["roi_size"]
        
        # Inference transforms
        transforms["inference"] = Compose([
            LoadImaged(keys=["image"]),
            EnsureChannelFirstd(keys=["image"]),
            Orientationd(keys=["image"], axcodes="RAS"),
            Spacingd(keys=["image"], pixdim=spacing, mode="bilinear"),
            ScaleIntensityRanged(
                keys=["image"],
                a_min=intensity_range[0],
                a_max=intensity_range[1],
                b_min=intensity_scale[0],
                b_max=intensity_scale[1],
                clip=True
            ),
            CropForegroundd(keys=["image"], source_key="image"),
            EnsureTyped(keys=["image"])
        ])
        
        # Training transforms with augmentation
        transforms["training"] = Compose([
            LoadImaged(keys=["image", "label"]),
            EnsureChannelFirstd(keys=["image", "label"]),
            Orientationd(keys=["image", "label"], axcodes="RAS"),
            Spacingd(keys=["image", "label"], pixdim=spacing,
                     mode=["bilinear", "nearest"]),
            ScaleIntensityRanged(
                keys=["image"],
                a_min=intensity_range[0],
                a_max=intensity_range[1],
                b_min=intensity_scale[0],
                b_max=intensity_scale[1],
                clip=True
            ),
            CropForegroundd(keys=["image", "label"], source_key="image"),
            RandCropByPosNegLabeld(
                keys=["image", "label"],
                label_key="label",
                spatial_size=roi_size,
                pos=1,
                neg=1,
                num_samples=4,
                image_key="image",
                image_threshold=0
            ),
            RandFlipd(keys=["image", "label"], prob=0.10, spatial_axis=0),
            RandFlipd(keys=["image", "label"], prob=0.10, spatial_axis=1),
            RandFlipd(keys=["image", "label"], prob=0.10, spatial_axis=2),
            RandRotate90d(keys=["image", "label"], prob=0.10, max_k=3),
            RandScaleIntensityd(keys="image", factors=0.1, prob=0.15),
            RandShiftIntensityd(keys="image", offsets=0.1, prob=0.15),
            EnsureTyped(keys=["image", "label"])
        ])
        
        # Post-processing transforms
        transforms["postprocessing"] = Compose([
            EnsureTyped(keys="pred"),
            AsDiscreted(keys="pred", argmax=True, to_onehot=2),
            KeepLargestConnectedComponentd(keys="pred", applied_labels=[1])
        ])
        
        return transforms
    
    def load_model(self, model_name: str,
                   checkpoint_path: str = None) -> torch.nn.Module:
        """Load a specific model architecture"""
        if model_name not in self.config["models"]:
            raise ValueError("Unknown model: %s" % model_name)
        
        model_config = self.config["models"][model_name]
        
        if model_name == "unet":
            model = UNet(**model_config)
        elif model_name == "segresnet":
            model = SegResNet(**model_config)
        elif model_name == "swinunetr":
            model = SwinUNETR(**model_config)
        else:
            raise ValueError("Model %s not implemented" % model_name)
        
        model = model.to(self.device)
        
        if checkpoint_path and os.path.exists(checkpoint_path):
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            model.load_state_dict(checkpoint["model_state_dict"])
            logger.info("Loaded model from %s", checkpoint_path)
        
        self.models[model_name] = model
        return model
        
    def _default_config(self) -> Dict:
        """Default configuration for medical imaging AI"""
        return {
            "models": {
                "unet": {
                    "spatial_dims": 3,
                    "in_channels": 1,
                    "out_channels": 2,  # background + tumor
                    "channels": (16, 32, 64, 128, 256),
                    "strides": (2, 2, 2, 2),
                    "num_res_units": 2,
                    "norm": Norm.BATCH,
                    "dropout": 0.1
                },
                "segresnet": {
                    "spatial_dims": 3,
                    "init_filters": 32,
                    "in_channels": 1,
                    "out_channels": 2,
                    "dropout_prob": 0.2,
                    "norm_name": "batch",
                    "num_groups": 8
                },
                "swinunetr": {
                    "img_size": (96, 96, 96),
                    "in_channels": 1,
                    "out_channels": 2,
                    "feature_size": 48,
                    "use_checkpoint": True,
                    "spatial_dims": 3
                }
            },
            "inference": {
                "roi_size": (96, 96, 96),
                "sw_batch_size": 4,
                "overlap": 0.5,
                "mode": "gaussian",
                "sigma_scale": 0.125
            },
            "preprocessing": {
                "spacing": [1.0, 1.0, 1.0],
                "intensity_range": [-200, 200],
                "intensity_scale": [0, 1],
                "crop_foreground": True
            },
            "postprocessing": {
                "keep_largest_component": True,
                "threshold": 0.5
            }
        }
    
    def _setup_metrics(self) -> Dict:
        """Setup evaluation metrics"""
        return {
            "dice": DiceMetric(include_background=False, reduction="mean"),
            "hausdorff": HausdorffDistanceMetric(include_background=False, reduction="mean"),
            "surface_distance": SurfaceDistanceMetric(include_background=False, reduction="mean")
        }
    
    def _setup_transforms(self) -> Dict:
        """Setup data transforms for preprocessing and augmentation"""
        transforms = {}
        
        # Inference transforms
        transforms["inference"] = Compose([
            LoadImaged(keys=["image"]),
            EnsureChannelFirstd(keys=["image"]),
            Orientationd(keys=["image"], axcodes="RAS"),
            Spacingd(keys=["image"], pixdim=self.config["preprocessing"]["spacing"], mode="bilinear"),
            ScaleIntensityRanged(
                keys=["image"],
                a_min=self.config["preprocessing"]["intensity_range"][0],
                a_max=self.config["preprocessing"]["intensity_range"][1],
                b_min=self.config["preprocessing"]["intensity_scale"][0],
                b_max=self.config["preprocessing"]["intensity_scale"][1],
                clip=True
            ),
            CropForegroundd(keys=["image"], source_key="image"),
            EnsureTyped(keys=["image"])
        ])
        
        # Training transforms with augmentation
        transforms["training"] = Compose([
            LoadImaged(keys=["image", "label"]),
            EnsureChannelFirstd(keys=["image", "label"]),
            Orientationd(keys=["image", "label"], axcodes="RAS"),
            Spacingd(keys=["image", "label"], pixdim=self.config["preprocessing"]["spacing"], mode=["bilinear", "nearest"]),
            ScaleIntensityRanged(
                keys=["image"],
                a_min=self.config["preprocessing"]["intensity_range"][0],
                a_max=self.config["preprocessing"]["intensity_range"][1],
                b_min=self.config["preprocessing"]["intensity_scale"][0],
                b_max=self.config["preprocessing"]["intensity_scale"][1],
                clip=True
            ),
            CropForegroundd(keys=["image", "label"], source_key="image"),
            RandCropByPosNegLabeld(
                keys=["image", "label"],
                label_key="label",
                spatial_size=self.config["inference"]["roi_size"],
                pos=1,
                neg=1,
                num_samples=4,
                image_key="image",
                image_threshold=0
            ),
            RandFlipd(keys=["image", "label"], prob=0.10, spatial_axis=0),
            RandFlipd(keys=["image", "label"], prob=0.10, spatial_axis=1),
            RandFlipd(keys=["image", "label"], prob=0.10, spatial_axis=2),
            RandRotate90d(keys=["image", "label"], prob=0.10, max_k=3),
            RandScaleIntensityd(keys="image", factors=0.1, prob=0.15),
            RandShiftIntensityd(keys="image", offsets=0.1, prob=0.15),
            EnsureTyped(keys=["image", "label"])
        ])
        
        # Post-processing transforms
        transforms["postprocessing"] = Compose([
            EnsureTyped(keys="pred"),
            AsDiscreted(keys="pred", argmax=True, to_onehot=2),
            KeepLargestConnectedComponentd(keys="pred", applied_labels=[1])
        ])
        
        return transforms
    
    def load_model(self, model_name: str, checkpoint_path: str = None) -> torch.nn.Module:
        """Load a specific model architecture"""
        if model_name not in self.config["models"]:
            raise ValueError(f"Unknown model: {model_name}")
        
        model_config = self.config["models"][model_name]
        
        if model_name == "unet":
            model = UNet(**model_config)
        elif model_name == "segresnet":
            model = SegResNet(**model_config)
        elif model_name == "swinunetr":
            model = SwinUNETR(**model_config)
        else:
            raise ValueError(f"Model {model_name} not implemented")
        
        model = model.to(self.device)
        
        if checkpoint_path and os.path.exists(checkpoint_path):
            checkpoint = torch.load(checkpoint_path, map_location=self.device)
            model.load_state_dict(checkpoint["model_state_dict"])
            logger.info(f"Loaded model from {checkpoint_path}")
        
        self.models[model_name] = model
        return model
    
    def preprocess_dicom(self, dicom_path: str) -> Dict:
        """Preprocess DICOM image for inference"""
        try:
            # Convert DICOM to NIfTI format for MONAI processing
            import pydicom
            import SimpleITK as sitk
            
            # Read DICOM
            dicom = pydicom.dcmread(dicom_path)
            
            # Convert to SimpleITK image
            image_array = dicom.pixel_array.astype(np.float32)
            sitk_image = sitk.GetImageFromArray(image_array)
            
            # Set spacing from DICOM metadata
            if hasattr(dicom, 'PixelSpacing'):
                spacing = list(dicom.PixelSpacing) + [dicom.SliceThickness if hasattr(dicom, 'SliceThickness') else 1.0]
                sitk_image.SetSpacing(spacing)
            
            # Save as temporary NIfTI
            temp_nii_path = "/tmp/temp_dicom.nii.gz"
            sitk.WriteImage(sitk_image, temp_nii_path)
            
            # Process with MONAI transforms
            data = {"image": temp_nii_path}
            processed = self.transforms["inference"](data)
            
            # Extract metadata
            metadata = {
                "patient_id": getattr(dicom, 'PatientID', 'Unknown'),
                "study_date": getattr(dicom, 'StudyDate', 'Unknown'),
                "modality": getattr(dicom, 'Modality', 'Unknown'),
                "series_description": getattr(dicom, 'SeriesDescription', 'Unknown'),
                "spacing": spacing if 'spacing' in locals() else [1.0, 1.0, 1.0],
                "shape": processed["image"].shape[1:],  # Exclude channel dimension
                "processed_path": temp_nii_path
            }
            
            return {
                "image_tensor": processed["image"],
                "metadata": metadata,
                "original_transforms": processed.get("original_transforms", {})
            }
            
        except Exception as e:
            logger.error(f"Error preprocessing DICOM {dicom_path}: {str(e)}")
            raise
    
    def predict_tumor(self, image_data: Dict, model_name: str = "unet") -> Dict:
        """Perform tumor segmentation prediction"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not loaded")
        
        model = self.models[model_name]
        model.eval()
        
        with torch.no_grad():
            # Prepare input
            image_tensor = image_data["image_tensor"].unsqueeze(0).to(self.device)
            
            # Sliding window inference for large volumes
            prediction = sliding_window_inference(
                inputs=image_tensor,
                roi_size=self.config["inference"]["roi_size"],
                sw_batch_size=self.config["inference"]["sw_batch_size"],
                predictor=model,
                overlap=self.config["inference"]["overlap"],
                mode=self.config["inference"]["mode"],
                sigma_scale=self.config["inference"]["sigma_scale"]
            )
            
            # Post-process prediction
            pred_data = {"pred": prediction}
            post_processed = self.transforms["postprocessing"](pred_data)
            
            # Calculate confidence scores
            probabilities = torch.softmax(prediction, dim=1)
            tumor_probability = probabilities[0, 1].cpu().numpy()
            
            # Extract tumor regions and statistics
            tumor_mask = post_processed["pred"][0, 1].cpu().numpy()
            tumor_volume = np.sum(tumor_mask) * np.prod(image_data["metadata"]["spacing"])
            
            # Calculate confidence score (mean probability of tumor voxels)
            tumor_voxels = tumor_mask > 0
            confidence_score = float(np.mean(tumor_probability[tumor_voxels])) if np.any(tumor_voxels) else 0.0
            
            # Generate bounding box
            if np.any(tumor_voxels):
                coords = np.where(tumor_voxels)
                bbox = {
                    "min": [int(np.min(coords[i])) for i in range(3)],
                    "max": [int(np.max(coords[i])) for i in range(3)]
                }
            else:
                bbox = None
            
            return {
                "segmentation_mask": tumor_mask,
                "probability_map": tumor_probability,
                "confidence_score": confidence_score,
                "tumor_volume_mm3": tumor_volume,
                "bounding_box": bbox,
                "model_used": model_name,
                "inference_time": datetime.now().isoformat(),
                "metadata": image_data["metadata"]
            }
    
    def batch_predict(self, image_paths: List[str], model_name: str = "unet") -> List[Dict]:
        """Perform batch prediction on multiple images"""
        results = []
        
        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"Processing image {i+1}/{len(image_paths)}: {image_path}")
                
                # Preprocess
                image_data = self.preprocess_dicom(image_path)
                
                # Predict
                prediction = self.predict_tumor(image_data, model_name)
                prediction["image_path"] = image_path
                
                results.append(prediction)
                
            except Exception as e:
                logger.error(f"Error processing {image_path}: {str(e)}")
                results.append({
                    "image_path": image_path,
                    "error": str(e),
                    "inference_time": datetime.now().isoformat()
                })
        
        return results
    
    def evaluate_model(self, test_data: List[Dict], model_name: str = "unet") -> Dict:
        """Evaluate model performance on test data"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not loaded")
        
        model = self.models[model_name]
        model.eval()
        
        # Reset metrics
        for metric in self.metrics.values():
            metric.reset()
        
        results = []
        
        with torch.no_grad():
            for data in test_data:
                # Preprocess
                image_tensor = data["image"].unsqueeze(0).to(self.device)
                label_tensor = data["label"].unsqueeze(0).to(self.device)
                
                # Predict
                prediction = sliding_window_inference(
                    inputs=image_tensor,
                    roi_size=self.config["inference"]["roi_size"],
                    sw_batch_size=self.config["inference"]["sw_batch_size"],
                    predictor=model,
                    overlap=self.config["inference"]["overlap"]
                )
                
                # Post-process
                pred_data = {"pred": prediction}
                post_processed = self.transforms["postprocessing"](pred_data)
                pred_tensor = post_processed["pred"]
                
                # Update metrics
                self.metrics["dice"](y_pred=pred_tensor, y=label_tensor)
                self.metrics["hausdorff"](y_pred=pred_tensor, y=label_tensor)
                self.metrics["surface_distance"](y_pred=pred_tensor, y=label_tensor)
                
                results.append({
                    "dice": float(self.metrics["dice"].aggregate().item()),
                    "hausdorff": float(self.metrics["hausdorff"].aggregate().item()),
                    "surface_distance": float(self.metrics["surface_distance"].aggregate().item())
                })
        
        # Aggregate final metrics
        final_metrics = {
            "dice_score": float(self.metrics["dice"].aggregate().item()),
            "hausdorff_distance": float(self.metrics["hausdorff"].aggregate().item()),
            "surface_distance": float(self.metrics["surface_distance"].aggregate().item()),
            "num_cases": len(test_data),
            "model_name": model_name,
            "evaluation_time": datetime.now().isoformat()
        }
        
        return final_metrics
    
    def save_segmentation(self, prediction: Dict, output_path: str, format: str = "nifti"):
        """Save segmentation mask in specified format"""
        mask = prediction["segmentation_mask"]
        metadata = prediction["metadata"]
        
        if format.lower() == "nifti":
            # Create NIfTI image
            nii_img = nib.Nifti1Image(mask.astype(np.uint8), affine=np.eye(4))
            nii_img.header.set_xyzt_units('mm', 'sec')
            
            # Set spacing
            spacing = metadata.get("spacing", [1.0, 1.0, 1.0])
            nii_img.header.set_zooms(spacing)
            
            nib.save(nii_img, output_path)
            
        elif format.lower() == "dicom":
            # Convert back to DICOM format (requires additional implementation)
            # This would involve creating DICOM segmentation objects
            pass
            
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Segmentation saved to {output_path}")
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        info = {}
        
        for name, model in self.models.items():
            # Count parameters
            total_params = sum(p.numel() for p in model.parameters())
            trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
            
            info[name] = {
                "architecture": model.__class__.__name__,
                "total_parameters": total_params,
                "trainable_parameters": trainable_params,
                "device": str(next(model.parameters()).device),
                "config": self.config["models"][name]
            }
        
        return info
    
    def update_config(self, new_config: Dict):
        """Update configuration parameters"""
        self.config.update(new_config)
        self.transforms = self._setup_transforms()  # Recreate transforms with new config
        logger.info("Configuration updated")

# Example usage and testing
if __name__ == "__main__":
    # Initialize the medical imaging AI
    ai = MedicalImagingAI()
    
    # Load models
    ai.load_model("unet")
    ai.load_model("segresnet")
    
    # Get model information
    model_info = ai.get_model_info()
    print("Available models:")
    for name, info in model_info.items():
        print(f"  {name}: {info['total_parameters']} parameters")
    
    print("Medical Imaging AI backend ready for integration with GUI frontend.")
