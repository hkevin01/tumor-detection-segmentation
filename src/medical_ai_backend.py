#!/usr/bin/env python3
"""
Medical Imaging AI Backend for Tumor Detection and Segmentation
Comprehensive MONAI-based implementation with multiple model architectures
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
import warnings

import torch
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)


class MedicalImagingAI:
    """
    Comprehensive medical imaging AI backend for tumor detection and segmentation
    Supports UNet, SegResNet, SwinUNETR architectures with MONAI transforms
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the medical imaging AI system"""
        self.config = config or self._default_config()
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = torch.device(device_str)
        self.models = {}
        self.transforms = {}
        
        # Initialize MONAI components
        self._setup_transforms()
        
        logger.info("Medical Imaging AI initialized on device: %s",
                    self.device)
        if torch.cuda.is_available():
            logger.info("GPU: %s", torch.cuda.get_device_name(0))
            logger.info("CUDA Memory: %.1f GB",
                       torch.cuda.get_device_properties(0).total_memory / 1e9)
    
    def _default_config(self) -> Dict:
        """Comprehensive configuration for medical imaging AI"""
        return {
            "models": {
                "unet": {
                    "spatial_dims": 3,
                    "in_channels": 1,
                    "out_channels": 2,
                    "channels": (16, 32, 64, 128, 256),
                    "strides": (2, 2, 2, 2),
                    "num_res_units": 2,
                    "dropout": 0.1
                },
                "segresnet": {
                    "spatial_dims": 3,
                    "init_filters": 8,
                    "in_channels": 1,
                    "out_channels": 2,
                    "dropout_prob": 0.2,
                    "blocks_down": [1, 2, 2, 4],
                    "blocks_up": [1, 1, 1]
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
                "sigma_scale": 0.125,
                "padding_mode": "constant",
                "cval": 0.0
            },
            "preprocessing": {
                "spacing": [1.0, 1.0, 1.0],
                "spatial_size": [96, 96, 96],
                "intensity_range": [-200, 200],
                "intensity_scale": [0, 1],
                "clip": True
            },
            "postprocessing": {
                "threshold": 0.5,
                "connectivity": 1,
                "min_size": 64
            }
        }
    
    def _setup_transforms(self):
        """Setup MONAI transforms for preprocessing and augmentation"""
        try:
            from monai.transforms import (
                Compose, LoadImaged, AddChanneld, Spacingd, Orientationd,
                ScaleIntensityRanged, CropForegroundd, Resized,
                EnsureTyped, EnsureChannelFirstd, NormalizeIntensityd,
                RandRotated, RandFlipd, RandScaleIntensityd, RandShiftIntensityd
            )
            
            # Training transforms with augmentation
            self.transforms["train"] = Compose([
                LoadImaged(keys=["image", "label"]),
                EnsureChannelFirstd(keys=["image", "label"]),
                Spacingd(keys=["image", "label"], 
                        pixdim=self.config["preprocessing"]["spacing"],
                        mode=("bilinear", "nearest")),
                Orientationd(keys=["image", "label"], axcodes="RAS"),
                ScaleIntensityRanged(keys=["image"],
                                   a_min=self.config["preprocessing"]["intensity_range"][0],
                                   a_max=self.config["preprocessing"]["intensity_range"][1],
                                   b_min=self.config["preprocessing"]["intensity_scale"][0],
                                   b_max=self.config["preprocessing"]["intensity_scale"][1],
                                   clip=self.config["preprocessing"]["clip"]),
                CropForegroundd(keys=["image", "label"], source_key="image"),
                Resized(keys=["image", "label"],
                       spatial_size=self.config["preprocessing"]["spatial_size"],
                       mode=("trilinear", "nearest")),
                # Data augmentation
                RandRotated(keys=["image", "label"], range_x=0.1, range_y=0.1, range_z=0.1, prob=0.2),
                RandFlipd(keys=["image", "label"], spatial_axis=[0], prob=0.5),
                RandFlipd(keys=["image", "label"], spatial_axis=[1], prob=0.5),
                RandFlipd(keys=["image", "label"], spatial_axis=[2], prob=0.5),
                RandScaleIntensityd(keys=["image"], factors=0.1, prob=0.1),
                RandShiftIntensityd(keys=["image"], offsets=0.1, prob=0.1),
                EnsureTyped(keys=["image", "label"])
            ])
            
            # Validation/Inference transforms
            self.transforms["val"] = Compose([
                LoadImaged(keys=["image"]),
                EnsureChannelFirstd(keys=["image"]),
                Spacingd(keys=["image"], 
                        pixdim=self.config["preprocessing"]["spacing"],
                        mode="bilinear"),
                Orientationd(keys=["image"], axcodes="RAS"),
                ScaleIntensityRanged(keys=["image"],
                                   a_min=self.config["preprocessing"]["intensity_range"][0],
                                   a_max=self.config["preprocessing"]["intensity_range"][1],
                                   b_min=self.config["preprocessing"]["intensity_scale"][0],
                                   b_max=self.config["preprocessing"]["intensity_scale"][1],
                                   clip=self.config["preprocessing"]["clip"]),
                CropForegroundd(keys=["image"], source_key="image"),
                EnsureTyped(keys=["image"])
            ])
            
        except ImportError:
            logger.warning("MONAI transforms not available. Using basic preprocessing.")
            self.transforms["train"] = None
            self.transforms["val"] = None
    
    def load_model(self, model_name: str, checkpoint_path: Optional[str] = None) -> torch.nn.Module:
        """Load a MONAI model for inference"""
        try:
            if model_name == "unet":
                from monai.networks.nets import UNet
                model_config = self.config["models"][model_name]
                model = UNet(**model_config)
                
            elif model_name == "segresnet":
                from monai.networks.nets import SegResNet
                model_config = self.config["models"][model_name]
                model = SegResNet(**model_config)
                
            elif model_name == "swinunetr":
                from monai.networks.nets import SwinUNETR
                model_config = self.config["models"][model_name]
                model = SwinUNETR(**model_config)
                
            else:
                raise ValueError(f"Model {model_name} not supported")
            
            model = model.to(self.device)
            model.eval()
            
            if checkpoint_path and os.path.exists(checkpoint_path):
                checkpoint = torch.load(checkpoint_path, map_location=self.device)
                if "model_state_dict" in checkpoint:
                    model.load_state_dict(checkpoint["model_state_dict"])
                else:
                    model.load_state_dict(checkpoint)
                logger.info("Loaded model from %s", checkpoint_path)
            else:
                logger.info("Initialized model %s with random weights", model_name)
            
            self.models[model_name] = model
            return model
            
        except ImportError:
            logger.error("MONAI not available. Install with: pip install monai")
            raise
    
    def predict_tumor(self, 
                     image_data: Union[str, np.ndarray, torch.Tensor], 
                     model_name: str = "unet",
                     return_probabilities: bool = False) -> Dict:
        """
        Comprehensive tumor prediction with multiple output formats
        
        Args:
            image_data: Path to image file, numpy array, or torch tensor
            model_name: Name of the model to use
            return_probabilities: Whether to return probability maps
            
        Returns:
            Dictionary with prediction results
        """
        if model_name not in self.models:
            logger.warning("Model %s not loaded. Loading now...", model_name)
            self.load_model(model_name)
        
        model = self.models[model_name]
        
        start_time = datetime.now()
        
        try:
            # Preprocess input
            if isinstance(image_data, str):
                # Load from file path
                processed_data = self._preprocess_image_file(image_data)
            elif isinstance(image_data, np.ndarray):
                processed_data = self._preprocess_array(image_data)
            elif isinstance(image_data, torch.Tensor):
                processed_data = image_data.to(self.device)
            else:
                raise ValueError("Unsupported image_data type")
            
            # Run inference
            with torch.no_grad():
                if processed_data.dim() == 4:  # Add batch dimension if needed
                    processed_data = processed_data.unsqueeze(0)
                
                # Use sliding window inference for large volumes
                prediction = self._sliding_window_inference(processed_data, model)
            
            # Post-process results
            results = self._postprocess_prediction(prediction, return_probabilities)
            
            # Calculate metrics
            inference_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "segmentation_mask": results["mask"],
                "probability_maps": results.get("probabilities"),
                "confidence_score": results["confidence"],
                "tumor_volume_mm3": results["volume"],
                "tumor_volume_ml": results["volume"] / 1000.0,
                "bounding_box": results["bbox"],
                "model_used": model_name,
                "inference_time": inference_time,
                "timestamp": datetime.now().isoformat(),
                "device": str(self.device),
                "roi_size": self.config["inference"]["roi_size"],
                "overlap": self.config["inference"]["overlap"]
            }
            
        except Exception as e:
            logger.error("Prediction failed: %s", str(e))
            return {
                "error": str(e),
                "model_used": model_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def _preprocess_image_file(self, image_path: str) -> torch.Tensor:
        """Preprocess image from file path"""
        if self.transforms["val"]:
            data = self.transforms["val"]({"image": image_path})
            return data["image"].to(self.device)
        else:
            # Basic preprocessing without MONAI transforms
            import SimpleITK as sitk
            image = sitk.ReadImage(image_path)
            array = sitk.GetArrayFromImage(image)
            tensor = torch.from_numpy(array).float()
            return tensor.unsqueeze(0).to(self.device)  # Add channel dimension
    
    def _preprocess_array(self, array: np.ndarray) -> torch.Tensor:
        """Preprocess numpy array"""
        tensor = torch.from_numpy(array).float()
        if tensor.dim() == 3:  # Add channel dimension
            tensor = tensor.unsqueeze(0)
        return tensor.to(self.device)
    
    def _sliding_window_inference(self, image: torch.Tensor, model: torch.nn.Module) -> torch.Tensor:
        """Perform sliding window inference for large volumes"""
        try:
            from monai.inferers import sliding_window_inference
            return sliding_window_inference(
                inputs=image,
                roi_size=self.config["inference"]["roi_size"],
                sw_batch_size=self.config["inference"]["sw_batch_size"],
                predictor=model,
                overlap=self.config["inference"]["overlap"],
                mode=self.config["inference"]["mode"],
                sigma_scale=self.config["inference"]["sigma_scale"],
                padding_mode=self.config["inference"]["padding_mode"],
                cval=self.config["inference"]["cval"],
                device=self.device
            )
        except ImportError:
            # Fallback to direct model inference
            logger.warning("MONAI sliding window inference not available. Using direct inference.")
            return model(image)
    
    def _postprocess_prediction(self, prediction: torch.Tensor, return_probabilities: bool = False) -> Dict:
        """Post-process prediction tensor to extract results"""
        # Convert to numpy
        if prediction.is_cuda:
            pred_numpy = prediction.cpu().numpy()
        else:
            pred_numpy = prediction.numpy()
        
        # Remove batch dimension
        if pred_numpy.ndim == 5:  # [B, C, H, W, D]
            pred_numpy = pred_numpy[0]
        
        # Get probability and segmentation
        if pred_numpy.shape[0] == 2:  # Binary segmentation with background
            prob_map = pred_numpy[1]  # Tumor probability
            seg_mask = (prob_map > self.config["postprocessing"]["threshold"]).astype(np.uint8)
        else:
            prob_map = pred_numpy[0] if pred_numpy.ndim == 4 else pred_numpy
            seg_mask = (prob_map > self.config["postprocessing"]["threshold"]).astype(np.uint8)
        
        # Calculate metrics
        confidence = float(np.max(prob_map))
        volume = float(np.sum(seg_mask))  # Volume in voxels (convert to mm³ with spacing)
        
        # Calculate bounding box
        indices = np.where(seg_mask > 0)
        if len(indices[0]) > 0:
            bbox = {
                "min": [int(np.min(indices[i])) for i in range(3)],
                "max": [int(np.max(indices[i])) for i in range(3)]
            }
        else:
            bbox = {"min": [0, 0, 0], "max": [0, 0, 0]}
        
        results = {
            "mask": seg_mask,
            "confidence": confidence,
            "volume": volume,
            "bbox": bbox
        }
        
        if return_probabilities:
            results["probabilities"] = prob_map
        
        return results
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        model_info = {}
        
        for model_name, model in self.models.items():
            try:
                total_params = sum(p.numel() for p in model.parameters())
                trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
                
                model_info[model_name] = {
                    "architecture": model.__class__.__name__,
                    "total_parameters": total_params,
                    "trainable_parameters": trainable_params,
                    "device": str(next(model.parameters()).device),
                    "memory_footprint_mb": self._estimate_model_memory(model),
                    "config": self.config["models"].get(model_name, {})
                }
            except Exception as e:
                model_info[model_name] = {"error": str(e)}
        
        return model_info
    
    def _estimate_model_memory(self, model: torch.nn.Module) -> float:
        """Estimate model memory footprint in MB"""
        param_size = 0
        buffer_size = 0
        
        for param in model.parameters():
            param_size += param.nelement() * param.element_size()
        
        for buffer in model.buffers():
            buffer_size += buffer.nelement() * buffer.element_size()
        
        return (param_size + buffer_size) / 1024 / 1024  # Convert to MB
    
    def benchmark_model(self, model_name: str, input_shape: Tuple[int, ...] = (1, 96, 96, 96)) -> Dict:
        """Benchmark model performance"""
        if model_name not in self.models:
            self.load_model(model_name)
        
        model = self.models[model_name]
        
        # Create dummy input
        dummy_input = torch.randn(1, *input_shape).to(self.device)
        
        # Warmup
        with torch.no_grad():
            for _ in range(5):
                _ = model(dummy_input)
        
        # Benchmark
        torch.cuda.synchronize() if torch.cuda.is_available() else None
        start_time = datetime.now()
        
        with torch.no_grad():
            for _ in range(10):
                _ = model(dummy_input)
        
        torch.cuda.synchronize() if torch.cuda.is_available() else None
        end_time = datetime.now()
        
        avg_time = (end_time - start_time).total_seconds() / 10
        
        return {
            "model_name": model_name,
            "input_shape": input_shape,
            "average_inference_time": avg_time,
            "throughput_fps": 1.0 / avg_time,
            "device": str(self.device),
            "timestamp": datetime.now().isoformat()
        }


# Example usage and testing
if __name__ == "__main__":
    print("Medical Imaging AI Backend - Comprehensive MONAI Implementation")
    print("=" * 60)
    
    # Initialize AI system
    ai = MedicalImagingAI()
    
    # Test model loading
    try:
        model = ai.load_model("unet")
        print("✅ UNet model loaded successfully")
        
        # Get model info
        info = ai.get_model_info()
        print(f"📊 Model parameters: {info['unet']['total_parameters']:,}")
        
        # Test benchmark
        benchmark = ai.benchmark_model("unet")
        print(f"⚡ Inference time: {benchmark['average_inference_time']:.3f}s")
        
    except Exception as e:
        print(f"⚠️  Model loading failed: {e}")
        print("💡 Install dependencies: pip install monai torch numpy")
    
    print("\n🏥 Medical Imaging AI backend ready for GUI integration.")
