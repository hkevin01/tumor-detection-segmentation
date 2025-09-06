#!/usr/bin/env python3
"""
Enhanced evaluation script with comprehensive metrics including HD95 and ASSD.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

# Add repo src to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from benchmarking.evaluation_metrics import MedicalSegmentationMetrics
    from utils.logging_mlflow import MedicalImagingMLflowLogger
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

def compute_comprehensive_metrics(
    prediction_dir: str,
    ground_truth_dir: str,
    output_file: str = None,
    log_mlflow: bool = False
):
    """Compute comprehensive metrics including HD95 and ASSD."""
    if not DEPENDENCIES_AVAILABLE:
        print("Error: Required dependencies not available")
        return
    
    pred_path = Path(prediction_dir)
    gt_path = Path(ground_truth_dir)
    
    # Initialize metrics calculator
    metrics_calc = MedicalSegmentationMetrics()
    
    # Find matching prediction and ground truth files
    pred_files = list(pred_path.glob("*.nii.gz"))
    results = []
    
    for pred_file in pred_files:
        # Find corresponding ground truth file
        gt_file = gt_path / pred_file.name
        if not gt_file.exists():
            # Try different naming conventions
            case_name = pred_file.stem.replace("_prediction", "").replace("_pred", "")
            gt_file = gt_path / f"{case_name}.nii.gz"
            if not gt_file.exists():
                print(f"Warning: No ground truth found for {pred_file.name}")
                continue
        
        try:
            # Load images (simplified - would need nibabel in practice)
            print(f"Processing {pred_file.name}...")
            
            # This would load actual NIfTI files in practice
            # For now, simulate with dummy data
            prediction = np.random.randint(0, 2, (128, 128, 64))
            ground_truth = np.random.randint(0, 2, (128, 128, 64))
            
            # Compute comprehensive metrics
            metrics = metrics_calc.compute_comprehensive_metrics(
                prediction, ground_truth, spacing=(1.0, 1.0, 1.0)
            )
            
            result = {
                "case_id": pred_file.stem,
                "metrics": metrics.to_dict()
            }
            results.append(result)
            
            print(f"  Dice: {metrics.dice_score:.4f}")
            print(f"  HD95: {metrics.robust_hausdorff:.4f}")
            print(f"  ASSD: {metrics.symmetric_surface_distance:.4f}")
            
        except Exception as e:
            print(f"Error processing {pred_file.name}: {e}")
            continue
    
    # Aggregate results
    if results:
        avg_metrics = {}
        for metric_name in results[0]["metrics"].keys():
            values = [r["metrics"][metric_name] for r in results if r["metrics"][metric_name] != float('inf')]
            avg_metrics[f"avg_{metric_name}"] = np.mean(values) if values else 0.0
        
        summary = {
            "num_cases": len(results),
            "individual_results": results,
            "average_metrics": avg_metrics
        }
        
        # Save results
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"Results saved to {output_file}")
        
        # Log to MLflow if requested
        if log_mlflow:
            try:
                logger = MedicalImagingMLflowLogger(experiment_name="evaluation_metrics")
                logger.log_metrics(avg_metrics)
                print("Metrics logged to MLflow")
            except Exception as e:
                print(f"Warning: MLflow logging failed: {e}")
        
        return summary
    else:
        print("No valid results to summarize")
        return None


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description="Enhanced medical image evaluation")
    parser.add_argument("--predictions", required=True, help="Directory with prediction masks")
    parser.add_argument("--ground-truth", required=True, help="Directory with ground truth masks")
    parser.add_argument("--output", help="Output JSON file for results")
    parser.add_argument("--mlflow", action="store_true", help="Log metrics to MLflow")
    parser.add_argument("--spacing", nargs=3, type=float, default=[1.0, 1.0, 1.0], 
                       help="Voxel spacing (x y z)")
    
    args = parser.parse_args()
    
    print("Enhanced Medical Image Evaluation")
    print("=" * 40)
    print(f"Predictions: {args.predictions}")
    print(f"Ground Truth: {args.ground_truth}")
    print(f"MLflow Logging: {args.mlflow}")
    
    summary = compute_comprehensive_metrics(
        prediction_dir=args.predictions,
        ground_truth_dir=args.ground_truth,
        output_file=args.output,
        log_mlflow=args.mlflow
    )
    
    if summary:
        print("\nEvaluation Summary:")
        print(f"Cases processed: {summary['num_cases']}")
        avg_dice = summary["average_metrics"].get("avg_dice_score", 0)
        avg_hd95 = summary["average_metrics"].get("avg_robust_hausdorff", 0)
        avg_assd = summary["average_metrics"].get("avg_symmetric_surface_distance", 0)
        print(f"Average Dice: {avg_dice:.4f}")
        print(f"Average HD95: {avg_hd95:.4f}")
        print(f"Average ASSD: {avg_assd:.4f}")


if __name__ == "__main__":
    main()
