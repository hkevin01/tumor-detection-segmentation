# Hyperparameter Optimization Module

This module provides comprehensive hyperparameter optimization capabilities for medical image segmentation models using Optuna.

## 🎯 **Features**

- **Multi-Architecture Support**: UNETR, SwinUNETR, SegResNet, U-Net
- **Intelligent Search Spaces**: Optimized parameter ranges for medical imaging
- **Multi-Objective Optimization**: Balance performance, efficiency, and complexity
- **Advanced Pruning**: Early stopping for poor trials
- **Comprehensive Visualization**: Interactive plots and analysis dashboards
- **Resume Capability**: Continue interrupted optimization studies
- **MLflow Integration**: Track experiments with MLflow

## 🚀 **Quick Start**

### 1. Install Dependencies
```bash
pip install optuna optuna-dashboard plotly mlflow
```

### 2. Run Fast Exploration
```bash
# Quick hyperparameter exploration (10 epochs, 50 trials)
python src/optimization/optimize.py optimize \
    --config src/optimization/configs/fast_exploration.json \
    --output-dir reports/optimization/fast_study
```

### 3. Full UNETR Optimization
```bash
# Comprehensive UNETR optimization (50 epochs, 100 trials)
python src/optimization/optimize.py optimize \
    --config src/optimization/configs/unetr_optimization.json \
    --n-trials 100 \
    --output-dir reports/optimization/unetr_study
```

### 4. View Results
```bash
# Start Optuna Dashboard
optuna-dashboard sqlite:///reports/optimization/unetr_study/unetr_optimization_v1.db
# Visit http://localhost:8080
```

## 📊 **Configuration Files**

### UNETR Optimization
```json
{
  "optimizer": {
    "study_name": "unetr_optimization_v1",
    "direction": "maximize",
    "pruning_enabled": true
  },
  "objective": {
    "max_epochs": 50,
    "target_metrics": {
      "dice_score": 0.85,
      "training_time": 3600
    }
  },
  "optimization": {
    "n_trials": 100
  }
}
```

### SwinUNETR Optimization
```json
{
  "optimizer": {
    "study_name": "swinunetr_optimization_v1",
    "direction": "maximize"
  },
  "objective": {
    "max_epochs": 50,
    "target_metrics": {
      "dice_score": 0.85,
      "training_time": 7200
    }
  }
}
```

## 🔧 **Available Commands**

### Optimize
Start a new optimization study:
```bash
python src/optimization/optimize.py optimize \
    --config CONFIG_FILE \
    --n-trials 100 \
    --output-dir OUTPUT_DIR \
    --log-level INFO
```

### Resume
Resume an interrupted study:
```bash
python src/optimization/optimize.py resume \
    --study STUDY_FILE.pkl \
    --config CONFIG_FILE \
    --n-trials 50
```

### Analyze
Analyze completed study:
```bash
python src/optimization/optimize.py analyze \
    --study STUDY_FILE.pkl \
    --output-dir ANALYSIS_DIR
```

## 📈 **Search Spaces**

### UNETR Parameters
- **Learning Rate**: 1e-5 to 1e-2 (log scale)
- **Batch Size**: [2, 4, 8, 16]
- **Feature Size**: [16, 32, 48, 64]
- **Hidden Size**: [768, 1024, 1536]
- **Dropout Rate**: 0.0 to 0.3

### SwinUNETR Parameters
- **Learning Rate**: 1e-5 to 1e-2 (log scale)
- **Batch Size**: [2, 4, 8] (smaller for memory)
- **Feature Size**: [24, 48, 96]
- **Window Size**: [[7,7,7], [8,8,8]]
- **Depths**: [[2,2,2,2], [2,2,6,2], [2,2,18,2]]

### Loss Function Parameters
- **Focal Loss**: alpha (0.25-0.75), gamma (1.0-3.0)
- **Tversky Loss**: alpha (0.3-0.7), beta (0.3-0.7)
- **Combined Loss**: weighted combinations

