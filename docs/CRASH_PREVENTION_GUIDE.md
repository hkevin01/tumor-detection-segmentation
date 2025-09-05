# VSCode Crash Prevention System

🛡️ **Complete solution for preventing VSCode crashes during intensive medical imaging training**

## Problem Solved

When training deep learning models for medical imaging (especially with MONAI and large datasets), the high memory and CPU usage can cause VSCode to become unresponsive or crash. This system provides multiple layers of protection.

## Quick Start

### 1. Interactive Menu (Recommended)
```bash
./scripts/training/crash_prevention_menu.sh
```

### 2. Direct Scripts
```bash
# Clean up resources first
./scripts/training/cleanup_resources.sh

# Ultra-light training (safest)
./scripts/training/ultra_light_training.sh

# Conservative training with limits
./scripts/training/vscode_safe_training.sh 2 1

# Normal training with monitoring
./scripts/training/vscode_safe_training.sh 5 2
```

## System Status Guide

| Memory Usage | Status | Recommended Action |
|-------------|--------|-------------------|
| < 60% | 🟢 Excellent | Any training mode safe |
| 60-70% | 🟡 Good | Conservative training |
| 70-80% | 🟠 Caution | Ultra-light only |
| > 80% | 🔴 Critical | Clean up first |

## Scripts Overview

### `crash_prevention_menu.sh`
Interactive menu system with:
- Real-time resource monitoring
- Smart recommendations based on system status
- Easy access to all protection modes

### `cleanup_resources.sh`
Resource optimization including:
- Python cache cleanup
- Temporary file removal
- Memory optimization
- System status reporting

### `ultra_light_training.sh`
Minimal training mode:
- 1 epoch only
- 1 validation batch
- Lowest system priority
- Minimal memory footprint

### `vscode_safe_training.sh`
Conservative training with:
- Configurable epochs and batches
- Resource monitoring
- CPU/memory limits
- Process isolation

## Protection Mechanisms

### 1. Resource Monitoring
- Real-time memory and CPU checking
- Pre-flight safety verification
- Continuous monitoring during training

### 2. Process Isolation
- Lower process priority (`nice -n 10`)
- Limited thread usage
- Memory allocation limits

### 3. Environment Optimization
```bash
OMP_NUM_THREADS=2                    # Limit CPU threads
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:256  # Memory management
PYTHONHASHSEED=0                     # Reproducibility
```

### 4. Graceful Degradation
- Automatic resource limit detection
- Emergency shutdown capabilities
- Progressive training modes

## Usage Examples

### Start with System Check
```bash
# Check if system is ready
./scripts/training/cleanup_resources.sh
```

### Progressive Training Approach
```bash
# 1. Test with minimal load
./scripts/training/ultra_light_training.sh

# 2. If stable, try conservative mode
./scripts/training/vscode_safe_training.sh 2 1

# 3. If still stable, increase gradually
./scripts/training/vscode_safe_training.sh 5 2
```

### Emergency Mode
If VSCode becomes unresponsive:
1. Open terminal outside VSCode
2. Kill training processes: `pkill -f train_enhanced.py`
3. Run cleanup: `./scripts/training/cleanup_resources.sh`
4. Restart VSCode

## Warning Signs

🚨 **Stop training immediately if you see:**
- VSCode becoming slow or unresponsive
- System memory > 85%
- High swap usage
- System lag or freezing

## Memory Reduction Tips

### Browser
- Close unnecessary tabs
- Use `chrome://discards/` to check memory usage
- Consider lightweight browsers during training

### VSCode
- Close unused editor tabs
- Disable heavy extensions temporarily
- Use `Developer: Reload Window` to refresh

### System
- Close other applications
- Check `htop` for memory-heavy processes
- Consider increasing swap space if needed

## Troubleshooting

### "System not safe for training"
1. Run cleanup script
2. Close browser tabs
3. Close other applications
4. Wait a few minutes
5. Try ultra-light mode

### Training fails to start
1. Check virtual environment: `ls -la .venv/`
2. Verify dependencies: `source .venv/bin/activate && pip list`
3. Check available memory: `free -h`

### VSCode crashes during training
1. Restart VSCode
2. Use ultra-light mode only
3. Consider training outside VSCode
4. Check system specifications

## Advanced Configuration

### Custom Resource Limits
Edit scripts to modify limits:
```bash
# In vscode_safe_training.sh
MEMORY_SAFE_LIMIT=65.0    # Default: 65%
CPU_SAFE_LIMIT=70.0       # Default: 70%
MIN_MEMORY_GB=4           # Default: 4GB
```

### Thread Limits
Adjust for your system:
```bash
# For 4-core systems
export OMP_NUM_THREADS=2

# For 8-core systems
export OMP_NUM_THREADS=4
```

## Files Created

```
scripts/training/
├── crash_prevention_menu.sh      # Interactive menu system
├── cleanup_resources.sh          # Resource optimization
├── ultra_light_training.sh       # Minimal training mode
├── vscode_safe_training.sh       # Conservative training
├── crash_prevention.py           # Python utilities (advanced)
└── vscode_safe_launcher.py       # Python launcher (advanced)
```

## System Requirements

- **Minimum RAM:** 8GB (16GB+ recommended)
- **Available Memory:** 4GB+ free for training
- **CPU:** Multi-core recommended
- **Storage:** Sufficient space for model outputs

## Success Metrics

✅ **System is working correctly if:**
- VSCode remains responsive during training
- Memory usage stays below 80%
- Training completes without system lag
- No emergency shutdowns needed

---

🎯 **Goal:** Train medical imaging models without compromising VSCode stability

💡 **Remember:** Start conservative, monitor closely, scale up gradually
