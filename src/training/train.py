"""
Simplified training script for tumor detection and segmentation.

This script provides an easy-to-use interface for training models
using the comprehensive trainer class.
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from training.trainer import ModelTrainer, setup_training
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description='Train tumor segmentation model')
    parser.add_argument(
        '--config', 
        type=str, 
        default='config.json',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Path to checkpoint to resume from'
    )
    
    args = parser.parse_args()
    
    if not DEPENDENCIES_AVAILABLE:
        print("Error: Required dependencies not available.")
        print("Please install the required packages:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Load configuration
    if not Path(args.config).exists():
        print(f"Configuration file not found: {args.config}")
        sys.exit(1)
    
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    print("Tumor Detection and Segmentation Training")
    print("=" * 45)
    print(f"Configuration: {args.config}")
    
    try:
        # Setup training components
        model, train_loader, val_loader = setup_training(args.config)
        
        # Create trainer
        trainer = ModelTrainer(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            config=config
        )
        
        # Resume from checkpoint if specified
        if args.resume:
            trainer.load_checkpoint(args.resume)
            print(f"Resumed from checkpoint: {args.resume}")
        
        # Start training
        num_epochs = config.get('epochs', 100)
        trainer.train(num_epochs)
        
        print("Training completed successfully!")
        
    except Exception as e:
        print(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
