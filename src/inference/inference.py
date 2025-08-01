"""
Inference module for tumor detection and segmentation.

This module provides functionality for running inference on new medical images
using trained models.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    import torch
    import numpy as np
    from monai.transforms import Compose, LoadImage, EnsureChannelFirst, Resize, ScaleIntensity
    from monai.data import DataLoader, Dataset
    import matplotlib.pyplot as plt
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

import json
import argparse
from typing import Dict, Any, List, Optional, Union


class TumorPredictor:
    """Class for running inference on medical images."""
    
    def __init__(self, model_path: str, config_path: str, device: str = 'auto'):
        """
        Initialize predictor.
        
        Args:
            model_path: Path to trained model checkpoint
            config_path: Path to configuration file
            device: Device to run inference on
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies not available")
        
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Set device
        if device == 'auto':
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # Load model
        self.model = self._load_model(model_path)
        self.model.eval()
        
        # Setup transforms
        self.transforms = self._setup_transforms()
    
    def _load_model(self, model_path: str):
        """Load trained model from checkpoint."""
        from training.trainer import create_model
        
        # Create model architecture
        model = create_model(self.config)
        
        # Load trained weights
        checkpoint = torch.load(model_path, map_location=self.device)
        
        if 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
        
        model.to(self.device)
        return model
    
    def _setup_transforms(self):
        """Setup preprocessing transforms for inference."""
        return Compose([
            LoadImage(image_only=True),
            EnsureChannelFirst(),
            Resize(self.config.get('image_size', [128, 128, 128])),
            ScaleIntensity(),
        ])
    
    def predict_single(self, image_path: str) -> Dict[str, Any]:
        """
        Run inference on a single image.
        
        Args:
            image_path: Path to input image
            
        Returns:
            Dictionary containing prediction results
        """
        # Preprocess image
        data_dict = {"image": image_path}
        data_dict = self.transforms(data_dict)
        
        # Add batch dimension
        image = data_dict["image"].unsqueeze(0).to(self.device)
        
        # Run inference
        with torch.no_grad():
            prediction = self.model(image)
            
            # Post-process prediction
            prediction = torch.softmax(prediction, dim=1)
            prediction = torch.argmax(prediction, dim=1)
            
        # Convert to numpy for easier handling
        prediction_np = prediction.cpu().numpy().squeeze()
        
        return {
            'prediction': prediction_np,
            'input_shape': image.shape,
            'output_shape': prediction.shape,
            'device': str(self.device)
        }
    
    def predict_batch(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Run inference on multiple images.
        
        Args:
            image_paths: List of paths to input images
            
        Returns:
            List of prediction results
        """
        results = []
        
        for image_path in image_paths:
            try:
                result = self.predict_single(image_path)
                result['image_path'] = image_path
                result['status'] = 'success'
            except Exception as e:
                result = {
                    'image_path': image_path,
                    'status': 'error',
                    'error': str(e)
                }
            
            results.append(result)
        
        return results
    
    def predict_from_directory(self, input_dir: str, 
                              output_dir: Optional[str] = None,
                              file_pattern: str = "*.nii.gz") -> Dict[str, Any]:
        """
        Run inference on all images in a directory.
        
        Args:
            input_dir: Directory containing input images
            output_dir: Directory to save results (optional)
            file_pattern: Pattern to match image files
            
        Returns:
            Summary of prediction results
        """
        input_path = Path(input_dir)
        image_files = list(input_path.glob(file_pattern))
        
        if not image_files:
            raise ValueError(f"No images found matching pattern {file_pattern} in {input_dir}")
        
        print(f"Found {len(image_files)} images to process")
        
        # Run predictions
        results = self.predict_batch([str(f) for f in image_files])
        
        # Save results if output directory specified
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save individual predictions
            for result in results:
                if result['status'] == 'success':
                    filename = Path(result['image_path']).stem + '_prediction.npy'
                    np.save(output_path / filename, result['prediction'])
            
            # Save summary
            summary_file = output_path / 'prediction_summary.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_images': len(image_files),
                    'successful_predictions': sum(1 for r in results if r['status'] == 'success'),
                    'failed_predictions': sum(1 for r in results if r['status'] == 'error'),
                    'results': results
                }, f, indent=2)
        
        return {
            'total_processed': len(image_files),
            'successful': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'error'),
            'results': results
        }


def main():
    """Main inference function."""
    parser = argparse.ArgumentParser(description='Run tumor segmentation inference')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to trained model checkpoint')
    parser.add_argument('--config', type=str, default='config.json',
                       help='Path to configuration file')
    parser.add_argument('--input', type=str, required=True,
                       help='Path to input image or directory')
    parser.add_argument('--output', type=str, default='./results',
                       help='Path to output directory')
    parser.add_argument('--device', type=str, default='auto',
                       help='Device to run inference on (auto, cpu, cuda)')
    
    args = parser.parse_args()
    
    if not DEPENDENCIES_AVAILABLE:
        print("Error: Required dependencies not available.")
        print("Please install: pip install -r requirements.txt")
        return
    
    print("Tumor Segmentation Inference")
    print("=" * 35)
    print(f"Model: {args.model}")
    print(f"Input: {args.input}")
    print(f"Output: {args.output}")
    
    try:
        # Create predictor
        predictor = TumorPredictor(
            model_path=args.model,
            config_path=args.config,
            device=args.device
        )
        
        print(f"Using device: {predictor.device}")
        
        # Run inference
        input_path = Path(args.input)
        
        if input_path.is_file():
            # Single file inference
            result = predictor.predict_single(str(input_path))
            
            # Save result
            output_path = Path(args.output)
            output_path.mkdir(parents=True, exist_ok=True)
            np.save(output_path / 'prediction.npy', result['prediction'])
            
            print(f"Prediction saved to: {output_path / 'prediction.npy'}")
            
        elif input_path.is_dir():
            # Directory inference
            summary = predictor.predict_from_directory(
                input_dir=str(input_path),
                output_dir=args.output
            )
            
            print(f"Processed {summary['total_processed']} images")
            print(f"Successful: {summary['successful']}")
            print(f"Failed: {summary['failed']}")
            
        else:
            print(f"Error: Input path does not exist: {args.input}")
            return
        
        print("Inference completed!")
        
    except Exception as e:
        print(f"Inference failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
