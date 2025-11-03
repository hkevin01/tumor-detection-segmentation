# AdamW + ReduceLROnPlateau Optimization Guide

## Overview
This guide covers best practices for using AdamW optimizer with ReduceLROnPlateau scheduler for medical image segmentation.

## Why AdamW?
- **Better generalization**: Decoupled weight decay prevents L2 regularization from interfering with adaptive learning rates
- **Stable training**: More robust to hyperparameter choices than Adam
- **Clinical validation**: Proven effective in medical imaging tasks

## Why ReduceLROnPlateau?
- **Adaptive**: Reduces learning rate when validation metric plateaus
- **No epoch scheduling**: Automatically adjusts based on performance
- **Early stopping synergy**: Works well with early stopping strategies

## Configuration Parameters

### AdamW Optimizer
```json
"optimizer": {
  "type": "AdamW",
  "lr": 0.0001,           // Initial learning rate
  "betas": [0.9, 0.999],  // Momentum coefficients
  "eps": 1e-08,           // Numerical stability
  "weight_decay": 0.01,   // L2 penalty (0.01-0.1 for medical imaging)
  "amsgrad": false        // Use AMSGrad variant (rarely needed)
}
```

### ReduceLROnPlateau Scheduler
```json
"scheduler": {
  "type": "ReduceLROnPlateau",
  "mode": "max",          // "max" for Dice, "min" for loss
  "factor": 0.5,          // LR reduction factor (0.1-0.5)
  "patience": 5,          // Epochs to wait before reducing
  "threshold": 0.0001,    // Minimum change to qualify as improvement
  "threshold_mode": "abs",// "abs" or "rel" threshold
  "cooldown": 2,          // Epochs to wait after LR reduction
  "min_lr": 1e-07,        // Minimum learning rate
  "verbose": true         // Log LR changes
}
```

## Recommended Settings

### Small Datasets (<100 samples)
- **lr**: 0.0001
- **weight_decay**: 0.01
- **patience**: 3
- **factor**: 0.5

### Medium Datasets (100-500 samples)
- **lr**: 0.0001
- **weight_decay**: 0.01
- **patience**: 5
- **factor**: 0.5

### Large Datasets (>500 samples)
- **lr**: 0.0003
- **weight_decay**: 0.01
- **patience**: 7
- **factor**: 0.3

## Usage Example

```bash
# Using the optimized configuration
python src/training/train_enhanced.py \
    --config config/recipes/unetr_adamw_optimized.json \
    --dataset-config config/datasets/msd_task01_brain.json \
    --epochs 100
```

## Monitoring Tips

1. **Watch for plateaus**: If LR reduces too frequently, increase patience
2. **Check convergence**: If training stalls, decrease min_lr
3. **Monitor gradients**: Use gradient clipping if gradients explode
4. **Track weight decay**: Higher values prevent overfitting but may reduce capacity

## Common Issues

### Problem: Training plateaus early
**Solution**: Increase patience or decrease threshold

### Problem: LR never reduces
**Solution**: Decrease patience or increase threshold

### Problem: Model underfits
**Solution**: Decrease weight_decay or increase initial lr

### Problem: Model overfits
**Solution**: Increase weight_decay or add more augmentation

## Performance Expectations

With proper configuration, expect:
- **Convergence**: 30-50 epochs for small models, 50-100 for large models
- **Dice Score**: 0.85-0.92 on brain tumor segmentation
- **LR Reductions**: 2-4 times during training
- **Final LR**: ~1e-6 to 1e-7

## Advanced Tips

1. **Warmup**: Start with lower LR for first 5 epochs
2. **Gradient Accumulation**: Use when batch size is limited
3. **Mixed Precision**: Enable AMP for faster training
4. **Early Stopping**: Set patience = scheduler_patience + 5

## References

- AdamW Paper: "Decoupled Weight Decay Regularization" (Loshchilov & Hutter, 2019)
- ReduceLROnPlateau: PyTorch documentation
- Medical Imaging Best Practices: MONAI tutorials

Last Updated: November 3, 2025