### Data Augmentation Parameters
- **Rotation**: 0-30 degrees
- **Scaling**: 0.8-1.2
- **Elastic Deformation**: sigma 5-15, magnitude 50-200
- **Intensity**: brightness ±0.3, contrast 0.7-1.3

## 🎯 **Objective Functions**

### Single Objective
Optimizes a weighted combination of:
- **Performance** (70%): Dice score
- **Efficiency** (20%): Training time + convergence speed
- **Complexity** (10%): Parameter count

### Multi-Objective
Simultaneously optimizes:
1. Dice Score (maximize)
2. Training Efficiency (maximize)
3. Model Complexity (minimize)

### Fast Objective
Reduced epochs for quick exploration:
- Max 10 epochs
- Early stopping after 3 epochs
- Smaller batch sizes
- AMP enabled

## 📊 **Results Analysis**

### Automatic Outputs
- `best_config.json`: Best hyperparameter configuration
- `study_statistics.json`: Comprehensive study statistics
- `visualizations/`: Interactive HTML plots
- `study.pkl`: Complete study object for analysis

### Visualization Plots
- **Optimization History**: Performance over trials
- **Parameter Importance**: Most influential parameters
- **Parallel Coordinates**: Parameter relationships
- **Slice Plots**: Individual parameter effects

## 🔄 **Integration with Training**

The optimized configurations can be directly used with the training pipeline:

```bash
# Use optimized config for training
python src/training/train_enhanced.py \
    --config reports/optimization/unetr_study/best_config.json \
    --dataset-config config/datasets/msd_task01_brain.json \
    --epochs 100 --amp
```

## 🎛️ **Advanced Features**

### MLflow Tracking
```json
{
  "optimizer": {
    "enable_mlflow": true,
    "mlflow_tracking_uri": "http://localhost:5000"
  }
}
```

### Distributed Optimization
```json
{
  "optimizer": {
    "storage_url": "mysql://user:pass@host/db",
    "n_jobs": -1
  }
}
```

### Custom Search Spaces
```python
from src.optimization.hyperparameter_search import create_combined_search_space

search_space = create_combined_search_space(
    model_arch="unetr",
    include_loss_params=True,
    include_aug_params=True
)
```

## 📝 **Best Practices**

1. **Start with Fast Exploration**: Use `fast_exploration.json` to quickly identify promising regions
2. **Monitor Progress**: Use Optuna Dashboard for real-time monitoring
3. **Save Intermediate Results**: Studies are automatically saved and resumable
4. **Use Pruning**: Enable pruning to skip obviously poor trials
5. **Multiple Runs**: Run multiple studies with different random seeds

## 🎯 **Expected Results**

After optimization, expect improvements:
- **Dice Score**: 5-15% improvement over default parameters
- **Training Efficiency**: 20-30% faster convergence
- **Stability**: More consistent results across runs
- **Robustness**: Better generalization to new datasets

## 📋 **Configuration Examples**

### Research Setting (Thorough)
```bash
python src/optimization/optimize.py optimize \
    --config src/optimization/configs/unetr_optimization.json \
    --n-trials 200 \
    --timeout 86400  # 24 hours
```

### Production Setting (Efficient)
```bash
python src/optimization/optimize.py optimize \
    --config src/optimization/configs/fast_exploration.json \
    --n-trials 50 \
    --timeout 3600  # 1 hour
```

### Ablation Study
```bash
# Test specific components
python src/optimization/optimize.py optimize \
    --config src/optimization/configs/loss_function_ablation.json
```

## 🐛 **Troubleshooting**

### Common Issues

1. **CUDA Out of Memory**: Reduce batch size in search space
2. **Slow Convergence**: Enable pruning and reduce max_epochs
3. **Poor Results**: Check data quality and preprocessing
4. **Study Corruption**: Use database storage for robustness

### Debug Mode
```bash
python src/optimization/optimize.py optimize \
    --config CONFIG_FILE \
    --log-level DEBUG \
    --log-file debug.log
```

---

**Ready to optimize your medical image segmentation models!** 🚀

For questions or issues, check the logs or enable debug mode for detailed information.
