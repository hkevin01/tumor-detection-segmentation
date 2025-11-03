# 🚀 Optimizer & Scheduler Configuration Guide

## Overview

This guide provides comprehensive documentation for configuring optimizers and learning rate schedulers in the tumor detection and segmentation training pipeline.

## Table of Contents

1. [AdamW Optimizer](#adamw-optimizer)
2. [ReduceLROnPlateau Scheduler](#reducelronplateau-scheduler)
3. [Best Practices](#best-practices)
4. [Configuration Examples](#configuration-examples)
5. [Troubleshooting](#troubleshooting)

---

## AdamW Optimizer

### What is AdamW?

AdamW (Adam with Weight Decay) is an improved version of the Adam optimizer that decouples weight decay from the gradient-based optimization step. This leads to better generalization and more stable training.

### Key Advantages

✅ **Better Generalization**: Improved weight decay mechanism  
✅ **Stable Training**: More robust convergence properties  
✅ **Medical Imaging Friendly**: Works well with small batch sizes  
✅ **Transfer Learning**: Excellent for fine-tuning pretrained models  

### Configuration Parameters

```json
{
  "optimizer": {
    "name": "AdamW",
    "lr": 0.0001,              // Learning rate (typical: 1e-4 to 1e-3)
    "betas": [0.9, 0.999],      // Momentum coefficients
    "eps": 1e-8,                // Numerical stability term
    "weight_decay": 0.01,       // L2 regularization (typical: 0.01 to 0.1)
    "amsgrad": false            // Use AMSGrad variant (rarely needed)
  }
}
```

### Parameter Guidelines

| Parameter | Typical Range | Description | Recommendation |
|-----------|--------------|-------------|----------------|
| `lr` | 1e-5 to 1e-3 | Base learning rate | Start with 1e-4 for medical imaging |
| `betas` | [0.9, 0.999] | Momentum parameters | Use defaults unless specific reason |
| `eps` | 1e-8 | Numerical stability | Use default |
| `weight_decay` | 0.01 to 0.1 | Regularization strength | 0.01 for small models, 0.05-0.1 for large |
| `amsgrad` | true/false | Variant selection | false (rarely helps) |

### When to Use AdamW

✅ **Use AdamW when:**
- Training transformers (UNETR, SwinUNETR)
- Fine-tuning pretrained models
- Working with small batch sizes (1-4)
- Training large models with many parameters
- Need stable convergence without hyperparameter tuning

❌ **Consider alternatives when:**
- Using very simple models (basic UNet)
- Have large batch sizes (>32)
- Need maximum convergence speed on small datasets

---

## ReduceLROnPlateau Scheduler

### What is ReduceLROnPlateau?

ReduceLROnPlateau dynamically reduces the learning rate when a monitored metric (e.g., validation Dice score) stops improving. This adaptive approach helps escape plateaus and achieve better final performance.

### Key Advantages

✅ **Adaptive**: Automatically adjusts learning rate based on validation performance  
✅ **No Manual Tuning**: No need to set epoch schedules  
✅ **Better Final Accuracy**: Helps achieve optimal convergence  
✅ **Plateau Escape**: Breaks through training plateaus  

### Configuration Parameters

```json
{
  "scheduler": {
    "name": "ReduceLROnPlateau",
    "mode": "max",              // "max" for metrics to maximize (Dice), "min" for loss
    "factor": 0.5,              // Multiply LR by this (0.5 = halve LR)
    "patience": 10,             // Epochs without improvement before reducing
    "threshold": 0.0001,        // Minimum change to count as improvement
    "threshold_mode": "rel",    // "rel" for relative, "abs" for absolute
    "cooldown": 5,              // Epochs to wait after LR reduction
    "min_lr": 1e-7,             // Minimum learning rate
    "verbose": true             // Print LR changes
  }
}
```

### Parameter Guidelines

| Parameter | Typical Range | Description | Recommendation |
|-----------|--------------|-------------|----------------|
| `mode` | "max" or "min" | Optimization direction | "max" for Dice/accuracy, "min" for loss |
| `factor` | 0.1 to 0.5 | LR reduction factor | 0.5 (moderate) or 0.2 (aggressive) |
| `patience` | 5 to 20 | Epochs to wait | 10 for stable training, 5 for quick experiments |
| `threshold` | 1e-5 to 1e-3 | Improvement threshold | 1e-4 (balanced sensitivity) |
| `threshold_mode` | "rel" or "abs" | Threshold type | "rel" (relative improvement) |
| `cooldown` | 0 to 10 | Rest period after reduction | 5 (allows adjustment) |
| `min_lr` | 1e-8 to 1e-6 | Minimum LR | 1e-7 (standard floor) |
| `verbose` | true/false | Print updates | true (for monitoring) |

### When to Use ReduceLROnPlateau

✅ **Use ReduceLROnPlateau when:**
- Training for many epochs (>50)
- Unsure about optimal LR schedule
- Validation metric plateaus frequently
- Training medical imaging models
- Want adaptive learning without manual intervention

❌ **Consider alternatives when:**
- Training for few epochs (<20)
- Using cyclical training strategies
- Need predictable LR schedules for reproducibility

---

## Best Practices

### 1. Combining AdamW + ReduceLROnPlateau

**Recommended Configuration:**

```json
{
  "optimizer": {
    "name": "AdamW",
    "lr": 0.0001,
    "weight_decay": 0.01
  },
  "scheduler": {
    "name": "ReduceLROnPlateau",
    "mode": "max",
    "factor": 0.5,
    "patience": 10,
    "min_lr": 1e-7
  }
}
```

**Why this works:**
- AdamW provides stable base optimization
- ReduceLROnPlateau adapts to validation performance
- Combination handles plateaus automatically
- Minimal hyperparameter tuning needed

### 2. Learning Rate Ranges

| Model Size | Initial LR | Weight Decay | Patience |
|------------|-----------|--------------|----------|
| Small (<5M params) | 3e-4 | 0.01 | 5-10 |
| Medium (5-50M params) | 1e-4 | 0.01 | 10-15 |
| Large (>50M params) | 5e-5 | 0.05 | 15-20 |

### 3. Gradient Clipping

**Recommended for all medical imaging models:**

```json
{
  "training": {
    "gradient_clipping": true,
    "max_grad_norm": 1.0
  }
}
```

### 4. Warmup Strategy

For large models or small datasets, consider learning rate warmup:

```python
# Linear warmup over first 5 epochs
warmup_epochs = 5
if epoch < warmup_epochs:
    warmup_factor = (epoch + 1) / warmup_epochs
    for param_group in optimizer.param_groups:
        param_group['lr'] = base_lr * warmup_factor
```

### 5. Monitoring and Logging

**Essential metrics to track:**

```python
# Log every epoch
mlflow.log_metric("learning_rate", optimizer.param_groups[0]['lr'], step=epoch)
mlflow.log_metric("train_loss", train_loss, step=epoch)
mlflow.log_metric("val_dice", val_dice, step=epoch)
mlflow.log_metric("val_loss", val_loss, step=epoch)
```

---

## Configuration Examples

### Example 1: Quick Experimentation (Few Epochs)

```json
{
  "optimizer": {
    "name": "AdamW",
    "lr": 0.0003,
    "weight_decay": 0.01
  },
  "scheduler": {
    "name": "ReduceLROnPlateau",
    "mode": "max",
    "factor": 0.5,
    "patience": 3,
    "min_lr": 1e-6
  },
  "training": {
    "max_epochs": 20,
    "gradient_clipping": true,
    "max_grad_norm": 1.0
  }
}
```

### Example 2: Production Training (Long Run)

```json
{
  "optimizer": {
    "name": "AdamW",
    "lr": 0.0001,
    "betas": [0.9, 0.999],
    "weight_decay": 0.01
  },
  "scheduler": {
    "name": "ReduceLROnPlateau",
    "mode": "max",
    "factor": 0.5,
    "patience": 15,
    "threshold": 0.0001,
    "cooldown": 5,
    "min_lr": 1e-7,
    "verbose": true
  },
  "training": {
    "max_epochs": 200,
    "gradient_clipping": true,
    "max_grad_norm": 1.0,
    "early_stopping": true,
    "early_stopping_patience": 50
  }
}
```

### Example 3: Large Model (UNETR)

```json
{
  "optimizer": {
    "name": "AdamW",
    "lr": 0.00005,
    "weight_decay": 0.05
  },
  "scheduler": {
    "name": "ReduceLROnPlateau",
    "mode": "max",
    "factor": 0.5,
    "patience": 20,
    "min_lr": 1e-8
  },
  "training": {
    "max_epochs": 300,
    "gradient_clipping": true,
    "max_grad_norm": 1.0,
    "warmup_epochs": 10
  }
}
```

### Example 4: Fine-tuning Pretrained Model

```json
{
  "optimizer": {
    "name": "AdamW",
    "lr": 0.00001,
    "weight_decay": 0.001
  },
  "scheduler": {
    "name": "ReduceLROnPlateau",
    "mode": "max",
    "factor": 0.3,
    "patience": 5,
    "min_lr": 1e-8
  },
  "training": {
    "max_epochs": 50,
    "gradient_clipping": true,
    "max_grad_norm": 0.5
  }
}
```

---

## Troubleshooting

### Problem 1: Training Loss Not Decreasing

**Symptoms:**
- Loss stays high or increases
- Validation metrics don't improve

**Solutions:**
1. **Increase learning rate** (try 3e-4 or 5e-4)
2. **Reduce weight decay** (try 0.001)
3. **Check data augmentation** (might be too aggressive)
4. **Verify data loading** (ensure targets are correct)

### Problem 2: Overfitting Quickly

**Symptoms:**
- Train loss decreases but val loss increases
- Large gap between train and val metrics

**Solutions:**
1. **Increase weight decay** (try 0.05 or 0.1)
2. **Add more augmentation**
3. **Reduce model size or add dropout**
4. **Use more training data**

### Problem 3: Learning Rate Drops Too Quickly

**Symptoms:**
- LR reaches min_lr early in training
- Performance plateaus prematurely

**Solutions:**
1. **Increase patience** (try 15-20)
2. **Reduce factor** (try 0.7 instead of 0.5)
3. **Lower min_lr** (try 1e-8 or 1e-9)
4. **Add cooldown period** (5-10 epochs)

### Problem 4: Training Unstable / Exploding Gradients

**Symptoms:**
- Loss becomes NaN or Inf
- Gradients become very large

**Solutions:**
1. **Enable gradient clipping** (max_norm=1.0)
2. **Reduce learning rate** (try 1e-5)
3. **Check for batch norm issues**
4. **Verify input normalization**

### Problem 5: No Improvement After LR Reduction

**Symptoms:**
- LR reduces but metrics don't improve
- Multiple reductions without progress

**Solutions:**
1. **Check if min_lr is too high**
2. **Model might be at capacity** (try larger model)
3. **Data might be insufficient** (add more samples)
4. **Consider early stopping**

---

## Advanced Techniques

### 1. Layer-wise Learning Rates

For fine-tuning, use different LRs for different layers:

```python
param_groups = [
    {'params': model.encoder.parameters(), 'lr': 1e-5},
    {'params': model.decoder.parameters(), 'lr': 1e-4}
]
optimizer = torch.optim.AdamW(param_groups, weight_decay=0.01)
```

### 2. Cosine Annealing Alternative

For fixed epoch training:

```json
{
  "scheduler": {
    "name": "cosine",
    "T_max": 100,
    "eta_min": 1e-7
  }
}
```

### 3. Exponential Moving Average (EMA)

For more stable models:

```python
from torch.optim.swa_utils import AveragedModel

ema_model = AveragedModel(model, decay=0.999)
```

---

## Performance Expectations

### Typical Training Curves

**With AdamW + ReduceLROnPlateau:**

- **Epochs 1-20**: Rapid improvement (Dice: 0.40 → 0.75)
- **Epochs 20-60**: Steady improvement (Dice: 0.75 → 0.85)
- **Epochs 60-100**: Fine-tuning (Dice: 0.85 → 0.88)
- **First LR reduction**: Around epoch 40-50
- **Second LR reduction**: Around epoch 70-80

### Expected Metrics

| Dataset | Final Dice | Epochs | LR Reductions |
|---------|-----------|---------|---------------|
| BraTS (Brain) | 0.85-0.90 | 100-150 | 2-3 |
| MSD Liver | 0.80-0.85 | 80-120 | 2-3 |
| KiTS (Kidney) | 0.82-0.88 | 100-150 | 2-4 |

---

## References

1. **AdamW Paper**: [Decoupled Weight Decay Regularization](https://arxiv.org/abs/1711.05101)
2. **PyTorch Documentation**: [torch.optim](https://pytorch.org/docs/stable/optim.html)
3. **Best Practices**: [Medical Imaging Deep Learning Guide](https://monai.io)

---

## Quick Start Commands

### Training with Optimized Config

```bash
# Use the optimized AdamW configuration
python src/training/train_enhanced.py \
  --config config/recipes/unetr_adamw_optimized.json \
  --dataset-config config/datasets/msd_task01_brain.json \
  --epochs 100 \
  --amp

# Monitor with MLflow
mlflow ui --port 5000
```

### Experiment with Different Settings

```bash
# Higher learning rate (faster convergence)
python src/training/train_enhanced.py \
  --config config/recipes/unetr_adamw_optimized.json \
  --override optimizer.lr=0.0003 \
  --epochs 50

# More aggressive LR reduction
python src/training/train_enhanced.py \
  --config config/recipes/unetr_adamw_optimized.json \
  --override scheduler.factor=0.2 \
  --override scheduler.patience=5 \
  --epochs 100
```

---

**Last Updated**: November 3, 2025  
**Version**: 1.0  
**Maintainer**: Medical Imaging AI Team
