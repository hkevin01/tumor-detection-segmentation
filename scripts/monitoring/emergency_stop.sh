#!/bin/bash
# Emergency stop script for runaway processes

echo "🚨 EMERGENCY STOP TRIGGERED"

# Kill all Python training processes
pkill -f "train_enhanced.py"
pkill -f "train.py"

# Kill high-memory Python processes
ps aux | grep python | awk '$6 > 1000000 {print $2}' | xargs kill -9 2>/dev/null

# Clear GPU memory
python -c "
try:
    import torch
    torch.cuda.empty_cache()
    print('✅ GPU cache cleared')
except:
    print('ℹ️  No GPU cache to clear')
"

# Force garbage collection
python -c "import gc; gc.collect(); print('✅ Garbage collection completed')"

echo "✅ Emergency stop completed"
